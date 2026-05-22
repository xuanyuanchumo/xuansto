"""
增强的性能优化器模块 (Phase 7.2)

核心功能:
1. 智能性能瓶颈检测 - 多维度性能分析
2. 优化方案自动生成 - 基于瓶颈类型的智能建议
3. 自动优化执行 - 安全的代码优化应用
4. 效果验证与回滚 - 确保优化效果可追溯

增强特性:
- 支持运行时性能分析
- 智能优化优先级排序
- 增量式优化策略
- 性能基线对比
- 优化效果预测
"""

import ast
import re
import json
import time
import statistics
import hashlib
import os
import sys
import tracemalloc
import cProfile
import pstats
import io
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Callable, Set, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
import threading
import logging
from collections import defaultdict
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class BottleneckSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class OptimizationCategory(Enum):
    CODE_STRUCTURE = "code_structure"
    ALGORITHM = "algorithm"
    MEMORY_MANAGEMENT = "memory_management"
    I_O_OPERATIONS = "io_operations"
    CONCURRENCY = "concurrency"
    DATABASE = "database"
    CACHE_STRATEGY = "cache_strategy"
    NETWORK = "network"
    RESOURCE_MANAGEMENT = "resource_management"


@dataclass
class PerformanceBaseline:
    """性能基线数据"""
    baseline_id: str
    timestamp: str
    metrics: Dict[str, float]
    project_state: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'baseline_id': self.baseline_id,
            'timestamp': self.timestamp,
            'metrics': self.metrics,
            'project_state': self.project_state
        }


@dataclass
class BottleneckDetectionResult:
    """瓶颈检测结果"""
    detection_id: str
    timestamp: str
    bottlenecks: List[Dict[str, Any]]
    analysis_summary: Dict[str, Any]
    detection_method: str
    confidence_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'detection_id': self.detection_id,
            'timestamp': self.timestamp,
            'bottlenecks': self.bottlenecks,
            'analysis_summary': self.analysis_summary,
            'detection_method': self.detection_method,
            'confidence_score': self.confidence_score
        }


@dataclass
class OptimizationPlan:
    """优化方案"""
    plan_id: str
    created_at: str
    bottlenecks_addressed: List[str]
    optimizations: List[Dict[str, Any]]
    priority_order: List[str]
    estimated_impact: Dict[str, float]
    risk_assessment: Dict[str, Any]
    implementation_phases: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'plan_id': self.plan_id,
            'created_at': self.created_at,
            'bottlenecks_addressed': self.bottlenecks_addressed,
            'optimizations': self.optimizations,
            'priority_order': self.priority_order,
            'estimated_impact': self.estimated_impact,
            'risk_assessment': self.risk_assessment,
            'implementation_phases': self.implementation_phases
        }


@dataclass
class ExecutionResult:
    """优化执行结果"""
    execution_id: str
    optimization_id: str
    status: str
    started_at: str
    completed_at: str
    changes_made: List[Dict[str, Any]]
    backup_created: bool
    backup_path: str = ""
    rollback_available: bool = False
    performance_before: Dict[str, float] = field(default_factory=dict)
    performance_after: Dict[str, float] = field(default_factory=dict)
    validation_result: Dict[str, Any] = field(default_factory=dict)
    success: bool = False
    error_message: str = ""
    execution_log: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'execution_id': self.execution_id,
            'optimization_id': self.optimization_id,
            'status': self.status,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'changes_made': self.changes_made,
            'backup_created': self.backup_created,
            'backup_path': self.backup_path,
            'rollback_available': self.rollback_available,
            'performance_before': self.performance_before,
            'performance_after': self.performance_after,
            'validation_result': self.validation_result,
            'success': self.success,
            'error_message': self.error_message,
            'execution_log': self.execution_log
        }


