#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动学习系统高级功能示例

演示新增的高级功能，包括：
- 模式演化跟踪
- 模式聚类分析
- 模式适用性预测
- 高级特征提取
- 实践关联分析
- 实践推荐引擎
- 知识图谱构建
- 知识关系推理
- 改进的去重算法
- 知识生命周期管理
"""

import sys
from pathlib import Path

sys.path.insert(0, str(get_path_config().SKILL_ROOT))

from learning import (
    PatternRecognizer,
    PatternType,
    BestPracticeExtractor,
    KnowledgeUpdater,
    KnowledgeCategory,
    KnowledgeQuality
)


def example_pattern_evolution_tracking():
    """模式演化跟踪示例"""
    print("\n" + "="*60)
    print("模式演化跟踪示例")
    print("="*60)
    
    recognizer = PatternRecognizer()
    
    success_data = {
        "status": "success",
        "success_rate": 0.85,
        "quality_score": 0.80,
        "code": "def example():\n    return True",
        "file_path": "example.py"
    }
    
    pattern = recognizer.recognize_success_pattern(success_data)
    
    if pattern:
        print(f"\n初始模式:")
        print(f"  - 模式ID: {pattern.pattern_id}")
        print(f"  - 置信度分数: {pattern.confidence_score:.2f}")
        print(f"  - 出现次数: {pattern.occurrences}")
        
        evolution_data = {
            "confidence_change": 0.92,
            "occurrence_change": 3,
            "feature_changes": {
                "code_length": {"old": 100, "new": 150, "delta": 50}
            }
        }
        
        evolution_result = recognizer.track_pattern_evolution(
            pattern.pattern_id,
            evolution_data
        )
        
        print(f"\n演化结果:")
        print(f"  - 演化类型: {evolution_result['evolution_type']}")
        print(f"  - 趋势: {evolution_result['trend']}")
        print(f"  - 变更数量: {len(evolution_result['changes'])}")
        
        for change in evolution_result['changes']:
            print(f"    - {change['aspect']}: {change['old_value']:.2f} -> {change['new_value']:.2f}")


def example_pattern_clustering():
    """模式聚类分析示例"""
    print("\n" + "="*60)
    print("模式聚类分析示例")
    print("="*60)
    
    recognizer = PatternRecognizer()
    
    for i in range(10):
        success_data = {
            "status": "success",
            "success_rate": 0.85 + i * 0.01,
            "code": f"def function_{i}():\n    return {i}",
            "file_path": f"module_{i}.py"
        }
        recognizer.recognize_success_pattern(success_data)
    
    clusters = recognizer.cluster_patterns(
        pattern_type=PatternType.SUCCESS,
        min_cluster_size=2
    )
    
    print(f"\n聚类结果:")
    print(f"  - 聚类数量: {len(clusters)}")
    
    for cluster_id, pattern_ids in clusters.items():
        print(f"\n  {cluster_id}:")
        print(f"    - 模式数量: {len(pattern_ids)}")
        print(f"    - 模式ID: {pattern_ids[:3]}")


def example_pattern_applicability_prediction():
    """模式适用性预测示例"""
    print("\n" + "="*60)
    print("模式适用性预测示例")
    print("="*60)
    
    recognizer = PatternRecognizer()
    
    success_data = {
        "status": "success",
        "success_rate": 0.90,
        "code": "def optimized_function():\n    return [x*2 for x in range(100)]",
        "file_path": "optimized.py",
        "tags": ["python", "optimization", "list-comprehension"]
    }
    
    pattern = recognizer.recognize_success_pattern(success_data)
    
    if pattern:
        context = {
            "project_type": "web_application",
            "technology_stack": ["python", "django"],
            "tags": ["python", "optimization"],
            "objectives": ["improve_performance"]
        }
        
        prediction = recognizer.predict_pattern_applicability(
            pattern.pattern_id,
            context
        )
        
        print(f"\n适用性预测:")
        print(f"  - 是否适用: {prediction['applicable']}")
        print(f"  - 置信度: {prediction['confidence']:.2f}")
        print(f"\n  影响因素:")
        for factor in prediction['factors']:
            print(f"    - {factor['name']}: {factor['score']:.2f} (权重: {factor['weight']})")
        
        if prediction['recommendations']:
            print(f"\n  建议:")
            for rec in prediction['recommendations']:
                print(f"    - {rec}")


def example_advanced_feature_extraction():
    """高级特征提取示例"""
    print("\n" + "="*60)
    print("高级特征提取示例")
    print("="*60)
    
    recognizer = PatternRecognizer()
    
    code_data = {
        "code": """
