#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最佳实践提取器增强功能示例

演示如何使用增强的最佳实践提取器功能：
1. 代码模式识别
2. 最佳实践文档生成
3. 模式适用性分析
4. 导出到礼部规范库
"""

import json
from pathlib import Path
from best_practice_extractor import (
    BestPracticeExtractor,
    PracticeCategory,
    PracticeQuality
)
from pattern_recognizer import (
    PatternRecognizer,
    PatternType,
    RecognizedPattern
)


def demo_code_pattern_recognition():
    """演示代码模式识别功能"""
    print("=" * 80)
    print("代码模式识别示例")
    print("=" * 80)
    
    extractor = BestPracticeExtractor()
    
    sample_code = '''
import logging
from typing import List, Optional

class DatabaseManager:
    """数据库管理器 - 单例模式"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.connections = {}
            self.logger = logging.getLogger(__name__)
            self.initialized = True
    
    def get_connection(self, db_name: str):
        """获取数据库连接"""
        if db_name not in self.connections:
            self.connections[db_name] = self._create_connection(db_name)
        return self.connections[db_name]
    
    def _create_connection(self, db_name: str):
        """创建数据库连接"""
        self.logger.info(f"Creating connection for {db_name}")
        return {"name": db_name, "status": "connected"}

class UserFactory:
    """用户工厂 - 工厂模式"""
    
    @staticmethod
    def create_user(user_type: str, **kwargs):
        """创建用户"""
        if user_type == "admin":
            return AdminUser(**kwargs)
        elif user_type == "regular":
            return RegularUser(**kwargs)
        else:
            raise ValueError(f"Unknown user type: {user_type}")

class NotificationService:
    """通知服务 - 观察者模式"""
    
    def __init__(self):
        self._observers = []
    
    def attach(self, observer):
        """添加观察者"""
        self._observers.append(observer)
    
    def detach(self, observer):
        """移除观察者"""
        self._observers.remove(observer)
    
    def notify(self, message: str):
        """通知所有观察者"""
        for observer in self._observers:
            observer.update(message)

def calculate_statistics(data: List[float]) -> dict:
    """计算统计数据"""
    if not data:
        return {"mean": 0, "sum": 0, "count": 0}
    
    total = sum(data)
    count = len(data)
    mean = total / count
    
    return {
        "mean": mean,
        "sum": total,
        "count": count
    }
