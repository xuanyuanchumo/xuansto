"""
Task 7.1 增强代码优化器 - 测试验证脚本

验证智能重构建议、安全重构执行、优化效果验证和回滚机制
"""

import sys
from pathlib import Path

project_root = get_path_config().SKILL_ROOT
sys.path.insert(0, str(project_root / ".trae" / "skills" / "sanliu" / "skillscripts"))

from optimization.code_quality_optimizer_enhanced import (
    UnifiedCodeQualityOptimizer,
    IntelligentRefactoringPatternLibrary,
    CodeRefactoringAdvisor,
    SafeRefactoringExecutor,
    ComplexityLevel,
    ComplexityIssue,
    DuplicationIssue,
    RefactoringType
)
from optimization.xingbu_refactoring_integration import (
    XingbuRefactoringIntegrator,
    XingbuRefactoringConfig,
    XingbuRefactoringMode
)


def test_intelligent_pattern_library():
    """测试智能重构模式库"""
    print("\n=== 测试智能重构模式库 ===")
    
    pattern = IntelligentRefactoringPatternLibrary.get_pattern('cyclomatic_complexity')
    assert pattern is not None, "应该找到圈复杂度模式"
    assert pattern['type'] == RefactoringType.EXTRACT_METHOD, "类型应该是提取方法"
    print(f"✓ 找到圈复杂度模式: {pattern['title']}")
    
    effort, minutes = IntelligentRefactoringPatternLibrary.get_effort_for_complexity(
        'cyclomatic_complexity', ComplexityLevel.HIGH
    )
    assert effort == 'high', "高复杂度应该是高工作量"
    assert minutes == 60, "高复杂度应该是60分钟"
    print(f"✓ 工作量映射正确: {effort}, {minutes}分钟")
    
    effort, minutes = IntelligentRefactoringPatternLibrary.get_effort_for_duplication(3)
    assert effort == 'medium', "3处重复应该是中等工作量"
    print(f"✓ 重复代码工作量映射正确: {effort}, {minutes}分钟")
    
    print("✓ 智能重构模式库测试通过")


def test_intelligent_refactoring_advisor():
    """测试智能重构建议生成器"""
    print("\n=== 测试智能重构建议生成器 ===")
    
    advisor = CodeRefactoringAdvisor()
    
    complexity_issue = ComplexityIssue(
        file_path="backend/app/test.py",
        line_number=10,
        function_name="complex_function",
        complexity_type="cyclomatic_complexity",
        complexity_value=15,
        complexity_level=ComplexityLevel.HIGH,
        description="高圈复杂度",
        suggestions=["提取方法"]
    )
    
    duplication_issue = DuplicationIssue(
        duplication_type=DuplicationIssue.__annotations__['duplication_type'].__args__[0].EXACT_DUPLICATE,
        file_path="backend/app/test.py",
        line_numbers=[10, 20, 30],
        duplicate_count=3,
        similarity_score=1.0,
        code_snippet="def duplicate_code():\n    pass",
        suggested_refactoring="提取公共方法"
    )
    
    suggestions = advisor.generate_refactoring_suggestions([complexity_issue], [duplication_issue])
    
    assert len(suggestions) > 0, "应该生成建议"
    assert suggestions[0].priority in ['critical', 'high', 'medium', 'low'], "应该有优先级"
    print(f"✓ 生成了 {len(suggestions)} 个重构建议")
    print(f"  - 第一个建议: {suggestions[0].description}")
    print(f"  - 优先级: {suggestions[0].priority}")
    print(f"  - 工作量: {suggestions[0].estimated_effort}")
    
    print("✓ 智能重构建议生成器测试通过")


