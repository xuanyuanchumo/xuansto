#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强型自优化系统 - Enhanced Auto Optimization System

核心功能：
1. ExtendedStrategyLibrary - 扩展优化策略库（20+策略）
   - 性能优化类：异步转换、缓存层、连接池、懒加载、批处理
   - 内存优化类：内存分析、对象池、流式处理、数据结构优化
   - 并发优化类：并行执行、锁优化、队列缓冲、限流控制
   - I/O优化类：I/O批处理、数据压缩、CDN集成
   - 代码质量类：死代码消除、复杂度降低、命名规范、类型提示

2. ABTestFramework - A/B测试框架
   - 统计显著性检验
   - 置信区间计算
   - 推荐决策生成

3. SmartRollbackManager - 智能回滚决策管理器
   - 基于退化程度选择回滚策略
   - 多级回滚方案
   - 回滚效果评估

使用示例：
    from enhanced_auto_optimization import (
        ExtendedStrategyLibrary,
        ABTestFramework,
        SmartRollbackManager
    )

    library = ExtendedStrategyLibrary()
    strategies = library.get_strategies_by_category('performance')

    ab_test = ABTestFramework()
    result = ab_test.run_comparison(control_group, test_group)

    rollback_mgr = SmartRollbackManager()
    decision = rollback_mgr.decide_rollback(metrics_before, metrics_after)
"""

import json
import logging
import math
import random
import statistics
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Union

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StrategyCategory(Enum):
    """策略分类"""
    PERFORMANCE = "performance"
    MEMORY = "memory"
    CONCURRENCY = "concurrency"
    IO_OPTIMIZATION = "io"
    CODE_QUALITY = "code_quality"


class StrategyImpact(Enum):
    """策略影响程度"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RollbackStrategy(Enum):
    """回滚策略"""
    IMMEDIATE = "immediate"
    GRADUAL = "gradual"
    MONITOR = "monitor"
    CONTINUE = "continue"


class DecisionType(Enum):
    """A/B测试决策类型"""
    ADOPT = "adopt"           # 采用新方案
    REJECT = "reject"         # 拒绝新方案
    CONTINUE_OBSERVING = "continue_observing"  # 继续观察
    INCONCLUSIVE = "inconclusive"              # 结果不明确


@dataclass
class OptimizationStrategy:
    """优化策略定义"""
    strategy_id: str
    name: str
    description: str
    category: StrategyCategory
    impact: StrategyImpact
    applicable_scenarios: List[str]
    implementation_complexity: int          # 1-10
    expected_improvement_range: Tuple[float, float]  # (min%, max%)
    risk_level: int                         # 1-10
    prerequisites: List[str] = field(default_factory=list)
    side_effects: List[str] = field(default_factory=list)
    code_patterns: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'impact': self.impact.value,
            'applicable_scenarios': self.applicable_scenarios,
            'implementation_complexity': self.implementation_complexity,
            'expected_improvement_range': list(self.expected_improvement_range),
            'risk_level': self.risk_level,
            'prerequisites': self.prerequisites,
            'side_effects': self.side_effects,
            'code_patterns': self.code_patterns,
            'metadata': self.metadata
        }


@dataclass
class ABTestResult:
    """A/B测试结果"""
    test_id: str
    control_mean: float
    test_mean: float
    control_std: float
    test_std: float
    control_size: int
    test_size: int
    improvement_percentage: float
    p_value: float
    is_significant: bool
    confidence_interval: Tuple[float, float]
    decision: DecisionType
    recommendation: str
    statistical_power: float
    effect_size: float
    test_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'test_id': self.test_id,
            'control_mean': round(self.control_mean, 4),
            'test_mean': round(self.test_mean, 4),
            'control_std': round(self.control_std, 4),
            'test_std': round(self.test_std, 4),
            'control_size': self.control_size,
            'test_size': self.test_size,
            'improvement_percentage': round(self.improvement_percentage, 2),
            'p_value': round(self.p_value, 6),
            'is_significant': self.is_significant,
            'confidence_interval': [round(x, 4) for x in self.confidence_interval],
            'decision': self.decision.value,
            'recommendation': self.recommendation,
            'statistical_power': round(self.statistical_power, 4),
            'effect_size': round(self.effect_size, 4),
            'metadata': self.test_metadata
        }


@dataclass
class RollbackDecision:
    """回滚决策"""
    decision_id: str
    strategy: RollbackStrategy
    degradation_level: str
    reason: str
    affected_metrics: List[str]
    degradation_percentages: Dict[str, float]
    steps: List[Dict[str, str]]
    estimated_recovery_time_minutes: int
    risk_of_rollback: str
    confidence: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'decision_id': self.decision_id,
            'strategy': self.strategy.value,
            'degradation_level': self.degradation_level,
            'reason': self.reason,
            'affected_metrics': self.affected_metrics,
            'degradation_percentages': {k: round(v, 2) for k, v in self.degradation_percentages.items()},
            'steps': self.steps,
            'estimated_recovery_time_minutes': self.estimated_recovery_time_minutes,
            'risk_of_rollback': self.risk_of_rollback,
            'confidence': round(self.confidence, 3),
            'timestamp': self.timestamp
        }


