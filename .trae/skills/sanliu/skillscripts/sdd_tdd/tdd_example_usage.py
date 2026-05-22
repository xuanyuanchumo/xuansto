#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TDD循环执行器使用示例

展示如何使用完善后的TDD红绿蓝循环执行器
"""

from pathlib import Path
import sys

sys.path.insert(0, str(get_path_config().SCRIPTS_DIR / "sdd_tdd"))

from tdd_cycle_executor import (
    TDDCycleExecutor,
    CodeLanguage,
    TDDCyclePhase,
    TestStatus,
)


def example_red_phase():
    print("\n" + "="*80)
    print("示例1: 红阶段 - 测试先行")
    print("="*80)
    
    executor = TDDCycleExecutor(
        test_command="pytest",
        test_dir=Path("tests"),
        source_dir=Path("src"),
        language=CodeLanguage.PYTHON
    )
    
    test_file = Path("tests/test_example.py")
    test_cases = ["test_create_user", "test_get_user", "test_update_user", "test_delete_user"]
    
    print(f"\n生成测试文件: {test_file}")
    print(f"测试用例: {test_cases}")
    
    result = executor.execute_red_phase(
        test_file=test_file,
        test_cases=test_cases,
        test_template="unit_test"
    )
    
    print(f"\n红阶段结果:")
    print(f"  状态: {result.test_status.value}")
    print(f"  失败数: {result.failure_count}")
    print(f"  耗时: {result.duration:.2f}秒")
    print(f"  覆盖率估计: {result.coverage_estimate}%")
    print(f"  使用模板: {result.test_templates_used}")
    
    if result.test_status == TestStatus.FAILED:
        print("\n✓ 红阶段成功：测试正确失败（符合TDD原则）")
    
    return result


def example_green_phase():
    print("\n" + "="*80)
    print("示例2: 绿阶段 - 最小实现")
    print("="*80)
    
    executor = TDDCycleExecutor(language=CodeLanguage.PYTHON)
    
    test_file = Path("tests/test_example.py")
    impl_file = Path("src/user_service.py")
    
    impl_code = '''
"""用户服务实现"""

from typing import Optional, List


class UserService:
    """用户服务类"""
    
    def __init__(self):
        self.users = {}
        self.next_id = 1
    
    def create(self, data: dict) -> dict:
        """创建用户"""
        user_id = self.next_id
        self.users[user_id] = {"id": user_id, **data}
        self.next_id += 1
        return self.users[user_id]
    
    def get_by_id(self, user_id: int) -> Optional[dict]:
        """根据ID获取用户"""
        return self.users.get(user_id)
    
    def update(self, user_id: int, data: dict) -> Optional[dict]:
        """更新用户"""
        if user_id not in self.users:
            return None
        self.users[user_id].update(data)
        return self.users[user_id]
    
    def delete(self, user_id: int) -> bool:
        """删除用户"""
        if user_id not in self.users:
            return False
        del self.users[user_id]
        return True
'''
    
    print(f"\n实现文件: {impl_file}")
    print(f"测试文件: {test_file}")
    
    result = executor.execute_green_phase(
        test_file=test_file,
        implementation_file=impl_file,
        implementation_code=impl_code
    )
    
    print(f"\n绿阶段结果:")
    print(f"  状态: {result.test_status.value}")
    print(f"  通过数: {result.passed_count}")
    print(f"  失败数: {result.failed_count}")
    print(f"  迭代次数: {result.iterations}")
    print(f"  最小实现: {'是' if result.min_implementation else '否'}")
    print(f"  实现建议数: {len(result.implementation_suggestions)}")
    
    if result.test_status == TestStatus.PASSED:
        print("\n✓ 绿阶段成功：所有测试通过")
    
    return result


def example_blue_phase():
    print("\n" + "="*80)
    print("示例3: 蓝阶段 - 重构优化")
    print("="*80)
    
    executor = TDDCycleExecutor(language=CodeLanguage.PYTHON)
    
    impl_file = Path("src/user_service.py")
    test_file = Path("tests/test_example.py")
    
    print(f"\n重构文件: {impl_file}")
    
    result = executor.execute_blue_phase(
        implementation_file=impl_file,
        test_file=test_file
    )
    
    print(f"\n蓝阶段结果:")
    print(f"  状态: {result.test_status.value}")
    print(f"  改进项数: {len(result.improvements)}")
    print(f"  重构建议数: {len(result.refactoring_suggestions)}")
    print(f"  质量改进数: {len(result.quality_improvements)}")
    
    if result.refactoring_suggestions:
        print(f"\n重构建议:")
        for i, suggestion in enumerate(result.refactoring_suggestions[:3], 1):
            print(f"  {i}. {suggestion.description}")
            print(f"     影响: {suggestion.impact}")
    
    if result.code_metrics_before and result.code_metrics_after:
        print(f"\n代码质量指标变化:")
        print(f"  圈复杂度: {result.code_metrics_before.cyclomatic_complexity} → {result.code_metrics_after.cyclomatic_complexity}")
        print(f"  可维护性指数: {result.code_metrics_before.maintainability_index:.2f} → {result.code_metrics_after.maintainability_index:.2f}")
        print(f"  代码重复率: {result.code_metrics_before.duplication_percentage:.2f}% → {result.code_metrics_after.duplication_percentage:.2f}%")
    
    if result.test_status == TestStatus.PASSED:
        print("\n✓ 蓝阶段成功：重构后测试仍通过")
    
    return result


def example_full_cycle():
    print("\n" + "="*80)
    print("示例4: 完整TDD循环")
    print("="*80)
    
    executor = TDDCycleExecutor(
        test_command="pytest",
        test_dir=Path("tests"),
        source_dir=Path("src"),
        coverage_threshold=80.0,
        language=CodeLanguage.PYTHON
    )
    
    class MockSpec:
        class Metadata:
            id = "SPEC-001"
            name = "UserService"
            version = "1.0.0"
        
        metadata = Metadata()
        attributes = []
        endpoints = []
        scenarios = []
    
    spec = MockSpec()
    test_file = Path("tests/test_user_service.py")
    impl_file = Path("src/user_service.py")
    test_cases = ["test_create_user", "test_get_user", "test_update_user", "test_delete_user"]
    
    impl_code = '''
"""用户服务实现"""

from typing import Optional
from skillscripts.core.path_config_center import get_path_config


class UserService:
    """用户服务类"""
    
    def __init__(self):
        self.users = {}
        self.next_id = 1
    
    def create(self, data: dict) -> dict:
        user_id = self.next_id
        self.users[user_id] = {"id": user_id, **data}
        self.next_id += 1
        return self.users[user_id]
    
    def get_by_id(self, user_id: int) -> Optional[dict]:
        return self.users.get(user_id)
    
    def update(self, user_id: int, data: dict) -> Optional[dict]:
        if user_id not in self.users:
            return None
        self.users[user_id].update(data)
        return self.users[user_id]
    
    def delete(self, user_id: int) -> bool:
        if user_id not in self.users:
            return False
        del self.users[user_id]
        return True
'''
    
    print(f"\n规范ID: {spec.metadata.id}")
    print(f"规范名称: {spec.metadata.name}")
    print(f"测试用例数: {len(test_cases)}")
    
    result = executor.execute_full_cycle(
        spec=spec,
        test_file=test_file,
        implementation_file=impl_file,
        test_cases=test_cases,
        implementation_code=impl_code,
        test_template="unit_test"
    )
    
    print(f"\n完整循环结果:")
    print(f"  循环ID: {result.cycle_id}")
    print(f"  成功: {result.success}")
    print(f"  完整: {result.is_complete}")
    print(f"  总耗时: {result.total_duration:.2f}秒")
    
    verification = executor.verify_cycle_integrity(result)
    print(f"\n循环完整性验证:")
    print(f"  有效: {verification['is_valid']}")
    for check in verification['checks']:
        print(f"    {check}")
    
    report_file = executor.save_cycle_report(result, Path("reports"))
    print(f"\n报告已保存: {report_file}")
    
    return result


def example_test_templates():
    print("\n" + "="*80)
    print("示例5: 测试模板使用")
    print("="*80)
    
    executor = TDDCycleExecutor(language=CodeLanguage.PYTHON)
    
    print("\n可用的测试模板:")
    for template_name, template in executor.TEST_TEMPLATES.items():
        print(f"\n  {template_name}:")
        print(f"    类型: {template.test_type}")
        print(f"    描述: {template.description}")
        print(f"    参数: {list(template.parameters.keys())}")


def example_implementation_patterns():
    print("\n" + "="*80)
    print("示例6: 实现模式")
    print("="*80)
    
    executor = TDDCycleExecutor(language=CodeLanguage.PYTHON)
    
    print("\n可用的实现模式 (Python):")
    patterns = executor.IMPLEMENTATION_PATTERNS.get(CodeLanguage.PYTHON, {})
    for pattern_name, pattern_code in patterns.items():
        print(f"\n  {pattern_name}:")
        print(f"    {pattern_code[:100]}...")


def main():
    print("\n" + "="*80)
    print("TDD红绿蓝循环执行器 - 使用示例")
    print("="*80)
    
    print("\n本示例展示完善后的TDD执行器功能:")
    print("1. 红阶段：增强的测试生成和模板支持")
    print("2. 绿阶段：代码实现引导和多语言支持")
    print("3. 蓝阶段：重构建议和代码质量检查")
    print("4. 完整循环：循环完整性验证和报告生成")
    
    print("\n注意：这些示例仅展示API用法，实际运行需要:")
    print("- 安装pytest: pip install pytest")
    print("- 创建相应的测试和实现文件")
    print("- 配置正确的文件路径")
    
    example_test_templates()
    example_implementation_patterns()
    
    print("\n" + "="*80)
    print("示例完成")
    print("="*80)
    
    print("\n更多使用方法:")
    print("  python tdd_cycle_executor.py --help")
    print("  python tdd_cycle_executor.py --test-file tests/test.py --impl-file src/impl.py --phase red")


if __name__ == "__main__":
    main()
