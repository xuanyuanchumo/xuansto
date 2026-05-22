#!/usr/bin/env python3
"""
测试SDD测试生成器增强版功能
"""

import sys
from pathlib import Path

sys.path.insert(0, str(get_path_config().SKILL_ROOT))
sys.path.insert(0, str(get_path_config().SKILL_ROOT.parent))

from test.sdd_test_generator_enhanced import (
    MultiFrameworkTestGenerator,
    TestCoverageValidator,
    TestFramework,
)
from pipeline.sdd_spec_parser_enhanced import EnhancedSDDSpecParser


def test_basic_generation():
    print("="*60)
    print("测试1: 基本测试生成功能")
    print("="*60)
    
    spec_path = Path(__file__).parent / "test_spec_user.yaml"
    
    with open(spec_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    parser = EnhancedSDDSpecParser()
    spec, validation_result = parser.parse(
        content=content,
        source_format="yaml",
        source_path=str(spec_path)
    )
    
    print(f"\n规范ID: {spec.metadata.id}")
    print(f"规范名称: {spec.metadata.name}")
    print(f"规范类型: {spec.kind.value}")
    print(f"验证结果: {'通过' if validation_result.is_valid else '失败'}")
    
    if not validation_result.is_valid:
        print("\n验证错误:")
        for err in validation_result.errors:
            print(f"  - [{err.path}] {err.message}")
        return
    
    generator = MultiFrameworkTestGenerator()
    
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n生成测试文件...")
    results = generator.generate(
        spec=spec,
        frameworks=[TestFramework.PYTEST],
        output_dir=str(output_dir)
    )
    
    print(f"\n生成结果:")
    for result in results:
        print(f"  - 文件名: {result.filename}")
        print(f"    测试用例数: {result.test_count}")
        print(f"    框架: {result.framework.value}")
        print(f"    依赖: {', '.join(result.dependencies)}")
    
    print(f"\n测试文件已保存到: {output_dir}")


def test_coverage_validation():
    print("\n" + "="*60)
    print("测试2: 测试覆盖率验证功能")
    print("="*60)
    
    spec_path = Path(__file__).parent / "test_spec_user.yaml"
    
    with open(spec_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    parser = EnhancedSDDSpecParser()
    spec, validation_result = parser.parse(
        content=content,
        source_format="yaml",
        source_path=str(spec_path)
    )
    
    if not validation_result.is_valid:
        print("规范验证失败")
        return
    
    generator = MultiFrameworkTestGenerator()
    pytest_gen = generator.generators.get(TestFramework.PYTEST)
    test_suite = pytest_gen._build_test_suite(spec)
    
    validator = TestCoverageValidator()
    report = validator.validate_coverage(spec, test_suite.test_cases)
    
    print(f"\n覆盖率报告:")
    print(f"  规范ID: {report.spec_id}")
    print(f"  规范名称: {report.spec_name}")
    print(f"  总元素数: {report.total_elements}")
    print(f"  已覆盖元素: {report.covered_elements}")
    print(f"  覆盖率: {report.coverage_percentage:.2f}%")
    
    if report.uncovered_elements:
        print(f"\n未覆盖元素:")
        for element in report.uncovered_elements[:5]:
            print(f"    - {element}")
    
    if report.recommendations:
        print(f"\n建议:")
        for rec in report.recommendations[:3]:
            print(f"    - {rec}")
    
    passed, message = validator.check_threshold(report, "entity")
    print(f"\n阈值检查: {'通过' if passed else '未通过'}")
    print(f"  {message}")


def test_business_rule_generation():
    print("\n" + "="*60)
    print("测试3: 业务规则测试生成")
    print("="*60)
    
    spec_path = Path(__file__).parent / "test_spec_user.yaml"
    
    with open(spec_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    parser = EnhancedSDDSpecParser()
    spec, validation_result = parser.parse(
        content=content,
        source_format="yaml",
        source_path=str(spec_path)
    )
    
    if not validation_result.is_valid:
        print("规范验证失败")
        return
    
    generator = MultiFrameworkTestGenerator()
    pytest_gen = generator.generators.get(TestFramework.PYTEST)
    test_suite = pytest_gen._build_test_suite(spec)
    
    business_rule_tests = [
        tc for tc in test_suite.test_cases
        if "business_rule" in tc.markers
    ]
    
    print(f"\n业务规则测试用例数: {len(business_rule_tests)}")
    print(f"\n业务规则测试用例:")
    for tc in business_rule_tests[:5]:
        print(f"  - ID: {tc.id}")
        print(f"    名称: {tc.name}")
        print(f"    描述: {tc.description}")
        print(f"    标记: {', '.join(tc.markers)}")
        print()


def test_constraint_generation():
    print("\n" + "="*60)
    print("测试4: 约束条件测试生成")
    print("="*60)
    
    spec_path = Path(__file__).parent / "test_spec_user.yaml"
    
    with open(spec_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    parser = EnhancedSDDSpecParser()
    spec, validation_result = parser.parse(
        content=content,
        source_format="yaml",
        source_path=str(spec_path)
    )
    
    if not validation_result.is_valid:
        print("规范验证失败")
        return
    
    generator = MultiFrameworkTestGenerator()
    pytest_gen = generator.generators.get(TestFramework.PYTEST)
    test_suite = pytest_gen._build_test_suite(spec)
    
    constraint_tests = [
        tc for tc in test_suite.test_cases
        if "constraint" in tc.markers
    ]
    
    print(f"\n约束条件测试用例数: {len(constraint_tests)}")
    print(f"\n约束条件测试用例示例:")
    for tc in constraint_tests[:5]:
        print(f"  - ID: {tc.id}")
        print(f"    名称: {tc.name}")
        print(f"    描述: {tc.description}")
        print(f"    标记: {', '.join(tc.markers)}")
        print()


if __name__ == "__main__":
    try:
        test_basic_generation()
        test_coverage_validation()
        test_business_rule_generation()
        test_constraint_generation()
        
        print("\n" + "="*60)
        print("所有测试完成!")
        print("="*60)
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
from skillscripts.core.path_config_center import get_path_config
        traceback.print_exc()