class ExtendedStrategyLibrary:
    """
    扩展优化策略库

    提供20+种优化策略，覆盖性能、内存、并发、I/O、代码质量等多个维度。
    每个策略包含详细的应用场景、预期效果和风险评估。
    """

    EXTENDED_STRATEGIES = {
        # ===== 性能优化类 (5个) =====
        'async_conversion': {
            'desc': '同步转异步',
            'impact': 'high',
            'category': 'performance',
            'scenarios': ['I/O密集操作', '网络请求', '文件读写'],
            'complexity': 6,
            'improvement': (10, 50),
            'risk': 5,
            'prereqs': ['异步框架支持', '回调或async/await理解'],
            'side_effects': ['调试复杂度增加', '错误处理更复杂'],
            'patterns': ['def ', '.read(', '.write(', 'requests.', 'urllib']
        },
        'caching_layer': {
            'desc': '添加缓存层',
            'impact': 'high',
            'category': 'performance',
            'scenarios': ['频繁读取数据', '计算昂贵操作', '数据库查询'],
            'complexity': 4,
            'improvement': (20, 80),
            'risk': 3,
            'prereqs': ['缓存基础设施', '缓存失效策略'],
            'side_effects': ['数据一致性挑战', '内存占用增加'],
            'patterns': ['SELECT', 'query(', 'fetch(', 'get_data(']
        },
        'connection_pooling': {
            'desc': '连接池优化',
            'impact': 'medium',
            'category': 'performance',
            'scenarios': ['数据库连接', 'HTTP连接', 'Redis连接'],
            'complexity': 5,
            'improvement': (15, 40),
            'risk': 4,
            'prereqs': ['连接池库', '连接配置'],
            'side_effects': ['资源占用', '连接泄漏风险'],
            'patterns': ['connect(', 'create_connection(', 'Session()']
        },
        'lazy_loading': {
            'desc': '懒加载优化',
            'impact': 'medium',
            'category': 'performance',
            'scenarios': ['大型对象初始化', '可选依赖', '延迟计算'],
            'complexity': 3,
            'improvement': (5, 30),
            'risk': 2,
            'prereqs': ['属性访问器', '延迟初始化模式'],
            'side_effects': ['首次访问延迟', '线程安全问题'],
            'patterns': ['__init__(self', '= {', '= [', 'load_all(']
        },
        'batch_processing': {
            'desc': '批量处理优化',
            'impact': 'medium',
            'category': 'performance',
            'scenarios': ['批量插入', '批量更新', '批量删除'],
            'complexity': 4,
            'improvement': (30, 70),
            'risk': 3,
            'prereqs': ['批量API支持', '事务管理'],
            'side_effects': ['错误处理复杂', '内存峰值'],
            'patterns': ['for .* in', '.insert(', '.update(', '.delete(']
        },

        # ===== 内存优化类 (4个) =====
        'memory_profiling': {
            'desc': '内存分析优化',
            'impact': 'high',
            'category': 'memory',
            'scenarios': ['内存泄漏', '高内存占用', '内存碎片'],
            'complexity': 5,
            'improvement': (10, 60),
            'risk': 2,
            'prereqs': ['内存分析工具', '基线数据'],
            'side_effects': ['分析开销', '需要专业知识'],
            'patterns': ['[] * n', '{} * n', 'list comprehension']
        },
        'object_pooling': {
            'desc': '对象池复用',
            'impact': 'medium',
            'category': 'memory',
            'scenarios': ['频繁创建销毁对象', '重量级对象', '连接对象'],
            'complexity': 6,
            'improvement': (15, 45),
            'risk': 4,
            'prereqs': ['对象池实现', '生命周期管理'],
            'side_effects': ['代码复杂度', '状态污染'],
            'patterns': ['ClassName()', '= object()', 'new ']
        },
        'streaming_processing': {
            'desc': '流式处理',
            'impact': 'high',
            'category': 'memory',
            'scenarios': ['大文件处理', '大数据集', '实时数据流'],
            'complexity': 5,
            'improvement': (40, 90),
            'risk': 3,
            'prereqs': ['迭代器/生成器', '流式API'],
            'side_effects': ['无法随机访问', '错误恢复困难'],
            'patterns': ['read()', '.readlines(', 'for line in f', 'load(']
        },
        'data_structure_opt': {
            'desc': '数据结构优化',
            'impact': 'medium',
            'category': 'memory',
            'scenarios': ['查找密集', '频繁插入删除', '排序需求'],
            'complexity': 4,
            'improvement': (10, 40),
            'risk': 3,
            'prereqs': ['数据结构知识', '性能特征了解'],
            'side_effects': ['可读性影响', 'API变化'],
            'patterns': ['[', '{', '(', 'list(', 'dict(', 'set(']
        },

        # ===== 并发优化类 (4个) =====
        'parallel_execution': {
            'desc': '并行执行',
            'impact': 'high',
            'category': 'concurrency',
            'scenarios': ['CPU密集任务', '独立子任务', 'MapReduce'],
            'complexity': 7,
            'improvement': (30, 80),
            'risk': 6,
            'prereqs': ['多进程/多线程', '任务分解'],
            'side_effects': ['竞态条件', '死锁风险', '调试困难'],
            'patterns': ['for i in range(', '.map(', '.apply(']
        },
        'lock_optimization': {
            'desc': '锁优化',
            'impact': 'medium',
            'category': 'concurrency',
            'scenarios': ['锁竞争', '死锁', '活锁'],
            'complexity': 7,
            'improvement': (10, 35),
            'risk': 7,
            'prereqs': ['锁机制理解', '并发编程经验'],
            'side_effects': ['正确性风险', '引入新bug'],
            'patterns': ['Lock(', 'acquire(', 'synchronized', '@lock']
        },
        'queue_buffering': {
            'desc': '队列缓冲',
            'impact': 'medium',
            'category': 'concurrency',
            'scenarios': ['生产者消费者', '削峰填谷', '异步处理'],
            'complexity': 5,
            'improvement': (15, 50),
            'risk': 4,
            'prereqs': ['消息队列', '缓冲机制'],
            'side_effects': ['延迟增加', '顺序保证问题'],
            'patterns': ['.put(', '.get(', 'send(', 'publish(']
        },
        'rate_limiting': {
            'desc': '限流控制',
            'impact': 'low',
            'category': 'concurrency',
            'scenarios': ['API保护', '防止过载', '公平使用'],
            'complexity': 3,
            'improvement': (5, 20),
            'risk': 2,
            'prereqs': ['限流算法', '计数器/令牌桶'],
            'side_effects': ['用户体验影响', '请求拒绝'],
            'patterns': ['api_call(', 'request(', 'fetch(']
        },

        # ===== I/O优化类 (3个) =====
        'io_batching': {
            'desc': 'I/O批处理',
            'impact': 'high',
            'category': 'io',
            'scenarios': ['频繁小I/O', '日志写入', '文件操作'],
            'complexity': 4,
            'improvement': (25, 60),
            'risk': 3,
            'prereqs': ['缓冲机制', '批量写入支持'],
            'side_effects': ['数据丢失风险', '延迟写入'],
            'patterns': ['.write(', '.flush(', 'open(', 'close(']
        },
        'compression': {
            'desc': '数据压缩',
            'impact': 'medium',
            'category': 'io',
            'scenarios': ['大体积传输', '存储优化', '带宽受限'],
            'complexity': 3,
            'improvement': (30, 80),
            'risk': 2,
            'prereqs': ['压缩库', '解压兼容性'],
            'side_effects': ['CPU开销', '延迟增加'],
            'patterns': ['.send(', '.dump(', 'json.dumps(', 'str(']
        },
        'cdn_integration': {
            'desc': 'CDN集成',
            'impact': 'medium',
            'category': 'io',
            'scenarios': ['静态资源', '全球分发', '高并发下载'],
            'complexity': 5,
            'improvement': (20, 70),
            'risk': 3,
            'prereqs': ['CDN服务', '域名配置'],
            'side_effects': ['缓存一致性', '成本增加'],
            'patterns': ['/static/', '/assets/', '/images/', '.css', '.js']
        },

        # ===== 代码质量类 (4个) =====
        'dead_code_elimination': {
            'desc': '死代码消除',
            'impact': 'low',
            'category': 'code_quality',
            'scenarios': ['未使用函数', '不可达代码', '废弃功能'],
            'complexity': 2,
            'improvement': (5, 15),
            'risk': 2,
            'prereqs': ['静态分析工具', '覆盖率报告'],
            'side_effects': ['可能误删', '破坏隐式依赖'],
            'patterns': ['def unused_', '# TODO:', '# FIXME:']
        },
        'complexity_reduction': {
            'desc': '复杂度降低',
            'impact': 'medium',
            'category': 'code_quality',
            'scenarios': ['圈复杂度高', '嵌套过深', '长函数'],
            'complexity': 5,
            'improvement': (10, 30),
            'risk': 4,
            'prereqs': ['重构技能', '测试覆盖'],
            'side_effects': ['行为变化风险', '过度拆分'],
            'patterns': ['if ', 'elif ', 'else:', 'for ', 'while ']
        },
        'naming_standardization': {
            'desc': '命名规范化',
            'impact': 'low',
            'category': 'code_quality',
            'scenarios': ['命名不一致', '缩写混乱', '不符合规范'],
            'complexity': 2,
            'improvement': (3, 10),
            'risk': 1,
            'prereqs': ['命名规范文档', '自动化检查'],
            'side_effects': ['大量修改', 'API变更'],
            'patterns': ['def ', 'class ', 'var_name', 'param_name']
        },
        'type_hints_addition': {
            'desc': '类型提示添加',
            'impact': 'low',
            'category': 'code_quality',
            'scenarios': ['缺少类型注解', 'IDE支持差', '重构困难'],
            'complexity': 3,
            'improvement': (5, 15),
            'risk': 1,
            'prereqs': ['Python 3.6+', '类型检查器'],
            'side_effects': ['代码量增加', '灵活性降低'],
            'patterns': ['def func(', '-> ', ': Optional', ': List[']
        }
    }

    def __init__(self):
        self.logger = logging.getLogger('ExtendedStrategyLibrary')
        self._strategies_cache: Dict[str, OptimizationStrategy] = {}
        self._initialize_strategies()

    def _initialize_strategies(self):
        """初始化所有策略"""
        for strategy_id, config in self.EXTENDED_STRATEGIES.items():
            strategy = OptimizationStrategy(
                strategy_id=strategy_id,
                name=config['desc'],
                description=f"{config['desc']} - 适用于{', '.join(config['scenarios'][:2])}",
                category=StrategyCategory(config['category']),
                impact=StrategyImpact(config['impact']),
                applicable_scenarios=config['scenarios'],
                implementation_complexity=config['complexity'],
                expected_improvement_range=config['improvement'],
                risk_level=config['risk'],
                prerequisites=config.get('prereqs', []),
                side_effects=config.get('side_effects', []),
                code_patterns=config.get('patterns', [])
            )
            self._strategies_cache[strategy_id] = strategy

        self.logger.info(f"已初始化 {len(self._strategies_cache)} 个优化策略")

    def get_all_strategies(self) -> List[OptimizationStrategy]:
        """获取所有策略"""
        return list(self._strategies_cache.values())

    def get_strategy(self, strategy_id: str) -> Optional[OptimizationStrategy]:
        """获取单个策略"""
        return self._strategies_cache.get(strategy_id)

    def get_strategies_by_category(self, category: Union[str, StrategyCategory]) -> List[OptimizationStrategy]:
        """按类别获取策略"""
        if isinstance(category, str):
            category = StrategyCategory(category)
        return [s for s in self._strategies_cache.values() if s.category == category]

    def get_strategies_by_impact(self, impact: Union[str, StrategyImpact]) -> List[OptimizationStrategy]:
        """按影响程度获取策略"""
        if isinstance(impact, str):
            impact = StrategyImpact(impact)
        return [s for s in self._strategies_cache.values() if s.impact == impact]

    def get_strategies_by_scenario(self, scenario: str) -> List[OptimizationStrategy]:
        """按应用场景推荐策略"""
        scenario_lower = scenario.lower()
        matching = []
        for strategy in self._strategies_cache.values():
            if any(scenario_lower in s.lower() for s in strategy.applicable_scenarios):
                matching.append(strategy)
        return sorted(matching, key=lambda x: x.impact.value, reverse=True)

    def recommend_strategies(
        self,
        problem_description: str,
        max_recommendations: int = 5
    ) -> List[Tuple[OptimizationStrategy, float]]:
        """
        根据问题描述推荐策略

        Returns:
            策略列表，每个元素为(策略, 匹配度得分)
        """
        problem_lower = problem_description.lower()
        recommendations = []

        for strategy in self._strategies_cache.values():
            score = 0.0

            desc_match = sum(1 for word in problem_lower.split() if word in strategy.description.lower())
            score += desc_match * 2

            scenario_match = sum(1 for scenario in strategy.applicable_scenarios
                               if any(word in scenario.lower() for word in problem_lower.split()))
            score += scenario_match * 3

            pattern_match = sum(1 for pattern in strategy.code_patterns
                              if pattern.lower() in problem_lower)
            score += pattern_match * 1.5

            if score > 0:
                recommendations.append((strategy, score))

        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:max_recommendations]

    def get_statistics(self) -> Dict[str, Any]:
        """获取策略库统计信息"""
        categories = defaultdict(int)
        impacts = defaultdict(int)

        for strategy in self._strategies_cache.values():
            categories[strategy.category.value] += 1
            impacts[strategy.impact.value] += 1

        return {
            'total_strategies': len(self._strategies_cache),
            'by_category': dict(categories),
            'by_impact': dict(impacts),
            'avg_complexity': sum(s.implementation_complexity for s in self._strategies_cache.values()) / len(self._strategies_cache),
            'avg_risk': sum(s.risk_level for s in self._strategies_cache.values()) / len(self._strategies_cache)
        }


