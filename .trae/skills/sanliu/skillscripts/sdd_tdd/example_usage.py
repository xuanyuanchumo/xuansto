#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDD+TDD循环开发模式使用示例

本示例展示如何使用SDD-TDD集成流程进行开发：
1. 创建规范文件
2. 执行SDD-TDD集成流程
3. 查看生成的测试和代码
"""

from pathlib import Path

try:
    from sdd_tdd_integration import SddTddIntegration, IntegrationConfig
    from enhanced_spec_parser import EnhancedSDDSpecParser, SpecFormat
    from spec_to_test_mapper import SpecToTestMapper, TestFramework
    from spec_to_code_generator import SpecToCodeGenerator, CodeLanguage
    from spec_completeness_validator import SpecCompletenessValidator
    from tdd_cycle_executor import TDDCycleExecutor
except ImportError:
    from .sdd_tdd_integration import SddTddIntegration, IntegrationConfig
    from .enhanced_spec_parser import EnhancedSDDSpecParser, SpecFormat
    from .spec_to_test_mapper import SpecToTestMapper, TestFramework
    from .spec_to_code_generator import SpecToCodeGenerator, CodeLanguage
    from .spec_completeness_validator import SpecCompletenessValidator
    from .tdd_cycle_executor import TDDCycleExecutor


def create_example_spec() -> Path:
    """创建示例规范文件"""
    spec_content = """# 用户管理规范

规范ID: SPC-USER-001
版本: v1.0
作者: SDD-TDD系统

## 功能描述

用户管理模块提供用户的增删改查功能，包括用户注册、登录、信息更新和注销等核心功能。

## 属性定义

- username: 用户名，必填，唯一，类型: string，描述: 用户登录名，长度3-20字符
- email: 电子邮箱，必填，唯一，类型: string，描述: 用户邮箱地址
- password: 密码，必填，类型: string，描述: 用户密码，长度6-50字符
- age: 年龄，可选，类型: integer，描述: 用户年龄
- status: 状态，必填，类型: enum，枚举值: [active, inactive, banned]，默认值: active
- created_at: 创建时间，必填，类型: datetime，描述: 账户创建时间

## 接口定义

### 用户注册
- 方法: POST
- 路径: /api/v1/users/register
- 描述: 用户注册接口

### 用户登录
- 方法: POST
- 路径: /api/v1/users/login
- 描述: 用户登录接口

### 获取用户信息
- 方法: GET
- 路径: /api/v1/users/{user_id}
- 描述: 根据ID获取用户信息

### 更新用户信息
- 方法: PUT
- 路径: /api/v1/users/{user_id}
- 描述: 更新用户信息

### 删除用户
- 方法: DELETE
- 路径: /api/v1/users/{user_id}
- 描述: 删除用户账户

## 测试场景

### 场景1: 用户注册成功
- Given: 系统正常运行，用户未注册
- When: 提交有效的注册信息（用户名、邮箱、密码）
- Then: 用户注册成功，返回用户ID和成功消息

### 场景2: 用户注册失败-用户名重复
- Given: 系统正常运行，用户名已存在
- When: 提交已存在的用户名进行注册
- Then: 注册失败，返回用户名已存在错误

### 场景3: 用户登录成功
- Given: 用户已注册，状态为active
- When: 提交正确的用户名和密码
- Then: 登录成功，返回认证令牌

### 场景4: 用户登录失败-密码错误
- Given: 用户已注册
- When: 提交错误的密码
- Then: 登录失败，返回密码错误提示

## 约束条件

- 用户名长度必须在3-20字符之间
- 密码长度必须在6-50字符之间
- 邮箱格式必须符合标准格式
- 用户年龄必须在1-150之间

## 业务规则

- BR-001: 新注册用户默认状态为active
- BR-002: 被ban的用户无法登录
- BR-003: 密码必须加密存储

## 异常处理

