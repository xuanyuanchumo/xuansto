#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自演化四大能力集成测试 - Integration Test for Four Core Capabilities

验证自迭代、自优化、自修复、自完善四大核心能力的闭环协同工作。

测试场景:
1. 自迭代能力：问题预测和优先级排序
2. 自优化能力：策略选择和A/B对比
3. 自修复能力：规则匹配和编码修复
4. 自完善能力：知识共享和学习

集成流程:
    问题检测 → 预测分析 → 优化方案生成 → 修复执行 → 知识积累 → 持续改进
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))
sys.path.insert(0, str(script_dir.parent))

import importlib.util

def load_module_directly(module_name, file_path):
    """直接加载模块，避免包初始化问题"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

core_dir = script_dir / "core"
opt_dir = script_dir / "optimization"
repair_dir = script_dir / "auto_repair"
learn_dir = script_dir / "learning"

intelligent_auto_iteration = load_module_directly(
    "intelligent_auto_iteration",
    core_dir / "intelligent_auto_iteration.py"
)
IntelligentProblemPredictor = intelligent_auto_iteration.IntelligentProblemPredictor
MultiStrategyOptimizer = intelligent_auto_iteration.MultiStrategyOptimizer
PrioritySorter = intelligent_auto_iteration.PrioritySorter

enhanced_auto_optimization = load_module_directly(
    "enhanced_auto_optimization",
    opt_dir / "enhanced_auto_optimization.py"
)
ExtendedStrategyLibrary = enhanced_auto_optimization.ExtendedStrategyLibrary
ABTestFramework = enhanced_auto_optimization.ABTestFramework
SmartRollbackManager = enhanced_auto_optimization.SmartRollbackManager

comprehensive_auto_repair = load_module_directly(
    "comprehensive_auto_repair",
    repair_dir / "comprehensive_auto_repair.py"
)
ExtendedFixRuleLibrary = comprehensive_auto_repair.ExtendedFixRuleLibrary
EnhancedDocEncodingFixer = comprehensive_auto_repair.EnhancedDocEncodingFixer

enhanced_self_improvement = load_module_directly(
    "enhanced_self_improvement",
    learn_dir / "enhanced_self_improvement.py"
)
CrossProjectKnowledgeBase = enhanced_self_improvement.CrossProjectKnowledgeBase
EnhancedBestPracticeExtractor = enhanced_self_improvement.EnhancedBestPracticeExtractor
FailurePatternLearner = enhanced_self_improvement.FailurePatternLearner
StandardizedKnowledge = enhanced_self_improvement.StandardizedKnowledge
KnowledgeCategory = enhanced_self_improvement.KnowledgeCategory
KnowledgeSource = enhanced_self_improvement.KnowledgeSource


def test_intelligent_problem_predictor():
    """测试1: 智能问题预测器"""
    print("\n" + "="*60)
    print("测试1: 智能问题预测器 (IntelligentProblemPredictor)")
    print("="*60)

    predictor = IntelligentProblemPredictor()

    historical_data = [
        {
            'issue_type': 'performance_degradation',
            'description': 'API响应时间增加',
            'timestamp': (datetime.now() - timedelta(days=5)).isoformat(),
            'severity': 'high',
            'resolved': True,
            'resolution_time_hours': 4,
            'affected_modules': ['api', 'database'],
            'root_cause': '数据库查询未优化'
        },
        {
            'issue_type': 'memory_leak',
            'description': '内存使用持续增长',
            'timestamp': (datetime.now() - timedelta(days=3)).isoformat(),
            'severity': 'critical',
            'resolved': True,
            'resolution_time_hours': 8,
            'affected_modules': ['worker', 'cache'],
            'root_cause': '对象未正确释放'
        },
        {
            'issue_type': 'memory_leak',
            'description': '又发现内存泄漏',
            'timestamp': (datetime.now() - timedelta(days=1)).isoformat(),
            'severity': 'critical',
            'resolved': False,
            'resolution_time_hours': 0,
            'affected_modules': ['scheduler'],
            'root_cause': '定时任务资源泄漏'
        },
        {
            'issue_type': 'error_rate_increase',
            'description': '错误率上升',
            'timestamp': (datetime.now() - timedelta(days=2)).isoformat(),
            'severity': 'medium',
            'resolved': True,
            'resolution_time_hours': 2,
            'affected_modules': ['auth'],
            'root_cause': 'token过期处理不当'
        },
        {
            'issue_type': 'security_vulnerability',
            'description': 'XSS漏洞',
            'timestamp': (datetime.now() - timedelta(days=10)).isoformat(),
            'severity': 'critical',
            'resolved': True,
            'resolution_time_hours': 6,
            'affected_modules': ['frontend'],
            'root_cause': '输出未转义'
        }
    ]

    predictions = predictor.predict_issues(historical_data, time_window_days=30)

    print(f"\n✅ 预测结果: 共生成 {len(predictions)} 个预测")
    for i, pred in enumerate(predictions[:5], 1):
        print(f"  {i}. [{pred.severity.value.upper()}] {pred.issue_type}")
        print(f"     概率: {pred.probability:.1%} | 置信度: {pred.confidence:.1%}")
        print(f"     建议: {pred.suggested_prevention[:80]}...")

    patterns = predictor.analyze_patterns(historical_data)
    print(f"\n✅ 模式分析: 发现 {len(patterns)} 种问题模式")

    assert len(predictions) > 0, "应该生成预测"
    assert len(patterns) > 0, "应该识别模式"

    print("✅ 测试1通过: 智能问题预测器工作正常\n")
    return True


def test_multi_strategy_optimizer():
    """测试2: 多策略协同优化方案生成器"""
    print("\n" + "="*60)
    print("测试2: 多策略协同优化方案生成器 (MultiStrategyOptimizer)")
    print("="*60)

    optimizer = MultiStrategyOptimizer()

    problem = {
        'problem_type': 'performance',
        'description': '系统响应时间过长，需要性能优化',
        'severity': 'high',
        'affected_metrics': ['response_time', 'throughput', 'cpu_usage'],
        'current_state': {'avg_response_time': 500, 'throughput': 100},
        'target_state': {'avg_response_time': 200, 'throughput': 300}
    }

    context = {
        'team_experience': 'senior',
        'has_testing_framework': True,
        'has_ci_cd': True,
        'urgency': 'high'
    }

    plans = optimizer.generate_optimization_plan(problem, context=context)

    print(f"\n✅ 优化方案: 为 '{problem['problem_type']}' 问题生成 {len(plans)} 个方案")

    for i, plan in enumerate(plans, 1):
        improvements = ', '.join([f"{k}:+{v:.0%}" for k, v in plan.expected_improvement.items()])
        print(f"  {i}. [{plan.strategy}] {plan.description[:40]}...")
        print(f"     优先级: {plan.priority_score:.1f} | 成功率: {plan.success_probability:.0%}")
        print(f"     预期改进: {improvements}")

    report = optimizer.generate_optimization_report(plans)
    print(f"\n✅ 报告生成: {len(report)} 字符")

    assert len(plans) > 0, "应该生成优化方案"

    print("✅ 测试2通过: 多策略优化器工作正常\n")
    return True


def test_priority_sorter():
    """测试3: 四维优先级排序器"""
    print("\n" + "="*60)
    print("测试3: 四维优先级排序器 (PrioritySorter)")
    print("="*60)

    sorter = PrioritySorter()

    tasks = [
        {'task_id': 'TASK-001', 'title': '修复安全漏洞', 'value': 95, 'cost': 30, 'risk': 20, 'dependency_complexity': 10},
        {'task_id': 'TASK-002', 'title': '性能优化', 'value': 80, 'cost': 50, 'risk': 40, 'dependency_complexity': 30},
        {'task_id': 'TASK-003', 'title': '代码重构', 'value': 60, 'cost': 70, 'risk': 30, 'dependency_complexity': 50},
        {'task_id': 'TASK-004', 'title': '文档更新', 'value': 40, 'cost': 20, 'risk': 10, 'dependency_complexity': 5},
        {'task_id': 'TASK-005', 'title': '添加单元测试', 'value': 70, 'cost': 40, 'risk': 15, 'dependency_complexity': 20},
    ]

    sorted_tasks = sorter.sort_tasks(tasks)

    print(f"\n✅ 排序结果: {len(sorted_tasks)} 个任务已排序")
    print(f"\n{'排名':<6}{'任务ID':<12}{'标题':<20}{'价值':<8}{'成本':<8}{'风险':<8}{'依赖':<8}{'总分':<8}")
    print("-" * 80)

    for task in sorted_tasks:
        print(
            f"{task.rank:<6}{task.task_id:<12}{task.title:<20}"
            f"{task.value_score:<8.0f}{task.cost_score:<8.0f}"
            f"{task.risk_score:<8.0f}{task.dependency_score:<8.0f}"
            f"{task.final_priority:<8.1f}"
        )

    assert sorted_tasks[0].task_id == 'TASK-001', "高价值低风险任务应该排在前面"
    assert sorted_tasks[-1].final_priority < sorted_tasks[0].final_priority, "应该按优先级降序排列"

    sorter.adjust_weights_for_context('urgent')
    print(f"\n✅ 权重调整: 已针对'紧急'上下文调整权重")

    print("✅ 测试3通过: 优先级排序器工作正常\n")
    return True


def test_extended_strategy_library():
    """测试4: 扩展优化策略库"""
    print("\n" + "="*60)
    print("测试4: 扩展优化策略库 (ExtendedStrategyLibrary)")
    print("="*60)

    library = ExtendedStrategyLibrary()

    all_strategies = library.get_all_strategies()
    print(f"\n✅ 策略总数: {len(all_strategies)} 个")

    perf_strategies = library.get_strategies_by_category('performance')
    print(f"✅ 性能优化策略: {len(perf_strategies)} 个")

    high_impact = library.get_strategies_by_impact('high')
    print(f"✅ 高影响策略: {len(high_impact)} 个")

    recommendations = library.recommend_strategies("数据库查询慢，需要缓存优化", max_recommendations=3)
    print(f"\n✅ 推荐策略 (数据库查询优化):")
    for strategy, score in recommendations:
        print(f"  - {strategy.name}: 匹配度={score:.1f}")

    stats = library.get_statistics()
    print(f"\n📊 策略库统计:")
    print(f"  总计: {stats['total_strategies']} 条")
    print(f"  分类: {json.dumps(stats['by_category'], ensure_ascii=False)}")
    print(f"  可自动修复: {stats['auto_fixable_count']} 条 ({stats['auto_fixable_rate']})")

    assert len(all_strategies) >= 20, "应该有至少20个策略"

    print("✅ 测试4通过: 扩展策略库工作正常\n")
    return True


def test_ab_test_framework():
    """测试5: A/B测试框架"""
    print("\n" + "="*60)
    print("测试5: A/B测试框架 (ABTestFramework)")
    print("="*60)

    ab_test = ABTestFramework(confidence_level=0.95)

    control_group = [100, 102, 98, 101, 99, 103, 97, 100, 102, 98,
                     101, 99, 100, 98, 102, 97, 103, 99, 101, 100,
                     98, 102, 99, 101, 100, 97, 103, 98, 102, 99]

    test_group_improved = [85, 87, 83, 86, 84, 88, 82, 85, 87, 83,
                           86, 84, 85, 83, 88, 82, 86, 84, 87, 85,
                           83, 87, 84, 86, 85, 82, 88, 83, 87, 84]

    test_group_worse = [115, 117, 113, 116, 114, 118, 112, 115, 117, 113,
                        116, 114, 115, 113, 118, 112, 116, 114, 117, 115,
                        113, 117, 114, 116, 115, 112, 118, 113, 117, 114]

    result_good = ab_test.run_comparison(control_group, test_group_improved, metric_name="response_time_ms")
    result_bad = ab_test.run_comparison(control_group, test_group_worse, metric_name="response_time_ms")

    print(f"\n✅ A/B测试结果 (正向改进):")
    print(f"  对照组均值: {result_good.control_mean:.2f}")
    print(f"  测试组均值: {result_good.test_mean:.2f}")
    print(f"  改进幅度: {result_good.improvement_percentage:+.1f}%")
    print(f"  P值: {result_good.p_value:.6f}")
    print(f"  显著性: {'是' if result_good.is_significant else '否'}")
    print(f"  决策: {result_good.decision.value}")
    print(f"  推荐: {result_good.recommendation}")

    print(f"\n✅ A/B测试结果 (负向影响):")
    print(f"  决策: {result_bad.decision.value}")
    print(f"  推荐: {result_bad.recommendation}")

    assert result_good.is_significant or result_bad.is_significant, "至少一个测试应该是显著的"

    print("✅ 测试5通过: A/B测试框架工作正常\n")
    return True


def test_smart_rollback_manager():
    """测试6: 智能回滚决策管理器"""
    print("\n" + "="*60)
    print("测试6: 智能回滚决策管理器 (SmartRollbackManager)")
    print("="*60)

    rollback_mgr = SmartRollbackManager()

    metrics_before = {
        'error_rate': 0.01,
        'response_time': 200,
        'throughput': 1000,
        'cpu_usage': 45,
        'memory_usage': 60
    }

    test_cases = [
        ('轻微退化', {'error_rate': 0.02, 'response_time': 220, 'throughput': 950, 'cpu_usage': 50, 'memory_usage': 65}),
        ('中度退化', {'error_rate': 0.05, 'response_time': 350, 'throughput': 800, 'cpu_usage': 65, 'memory_usage': 75}),
        ('严重退化', {'error_rate': 0.15, 'response_time': 800, 'throughput': 400, 'cpu_usage': 90, 'memory_usage': 95}),
    ]

    for name, metrics_after in test_cases:
        decision = rollback_mgr.decide_rollback(metrics_before, metrics_after)

        print(f"\n📊 场景: {name}")
        print(f"  回滚策略: {decision.strategy.value}")
        print(f"  退化等级: {decision.degradation_level}")
        print(f"  原因: {decision.reason}")
        print(f"  置信度: {decision.confidence:.1%}")
        print(f"  预计恢复时间: {decision.estimated_recovery_time_minutes}分钟")
        print(f"  执行步骤数: {len(decision.steps)}")

    decision_critical = rollback_mgr.decide_rollback(
        metrics_before,
        {'error_rate': 0.25, 'response_time': 1500, 'throughput': 200}
    )
    assert decision_critical.strategy.value == 'immediate', "严重退化应立即回滚"

    print("✅ 测试6通过: 智能回滚管理器工作正常\n")
    return True


def test_extended_fix_rule_library():
    """测试7: 扩展修复规则库"""
    print("\n" + "="*60)
    print("测试7: 扩展修复规则库 (ExtendedFixRuleLibrary)")
    print("="*60)

    rule_library = ExtendedFixRuleLibrary()

    all_rules = rule_library.get_all_rules()
    print(f"\n✅ 规则总数: {len(all_rules)} 条")

    code_rules = rule_library.get_rules_by_category('code')
    doc_rules = rule_library.get_rules_by_category('document')
    config_rules = rule_library.get_rules_by_category('config')
    path_rules = rule_library.get_rules_by_category('path')
    dep_rules = rule_library.get_rules_by_category('dependency')

    print(f"  代码修复规则: {len(code_rules)} 条")
    print(f"  文档修复规则: {len(doc_rules)} 条")
    print(f"  配置修复规则: {len(config_rules)} 条")
    print(f"  路径修复规则: {len(path_rules)} 条")
    print(f"  依赖修复规则: {len(dep_rules)} 条")

    critical_rules = rule_library.get_rules_by_severity('critical')
    auto_fixable = rule_library.get_auto_fixable_rules()
    print(f"\n  严重规则: {len(critical_rules)} 条")
    print(f"  可自动修复: {len(auto_fixable)} 条")

    test_content = """
    def query_user(user_id):
        sql = f"SELECT * FROM users WHERE id = {user_id}"
        return execute(sql)  # SQL注入风险

    password = "admin123"  # 硬编码密码
    """

    matching_rules = rule_library.find_matching_rules(test_content, '.py')
    print(f"\n✅ 规则匹配测试:")
    for rule, score in matching_rules[:5]:
        print(f"  - {rule.rule_id}: {rule.description} (匹配度: {score:.1f})")

    stats = rule_library.get_statistics()
    print(f"\n📊 规则库统计:")
    print(f"  总计: {stats['total_rules']} 条")
    print(f"  自动修复率: {stats['auto_fixable_rate']}")

    total = len(code_rules) + len(doc_rules) + len(config_rules) + len(path_rules) + len(dep_rules)
    assert total >= 100, f"应该有至少100条规则，实际{total}"

    print("✅ 测试7通过: 扩展修复规则库工作正常\n")
    return True


def test_enhanced_doc_encoding_fixer():
    """测试8: 增强文档编码修复器"""
    print("\n" + "="*60)
    print("测试8: 增强文档编码修复器 (EnhancedDocEncodingFixer)")
    print("="*60)

    fixer = EnhancedDocEncodingFixer()

    with tempfile.NamedTemporaryFile(mode='wb', suffix='.md', delete=False, encoding=None) as f:
        temp_path = f.name

        test_contents = [
            (b'# \xe6\xb5\x8b\xe8\xaf\x95\xe6\x96\x87\xe6\xa1\xa3\n\n\xe8\xbf\x99\xe6\x98\xaf\xe4\xb8\xad\xe6\x96\x87\xe5\x86\x85\xe5\xae\xb9\n', 'UTF-8中文'),
            (b'\xef\xbb\xbf# BOM Test\nThis file has BOM\n', 'BOM标记'),
        ]

        content_bytes, desc = test_contents[0]
        f.write(content_bytes)
        f.flush()

        result = fixer.detect_and_fix(temp_path)

        print(f"\n✅ 编码修复测试 ({desc}):")
        print(f"  文件: {Path(result.file_path).name}")
        print(f"  原始编码: {result.original_encoding}")
        print(f"  检测编码: {result.detected_encoding}")
        print(f"  修复后编码: {result.fixed_encoding}")
        print(f"  有BOM: {result.had_bom}")
        print(f"  乱码字符: {result.garbled_chars_found} 个 (已修复 {result.garbled_chars_fixed})")
        print(f"  成功: {result.success}")
        print(f"  详情: {result.details}")

    try:
        os.unlink(temp_path)
    except:
        pass

    assert result.success, "编码修复应该成功"

    print("✅ 测试8通过: 文档编码修复器工作正常\n")
    return True


def test_cross_project_knowledge_base():
    """测试9: 跨项目知识库"""
    print("\n" + "="*60)
    print("测试9: 跨项目知识库 (CrossProjectKnowledgeBase)")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        kb = CrossProjectKnowledgeBase(storage_path=tmpdir)
        initialized = kb.initialize()

        assert initialized, "知识库应该初始化成功"

        knowledge1 = StandardizedKnowledge(
            id="KB-TEST-001",
            title="微服务架构最佳实践",
            category=KnowledgeCategory.ARCHITECTURE,
            project="project-alpha",
            version="1.0",
            content="采用领域驱动设计(DDD)划分服务边界...",
            tags=["microservice", "architecture", "DDD"],
            source=KnowledgeSource.AUTO_EXTRACTED,
            effectiveness=0.85,
            usage_count=15
        )

        knowledge2 = StandardizedKnowledge(
            id="KB-TEST-002",
            title="Redis缓存优化技巧",
            category=KnowledgeCategory.PERFORMANCE,
            project="project-beta",
            version="1.0",
            content="使用Redis Cluster实现分布式缓存...",
            tags=["redis", "cache", "performance"],
            source=KnowledgeSource.MANUAL,
            effectiveness=0.92,
            usage_count=28
        )

        add_result1 = kb.add_knowledge(knowledge1)
        add_result2 = kb.add_knowledge(knowledge2)

        print(f"\n✅ 知识添加: KB-001={add_result1}, KB-002={add_result2}")

        share_result = kb.share_knowledge("KB-TEST-001", ["project-gamma", "project-delta"])
        print(f"✅ 知识共享: {share_result}")

        search_results = kb.query_knowledge("缓存 性能", limit=5)
        print(f"\n✅ 知识查询 ('缓存 性能'): 找到 {len(search_results)} 条")
        for item in search_results:
            print(f"  - [{item.category.value}] {item.title} (有效性: {item.effectiveness:.0%})")

        similar_projects = kb.query_similar_projects("架构设计", "project-gamma")
        print(f"\n✅ 相似项目经验: 找到 {len(similar_projects)} 条")

        record_result = kb.record_usage("KB-TEST-002", success=True, feedback="非常有用")
        print(f"✅ 使用记录: {record_result}")

        stats = kb.get_statistics()
        print(f"\n📊 知识库统计:")
        print(f"  总知识数: {stats['total_knowledge']}")
        print(f"  高质量知识: {stats['high_effective_count']} 条")
        print(f"  平均有效性: {stats['avg_effectiveness']:.1%}")
        print(f"  总使用次数: {stats['total_usage_count']}")

        assert len(search_results) > 0, "应该能搜索到知识"

    print("✅ 测试9通过: 跨项目知识库工作正常\n")
    return True


def test_best_practice_extractor():
    """测试10: 最佳实践提取器"""
    print("\n" + "="*60)
    print("测试10: 最佳实践提取器 (EnhancedBestPracticeExtractor)")
    print("="*60)

    extractor = EnhancedBestPracticeExtractor()

    case_data = {
        'case_id': 'CASE-2024-001',
        'title': '电商平台性能优化项目',
        'description': '对电商平台进行全面的性能优化',
        'problem_solved': '页面加载时间从5秒降低到1.5秒',
        'solution_description': '''
        实施了以下优化措施：
        1. 引入Redis缓存层，缓存热点数据
        2. 数据库查询优化，添加索引和使用批量查询
        3. 使用CDN加速静态资源加载
        4. 实现异步非阻塞的API调用
        ''',
        'results': {
            'page_load_time_before': 5000,
            'page_load_time_after': 1500,
            'throughput_before': 100,
            'throughput_after': 400
        },
        'lessons_learned': [
            '缓存是提升性能最有效的手段之一',
            '数据库优化需要结合具体业务场景',
            '监控和基线数据对于评估优化效果至关重要'
        ],
        'metrics_before': {'response_time': 5000, 'throughput': 100, 'error_rate': 0.05},
        'metrics_after': {'response_time': 1500, 'throughput': 400, 'error_rate': 0.01},
        'challenges_overcome': [
            '缓存一致性维护困难',
            '旧代码重构风险高',
            '团队对新技术的学习曲线'
        ],
        'technologies_used': ['Redis', 'MySQL', 'Nginx', 'CDN', 'Python'],
        'duration_days': 45
    }

    practices = extractor.extract_from_success_case(case_data)

    print(f"\n✅ 提取结果: 从案例中提取了 {len(practices)} 条最佳实践")

    for i, practice in enumerate(practices, 1):
        print(f"\n  {i}. [{practice.dimension.value}] {practice.title[:50]}...")
        print(f"     有效性: {practice.effectiveness_score:.1%} | 难度: {practice.difficulty_level}/10")
        print(f"     状态: {practice.validity.value}")
        if practice.benefits:
            print(f"     收益: {', '.join(practice.benefits[:3])}")

    is_valid, message = extractor.validate_practice(practices[0]) if practices else (False, "无实践")
    print(f"\n✅ 验证结果: {message}")

    stats = extractor.get_extraction_statistics()
    print(f"\n📊 提取统计:")
    print(f"  总实践数: {stats['total_practices_extracted']}")
    print(f"  平均有效性: {stats['avg_effectiveness']:.1%}")
    print(f"  验证通过率: {stats['validation_pass_rate']:.1%}")

    assert len(practices) > 0, "应该提取到最佳实践"

    print("✅ 测试10通过: 最佳实践提取器工作正常\n")
    return True


def test_failure_pattern_learner():
    """测试11: 失败模式学习器"""
    print("\n" + "="*60)
    print("测试11: 失败模式学习器 (FailurePatternLearner)")
    print("="*60)

    learner = FailurePatternLearner()

    failure_case = {
        'failure_id': 'FAIL-2024-001',
        'title': '生产环境数据库连接池耗尽',
        'description': '高峰期数据库连接池耗尽导致服务不可用',
        'severity': 'critical',
        'category': 'performance',
        'symptoms': [
            '数据库连接超时错误激增',
            'API响应时间从200ms增加到30秒',
            '用户请求大量失败'
        ],
        'timeline': [
            '09:00 开始出现偶发超时',
            '10:00 错误率上升到5%',
            '11:00 服务完全不可用'
        ],
        'root_cause_analysis': '连接池配置过小，且存在连接泄漏，高并发下连接无法及时释放',
        'impact': {
            'downtime_minutes': 120,
            'affected_users': 50000,
            'revenue_loss': 50000
        },
        'resolution': '增大连接池大小，修复连接泄漏bug，添加连接池监控',
        'lessons_learned': [
            '连接池大小应根据压测结果设置',
            '必须监控连接池使用率',
            '需要设置连接超时和获取超时'
        ],
        'preventive_measures_taken': [
            '实施连接池监控告警',
            '定期进行压力测试',
            '代码审查关注资源释放'
        ],
        'detected_at': '2024-03-15T11:00:00',
        'resolved_at': '2024-03-15T13:00:00',
        'related_systems': ['user-service', 'order-service', 'payment-service'],
        'environment_context': {
            'environment': 'production',
            'db_type': 'PostgreSQL',
            'max_connections': 100,
            'peak_qps': 5000
        }
    }

    learning_result = learner.learn_from_failure(failure_case)

    print(f"\n✅ 学习结果:")
    print(f"  失败ID: {learning_result['failure_id']}")
    print(f"  识别模式: {learning_result['pattern']['name']}")
    print(f"  学习置信度: {learning_result['learning_confidence']:.1%}")
    print(f"  相似案例: {learning_result['similar_cases_found']} 个")

    prevention_rule = learning_result['prevention_rule']
    print(f"\n  生成的预防规则:")
    print(f"    规则ID: {prevention_rule['rule_id']}")
    print(f"    行动: {', '.join(prevention_rule['actions'][:3])}")

    current_state = {
        'metrics': {
            'db_connection_pool_usage': 0.85,
            'active_connections': 90,
            'max_connections': 100
        },
        'recent_errors': [
            'Database connection timeout',
            'Connection pool exhausted warning'
        ],
        'system_health': 'degraded',
        'active_alerts': ['HIGH: DB connection pool at 85%']
    }

    warnings = learner.check_prevention(current_state)

    print(f"\n⚠️ 预防警告检查: 发现 {len(warnings)} 个潜在风险")
    for warning in warnings:
        print(f"  - [{warning.severity.upper()}] {warning.message}")
        print(f"    置信度: {warning.confidence:.1%}")
        print(f"    触发条件: {', '.join(warning.triggered_by[:2])}")

    stats = learner.get_pattern_statistics()
    print(f"\n📊 学习统计:")
    print(f"  识别的模式数: {stats['total_patterns_identified']}")
    print(f"  分析的失败案例: {stats['total_failures_analyzed']}")
    print(f"  生成的预防规则: {stats['total_prevention_rules_generated']}")

    assert learning_result['pattern']['name'] != 'Unknown Pattern', "应该识别出已知模式"

    print("✅ 测试11通过: 失败模式学习器工作正常\n")
    return True


def run_integration_test():
    """运行完整的集成测试"""
    print("\n" + "#"*70)
    print("#" + " "*68 + "#")
    print("#" + "  自演化四大能力集成测试 - Integration Test Suite".center(66) + "#")
    print("#" + " "*68 + "#")
    print("#"*70)

    tests = [
        ("智能问题预测器", test_intelligent_problem_predictor),
        ("多策略优化器", test_multi_strategy_optimizer),
        ("四维优先级排序器", test_priority_sorter),
        ("扩展策略库", test_extended_strategy_library),
        ("A/B测试框架", test_ab_test_framework),
        ("智能回滚管理器", test_smart_rollback_manager),
        ("扩展修复规则库", test_extended_fix_rule_library),
        ("文档编码修复器", test_enhanced_doc_encoding_fixer),
        ("跨项目知识库", test_cross_project_knowledge_base),
        ("最佳实践提取器", test_best_practice_extractor),
        ("失败模式学习器", test_failure_pattern_learner),
    ]

    results = []
    start_time = datetime.now()

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, True, None))
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"❌ 测试失败: {name}")
            print(f"   错误: {e}\n")

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("\n" + "#"*70)
    print("#" + " "*68 + "#")
    print("#" + "  测试报告汇总".center(66) + "#")
    print("#" + " "*68 + "#")
    print("#"*70)

    passed = sum(1 for _, success, _ in results if success)
    failed = len(results) - passed

    print(f"\n{'测试名称':<25}{'状态':<10}{'备注'}")
    print("-" * 60)

    for name, success, error in results:
        status = "✅ 通过" if success else "❌ 失败"
        note = error[:40] if error else ""
        print(f"{name:<25}{status:<10}{note}")

    print(f"\n{'='*60}")
    print(f"总计: {len(results)} 个测试 | 通过: {passed} | 失败: {failed}")
    print(f"总耗时: {duration:.2f} 秒")
    print(f"通过率: {passed/len(results)*100:.1f}%")
    print(f"完成时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

    if failed == 0:
        print("\n🎉 所有测试通过！自演化四大能力闭环验证成功！")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查上述错误信息")

    print("#"*70 + "\n")

    return failed == 0


if __name__ == '__main__':
    success = run_integration_test()
    sys.exit(0 if success else 1)
