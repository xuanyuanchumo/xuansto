"""
自动优化器模块

实现功能:
1. 自动检测性能问题
2. 自动生成优化方案
3. 自动执行优化操作
4. 自动验证优化效果
5. 自动回滚失败优化
"""

import ast
import re
import json
import time
import statistics
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Callable, Set, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import logging
import shutil
from collections import defaultdict

sys.path.insert(0, str(get_path_config().SKILL_ROOT))

from skillscripts.core.performance_optimizer import (
    PerformanceBottleneckIdentifier,
    PerformanceOptimizationAdvisor,
    PerformanceOptimizationExecutor,
    PerformanceOptimizationValidator,
    UnifiedPerformanceOptimizer,
    PerformanceBottleneck,
    OptimizationSuggestion,
    OptimizationResult,
    BottleneckType,
    OptimizationPriority,
    OptimizationStatus
)


class AutoOptimizationMode(Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


class AutoOptimizationState(Enum):
    IDLE = "idle"
    SCANNING = "scanning"
    ANALYZING = "analyzing"
    OPTIMIZING = "optimizing"
    VALIDATING = "validating"
    ROLLBACK = "rollback"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AutoOptimizationConfig:
    mode: AutoOptimizationMode = AutoOptimizationMode.BALANCED
    auto_apply: bool = False
    max_optimizations_per_cycle: int = 5
    min_impact_score: float = 5.0
    allowed_optimization_types: List[str] = None
    excluded_files: List[str] = None
    backup_enabled: bool = True
    rollback_on_failure: bool = True
    validation_iterations: int = 10
    schedule_interval_minutes: int = 60
    notification_enabled: bool = False
    notification_channels: List[str] = None
    
    def __post_init__(self):
        if self.allowed_optimization_types is None:
            self.allowed_optimization_types = [
                "cpu_optimization",
                "memory_optimization",
                "io_optimization",
                "resource_optimization",
                "algorithm_optimization"
            ]
        if self.excluded_files is None:
            self.excluded_files = []
        if self.notification_channels is None:
            self.notification_channels = []


@dataclass
class AutoOptimizationSession:
    session_id: str
    started_at: str
    completed_at: str
    state: AutoOptimizationState
    bottlenecks_found: int
    optimizations_applied: int
    optimizations_successful: int
    optimizations_failed: int
    total_improvement: float
    report: Dict[str, Any]
    errors: List[str]


class OptimizationScheduler:
    """优化调度器"""
    
    def __init__(self, config: AutoOptimizationConfig):
        self._config = config
        self._scheduled_tasks: List[Dict[str, Any]] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('OptimizationScheduler')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def schedule_optimization(
        self,
        project_path: Path,
        callback: Optional[Callable] = None,
        delay_minutes: int = 0
    ) -> str:
        task_id = f"SCHED-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        task = {
            'task_id': task_id,
            'project_path': str(project_path),
            'callback': callback,
            'scheduled_time': datetime.now() + timedelta(minutes=delay_minutes),
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        self._scheduled_tasks.append(task)
        self._logger.info(f"已调度优化任务: {task_id}")
        
        return task_id
    
    def start(self):
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._thread.start()
        self._logger.info("优化调度器已启动")
    
    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self._logger.info("优化调度器已停止")
    
    def _run_scheduler(self):
        while self._running:
            try:
                now = datetime.now()
                for task in self._scheduled_tasks:
                    if task['status'] == 'pending' and task['scheduled_time'] <= now:
                        task['status'] = 'running'
                        self._logger.info(f"执行调度任务: {task['task_id']}")
                        
                        if task['callback']:
                            try:
                                task['callback'](Path(task['project_path']))
                                task['status'] = 'completed'
                            except Exception as e:
                                task['status'] = 'failed'
                                self._logger.error(f"任务执行失败: {e}")
                
                time.sleep(60)
                
            except Exception as e:
                self._logger.error(f"调度器错误: {e}")
                time.sleep(60)
    
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        return [t for t in self._scheduled_tasks if t['status'] == 'pending']


class OptimizationNotifier:
    """优化通知器"""
    
    def __init__(self, config: AutoOptimizationConfig):
        self._config = config
        self._logger = self._setup_logger()
        self._notifications: List[Dict[str, Any]] = []
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('OptimizationNotifier')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def notify(self, event_type: str, message: str, details: Dict[str, Any] = None):
        notification = {
            'id': f"NOTIF-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'event_type': event_type,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        
        self._notifications.append(notification)
        
        if self._config.notification_enabled:
            self._send_notification(notification)
        
        self._logger.info(f"[{event_type}] {message}")
    
    def _send_notification(self, notification: Dict[str, Any]):
        for channel in self._config.notification_channels:
            try:
                if channel == 'log':
                    self._logger.info(json.dumps(notification, ensure_ascii=False))
                elif channel == 'file':
                    self._write_to_file(notification)
            except Exception as e:
                self._logger.error(f"发送通知失败: {e}")
    
    def _write_to_file(self, notification: Dict[str, Any]):
        log_dir = get_path_config().LOGS_DIR / "optimization"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"notifications_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(notification, ensure_ascii=False) + '\n')
    
    def get_notifications(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._notifications[-limit:]


class OptimizationRollbackManager:
    """优化回滚管理器"""
    
    def __init__(self, project_path: Path, config: AutoOptimizationConfig):
        self._project_path = project_path
        self._config = config
        self._backup_dir = project_path / ".optimization_backups"
        self._rollback_history: List[Dict[str, Any]] = []
        self._logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('OptimizationRollbackManager')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def create_backup(self, file_path: Path, optimization_id: str) -> Optional[Path]:
        if not self._config.backup_enabled:
            return None
        
        try:
            self._backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            backup_name = f"{file_path.name}.{optimization_id}.{timestamp}.bak"
            backup_path = self._backup_dir / backup_name
            
            shutil.copy2(file_path, backup_path)
            
            self._logger.info(f"已创建备份: {backup_path}")
            return backup_path
            
        except Exception as e:
            self._logger.error(f"创建备份失败: {e}")
            return None
    
    def rollback(self, optimization_id: str) -> bool:
        try:
            backup_files = list(self._backup_dir.glob(f"*.{optimization_id}.*.bak"))
            
            if not backup_files:
                self._logger.warning(f"未找到优化 {optimization_id} 的备份文件")
                return False
            
            for backup_file in backup_files:
                original_name = backup_file.name.split('.')[0]
                original_path = self._find_original_path(original_name)
                
                if original_path:
                    shutil.copy2(backup_file, original_path)
                    self._logger.info(f"已回滚文件: {original_path}")
            
            self._rollback_history.append({
                'optimization_id': optimization_id,
                'timestamp': datetime.now().isoformat(),
                'files_restored': len(backup_files)
            })
            
            return True
            
        except Exception as e:
            self._logger.error(f"回滚失败: {e}")
            return False
    
    def _find_original_path(self, filename: str) -> Optional[Path]:
        for ext in ['.py', '.ts', '.vue', '.js']:
            for file_path in self._project_path.rglob(f"{filename}{ext}"):
                if ".optimization_backups" not in str(file_path):
                    return file_path
        return None
    
    def cleanup_old_backups(self, days: int = 30) -> int:
        cutoff = datetime.now() - timedelta(days=days)
        removed_count = 0
        
        for backup_file in self._backup_dir.glob("*.bak"):
            try:
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_time < cutoff:
                    backup_file.unlink()
                    removed_count += 1
            except Exception:
                pass
        
        self._logger.info(f"清理了 {removed_count} 个旧备份文件")
        return removed_count


class AutoOptimizer:
    """自动优化器主类"""
    
    def __init__(
        self,
        project_path: Path,
        config: AutoOptimizationConfig = None
    ):
        self._project_path = Path(project_path)
        self._config = config or AutoOptimizationConfig()
        
        self._optimizer = UnifiedPerformanceOptimizer(self._project_path)
        self._scheduler = OptimizationScheduler(self._config)
        self._notifier = OptimizationNotifier(self._config)
        self._rollback_manager = OptimizationRollbackManager(self._project_path, self._config)
        
        self._state = AutoOptimizationState.IDLE
        self._sessions: List[AutoOptimizationSession] = []
        self._logger = self._setup_logger()
        
        self._optimization_history: List[Dict[str, Any]] = []
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('AutoOptimizer')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    @property
    def state(self) -> AutoOptimizationState:
        return self._state
    
    def run_optimization_cycle(self) -> AutoOptimizationSession:
        session_id = f"SESSION-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        started_at = datetime.now().isoformat()
        
        self._state = AutoOptimizationState.SCANNING
        self._notifier.notify('cycle_start', f"开始自动优化周期: {session_id}")
        
        errors = []
        bottlenecks_found = 0
        optimizations_applied = 0
        optimizations_successful = 0
        optimizations_failed = 0
        total_improvement = 0.0
        report = {}
        
        try:
            self._state = AutoOptimizationState.ANALYZING
            self._notifier.notify('scanning', "正在扫描性能瓶颈")
            
            all_bottlenecks = self._optimizer.bottleneck_identifier.identify_bottlenecks(self._project_path)
            
            filtered_bottlenecks = self._filter_bottlenecks(all_bottlenecks)
            bottlenecks_found = len(filtered_bottlenecks)
            
            self._notifier.notify('analysis_complete', f"发现 {bottlenecks_found} 个性能瓶颈")
            
            if not filtered_bottlenecks:
                self._notifier.notify('no_issues', "未发现需要优化的性能问题")
                self._state = AutoOptimizationState.COMPLETED
            else:
                self._state = AutoOptimizationState.OPTIMIZING
                
                suggestions = self._optimizer.optimization_advisor.generate_suggestions(
                    filtered_bottlenecks[:self._config.max_optimizations_per_cycle]
                )
                
                for suggestion in suggestions:
                    if self._should_apply_optimization(suggestion):
                        optimizations_applied += 1
                        
                        result = self._apply_optimization_with_backup(suggestion)
                        
                        if result.success:
                            self._state = AutoOptimizationState.VALIDATING
                            
                            validation = self._optimizer.optimization_validator.validate_optimization(
                                result,
                                self._config.validation_iterations
                            )
                            
                            if validation['improvement_verified']:
                                optimizations_successful += 1
                                total_improvement += result.improvement_percent
                                self._notifier.notify(
                                    'optimization_success',
                                    f"优化成功: {suggestion.optimization_type}",
                                    {'improvement': result.improvement_percent}
                                )
                            else:
                                if self._config.rollback_on_failure:
                                    self._state = AutoOptimizationState.ROLLBACK
                                    self._rollback_manager.rollback(result.optimization_id)
                                    self._notifier.notify('rollback', f"已回滚优化: {result.optimization_id}")
                                optimizations_failed += 1
                        else:
                            optimizations_failed += 1
                            errors.append(f"优化执行失败: {suggestion.suggestion_id}")
                
                self._state = AutoOptimizationState.COMPLETED
            
            report = self._generate_session_report(
                session_id,
                filtered_bottlenecks,
                optimizations_applied,
                optimizations_successful,
                optimizations_failed
            )
            
        except Exception as e:
            self._state = AutoOptimizationState.FAILED
            errors.append(str(e))
            self._notifier.notify('error', f"优化周期失败: {str(e)}")
            self._logger.error(f"优化周期失败: {e}")
        
        completed_at = datetime.now().isoformat()
        
        session = AutoOptimizationSession(
            session_id=session_id,
            started_at=started_at,
            completed_at=completed_at,
            state=self._state,
            bottlenecks_found=bottlenecks_found,
            optimizations_applied=optimizations_applied,
            optimizations_successful=optimizations_successful,
            optimizations_failed=optimizations_failed,
            total_improvement=total_improvement,
            report=report,
            errors=errors
        )
        
        self._sessions.append(session)
        self._state = AutoOptimizationState.IDLE
        
        self._notifier.notify(
            'cycle_complete',
            f"优化周期完成: 成功 {optimizations_successful}/{optimizations_applied}"
        )
        
        return session
    
    def _filter_bottlenecks(self, bottlenecks: List[PerformanceBottleneck]) -> List[PerformanceBottleneck]:
        filtered = []
        
        for bottleneck in bottlenecks:
            if bottleneck.impact_score < self._config.min_impact_score:
                continue
            
            if any(excluded in bottleneck.file_path for excluded in self._config.excluded_files):
                continue
            
            if self._config.mode == AutoOptimizationMode.CONSERVATIVE:
                if bottleneck.priority not in [OptimizationPriority.CRITICAL, OptimizationPriority.HIGH]:
                    continue
            elif self._config.mode == AutoOptimizationMode.AGGRESSIVE:
                pass
            else:
                if bottleneck.priority == OptimizationPriority.LOW:
                    continue
            
            filtered.append(bottleneck)
        
        return filtered
    
    def _should_apply_optimization(self, suggestion: OptimizationSuggestion) -> bool:
        if suggestion.optimization_type not in self._config.allowed_optimization_types:
            return False
        
        if self._config.mode == AutoOptimizationMode.CONSERVATIVE:
            if suggestion.risk_level not in ['低', 'low']:
                return False
        
        return True
    
    def _apply_optimization_with_backup(self, suggestion: OptimizationSuggestion) -> OptimizationResult:
        file_path = self._project_path / suggestion.bottleneck.file_path
        
        if file_path.exists() and self._config.backup_enabled:
            self._rollback_manager.create_backup(file_path, f"OPT-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        
        return self._optimizer.optimization_executor.execute_optimization(
            suggestion,
            self._project_path,
            auto_apply=self._config.auto_apply
        )
    
    def _generate_session_report(
        self,
        session_id: str,
        bottlenecks: List[PerformanceBottleneck],
        applied: int,
        successful: int,
        failed: int
    ) -> Dict[str, Any]:
        return {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'project_path': str(self._project_path),
            'config': {
                'mode': self._config.mode.value,
                'auto_apply': self._config.auto_apply,
                'max_optimizations': self._config.max_optimizations_per_cycle
            },
            'bottlenecks': [
                {
                    'type': b.bottleneck_type.value,
                    'file': b.file_path,
                    'line': b.line_number,
                    'description': b.description,
                    'impact_score': b.impact_score,
                    'priority': b.priority.value
                }
                for b in bottlenecks
            ],
            'summary': {
                'bottlenecks_found': len(bottlenecks),
                'optimizations_applied': applied,
                'optimizations_successful': successful,
                'optimizations_failed': failed,
                'success_rate': (successful / applied * 100) if applied > 0 else 0
            },
            'recommendations': self._generate_recommendations(bottlenecks, successful, failed)
        }
    
    def _generate_recommendations(
        self,
        bottlenecks: List[PerformanceBottleneck],
        successful: int,
        failed: int
    ) -> List[str]:
        recommendations = []
        
        critical = [b for b in bottlenecks if b.priority == OptimizationPriority.CRITICAL]
        if critical:
            recommendations.append(f"发现 {len(critical)} 个严重性能问题，建议立即处理")
        
        high_priority = [b for b in bottlenecks if b.priority == OptimizationPriority.HIGH]
        if high_priority:
            recommendations.append(f"发现 {len(high_priority)} 个高优先级性能问题，建议优先优化")
        
        if failed > 0:
            recommendations.append(f"{failed} 个优化执行失败，建议检查日志并重试")
        
        if successful > 0:
            recommendations.append(f"成功优化 {successful} 个性能问题，建议持续监控效果")
        
        if not recommendations:
            recommendations.append("性能状态良好，建议定期运行优化检查")
        
        return recommendations
    
    def schedule_periodic_optimization(self, interval_minutes: int = None):
        interval = interval_minutes or self._config.schedule_interval_minutes
        
        def run_cycle():
            self.run_optimization_cycle()
        
        self._scheduler.schedule_optimization(self._project_path, run_cycle, interval)
        self._logger.info(f"已调度定期优化，间隔: {interval} 分钟")
    
    def start_scheduler(self):
        self._scheduler.start()
    
    def stop_scheduler(self):
        self._scheduler.stop()
    
    def get_sessions(self, limit: int = 10) -> List[AutoOptimizationSession]:
        return self._sessions[-limit:]
    
    def get_latest_session(self) -> Optional[AutoOptimizationSession]:
        return self._sessions[-1] if self._sessions else None
    
    def export_session_report(self, session: AutoOptimizationSession, output_path: Path):
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            'session_id': session.session_id,
            'started_at': session.started_at,
            'completed_at': session.completed_at,
            'state': session.state.value,
            'bottlenecks_found': session.bottlenecks_found,
            'optimizations_applied': session.optimizations_applied,
            'optimizations_successful': session.optimizations_successful,
            'optimizations_failed': session.optimizations_failed,
            'total_improvement': session.total_improvement,
            'report': session.report,
            'errors': session.errors
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self._logger.info(f"会话报告已导出: {output_path}")


class AutoOptimizerScript:
    """自动优化器脚本"""
    
    def __init__(self):
        self._optimizer: Optional[AutoOptimizer] = None
    
    def run(
        self,
        project_path: str,
        mode: str = "balanced",
        auto_apply: bool = False,
        max_optimizations: int = 5,
        output_path: str = None
    ) -> Dict[str, Any]:
        config = AutoOptimizationConfig(
            mode=AutoOptimizationMode(mode),
            auto_apply=auto_apply,
            max_optimizations_per_cycle=max_optimizations
        )
        
        self._optimizer = AutoOptimizer(Path(project_path), config)
        
        session = self._optimizer.run_optimization_cycle()
        
        if output_path:
            self._optimizer.export_session_report(session, Path(output_path))
        
        return {
            'session_id': session.session_id,
            'state': session.state.value,
            'bottlenecks_found': session.bottlenecks_found,
            'optimizations_applied': session.optimizations_applied,
            'optimizations_successful': session.optimizations_successful,
            'optimizations_failed': session.optimizations_failed,
            'total_improvement': session.total_improvement
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description='自动优化器')
    parser.add_argument('--project-path', '-p', default='.', help='项目根目录')
    parser.add_argument('--mode', '-m', choices=['conservative', 'balanced', 'aggressive'],
                        default='balanced', help='优化模式')
    parser.add_argument('--auto-apply', '-a', action='store_true', help='自动应用优化')
    parser.add_argument('--max-optimizations', type=int, default=5, help='每周期最大优化数量')
    parser.add_argument('--output', '-o', default=str(get_path_config().REPORTS_DIR / "auto_optimization_report.json"), help='输出报告路径')
    parser.add_argument('--schedule', '-s', type=int, help='调度定期优化（分钟）')
    
    args = parser.parse_args()
    
    config = AutoOptimizationConfig(
        mode=AutoOptimizationMode(args.mode),
        auto_apply=args.auto_apply,
        max_optimizations_per_cycle=args.max_optimizations
    )
    
    optimizer = AutoOptimizer(Path(args.project_path), config)
    
    if args.schedule:
        optimizer.schedule_periodic_optimization(args.schedule)
        optimizer.start_scheduler()
        print(f"已启动定期优化调度器，间隔: {args.schedule} 分钟")
        print("按 Ctrl+C 停止...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            optimizer.stop_scheduler()
            print("\n调度器已停止")
    else:
        session = optimizer.run_optimization_cycle()
        
        optimizer.export_session_report(session, Path(args.output))
        
        print(f"\n自动优化报告已生成: {args.output}")
        print(f"会话 ID: {session.session_id}")
        print(f"状态: {session.state.value}")
        print(f"发现瓶颈: {session.bottlenecks_found}")
        print(f"应用优化: {session.optimizations_applied}")
        print(f"成功优化: {session.optimizations_successful}")
        print(f"失败优化: {session.optimizations_failed}")
        print(f"总体提升: {session.total_improvement:.2f}%")


if __name__ == '__main__':
    main()
