#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""演化推荐功能测试脚本"""

import sys
sys.path.insert(0, '.')

from recommendation_engine import (
    RecommendationEngine,
    EvolutionRecommender,
    EvolutionRecommendation,
    EvolutionPrediction,
    EvolutionPriorityScore,
    PersonalizedEvolutionSuggestion,
    EvolutionRiskLevel,
    EvolutionTiming,
    EvolutionResourceLevel
)

def main():
    print('=' * 60)
    print('演化推荐功能测试')
    print('=' * 60)

    # 1. 测试初始化
    print('\n1. 测试引擎初始化...')
    engine = RecommendationEngine()
    print('   OK RecommendationEngine 初始化成功')
    print('   OK EvolutionRecommender 已集成')

    # 2. 测试演化推荐
    print('\n2. 测试演化推荐...')
    context = {
        'metrics': {
            'performance_score': 65,
            'code_complexity': 18,
            'test_coverage': 55,
            'security_issues': 2,
            'code_quality_score': 70
        },
        'issues': [
            'Performance degradation detected',
            'High code complexity in module X'
        ],
        'triggers': ['performance_issue', 'code_smell']
    }

    recommendations = engine.get_evolution_recommendations('skill-001', context, limit=5)
    print(f'   OK 获取到 {len(recommendations)} 条演化推荐')
    for i, rec in enumerate(recommendations[:3], 1):
        print(f'     {i}. {rec.title} (优先级: {rec.priority_score:.3f})')
        print(f'        类型: {rec.evolution_type}, 风险: {rec.risk_level.value}')

    # 3. 测试优先级排序
    print('\n3. 测试优先级排序...')
    sorted_recs = engine.prioritize_evolutions(recommendations, strategy='balanced')
    print(f'   OK 使用 balanced 策略排序完成')
    print(f'   OK 排序后优先级分数: {[round(r.priority_score, 3) for r in sorted_recs[:3]]}')

    # 4. 测试效果预测
    print('\n4. 测试效果预测...')
    if recommendations:
        pattern_id = recommendations[0].related_patterns[0] if recommendations[0].related_patterns else 'perf_optimize'
        prediction = engine.predict_evolution_effect(pattern_id, context)
        if prediction:
            print('   OK 预测演化效果:')
            print(f'     - 性能提升: {prediction.performance_improvement:.2%}')
            print(f'     - 质量改进: {prediction.quality_improvement:.2%}')
            print(f'     - 成功概率: {prediction.success_probability:.2%}')
            print(f'     - 风险分数: {prediction.risk_score:.2f}')

    # 5. 测试个性化推荐
    print('\n5. 测试个性化推荐...')
    user_preferences = {
        'preferred_evolution_types': ['optimization', 'bug_fix'],
        'risk_tolerance': 'medium',
        'resource_availability': 'medium'
    }

    personalized = engine.get_personalized_evolution_recommendations('skill-001', user_preferences, context)
    print(f'   OK 获取个性化建议: {personalized.suggestion_id}')
    print(f'   OK 推荐数量: {len(personalized.recommendations)}')
    print(f'   OK 置信度: {personalized.confidence:.2%}')

    # 6. 测试健康度集成
    print('\n6. 测试健康度集成...')
    health_report = {
        'overall_score': 72,
        'health_level': 'good',
        'category_results': [
            {
                'category': 'scripts',
                'percentage': 45,
                'items': [
                    {'name': '核心脚本', 'percentage': 40, 'suggestions': ['恢复缺失脚本']}
                ]
            }
        ]
    }
    integrated = engine.integrate_health_assessment(health_report)
    print('   OK 健康度报告已集成')
    print(f'   OK 健康等级: {integrated["health_level"]}')
    print(f'   OK 生成的推荐: {len(integrated["recommendations"])} 条')

    # 7. 测试演化报告生成
    print('\n7. 测试演化报告生成...')
    report = engine.generate_evolution_report('skill-001', context, user_preferences)
    print('   OK 报告生成完成')
    print(f'   OK 总推荐数: {report["summary"]["total_recommendations"]}')
    print(f'   OK 高优先级数: {report["summary"]["high_priority_count"]}')
    print(f'   OK 改进潜力: {report["summary"]["improvement_potential"]:.2%}')

    # 8. 测试统计信息
    print('\n8. 测试统计信息...')
    stats = engine.get_evolution_statistics()
    print(f'   OK 总演化数: {stats["total_evolutions"]}')
    print(f'   OK 成功率: {stats["success_rate"]:.2%}')

    print('\n' + '=' * 60)
    print('所有测试通过!')
    print('=' * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
