"""
质量趋势分析与预测器 - Quality Trend Predictor v3.3.0

功能：
1. 历史数据趋势分析（7天/30天/90天视图）
2. 基于简单机器学习的质量预测
3. 质量改进建议报告生成
4. 与自演化系统联动接口

使用方法：
    predictor = QualityTrendPredictor()
    
    # 分析历史趋势
    analysis = predictor.analyze_trends(historical_data, period_days=30)
    
    # 预测未来质量
    prediction = predictor.predict_quality(current_metrics, history)
    
    # 生成改进报告
    report = predictor.generate_improvement_report(analysis)
    
    # 获取演化建议
    action = predictor.get_evolution_action(metrics)
"""

import json
import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    """趋势方向枚举"""
    IMPROVING = "improving"       # 改善中
    DECLINING = "declining"       # 恶化中
    STABLE = "stable"             # 稳定
    VOLATILE = "volatile"         # 波动大


class EvolutionAction(Enum):
    """演化动作类型"""
    NONE = "none"                 # 无需动作
    MONITOR = "monitor"           # 继续监控
    OPTIMIZE = "optimize"         # 优化调整
    REPAIR = "repair"             # 触发修复
    ITERATE = "iterate"           # 迭代升级


@dataclass
class TrendPoint:
    """趋势数据点"""
    timestamp: datetime
    value: float
    dimension: str
    
    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'dimension': self.dimension
        }


@dataclass
class TrendAnalysis:
    """趋势分析结果"""
    dimension: str
    direction: TrendDirection
    current_value: float
    previous_value: float
    change_rate: float
    trend_strength: float  # 0-1, 趋势强度
    prediction_7d: float   # 7天后的预测值
    prediction_30d: float  # 30天后的预测值
    confidence: float      # 预测置信度 (0-1)
    data_points: List[TrendPoint] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            'dimension': self.dimension,
            'direction': self.direction.value,
            'current_value': self.current_value,
            'previous_value': self.previous_value,
            'change_rate': f"{self.change_rate:.2f}%",
            'trend_strength': f"{self.trend_strength:.2f}",
            'prediction_7d': f"{self.prediction_7d:.1f}",
            'prediction_30d': f"{self.prediction_30d:.1f}",
            'confidence': f"{self.confidence:.2f}",
            'data_points_count': len(self.data_points),
            'data_points': [p.to_dict() for p in self.data_points[-10:]]  # 最近10个点
        }


@dataclass
class QualityPrediction:
    """质量预测结果"""
    overall_score_prediction: Dict[str, float]  # {时间范围: 预测分数}
    dimension_predictions: Dict[str, TrendAnalysis]
    risk_assessment: str                        # 风险评估描述
    recommendations: List[str]                  # 改进建议
    confidence_level: float                     # 整体置信度
    
    def to_dict(self) -> dict:
        return {
            'overall_score_prediction': self.overall_score_prediction,
            'dimension_predictions': {k: v.to_dict() for k, v in self.dimension_predictions.items()},
            'risk_assessment': self.risk_assessment,
            'recommendations': self.recommendations,
            'confidence_level': f"{self.confidence_level:.2f}"
        }