import os
import sys
from typing import List, Dict
from skillscripts.core.path_config_center import get_path_config

class DataProcessor:
    def __init__(self):
        self.data = []
    
    def process(self, items: List[Dict]) -> List[Dict]:
        results = []
        for item in items:
            if item.get('active'):
                processed = self._transform(item)
                results.append(processed)
        return results
    
    def _transform(self, item: Dict) -> Dict:
        return {'id': item['id'], 'value': item['value'] * 2}

if __name__ == '__main__':
    processor = DataProcessor()
    print(processor.process([{'id': 1, 'value': 10, 'active': True}]))
""",
        "description": "数据处理类，用于转换和过滤数据",
        "title": "数据处理器",
        "dependencies": ["os", "sys", "typing"]
    }
    
    features = recognizer.extract_advanced_features(
        code_data,
        feature_types=['complexity', 'dependency', 'semantic', 'structural']
    )
    
    print(f"\n提取的高级特征:")
    
    if 'complexity' in features:
        print(f"\n  复杂度特征:")
        for key, value in features['complexity'].items():
            print(f"    - {key}: {value}")
    
    if 'dependency' in features:
        print(f"\n  依赖特征:")
        for key, value in features['dependency'].items():
            if isinstance(value, list):
                print(f"    - {key}: {value[:3]}")
            else:
                print(f"    - {key}: {value}")
    
    if 'semantic' in features:
        print(f"\n  语义特征:")
        for key, value in features['semantic'].items():
            print(f"    - {key}: {value:.2f}")
    
    if 'structural' in features:
        print(f"\n  结构特征:")
        for key, value in features['structural'].items():
            print(f"    - {key}: {value}")


def example_practice_correlation_analysis():
    """实践关联分析示例"""
    print("\n" + "="*60)
    print("实践关联分析示例")
    print("="*60)
    
    recognizer = PatternRecognizer()
    extractor = BestPracticeExtractor(pattern_recognizer=recognizer)
    
    for i in range(5):
        success_data = {
            "status": "success",
            "success_rate": 0.85 + i * 0.02,
            "code": f"def function_{i}():\n    return {i}",
            "file_path": f"module_{i}.py"
        }
        
        pattern = recognizer.recognize_success_pattern(success_data)
        
        if pattern and pattern.occurrences >= 3:
            extractor.extract_code_practice(pattern)
    
    practices = list(extractor._practices.values())
    
    if practices:
        practice = practices[0]
        
        correlations = extractor.analyze_practice_correlations(practice.practice_id)
        
        print(f"\n实践关联分析结果:")
        print(f"  - 实践ID: {correlations['practice_id']}")
        print(f"  - 强相关实践数: {len(correlations['strongly_related'])}")
        print(f"  - 中等相关实践数: {len(correlations['moderately_related'])}")
        print(f"  - 弱相关实践数: {len(correlations['weakly_related'])}")
        print(f"  - 互补实践数: {len(correlations['complementary'])}")
        print(f"  - 冲突实践数: {len(correlations['conflicting'])}")
        
        if correlations['strongly_related']:
            print(f"\n  强相关实践:")
            for rel in correlations['strongly_related'][:2]:
                print(f"    - {rel['title']} (相似度: {rel['similarity']:.2f})")


def example_practice_recommendation():
    """实践推荐引擎示例"""
    print("\n" + "="*60)
    print("实践推荐引擎示例")
    print("="*60)
    
    recognizer = PatternRecognizer()
    extractor = BestPracticeExtractor(pattern_recognizer=recognizer)
    
    for i in range(5):
        success_data = {
            "status": "success",
            "success_rate": 0.88 + i * 0.02,
            "code": f"def optimized_{i}():\n    return [x*2 for x in range(100)]",
            "file_path": f"optimized_{i}.py",
            "tags": ["python", "optimization", "performance"]
        }
        
        pattern = recognizer.recognize_success_pattern(success_data)
        
        if pattern and pattern.occurrences >= 3:
            extractor.extract_code_practice(pattern)
    
    context = {
        "project_type": "web_api",
        "technology_stack": ["python", "fastapi"],
        "tags": ["python", "optimization"]
    }
    
    objectives = [
        "improve_performance",
        "reduce_latency",
        "optimize_code"
    ]
    
    constraints = [
        "maintain_readability"
    ]
    
    recommendations = extractor.recommend_practices(
        context,
        objectives,
        constraints,
        limit=3
    )
    
    print(f"\n实践推荐结果:")
    print(f"  - 推荐数量: {len(recommendations)}")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n  推荐 {i}:")
        print(f"    - 标题: {rec['title']}")
        print(f"    - 类别: {rec['category']}")
        print(f"    - 质量: {rec['quality']}")
        print(f"    - 相关性分数: {rec['relevance_score']:.2f}")
        print(f"    - 推荐理由: {', '.join(rec['reasons'])}")
        
        if rec['warnings']:
            print(f"    - 警告: {', '.join(rec['warnings'])}")


def example_knowledge_graph_building():
    """知识图谱构建示例"""
    print("\n" + "="*60)
    print("知识图谱构建示例")
    print("="*60)
    
    updater = KnowledgeUpdater()
    
    updater.add_knowledge({
        "title": "Python列表推导式",
        "content": {"pattern": "list_comprehension"},
        "tags": ["python", "optimization"],
        "quality_score": 0.9
    })
    
    updater.add_knowledge({
        "title": "Python生成器表达式",
        "content": {"pattern": "generator_expression"},
        "tags": ["python", "optimization", "memory"],
        "quality_score": 0.88,
        "dependencies": ["Python列表推导式"]
    })
    
    updater.add_knowledge({
        "title": "Python装饰器模式",
        "content": {"pattern": "decorator"},
        "tags": ["python", "design-pattern"],
        "quality_score": 0.85
    })
    
    graph = updater.build_knowledge_graph()
    
    print(f"\n知识图谱:")
    print(f"  - 节点数: {len(graph['nodes'])}")
    print(f"  - 边数: {len(graph['edges'])}")
    print(f"  - 聚类数: {len(graph['clusters'])}")
    
    print(f"\n  节点示例:")
    for node in graph['nodes'][:3]:
        print(f"    - {node['label']} (类别: {node['category']}, 质量: {node['quality']})")
    
    if graph['edges']:
        print(f"\n  边示例:")
        for edge in graph['edges'][:3]:
            print(f"    - {edge['source'][:20]} -> {edge['target'][:20]} ({edge['type']})")


def example_knowledge_inference():
    """知识关系推理示例"""
    print("\n" + "="*60)
    print("知识关系推理示例")
    print("="*60)
    
    updater = KnowledgeUpdater()
    
    pattern_entry = updater.add_knowledge({
        "title": "成功模式：快速排序优化",
        "category": "pattern",
        "content": {"algorithm": "quicksort", "optimization": "pivot_selection"},
        "tags": ["algorithm", "sorting", "optimization"],
        "quality_score": 0.9
    })
    
    practice_entry = updater.add_knowledge({
        "title": "最佳实践：选择合适的基准点",
        "category": "practice",
        "content": {
            "source_patterns": [pattern_entry.entry_id],
            "implementation": "使用中位数作为基准点"
        },
        "tags": ["algorithm", "sorting", "optimization"],
        "quality_score": 0.85
    })
    
    inference_result = updater.infer_knowledge_relations(practice_entry.entry_id)
    
    print(f"\n知识关系推理结果:")
    print(f"  - 条目ID: {inference_result['entry_id']}")
    print(f"  - 相似条目数: {len(inference_result['similar_entries'])}")
    print(f"  - 互补条目数: {len(inference_result['complementary_entries'])}")
    print(f"  - 推理关系数: {len(inference_result['inferred_relations'])}")
    print(f"  - 推理依赖数: {len(inference_result['inferred_dependencies'])}")
    
    if inference_result['inferred_relations']:
        print(f"\n  推理的关系:")
        for rel in inference_result['inferred_relations']:
            print(f"    - {rel['title']} (类型: {rel['relation_type']})")


def example_improved_deduplication():
    """改进的去重算法示例"""
    print("\n" + "="*60)
    print("改进的去重算法示例")
    print("="*60)
    
    updater = KnowledgeUpdater()
    
    updater.add_knowledge({
        "title": "Python代码优化技巧",
        "content": {
            "technique": "list_comprehension",
            "example": "[x*2 for x in range(10)]"
        },
        "tags": ["python", "optimization"],
        "quality_score": 0.85
    })
    
    similar_data = {
        "title": "Python代码优化技术",
        "content": {
            "technique": "list_comprehension",
            "example": "[x*2 for x in range(10)]",
            "additional_info": "提高性能"
        },
        "tags": ["python", "optimization", "performance"]
    }
    
    is_duplicate, duplicate_id, similarity = updater.improve_deduplication(
        similar_data,
        use_semantic_similarity=True
    )
    
    print(f"\n去重检测结果:")
    print(f"  - 是否重复: {is_duplicate}")
    print(f"  - 相似度分数: {similarity:.2f}")
    
    if is_duplicate and duplicate_id:
        entry = updater._entries.get(duplicate_id)
        if entry:
            print(f"  - 重复条目: {entry.title}")


def example_knowledge_lifecycle_management():
    """知识生命周期管理示例"""
    print("\n" + "="*60)
    print("知识生命周期管理示例")
    print("="*60)
    
    updater = KnowledgeUpdater()
    
    for i in range(5):
        updater.add_knowledge({
            "title": f"知识条目 {i}",
            "content": {"data": f"example_{i}"},
            "tags": ["example"],
            "quality_score": 0.6 + i * 0.08,
            "application_count": i * 3
        })
    
    lifecycle_policy = {
        "archive_after_days": 90,
        "remove_after_days": 180,
        "min_quality_for_archive": KnowledgeQuality.POOR,
        "min_applications_for_keep": 2
    }
    
    result = updater.manage_knowledge_lifecycle(lifecycle_policy)
    
    print(f"\n生命周期管理结果:")
    print(f"  - 归档数量: {len(result['archived'])}")
    print(f"  - 删除数量: {len(result['removed'])}")
    print(f"  - 保留数量: {len(result['kept'])}")
    print(f"  - 提升数量: {len(result['promoted'])}")
    
    if result['promoted']:
        print(f"\n  提升的知识:")
        for item in result['promoted']:
            print(f"    - {item['title']} -> {item['new_quality']}")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("三省六部技能 - 自动学习系统高级功能示例")
    print("="*60)
    
    example_pattern_evolution_tracking()
    example_pattern_clustering()
    example_pattern_applicability_prediction()
    example_advanced_feature_extraction()
    example_practice_correlation_analysis()
    example_practice_recommendation()
    example_knowledge_graph_building()
    example_knowledge_inference()
    example_improved_deduplication()
    example_knowledge_lifecycle_management()
    
    print("\n" + "="*60)
    print("高级功能示例运行完成")
    print("="*60)


if __name__ == "__main__":
    main()
