#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户体验监控器 (UxMonitor)
==========================

采集和分析用户体验相关指标，包括：
- 页面加载时间
- 交互响应时间
- 错误率统计
- 用户流程完成率

使用示例:
    >>> from skillscripts.monitoring.ux_monitor import UxMonitor
    >>> monitor = UxMonitor()
    >>> metrics = monitor.collect_metrics()
    >>> print(metrics['page_load_time'])
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class UxMonitor:
    """
    用户体验监控器

    采集和分析用户交互相关的性能和体验指标，
    为六维质量监控提供用户体验维度数据。

    Attributes:
        METRICS: 支持的UX指标定义和阈值配置
    """

    METRICS: Dict[str, Dict[str, Any]] = {
        'page_load_time': {
            'threshold': 3000,
            'unit': 'ms',
            'description': '页面加载时间'
        },
        'interaction_response': {
            'threshold': 200,
            'unit': 'ms',
            'description': '交互响应时间'
        },
        'error_rate': {
            'threshold': 1,
            'unit': '%',
            'description': '错误率'
        },
        'user_flow_completion': {
            'threshold': 90,
            'unit': '%',
            'description': '用户流程完成率'
        }
    }

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化UX监控器

        Args:
            logger: 可选的日志记录器
        """
        self.logger = logger or logging.getLogger(__name__)
        self._setup_logging()

        self._historical_data: List[Dict] = []

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

    def collect_metrics(self, analytics_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        采集用户体验指标

        从分析数据或模拟数据中提取UX指标。

        Args:
            analytics_data: 可选的分析数据字典。如果为None，则使用模拟数据。

        Returns:
            包含所有UX指标的字典，格式为：
            {
                'metric_name': {
                    'value': 实际值,
                    'threshold': 阈值,
                    'status': 'pass' | 'warning' | 'fail',
                    'details': 详细信息
                },
                ...
            }

        示例:
            >>> monitor = UxMonitor()
            >>> metrics = monitor.collect_metrics()
            >>> print(metrics['page_load_time']['value'])
            1500.5
        """
        self.logger.info("开始采集用户体验指标")

        data = analytics_data or self._generate_simulated_data()

        results = {}

        for metric_name, config in self.METRICS.items():
            method_name = f'_collect_{metric_name}'
            method = getattr(self, method_name, None)

            if method:
                try:
                    metric_data = method(data)
                    results[metric_name] = {
                        **metric_data,
                        'threshold': config['threshold'],
                        'unit': config['unit'],
                        'description': config['description']
                    }
                except Exception as e:
                    self.logger.error(f"采集失败 [{metric_name}]: {e}")
                    results[metric_name] = {
                        'value': None,
                        'threshold': config['threshold'],
                        'status': 'error',
                        'error': str(e),
                        'unit': config['unit'],
                        'description': config['description']
                    }

        self._store_historical_data(results)

        self.logger.info("用户体验指标采集完成")

        return results

    def analyze_user_paths(self, session_data: List[Dict]) -> Dict[str, Any]:
        """
        分析用户行为路径

        分析用户的操作序列，识别常见模式和潜在问题。

        Args:
            session_data: 用户会话数据列表，每个会话包含：
                - session_id: 会话ID
                - user_id: 用户ID
                - actions: 操作列表（按时间排序）
                - start_time: 开始时间
                - end_time: 结束时间
                - completed: 是否完成目标流程

        Returns:
            路径分析结果字典，包含：
                - common_paths: 常见路径模式
                - drop_off_points: 用户流失点
                - avg_session_duration: 平均会话时长
                - conversion_funnel: 转化漏斗数据

        示例:
            >>> sessions = [...]  # 会话数据
            >>> analysis = monitor.analyze_user_paths(sessions)
            >>> print(analysis['conversion_funnel'])
        """
        self.logger.info(f"开始分析用户行为路径 (共 {len(session_data)} 个会话)")

        if not session_data:
            return {
                'error': '无会话数据',
                'common_paths': [],
                'drop_off_points': [],
                'avg_session_duration': 0,
                'conversion_funnel': {}
            }

        common_paths = self._identify_common_paths(session_data)
        drop_off_points = self._identify_drop_off_points(session_data)
        funnel_data = self._calculate_conversion_funnel(session_data)

        total_duration = sum(
            (s.get('end_time', 0) - s.get('start_time', 0))
            for s in session_data
            if s.get('end_time') and s.get('start_time')
        )
        avg_duration = total_duration / len(session_data) if session_data else 0

        analysis_result = {
            'total_sessions': len(session_data),
            'common_paths': common_paths[:10],
            'drop_off_points': drop_off_points[:10],
            'avg_session_duration': round(avg_duration, 2),
            'conversion_funnel': funnel_data,
            'analyzed_at': datetime.now().isoformat()
        }

        self.logger.info(
            f"用户路径分析完成: 平均会话时长 {avg_duration:.2f}s"
        )

        return analysis_result

    def _collect_page_load_time(self, data: Dict) -> Dict[str, Any]:
        """
        采集页面加载时间指标

        Args:
            data: 分析数据

        Returns:
            页面加载数据
        """
        load_times = data.get('page_load_times', [1500, 1800, 1200, 2000, 1600])

        if not load_times:
            return {
                'value': None,
                'status': 'info',
                'details': {'message': '无数据'}
            }

        avg_load_time = sum(load_times) / len(load_times)
        max_load_time = max(load_times)
        min_load_time = min(load_times)
        p95_load_time = sorted(load_times)[int(len(load_times) * 0.95)] if load_times else 0

        status = 'pass' if avg_load_time <= 3000 else ('warning' if avg_load_time <= 5000 else 'fail')

        return {
            'value': round(avg_load_time, 2),
            'status': status,
            'details': {
                'average_ms': round(avg_load_time, 2),
                'max_ms': max_load_time,
                'min_ms': min_load_time,
                'p95_ms': p95_load_time,
                'samples': len(load_times),
                'target_threshold_ms': 3000
            }
        }

    def _collect_interaction_response(self, data: Dict) -> Dict[str, Any]:
        """
        采集交互响应时间指标

        Args:
            data: 分析数据

        Returns:
            交互响应数据
        """
        response_times = data.get('interaction_responses', [100, 150, 80, 200, 120])

        if not response_times:
            return {
                'value': None,
                'status': 'info',
                'details': {'message': '无数据'}
            }

        avg_response = sum(response_times) / len(response_times)
        max_response = max(response_times)
        p99_response = sorted(response_times)[int(len(response_times) * 0.99)] if response_times else 0

        status = 'pass' if avg_response <= 200 else ('warning' if avg_response <= 500 else 'fail')

        return {
            'value': round(avg_response, 2),
            'status': status,
            'details': {
                'average_ms': round(avg_response, 2),
                'max_ms': max_response,
                'p99_ms': p99_response,
                'samples': len(response_times),
                'target_threshold_ms': 200
            }
        }

    def _collect_error_rate(self, data: Dict) -> Dict[str, Any]:
        """
        采集错误率指标

        Args:
            data: 分析数据

        Returns:
            错误率数据
        """
        total_requests = data.get('total_requests', 1000)
        error_count = data.get('error_count', 5)

        if total_requests == 0:
            return {
                'value': 0,
                'status': 'pass',
                'details': {'message': '无请求数据'}
            }

        error_rate = (error_count / total_requests) * 100

        status = 'pass' if error_rate <= 1 else ('warning' if error_rate <= 3 else 'fail')

        errors_by_type = data.get('errors_by_type', {})

        return {
            'value': round(error_rate, 3),
            'status': status,
            'details': {
                'error_rate_percentage': round(error_rate, 3),
                'total_requests': total_requests,
                'error_count': error_count,
                'errors_by_type': errors_by_type,
                'target_threshold_percentage': 1
            }
        }

    def _collect_user_flow_completion(self, data: Dict) -> Dict[str, Any]:
        """
        采集用户流程完成率指标

        Args:
            data: 分析数据

        Returns:
            流程完成率数据
        """
        total_sessions = data.get('total_sessions', 100)
        completed_sessions = data.get('completed_sessions', 92)

        if total_sessions == 0:
            return {
                'value': 0,
                'status': 'info',
                'details': {'message': '无会话数据'}
            }

        completion_rate = (completed_sessions / total_sessions) * 100

        status = 'pass' if completion_rate >= 90 else ('warning' if completion_rate >= 70 else 'fail')

        funnel_stages = data.get('funnel_stages', [
            {'stage': '访问', 'count': 100},
            {'stage': '浏览', 'count': 85},
            {'stage': '交互', 'count': 70},
            {'stage': '转化', 'count': 55},
            {'stage': '完成', 'count': 92}
        ])

        return {
            'value': round(completion_rate, 2),
            'status': status,
            'details': {
                'completion_rate_percentage': round(completion_rate, 2),
                'total_sessions': total_sessions,
                'completed_sessions': completed_sessions,
                'abandoned_sessions': total_sessions - completed_sessions,
                'funnel_stages': funnel_stages,
                'target_threshold_percentage': 90
            }
        }

    def _generate_simulated_data(self) -> Dict:
        """生成模拟的分析数据（用于测试）"""
        import random

        random.seed(42)

        return {
            'page_load_times': [
                random.randint(800, 2500) for _ in range(20)
            ],
            'interaction_responses': [
                random.randint(50, 300) for _ in range(50)
            ],
            'total_requests': random.randint(500, 2000),
            'error_count': random.randint(1, 15),
            'errors_by_type': {
                '400 Bad Request': random.randint(0, 5),
                '404 Not Found': random.randint(0, 8),
                '500 Server Error': random.randint(0, 2)
            },
            'total_sessions': random.randint(80, 150),
            'completed_sessions': random.randint(70, 140)
        }

    def _identify_common_paths(self, session_data: List[Dict]) -> List[Dict]:
        """
        识别常见的用户行为路径

        Args:
            session_data: 会话数据列表

        Returns:
            常见路径列表
        """
        path_counts: Dict[str, int] = {}

        for session in session_data:
            actions = session.get('actions', [])
            if len(actions) >= 2:
                path_tuple = tuple(action.get('action_type') for action in actions[:5])
                path_str = ' → '.join(path_tuple)
                path_counts[path_str] = path_counts.get(path_str, 0) + 1

        common_paths = sorted(
            [{'path': path, 'occurrences': count} for path, count in path_counts.items()],
            key=lambda x: x['occurrences'],
            reverse=True
        )

        return common_paths

    def _identify_drop_off_points(self, session_data: List[Dict]) -> List[Dict]:
        """
        识别用户流失点

        Args:
            session_data: 会话数据列表

        Returns:
            流失点列表
        """
        action_drop_offs: Dict[str, int] = {}

        for session in session_data:
            if not session.get('completed', False):
                actions = session.get('actions', [])
                if actions:
                    last_action = actions[-1].get('action_type', 'unknown')
                    action_drop_offs[last_action] = action_drop_offs.get(last_action, 0) + 1

        drop_off_points = sorted(
            [{'action': action, 'drop_offs': count} 
             for action, count in action_drop_offs.items()],
            key=lambda x: x['drop_offs'],
            reverse=True
        )

        return drop_off_points

    def _calculate_conversion_funnel(self, session_data: List[Dict]) -> Dict[str, Any]:
        """
        计算转化漏斗数据

        Args:
            session_data: 会话数据列表

        Returns:
            漏斗数据字典
        """
        stages = ['visit', 'browse', 'interact', 'convert', 'complete']
        stage_counts = {stage: 0 for stage in stages}

        for session in session_data:
            actions = session.get('actions', [])
            max_stage_index = 0

            for action in actions:
                action_type = action.get('action_type', '').lower()
                if action_type in stages:
                    stage_index = stages.index(action_type)
                    max_stage_index = max(max_stage_index, stage_index)

            for i in range(max_stage_index + 1):
                stage_counts[stages[i]] += 1

        total_sessions = len(session_data) if session_data else 1

        funnel_data = {}
        for stage in stages:
            count = stage_counts[stage]
            percentage = (count / total_sessions * 100) if total_sessions > 0 else 0
            funnel_data[stage] = {
                'count': count,
                'percentage': round(percentage, 1)
            }

        return funnel_data

    def _store_historical_data(self, metrics: Dict) -> None:
        """
        存储历史数据用于趋势分析

        Args:
            metrics: 当前指标数据
        """
        record = {
            'timestamp': datetime.now().isoformat(),
            **{k: v.get('value') for k, v in metrics.items()}
        }

        self._historical_data.append(record)

        if len(self._historical_data) > 100:
            self._historical_data = self._historical_data[-100:]

    def get_ux_trend(self, metric_name: str, last_n: int = 10) -> List[Dict]:
        """
        获取指定指标的近期趋势

        Args:
            metric_name: 指标名称
            last_n: 返回最近N条记录

        Returns:
            历史数据列表
        """
        relevant_records = [
            record for record in self._historical_data[-last_n:]
            if metric_name in record
        ]

        return relevant_records