@dataclass
class ImprovementReport:
    """质量改进报告"""
    generated_at: datetime
    summary: str
    current_status: Dict[str, Any]
    trends_analysis: Dict[str, Any]
    priority_actions: List[Dict[str, Any]]
    evolution_suggestions: List[str]
    markdown_report: str
    
    def to_dict(self) -> dict:
        return {
            'generated_at': self.generated_at.isoformat(),
            'summary': self.summary,
            'current_status': self.current_status,
            'trends_analysis': self.trends_analysis,
            'priority_actions': self.priority_actions,
            'evolution_suggestions': self.evolution_suggestions,
            'markdown_report': self.markdown_report
        }
    
    def save_to_file(self, filepath: str):
        """保存到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.markdown_report)


class SimpleLinearRegression:
    """
    简单线性回归模型
    
    用于时间序列数据的趋势拟合和短期预测。
    不依赖外部机器学习库，使用纯Python实现。
    """
    
    @staticmethod
    def fit_predict(data_points: List[Tuple[float, float]], 
                   future_steps: int = 1) -> Tuple[float, float, float]:
        """
        拟合线性回归并预测未来值
        
        Args:
            data_points: [(x, y)] 数据点列表，x为时间索引，y为值
            future_steps: 未来预测步数
            
        Returns:
            (斜率, 截距, 下一个预测值)
        """
        if len(data_points) < 2:
            return 0.0, data_points[0][1] if data_points else 0.0, data_points[0][1] if data_points else 0.0
        
        n = len(data_points)
        sum_x = sum(x for x, y in data_points)
        sum_y = sum(y for x, y in data_points)
        sum_xy = sum(x * y for x, y in data_points)
        sum_x2 = sum(x * x for x, y in data_points)
        
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0, sum_y / n, sum_y / n
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n
        
        next_x = max(x for x, y in data_points) + future_steps
        predicted_y = slope * next_x + intercept
        
        return slope, intercept, predicted_y
    
    @staticmethod
    def calculate_r_squared(data_points: List[Tuple[float, float]], 
                           slope: float, intercept: float) -> float:
        """计算R²决定系数"""
        if len(data_points) < 2:
            return 1.0
        
        y_mean = sum(y for x, y in data_points) / len(data_points)
        ss_tot = sum((y - y_mean) ** 2 for x, y in data_points)
        ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in data_points)
        
        if ss_tot == 0:
            return 1.0
        
        return max(0, 1 - (ss_res / ss_tot))
    
    @staticmethod
    def calculate_confidence(n: int, r_squared: float) -> float:
        """基于样本量和R²计算置信度"""
        base_confidence = min(r_squared, 0.95)
        size_factor = min(n / 30, 1.0)  # 30个点达到满置信度
        return base_confidence * size_factor


class ExponentialSmoothing:
    """
    指数平滑预测器
    
    适用于具有趋势和季节性的时间序列数据。
    使用Holt-Winters方法的简化版本。
    """
    
    @staticmethod
    def predict(data: List[float], alpha: float = 0.3, 
                beta: float = 0.1, steps: int = 1) -> float:
        """
        双指数平滑预测（带趋势）
        
        Args:
            data: 历史数据列表
            alpha: 水平平滑因子
            beta: 趋势平滑因子
            steps: 预测步数
            
        Returns:
            预测值
        """
        if not data:
            return 0.0
        
        if len(data) == 1:
            return data[0]
        
        level = data[0]
        trend = data[1] - data[0] if len(data) > 1 else 0
        
        for i in range(1, len(data)):
            prev_level = level
            prev_trend = trend
            level = alpha * data[i] + (1 - alpha) * (prev_level + prev_trend)
            trend = beta * (level - prev_level) + (1 - beta) * prev_trend
        
        return level + steps * trend


class QualityTrendPredictor:
    """
    质量趋势预测器主类
    
    提供历史数据分析、趋势预测、改进建议等完整功能，
    并与自演化系统联动提供演化决策支持。
    """
    
    DIMENSIONS = [
        'code_quality',      # 代码质量
        'test_coverage',     # 测试覆盖
        'tech_debt',         # 技术债务
        'performance',       # 性能基准
        'security',          # 安全合规
        'ux'                 # 用户体验
    ]
    
    DIMENSION_WEIGHTS = {
        'code_quality': 0.20,
        'test_coverage': 0.20,
        'tech_debt': 0.15,
        'performance': 0.15,
        'security': 0.15,
        'ux': 0.15
    }
    
    THRESHOLDS = {
        'excellent': 90,
        'good': 80,
        'acceptable': 70,
        'poor': 60
    }
    
    def __init__(self):
        """初始化预测器"""
        self.historical_data: Dict[str, List[TrendPoint]] = {}
        self.predictions_cache: Dict[str, Any] = {}
        logger.info("Quality Trend Predictor v3.3.0 initialized")
    
    def add_data_point(self, dimension: str, value: float, 
                      timestamp: Optional[datetime] = None):
        """
        添加数据点
        
        Args:
            dimension: 维度名称
            value: 值 (0-100)
            timestamp: 时间戳，默认当前时间
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        point = TrendPoint(timestamp=timestamp, value=value, dimension=dimension)
        
        if dimension not in self.historical_data:
            self.historical_data[dimension] = []
        
        self.historical_data[dimension].append(point)
        self.predictions_cache.clear()  # 清空缓存
    
    def load_historical_data(self, data: List[Dict]):
        """
        批量加载历史数据
        
        Args:
            data: 数据字典列表，每个包含timestamp, dimension, value
        """
        for item in data:
            ts = datetime.fromisoformat(item['timestamp']) if isinstance(item['timestamp'], str) else item['timestamp']
            self.add_data_point(item['dimension'], item['value'], ts)
        
        logger.info(f"Loaded {len(data)} historical data points")
    
    def analyze_trends(self, historical_data: List[Dict] = None, 
                      period_days: int = 30) -> Dict[str, TrendAnalysis]:
        """
        分析历史数据趋势
        
        Args:
            historical_data: 历史数据列表（可选，不传则使用内部数据）
            period_days: 分析周期（天）
            
        Returns:
            各维度的趋势分析结果
        """
        if historical_data:
            self.load_historical_data(historical_data)
        
        results = {}
        cutoff_time = datetime.now() - timedelta(days=period_days)
        
        for dimension in self.DIMENSIONS:
            points = self.historical_data.get(dimension, [])
            
            filtered_points = [p for p in points if p.timestamp >= cutoff_time]
            
            if len(filtered_points) < 2:
                results[dimension] = self._create_default_analysis(dimension)
                continue
            
            analysis = self._analyze_single_dimension(filtered_points, dimension)
            results[dimension] = analysis
        
        return results
    
    def _analyze_single_dimension(self, points: List[TrendPoint], 
                                  dimension: str) -> TrendAnalysis:
        """分析单个维度"""
        sorted_points = sorted(points, key=lambda p: p.timestamp)
        
        current_value = sorted_points[-1].value
        previous_value = sorted_points[0].value
        
        change_rate = ((current_value - previous_value) / max(previous_value, 1)) * 100
        
        data_tuples = [(i, p.value) for i, p in enumerate(sorted_points)]
        slope, intercept, pred_next = SimpleLinearRegression.fit_predict(data_tuples, 7)
        _, _, pred_30 = SimpleLinearRegression.fit_predict(data_tuples, 30)
        
        r_squared = SimpleLinearRegression.calculate_r_squared(data_tuples, slope, intercept)
        confidence = SimpleLinearRegression.calculate_confidence(len(sorted_points), r_squared)
        
        direction = self._determine_direction(change_rate, r_squared, sorted_points)
        trend_strength = abs(r_squared) * min(len(sorted_points) / 20, 1.0)
        
        exp_pred_7d = ExponentialSmoothing.predict([p.value for p in sorted_points], steps=7)
        exp_pred_30d = ExponentialSmoothing.predict([p.value for p in sorted_points], steps=30)
        
        pred_7d = (pred_next + exp_pred_7d) / 2  # 平均两种方法
        pred_30d = (pred_30 + exp_pred_30d) / 2
        
        return TrendAnalysis(
            dimension=dimension,
            direction=direction,
            current_value=current_value,
            previous_value=previous_value,
            change_rate=change_rate,
            trend_strength=trend_strength,
            prediction_7d=max(0, min(100, pred_7d)),
            prediction_30d=max(0, min(100, pred_30d)),
            confidence=confidence,
            data_points=sorted_points
        )
    
    def _determine_direction(self, change_rate: float, r_squared: float,
                            points: List[TrendPoint]) -> TrendDirection:
        """确定趋势方向"""
        if r_squared < 0.3:
            return TrendDirection.VOLATILE
        
        if change_rate > 5:
            return TrendDirection.IMPROVING
        elif change_rate < -5:
            return TrendDirection.DECLINING
        else:
            return TrendDirection.STABLE
    
    def _create_default_analysis(self, dimension: str) -> TrendAnalysis:
        """创建默认分析结果"""
        return TrendAnalysis(
            dimension=dimension,
            direction=TrendDirection.STABLE,
            current_value=75.0,
            previous_value=75.0,
            change_rate=0.0,
            trend_strength=0.0,
            prediction_7d=75.0,
            prediction_30d=75.0,
            confidence=0.0,
            data_points=[]
        )
    
    def predict_quality(self, current_metrics: Dict[str, float],
                       history: List[Dict] = None) -> QualityPrediction:
        """
        预测未来质量走向
        
        使用多种方法综合预测：
        1. 线性回归趋势外推
        2. 指数平滑预测
        3. 维度加权综合评分
        
        Args:
            current_metrics: 当前各维度指标 {dimension: score}
            history: 历史数据
            
        Returns:
            质量预测结果对象
        """
        if history:
            self.load_historical_data(history)
        
        trends = self.analyze_trends(period_days=30)
        
        overall_predictions = {}
        
        for period in ['7d', '30d', '90d']:
            weighted_score = 0.0
            total_weight = 0.0
            
            for dim, analysis in trends.items():
                weight = self.DIMENSION_WEIGHTS.get(dim, 0.1)
                
                if period == '7d':
                    pred_val = analysis.prediction_7d
                elif period == '30d':
                    pred_val = analysis.prediction_30d
                else:
                    pred_val = analysis.prediction_30d + (
                        (analysis.prediction_30d - analysis.current_value) * 2
                    )
                
                pred_val = max(0, min(100, pred_val))
                weighted_score += pred_val * weight
                total_weight += weight
            
            overall_predictions[period] = weighted_score / max(total_weight, 1)
        
        risk_assessment = self._assess_risk(trends, overall_predictions)
        recommendations = self._generate_recommendations(trends, overall_predictions)
        avg_confidence = sum(a.confidence for a in trends.values()) / max(len(trends), 1)
        
        return QualityPrediction(
            overall_score_prediction={k: round(v, 1) for k, v in overall_predictions.items()},
            dimension_predictions=trends,
            risk_assessment=risk_assessment,
            recommendations=recommendations,
            confidence_level=avg_confidence
        )
    
    def _assess_risk(self, trends: Dict[str, TrendAnalysis],
                    predictions: Dict[str, float]) -> str:
        """风险评估"""
        risk_factors = []
        declining_dims = [dim for dim, t in trends.items() 
                         if t.direction == TrendDirection.DECLINING]
        
        if declining_dims:
            risk_factors.append(f"以下维度呈下降趋势: {', '.join(declining_dims)}")
        
        pred_30d = predictions.get('30d', 75)
        if pred_30d < self.THRESHOLDS['acceptable']:
            risk_factors.append("30天后预期质量可能降至可接受水平以下")
        elif pred_30d < self.THRESHOLDS['good']:
            risk_factors.append("30天后预期质量可能降至良好水平以下")
        
        volatile_dims = [dim for dim, t in trends.items() 
                        if t.direction == TrendDirection.VOLATILE]
        if volatile_dims:
            risk_factors.append(f"以下维度波动较大: {', '.join(volatile_dims)}")
        
        if not risk_factors:
            return "✅ 当前风险较低，整体质量稳定向好"
        else:
            return "⚠️ " + "; ".join(risk_factors)
    
    def _generate_recommendations(self, trends: Dict[str, TrendAnalysis],
                                 predictions: Dict[str, float]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        for dim, analysis in trends.items():
            if analysis.direction == TrendDirection.DECLINING and analysis.current_value < 70:
                recommendations.append(
                    f"🔴 紧急: {dim}维度持续下降({analysis.change_rate:.1f}%)，"
                    f"当前值{analysis.current_value:.1f}，需立即关注"
                )
            elif analysis.direction == TrendDirection.DECLINING:
                recommendations.append(
                    f"🟡 关注: {dim}维度有下降趋势({analysis.change_rate:.1f}%)，"
                    f"建议制定预防措施"
                )
            elif analysis.current_value < self.THRESHOLDS['good']:
                recommendations.append(
                    f"🟢 改进: {dim}维度当前值偏低({analysis.current_value:.1f})，"
                    f"建议持续优化"
                )
        
        pred_7d = predictions.get('7d', 75)
        if pred_7d > predictions.get('30d', 75):
            recommendations.append(
                "📊 建议: 长期预测显示质量可能下降，应提前规划改进措施"
            )
        
        return recommendations[:8]  # 限制数量
    
    def generate_improvement_report(self, analysis_result: Dict[str, TrendAnalysis] = None,
                                   output_format: str = 'markdown') -> ImprovementReport:
        """
        生成质量改进建议报告
        
        Args:
            analysis_result: 趋势分析结果（可选）
            output_format: 输出格式 ('markdown', 'json')
            
        Returns:
            改进报告对象
        """
        if analysis_result is None:
            analysis_result = self.analyze_trends(period_days=30)
        
        current_status = self._build_current_status(analysis_result)
        trends_summary = self._build_trends_summary(analysis_result)
        priority_actions = self._prioritize_actions(analysis_result)
        evolution_suggestions = self._get_evolution_suggestions(analysis_result)
        
        markdown = self._format_markdown_report(
            current_status, trends_summary, 
            priority_actions, evolution_suggestions
        )
        
        report = ImprovementReport(
            generated_at=datetime.now(),
            summary=self._generate_summary(analysis_result),
            current_status=current_status,
            trends_analysis=trends_summary,
            priority_actions=priority_actions,
            evolution_suggestions=evolution_suggestions,
            markdown_report=markdown
        )
        
        return report
    
    def _build_current_status(self, analysis: Dict[str, TrendAnalysis]) -> Dict:
        """构建当前状态"""
        status = {}
        for dim, result in analysis.items():
            status[dim] = {
                'score': round(result.current_value, 1),
                'status': self._get_score_status(result.current_value),
                'trend': result.direction.value,
                'change': f"{result.change_rate:+.1f}%"
            }
        return status
    
    def _get_score_status(self, score: float) -> str:
        """获取分数状态"""
        if score >= self.THRESHOLDS['excellent']:
            return "优秀 ✅"
        elif score >= self.THRESHOLDS['good']:
            return "良好 🟢"
        elif score >= self.THRESHOLDS['acceptable']:
            return "可接受 🟡"
        else:
            return "需改进 🔴"
    
    def _build_trends_summary(self, analysis: Dict[str, TrendAnalysis]) -> Dict:
        """构建趋势摘要"""
        summary = {}
        for dim, result in analysis.items():
            summary[dim] = {
                'direction': result.direction.value,
                'strength': round(result.trend_strength, 2),
                'prediction_7d': round(result.prediction_7d, 1),
                'prediction_30d': round(result.prediction_30d, 1),
                'confidence': round(result.confidence, 2)
            }
        return summary
    
    def _prioritize_actions(self, analysis: Dict[str, TrendAnalysis]) -> List[Dict]:
        """优先级排序的改进行动"""
        actions = []
        
        for dim, result in analysis.items():
            urgency = self._calculate_urgency(result)
            if urgency > 0.3:
                actions.append({
                    'dimension': dim,
                    'urgency': round(urgency, 2),
                    'current_score': round(result.current_value, 1),
                    'trend': result.direction.value,
                    'action': self._suggest_action(dim, result)
                })
        
        actions.sort(key=lambda x: x['urgency'], reverse=True)
        return actions[:10]
    
    def _calculate_urgency(self, analysis: TrendAnalysis) -> float:
        """计算紧急程度 (0-1)"""
        score_factor = max(0, (80 - analysis.current_value) / 80)
        trend_factor = 0
        if analysis.direction == TrendDirection.DECLINING:
            trend_factor = min(abs(analysis.change_rate) / 20, 0.4)
        elif analysis.direction == TrendDirection.VOLATILE:
            trend_factor = 0.2
        
        return min(score_factor + trend_factor, 1.0)
    
    def _suggest_action(self, dimension: str, analysis: TrendAnalysis) -> str:
        """建议具体行动"""
        actions_map = {
            'code_quality': [
                "进行代码审查和重构",
                "优化复杂度过高的函数",
                "消除代码重复"
            ],
            'test_coverage': [
                "补充单元测试用例",
                "提高分支覆盖率",
                "增加边界条件测试"
            ],
            'tech_debt': [
                "处理TODO和FIXME标记",
                "升级废弃API",
                "优化代码结构"
            ],
            'performance': [
                "性能瓶颈分析和优化",
                "数据库查询优化",
                "缓存策略优化"
            ],
            'security': [
                "安全漏洞修复",
                "依赖库更新",
                "权限配置审计"
            ],
            'ux': [
                "用户反馈收集和分析",
                "界面响应优化",
                "流程简化"
            ]
        }
        
        suggestions = actions_map.get(dimension, ["持续优化"])
        idx = min(int(analysis.current_value // 25), len(suggestions) - 1)
        return suggestions[idx]
    
    def _get_evolution_suggestions(self, analysis: Dict[str, TrendAnalysis]) -> List[str]:
        """获取演化系统联动建议"""
        suggestions = []
        
        declining = [dim for dim, r in analysis.items() 
                    if r.direction == TrendDirection.DECLINING and r.current_value < 70]
        
        if declining:
            suggestions.append(
                f"触发自动修复流程处理以下维度: {', '.join(declining)}"
            )
        
        critical_dims = [dim for dim, r in analysis.items() if r.current_value < 60]
        if critical_dims:
            suggestions.append(
                f"启动紧急优化迭代以提升: {', '.join(critical_dims)}"
            )
        
        all_improving = all(r.direction == TrendDirection.IMPROVING or r.direction == TrendDirection.STABLE 
                          for r in analysis.values())
        if all_improving:
            suggestions.append("整体质量稳定向好，可考虑进入下一个功能迭代周期")
        
        volatile = [dim for dim, r in analysis.items() if r.direction == TrendDirection.VOLATILE]
        if volatile:
            suggestions.append(
                f"增加监控频率以跟踪高波动维度: {', '.join(volatile)}"
            )
        
        return suggestions
    
    def _format_markdown_report(self, status: Dict, trends: Dict,
                               actions: List[Dict], evolution: List[str]) -> str:
        """格式化为Markdown报告"""
        lines = [
            "# 质量改进建议报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**版本**: v3.3.0",
            "",
            "---",
            "",
            "## 📊 当前状态总览",
            ""
        ]
        
        for dim, info in status.items():
            lines.append(f"- **{dim}**: {info['score']} ({info['status']}) | "
                        f"趋势: {info['trend']} ({info['change']})")
        
        lines.extend([
            "",
            "## 📈 趋势分析",
            ""
        ])
        
        for dim, trend in trends.items():
            emoji = {'improving': '↗️', 'declining': '↘️', 'stable': '➡️', 'volatile': '〰️'}
            lines.append(f"### {dim}")
            lines.append(f"- 方向: {emoji.get(trend['direction'], '')} {trend['direction']}")
            lines.append(f"- 趋势强度: {trend['strength']}")
            lines.append(f"- 7天预测: {trend['prediction_7d']} | 30天预测: {trend['prediction_30d']}")
            lines.append(f"- 置信度: {trend['confidence']}")
            lines.append("")
        
        if actions:
            lines.extend([
                "## 🎯 优先改进行动",
                ""
            ])
            for i, action in enumerate(actions, 1):
                lines.append(f"### {i}. {action['dimension']} (紧急度: {action['urgency']})")
                lines.append(f"- 当前得分: **{action['current_score']}**")
                lines.append(f"- 趋势: {action['trend']}")
                lines.append(f"- 建议行动: {action['action']}")
                lines.append("")
        
        if evolution:
            lines.extend([
                "## 🔄 自演化系统建议",
                ""
            ])
            for sug in evolution:
                lines.append(f"- {sug}")
            lines.append("")
        
        lines.extend([
            "---",
            "",
            "*本报告由 Quality Trend Predictor v3.3.0 自动生成*"
        ])
        
        return "\n".join(lines)
    
    def _generate_summary(self, analysis: Dict[str, TrendAnalysis]) -> str:
        """生成摘要"""
        scores = [r.current_value for r in analysis.values()]
        avg_score = sum(scores) / max(len(scores), 1)
        
        improving = sum(1 for r in analysis.values() if r.direction == TrendDirection.IMPROVING)
        declining = sum(1 for r in analysis.values() if r.direction == TrendDirection.DECLINING)
        
        return (f"当前平均质量分: {avg_score:.1f}/100 | "
               f"改善中: {improving}项 | 下降: {declining}项 | "
               f"总体状态: {'良好' if avg_score >= 80 else '需关注'}")
    
    def get_evolution_action(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        与自演化系统联动
        
        根据当前指标判断需要哪种演化动作：
        - NONE: 无需动作，继续运行
        - MONITOR: 继续监控，暂不干预
        - OPTIMIZE: 进行参数调优和微调
        - REPAIR: 触发自动修复流程
        - ITERATE: 启动新的迭代周期
        
        Args:
            metrics: 当前各维度指标
            
        Returns:
            包含建议动作及详细信息的字典
        """
        prediction = self.predict_quality(metrics)
        
        current_avg = sum(metrics.values()) / max(len(metrics), 1)
        pred_7d = prediction.overall_score_prediction.get('7d', current_avg)
        pred_30d = prediction.overall_score_prediction.get('30d', current_avg)
        
        decline_rate = (current_avg - pred_30d) if pred_30d < current_avg else 0
        
        critical_dims = [dim for dim, val in metrics.items() if val < 50]
        warning_dims = [dim for dim, val in metrics.items() if 50 <= val < 70]
        
        if critical_dims:
            action = EvolutionAction.REPAIR
            reason = f"存在严重问题维度: {', '.join(critical_dims)}"
        elif decline_rate > 10 or pred_30d < 65:
            action = EvolutionAction.ITERATE
            reason = f"质量下降趋势明显，预计30天后降至{pred_30d:.1f}"
        elif warning_dims or decline_rate > 5:
            action = EvolutionAction.OPTIMIZE
            reason = f"需要优化: {', '.join(warning_dims) if warning_dims else '轻微下降趋势'}"
        elif current_avg >= 85 and pred_7d >= current_avg:
            action = EvolutionAction.NONE
            reason = "质量优秀且稳定"
        else:
            action = EvolutionAction.MONITOR
            reason = "正常监控范围内"
        
        return {
            'action': action.value,
            'reason': reason,
            'current_score': round(current_avg, 1),
            'prediction_7d': round(pred_7d, 1),
            'prediction_30d': round(pred_30d, 1),
            'confidence': round(prediction.confidence_level, 2),
            'recommendations': prediction.recommendations,
            'trigger_conditions': {
                'critical_dimensions': critical_dims,
                'warning_dimensions': warning_dims,
                'decline_rate': round(decline_rate, 1)
            },
            'suggested_parameters': self._get_suggested_params(action, metrics)
        }
    
    def _get_suggested_params(self, action: EvolutionAction, 
                             metrics: Dict[str, float]) -> Dict[str, Any]:
        """获取建议的演化参数"""
        params = {
            'action_type': action.value,
            'priority_list': [],
            'resource_allocation': {},
            'timeline': None
        }
        
        if action == EvolutionAction.REPAIR:
            params['priority_list'] = sorted(
                [(dim, val) for dim, val in metrics.items() if val < 50],
                key=lambda x: x[1]
            )
            params['resource_allocation'] = {'engineering': 'high', 'qa': 'high'}
            params['timeline'] = '1-3 days'
        
        elif action == EvolutionAction.OPTIMIZE:
            params['priority_list'] = sorted(
                [(dim, val) for dim, val in metrics.items() if 50 <= val < 80],
                key=lambda x: x[1]
            )
            params['resource_allocation'] = {'engineering': 'medium', 'qa': 'medium'}
            params['timeline'] = '1-2 weeks'
        
        elif action == EvolutionAction.ITERATE:
            params['priority_list'] = list(metrics.items())
            params['resource_allocation'] = {'engineering': 'high', 'qa': 'high', 'design': 'medium'}
            params['timeline'] = '2-4 weeks'
        
        return params
    
    def export_prediction(self, filepath: str, prediction: QualityPrediction = None):
        """导出预测结果"""
        if prediction is None:
            prediction = self.predict_quality({})
        
        data = prediction.to_dict()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Prediction exported to {filepath}")


# 快速示例函数
def quick_example():
    """快速演示示例"""
    print("="*60)
    print("  Quality Trend Predictor v3.3.0 - Quick Demo")
    print("="*60)
    
    predictor = QualityTrendPredictor()
    
    # 模拟历史数据（最近30天）
    base_date = datetime.now()
    sample_data = []
    
    for days_ago in range(30, 0, -1):
        ts = base_date - timedelta(days=days_ago)
        noise = __import__('random').uniform(-2, 2)
        
        sample_data.append({
            'timestamp': ts.isoformat(),
            'dimension': 'code_quality',
            'value': 82 + (30 - days_ago) * 0.2 + noise
        })
        sample_data.append({
            'timestamp': ts.isoformat(),
            'dimension': 'test_coverage',
            'value': 78 + (30 - days_ago) * 0.3 + noise
        })
        sample_data.append({
            'timestamp': ts.isoformat(),
            'dimension': 'tech_debt',
            'value': 75 - (30 - days_ago) * 0.1 + noise
        })
        sample_data.append({
            'timestamp': ts.isoformat(),
            'dimension': 'performance',
            'value:': 88 + noise * 0.5
        })
    
    predictor.load_historical_data(sample_data)
    
    print("\n1️⃣  趋势分析:")
    trends = predictor.analyze_trends(period_days=30)
    for dim, analysis in trends.items():
        print(f"   {dim}: {analysis.direction.value} "
              f"(当前: {analysis.current_value:.1f}, 变化: {analysis.change_rate:+.1f}%)")
    
    print("\n2️⃣  质量预测:")
    current = {dim: trends[dim].current_value for dim in predictor.DIMENSIONS}
    prediction = predictor.predict_quality(current)
    print(f"   7天后预计: {prediction.overall_score_prediction['7d']}")
    print(f"   30天后预计: {prediction.overall_score_prediction['30d']}")
    print(f"   风险评估: {prediction.risk_assessment}")
    
    print("\n3️⃣  改进建议:")
    for rec in prediction.recommendations[:3]:
        print(f"   • {rec}")
    
    print("\n4️⃣  演化动作建议:")
    action = predictor.get_evolution_action(current)
    print(f"   建议动作: {action['action'].upper()}")
    print(f"   原因: {action['reason']}")


if __name__ == '__main__':
    print("="*60)
    print("  Quality Trend Predictor v3.3.0")
    print("  质量趋势分析 | 智能预测 | 改进建议 | 演化联动")
    print("="*60)
    
    predictor = QualityTrendPredictor()
    
    print("\n✅ 已初始化预测器")
    print(f"📊 监控维度: {', '.join(predictor.DIMENSIONS)}")
    print(f"⚖️  权重配置: {predictor.DIMENSION_WEIGHTS}")
    print(f"📏 评分阈值: {predictor.THRESHOLDS}")
    
    print("\n💡 运行 quick_example() 查看完整演示")
