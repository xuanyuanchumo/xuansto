#!/usr/bin/env python3
"""
自迭代触发器脚本
实现自迭代触发条件检测、执行流程和监控

功能:
- 监控系统指标
- 检测触发条件
- 执行自迭代流程
- 生成迭代报告
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from version_iterator import (
    VersionIterator,
    IterationTriggerType,
    VersionBumpType,
    ChangeEntry,
    ChangeType
)


@dataclass
class MonitoringMetrics:
    error_rate: float = 0.0
    continuous_failures: int = 0
    code_quality_score: float = 1.0
    security_alerts: List[Dict[str, Any]] = None
    performance_baseline: Dict[str, float] = None
    current_performance: Dict[str, float] = None
    last_updated: str = ""
    
    def __post_init__(self):
        if self.security_alerts is None:
            self.security_alerts = []
        if self.performance_baseline is None:
            self.performance_baseline = {}
        if self.current_performance is None:
            self.current_performance = {}
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('MetricsCollector')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def collect_from_logs(self, log_dir: str) -> Dict[str, Any]:
        """从日志收集指标"""
        log_path = Path(log_dir)
        if not log_path.exists():
            return {}
        
        total_entries = 0
        error_count = 0
        failure_streak = 0
        max_failure_streak = 0
        
        log_files = list(log_path.glob('*.log'))
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        total_entries += 1
                        
                        if 'ERROR' in line or 'error' in line.lower():
                            error_count += 1
                            failure_streak += 1
                            max_failure_streak = max(max_failure_streak, failure_streak)
                        elif 'SUCCESS' in line or 'success' in line.lower():
                            failure_streak = 0
            except Exception as e:
                self.logger.warning(f"读取日志文件失败 {log_file}: {e}")
        
        error_rate = error_count / total_entries if total_entries > 0 else 0
        
        return {
            'error_rate': error_rate,
            'total_entries': total_entries,
            'error_count': error_count,
            'continuous_failures': max_failure_streak
        }
    
    def collect_from_test_results(self, test_result_file: str) -> Dict[str, Any]:
        """从测试结果收集指标"""
        result_path = Path(test_result_file)
        
        if not result_path.exists():
            return {'test_pass_rate': 1.0}
        
        try:
            with open(result_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            total = data.get('total', 0)
            passed = data.get('passed', 0)
            failed = data.get('failed', 0)
            
            pass_rate = passed / total if total > 0 else 1.0
            
            return {
                'test_pass_rate': pass_rate,
                'total_tests': total,
                'passed_tests': passed,
                'failed_tests': failed,
                'code_quality_score': pass_rate
            }
        except Exception:
            return {'test_pass_rate': 1.0}
    
    def collect_performance_metrics(self) -> Dict[str, float]:
        """收集性能指标"""
        metrics = {}
        
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, '-c', 
                 'import sys; print(sys.getsizeof(object()))'],
                capture_output=True,
                text=True,
                timeout=5
            )
            metrics['memory_baseline'] = 0
        except Exception:
            pass
        
        return metrics
    
    def collect_all_metrics(self, log_dir: Optional[str] = None,
                           test_result_file: Optional[str] = None) -> MonitoringMetrics:
        """收集所有指标"""
        metrics = MonitoringMetrics()
        
        if log_dir:
            log_metrics = self.collect_from_logs(log_dir)
            metrics.error_rate = log_metrics.get('error_rate', 0)
            metrics.continuous_failures = log_metrics.get('continuous_failures', 0)
        
        if test_result_file:
            test_metrics = self.collect_from_test_results(test_result_file)
            metrics.code_quality_score = test_metrics.get('code_quality_score', 1.0)
        
        perf_metrics = self.collect_performance_metrics()
        metrics.performance_baseline = perf_metrics
        metrics.current_performance = perf_metrics
        
        metrics.last_updated = datetime.now().isoformat()
        
        return metrics


class SelfIterationTrigger:
    """自迭代触发器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.iterator = VersionIterator(str(self.project_root))
        self.collector = MetricsCollector(str(self.project_root))
        self.logger = self._setup_logger()
        
        self.metrics_file = self.project_root / 'metrics_history.json'
        self.trigger_history_file = self.project_root / 'trigger_history.json'
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('SelfIterationTrigger')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def check_and_trigger(
        self,
        metrics: Optional[MonitoringMetrics] = None,
        auto_execute: bool = False,
        log_dir: Optional[str] = None,
        test_result_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """检查触发条件并可选执行迭代"""
        if metrics is None:
            metrics = self.collector.collect_all_metrics(log_dir, test_result_file)
        
        self._save_metrics(metrics)
        
        metrics_dict = {
            'error_rate': metrics.error_rate,
            'continuous_failures': metrics.continuous_failures,
            'code_quality_score': metrics.code_quality_score,
            'security_alerts': metrics.security_alerts,
            'performance_baseline': metrics.performance_baseline,
            'current_performance': metrics.current_performance
        }
        
        result = self.iterator.check_iteration_needed(metrics_dict)
        
        result['metrics'] = asdict(metrics)
        result['timestamp'] = datetime.now().isoformat()
        
        if result['needs_iteration'] and auto_execute:
            self.logger.info("触发条件满足，执行自迭代...")
            
            entry = self.iterator.trigger_iteration(metrics_dict)
            
            if entry:
                result['iteration_executed'] = True
                result['new_version'] = entry.version
                result['iteration_entry'] = {
                    'version': entry.version,
                    'previous_version': entry.previous_version,
                    'changes_count': len(entry.changes)
                }
                self.logger.info(f"自迭代完成: {entry.previous_version} -> {entry.version}")
            else:
                result['iteration_executed'] = False
                self.logger.warning("自迭代执行失败")
        
        self._save_trigger_history(result)
        
        return result
    
    def _save_metrics(self, metrics: MonitoringMetrics):
        """保存指标历史"""
        history = []
        
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except Exception:
                history = []
        
        history.append(asdict(metrics))
        
        if len(history) > 100:
            history = history[-100:]
        
        with open(self.metrics_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    
    def _save_trigger_history(self, result: Dict[str, Any]):
        """保存触发历史"""
        history = []
        
        if self.trigger_history_file.exists():
            try:
                with open(self.trigger_history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except Exception:
                history = []
        
        history.append(result)
        
        if len(history) > 50:
            history = history[-50:]
        
        with open(self.trigger_history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    
    def get_trigger_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取触发历史"""
        if not self.trigger_history_file.exists():
            return []
        
        try:
            with open(self.trigger_history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            return history[-limit:]
        except Exception:
            return []
    
    def get_metrics_trend(self, hours: int = 24) -> Dict[str, Any]:
        """获取指标趋势"""
        if not self.metrics_file.exists():
            return {}
        
        try:
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except Exception:
            return {}
        
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent_metrics = [
            m for m in history
            if datetime.fromisoformat(m['last_updated']) > cutoff
        ]
        
        if not recent_metrics:
            return {}
        
        error_rates = [m['error_rate'] for m in recent_metrics]
        quality_scores = [m['code_quality_score'] for m in recent_metrics]
        
        return {
            'period_hours': hours,
            'samples': len(recent_metrics),
            'error_rate': {
                'min': min(error_rates),
                'max': max(error_rates),
                'avg': sum(error_rates) / len(error_rates),
                'trend': 'increasing' if error_rates[-1] > error_rates[0] else 'decreasing'
            },
            'code_quality': {
                'min': min(quality_scores),
                'max': max(quality_scores),
                'avg': sum(quality_scores) / len(quality_scores),
                'trend': 'decreasing' if quality_scores[-1] < quality_scores[0] else 'increasing'
            }
        }
    
    def generate_report(self, output_path: Optional[str] = None) -> str:
        """生成触发器报告"""
        trigger_history = self.get_trigger_history(20)
        metrics_trend = self.get_metrics_trend(24)
        version_status = self.iterator.get_status()
        
        lines = [
            "# 自迭代触发器报告",
            "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 当前状态",
            "",
            f"- 项目: {version_status['project_name']}",
            f"- 当前版本: {version_status['current_version']}",
            f"- 迭代次数: {version_status['iteration_count']}",
            "",
            "## 最近24小时指标趋势",
            "",
        ]
        
        if metrics_trend:
            lines.extend([
                f"- 样本数: {metrics_trend['samples']}",
                f"- 错误率趋势: {metrics_trend['error_rate']['trend']} (平均: {metrics_trend['error_rate']['avg']:.2%})",
                f"- 代码质量趋势: {metrics_trend['code_quality']['trend']} (平均: {metrics_trend['code_quality']['avg']:.2f})",
            ])
        else:
            lines.append("- 无足够数据")
        
        lines.extend([
            "",
            "## 最近触发记录",
            "",
        ])
        
        if trigger_history:
            for record in reversed(trigger_history):
                status = "✅ 已触发" if record['needs_iteration'] else "❌ 未触发"
                lines.append(f"### {record['timestamp']}")
                lines.append(f"- 状态: {status}")
                
                if record.get('iteration_executed'):
                    lines.append(f"- 迭代执行: 是")
                    lines.append(f"- 新版本: {record.get('new_version', 'N/A')}")
                
                if record['triggered_conditions']:
                    lines.append("- 触发条件:")
                    for cond in record['triggered_conditions']:
                        lines.append(f"  - {cond['type']}: {cond['current_value']} (阈值: {cond['threshold']})")
                lines.append("")
        else:
            lines.append("- 无触发记录")
        
        report = '\n'.join(lines)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
        
        return report


def main():
    parser = argparse.ArgumentParser(description='自迭代触发器')
    
    parser.add_argument(
        '--project-root', '-p',
        default='.',
        help='项目根目录'
    )
    parser.add_argument(
        '--log-dir', '-l',
        help='日志目录'
    )
    parser.add_argument(
        '--test-result', '-t',
        help='测试结果文件'
    )
    parser.add_argument(
        '--auto-execute',
        action='store_true',
        help='自动执行迭代'
    )
    parser.add_argument(
        '--report', '-r',
        action='store_true',
        help='生成报告'
    )
    parser.add_argument(
        '--output', '-o',
        help='报告输出路径'
    )
    parser.add_argument(
        '--history',
        action='store_true',
        help='显示触发历史'
    )
    parser.add_argument(
        '--trend',
        action='store_true',
        help='显示指标趋势'
    )
    parser.add_argument(
        '--metrics',
        nargs='*',
        help='手动指定指标 (格式: key=value)'
    )
    
    args = parser.parse_args()
    
    trigger = SelfIterationTrigger(args.project_root)
    
    if args.history:
        history = trigger.get_trigger_history(10)
        print("=== 最近触发历史 ===")
        for record in history:
            status = "触发" if record['needs_iteration'] else "未触发"
            print(f"{record['timestamp']}: {status}")
            if record['triggered_conditions']:
                for cond in record['triggered_conditions']:
                    print(f"  - {cond['type']}: {cond['current_value']}")
        return 0
    
    if args.trend:
        trend = trigger.get_metrics_trend(24)
        print("=== 最近24小时指标趋势 ===")
        if trend:
            print(f"样本数: {trend['samples']}")
            print(f"错误率: 平均 {trend['error_rate']['avg']:.2%}, 趋势 {trend['error_rate']['trend']}")
            print(f"代码质量: 平均 {trend['code_quality']['avg']:.2f}, 趋势 {trend['code_quality']['trend']}")
        else:
            print("无足够数据")
        return 0
    
    if args.report:
        output_path = args.output or os.path.join(args.project_root, 'trigger_report.md')
        report = trigger.generate_report(output_path)
        print(f"报告已生成: {output_path}")
        return 0
    
    metrics = None
    if args.metrics:
        metrics = MonitoringMetrics()
        for item in args.metrics:
            if '=' in item:
                key, value = item.split('=', 1)
                if key == 'error_rate':
                    metrics.error_rate = float(value)
                elif key == 'failures':
                    metrics.continuous_failures = int(value)
                elif key == 'quality':
                    metrics.code_quality_score = float(value)
    
    result = trigger.check_and_trigger(
        metrics=metrics,
        auto_execute=args.auto_execute,
        log_dir=args.log_dir,
        test_result_file=args.test_result
    )
    
    print("=== 自迭代触发检查 ===")
    print(f"需要迭代: {'是' if result['needs_iteration'] else '否'}")
    
    if result['triggered_conditions']:
        print("\n触发的条件:")
        for cond in result['triggered_conditions']:
            print(f"  - {cond['type']}: 当前值 {cond['current_value']}, 阈值 {cond['threshold']}")
    
    if result.get('iteration_executed'):
        print(f"\n迭代已执行: {result['new_version']}")
    
    if result['recommended_bump_type']:
        print(f"\n建议版本升级类型: {result['recommended_bump_type']}")
    
    return 0


if __name__ == '__main__':
    exit(main())