class ABTestFramework:
    """
    A/B测试框架

    支持统计显著性检验和置信区间计算，
    用于科学评估优化方案的效果。
    """

    DEFAULT_CONFIDENCE_LEVEL = 0.95
    MIN_SAMPLE_SIZE = 30

    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
        self.logger = logging.getLogger('ABTestFramework')
        self.test_history: List[ABTestResult] = []

    def run_comparison(
        self,
        control_group: List[float],
        test_group: Dict[str, Any],
        metric_name: str = "performance",
        test_id: Optional[str] = None
    ) -> ABTestResult:
        """
        运行A/B对比测试

        Args:
            control_group: 对照组数据（原始版本的性能指标值列表）
            test_group: 测试组数据（可以是字典格式 {'values': [...], 'label': '...'} 或直接是数值列表）
            metric_name: 指标名称
            test_id: 测试ID（自动生成如果未提供）

        Returns:
            A/B测试结果，包含统计显著性和推荐决策
        """
        if not test_id:
            test_id = f"AB-{metric_name.upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        if isinstance(test_group, dict):
            test_values = test_group.get('values', [])
            test_label = test_group.get('label', 'optimized')
        else:
            test_values = list(test_group)
            test_label = 'optimized'

        if len(control_group) < self.MIN_SAMPLE_SIZE or len(test_values) < self.MIN_SAMPLE_SIZE:
            return self._create_insufficient_sample_result(test_id, control_group, test_values, metric_name)

        control_mean = statistics.mean(control_group)
        test_mean = statistics.mean(test_values)

        control_std = statistics.stdev(control_group) if len(control_group) > 1 else 0.0
        test_std = statistics.stdev(test_values) if len(test_values) > 1 else 0.0

        improvement_pct = ((test_mean - control_mean) / abs(control_mean)) * 100 if control_mean != 0 else 0.0

        p_value = self._calculate_t_test_pvalue(control_group, test_values)

        is_significant = p_value < (1 - self.confidence_level)

        ci_lower, ci_upper = self._calculate_confidence_interval(
            test_mean, test_std, len(test_values)
        )

        effect_size = self._calculate_cohens_d(control_group, test_values)

        statistical_power = self._estimate_statistical_power(
            effect_size, len(control_group), len(test_values)
        )

        decision, recommendation = self._make_decision(
            is_significant=is_significant,
            improvement_pct=improvement_pct,
            p_value=p_value,
            effect_size=effect_size,
            statistical_power=statistical_power,
            sample_sizes=(len(control_group), len(test_values))
        )

        result = ABTestResult(
            test_id=test_id,
            control_mean=control_mean,
            test_mean=test_mean,
            control_std=control_std,
            test_std=test_std,
            control_size=len(control_group),
            test_size=len(test_values),
            improvement_percentage=improvement_pct,
            p_value=p_value,
            is_significant=is_significant,
            confidence_interval=(ci_lower, ci_upper),
            decision=decision,
            recommendation=recommendation,
            statistical_power=statistical_power,
            effect_size=effect_size,
            test_metadata={
                'metric_name': metric_name,
                'confidence_level': self.confidence_level,
                'test_label': test_label
            }
        )

        self.test_history.append(result)
        self.logger.info(f"A/B测试完成: {test_id}, 决策: {decision.value}")

        return result

    def _calculate_t_test_pvalue(
        self,
        group1: List[float],
        group2: List[float]
    ) -> float:
        """计算双样本t检验的p值（简化版）"""
        try:
            n1, n2 = len(group1), len(group2)
            mean1, mean2 = statistics.mean(group1), statistics.mean(group2)

            var1 = statistics.variance(group1) if n1 > 1 else 0.0
            var2 = statistics.variance(group2) if n2 > 1 else 0.0

            pooled_se = math.sqrt(var1/n1 + var2/n2)

            if pooled_se == 0:
                return 1.0

            t_statistic = (mean2 - mean1) / pooled_se

            df = self._welch_df(n1, n2, var1, var2)

            p_value = 2 * (1 - self._t_cdf(abs(t_statistic), df))

            return max(0.0, min(1.0, p_value))

        except Exception as e:
            self.logger.warning(f"t检验计算错误: {e}")
            return 1.0

    def _welch_df(self, n1: int, n2: int, var1: float, var2: float) -> float:
        """计算Welch-Satterthwaite自由度"""
        num = (var1/n1 + var2/n2)**2
        denom = (var1/n1)**2/(n1-1) + (var2/n2)**2/(n2-1)
        return num / denom if denom != 0 else min(n1, n2) - 1

    def _t_cdf(self, t: float, df: float) -> float:
        """简化的t分布累积分布函数（近似）"""
        import math
        x = df / (df + t**2)
        return 0.5 + 0.5 * math.sqrt(1 - x**(df/3)) if t >= 0 else 0.5 - 0.5 * math.sqrt(1 - x**(df/3))

    def _calculate_confidence_interval(
        self,
        mean: float,
        std: float,
        n: int
    ) -> Tuple[float, float]:
        """计算置信区间"""
        if n == 0 or std == 0:
            return (mean, mean)

        se = std / math.sqrt(n)
        z_score = 1.96 if self.confidence_level == 0.95 else 2.576

        margin_error = z_score * se

        return (mean - margin_error, mean + margin_error)

    def _calculate_cohens_d(
        self,
        group1: List[float],
        group2: List[float]
    ) -> float:
        """计算Cohen's d效应量"""
        n1, n2 = len(group1), len(group2)
        mean1, mean2 = statistics.mean(group1), statistics.mean(group2)

        var1 = statistics.variance(group1) if n1 > 1 else 0.0
        var2 = statistics.variance(group2) if n2 > 1 else 0.0

        pooled_std = math.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2)) if (n1+n2-2) > 0 else 1.0

        if pooled_std == 0:
            return 0.0

        return (mean2 - mean1) / pooled_std

    def _estimate_statistical_power(
        self,
        effect_size: float,
        n1: int,
        n2: int
    ) -> float:
        """估算统计功效"""
        if effect_size == 0:
            return 0.05

        n_harmonic = 2 * n1 * n2 / (n1 + n2) if (n1 + n2) > 0 else 1
        ncp = effect_size * math.sqrt(n_harmonic / 2)

        power = min(0.99, 0.5 + 0.4 * math.tanh(ncp / 2))

        return max(0.05, power)

    def _make_decision(
        self,
        is_significant: bool,
        improvement_pct: float,
        p_value: float,
        effect_size: float,
        statistical_power: float,
        sample_sizes: Tuple[int, int]
    ) -> Tuple[DecisionType, str]:
        """
        基于统计指标做出决策

        决策规则：
        - 显著且正向改进 → ADOPT
        - 显著但负向 → REJECT
        - 不显著但样本不足 → CONTINUE_OBSERVING
        - 不显著且效应量小 → INCONCLUSIVE
        """
        if is_significant:
            if improvement_pct > 0 and abs(effect_size) > 0.2:
                return DecisionType.ADOPT, (
                    f"✅ 推荐采用：改进显著 ({improvement_pct:+.1f}%), "
                    f"p={p_value:.4f}, 效应量={abs(effect_size):.2f}"
                )
            elif improvement_pct < 0:
                return DecisionType.REJECT, (
                    f"❌ 建议拒绝：性能下降 ({improvement_pct:+.1f}%), "
                    f"建议回滚到原版本"
                )
            else:
                return DecisionType.INCONCLUSIVE, (
                    "⚠️ 结果不明确：统计显著但改进幅度极小，需进一步评估"
                )
        else:
            if statistical_power < 0.8:
                return DecisionType.CONTINUE_OBSERVING, (
                    f"🔍 继续观察：当前不显著(p={p_value:.4f})， "
                    f"统计功效不足({statistical_power:.2f})，建议增大样本量"
                )
            elif abs(effect_size) < 0.2:
                return DecisionType.INCONCLUSIVE, (
                    "⚠️ 效应量过小({:.2f}): 实际差异可能不具有实际意义".format(abs(effect_size))
                )
            else:
                return DecisionType.CONTINUE_OBSERVING, (
                    f"🔍 需要更多数据：效应量={abs(effect_size):.2f}，但不显著，继续收集数据"
                )

    def _create_insufficient_sample_result(
        self,
        test_id: str,
        control: List[float],
        test: List[float],
        metric: str
    ) -> ABTestResult:
        """创建样本不足的结果"""
        return ABTestResult(
            test_id=test_id,
            control_mean=statistics.mean(control) if control else 0,
            test_mean=statistics.mean(test) if test else 0,
            control_std=statistics.stdev(control) if len(control) > 1 else 0,
            test_std=statistics.stdev(test) if len(test) > 1 else 0,
            control_size=len(control),
            test_size=len(test),
            improvement_percentage=0,
            p_value=1.0,
            is_significant=False,
            confidence_interval=(0, 0),
            decision=DecisionType.CONTINUE_OBSERVING,
            recommendation=f"样本不足（对照组:{len(control)}, 测试组:{len(test)}），需要至少{self.MIN_SAMPLE_SIZE}个样本",
            statistical_power=0.0,
            effect_size=0.0,
            test_metadata={'metric_name': metric, 'error': 'insufficient_sample'}
        )

    def generate_ab_report(
        self,
        results: List[ABTestResult],
        output_path: Optional[str] = None
    ) -> str:
        """生成A/B测试报告"""
        lines = [
            "# A/B测试报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**置信水平**: {self.confidence_level:.0%}",
            f"**测试数量**: {len(results)}",
            "",
            "## 测试结果汇总",
            "",
            "| 测试ID | 对照均值 | 测试均值 | 改进% | P值 | 显著 | 决策 |",
            "|--------|----------|----------|-------|-----|------|------|",
        ]

        for r in results:
            icon = "✅" if r.is_significant and r.improvement_percentage > 0 else ("❌" if r.is_significant else "⏸️")
            lines.append(
                f"| {r.test_id[:20]} | {r.control_mean:.2f} | {r.test_mean:.2f} "
                f"| {r.improvement_percentage:+.1f}% | {r.p_value:.4f} "
                f"| {icon} | {r.decision.value} |"
            )

        adopted = [r for r in results if r.decision == DecisionType.ADOPT]
        rejected = [r for r in results if r.decision == DecisionType.REJECT]
        observing = [r for r in results if r.decision == DecisionType.CONTINUE_OBSERVING]

        lines.extend([
            "",
            "## 决策统计",
            "",
            f"- ✅ **采用**: {len(adopted)} 个",
            f"- ❌ **拒绝**: {len(rejected)} 个",
            f"- 🔍 **继续观察**: {len(observing)} 个",
            ""
        ])

        for result in results[:5]:
            lines.extend([
                f"### {result.test_id}",
                f"- **决策**: {result.recommendation}",
                f"- **效应量**: {result.effect_size:.3f} ({self._interpret_effect_size(result.effect_size)})",
                f"- **统计功效**: {result.statistical_power:.2f}",
                f"- **95% CI**: [{result.confidence_interval[0]:.3f}, {result.confidence_interval[1]:.3f}]",
                ""
            ])

        report = '\n'.join(lines)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)

        return report

    def _interpret_effect_size(self, d: float) -> str:
        """解释效应量大小"""
        abs_d = abs(d)
        if abs_d < 0.2:
            return "微小"
        elif abs_d < 0.5:
            return "小"
        elif abs_d < 0.8:
            return "中等"
        else:
            return "大"