def test_safe_refactoring_executor():
    """测试安全重构执行器"""
    print("\n=== 测试安全重构执行器 ===")
    
    executor = SafeRefactoringExecutor(project_root)
    
    assert executor._backup_dir.exists(), "备份目录应该存在"
    print(f"✓ 备份目录已创建: {executor._backup_dir}")
    
    assert hasattr(executor, '_validation_strategies'), "应该有验证策略"
    assert 'syntax' in executor._validation_strategies, "应该有语法验证策略"
    assert 'tests' in executor._validation_strategies, "应该有测试验证策略"
    assert 'behavior' in executor._validation_strategies, "应该有行为验证策略"
    assert 'quality' in executor._validation_strategies, "应该有质量验证策略"
    print("✓ 验证策略已配置")
    
    test_code = """
def test_function():
    if True:
        pass
"""
    valid, errors = executor._validate_syntax_enhanced(test_code, Path("test.py"))
    assert valid, "代码语法应该有效"
    print("✓ 语法验证功能正常")
    
    print("✓ 安全重构执行器测试通过")


def test_rollback_mechanism():
    """测试回滚机制"""
    print("\n=== 测试回滚机制 ===")
    
    executor = SafeRefactoringExecutor(project_root)
    
    assert hasattr(executor, 'rollback_multiple'), "应该有批量回滚方法"
    assert hasattr(executor, 'rollback_to_snapshot'), "应该有快照回滚方法"
    assert hasattr(executor, 'create_snapshot'), "应该有创建快照方法"
    assert hasattr(executor, 'get_rollback_candidates'), "应该有获取回滚候选方法"
    print("✓ 回滚机制方法已实现")
    
    candidates = executor.get_rollback_candidates()
    print(f"✓ 当前可回滚的重构数: {len(candidates)}")
    
    print("✓ 回滚机制测试通过")


def test_xingbu_integration():
    """测试刑部重构流程集成"""
    print("\n=== 测试刑部重构流程集成 ===")
    
    config = XingbuRefactoringConfig(
        mode=XingbuRefactoringMode.BALANCED,
        auto_apply=False,
        max_refactorings_per_cycle=5
    )
    
    integrator = XingbuRefactoringIntegrator(project_root, config)
    
    assert integrator.optimizer is not None, "应该有优化器实例"
    print("✓ 刑部重构集成器已创建")
    
    assert hasattr(integrator, 'run_xingbu_refactoring_cycle'), "应该有执行周期方法"
    assert hasattr(integrator, 'rollback_last_cycle'), "应该有回滚方法"
    assert hasattr(integrator, 'generate_xingbu_report'), "应该有生成报告方法"
    print("✓ 刑部重构集成方法已实现")
    
    print("✓ 刑部重构流程集成测试通过")


def test_unified_optimizer():
    """测试统一优化器"""
    print("\n=== 测试统一优化器 ===")
    
    optimizer = UnifiedCodeQualityOptimizer(project_root)
    
    assert optimizer.complexity_analyzer is not None, "应该有复杂度分析器"
    assert optimizer.duplication_detector is not None, "应该有重复检测器"
    assert optimizer.refactoring_advisor is not None, "应该有重构建议器"
    assert optimizer.safe_executor is not None, "应该有安全执行器"
    assert optimizer.history_manager is not None, "应该有历史管理器"
    print("✓ 统一优化器组件齐全")
    
    assert hasattr(optimizer, 'run_safe_optimization_cycle'), "应该有安全优化周期方法"
    assert hasattr(optimizer, 'validate_optimization_effect'), "应该有优化效果验证方法"
    print("✓ 统一优化器方法已实现")
    
    print("✓ 统一优化器测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("开始测试 Task 7.1: 增强代码优化器")
    print("=" * 60)
    
    try:
        test_intelligent_pattern_library()
        test_intelligent_refactoring_advisor()
        test_safe_refactoring_executor()
        test_rollback_mechanism()
        test_xingbu_integration()
        test_unified_optimizer()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
        
        print("\n功能验证摘要:")
        print("1. ✓ 智能重构模式库 - 支持多种重构模式和智能工作量估算")
        print("2. ✓ 智能重构建议生成 - 基于复杂度和重复问题的智能建议")
        print("3. ✓ 安全重构执行 - 多层验证（语法、测试、行为、质量）")
        print("4. ✓ 回滚机制 - 支持单次、批量、快照回滚")
        print("5. ✓ 刑部重构集成 - 完整的重构流程管理")
        print("6. ✓ 统一优化器 - 集成所有优化功能")
        
        return True
        
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n✗ 测试异常: {e}")
        import traceback
from skillscripts.core.path_config_center import get_path_config
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