def main():
    """测试用户体验监控功能"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    print("=" * 80)
    print("👥 用户体验监控测试")
    print("=" * 80)

    monitor = UxMonitor()

    print("\n📊 采集UX指标:\n")
    metrics = monitor.collect_metrics()

    for metric_name, data in metrics.items():
        value = data.get('value')
        threshold = data.get('threshold')
        status = data.get('status', 'unknown')
        unit = data.get('unit', '')
        description = data.get('description', '')

        status_icon = {'pass': '✅', 'warning': '⚠️', 'fail': '❌', 'error': '💥', 'info': 'ℹ️'}.get(status, '❓')

        print(f"{status_icon} {description}")
        print(f"   当前值: {value}{unit}")
        
        if threshold is not None:
            print(f"   阈值: ≤{threshold}{unit}")

        details = data.get('details', {})
        if isinstance(details, dict):
            for key, val in details.items():
                if key != 'funnel_stages':
                    print(f"   {key}: {val}")

        print()

    print("\n📈 UX趋势数据:")
    for metric_name in ['page_load_time', 'interaction_response']:
        trend = monitor.get_ux_trend(metric_name, 5)
        if trend:
            values = [record.get(metric_name) for record in trend]
            print(f"  {metric_name}: 最近5次均值 {sum(values)/len(values):.2f}")

    print("\n✅ UX监控测试完成!")


if __name__ == "__main__":
    main()