'''
    
    patterns = extractor.recognize_code_patterns(sample_code, language="python")
    
    print("\n识别到的设计模式:")
    for pattern in patterns["design_patterns"]:
        print(f"  - {pattern['pattern_name']}: {pattern['description']}")
        print(f"    置信度: {pattern['confidence']:.2f}, 质量: {pattern['quality']}")
    
    print("\n代码结构:")
    print(f"  类数量: {len(patterns['code_structures']['classes'])}")
    print(f"  函数数量: {len(patterns['code_structures']['functions'])}")
    print(f"  继承深度: {patterns['code_structures']['inheritance']['depth']}")
    
    print("\n命名规范合规性:")
    naming = patterns["naming_conventions"]
    print(f"  类命名: {naming['class_naming']['compliance']:.2%}")
    print(f"  函数命名: {naming['function_naming']['compliance']:.2%}")
    print(f"  变量命名: {naming['variable_naming']['compliance']:.2%}")
    print(f"  整体合规性: {naming['overall_compliance']:.2%}")
    
    print("\n代码质量指标:")
    quality = patterns["code_quality_indicators"]
    print(f"  文档字符串覆盖率: {quality['documentation']['docstring_coverage']:.2%}")
    print(f"  圈复杂度: {quality['complexity']['cyclomatic_complexity']}")
    print(f"  嵌套深度: {quality['complexity']['nesting_depth']}")
    print(f"  错误处理: {'有' if quality['error_handling']['has_try_catch'] else '无'}")
    
    print("\n反模式检测:")
    for ap in patterns["anti_patterns"]:
        print(f"  - {ap['name']}: {ap['description']}")
    
    print("\n整体得分: {:.2f}".format(patterns["overall_score"]))
    
    print("\n建议:")
    for rec in patterns["recommendations"]:
        print(f"  - {rec}")
    
    return patterns


def demo_practice_document_generation():
    """演示最佳实践文档生成功能"""
    print("\n" + "=" * 80)
    print("最佳实践文档生成示例")
    print("=" * 80)
    
    recognizer = PatternRecognizer()
    extractor = BestPracticeExtractor(pattern_recognizer=recognizer)
    
    execution_data = {
        "task_type": "code_review",
        "success_rate": 0.95,
        "execution_time": 120,
        "code_quality_score": 0.92
    }
    
    pattern = recognizer.recognize_success_pattern(
        execution_data,
        context={"language": "python", "project": "skiller"}
    )
    
    if pattern:
        practice = extractor.extract_code_practice(
            pattern,
            code_analysis={
                "complexity": 8,
                "test_coverage": 85,
                "documentation": 0.9
            }
        )
        
        if practice:
            print("\n生成Markdown文档:")
            print("-" * 80)
            markdown_doc = extractor.generate_practice_document(
                practice.practice_id,
                output_format="markdown",
                include_examples=False
            )
            print(markdown_doc[:500] + "...")
            
            print("\n生成HTML文档:")
            print("-" * 80)
            html_doc = extractor.generate_practice_document(
                practice.practice_id,
                output_format="html",
                include_examples=False
            )
            print(html_doc[:500] + "...")
            
            return practice
    
    return None


def demo_pattern_applicability_analysis():
    """演示模式适用性分析功能"""
    print("\n" + "=" * 80)
    print("模式适用性分析示例")
    print("=" * 80)
    
    recognizer = PatternRecognizer()
    extractor = BestPracticeExtractor(pattern_recognizer=recognizer)
    
    execution_data = {
        "task_type": "feature_development",
        "success_rate": 0.88,
        "execution_time": 240
    }
    
    pattern = recognizer.recognize_success_pattern(
        execution_data,
        context={"language": "python", "framework": "fastapi", "scale": "medium"}
    )
    
    if pattern:
        target_context = {
            "language": "python",
            "framework": "django",
            "scale": "large",
            "team_size": 10
        }
        
        constraints = [
            "avoid singleton",
            "must be scalable"
        ]
        
        analysis = extractor.analyze_pattern_applicability(
            pattern,
            target_context,
            constraints
        )
        
        print(f"\n模式: {analysis['pattern_name']}")
        print(f"适用性得分: {analysis['applicability_score']:.2f}")
        print(f"上下文匹配度: {analysis['context_match']:.2f}")
        print(f"约束合规性: {analysis['constraint_compliance']:.2f}")
        
        print("\n风险:")
        for risk in analysis["risks"]:
            print(f"  - {risk}")
        
        print("\n建议:")
        for rec in analysis["recommendations"]:
            print(f"  - {rec}")
        
        print("\n需要的适配:")
        for adaptation in analysis["adaptation_needed"]:
            print(f"  - {adaptation}")
        
        return analysis
    
    return None


def demo_export_to_standards():
    """演示导出到礼部规范库功能"""
    print("\n" + "=" * 80)
    print("导出到礼部规范库示例")
    print("=" * 80)
    
    recognizer = PatternRecognizer()
    extractor = BestPracticeExtractor(pattern_recognizer=recognizer)
    
    for i in range(3):
        execution_data = {
            "task_type": f"task_{i}",
            "success_rate": 0.85 + i * 0.05,
            "execution_time": 100 + i * 20
        }
        
        pattern = recognizer.recognize_success_pattern(
            execution_data,
            context={"language": "python", "project": "skiller"}
        )
        
        if pattern:
            extractor.extract_code_practice(
                pattern,
                code_analysis={
                    "complexity": 10 - i,
                    "test_coverage": 80 + i * 5,
                    "documentation": 0.85
                }
            )
    
    output_dir = Path(__file__).parent.parent.parent.parent / "shangshusheng" / "libu" / "best_practices"
    
    print(f"\n导出目录: {output_dir}")
    
    exported_files = extractor.export_practices_to_standards(
        str(output_dir),
        categories=[PracticeCategory.CODE],
        min_quality=PracticeQuality.GOOD
    )
    
    print("\n导出的文件:")
    for category, filepath in exported_files.items():
        print(f"  - {category}: {filepath}")
    
    return exported_files


def main():
    """主函数"""
    print("最佳实践提取器增强功能演示")
    print("=" * 80)
    
    demo_code_pattern_recognition()
    
    demo_practice_document_generation()
    
    demo_pattern_applicability_analysis()
    
    demo_export_to_standards()
    
    print("\n" + "=" * 80)
    print("演示完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
