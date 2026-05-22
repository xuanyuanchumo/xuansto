#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
六维质量监控聚合器 (SixDimensionalQualityMonitor)
===============================================

统一协调六个维度的监控任务，提供全面的质量扫描和报告。

六维体系:
1. 代码质量维度 (Code Quality)
2. 测试覆盖维度 (Test Coverage)
3. 技术债务维度 (Technical Debt)
4. 性能基准维度 (Performance)
5. 安全合规维度 (Security Compliance)
6. 用户体验维度 (User Experience)

使用示例:
    >>> from skillscripts.monitoring.six_dimensional_monitor import SixDimensionalQualityMonitor
    >>> monitor = SixDimensionalQualityMonitor()
    >>> report = monitor.run_full_scan('path/to/project')
    >>> print(f"总体评分: {report['overall_score']}")
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class SixDimensionalQualityMonitor:
    """
    六维质量监控聚合器

    协调所有维度的监控任务，执行完整的多维度质量扫描，
    并生成综合性的质量报告。

    Attributes:
        DIMENSIONS: 六个监控维度的定义和对应监控器类
    """

    DIMENSIONS: List[tuple] = [
        ('code_quality', 'CodeQualityMonitor', '代码质量'),
        ('test_coverage', 'TestCoverageMonitor', '测试覆盖'),
        ('tech_debt', 'TechDebtTracker', '技术债务'),
        ('performance', 'PerformanceBaselineMonitor', '性能基准'),
        ('security_compliance', 'SecurityComplianceMonitor', '安全合规'),
        ('user_experience', 'UxMonitor', '用户体验')
    ]

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化六维监控聚合器

        Args:
            logger: 可选的日志记录器
        """
        self.logger = logger or logging.getLogger(__name__)
        self._setup_logging()

        self._monitors = {}
        self._initialize_monitors()

    def _setup_logging(self):
        """配置日志"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _initialize_monitors(self) -> None:
        """
        初始化所有维度的监控器

        动态导入并实例化各维度的监控器类
        """
        for dim_key, monitor_class_name, dim_name in self.DIMENSIONS:
            try:
                if dim_key == 'code_quality':
                    from skillscripts.monitoring.code_quality_monitor import CodeQualityMonitor
                    self._monitors[dim_key] = CodeQualityMonitor(self.logger)

                elif dim_key == 'security_compliance':
                    from skillscripts.monitoring.security_compliance_monitor import SecurityComplianceMonitor
                    self._monitors[dim_key] = SecurityComplianceMonitor(self.logger)

                elif dim_key == 'user_experience':
                    from skillscripts.monitoring.ux_monitor import UxMonitor
                    self._monitors[dim_key] = UxMonitor(self.logger)

                elif dim_key == 'tech_debt':
                    from skillscripts.monitoring.tech_debt_tracker import TechDebtTracker
                    self._monitors[dim_key] = TechDebtTracker(logger=self.logger)

                else:
                    self._monitors[dim_key] = None

                self.logger.debug(f"初始化 {dim_name} 监控器: {'✅' if self._monitors.get(dim_key) else '⚠️'}")

            except Exception as e:
                self.logger.warning(f"无法初始化 {dim_name} 监控器: {e}")
                self._monitors[dim_key] = None

    def run_full_scan(self, project_path: str) -> Dict[str, Any]:
        """
        执行完整的六维质量扫描

        对项目进行所有维度的质量检查，生成综合性报告。

        Args:
            project_path: 项目根目录路径

        Returns:
            包含所有维度数据的聚合报告，格式为：
            {
                'scan_time': 扫描时间,
                'project': 项目路径,
                'dimensions': 各维度详细数据,
                'overall_score': 总体评分(0-100),
                'alerts': 告警列表,
                'summary': 摘要信息,
                'recommendations': 改进建议
            }

        示例:
            >>> monitor = SixDimensionalQualityMonitor()
            >>> report = monitor.run_full_scan('myproject')
            >>> print(f"总体评分: {report['overall_score']}/100")
        """
        self.logger.info(f"开始六维质量全量扫描: {project_path}")

        report = {
            'scan_time': datetime.now().isoformat(),
            'project': project_path,
            'dimensions': {},
            'dimension_scores': {},
            'overall_score': 0,
            'alerts': [],
            'summary': {
                'total_dimensions': len(self.DIMENSIONS),
                'completed_dimensions': 0,
                'failed_dimensions': 0,
                'total_alerts': 0
            },
            'recommendations': []
        }

        scores = []

        for dim_key, _, dim_name in self.DIMENSIONS:
            try:
                monitor_instance = self._monitors.get(dim_key)

                if not monitor_instance:
                    self.logger.warning(f"{dim_name} 监控器未初始化，跳过")
                    continue

                self.logger.info(f"正在扫描 [{dim_name}]...")

                if hasattr(monitor_instance, 'collect'):
                    dim_data = monitor_instance.collect(project_path)
                elif hasattr(monitor_instance, 'scan'):
                    dim_data = monitor_instance.scan()
                    dim_data = self._normalize_tech_debt_data(dim_data)
                elif hasattr(monitor_instance, 'collect_metrics'):
                    dim_data = monitor_instance.collect_metrics()
                else:
                    raise NotImplementedError(f"{dim_name} 监控器缺少采集方法")

                report['dimensions'][dim_key] = {
                    'name': dim_name,
                    'data': dim_data,
                    'status': 'success'
                }

                score = self._calculate_dimension_score(dim_key, dim_data)
                scores.append(score)
                report['dimension_scores'][dim_key] = score

                alerts = self._check_alert_conditions(dim_key, dim_data)
                report['alerts'].extend(alerts)

                report['summary']['completed_dimensions'] += 1

                self.logger.info(
                    f"[{dim_name}] 扫描完成，得分: {score:.1f}, "
                    f"告警数: {len(alerts)}"
                )

            except Exception as e:
                self.logger.error(f"[{dim_name}] 扫描失败: {e}")

                report['dimensions'][dim_key] = {
                    'name': dim_name,
                    'status': 'error',
                    'error': str(e)
                }

                report['summary']['failed_dimensions'] += 1

        if scores:
            report['overall_score'] = sum(scores) / len(scores)

        report['summary']['total_alerts'] = len(report['alerts'])

        report['recommendations'] = self._generate_recommendations(report)

        total_time = (
            datetime.fromisoformat(report['scan_time']) - 
            datetime.fromisoformat(report['scan_time'])
        ).total_seconds() if False else 0

        self.logger.info(
            f"六维扫描完成: 总体评分 {report['overall_score']:.1f}/100, "
            f"完成 {report['summary']['completed_dimensions']}/{len(self.DIMENSIONS)} 个维度, "
            f"发现 {len(report['alerts'])} 个告警"
        )

        return report

    def run_dimension_scan(
        self,
        dimension: str,
        project_path: str
    ) -> Dict[str, Any]:
        """
        执行单个维度的扫描

        Args:
            dimension: 维度标识（如 'code_quality', 'security' 等）
            project_path: 项目路径

        Returns:
            该维度的扫描结果
        """
        valid_dimensions = [d[0] for d in self.DIMENSIONS]

        if dimension not in valid_dimensions:
            raise ValueError(
                f"无效的维度: {dimension}. 有效值: {valid_dimensions}"
            )

        monitor_instance = self._monitors.get(dimension)

        if not monitor_instance:
            return {
                'status': 'error',
                'error': f'{dimension} 监控器未初始化'
            }

        try:
            if hasattr(monitor_instance, 'collect'):
                data = monitor_instance.collect(project_path)
            elif hasattr(monitor_instance, 'scan'):
                data = monitor_instance.scan()
            elif hasattr(monitor_instance, 'collect_metrics'):
                data = monitor_instance.collect_metrics()
            else:
                raise NotImplementedError("缺少采集方法")

            return {
                'status': 'success',
                'dimension': dimension,
                'data': data,
                'score': self._calculate_dimension_score(dimension, data),
                'scan_time': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'error',
                'dimension': dimension,
                'error': str(e)
            }

    def _calculate_dimension_score(
        self,
        dimension: str,
        data: Dict[str, Any]
    ) -> float:
        """
        计算单维度得分

        根据该维度的各项指标状态计算综合得分

        Args:
            dimension: 维度标识
            data: 维度数据

        Returns:
            得分 (0-100)
        """
        if not isinstance(data, dict) or not data:
            return 50.0

        scores = []

        for metric_key, metric_data in data.items():
            if not isinstance(metric_data, dict):
                continue

            status = metric_data.get('status', 'unknown')
            threshold = metric_data.get('threshold')
            value = metric_data.get('value')

            if value is None:
                continue

            if status == 'pass':
                if threshold and threshold > 0:
                    performance_ratio = min(value / threshold, 2.0)
                    score = max(80, 100 - abs(1 - performance_ratio) * 20)
                else:
                    score = 95
            elif status == 'warning':
                score = 70
            elif status == 'fail':
                score = 40
            elif status == 'error':
                score = 30
            else:
                score = 60

            scores.append(score)

        if dimension == 'security_compliance' and 'risk_score' in data:
            risk_score = data['risk_score']
            security_score = max(0, 100 - risk_score)
            scores.append(security_score)

        return sum(scores) / len(scores) if scores else 50.0

    def _check_alert_conditions(
        self,
        dimension: str,
        data: Dict[str, Any]
    ) -> List[Dict]:
        """
        检查告警条件

        Args:
            dimension: 维度标识
            data: 维度数据

        Returns:
            告警列表
        """
        alerts = []
        dim_names = dict(self.DIMENSIONS)

        for metric_key, metric_data in data.items():
            if not isinstance(metric_data, dict):
                continue

            status = metric_data.get('status')

            if status in ['fail', 'error']:
                alert = {
                    'dimension': dimension,
                    'dimension_name': dim_names.get(dimension, dimension),
                    'metric': metric_key,
                    'description': metric_data.get('description', ''),
                    'severity': 'critical' if status == 'fail' else 'high',
                    'value': metric_data.get('value'),
                    'threshold': metric_data.get('threshold'),
                    'message': f"{dim_names.get(dimension)} - {metric_data.get('description', '')} 未达标"
                }
                alerts.append(alert)

        if dimension == 'security_compliance' and isinstance(data.get('risk_score'), (int, float)):
            if data['risk_score'] > 70:
                alerts.append({
                    'dimension': dimension,
                    'dimension_name': dim_names.get(dimension),
                    'metric': 'risk_score',
                    'description': '安全风险评分',
                    'severity': 'critical' if data['risk_score'] > 85 else 'high',
                    'value': data['risk_score'],
                    'threshold': 70,
                    'message': f"安全风险过高 ({data['risk_score']}/100)"
                })

        return alerts

    def _generate_recommendations(self, report: Dict) -> List[str]:
        """
        生成改进建议

        Args:
            report: 完整报告数据

        Returns:
            建议列表
        """
        recommendations = []

        dim_scores = report.get('dimension_scores', {})

        low_scoring_dims = [
            (dim, score) for dim, score in dim_scores.items()
            if score < 70
        ]

        low_scoring_dims.sort(key=lambda x: x[1])

        for dim, score in low_scoring_dims[:5]:
            dim_names = dict(self.DIMENSIONS)
            recommendations.append(
                f"优先改进 [{dim_names.get(dim, dim)}] "
                f"(当前得分: {score:.1f}/100)"
            )

        alert_count = len(report.get('alerts', []))
        critical_alerts = [a for a in report.get('alerts', []) if a.get('severity') == 'critical']

        if critical_alerts:
            recommendations.insert(0, f"立即处理 {len(critical_alerts)} 个严重级别问题")

        if not recommendations:
            recommendations.append("整体质量良好，继续保持!")

        return recommendations

    def _normalize_tech_debt_data(self, debt_report) -> Dict[str, Any]:
        """
        规范化技术债务数据格式

        将TechDebtTracker的报告转换为统一格式

        Args:
            debt_report: 技术债务报告对象或字典

        Returns:
            规范化后的字典
        """
        try:
            if hasattr(debt_report, 'to_dict'):
                data = debt_report.to_dict()
            elif isinstance(debt_report, dict):
                data = debt_report
            else:
                return {}

            summary = data.get('summary', {})
            health_score = data.get('trends', {}).get('health_score', 50)

            return {
                'health_score': {
                    'value': health_score,
                    'status': 'pass' if health_score >= 70 else ('warning' if health_score >= 50 else 'fail'),
                    'threshold': 70,
                    'description': '技术债务健康评分'
                },
                'total_debts': {
                    'value': data.get('total_debts', 0),
                    'status': 'pass' if data.get('total_debts', 0) < 10 else 'warning',
                    'threshold': 10,
                    'description': '总债务数量'
                },
                'open_debts': {
                    'value': data.get('open_debts', 0),
                    'status': 'pass' if data.get('open_debts', 0) < 5 else 'fail',
                    'threshold': 5,
                    'description': '未解决债务数'
                },
                'by_type': summary.get('by_type', {})
            }

        except Exception as e:
            self.logger.error(f"规范化技术债务数据失败: {e}")
            return {}