- UserNotFoundException: 用户不存在
- DuplicateUsernameException: 用户名重复
- InvalidPasswordException: 密码格式错误
- AuthenticationFailedException: 认证失败
"""
    
    spec_dir = Path("examples/specs")
    spec_dir.mkdir(parents=True, exist_ok=True)
    
    spec_file = spec_dir / "user_management.md"
    spec_file.write_text(spec_content, encoding="utf-8")
    
    print(f"示例规范文件已创建: {spec_file}")
    return spec_file


def example_basic_usage():
    """基础使用示例"""
    print("\n" + "=" * 80)
    print("示例1: 基础使用流程")
    print("=" * 80)
    
    spec_file = create_example_spec()
    
    config = IntegrationConfig(
        spec_file=str(spec_file),
        output_dir="examples/output/basic",
        test_framework=TestFramework.PYTEST,
        code_language=CodeLanguage.PYTHON,
        execute_tdd_cycle=False,
        verbose=True
    )
    
    integration = SddTddIntegration(config)
    result = integration.execute()
    
    print(f"\n执行结果: {'成功' if result.success else '失败'}")
    print(f"生成文件数: {len(result.generated_files)}")
    
    return result


def example_spec_parsing():
    """规范解析示例"""
    print("\n" + "=" * 80)
    print("示例2: 规范解析")
    print("=" * 80)
    
    spec_file = create_example_spec()
    
    parser = EnhancedSDDSpecParser()
    spec, validation_result = parser.parse_file(str(spec_file))
    
    print(f"\n规范信息:")
    print(f"  ID: {spec.metadata.id}")
    print(f"  名称: {spec.metadata.name}")
    print(f"  版本: {spec.metadata.version}")
    print(f"  类型: {spec.kind.value}")
    print(f"  属性数: {len(spec.attributes)}")
    print(f"  端点数: {len(spec.endpoints)}")
    print(f"  场景数: {len(spec.scenarios)}")
    print(f"  约束数: {len(spec.constraints)}")
    print(f"  业务规则数: {len(spec.business_rules)}")
    
    print(f"\n验证结果:")
    print(f"  有效: {validation_result.is_valid}")
    print(f"  错误数: {len(validation_result.errors)}")
    print(f"  警告数: {len(validation_result.warnings)}")
    
    return spec


def example_test_generation():
    """测试生成示例"""
    print("\n" + "=" * 80)
    print("示例3: 测试用例生成")
    print("=" * 80)
    
    spec_file = create_example_spec()
    
    parser = EnhancedSDDSpecParser()
    spec, _ = parser.parse_file(str(spec_file))
    
    mapper = SpecToTestMapper(
        framework=TestFramework.PYTEST,
        output_dir=Path("examples/output/tests")
    )
    
    result = mapper.generate_tests_from_spec(spec)
    
    print(f"\n测试生成结果:")
    print(f"  测试用例数: {len(result.test_cases)}")
    print(f"  覆盖率: {result.coverage_report['coverage_percentage']:.2f}%")
    
    print(f"\n测试用例列表:")
    for idx, tc in enumerate(result.test_cases[:10], 1):
        print(f"  {idx}. {tc.name} ({tc.test_type.value}, {tc.priority})")
    
    test_file = mapper.save_test_file(result)
    print(f"\n测试文件已保存: {test_file}")
    
    return result


def example_code_generation():
    """代码生成示例"""
    print("\n" + "=" * 80)
    print("示例4: 代码骨架生成")
    print("=" * 80)
    
    spec_file = create_example_spec()
    
    parser = EnhancedSDDSpecParser()
    spec, _ = parser.parse_file(str(spec_file))
    
    generator = SpecToCodeGenerator(
        output_dir=Path("examples/output/src")
    )
    
    skeletons = generator.generate(
        spec,
        languages=[CodeLanguage.PYTHON],
        output_dir=Path("examples/output/src")
    )
    
    print(f"\n代码生成结果:")
    print(f"  生成文件数: {len(skeletons)}")
    
    for skeleton in skeletons:
        print(f"\n  文件: {skeleton.filename}")
        print(f"  类型: {skeleton.artifact_type.value}")
        print(f"  语言: {skeleton.language.value}")
        print(f"  代码行数: {len(skeleton.content.splitlines())}")
    
    return skeletons


def example_completeness_validation():
    """完整性验证示例"""
    print("\n" + "=" * 80)
    print("示例5: 规范完整性验证")
    print("=" * 80)
    
    spec_file = create_example_spec()
    
    parser = EnhancedSDDSpecParser()
    spec, _ = parser.parse_file(str(spec_file))
    
    validator = SpecCompletenessValidator()
    report = validator.validate_completeness(spec)
    
    print(f"\n完整性验证结果:")
    print(f"  完整性得分: {report.completeness_score}%")
    print(f"  完整性级别: {report.level.value}")
    print(f"  通过检查: {len(report.passed_checks)}")
    print(f"  未通过检查: {len(report.failed_checks)}")
    
    if report.passed_checks:
        print(f"\n  通过的检查:")
        for check in report.passed_checks[:5]:
            print(f"    ✓ {check}")
    
    if report.failed_checks:
        print(f"\n  未通过的检查:")
        for check in report.failed_checks[:5]:
            print(f"    ✗ {check}")
    
    if report.suggestions:
        print(f"\n  改进建议:")
        for suggestion in report.suggestions[:5]:
            print(f"    - {suggestion}")
    
    return report


def example_full_integration():
    """完整集成流程示例"""
    print("\n" + "=" * 80)
    print("示例6: 完整SDD-TDD集成流程")
    print("=" * 80)
    
    spec_file = create_example_spec()
    
    config = IntegrationConfig(
        spec_file=str(spec_file),
        output_dir="examples/output/full",
        test_framework=TestFramework.PYTEST,
        code_language=CodeLanguage.PYTHON,
        execute_tdd_cycle=True,
        coverage_threshold=80.0,
        auto_refactor=True,
        verbose=True
    )
    
    integration = SddTddIntegration(config)
    result = integration.execute()
    
    report_file = integration.save_result_report(result)
    
    print(f"\n集成报告已保存: {report_file}")
    
    return result


def main():
    """主函数"""
    print("=" * 80)
    print("SDD+TDD循环开发模式使用示例")
    print("=" * 80)
    
    examples = [
        ("基础使用流程", example_basic_usage),
        ("规范解析", example_spec_parsing),
        ("测试用例生成", example_test_generation),
        ("代码骨架生成", example_code_generation),
        ("完整性验证", example_completeness_validation),
        ("完整集成流程", example_full_integration),
    ]
    
    print("\n可用示例:")
    for idx, (name, _) in enumerate(examples, 1):
        print(f"  {idx}. {name}")
    
    print("\n提示: 可以单独运行各个示例函数来查看详细演示")
    
    print("\n运行基础示例...")
    example_basic_usage()
    
    print("\n" + "=" * 80)
    print("示例运行完成")
    print("=" * 80)
    print("\n生成的文件位于: examples/output/")
    print("\n下一步:")
    print("  1. 查看生成的测试文件: examples/output/basic/tests/")
    print("  2. 查看生成的代码文件: examples/output/basic/src/")
    print("  3. 查看集成报告: examples/output/full/integration_report_*.json")
    print("  4. 运行测试: pytest examples/output/basic/tests/")
    print("  5. 根据测试结果实现代码逻辑")


if __name__ == "__main__":
    main()