class SmartRollbackManager:
    """
    智能回滚决策管理器

    基于退化程度选择合适的回滚策略，
    支持多级回滚和智能决策。
    """

    ROLLBACK_STRATEGIES = {
        'immediate': {
            'condition': 'critical_degradation',
            'action': 'full_rollback',
            'description': '立即完全回滚',
            'threshold': 0.25,
            'recovery_time': 5,
            'risk': 'low'
        },
        'gradual': {
            'condition': 'moderate_degradation',
            'action': 'partial_rollback',
            'description': '渐进式部分回滚',
            'threshold': 0.15,
            'recovery_time': 15,
            'risk': 'medium'
        },
        'monitor': {
            'condition': 'minor_degradation',
            'action': 'enhanced_monitoring',
            'description': '增强监控并准备回滚',
            'threshold': 0.08,
            'recovery_time': 30,
            'risk': 'very_low'
        },
        'continue': {
            'condition': 'within_threshold',
            'action': 'no_action',
            'description': '在阈值范围内，无需操作',
            'threshold': 0.08,
            'recovery_time': 0,
            'risk': 'none'
        }
    }

    METRIC_WEIGHTS = {
        'error_rate': 0.30,
        'response_time': 0.25,
        'throughput': 0.20,
        'cpu_usage': 0.10,
        'memory_usage': 0.10,
        'custom': 0.05
    }

    def __init__(self, custom_thresholds: Optional[Dict[str, float]] = None):
        self.thresholds = custom_thresholds or {}
        self.logger = logging.getLogger('SmartRollbackManager')
        self.rollback_history: List[RollbackDecision] = []

    def decide_rollback(
        self,
        metrics_before: Dict[str, float],
        metrics_after: Dict[str, float],
        context: Optional[Dict[str, Any]] = None
    ) -> RollbackDecision:
        """
        决定回滚策略

        Args:
            metrics_before: 优化前的指标字典
            metrics_after: 优化后的指标字典
            context: 额外上下文信息

        Returns:
            回滚决策，包含策略、原因、执行步骤
        """
        context = context or {}
        degradation = self._calculate_degradation(metrics_before, metrics_after)
        strategy_key = self._select_strategy(degradation)

        strategy_config = self.ROLLBACK_STRATEGIES[strategy_key]

        steps = self._get_rollback_steps(strategy_key, degradation, context)

        decision = RollbackDecision(
            decision_id=f"RB-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            strategy=RollbackStrategy(strategy_key),
            degradation_level=degradation['level'],
            reason=degradation['reason'],
            affected_metrics=degradation['affected_metrics'],
            degradation_percentages=degradation['percentages'],
            steps=steps,
            estimated_recovery_time_minutes=strategy_config['recovery_time'],
            risk_of_rollback=strategy_config['risk'],
            confidence=self._calculate_confidence(degradation, context),
            timestamp=datetime.now().isoformat()
        )

        self.rollback_history.append(decision)
        self.logger.info(
            f"回滚决策: {strategy_key}, 退化等级: {degradation['level']}, "
            f"置信度: {decision.confidence:.2f}"
        )

        return decision

    def _calculate_degradation(
        self,
        before: Dict[str, float],
        after: Dict[str, float]
    ) -> Dict[str, Any]:
        """计算各指标的退化程度"""
        percentages = {}
        affected_metrics = []
        weighted_degradation = 0.0
        total_weight = 0.0

        common_metrics = set(before.keys()) & set(after.keys())

        for metric in common_metrics:
            before_val = before[metric]
            after_val = after[metric]

            if before_val == 0:
                continue

            weight = self.METRIC_WEIGHTS.get(metric, 0.05)

            if metric in ['error_rate', 'response_time', 'cpu_usage', 'memory_usage']:
                pct_change = ((after_val - before_val) / before_val) * 100
            elif metric in ['throughput', 'success_rate']:
                pct_change = ((before_val - after_val) / before_val) * 100
            else:
                pct_change = ((after_val - before_val) / abs(before_val)) * 100

            percentages[metric] = round(pct_change, 2)

            if pct_change > 5:
                affected_metrics.append(metric)
                weighted_degradation += abs(pct_change) * weight

            total_weight += weight

        overall_degradation = weighted_degradation / total_weight if total_weight > 0 else 0

        level, reason = self._classify_degradation(overall_degradation, affected_metrics)

        return {
            'overall_degradation': round(overall_degradation, 2),
            'level': level,
            'reason': reason,
            'affected_metrics': affected_metrics,
            'percentages': percentages
        }

    def _classify_degradation(
        self,
        degradation: float,
        affected_metrics: List[str]
    ) -> Tuple[str, str]:
        """分类退化等级"""
        critical_threshold = self.thresholds.get('critical', 0.25)
        moderate_threshold = self.thresholds.get('moderate', 0.15)
        minor_threshold = self.thresholds.get('minor', 0.08)

        if degradation >= critical_threshold or 'error_rate' in affected_metrics:
            level = 'critical'
            reason = f"严重退化({degradation:.1f}%)，关键指标恶化，需要立即回滚"
        elif degradation >= moderate_threshold:
            level = 'moderate'
            reason = f"中度退化({degradation:.1f}%)，多个指标受影响，建议部分回滚"
        elif degradation >= minor_threshold:
            level = 'minor'
            reason = f"轻度退化({degradation:.1f}%)，建议加强监控并准备回滚方案"
        else:
            level = 'normal'
            reason = f"退化在可接受范围内({degradation:.1f}%)，可以继续观察"

        return level, reason

    def _select_strategy(self, degradation: Dict[str, Any]) -> str:
        """选择回滚策略"""
        level = degradation['level']

        if level == 'critical':
            return 'immediate'
        elif level == 'moderate':
            return 'gradual'
        elif level == 'minor':
            return 'monitor'
        else:
            return 'continue'

    def _get_rollback_steps(
        self,
        strategy: str,
        degradation: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """获取回滚执行步骤"""
        base_steps = {
            'immediate': [
                {'step': '1', 'action': '停止流量导入到新版本', 'duration': '1分钟'},
                {'step': '2', 'action': '切换到上一个稳定版本', 'duration': '2分钟'},
                {'step': '3', 'action': '验证服务恢复正常', 'duration': '1分钟'},
                {'step': '4', 'action': '通知相关团队并记录事件', 'duration': '1分钟'}
            ],
            'gradual': [
                {'step': '1', 'action': '将流量逐步切回旧版本（每次10%）', 'duration': '5分钟'},
                {'step': '2', 'action': '监控每步切换后的指标变化', 'duration': '持续'},
                {'step': '3', 'action': '如指标改善则继续，否则加速回滚', 'duration': '动态'},
                {'step': '4', 'action': '完成回滚后进行全面验证', 'duration': '5分钟'}
            ],
            'monitor': [
                {'step': '1', 'action': '提高监控采样频率至1次/分钟', 'duration': '立即'},
                {'step': '2', 'action': '设置更严格的告警阈值', 'duration': '1分钟'},
                {'step': '3', 'action': '准备回滚脚本并预加载', 'duration': '2分钟'},
                {'step': '4', 'action': '安排人员待命，随时准备执行回滚', 'duration': '持续'}
            ],
            'continue': [
                {'step': '1', 'action': '保持当前监控频率', 'duration': '持续'},
                {'step': '2', 'action': '记录当前指标作为新的基线', 'duration': '1分钟'},
                {'step': '3', 'action': '继续常规监控流程', 'duration': '持续'}
            ]
        }

        return base_steps.get(strategy, [])

    def _calculate_confidence(
        self,
        degradation: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        """计算决策置信度"""
        base_confidence = 0.8

        deg = degradation.get('overall_degradation', 0)
        if deg > 30:
            base_confidence = 0.95
        elif deg > 20:
            base_confidence = 0.90
        elif deg > 10:
            base_confidence = 0.85

        affected_count = len(degradation.get('affected_metrics', []))
        if affected_count >= 3:
            base_confidence += 0.05
        elif affected_count >= 2:
            base_confidence += 0.03

        if context.get('has_historical_data'):
            base_confidence += 0.02

        if context.get('team_experience') == 'senior':
            base_confidence += 0.03

        return min(0.99, max(0.5, base_confidence))

    def generate_rollback_report(
        self,
        decisions: List[RollbackDecision],
        output_path: Optional[str] = None
    ) -> str:
        """生成回滚决策报告"""
        lines = [
            "# 智能回滚决策报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**决策数量**: {len(decisions)}",
            "",
            "## 决策历史",
            "",
        ]

        for i, dec in enumerate(decisions, 1):
            strategy_icon = {
                RollbackStrategy.IMMEDIATE: "🚨",
                RollbackStrategy.GRADUAL: "⚠️",
                RollbackStrategy.MONITOR: "👁️",
                RollbackStrategy.CONTINUE: "✅"
            }.get(dec.strategy, "❓")

            lines.extend([
                f"### 决策{i}: {dec.decision_id} [{strategy_icon}]",
                f"- **策略**: {dec.strategy.value} - {self.ROLLBACK_STRATEGIES[dec.strategy.value]['description']}",
                f"- **退化等级**: {dec.degradation_level}",
                f"- **原因**: {dec.reason}",
                f"- **置信度**: {dec.confidence:.1%}",
                f"- **预计恢复时间**: {dec.estimated_recovery_time_minutes}分钟",
                f"- **回滚风险**: {dec.risk_of_rollback}",
                "- **受影响指标**:",
            ])

            for metric, pct in dec.degradation_percentages.items():
                icon = "📈" if pct > 0 else "📉"
                lines.append(f"  - {metric}: {pct:+.1f}% {icon}")

            if dec.steps:
                lines.append("- **执行步骤**:")
                for step in dec.steps:
                    lines.append(f"  - 步骤{step['step']}: {step['action']} ({step.get('duration', '-')})")

            lines.append("")

        report = '\n'.join(lines)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)

        return report


if __name__ == '__main__':
    print("增强型自优化系统模块已加载")