class EnhancedPerformanceAnalyzer:
    """增强的性能分析器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self._config = config or {}
        self._analysis_cache: Dict[str, Any] = {}
        self._logger = self._setup_logger()
        
        self._analysis_thresholds = {
            'function_complexity_limit': self._config.get('function_complexity_limit', 10),
            'nested_loop_threshold': self._config.get('nested_loop_threshold', 3),
            'memory_usage_warning_mb': self._config.get('memory_usage_warning_mb', 100),
            'execution_time_warning_ms': self._config.get('execution_time_warning_ms', 1000),
            'n_plus_one_detection': self._config.get('n_plus_one_detection', True),
            'blocking_operation_detection': self._config.get('blocking_operation_detection', True),
            'code_duplication_threshold': self._config.get('code_duplication_threshold', 0.8),
        }
        
        self._pattern_library = self._load_pattern_library()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('EnhancedPerformanceAnalyzer')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def _load_pattern_library(self) -> Dict[str, Any]:
        """加载性能模式库"""
        return {
            'anti_patterns': {
                'god_function': {
                    'description': '函数过长或过于复杂',
                    'threshold': {'lines': 100, 'complexity': 10},
                    'impact': 'high',
                    'suggestion': '拆分为多个小函数'
                },
                'deep_nesting': {
                    'description': '嵌套层级过深',
                    'threshold': {'depth': 4},
                    'impact': 'medium',
                    'suggestion': '使用早返回或提取方法'
                },
                'magic_numbers': {
                    'description': '使用魔法数字',
                    'pattern': r'\b\d{2,}\b',
                    'impact': 'low',
                    'suggestion': '使用命名常量'
                }
            },
            'optimization_patterns': {
                'lazy_loading': {
                    'description': '延迟加载模式',
                    'applicable_to': ['database', 'io'],
                    'benefit': '减少初始化时间'
                },
                'caching': {
                    'description': '缓存模式',
                    'applicable_to': ['computation', 'database'],
                    'benefit': '减少重复计算'
                },
                'batch_processing': {
                    'description': '批处理模式',
                    'applicable_to': ['database', 'io'],
                    'benefit': '减少I/O操作次数'
                }
            }
        }
    
    def analyze_project_performance(
        self, 
        project_path: Path,
        analysis_depth: str = "standard",
        include_runtime: bool = False
    ) -> BottleneckDetectionResult:
        """全面分析项目性能"""
        detection_id = f"DET-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        start_time = datetime.now()
        
        bottlenecks = []
        analysis_stats = {
            'files_analyzed': 0,
            'functions_analyzed': 0,
            'classes_analyzed': 0,
            'total_lines_analyzed': 0,
            'analysis_duration_seconds': 0
        }
        
        backend_dir = project_path / "backend" / "app"
        if backend_dir.exists():
            backend_results = self._analyze_directory(backend_dir, analysis_depth)
            bottlenecks.extend(backend_results['bottlenecks'])
            analysis_stats['files_analyzed'] += backend_results['stats']['files']
            analysis_stats['functions_analyzed'] += backend_results['stats']['functions']
            analysis_stats['classes_analyzed'] += backend_results['stats']['classes']
            analysis_stats['total_lines_analyzed'] += backend_results['stats']['lines']
        
        frontend_dir = project_path / "frontend" / "src"
        if frontend_dir.exists():
            frontend_results = self._analyze_frontend(frontend_dir, analysis_depth)
            bottlenecks.extend(frontend_results['bottlenecks'])
            analysis_stats['files_analyzed'] += frontend_results['stats']['files']
        
        scripts_dir = project_path / "skillscripts"
        if scripts_dir.exists():
            scripts_results = self._analyze_directory(scripts_dir, analysis_depth)
            bottlenecks.extend(scripts_results['bottlenecks'])
            analysis_stats['files_analyzed'] += scripts_results['stats']['files']
            analysis_stats['functions_analyzed'] += scripts_results['stats']['functions']
        
        end_time = datetime.now()
        analysis_stats['analysis_duration_seconds'] = (end_time - start_time).total_seconds()
        
        bottlenecks = self._deduplicate_bottlenecks(bottlenecks)
        bottlenecks = self._prioritize_bottlenecks(bottlenecks)
        
        confidence_score = self._calculate_confidence_score(bottlenecks, analysis_stats)
        
        result = BottleneckDetectionResult(
            detection_id=detection_id,
            timestamp=start_time.isoformat(),
            bottlenecks=bottlenecks,
            analysis_summary=analysis_stats,
            detection_method=f"static_analysis_{analysis_depth}",
            confidence_score=confidence_score
        )
        
        self._logger.info(f"性能分析完成: 发现 {len(bottlenecks)} 个瓶颈")
        return result
    
    def analyze_runtime_performance(
        self,
        func: Callable,
        *args,
        warmup_runs: int = 3,
        measurement_runs: int = 10,
        **kwargs
    ) -> BottleneckDetectionResult:
        """运行时性能分析"""
        detection_id = f"RT-DET-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        start_time = datetime.now()
        
        bottlenecks = []
        
        for _ in range(warmup_runs):
            try:
                func(*args, **kwargs)
            except Exception:
                pass
        
        tracemalloc.start()
        profiler = cProfile.Profile()
        
        runtime_metrics = {
            'executions': [],
            'memory_samples': [],
            'timing_samples': []
        }
        
        profiler.enable()
        
        for i in range(measurement_runs):
            exec_start = time.perf_counter()
            
            try:
                result = func(*args, **kwargs)
                exec_end = time.perf_counter()
                
                current_mem, peak_mem = tracemalloc.get_traced_memory()
                
                runtime_metrics['executions'].append({
                    'run': i + 1,
                    'success': True,
                    'execution_time_ms': (exec_end - exec_start) * 1000,
                    'current_memory_mb': current_mem / 1024 / 1024,
                    'peak_memory_mb': peak_mem / 1024 / 1024
                })
                
            except Exception as e:
                exec_end = time.perf_counter()
                runtime_metrics['executions'].append({
                    'run': i + 1,
                    'success': False,
                    'error': str(e),
                    'execution_time_ms': (exec_end - exec_start) * 1000
                })
        
        profiler.disable()
        tracemalloc.stop()
        
        successful_executions = [e for e in runtime_metrics['executions'] if e['success']]
        
        if successful_executions:
            avg_time = statistics.mean([e['execution_time_ms'] for e in successful_executions])
            max_time = max(e['execution_time_ms'] for e in successful_executions)
            min_time = min(e['execution_time_ms'] for e in successful_executions)
            std_time = statistics.stdev([e['execution_time_ms'] for e in successful_executions]) if len(successful_executions) > 1 else 0
            
            avg_memory = statistics.mean([e['peak_memory_mb'] for e in successful_executions])
            
            if avg_time > self._analysis_thresholds['execution_time_warning_ms']:
                bottlenecks.append({
                    'type': 'runtime_performance',
                    'category': 'execution_time',
                    'severity': 'high' if avg_time > 5000 else 'medium',
                    'location': f'function:{func.__name__}',
                    'description': f'函数 {func.__name__} 平均执行时间 {avg_time:.2f}ms 超过阈值',
                    'metrics': {
                        'avg_time_ms': avg_time,
                        'max_time_ms': max_time,
                        'min_time_ms': min_time,
                        'std_time_ms': std_time,
                        'threshold_ms': self._analysis_thresholds['execution_time_warning_ms']
                    },
                    'suggestions': [
                        '分析热点代码路径',
                        '考虑算法优化',
                        '添加缓存层',
                        '使用异步处理'
                    ],
                    'estimated_improvement': '30-70%'
                })
            
            if avg_memory > self._analysis_thresholds['memory_usage_warning_mb']:
                bottlenecks.append({
                    'type': 'runtime_performance',
                    'category': 'memory_usage',
                    'severity': 'high' if avg_memory > 500 else 'medium',
                    'location': f'function:{func.__name__}',
                    'description': f'函数 {func.__name__} 平均内存使用 {avg_memory:.2f}MB 超过阈值',
                    'metrics': {
                        'avg_memory_mb': avg_memory,
                        'peak_memory_mb': max(e['peak_memory_mb'] for e in successful_executions),
                        'threshold_mb': self._analysis_thresholds['memory_usage_warning_mb']
                    },
                    'suggestions': [
                        '使用生成器替代列表',
                        '流式处理大数据',
                        '及时释放大对象',
                        '使用内存池技术'
                    ],
                    'estimated_improvement': '40-80%'
                })
        
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(15)
        
        profile_output = s.getvalue()
        hotspots = self._parse_profile_hotspots(profile_output)
        
        for hotspot in hotspots[:5]:
            if hotspot['cumulative_time'] > 0.1:
                bottlenecks.append({
                    'type': 'hotspot',
                    'category': 'cpu_intensive',
                    'severity': 'medium',
                    'location': f"{hotspot.get('file', 'unknown')}:{hotspot.get('line', 0)}",
                    'description': f"热点函数 {hotspot['function']} 累计耗时 {hotspot['cumulative_time']:.3f}s",
                    'metrics': {
                        'cumulative_time_s': hotspot['cumulative_time'],
                        'total_calls': hotspot.get('ncalls', 0),
                        'per_call_time_s': hotspot.get('per_call', 0)
                    },
                    'suggestions': [
                        '优化此函数实现',
                        '缓存计算结果',
                        '考虑并行化'
                    ],
                    'estimated_improvement': '10-30%'
                })
        
        end_time = datetime.now()
        
        result = BottleneckDetectionResult(
            detection_id=detection_id,
            timestamp=start_time.isoformat(),
            bottlenecks=bottlenecks,
            analysis_summary={
                'analysis_type': 'runtime',
                'warmup_runs': warmup_runs,
                'measurement_runs': measurement_runs,
                'successful_executions': len(successful_executions),
                'runtime_metrics': runtime_metrics
            },
            detection_method="runtime_profiling",
            confidence_score=0.9 if bottlenecks else 1.0
        )
        
        return result
    
    def _analyze_directory(
        self, 
        directory: Path, 
        depth: str = "standard"
    ) -> Dict[str, Any]:
        """分析目录中的Python文件"""
        results = {
            'bottlenecks': [],
            'stats': {
                'files': 0,
                'functions': 0,
                'classes': 0,
                'lines': 0
            }
        }
        
        for py_file in directory.rglob("*.py"):
            if "__pycache__" in str(py_file) or "test_" in py_file.name:
                continue
            
            file_results = self._analyze_python_file(py_file, depth)
            results['bottlenecks'].extend(file_results['bottlenecks'])
            results['stats']['files'] += 1
            results['stats']['functions'] += file_results['stats']['functions']
            results['stats']['classes'] += file_results['stats']['classes']
            results['stats']['lines'] += file_results['stats']['lines']
        
        return results
    
    def _analyze_python_file(
        self, 
        file_path: Path, 
        depth: str = "standard"
    ) -> Dict[str, Any]:
        """分析单个Python文件"""
        results = {
            'bottlenecks': [],
            'stats': {
                'functions': 0,
                'classes': 0,
                'lines': 0
            }
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                results['stats']['lines'] = len(lines)
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    results['stats']['functions'] += 1
                    func_bottlenecks = self._analyze_function(node, file_path, content, depth)
                    results['bottlenecks'].extend(func_bottlenecks)
                
                elif isinstance(node, ast.ClassDef):
                    results['stats']['classes'] += 1
                    class_bottlenecks = self._analyze_class(node, file_path, content, depth)
                    results['bottlenecks'].extend(class_bottlenecks)
                    
        except Exception as e:
            self._logger.debug(f"分析文件失败 {file_path}: {e}")
        
        return results
    
    def _analyze_function(
        self, 
        node: ast.FunctionDef, 
        file_path: Path, 
        content: str,
        depth: str
    ) -> List[Dict[str, Any]]:
        """分析函数性能问题"""
        bottlenecks = []
        
        complexity = self._calculate_cyclomatic_complexity(node)
        if complexity > self._analysis_thresholds['function_complexity_limit']:
            bottlenecks.append({
                'type': 'complexity',
                'category': 'code_structure',
                'severity': 'high' if complexity > 20 else 'medium',
                'location': f"{file_path}:{node.lineno}",
                'description': f"函数 {node.name} 圈复杂度过高 ({complexity})",
                'metrics': {'complexity': complexity},
                'suggestions': [
                    '拆分函数为多个小函数',
                    '简化条件逻辑',
                    '使用策略模式替代复杂条件',
                    '提取重复逻辑'
                ],
                'estimated_improvement': '提升可维护性和潜在性能'
            })
        
        nested_depth = self._calculate_nested_depth(node)
        if nested_depth >= self._analysis_thresholds['nested_loop_threshold']:
            bottlenecks.append({
                'type': 'nesting',
                'category': 'algorithm',
                'severity': 'high' if nested_depth >= 4 else 'medium',
                'location': f"{file_path}:{node.lineno}",
                'description': f"函数 {node.name} 嵌套深度过深 ({nested_depth} 层)",
                'metrics': {'nested_depth': nested_depth},
                'suggestions': [
                    '使用早返回 (early return)',
                    '提取嵌套块为独立函数',
                    '使用卫语句 (guard clause)',
                    '重新设计控制流'
                ],
                'estimated_improvement': '50-90%'
            })
        
        if self._has_database_queries_in_loop(node):
            bottlenecks.append({
                'type': 'n_plus_one',
                'category': 'database',
                'severity': 'critical',
                'location': f"{file_path}:{node.lineno}",
                'description': f"函数 {node.name} 存在 N+1 查询问题",
                'suggestions': [
                    '使用批量查询 (IN 子句)',
                    '使用 JOIN 预加载关联数据',
                    '使用 select_related/prefetch_related (Django)',
                    '使用 joinedload (SQLAlchemy)',
                    '实现查询结果缓存'
                ],
                'estimated_improvement': '80-95%'
            })
        
        if self._has_blocking_operations(node):
            bottlenecks.append({
                'type': 'blocking',
                'category': 'io_operations',
                'severity': 'high',
                'location': f"{file_path}:{node.lineno}",
                'description': f"函数 {node.name} 包含阻塞操作",
                'suggestions': [
                    '使用异步版本 (async/await)',
                    '使用线程池执行阻塞操作',
                    '使用 asyncio 替代同步调用',
                    '考虑使用消息队列'
                ],
                'estimated_improvement': '并发性能提升 5-10 倍'
            })
        
        if self._has_memory_intensive_patterns(node):
            bottlenecks.append({
                'type': 'memory',
                'category': 'memory_management',
                'severity': 'medium',
                'location': f"{file_path}:{node.lineno}",
                'description': f"函数 {node.name} 包含内存密集型操作",
                'suggestions': [
                    '使用生成器替代列表',
                    '流式处理大数据',
                    '分批处理数据集',
                    '及时释放不需要的对象'
                ],
                'estimated_improvement': '内存使用减少 40-80%'
            })
        
        if depth == "deep":
            deep_bottlenecks = self._deep_analysis(node, file_path, content)
            bottlenecks.extend(deep_bottlenecks)
        
        return bottlenecks
    
    def _analyze_class(
        self, 
        node: ast.ClassDef, 
        file_path: Path, 
        content: str,
        depth: str
    ) -> List[Dict[str, Any]]:
        """分析类性能问题"""
        bottlenecks = []
        
        method_count = sum(1 for n in node.body if isinstance(n, ast.FunctionDef))
        
        if method_count > 25:
            bottlenecks.append({
                'type': 'god_class',
                'category': 'code_structure',
                'severity': 'medium',
                'location': f"{file_path}:{node.lineno}",
                'description': f"类 {node.name} 包含过多方法 ({method_count}个)",
                'metrics': {'method_count': method_count},
                'suggestions': [
                    '拆分为多个职责单一的类',
                    '使用组合替代继承',
                    '提取相关方法到工具类',
                    '应用设计模式优化结构'
                ],
                'estimated_improvement': '提升可维护性和测试性'
            })
        
        return bottlenecks
    
    def _analyze_frontend(
        self, 
        frontend_dir: Path, 
        depth: str = "standard"
    ) -> Dict[str, Any]:
        """分析前端代码性能"""
        results = {
            'bottlenecks': [],
            'stats': {
                'files': 0
            }
        }
        
        for vue_file in frontend_dir.rglob("*.vue"):
            if "node_modules" in str(vue_file):
                continue
            
            vue_bottlenecks = self._analyze_vue_component(vue_file)
            results['bottlenecks'].extend(vue_bottlenecks)
            results['stats']['files'] += 1
        
        for ts_file in frontend_dir.rglob("*.ts"):
            if "node_modules" in str(ts_file):
                continue
            
            ts_bottlenecks = self._analyze_typescript_file(ts_file)
            results['bottlenecks'].extend(ts_bottlenecks)
            results['stats']['files'] += 1
        
        return results
    
    def _analyze_vue_component(self, file_path: Path) -> List[Dict[str, Any]]:
        """分析Vue组件性能"""
        bottlenecks = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            vfor_count = content.count('v-for')
            if vfor_count > 5:
                bottlenecks.append({
                    'type': 'rendering',
                    'category': 'frontend',
                    'severity': 'medium',
                    'location': str(file_path),
                    'description': f"组件包含多个 v-for ({vfor_count}个)，可能影响渲染性能",
                    'suggestions': [
                        '使用虚拟滚动处理大列表',
                        '使用分页加载',
                        '优化 key 绑定',
                        '使用计算属性缓存结果'
                    ],
                    'estimated_improvement': '渲染性能提升 50-70%'
                })
            
            if 'watch:' in content and 'deep: true' in content:
                bottlenecks.append({
                    'type': 'reactivity',
                    'category': 'frontend',
                    'severity': 'medium',
                    'location': str(file_path),
                    'description': "组件使用深度 watch 可能影响性能",
                    'suggestions': [
                        '避免深度监听',
                        '使用精确属性监听',
                        '使用计算属性替代',
                        '考虑使用 immutable 数据'
                    ],
                    'estimated_improvement': '30-50%'
                })
                
        except Exception:
            pass
        
        return bottlenecks
    
    def _analyze_typescript_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """分析TypeScript文件性能"""
        bottlenecks = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            chained_methods = content.count('.filter(') + content.count('.map(') + content.count('.reduce(')
            if chained_methods > 5:
                bottlenecks.append({
                    'type': 'array_operations',
                    'category': 'frontend',
                    'severity': 'low',
                    'location': str(file_path),
                    'description': f"文件包含大量链式数组操作 ({chained_methods}次)",
                    'suggestions': [
                        '合并为单次遍历',
                        '使用 for 循环替代',
                        '考虑使用 transducer 模式',
                        '使用缓存避免重复计算'
                    ],
                    'estimated_improvement': '20-40%'
                })
                
        except Exception:
            pass
        
        return bottlenecks
    
    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """计算圈复杂度"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
            elif isinstance(child, (ast.BoolOp,)):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _calculate_nested_depth(self, node: ast.AST) -> int:
        """计算最大嵌套深度"""
        max_depth = 0
        
        def get_depth(n: ast.AST, current_depth: int = 0):
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)
            
            if isinstance(n, (ast.If, ast.While, ast.For, ast.With, ast.Try, ast.ExceptHandler)):
                for child in ast.iter_child_nodes(n):
                    get_depth(child, current_depth + 1)
            else:
                for child in ast.iter_child_nodes(n):
                    get_depth(child, current_depth)
        
        get_depth(node)
        return max_depth
    
    def _has_database_queries_in_loop(self, node: ast.FunctionDef) -> bool:
        """检查是否有循环中的数据库查询"""
        has_loop = any(isinstance(child, (ast.For, ast.While)) for child in ast.walk(node))
        
        if not has_loop:
            return False
        
        db_methods = {'query', 'filter', 'get', 'execute', 'fetchall', 'first', 'all', 'save', 'update', 'delete'}
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    if child.func.attr in db_methods:
                        return True
        
        return False
    
    def _has_blocking_operations(self, node: ast.FunctionDef) -> bool:
        """检查是否有阻塞操作"""
        blocking_patterns = {
            'time.sleep', 'requests.get', 'requests.post', 
            'requests.put', 'requests.delete', 'open('
        }
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                call_str = ""
                if isinstance(child.func, ast.Attribute):
                    if isinstance(child.func.value, ast.Name):
                        call_str = f"{child.func.value.id}.{child.func.attr}"
                elif isinstance(child.func, ast.Name):
                    call_str = child.func.id
                
                for pattern in blocking_patterns:
                    if pattern in call_str or (isinstance(child.func, ast.Name) and pattern.startswith(child.func.id)):
                        return True
        
        return False
    
    def _has_memory_intensive_patterns(self, node: ast.FunctionDef) -> bool:
        """检查是否有内存密集型操作"""
        patterns = ['.read()', '.readlines()', 'list(range(', 'list(']
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                call_str = ast.dump(child)
                for pattern in patterns:
                    if pattern in call_str:
                        return True
        
        return False
    
    def _deep_analysis(
        self, 
        node: ast.FunctionDef, 
        file_path: Path, 
        content: str
    ) -> List[Dict[str, Any]]:
        """深度分析（仅在深度模式下执行）"""
        bottlenecks = []
        
        inefficient_calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    if child.func.attr in ['index', 'find', 'count', 'remove']:
                        inefficient_calls.append(child.func.attr)
        
        if len(inefficient_calls) >= 3:
            bottlenecks.append({
                'type': 'inefficient_algorithm',
                'category': 'algorithm',
                'severity': 'low',
                'location': f"{file_path}:{node.lineno}",
                'description': f"函数 {node.name} 使用了多个低效操作: {', '.join(inefficient_calls)}",
                'suggestions': [
                    '使用集合/字典实现 O(1) 查找',
                    '使用二分查找',
                    '预计算和缓存结果'
                ],
                'estimated_improvement': '10-50%'
            })
        
        magic_numbers = self._detect_magic_numbers(content, node.lineno, getattr(node, 'end_lineno', node.lineno + 50))
        if len(magic_numbers) > 3:
            bottlenecks.append({
                'type': 'magic_numbers',
                'category': 'code_quality',
                'severity': 'info',
                'location': f"{file_path}:{node.lineno}",
                'description': f"函数 {node.name} 使用了多个魔法数字",
                'suggestions': [
                    '使用命名常量替代魔法数字',
                    '提取为配置参数',
                    '添加注释说明数值含义'
                ],
                'estimated_improvement': '提升代码可读性和维护性'
            })
        
        return bottlenecks
    
    def _detect_magic_numbers(self, content: str, start_line: int, end_line: int) -> List[str]:
        """检测魔法数字"""
        lines = content.split('\n')
        magic_numbers = []
        
        pattern = r'\b(\d{2,}|0[xX][\da-fA-F]+)\b'
        
        for line_num in range(start_line - 1, min(end_line, len(lines))):
            line = lines[line_num]
            
            if re.search(r'(const|var|let|CONFIG|#define)\s+', line):
                continue
            
            matches = re.findall(pattern, line)
            for match in matches:
                if match not in ['0', '1', '2']:
                    magic_numbers.append(match)
        
        return magic_numbers
    
    def _parse_profile_hotspots(self, profile_output: str) -> List[Dict[str, Any]]:
        """解析性能分析热点"""
        hotspots = []
        lines = profile_output.strip().split('\n')
        
        for line in lines[5:]:
            parts = line.split()
            if len(parts) >= 6:
                try:
                    hotspots.append({
                        'ncalls': parts[0],
                        'total_time': float(parts[1]),
                        'per_call': float(parts[2]),
                        'cumulative_time': float(parts[3]),
                        'function': parts[5] if len(parts) > 5 else 'unknown',
                        'file': parts[6].split(':')[0] if len(parts) > 6 else 'unknown',
                        'line': int(parts[6].split(':')[1]) if len(parts) > 6 and ':' in parts[6] else 0
                    })
                except (ValueError, IndexError):
                    continue
        
        return hotspots
    
    def _deduplicate_bottlenecks(self, bottlenecks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重瓶颈"""
        seen = set()
        unique_bottlenecks = []
        
        for bottleneck in bottlenecks:
            key = (bottleneck.get('type'), bottleneck.get('location'), bottleneck.get('category'))
            if key not in seen:
                seen.add(key)
                unique_bottlenecks.append(bottleneck)
        
        return unique_bottlenecks
    
    def _prioritize_bottlenecks(self, bottlenecks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """对瓶颈按优先级排序"""
        severity_order = {
            'critical': 0,
            'high': 1,
            'medium': 2,
            'low': 3,
            'info': 4
        }
        
        return sorted(
            bottlenecks, 
            key=lambda b: severity_order.get(b.get('severity', 'low'), 4)
        )
    
    def _calculate_confidence_score(
        self, 
        bottlenecks: List[Dict[str, Any]], 
        stats: Dict[str, Any]
    ) -> float:
        """计算置信度分数"""
        base_confidence = 0.85
        
        if stats.get('files_analyzed', 0) > 50:
            base_confidence += 0.05
        if stats.get('functions_analyzed', 0) > 200:
            base_confidence += 0.05
        
        critical_count = sum(1 for b in bottlenecks if b.get('severity') == 'critical')
        if critical_count > 0:
            base_confidence = min(base_confidence + 0.05, 1.0)
        
        return min(base_confidence, 1.0)


class IntelligentOptimizationPlanner:
    """智能优化方案规划器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self._config = config or {}
        self._logger = self._setup_logger()
        self._historical_data: List[Dict[str, Any]] = []
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('IntelligentOptimizationPlanner')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def generate_optimization_plan(
        self,
        detection_result: BottleneckDetectionResult,
        project_context: Dict[str, Any] = None
    ) -> OptimizationPlan:
        """生成智能优化方案"""
        plan_id = f"PLAN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        optimizations = []
        bottleneck_ids = []
        
        for bottleneck in detection_result.bottlenecks:
            opt = self._create_optimization_for_bottleneck(bottleneck, project_context)
            optimizations.append(opt)
            bottleneck_ids.append(f"{bleneck.get('type')}:{bottleneck.get('location')}")
        
        prioritized = self._prioritize_optimizations(optimizations)
        priority_order = [opt['id'] for opt in prioritized]
        
        phases = self._group_into_phases(prioritized)
        
        impact_estimation = self._estimate_overall_impact(prioritized)
        risk_assessment = self._assess_risks(prioritized, project_context)
        
        plan = OptimizationPlan(
            plan_id=plan_id,
            created_at=datetime.now().isoformat(),
            bottlenecks_addressed=bottleneck_ids,
            optimizations=prioritized,
            priority_order=priority_order,
            estimated_impact=impact_estimation,
            risk_assessment=risk_assessment,
            implementation_phases=phases
        )
        
        self._logger.info(f"优化方案已生成: {len(optimizations)} 个优化项")
        return plan
    
    def _create_optimization_for_bottleneck(
        self, 
        bottleneck: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """为单个瓶颈创建优化项"""
        opt_id = f"OPT-{hashlib.md5(str(bottleneck).encode()).hexdigest()[:8].upper()}"
        
        category = bottleneck.get('category', 'general')
        category_config = self._get_category_optimization_config(category)
        
        optimization = {
            'id': opt_id,
            'target_bottleneck': bottleneck,
            'category': category,
            'title': self._generate_optimization_title(bottleneck),
            'description': bottleneck.get('description', ''),
            'implementation_steps': self._generate_implementation_steps(bottleneck, category),
            'code_changes': self._generate_code_change_template(bottleneck, category),
            'expected_benefits': bottleneck.get('suggestions', []),
            'estimated_effort': self._estimate_effort(bottleneck, category),
            'risk_level': self._assess_optimization_risk(bottleneck, category),
            'dependencies': self._identify_dependencies(bottleneck, category),
            'rollback_strategy': self._define_rollback_strategy(category),
            'validation_criteria': self._define_validation_criteria(bottleneck),
            **category_config
        }
        
        return optimization
    
    def _get_category_optimization_config(self, category: str) -> Dict[str, Any]:
        """获取类别特定的优化配置"""
        configs = {
            'algorithm': {
                'auto_applicable': True,
                'safe_mode': True,
                'requires_testing': True,
                'typical_improvement_range': (30, 70)
            },
            'database': {
                'auto_applicable': False,
                'safe_mode': False,
                'requires_testing': True,
                'typical_improvement_range': (60, 95)
            },
            'memory_management': {
                'auto_applicable': True,
                'safe_mode': True,
                'requires_testing': False,
                'typical_improvement_range': (40, 80)
            },
            'io_operations': {
                'auto_applicable': True,
                'safe_mode': True,
                'requires_testing': True,
                'typical_improvement_range': (30, 60)
            },
            'code_structure': {
                'auto_applicable': False,
                'safe_mode': True,
                'requires_testing': True,
                'typical_improvement_range': (10, 30)
            },
            'frontend': {
                'auto_applicable': False,
                'safe_mode': True,
                'requires_testing': True,
                'typical_improvement_range': (20, 50)
            }
        }
        
        return configs.get(category, configs.get('general', {}))
    
    def _generate_optimization_title(self, bottleneck: Dict[str, Any]) -> str:
        """生成优化标题"""
        type_labels = {
            'complexity': '降低圈复杂度',
            'nesting': '减少嵌套深度',
            'n_plus_one': '解决N+1查询问题',
            'blocking': '转换为非阻塞操作',
            'memory': '优化内存使用',
            'god_class': '拆分大类',
            'rendering': '优化渲染性能',
            'reactivity': '优化响应式系统',
            'inefficient_algorithm': '改进算法效率',
            'runtime_performance': '优化运行时性能',
            'hotspot': '优化热点函数'
        }
        
        return type_labels.get(bottleneck.get('type'), '通用性能优化')
    
    def _generate_implementation_steps(
        self, 
        bottleneck: Dict[str, Any], 
        category: str
    ) -> List[str]:
        """生成实施步骤"""
        base_steps = [
            "分析当前实现并理解业务逻辑",
            "设计优化方案并评估影响范围",
            "编写优化代码",
            "编写或更新单元测试",
            "在安全环境中验证优化效果",
            "监控生产环境表现"
        ]
        
        category_specific = {
            'algorithm': [
                "识别算法的时间/空间复杂度",
                "研究更高效的算法或数据结构",
                "实现优化并保持接口不变"
            ],
            'database': [
                "分析查询执行计划",
                "识别缺失索引",
                "重构查询以消除N+1问题"
            ],
            'memory_management': [
                "分析内存分配模式",
                "识别大对象和内存泄漏点",
                "实现对象池或延迟加载"
            ]
        }
        
        steps = category_specific.get(category, [])
        steps.extend(base_steps)
        
        return steps
    
    def _generate_code_change_template(
        self, 
        bottleneck: Dict[str, Any], 
        category: str
    ) -> Dict[str, Any]:
        """生成代码变更模板"""
        templates = {
            'algorithm': {
                'before_pattern': 'O(n²) 或更高复杂度的实现',
                'after_pattern': 'O(n log n) 或更低复杂度的实现',
                'example': '''
# Before: Nested loop O(n²)
def find_duplicates(items):
    duplicates = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j]:
                duplicates.append(items[i])
    return duplicates

# After: Using set O(n)
def find_duplicates_optimized(items):
    seen = set()
    duplicates = set()
    for item in items:
        if item in seen:
            duplicates.add(item)
        else:
            seen.add(item)
    return list(duplicates)
'''
            },
            'database': {
                'before_pattern': '循环中的数据库查询',
                'after_pattern': '批量查询或JOIN',
                'example': '''
# Before: N+1 queries
def get_user_orders(user_ids):
    orders = []
    for user_id in user_ids:
        orders.extend(db.query(Order).filter_by(user_id=user_id).all())
    return orders

# After: Single query with IN clause
def get_user_orders_optimized(user_ids):
    return db.query(Order).filter(Order.user_id.in_(user_ids)).all()
'''
            },
            'memory_management': {
                'before_pattern': '一次性加载全部数据到内存',
                'after_pattern': '流式处理或分页加载',
                'example': '''
# Before: Load all into memory
def process_large_file(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    for line in lines:
        process(line)

# After: Stream processing
def process_large_file_optimized(file_path):
    with open(file_path, 'r') as f:
        for line in f:
            process(line)
'''
            }
        }
        
        return templates.get(category, templates.get('algorithm', {}))
    
    def _estimate_effort(self, bottleneck: Dict[str, Any], category: str) -> Dict[str, Any]:
        """估算工作量"""
        effort_map = {
            'algorithm': {'hours': 4, 'complexity': 'medium', 'skills_required': ['算法', '数据结构']},
            'database': {'hours': 8, 'complexity': 'high', 'skills_required': ['SQL', 'ORM', '索引优化']},
            'memory_management': {'hours': 3, 'complexity': 'medium', 'skills_required': ['内存管理', '性能调优']},
            'io_operations': {'hours': 4, 'complexity': 'medium', 'skills_required': ['异步编程', 'I/O优化']},
            'code_structure': {'hours': 6, 'complexity': 'high', 'skills_required': ['架构设计', '重构']}
        }
        
        base_effort = effort_map.get(category, {'hours': 4, 'complexity': 'medium'})
        
        severity_multiplier = {
            'critical': 1.5,
            'high': 1.2,
            'medium': 1.0,
            'low': 0.8,
            'info': 0.5
        }
        
        multiplier = severity_multiplier.get(bottleneck.get('severity', 'medium'), 1.0)
        
        return {
            **base_effort,
            'estimated_hours': base_effort['hours'] * multiplier
        }
    
    def _assess_optimization_risk(self, bottleneck: Dict[str, Any], category: str) -> Dict[str, Any]:
        """评估优化风险"""
        risk_factors = {
            'potential_breakage': self._calculate_breakage_risk(bottleneck, category),
            'performance_regression_risk': self._calculate_regression_risk(category),
            'testing_coverage_requirement': self._get_testing_requirement(category),
            'rollback_complexity': self._get_rollback_complexity(category)
        }
        
        overall_risk = (
            risk_factors['potential_breakage'] * 0.4 +
            risk_factors['performance_regression_risk'] * 0.3 +
            risk_factors['testing_coverage_requirement'] * 0.2 +
            risk_factors['rollback_complexity'] * 0.1
        )
        
        if overall_risk < 0.3:
            risk_level = 'low'
        elif overall_risk < 0.6:
            risk_level = 'medium'
        else:
            risk_level = 'high'
        
        return {
            'risk_level': risk_level,
            'overall_score': overall_risk,
            'factors': risk_factors,
            'mitigation_strategies': self._get_risk_mitigation(risk_level)
        }
    
    def _calculate_breakage_risk(self, bottleneck: Dict[str, Any], category: str) -> float:
        """计算破坏风险"""
        high_risk_categories = ['database', 'code_structure']
        medium_risk_categories = ['algorithm', 'io_operations']
        
        if category in high_risk_categories:
            base_risk = 0.6
        elif category in medium_risk_categories:
            base_risk = 0.4
        else:
            base_risk = 0.2
        
        severity_impact = {
            'critical': 0.3,
            'high': 0.2,
            'medium': 0.1,
            'low': 0.0,
            'info': 0.0
        }
        
        return min(base_risk + severity_impact.get(bottleneck.get('severity', 'medium'), 0), 1.0)
    
    def _calculate_regression_risk(self, category: str) -> float:
        """计算回退风险"""
        regression_risks = {
            'algorithm': 0.3,
            'database': 0.5,
            'memory_management': 0.2,
            'io_operations': 0.3,
            'code_structure': 0.4,
            'frontend': 0.35
        }
        
        return regression_risks.get(category, 0.3)
    
    def _get_testing_requirement(self, category: str) -> float:
        """获取测试覆盖要求"""
        requirements = {
            'database': 0.9,
            'algorithm': 0.8,
            'code_structure': 0.85,
            'io_operations': 0.75,
            'memory_management': 0.7,
            'frontend': 0.75
        }
        
        return requirements.get(category, 0.75)
    
    def _get_rollback_complexity(self, category: str) -> float:
        """获取回滚复杂度"""
        complexities = {
            'database': 0.6,
            'code_structure': 0.5,
            'algorithm': 0.3,
            'io_operations': 0.3,
            'memory_management': 0.2,
            'frontend': 0.4
        }
        
        return complexities.get(category, 0.3)
    
    def _get_risk_mitigation(self, risk_level: str) -> List[str]:
        """获取风险缓解策略"""
        mitigations = {
            'high': [
                '实施全面的回归测试',
                '在预发布环境充分验证',
                '准备详细的回滚计划',
                '逐步推出并监控',
                '建立快速回滚机制'
            ],
            'medium': [
                '编写单元测试和集成测试',
                '在开发环境充分测试',
                '准备回滚方案',
                '监控关键指标'
            ],
            'low': [
                '基本功能测试',
                '监控主要指标',
                '标准发布流程'
            ]
        }
        
        return mitigations.get(risk_level, mitigations['medium'])
    
    def _identify_dependencies(
        self, 
        bottleneck: Dict[str, Any], 
        category: str
    ) -> List[Dict[str, Any]]:
        """识别依赖关系"""
        dependencies = []
        
        common_deps = {
            'algorithm': [
                {'type': 'tool', 'name': '性能分析工具', 'required': True},
                {'type': 'knowledge', 'name': '算法和数据结构知识', 'required': True}
            ],
            'database': [
                {'type': 'tool', 'name': '数据库监控工具', 'required': True},
                {'type': 'access', 'name': '数据库管理员权限', 'required': False},
                {'type': 'knowledge', 'name': 'SQL和ORM知识', 'required': True}
            ],
            'memory_management': [
                {'type': 'tool', 'name': '内存分析工具', 'required': True},
                {'type': 'knowledge', 'name': '内存管理模式', 'required': True}
            ]
        }
        
        dependencies.extend(common_deps.get(category, []))
        
        return dependencies
    
    def _define_rollback_strategy(self, category: str) -> Dict[str, Any]:
        """定义回滚策略"""
        strategies = {
            'database': {
                'method': 'feature_flag',
                'complexity': 'high',
                'time_estimate_minutes': 15,
                'steps': [
                    '禁用功能标志',
                    '验证系统恢复正常',
                    '调查根本原因',
                    '制定修复计划'
                ]
            },
            'code_structure': {
                'method': 'git_revert',
                'complexity': 'medium',
                'time_estimate_minutes': 10,
                'steps': [
                    '回滚代码提交',
                    '重新部署',
                    '验证功能正常'
                ]
            },
            'default': {
                'method': 'git_revert',
                'complexity': 'low',
                'time_estimate_minutes': 5,
                'steps': [
                    '回滚更改',
                    '重新部署',
                    '验证修复'
                ]
            }
        }
        
        return strategies.get(category, strategies['default'])
    
    def _define_validation_criteria(self, bottleneck: Dict[str, Any]) -> Dict[str, Any]:
        """定义验证标准"""
        criteria = {
            'functional_correctness': {
                'required': True,
                'description': '所有现有测试必须通过',
                'threshold': '100% 测试通过率'
            },
            'performance_improvement': {
                'required': True,
                'description': '必须达到预期的性能改善',
                'threshold': f"至少 {bottleneck.get('estimated_improvement', '10%')}"
            },
            'no_regressions': {
                'required': True,
                'description': '不能引入新的性能问题',
                'threshold': '无新增瓶颈'
            },
            'code_quality': {
                'required': False,
                'description': '代码质量不应下降',
                'threshold': '维持或提升代码质量分数'
            }
        }
        
        return criteria
    
    def _prioritize_optimizations(self, optimizations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """对优化项排序"""
        def scoring_func(opt):
            score = 0
            
            severity_scores = {'critical': 100, 'high': 75, 'medium': 50, 'low': 25, 'info': 10}
            score += severity_scores.get(opt.get('target_bottleneck', {}).get('severity', 'low'), 10)
            
            risk_penalty = {'high': -30, 'medium': -15, 'low': 0}
            score += risk_penalty.get(opt.get('risk_level', {}).get('risk_level', 'medium'), -15)
            
            auto_applicable_bonus = 20 if opt.get('auto_applicable') else 0
            score += auto_applicable_bonus
            
            effort_factor = opt.get('estimated_effort', {}).get('estimated_hours', 10)
            score -= min(effort_factor, 20)
            
            return score
        
        return sorted(optimizations, key=scoring_func, reverse=True)
    
    def _group_into_phases(self, optimizations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将优化分组到实施阶段"""
        phases = []
        
        safe_auto_opts = [opt for opt in optimizations if opt.get('auto_applicable') and opt.get('risk_level', {}).get('risk_level') == 'low']
        manual_safe_opts = [opt for opt in optimizations if not opt.get('auto_applicable') and opt.get('risk_level', {}).get('risk_level') in ['low', 'medium']]
        risky_opts = [opt for opt in optimizations if opt.get('risk_level', {}).get('risk_level') == 'high']
        
        if safe_auto_opts:
            phases.append({
                'phase': 1,
                'name': '自动安全优化',
                'description': '低风险的自动适用优化',
                'optimizations': [opt['id'] for opt in safe_auto_opts],
                'estimated_duration_hours': sum(opt.get('estimated_effort', {}).get('estimated_hours', 1) for opt in safe_auto_opts),
                'risk_level': 'low'
            })
        
        if manual_safe_opts:
            phases.append({
                'phase': 2,
                'name': '手动安全优化',
                'description': '需要人工介入的中低风险优化',
                'optimizations': [opt['id'] for opt in manual_safe_opts],
                'estimated_duration_hours': sum(opt.get('estimated_effort', {}).get('estimated_hours', 2) for opt in manual_safe_opts),
                'risk_level': 'medium'
            })
        
        if risky_opts:
            phases.append({
                'phase': 3,
                'name': '高风险优化',
                'description': '需要特别关注的高风险优化',
                'optimizations': [opt['id'] for opt in risky_opts],
                'estimated_duration_hours': sum(opt.get('estimated_effort', {}).get('estimated_hours', 4) for opt in risky_opts),
                'risk_level': 'high'
            })
        
        return phases
    
    def _estimate_overall_impact(self, optimizations: List[Dict[str, Any]]) -> Dict[str, float]:
        """估算整体影响"""
        total_impact = {
            'performance_improvement_percent': 0.0,
            'memory_reduction_percent': 0.0,
            'throughput_increase_percent': 0.0,
            'code_quality_improvement': 0.0,
            'maintenance_cost_reduction': 0.0
        }
        
        for opt in optimizations:
            improvement_range = opt.get('typical_improvement_range', (10, 30))
            avg_improvement = sum(improvement_range) / 2
            
            category = opt.get('category', '')
            if category in ['algorithm', 'hotspot', 'runtime_performance']:
                total_impact['performance_improvement_percent'] += avg_improvement * 0.3
            elif category == 'memory_management':
                total_impact['memory_reduction_percent'] += avg_improvement * 0.4
            elif category == 'database':
                total_impact['throughput_increase_percent'] += avg_improvement * 0.3
            elif category == 'code_structure':
                total_impact['code_quality_improvement'] += avg_improvement * 0.2
                total_impact['maintenance_cost_reduction'] += avg_improvement * 0.3
        
        for key in total_impact:
            total_impact[key] = min(total_impact[key], 95.0)
        
        return total_impact
    
    def _assess_risks(
        self, 
        optimizations: List[Dict[str, Any]], 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """整体风险评估"""
        high_risk_count = sum(1 for opt in optimizations if opt.get('risk_level', {}).get('risk_level') == 'high')
        medium_risk_count = sum(1 for opt in optimizations if opt.get('risk_level', {}).get('risk_level') == 'medium')
        
        overall_risk_score = (high_risk_count * 0.8 + medium_risk_count * 0.4) / max(len(optimizations), 1)
        
        if overall_risk_score > 0.6:
            risk_level = 'high'
        elif overall_risk_score > 0.3:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'overall_risk_level': risk_level,
            'risk_score': overall_risk_score,
            'high_risk_items': high_risk_count,
            'medium_risk_items': medium_risk_count,
            'recommendations': self._generate_risk_recommendations(risk_level, high_risk_count)
        }
    
    def _generate_risk_recommendations(self, risk_level: str, high_risk_count: int) -> List[str]:
        """生成风险建议"""
        recommendations = []
        
        if risk_level == 'high':
            recommendations.extend([
                f"有 {high_risk_count} 个高风险优化项，建议分阶段实施",
                "每个高风险优化都需要完整的测试覆盖",
                "考虑使用特性开关进行灰度发布",
                "准备紧急回滚预案",
                "增加代码审查严格程度"
            ])
        elif risk_level == 'medium':
            recommendations.extend([
                "大部分优化项风险可控",
                "确保中等风险项有充分的测试",
                "按照优先级顺序逐步实施"
            ])
        else:
            recommendations.append("整体风险较低，可以较为放心地实施优化")
        
        return recommendations


class SafeOptimizationExecutor:
    """安全的优化执行器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self._config = config or {}
        self._execution_history: List[ExecutionResult] = []
        self._backup_manager = BackupManager(config)
        self._validator = OptimizationValidator(config)
        self._logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('SafeOptimizationExecutor')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def execute_optimization_plan(
        self,
        plan: OptimizationPlan,
        project_path: Path,
        auto_apply: bool = False,
        phase: int = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """执行优化方案"""
        execution_start = datetime.now()
        
        results = {
            'plan_id': plan.plan_id,
            'started_at': execution_start.isoformat(),
            'completed_at': '',
            'total_duration_seconds': 0,
            'executions': [],
            'summary': {},
            'success': False
        }
        
        optimizations_to_execute = self._select_optimizations_for_execution(plan, phase)
        
        for opt in optimizations_to_execute:
            if dry_run:
                result = self._simulate_execution(opt, project_path)
            else:
                result = self._execute_single_optimization(opt, project_path, auto_apply)
            
            results['executions'].append(result.to_dict())
            
            if not result.success and opt.get('risk_level', {}).get('risk_level') == 'high':
                self._logger.error(f"高风险优化失败，中止执行: {opt['id']}")
                break
        
        execution_end = datetime.now()
        results['completed_at'] = execution_end.isoformat()
        results['total_duration_seconds'] = (execution_end - execution_start).total_seconds()
        
        successful = sum(1 for e in results['executions'] if e.get('success', False))
        results['summary'] = {
            'total_optimizations': len(results['executions']),
            'successful': successful,
            'failed': len(results['executions']) - successful,
            'success_rate': (successful / len(results['executions']) * 100) if results['executions'] else 0
        }
        results['success'] = successful == len(results['executions'])
        
        return results
    
    def _select_optimizations_for_execution(
        self, 
        plan: OptimizationPlan, 
        phase: int = None
    ) -> List[Dict[str, Any]]:
        """选择要执行的优化项"""
        if phase is not None:
            phase_data = next((p for p in plan.implementation_phases if p['phase'] == phase), None)
            if phase_data:
                phase_opt_ids = set(phase_data['optimizations'])
                return [opt for opt in plan.optimizations if opt['id'] in phase_opt_ids]
        
        return plan.optimizations
    
    def _simulate_execution(
        self, 
        optimization: Dict[str, Any], 
        project_path: Path
    ) -> ExecutionResult:
        """模拟执行（dry run）"""
        execution_id = f"SIM-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        return ExecutionResult(
            execution_id=execution_id,
            optimization_id=optimization['id'],
            status='simulated',
            started_at=datetime.now().isoformat(),
            completed_at=datetime.now().isoformat(),
            changes_made=[{
                'type': 'simulation',
                'description': f"模拟执行优化: {optimization['title']}"
            }],
            backup_created=False,
            success=True,
            execution_log=[
                f"[DRY RUN] 将要执行优化: {optimization['title']}",
                f"[DRY RUN] 目标文件: {optimization.get('target_bottleneck', {}).get('location', 'unknown')}",
                f"[DRY RUN] 风险等级: {optimization.get('risk_level', {}).get('risk_level', 'unknown')}",
                "[DRY RUN] 执行成功（模拟）"
            ]
        )
    
    def _execute_single_optimization(
        self,
        optimization: Dict[str, Any],
        project_path: Path,
        auto_apply: bool
    ) -> ExecutionResult:
        """执行单个优化"""
        execution_id = f"EXEC-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        start_time = datetime.now()
        
        execution_log = []
        changes_made = []
        
        try:
            target_location = optimization.get('target_bottleneck', {}).get('location', '')
            
            if ':' in target_location and target_location.endswith('.py'):
                file_path_str = target_location.rsplit(':', 1)[0]
                file_path = Path(file_path_str)
                
                if file_path.exists():
                    execution_log.append(f"[{datetime.now().isoformat()}] 创建备份")
                    backup_path = self._backup_manager.create_backup([file_path])
                    
                    before_metrics = self._capture_metrics(project_path)
                    
                    execution_log.append(f"[{datetime.now().isoformat()}] 应用优化: {optimization['title']}")
                    
                    if auto_apply and optimization.get('auto_applicable'):
                        change_result = self._apply_code_changes(file_path, optimization)
                        changes_made.append(change_result)
                        
                        after_metrics = self._capture_metrics(project_path)
                        
                        validation = self._validator.validate_optimization(
                            before_metrics, 
                            after_metrics, 
                            optimization.get('validation_criteria', {})
                        )
                        
                        if validation['passed']:
                            execution_log.append(f"[{datetime.now().isoformat()}] 优化验证通过")
                            success = True
                        else:
                            execution_log.append(f"[{datetime.now().isoformat()}] 优化验证未通过，回滚")
                            self._backup_manager.rollback(backup_path)
                            success = False
                    else:
                        execution_log.append(f"[{datetime.now().isoformat()}] 优化方案已生成，等待手动实施")
                        changes_made.append({
                            'type': 'manual',
                            'description': f"需要手动实施: {optimization['title']}",
                            'steps': optimization.get('implementation_steps', [])
                        })
                        success = True
                else:
                    execution_log.append(f"[{datetime.now().isoformat()}] 文件不存在: {file_path}")
                    success = True
            else:
                execution_log.append(f"[{datetime.now().isoformat()}] 非代码优化或位置无效，跳过自动执行")
                changes_made.append({
                    'type': 'manual_only',
                    'description': f"此优化需要手动实施: {optimization['title']}"
                })
                success = True
                
        except Exception as e:
            execution_log.append(f"[{datetime.now().isoformat()}] 执行出错: {str(e)}")
            success = False
        
        end_time = datetime.now()
        
        return ExecutionResult(
            execution_id=execution_id,
            optimization_id=optimization['id'],
            status='completed' if success else 'failed',
            started_at=start_time.isoformat(),
            completed_at=end_time.isoformat(),
            changes_made=changes_made,
            backup_created=self._backup_manager.last_backup_path != "",
            backup_path=self._backup_manager.last_backup_path,
            rollback_available=self._backup_manager.last_backup_path != "",
            success=success,
            error_message='' if success else 'Execution failed',
            execution_log=execution_log
        )
    
    def _apply_code_changes(
        self, 
        file_path: Path, 
        optimization: Dict[str, Any]
    ) -> Dict[str, Any]:
        """应用代码变更"""
        category = optimization.get('category', 'general')
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            if category == 'memory_management':
                content = self._optimize_memory_patterns(content)
            elif category == 'algorithm':
                content = self._optimize_algorithm_patterns(content)
            elif category == 'io_operations':
                content = self._optimize_io_patterns(content)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                return {
                    'type': 'code_modification',
                    'file': str(file_path),
                    'applied': True,
                    'changes_count': self._count_changes(original_content, content)
                }
            else:
                return {
                    'type': 'no_changes_needed',
                    'file': str(file_path),
                    'applied': False,
                    'message': '无需修改或无法自动应用'
                }
                
        except Exception as e:
            return {
                'type': 'error',
                'file': str(file_path),
                'applied': False,
                'error': str(e)
            }
    
    def _optimize_memory_patterns(self, content: str) -> str:
        """优化内存模式"""
        optimized = content
        
        optimized = re.sub(
            r'(\w+)\s*=\s*\[\]\s*\n\s*for\s+(\w+)\s+in\s+(\w+):\s*\n\s*\1\.append\((.+)\)',
            r'\1 = [\4 for \2 in \3]',
            optimized
        )
        
        return optimized
    
    def _optimize_algorithm_patterns(self, content: str) -> str:
        """优化算法模式"""
        return content
    
    def _optimize_io_patterns(self, content: str) -> str:
        """优化I/O模式"""
        return content
    
    def _count_changes(self, original: str, modified: str) -> int:
        """统计变更数量"""
        orig_lines = original.split('\n')
        mod_lines = modified.split('\n')
        
        changes = 0
        for i, (orig, mod) in enumerate(zip(orig_lines, mod_lines)):
            if orig != mod:
                changes += 1
        
        changes += abs(len(orig_lines) - len(mod_lines))
        
        return changes
    
    def _capture_metrics(self, project_path: Path) -> Dict[str, float]:
        """捕获性能指标"""
        metrics = {
            'timestamp': time.time(),
            'cpu_usage': 0.0,
            'memory_usage_mb': 0.0,
            'disk_io_bytes': 0.0
        }
        
        try:
            import psutil
            process = psutil.Process(os.getpid())
            metrics['cpu_usage'] = process.cpu_percent(interval=0.1)
            metrics['memory_usage_mb'] = process.memory_info().rss / 1024 / 1024
            metrics['disk_io_bytes'] = process.io_counters().read_bytes + process.io_counters().write_bytes
        except ImportError:
            pass
        except Exception:
            pass
        
        return metrics
    
    def get_execution_history(self) -> List[ExecutionResult]:
        return self._execution_history


class BackupManager:
    """备份管理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self._config = config or {}
        self._base_backup_dir = Path(self._config.get('backup_dir', './.perf_backups'))
        self.last_backup_path = ""
        self._logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('BackupManager')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def create_backup(self, files: List[Path]) -> str:
        """创建备份"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = self._base_backup_dir / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path in files:
            if file_path.exists():
                relative_path = file_path.relative_to(Path.cwd())
                dest_path = backup_dir / relative_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, dest_path)
        
        manifest = {
            'timestamp': timestamp,
            'created_at': datetime.now().isoformat(),
            'files': [str(f.relative_to(Path.cwd())) for f in files if f.exists()]
        }
        
        manifest_path = backup_dir / 'manifest.json'
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        self.last_backup_path = str(backup_dir)
        self._logger.info(f"备份已创建: {backup_dir}")
        
        return str(backup_dir)
    
    def rollback(self, backup_path: str) -> bool:
        """回滚到备份"""
        backup_dir = Path(backup_path)
        
        if not backup_dir.exists():
            self._logger.error(f"备份目录不存在: {backup_path}")
            return False
        
        manifest_path = backup_dir / 'manifest.json'
        if not manifest_path.exists():
            self._logger.error("清单文件不存在")
            return False
        
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            for relative_file in manifest.get('files', []):
                src = backup_dir / relative_file
                dest = Path.cwd() / relative_file
                
                if src.exists():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
            
            self._logger.info(f"回滚成功: {backup_path}")
            return True
            
        except Exception as e:
            self._logger.error(f"回滚失败: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""
        backups = []
        
        if not self._base_backup_dir.exists():
            return backups
        
        for backup_dir in sorted(self._base_backup_dir.iterdir(), reverse=True):
            if backup_dir.is_dir():
                manifest_path = backup_dir / 'manifest.json'
                if manifest_path.exists():
                    try:
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            manifest = json.load(f)
                        backups.append({
                            'path': str(backup_dir),
                            'timestamp': manifest.get('timestamp', ''),
                            'files': manifest.get('files', [])
                        })
                    except Exception:
                        pass
        
        return backups
    
    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """清理旧备份"""
        backups = self.list_backups()
        removed = 0
        
        for backup in backups[keep_count:]:
            backup_path = Path(backup['path'])
            if backup_path.exists():
                shutil.rmtree(backup_path)
                removed += 1
        
        if removed > 0:
            self._logger.info(f"已清理 {removed} 个旧备份")
        
        return removed


class OptimizationValidator:
    """优化验证器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self._config = config or {}
        self._logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('OptimizationValidator')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def validate_optimization(
        self,
        before_metrics: Dict[str, float],
        after_metrics: Dict[str, float],
        criteria: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """验证优化效果"""
        validation = {
            'passed': True,
            'checks': [],
            'warnings': [],
            'details': {}
        }
        
        memory_check = self._check_memory_improvement(before_metrics, after_metrics)
        validation['checks'].append(memory_check)
        validation['details']['memory'] = memory_check
        
        if not memory_check['passed']:
            validation['warnings'].append('内存使用未明显改善')
        
        cpu_check = self._check_cpu_usage(before_metrics, after_metrics)
        validation['checks'].append(cpu_check)
        validation['details']['cpu'] = cpu_check
        
        if not cpu_check['passed']:
            validation['warnings'].append('CPU使用率未明显降低')
        
        validation['passed'] = all(check['passed'] for check in validation['checks'])
        
        return validation
    
    def _check_memory_improvement(
        self, 
        before: Dict[str, float], 
        after: Dict[str, float]
    ) -> Dict[str, Any]:
        """检查内存改善情况"""
        before_mem = before.get('memory_usage_mb', 0)
        after_mem = after.get('memory_usage_mb', 0)
        
        if before_mem > 0:
            reduction = ((before_mem - after_mem) / before_mem) * 100
            passed = reduction > 5
        else:
            reduction = 0
            passed = True
        
        return {
            'check_type': 'memory_improvement',
            'passed': passed,
            'before_mb': before_mem,
            'after_mb': after_mem,
            'reduction_percent': reduction,
            'message': f"内存{'减少' if reduction > 0 else '增加'} {abs(reduction):.1f}%"
        }
    
    def _check_cpu_usage(
        self, 
        before: Dict[str, float], 
        after: Dict[str, float]
    ) -> Dict[str, Any]:
        """检查CPU使用情况"""
        before_cpu = before.get('cpu_usage', 0)
        after_cpu = after.get('cpu_usage', 0)
        
        if before_cpu > 0:
            reduction = ((before_cpu - after_cpu) / before_cpu) * 100
            passed = reduction > 3
        else:
            reduction = 0
            passed = True
        
        return {
            'check_type': 'cpu_usage',
            'passed': passed,
            'before_pct': before_cpu,
            'after_pct': after_cpu,
            'reduction_percent': reduction,
            "message": f"CPU使用率{'降低' if reduction > 0 else '上升'} {abs(reduction):.1f}%"
        }


class UnifiedPerformanceOptimizerEnhanced:
    """统一增强性能优化器"""
    
    def __init__(self, project_path: Path, config: Dict[str, Any] = None):
        self.project_path = Path(project_path)
        self._config = config or {}
        
        self.analyzer = EnhancedPerformanceAnalyzer(config)
        self.planner = IntelligentOptimizationPlanner(config)
        self.executor = SafeOptimizationExecutor(config)
        
        self._optimization_history: List[Dict[str, Any]] = []
        self._baselines: List[PerformanceBaseline] = []
        self._logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('UnifiedPerformanceOptimizerEnhanced')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def create_baseline(self) -> PerformanceBaseline:
        """创建性能基线"""
        baseline_id = f"BASELINE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        baseline = PerformanceBaseline(
            baseline_id=baseline_id,
            timestamp=datetime.now().isoformat(),
            metrics=self._collect_system_metrics(),
            project_state={
                'files_count': len(list(self.project_path.rglob('*.py'))),
                'last_modified': datetime.now().isoformat()
            }
        )
        
        self._baselines.append(baseline)
        self._logger.info(f"性能基线已创建: {baseline_id}")
        
        return baseline
    
    def run_optimization_cycle(
        self,
        analysis_depth: str = "standard",
        auto_apply: bool = False,
        execute_phase: int = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """运行完整优化周期"""
        cycle_start = datetime.now()
        
        self._logger.info("=" * 60)
        self._logger.info("开始性能优化周期")
        self._logger.info("=" * 60)
        
        baseline = self.create_baseline()
        
        self._logger.info("步骤 1/4: 分析项目性能...")
        detection_result = self.analyzer.analyze_project_performance(
            self.project_path, 
            analysis_depth=analysis_depth
        )
        
        self._logger.info(f"发现 {len(detection_result.bottlenecks)} 个性能瓶颈")
        
        self._logger.info("步骤 2/4: 生成优化方案...")
        optimization_plan = self.planner.generate_optimization_plan(detection_result)
        
        self._logger.info(f"生成 {len(optimization_plan.optimizations)} 个优化项")
        
        self._logger.info("步骤 3/4: 执行优化...")
        execution_result = self.executor.execute_optimization_plan(
            optimization_plan,
            self.project_path,
            auto_apply=auto_apply,
            phase=execute_phase,
            dry_run=dry_run
        )
        
        cycle_end = datetime.now()
        
        report = {
            'cycle_id': f"CYCLE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'baseline': baseline.to_dict(),
            'detection_result': detection_result.to_dict(),
            'optimization_plan': optimization_plan.to_dict(),
            'execution_result': execution_result,
            'summary': self._generate_cycle_summary(detection_result, optimization_plan, execution_result),
            'started_at': cycle_start.isoformat(),
            'completed_at': cycle_end.isoformat(),
            'duration_seconds': (cycle_end - cycle_start).total_seconds()
        }
        
        self._optimization_history.append(report)
        
        self._logger.info("=" * 60)
        self._logger.info(f"优化周期完成")
        self._logger.info(f"- 瓶颈数量: {len(detection_result.bottlenecks)}")
        self._logger.info(f"- 优化项数: {len(optimization_plan.optimizations)}")
        self._logger.info(f"- 执行成功: {execution_result.get('summary', {}).get('successful', 0)}/{execution_result.get('summary', {}).get('total_optimizations', 0)}")
        self._logger.info(f"- 总耗时: {(cycle_end - cycle_start).total_seconds():.2f}s")
        self._logger.info("=" * 60)
        
        return report
    
    def _collect_system_metrics(self) -> Dict[str, float]:
        """收集系统指标"""
        metrics = {}
        
        try:
            import psutil
            metrics['system_cpu_percent'] = psutil.cpu_percent(interval=0.1)
            metrics['system_memory_total_gb'] = psutil.virtual().total / (1024**3)
            metrics['system_memory_used_gb'] = psutil.virtual().used / (1024**3)
            metrics['system_disk_usage_percent'] = psutil.disk_usage('/').percent
        except ImportError:
            pass
        
        return metrics
    
    def _generate_cycle_summary(
        self,
        detection: BottleneckDetectionResult,
        plan: OptimizationPlan,
        execution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成周期摘要"""
        critical_count = sum(1 for b in detection.bottlenecks if b.get('severity') == 'critical')
        high_count = sum(1 for b in detection.bottlenecks if b.get('severity') == 'high')
        
        return {
            'bottlenecks_found': len(detection.bottlenecks),
            'critical_issues': critical_count,
            'high_priority_issues': high_count,
            'optimizations_planned': len(plan.optimizations),
            'optimizations_executed': execution.get('summary', {}).get('total_optimizations', 0),
            'successful_optimizations': execution.get('summary', {}).get('successful', 0),
            'overall_success': execution.get('success', False),
            'estimated_impact': plan.estimated_impact,
            'risk_level': plan.risk_assessment.get('overall_risk_level', 'unknown'),
            'recommendations': self._generate_recommendations(critical_count, high_count, execution)
        }
    
    def _generate_recommendations(
        self, 
        critical: int, 
        high: int, 
        execution: Dict[str, Any]
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if critical > 0:
            recommendations.append(f"⚠️ 发现 {critical} 个严重问题，建议立即处理")
        
        if high > 0:
            recommendations.append(f"🔴 发现 {high} 个高优先级问题，建议优先优化")
        
        success_rate = execution.get('summary', {}).get('success_rate', 0)
        if success_rate < 100:
            failed_count = execution.get('summary', {}).get('failed', 0)
            recommendations.append(f"⚠️ {failed_count} 个优化执行失败，建议检查错误日志")
        
        if not recommendations:
            recommendations.append("✅ 优化周期完成良好，建议持续监控")
        
        return recommendations
    
    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """获取优化历史"""
        return self._optimization_history
    
    def export_report(self, report: Dict[str, Any], output_path: Path):
        """导出报告"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        self._logger.info(f"报告已导出: {output_path}")


if __name__ == '__main__':
    print("增强的性能优化器模块已加载 (Phase 7.2)")
    print("\n主要组件:")
    print("- EnhancedPerformanceAnalyzer: 增强的性能分析器")
    print("- IntelligentOptimizationPlanner: 智能优化方案规划器")
    print("- SafeOptimizationExecutor: 安全的优化执行器")
    print("- BackupManager: 备份管理器")
    print("- OptimizationValidator: 优化验证器")
    print("- UnifiedPerformanceOptimizerEnhanced: 统一增强优化器")