def main():
    """测试六维监控功能"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    print("=" * 80)
    print("🎯 六维质量监控聚合器测试")
    print("=" * 80)

    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = str(Path(__file__).parent.parent.parent)

    monitor = SixDimensionalQualityMonitor()

    print("\n🚀 开始全量扫描...\n")
    report = monitor.run_full_scan(project_path)

    print("\n" + "=" * 80)
    print("📊 六维质量扫描报告")
    print("=" * 80)

    print(f"\n⏰ 扫描时间: {report['scan_time']}")
    print(f"📁 项目路径: {report['project']}")

    overall_score = report.get('overall_score', 0)
    score_icon = '🎉' if overall_score >= 85 else ('✅' if overall_score >= 70 else ('⚠️' if overall_score >= 50 else '❌'))
    print(f"\n{score_icon} 总体评分: {overall_score:.1f}/100")

    print(f"\n{'─' * 80}")
    print("📈 各维度得分:")
    print(f"{'─' * 80}")

    dim_names = dict(monitor.DIMENSIONS)

    for dim_key, score in report.get('dimension_scores', {}).items():
        name = dim_names.get(dim_key, dim_key)
        icon = '✅' if score >= 80 else ('⚠️' if score >= 60 else '❌')
        print(f"  {icon} {name}: {score:.1f}/100")

    print(f"\n{'─' * 80}")
    print(f"📋 扫描摘要:")
    print(f"{'─' * 80}")

    summary = report.get('summary', {})
    print(f"  完成维度: {summary.get('completed_dimensions', 0)}/{summary.get('total_dimensions', 0)}")
    print(f"  失败维度: {summary.get('failed_dimensions', 0)}")
    print(f"  发现告警: {summary.get('total_alerts', 0)} 个")

    if report.get('alerts'):
        print(f"\n⚠️  告警详情:")
        for alert in report['alerts'][:10]:
            severity_icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🔵'}.get(
                alert.get('severity', ''), '⚪'
            )
            print(f"  {severity_icon} [{alert.get('severity', '?').upper()}] {alert.get('message', '')}")

    if report.get('recommendations'):
        print(f"\n💡 改进建议:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")

    print(f"\n{'=' * 80}")
    print("✅ 六维监控测试完成!")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
