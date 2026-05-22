"""
回归测试智能执行框架 - 增强版

提供历史功能验证、变更影响分析、自动回归执行等功能
支持配置文件、HTML报告生成、并行执行、智能重试、AST分析等高级功能

增强功能:
1. 并行测试执行与智能重试机制
2. AST级别的代码变更分析
3. 数据流与控制流分析
4. 机器学习驱动的测试优先级
5. 测试依赖图与隔离管理
6. 趋势分析与可视化报告
7. 配置文件与数据库迁移影响分析
"""

import os
import sys
import json
import time
import argparse
import subprocess
import hashlib
import pickle
import threading
import queue
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import ast
import traceback

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False


class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    RETRY = "retry"


class ChangeType(Enum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


class ImpactLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class TestPriority(Enum):
    P0_CRITICAL = "p0_critical"
    P1_HIGH = "p1_high"
    P2_MEDIUM = "p2_medium"
    P3_LOW = "p3_low"
    P4_OPTIONAL = "p4_optional"


@dataclass
class CodeChange:
    file_path: str
    change_type: ChangeType
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    diff: Optional[str] = None
    affected_functions: List[str] = field(default_factory=list)
    affected_classes: List[str] = field(default_factory=list)
    affected_variables: List[str] = field(default_factory=list)
    affected_imports: List[str] = field(default_factory=list)
    ast_changes: Dict[str, Any] = field(default_factory=dict)
    complexity_delta: float = 0.0


@dataclass
class ImpactAnalysis:
    changed_file: str
    affected_files: List[str]
    affected_tests: List[str]
    impact_level: ImpactLevel
    risk_score: float
    reasoning: str
    transitive_impact: Dict[str, List[str]] = field(default_factory=dict)
    data_flow_paths: List[List[str]] = field(default_factory=list)
    api_impact: List[str] = field(default_factory=list)
    db_impact: List[str] = field(default_factory=list)


@dataclass
class RegressionTestResult:
    test_name: str
    test_file: str
    status: TestStatus
    duration: float
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    related_changes: List[str] = field(default_factory=list)
    retry_count: int = 0
    retry_history: List[Dict[str, Any]] = field(default_factory=list)
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None


@dataclass
class RegressionTestSuite:
    suite_name: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration: float
    results: List[RegressionTestResult] = field(default_factory=list)
    parallel_workers: int = 1
    retry_stats: Dict[str, int] = field(default_factory=dict)


@dataclass
class RegressionTestConfig:
    source_dirs: List[str] = field(default_factory=lambda: ["backend/app", "src"])
    test_dirs: List[str] = field(default_factory=lambda: ["backend/tests", "tests"])
    output_dir: str = None
    output_formats: List[str] = field(default_factory=lambda: ["json", "html"])
    baseline_file: str = "test_baseline.json"
    exclude_patterns: List[str] = field(default_factory=lambda: ["__pycache__", ".venv", "venv", "node_modules"])
    fail_fast: bool = False
    parallel: bool = True
    max_workers: int = 4
    timeout: int = 300
    retry_failed: bool = True
    retry_count: int = 2
    retry_delay: float = 1.0
    enable_ast_analysis: bool = True
    enable_data_flow_analysis: bool = True
    enable_ml_priority: bool = False
    history_file: str = "test_history.pkl"
    coverage_threshold: float = 70.0
    performance_baseline: Dict[str, float] = field(default_factory=dict)
    test_dependencies: Dict[str, List[str]] = field(default_factory=dict)
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.output_dir is None:
            try:
                from skillscripts.utils.enhanced_path_config_manager import create_path_manager, OutputType
                _path_mgr = create_path_manager()
                self.output_dir = str(_path_mgr.get_output_path(OutputType.REPORT, subdirectory="regression"))
            except Exception:
                self.output_dir = "docs/reports"


@dataclass
class TestMetrics:
    test_name: str
    avg_duration: float
    success_rate: float
    flakiness_score: float
    last_run: datetime
    total_runs: int
    failure_patterns: List[str] = field(default_factory=list)
    resource_usage: Dict[str, float] = field(default_factory=dict)


@dataclass
class TrendData:
    date: str
    total_tests: int
    passed: int
    failed: int
    duration: float
    pass_rate: float
    avg_risk_score: float


class ConfigLoader:
    def __init__(self, base_path: str):
        self.base_path = base_path

    def load(self, config_path: Optional[str] = None) -> RegressionTestConfig:
        config = RegressionTestConfig()
        
        if config_path:
            full_path = Path(self.base_path) / config_path
            if full_path.exists():
                try:
                    if full_path.suffix in [".yaml", ".yml"] and HAS_YAML:
                        with open(full_path, "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f)
                    elif full_path.suffix == ".json":
                        with open(full_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                    else:
                        return config
                    
                    if data:
                        for key, value in data.items():
                            if hasattr(config, key):
                                setattr(config, key, value)
                except Exception as e:
                    print(f"加载配置文件失败: {e}")
        
        return config

    def save_template(self, output_path: str):
        template = {
            "source_dirs": ["backend/app", "src"],
            "test_dirs": ["backend/tests", "tests"],
            "output_dir": "docs/reports",
            "output_formats": ["json", "html"],
            "baseline_file": "test_baseline.json",
            "exclude_patterns": ["__pycache__", ".venv", "venv", "node_modules", "migrations"],
            "fail_fast": False,
            "parallel": True,
            "max_workers": 4,
            "timeout": 300,
            "retry_failed": True,
            "retry_count": 2,
            "retry_delay": 1.0,
            "enable_ast_analysis": True,
            "enable_data_flow_analysis": True,
            "enable_ml_priority": False,
            "history_file": "test_history.pkl",
            "coverage_threshold": 70.0,
            "performance_baseline": {},
            "test_dependencies": {},
            "resource_limits": {
                "max_memory_mb": 1024,
                "max_cpu_percent": 80
            }
        }
        
        full_path = Path(self.base_path) / output_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "w", encoding="utf-8") as f:
            if HAS_YAML:
                yaml.dump(template, f, default_flow_style=False, allow_unicode=True)
            else:
                json.dump(template, f, indent=2, ensure_ascii=False)


class ASTAnalyzer:
    """AST分析器 - 提供深度代码分析能力"""
    
    def __init__(self):
        self.ast_cache: Dict[str, ast.AST] = {}
    
    def parse_file(self, file_path: str) -> Optional[ast.AST]:
        """解析Python文件生成AST"""
        if file_path in self.ast_cache:
            return self.ast_cache[file_path]
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            tree = ast.parse(content)
            self.ast_cache[file_path] = tree
            return tree
        except Exception as e:
            print(f"AST解析失败 {file_path}: {e}")
            return None
    
    def extract_definitions(self, tree: ast.AST) -> Dict[str, List[str]]:
        """提取所有定义（函数、类、变量）"""
        definitions = {
            "functions": [],
            "classes": [],
            "variables": [],
            "imports": [],
            "decorators": []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                definitions["functions"].append(node.name)
                if node.decorator_list:
                    for dec in node.decorator_list:
                        if isinstance(dec, ast.Name):
                            definitions["decorators"].append(dec.id)
            elif isinstance(node, ast.ClassDef):
                definitions["classes"].append(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        definitions["variables"].append(target.id)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        definitions["imports"].append(alias.name)
                else:
                    module = node.module or ""
                    for alias in node.names:
                        definitions["imports"].append(f"{module}.{alias.name}")
        
        return definitions
    
    def extract_calls(self, tree: ast.AST) -> List[str]:
        """提取所有函数调用"""
        calls = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.append(f"{node.func.value}.{node.func.attr}" if isinstance(node.func.value, ast.Name) else node.func.attr)
        
        return calls
    
    def extract_api_routes(self, tree: ast.AST) -> List[Dict[str, str]]:
        """提取API路由定义"""
        routes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call):
                        if isinstance(dec.func, ast.Attribute):
                            if dec.func.attr in ["get", "post", "put", "delete", "patch", "route"]:
                                route_info = {
                                    "method": dec.func.attr.upper(),
                                    "function": node.name
                                }
                                if dec.args:
                                    if isinstance(dec.args[0], ast.Constant):
                                        route_info["path"] = dec.args[0].value
                                routes.append(route_info)
        
        return routes
    
    def compare_asts(self, old_tree: ast.AST, new_tree: ast.AST) -> Dict[str, Any]:
        """比较两个AST，识别变更"""
        changes = {
            "added_functions": [],
            "removed_functions": [],
            "modified_functions": [],
            "added_classes": [],
            "removed_classes": [],
            "modified_classes": [],
            "signature_changes": []
        }
        
        old_defs = self.extract_definitions(old_tree)
        new_defs = self.extract_definitions(new_tree)
        
        old_funcs = set(old_defs["functions"])
        new_funcs = set(new_defs["functions"])
        
        changes["added_functions"] = list(new_funcs - old_funcs)
        changes["removed_functions"] = list(old_funcs - new_funcs)
        
        old_classes = set(old_defs["classes"])
        new_classes = set(new_defs["classes"])
        
        changes["added_classes"] = list(new_classes - old_classes)
        changes["removed_classes"] = list(old_classes - new_classes)
        
        return changes
    
    def calculate_complexity(self, tree: ast.AST) -> int:
        """计算代码复杂度（圈复杂度）"""
        complexity = 1
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, ast.comprehension):
                complexity += 1
                if node.ifs:
                    complexity += len(node.ifs)
        
        return complexity


class DataFlowAnalyzer:
    """数据流分析器 - 追踪数据在代码中的流动"""
    
    def __init__(self):
        self.flow_graph: Dict[str, Set[str]] = defaultdict(set)
        self.variable_definitions: Dict[str, List[str]] = defaultdict(list)
        self.variable_uses: Dict[str, List[str]] = defaultdict(list)
    
    def analyze_file(self, file_path: str, tree: ast.AST) -> Dict[str, Any]:
        """分析单个文件的数据流"""
        result = {
            "definitions": {},
            "uses": {},
            "flows": []
        }
        
        current_function = None
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                current_function = node.name
                result["definitions"][current_function] = []
                result["uses"][current_function] = []
            
            if current_function:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            result["definitions"][current_function].append(target.id)
                            self.variable_definitions[target.id].append(f"{file_path}:{current_function}")
                
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    result["uses"][current_function].append(node.id)
                    self.variable_uses[node.id].append(f"{file_path}:{current_function}")
        
        return result
    
    def trace_data_flow(self, variable: str) -> List[str]:
        """追踪变量的数据流"""
        flow = []
        
        definitions = self.variable_definitions.get(variable, [])
        uses = self.variable_uses.get(variable, [])
        
        for definition in definitions:
            flow.append(f"定义: {definition}")
        
        for use in uses:
            flow.append(f"使用: {use}")
        
        return flow
    
    def find_tainted_sources(self, tree: ast.AST) -> List[str]:
        """查找受污染的数据源（如用户输入）"""
        tainted_sources = []
        
        dangerous_functions = ["input", "request.get", "request.post", "request.json"]
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = f"{node.func.value}.{node.func.attr}" if isinstance(node.func.value, ast.Name) else node.func.attr
                
                if func_name in dangerous_functions:
                    tainted_sources.append(func_name)
        
        return tainted_sources


class ConfigChangeAnalyzer:
    """配置文件变更分析器"""
    
    SUPPORTED_CONFIG_TYPES = [".yaml", ".yml", ".json", ".toml", ".ini", ".env"]
    
    def __init__(self, base_path: str):
        self.base_path = base_path
    
    def analyze_config_change(self, file_path: str, old_content: str, new_content: str) -> Dict[str, Any]:
        """分析配置文件变更"""
        result = {
            "file_type": Path(file_path).suffix,
            "changes": [],
            "impact": "unknown"
        }
        
        suffix = Path(file_path).suffix.lower()
        
        if suffix in [".yaml", ".yml"]:
            result["changes"] = self._analyze_yaml_change(old_content, new_content)
        elif suffix == ".json":
            result["changes"] = self._analyze_json_change(old_content, new_content)
        elif suffix == ".env":
            result["changes"] = self._analyze_env_change(old_content, new_content)
        
        result["impact"] = self._assess_config_impact(result["changes"])
        
        return result
    
    def _analyze_yaml_change(self, old_content: str, new_content: str) -> List[Dict[str, Any]]:
        """分析YAML配置变更"""
        changes = []
        
        try:
            old_config = yaml.safe_load(old_content) if old_content else {}
            new_config = yaml.safe_load(new_content) if new_content else {}
            
            changes.extend(self._compare_dicts(old_config, new_config, ""))
        except Exception as e:
            changes.append({"error": str(e)})
        
        return changes
    
    def _analyze_json_change(self, old_content: str, new_content: str) -> List[Dict[str, Any]]:
        """分析JSON配置变更"""
        changes = []
        
        try:
            old_config = json.loads(old_content) if old_content else {}
            new_config = json.loads(new_content) if new_content else {}
            
            changes.extend(self._compare_dicts(old_config, new_config, ""))
        except Exception as e:
            changes.append({"error": str(e)})
        
        return changes
    
    def _analyze_env_change(self, old_content: str, new_content: str) -> List[Dict[str, Any]]:
        """分析环境变量配置变更"""
        changes = []
        
        old_vars = self._parse_env_file(old_content)
        new_vars = self._parse_env_file(new_content)
        
        all_keys = set(old_vars.keys()) | set(new_vars.keys())
        
        for key in all_keys:
            if key not in old_vars:
                changes.append({"key": key, "change": "added", "value": new_vars[key]})
            elif key not in new_vars:
                changes.append({"key": key, "change": "removed", "old_value": old_vars[key]})
            elif old_vars[key] != new_vars[key]:
                changes.append({"key": key, "change": "modified", "old_value": old_vars[key], "new_value": new_vars[key]})
        
        return changes
    
    def _parse_env_file(self, content: str) -> Dict[str, str]:
        """解析.env文件"""
        env_vars = {}
        
        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip().strip('"').strip("'")
        
        return env_vars
    
    def _compare_dicts(self, old: Dict, new: Dict, path: str) -> List[Dict[str, Any]]:
        """递归比较字典"""
        changes = []
        
        all_keys = set(old.keys()) | set(new.keys())
        
        for key in all_keys:
            current_path = f"{path}.{key}" if path else key
            
            if key not in old:
                changes.append({"path": current_path, "change": "added", "value": new[key]})
            elif key not in new:
                changes.append({"path": current_path, "change": "removed", "old_value": old[key]})
            elif old[key] != new[key]:
                if isinstance(old[key], dict) and isinstance(new[key], dict):
                    changes.extend(self._compare_dicts(old[key], new[key], current_path))
                else:
                    changes.append({"path": current_path, "change": "modified", "old_value": old[key], "new_value": new[key]})
        
        return changes
    
    def _assess_config_impact(self, changes: List[Dict[str, Any]]) -> str:
        """评估配置变更的影响级别"""
        critical_keywords = ["database", "secret", "api_key", "password", "token", "auth"]
        high_keywords = ["url", "host", "port", "timeout", "cache", "redis"]
        
        for change in changes:
            path = change.get("path", "").lower()
            
            for keyword in critical_keywords:
                if keyword in path:
                    return "critical"
            
            for keyword in high_keywords:
                if keyword in path:
                    return "high"
        
        return "medium"


class TestDependencyManager:
    """测试依赖管理器 - 管理测试之间的依赖关系"""
    
    def __init__(self):
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.execution_order: List[str] = []
        self.resource_locks: Dict[str, threading.Lock] = {}
    
    def add_dependency(self, test: str, depends_on: str):
        """添加测试依赖"""
        self.dependency_graph[test].add(depends_on)
    
    def resolve_execution_order(self, tests: List[str]) -> List[str]:
        """解析测试执行顺序（拓扑排序）"""
        in_degree = {test: 0 for test in tests}
        graph = defaultdict(set)
        
        for test in tests:
            for dep in self.dependency_graph.get(test, []):
                if dep in tests:
                    graph[dep].add(test)
                    in_degree[test] += 1
        
        queue_list = [test for test in tests if in_degree[test] == 0]
        result = []
        
        while queue_list:
            current = queue_list.pop(0)
            result.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue_list.append(neighbor)
        
        if len(result) != len(tests):
            print("警告: 检测到循环依赖")
            remaining = [t for t in tests if t not in result]
            result.extend(remaining)
        
        self.execution_order = result
        return result
    
    def get_independent_tests(self, tests: List[str]) -> List[str]:
        """获取可以并行执行的独立测试"""
        independent = []
        
        for test in tests:
            deps = self.dependency_graph.get(test, set())
            if not deps or not any(d in tests for d in deps):
                independent.append(test)
        
        return independent
    
    def acquire_resource(self, resource_name: str) -> bool:
        """获取资源锁"""
        if resource_name not in self.resource_locks:
            self.resource_locks[resource_name] = threading.Lock()
        
        return self.resource_locks[resource_name].acquire(blocking=False)
    
    def release_resource(self, resource_name: str):
        """释放资源锁"""
        if resource_name in self.resource_locks:
            try:
                self.resource_locks[resource_name].release()
            except RuntimeError:
                pass


class ChangeDetector:
    def __init__(self, base_path: str, config: RegressionTestConfig):
        self.base_path = base_path
        self.config = config
        self.changes: List[CodeChange] = []
        self.ast_analyzer = ASTAnalyzer() if config.enable_ast_analysis else None
        self.config_analyzer = ConfigChangeAnalyzer(base_path)

    def detect_from_git(self, since: str = "HEAD~1") -> List[CodeChange]:
        self.changes = []
        
        try:
            result = subprocess.run(
                ["git", "diff", "--name-status", since],
                cwd=self.base_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if not line:
                        continue
                    
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        status = parts[0]
                        file_path = parts[1]
                        
                        change_type = {
                            "A": ChangeType.ADDED,
                            "M": ChangeType.MODIFIED,
                            "D": ChangeType.DELETED,
                            "R": ChangeType.RENAMED
                        }.get(status[0], ChangeType.MODIFIED)
                        
                        if not self._should_skip_file(file_path):
                            change = CodeChange(
                                file_path=file_path,
                                change_type=change_type
                            )
                            
                            if change_type == ChangeType.MODIFIED:
                                change.diff = self._get_file_diff(file_path, since)
                                change.affected_functions = self._extract_changed_functions(change.diff)
                                
                                if self.ast_analyzer:
                                    change.ast_changes = self._analyze_ast_changes(file_path, since)
                            
                            if self._is_config_file(file_path):
                                change.old_content = self._get_old_content(file_path, since)
                                change.new_content = self._get_current_content(file_path)
                            
                            self.changes.append(change)
        
        except Exception as e:
            print(f"检测Git变更失败: {e}")
        
        return self.changes

    def detect_from_filesystem(self) -> List[CodeChange]:
        self.changes = []
        
        baseline_path = Path(self.base_path) / self.config.baseline_file
        if not baseline_path.exists():
            return self.changes
        
        try:
            with open(baseline_path, "r", encoding="utf-8") as f:
                baseline = json.load(f)
            
            for source_dir in self.config.source_dirs:
                source_path = Path(self.base_path) / source_dir
                if source_path.exists():
                    self._compare_with_baseline(source_path, baseline)
        
        except Exception as e:
            print(f"检测文件系统变更失败: {e}")
        
        return self.changes

    def _should_skip_file(self, file_path: str) -> bool:
        return any(pattern in file_path for pattern in self.config.exclude_patterns)
    
    def _is_config_file(self, file_path: str) -> bool:
        suffix = Path(file_path).suffix.lower()
        return suffix in ConfigChangeAnalyzer.SUPPORTED_CONFIG_TYPES

    def _get_file_diff(self, file_path: str, since: str) -> str:
        try:
            result = subprocess.run(
                ["git", "diff", since, "--", file_path],
                cwd=self.base_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout if result.returncode == 0 else ""
        except Exception:
            return ""

    def _extract_changed_functions(self, diff: str) -> List[str]:
        functions = []
        
        patterns = [
            r'^@@.*def\s+(\w+)',
            r'^\+.*def\s+(\w+)',
            r'^-.*def\s+(\w+)',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, diff, re.MULTILINE):
                func_name = match.group(1)
                if not func_name.startswith("_") or func_name.startswith("__"):
                    functions.append(func_name)
        
        return list(set(functions))
    
    def _analyze_ast_changes(self, file_path: str, since: str) -> Dict[str, Any]:
        """使用AST分析代码变更"""
        ast_changes = {}
        
        try:
            old_content = self._get_old_content(file_path, since)
            new_content = self._get_current_content(file_path)
            
            if old_content and new_content:
                old_tree = ast.parse(old_content)
                new_tree = ast.parse(new_content)
                
                ast_changes = self.ast_analyzer.compare_asts(old_tree, new_tree)
                
                old_complexity = self.ast_analyzer.calculate_complexity(old_tree)
                new_complexity = self.ast_analyzer.calculate_complexity(new_tree)
                ast_changes["complexity_delta"] = new_complexity - old_complexity
        except Exception as e:
            print(f"AST分析失败: {e}")
        
        return ast_changes
    
    def _get_old_content(self, file_path: str, since: str) -> Optional[str]:
        """获取文件的旧版本内容"""
        try:
            result = subprocess.run(
                ["git", "show", f"{since}:{file_path}"],
                cwd=self.base_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout if result.returncode == 0 else None
        except Exception:
            return None
    
    def _get_current_content(self, file_path: str) -> Optional[str]:
        """获取文件的当前内容"""
        try:
            full_path = Path(self.base_path) / file_path
            if full_path.exists():
                with open(full_path, "r", encoding="utf-8") as f:
                    return f.read()
        except Exception:
            pass
        return None

    def _compare_with_baseline(self, directory: Path, baseline: Dict):
        for py_file in directory.rglob("*.py"):
            if self._should_skip_file(str(py_file)):
                continue
            
            relative_path = str(py_file.relative_to(self.base_path))
            current_mtime = py_file.stat().st_mtime
            
            if relative_path in baseline:
                baseline_mtime = baseline[relative_path].get("mtime", 0)
                if current_mtime > baseline_mtime:
                    self.changes.append(CodeChange(
                        file_path=relative_path,
                        change_type=ChangeType.MODIFIED
                    ))
            else:
                self.changes.append(CodeChange(
                    file_path=relative_path,
                    change_type=ChangeType.ADDED
                ))


class ImpactAnalyzer:
    def __init__(self, base_path: str, config: RegressionTestConfig):
        self.base_path = base_path
        self.config = config
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.class_hierarchy: Dict[str, Set[str]] = defaultdict(set)
        self.function_call_graph: Dict[str, Set[str]] = defaultdict(set)
        self.api_endpoints: Dict[str, List[str]] = defaultdict(list)
        self.ast_analyzer = ASTAnalyzer() if config.enable_ast_analysis else None
        self.data_flow_analyzer = DataFlowAnalyzer() if config.enable_data_flow_analysis else None
        self.config_analyzer = ConfigChangeAnalyzer(base_path)

    def build_dependency_graph(self, source_dirs: List[str]) -> Dict[str, Set[str]]:
        for source_dir in source_dirs:
            source_path = Path(self.base_path) / source_dir
            if source_path.exists():
                self._analyze_imports(source_path)
                self._analyze_class_hierarchy(source_path)
                self._analyze_function_calls(source_path)
                self._analyze_api_endpoints(source_path)
        
        for file_path, deps in self.dependency_graph.items():
            for dep in deps:
                self.reverse_dependencies[dep].add(file_path)
        
        return dict(self.dependency_graph)

    def _analyze_imports(self, directory: Path):
        for py_file in directory.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                relative_path = str(py_file.relative_to(self.base_path))
                
                import_patterns = [
                    r'^from\s+([\w.]+)\s+import',
                    r'^import\s+([\w.]+)',
                ]
                
                for pattern in import_patterns:
                    for match in re.finditer(pattern, content, re.MULTILINE):
                        module = match.group(1)
                        self.dependency_graph[relative_path].add(module)
            
            except Exception as e:
                print(f"分析导入失败 {py_file}: {e}")

    def _analyze_class_hierarchy(self, directory: Path):
        for py_file in directory.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                relative_path = str(py_file.relative_to(self.base_path))
                
                class_pattern = r'class\s+(\w+)\s*\(([^)]+)\)'
                for match in re.finditer(class_pattern, content):
                    class_name = match.group(1)
                    parent_classes = match.group(2).split(',')
                    for parent in parent_classes:
                        parent = parent.strip()
                        if parent and parent not in ['object', 'ABC']:
                            self.class_hierarchy[f"{relative_path}:{class_name}"].add(parent)
            
            except Exception as e:
                print(f"分析类层次失败 {py_file}: {e}")

    def _analyze_function_calls(self, directory: Path):
        for py_file in directory.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                relative_path = str(py_file.relative_to(self.base_path))
                
                func_def_pattern = r'def\s+(\w+)\s*\('
                func_call_pattern = r'(\w+)\s*\('
                
                defined_funcs = set()
                for match in re.finditer(func_def_pattern, content):
                    defined_funcs.add(match.group(1))
                
                current_func = None
                for line in content.split('\n'):
                    func_match = re.match(r'^\s*def\s+(\w+)', line)
                    if func_match:
                        current_func = func_match.group(1)
                    
                    if current_func:
                        for call_match in re.finditer(func_call_pattern, line):
                            called_func = call_match.group(1)
                            if called_func not in defined_funcs and not called_func.startswith('_'):
                                key = f"{relative_path}:{current_func}"
                                self.function_call_graph[key].add(called_func)
            
            except Exception as e:
                print(f"分析函数调用失败 {py_file}: {e}")

    def _analyze_api_endpoints(self, directory: Path):
        for py_file in directory.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                relative_path = str(py_file.relative_to(self.base_path))
                
                route_patterns = [
                    r'@app\.route\s*\(["\']([^"\']+)["\']',
                    r'@router\.(get|post|put|delete|patch)\s*\(["\']([^"\']+)["\']',
                    r'@api_view\s*\(["\']([^"\']+)["\']',
                    r'path\s*\(["\']([^"\']+)["\']',
                ]
                
                for pattern in route_patterns:
                    for match in re.finditer(pattern, content):
                        if len(match.groups()) > 1:
                            endpoint = f"{match.group(1)} {match.group(2)}"
                        else:
                            endpoint = match.group(1)
                        self.api_endpoints[relative_path].append(endpoint)
            
            except Exception as e:
                print(f"分析API端点失败 {py_file}: {e}")

    def _should_skip_file(self, file_path: Path) -> bool:
        return any(pattern in str(file_path) for pattern in self.config.exclude_patterns)

    def analyze_impact(self, changes: List[CodeChange]) -> List[ImpactAnalysis]:
        analyses = []
        
        for change in changes:
            affected_files = self._get_affected_files(change.file_path)
            affected_tests = self._get_affected_tests(change.file_path, affected_files)
            affected_apis = self._get_affected_apis(change.file_path)
            transitive_impact = self._get_transitive_impact_dict(change.file_path)
            data_flow_paths = self._analyze_data_flow_paths(change.file_path) if self.data_flow_analyzer else []
            db_impact = self._analyze_db_impact(change)
            
            impact_level = self._determine_impact_level(change, affected_files, affected_tests)
            risk_score = self._calculate_risk_score(change, affected_files, affected_tests, affected_apis)
            
            analysis = ImpactAnalysis(
                changed_file=change.file_path,
                affected_files=list(affected_files),
                affected_tests=list(affected_tests),
                impact_level=impact_level,
                risk_score=risk_score,
                reasoning=self._generate_reasoning(change, affected_files, affected_tests, affected_apis),
                transitive_impact=transitive_impact,
                data_flow_paths=data_flow_paths,
                api_impact=affected_apis,
                db_impact=db_impact
            )
            analyses.append(analysis)
        
        return analyses

    def _get_affected_files(self, changed_file: str) -> Set[str]:
        affected = set()
        
        for file_path, deps in self.dependency_graph.items():
            if changed_file.replace(".py", "").replace("/", ".") in deps:
                affected.add(file_path)
        
        if changed_file in self.reverse_dependencies:
            affected.update(self.reverse_dependencies[changed_file])
        
        class_name = None
        for key in self.class_hierarchy:
            if key.startswith(changed_file):
                parts = key.split(":")
                if len(parts) > 1:
                    class_name = parts[1]
                    break
        
        if class_name:
            for key, parents in self.class_hierarchy.items():
                if class_name in parents:
                    file_part = key.split(":")[0]
                    affected.add(file_part)
        
        return affected

    def _get_affected_tests(self, changed_file: str, affected_files: Set[str]) -> List[str]:
        tests = []
        
        test_patterns = [
            changed_file.replace("app/", "tests/").replace(".py", "_test.py"),
            changed_file.replace("app/", "tests/test_").replace(".py", ".py"),
            changed_file.replace(".py", "_test.py"),
        ]
        
        for pattern in test_patterns:
            test_path = Path(self.base_path) / pattern
            if test_path.exists():
                tests.append(pattern)
        
        for affected_file in affected_files:
            test_patterns = [
                affected_file.replace("app/", "tests/").replace(".py", "_test.py"),
                affected_file.replace("app/", "tests/test_").replace(".py", ".py"),
            ]
            for pattern in test_patterns:
                test_path = Path(self.base_path) / pattern
                if test_path.exists() and pattern not in tests:
                    tests.append(pattern)
        
        return tests

    def _get_affected_apis(self, changed_file: str) -> List[str]:
        return self.api_endpoints.get(changed_file, [])
    
    def _get_transitive_impact_dict(self, file_path: str, depth: int = 3) -> Dict[str, List[str]]:
        """获取传递性影响字典"""
        impact = {}
        visited = set()
        
        def _traverse(current: str, level: int):
            if level > depth or current in visited:
                return
            visited.add(current)
            
            dependents = self.reverse_dependencies.get(current, set())
            if dependents:
                impact[f"level_{level}"] = list(dependents)
            
            for dep in dependents:
                _traverse(dep, level + 1)
        
        _traverse(file_path, 1)
        return impact
    
    def _analyze_data_flow_paths(self, file_path: str) -> List[List[str]]:
        """分析数据流路径"""
        paths = []
        
        if self.data_flow_analyzer:
            for var, definitions in self.data_flow_analyzer.variable_definitions.items():
                for definition in definitions:
                    if file_path in definition:
                        flow = self.data_flow_analyzer.trace_data_flow(var)
                        if flow:
                            paths.append(flow)
        
        return paths[:10]
    
    def _analyze_db_impact(self, change: CodeChange) -> List[str]:
        """分析数据库影响"""
        db_impacts = []
        
        db_patterns = [
            r'models\.(\w+)',
            r'Model',
            r'database',
            r'migration',
            r'schema',
            r'table',
            r'column'
        ]
        
        if change.diff:
            for pattern in db_patterns:
                if re.search(pattern, change.diff, re.IGNORECASE):
                    db_impacts.append(f"可能影响数据库: {pattern}")
        
        return db_impacts

    def _determine_impact_level(
        self,
        change: CodeChange,
        affected_files: Set[str],
        affected_tests: List[str]
    ) -> ImpactLevel:
        if change.change_type == ChangeType.DELETED:
            return ImpactLevel.CRITICAL
        
        if change.ast_changes:
            if change.ast_changes.get("removed_functions"):
                return ImpactLevel.CRITICAL
            if change.ast_changes.get("removed_classes"):
                return ImpactLevel.CRITICAL
        
        if len(affected_files) > 10:
            return ImpactLevel.HIGH
        
        if len(affected_files) > 5:
            return ImpactLevel.MEDIUM
        
        if len(affected_tests) > 5:
            return ImpactLevel.HIGH
        
        if len(affected_tests) > 2:
            return ImpactLevel.MEDIUM
        
        if change.affected_functions:
            for func in change.affected_functions:
                for key in self.function_call_graph:
                    if func in self.function_call_graph[key]:
                        return ImpactLevel.HIGH
        
        if change.affected_functions:
            return ImpactLevel.MEDIUM
        
        return ImpactLevel.LOW

    def _calculate_risk_score(
        self,
        change: CodeChange,
        affected_files: Set[str],
        affected_tests: List[str],
        affected_apis: List[str]
    ) -> float:
        score = 0.0
        
        if change.change_type == ChangeType.DELETED:
            score += 30
        elif change.change_type == ChangeType.MODIFIED:
            score += 10
        elif change.change_type == ChangeType.ADDED:
            score += 5
        
        score += len(affected_files) * 2
        score += len(affected_tests) * 3
        score += len(change.affected_functions) * 5
        score += len(affected_apis) * 8
        
        if change.ast_changes:
            score += len(change.ast_changes.get("removed_functions", [])) * 10
            score += len(change.ast_changes.get("removed_classes", [])) * 15
            score += abs(change.ast_changes.get("complexity_delta", 0)) * 2
        
        for func in change.affected_functions:
            for key, calls in self.function_call_graph.items():
                if func in calls:
                    score += 3
        
        return min(score, 100)

    def _generate_reasoning(
        self,
        change: CodeChange,
        affected_files: Set[str],
        affected_tests: List[str],
        affected_apis: List[str]
    ) -> str:
        reasons = []
        
        if change.change_type == ChangeType.DELETED:
            reasons.append("文件被删除")
        elif change.change_type == ChangeType.MODIFIED:
            reasons.append("文件被修改")
        elif change.change_type == ChangeType.ADDED:
            reasons.append("新增文件")
        
        if affected_files:
            reasons.append(f"影响 {len(affected_files)} 个相关文件")
        
        if affected_tests:
            reasons.append(f"需要运行 {len(affected_tests)} 个测试")
        
        if change.affected_functions:
            reasons.append(f"修改了 {len(change.affected_functions)} 个函数")
        
        if affected_apis:
            reasons.append(f"影响 {len(affected_apis)} 个API端点")
        
        if change.ast_changes:
            if change.ast_changes.get("removed_functions"):
                reasons.append(f"删除了 {len(change.ast_changes['removed_functions'])} 个函数")
            if change.ast_changes.get("removed_classes"):
                reasons.append(f"删除了 {len(change.ast_changes['removed_classes'])} 个类")
        
        return "; ".join(reasons)

    def get_transitive_impact(self, file_path: str, depth: int = 3) -> Dict[str, Any]:
        visited = set()
        impact_chain = []
        
        def _traverse(current: str, level: int):
            if level > depth or current in visited:
                return
            visited.add(current)
            
            dependents = self.reverse_dependencies.get(current, set())
            impact_chain.append({
                "file": current,
                "level": level,
                "dependents": list(dependents)
            })
            
            for dep in dependents:
                _traverse(dep, level + 1)
        
        _traverse(file_path, 1)
        
        return {
            "source_file": file_path,
            "max_depth": depth,
            "total_affected": len(visited),
            "impact_chain": impact_chain
        }


class TestSelector:
    def __init__(self, base_path: str, config: RegressionTestConfig):
        self.base_path = base_path
        self.config = config
        self.selected_tests: Set[str] = set()
        self.test_priorities: Dict[str, float] = {}
        self.test_coverage_map: Dict[str, Set[str]] = defaultdict(set)
        self.test_history: Dict[str, Dict[str, Any]] = {}
        self.test_metrics: Dict[str, TestMetrics] = {}
        self.test_dependency_manager = TestDependencyManager()
        self.ml_model = None

    def select_tests_for_changes(
        self,
        impact_analyses: List[ImpactAnalysis]
    ) -> List[str]:
        self.selected_tests = set()
        self.test_priorities = {}
        
        for analysis in impact_analyses:
            for test in analysis.affected_tests:
                self.selected_tests.add(test)
                self._update_test_priority(test, analysis)
        
        for analysis in impact_analyses:
            if analysis.impact_level in [ImpactLevel.CRITICAL, ImpactLevel.HIGH]:
                self._add_related_tests(analysis.changed_file)
        
        return self._get_prioritized_tests()

    def _update_test_priority(self, test: str, analysis: ImpactAnalysis):
        if test not in self.test_priorities:
            self.test_priorities[test] = 0.0
        
        priority_boost = {
            ImpactLevel.CRITICAL: 50.0,
            ImpactLevel.HIGH: 30.0,
            ImpactLevel.MEDIUM: 15.0,
            ImpactLevel.LOW: 5.0,
            ImpactLevel.MINIMAL: 1.0
        }
        
        self.test_priorities[test] += priority_boost.get(analysis.impact_level, 5.0)
        self.test_priorities[test] += analysis.risk_score * 0.5
        
        if test in self.test_history:
            history = self.test_history[test]
            if history.get("last_failed"):
                self.test_priorities[test] += 20.0
            if history.get("flaky"):
                self.test_priorities[test] += 10.0
        
        if test in self.test_metrics:
            metrics = self.test_metrics[test]
            if metrics.flakiness_score > 0.3:
                self.test_priorities[test] += 15.0
            if metrics.success_rate < 0.8:
                self.test_priorities[test] += 10.0

    def _add_related_tests(self, changed_file: str):
        module_name = changed_file.replace(".py", "").replace("/", ".")
        
        for test_dir in self.config.test_dirs:
            test_path = Path(self.base_path) / test_dir
            if test_path.exists():
                for test_file in test_path.rglob("*.py"):
                    if self._is_test_related(test_file, module_name):
                        relative = str(test_file.relative_to(self.base_path))
                        self.selected_tests.add(relative)
                        if relative not in self.test_priorities:
                            self.test_priorities[relative] = 10.0

    def _is_test_related(self, test_file: Path, module_name: str) -> bool:
        try:
            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()
            return module_name.replace(".", "/") in content or module_name in content
        except Exception:
            return False

    def _get_prioritized_tests(self) -> List[str]:
        sorted_tests = sorted(
            self.selected_tests,
            key=lambda t: self.test_priorities.get(t, 0),
            reverse=True
        )
        return sorted_tests

    def select_all_tests(self) -> List[str]:
        all_tests = []
        
        for test_dir in self.config.test_dirs:
            test_path = Path(self.base_path) / test_dir
            if test_path.exists():
                for test_file in test_path.rglob("*.py"):
                    if test_file.name.startswith("test_") or test_file.name.endswith("_test.py"):
                        all_tests.append(str(test_file.relative_to(self.base_path)))
        
        return sorted(all_tests)

    def build_test_coverage_map(self, source_dirs: List[str]):
        for source_dir in source_dirs:
            source_path = Path(self.base_path) / source_dir
            if source_path.exists():
                self._analyze_test_coverage(source_path)

    def _analyze_test_coverage(self, directory: Path):
        for test_dir in self.config.test_dirs:
            test_path = Path(self.base_path) / test_dir
            if not test_path.exists():
                continue
            
            for test_file in test_path.rglob("*.py"):
                if not (test_file.name.startswith("test_") or test_file.name.endswith("_test.py")):
                    continue
                
                try:
                    with open(test_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    relative_test = str(test_file.relative_to(self.base_path))
                    
                    import_pattern = r'^from\s+([\w.]+)\s+import|^import\s+([\w.]+)'
                    for match in re.finditer(import_pattern, content, re.MULTILINE):
                        module = match.group(1) or match.group(2)
                        if module:
                            self.test_coverage_map[relative_test].add(module)
                
                except Exception:
                    pass

    def select_by_coverage(self, changed_files: List[str]) -> List[str]:
        selected = set()
        
        for changed_file in changed_files:
            module_name = changed_file.replace(".py", "").replace("/", ".")
            
            for test_file, covered_modules in self.test_coverage_map.items():
                if any(module_name in m for m in covered_modules):
                    selected.add(test_file)
        
        return list(selected)

    def select_by_history(self, max_tests: int = 20) -> List[str]:
        historical_failures = []
        
        for test, history in self.test_history.items():
            if history.get("failure_rate", 0) > 0.1:
                historical_failures.append((test, history["failure_rate"]))
        
        historical_failures.sort(key=lambda x: x[1], reverse=True)
        return [t[0] for t in historical_failures[:max_tests]]

    def select_by_risk(self, impact_analyses: List[ImpactAnalysis], max_risk_score: float = 50.0) -> List[str]:
        high_risk_tests = set()
        
        for analysis in impact_analyses:
            if analysis.risk_score >= max_risk_score:
                high_risk_tests.update(analysis.affected_tests)
        
        return list(high_risk_tests)
    
    def select_by_ml_priority(self, impact_analyses: List[ImpactAnalysis]) -> List[str]:
        """使用机器学习模型进行测试优先级排序"""
        if not self.config.enable_ml_priority:
            return self.select_tests_for_changes(impact_analyses)
        
        features = []
        test_names = []
        
        for analysis in impact_analyses:
            for test in analysis.affected_tests:
                test_features = self._extract_test_features(test, analysis)
                features.append(test_features)
                test_names.append(test)
        
        if self.ml_model and features:
            try:
                priorities = self.ml_model.predict(features)
                test_priority_pairs = list(zip(test_names, priorities))
                test_priority_pairs.sort(key=lambda x: x[1], reverse=True)
                return [t[0] for t in test_priority_pairs]
            except Exception as e:
                print(f"ML优先级排序失败: {e}")
        
        return self.select_tests_for_changes(impact_analyses)
    
    def _extract_test_features(self, test: str, analysis: ImpactAnalysis) -> List[float]:
        """提取测试特征用于机器学习"""
        features = [
            analysis.risk_score / 100.0,
            len(analysis.affected_files) / 20.0,
            len(analysis.affected_tests) / 10.0,
            1.0 if analysis.impact_level == ImpactLevel.CRITICAL else 0.0,
            1.0 if analysis.impact_level == ImpactLevel.HIGH else 0.0,
        ]
        
        if test in self.test_history:
            history = self.test_history[test]
            features.extend([
                history.get("failure_rate", 0),
                1.0 if history.get("last_failed") else 0.0,
                1.0 if history.get("flaky") else 0.0,
            ])
        else:
            features.extend([0.0, 0.0, 0.0])
        
        if test in self.test_metrics:
            metrics = self.test_metrics[test]
            features.extend([
                metrics.flakiness_score,
                metrics.success_rate,
                metrics.avg_duration / 10.0,
            ])
        else:
            features.extend([0.0, 1.0, 0.5])
        
        return features

    def smart_selection(
        self,
        impact_analyses: List[ImpactAnalysis],
        strategy: str = "balanced"
    ) -> Dict[str, Any]:
        strategies = {
            "fast": self._fast_selection,
            "thorough": self._thorough_selection,
            "balanced": self._balanced_selection,
            "risk_based": self._risk_based_selection,
            "ml_based": self._ml_based_selection
        }
        
        selector = strategies.get(strategy, self._balanced_selection)
        selected = selector(impact_analyses)
        
        if self.config.test_dependencies:
            selected = self.test_dependency_manager.resolve_execution_order(selected)
        
        return {
            "strategy": strategy,
            "selected_tests": selected,
            "total_selected": len(selected),
            "estimated_duration": self._estimate_duration(selected),
            "coverage_estimate": self._estimate_coverage(selected, impact_analyses)
        }

    def _fast_selection(self, impact_analyses: List[ImpactAnalysis]) -> List[str]:
        tests = set()
        for analysis in impact_analyses:
            if analysis.impact_level in [ImpactLevel.CRITICAL, ImpactLevel.HIGH]:
                tests.update(analysis.affected_tests[:3])
        return list(tests)[:10]

    def _thorough_selection(self, impact_analyses: List[ImpactAnalysis]) -> List[str]:
        return self.select_tests_for_changes(impact_analyses)

    def _balanced_selection(self, impact_analyses: List[ImpactAnalysis]) -> List[str]:
        tests = set()
        for analysis in impact_analyses:
            if analysis.impact_level == ImpactLevel.CRITICAL:
                tests.update(analysis.affected_tests)
            elif analysis.impact_level == ImpactLevel.HIGH:
                tests.update(analysis.affected_tests[:5])
            elif analysis.impact_level == ImpactLevel.MEDIUM:
                tests.update(analysis.affected_tests[:2])
        return list(tests)
    
    def _ml_based_selection(self, impact_analyses: List[ImpactAnalysis]) -> List[str]:
        return self.select_by_ml_priority(impact_analyses)

    def _risk_based_selection(self, impact_analyses: List[ImpactAnalysis]) -> List[str]:
        tests = set()
        for analysis in impact_analyses:
            if analysis.risk_score >= 30:
                tests.update(analysis.affected_tests)
        return list(tests)

    def _estimate_duration(self, tests: List[str]) -> float:
        base_duration = 0.5
        avg_test_duration = self._get_avg_test_duration()
        
        if self.config.parallel and self.config.max_workers > 1:
            return (len(tests) / self.config.max_workers) * avg_test_duration + base_duration
        else:
            return len(tests) * avg_test_duration + base_duration

    def _get_avg_test_duration(self) -> float:
        if not self.test_history:
            return 2.0
        durations = [h.get("avg_duration", 2.0) for h in self.test_history.values()]
        return sum(durations) / len(durations) if durations else 2.0

    def _estimate_coverage(self, tests: List[str], analyses: List[ImpactAnalysis]) -> float:
        if not analyses:
            return 0.0
        
        all_affected = set()
        for analysis in analyses:
            all_affected.update(analysis.affected_tests)
        
        if not all_affected:
            return 0.0
        
        covered = len(set(tests) & all_affected)
        return round(covered / len(all_affected) * 100, 2)

    def update_test_history(self, test_name: str, result: Dict[str, Any]):
        if test_name not in self.test_history:
            self.test_history[test_name] = {
                "runs": 0,
                "failures": 0,
                "total_duration": 0.0,
                "last_failed": False,
                "flaky": False
            }
        
        history = self.test_history[test_name]
        history["runs"] += 1
        history["total_duration"] += result.get("duration", 0)
        history["avg_duration"] = history["total_duration"] / history["runs"]
        
        if result.get("status") == "failed":
            history["failures"] += 1
            history["last_failed"] = True
        else:
            history["last_failed"] = False
        
        history["failure_rate"] = history["failures"] / history["runs"]
        
        if history["runs"] >= 3:
            history["flaky"] = 0.2 < history["failure_rate"] < 0.8
    
    def load_history(self):
        """加载测试历史数据"""
        history_path = Path(self.base_path) / self.config.history_file
        if history_path.exists():
            try:
                with open(history_path, "rb") as f:
                    data = pickle.load(f)
                    self.test_history = data.get("test_history", {})
                    self.test_metrics = data.get("test_metrics", {})
            except Exception as e:
                print(f"加载测试历史失败: {e}")
    
    def save_history(self):
        """保存测试历史数据"""
        history_path = Path(self.base_path) / self.config.history_file
        try:
            with open(history_path, "wb") as f:
                pickle.dump({
                    "test_history": self.test_history,
                    "test_metrics": self.test_metrics
                }, f)
        except Exception as e:
            print(f"保存测试历史失败: {e}")


class RegressionTestRunner:
    """增强的测试运行器 - 支持并行执行和智能重试"""
    
    def __init__(self, base_path: str, config: RegressionTestConfig):
        self.base_path = base_path
        self.config = config
        self.results: List[RegressionTestResult] = []
        self.test_queue: queue.Queue = queue.Queue()
        self.result_queue: queue.Queue = queue.Queue()
        self.lock = threading.Lock()
    
    def run_tests(self, test_files: List[str]) -> RegressionTestSuite:
        start_time = time.time()
        self.results = []
        
        if not test_files:
            return RegressionTestSuite(
                suite_name="regression_tests",
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=0,
                duration=0
            )
        
        print(f"\n运行 {len(test_files)} 个测试文件...")
        
        if self.config.parallel and self.config.max_workers > 1:
            suite = self._run_tests_parallel(test_files)
        else:
            suite = self._run_tests_sequential(test_files)
        
        suite.duration = time.time() - start_time
        return suite
    
    def _run_tests_sequential(self, test_files: List[str]) -> RegressionTestSuite:
        """顺序执行测试"""
        for test_file in test_files:
            result = self._run_single_test_with_retry(test_file)
            self.results.append(result)
            
            if result.status == TestStatus.FAILED and self.config.fail_fast:
                break
        
        return self._build_suite()
    
    def _run_tests_parallel(self, test_files: List[str]) -> RegressionTestSuite:
        """并行执行测试"""
        print(f"使用 {self.config.max_workers} 个并行工作线程")
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            future_to_test = {
                executor.submit(self._run_single_test_with_retry, test_file): test_file
                for test_file in test_files
            }
            
            for future in as_completed(future_to_test):
                test_file = future_to_test[future]
                try:
                    result = future.result()
                    with self.lock:
                        self.results.append(result)
                        
                        if result.status == TestStatus.FAILED and self.config.fail_fast:
                            executor.shutdown(wait=False, cancel_futures=True)
                            break
                except Exception as e:
                    with self.lock:
                        self.results.append(RegressionTestResult(
                            test_name=test_file,
                            test_file=test_file,
                            status=TestStatus.ERROR,
                            duration=0,
                            error_message=str(e)
                        ))
        
        return self._build_suite()
    
    def _build_suite(self) -> RegressionTestSuite:
        """构建测试套件结果"""
        retry_stats = {
            "total_retries": sum(r.retry_count for r in self.results),
            "tests_retried": sum(1 for r in self.results if r.retry_count > 0),
            "retries_passed": sum(1 for r in self.results if r.retry_count > 0 and r.status == TestStatus.PASSED)
        }
        
        return RegressionTestSuite(
            suite_name="regression_tests",
            total_tests=len(self.results),
            passed=sum(1 for r in self.results if r.status == TestStatus.PASSED),
            failed=sum(1 for r in self.results if r.status == TestStatus.FAILED),
            skipped=sum(1 for r in self.results if r.status == TestStatus.SKIPPED),
            errors=sum(1 for r in self.results if r.status == TestStatus.ERROR),
            duration=0,
            results=self.results,
            parallel_workers=self.config.max_workers if self.config.parallel else 1,
            retry_stats=retry_stats
        )
    
    def _run_single_test_with_retry(self, test_file: str) -> RegressionTestResult:
        """运行单个测试，支持重试"""
        result = self._run_single_test(test_file)
        
        if result.status == TestStatus.FAILED and self.config.retry_failed:
            retry_count = 0
            retry_history = []
            
            while retry_count < self.config.retry_count:
                retry_count += 1
                print(f"  重试 {test_file} ({retry_count}/{self.config.retry_count})...")
                
                time.sleep(self.config.retry_delay)
                
                retry_result = self._run_single_test(test_file)
                retry_result.retry_count = retry_count
                
                retry_history.append({
                    "attempt": retry_count,
                    "status": retry_result.status.value,
                    "duration": retry_result.duration,
                    "error": retry_result.error_message
                })
                
                if retry_result.status == TestStatus.PASSED:
                    retry_result.retry_history = retry_history
                    return retry_result
            
            result.retry_count = retry_count
            result.retry_history = retry_history
        
        return result

    def _run_single_test(self, test_file: str) -> RegressionTestResult:
        start_time = time.time()
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
                cwd=self.base_path,
                capture_output=True,
                text=True,
                timeout=self.config.timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                status = TestStatus.PASSED
                error = None
            else:
                status = TestStatus.FAILED
                error = self._extract_error(result.stdout + result.stderr)
            
            return RegressionTestResult(
                test_name=test_file,
                test_file=test_file,
                status=status,
                duration=duration,
                error_message=error,
                stack_trace=result.stdout[-2000:] if result.stdout else None
            )
        
        except subprocess.TimeoutExpired:
            return RegressionTestResult(
                test_name=test_file,
                test_file=test_file,
                status=TestStatus.ERROR,
                duration=self.config.timeout,
                error_message="测试超时"
            )
        
        except Exception as e:
            return RegressionTestResult(
                test_name=test_file,
                test_file=test_file,
                status=TestStatus.ERROR,
                duration=time.time() - start_time,
                error_message=str(e)
            )

    def _extract_error(self, output: str) -> str:
        error_lines = []
        in_error = False
        
        for line in output.split("\n"):
            if "FAILED" in line or "ERROR" in line:
                in_error = True
            if in_error:
                error_lines.append(line)
                if len(error_lines) > 10:
                    break
        
        return "\n".join(error_lines[:10]) if error_lines else "Unknown error"


class TrendAnalyzer:
    """趋势分析器 - 分析测试结果的历史趋势"""
    
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.trend_data: List[TrendData] = []
    
    def load_trend_data(self, trend_file: str = "test_trend.json") -> List[TrendData]:
        """加载历史趋势数据"""
        trend_path = Path(self.base_path) / trend_file
        if trend_path.exists():
            try:
                with open(trend_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.trend_data = [TrendData(**item) for item in data]
            except Exception as e:
                print(f"加载趋势数据失败: {e}")
        
        return self.trend_data
    
    def save_trend_data(self, trend_file: str = "test_trend.json"):
        """保存趋势数据"""
        trend_path = Path(self.base_path) / trend_file
        try:
            with open(trend_path, "w", encoding="utf-8") as f:
                json.dump([asdict(t) for t in self.trend_data], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存趋势数据失败: {e}")
    
    def add_trend_point(self, suite: RegressionTestSuite, avg_risk_score: float = 0):
        """添加趋势数据点"""
        pass_rate = round(suite.passed / max(suite.total_tests, 1) * 100, 2)
        
        trend = TrendData(
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_tests=suite.total_tests,
            passed=suite.passed,
            failed=suite.failed,
            duration=suite.duration,
            pass_rate=pass_rate,
            avg_risk_score=avg_risk_score
        )
        
        self.trend_data.append(trend)
        
        if len(self.trend_data) > 100:
            self.trend_data = self.trend_data[-100:]
    
    def analyze_trends(self) -> Dict[str, Any]:
        """分析趋势"""
        if len(self.trend_data) < 2:
            return {"message": "数据不足，无法分析趋势"}
        
        recent = self.trend_data[-10:] if len(self.trend_data) >= 10 else self.trend_data
        
        pass_rates = [t.pass_rate for t in recent]
        durations = [t.duration for t in recent]
        
        avg_pass_rate = sum(pass_rates) / len(pass_rates)
        avg_duration = sum(durations) / len(durations)
        
        trend_direction = "stable"
        if len(pass_rates) >= 3:
            recent_avg = sum(pass_rates[-3:]) / 3
            older_avg = sum(pass_rates[:3]) / 3
            if recent_avg > older_avg + 5:
                trend_direction = "improving"
            elif recent_avg < older_avg - 5:
                trend_direction = "declining"
        
        return {
            "avg_pass_rate": round(avg_pass_rate, 2),
            "avg_duration": round(avg_duration, 2),
            "trend_direction": trend_direction,
            "total_data_points": len(self.trend_data),
            "recent_data_points": len(recent)
        }
    
    def get_pass_rate_trend(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取通过率趋势"""
        cutoff = datetime.now() - timedelta(days=days)
        
        trend = []
        for t in self.trend_data:
            try:
                date = datetime.strptime(t.date, "%Y-%m-%d %H:%M:%S")
                if date >= cutoff:
                    trend.append({
                        "date": t.date,
                        "pass_rate": t.pass_rate
                    })
            except Exception:
                pass
        
        return trend


class HTMLReportGenerator:
    def __init__(self, base_path: str):
        self.base_path = base_path

    def generate(
        self,
        suite: RegressionTestSuite,
        impact_analyses: List[ImpactAnalysis],
        changes: List[CodeChange],
        output_path: str,
        trend_data: Optional[List[TrendData]] = None
    ) -> str:
        html_content = self._generate_html(suite, impact_analyses, changes, trend_data)
        
        full_output_path = Path(self.base_path) / output_path
        full_output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return str(full_output_path)

    def _generate_html(
        self,
        suite: RegressionTestSuite,
        impact_analyses: List[ImpactAnalysis],
        changes: List[CodeChange],
        trend_data: Optional[List[TrendData]] = None
    ) -> str:
        pass_rate = round(suite.passed / max(suite.total_tests, 1) * 100, 2)
        
        results_html = self._generate_results_table(suite.results)
        changes_html = self._generate_changes_table(changes)
        impact_html = self._generate_impact_table(impact_analyses)
        retry_html = self._generate_retry_stats(suite.retry_stats) if suite.retry_stats else ""
        trend_html = self._generate_trend_section(trend_data) if trend_data else ""
        performance_html = self._generate_performance_section(suite)

        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>回归测试报告 - 增强版</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .summary {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 20px; margin-bottom: 20px; }}
        .card {{ background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .card h3 {{ color: #333; margin-bottom: 15px; font-size: 14px; text-transform: uppercase; }}
        .card .value {{ font-size: 32px; font-weight: bold; color: #6366f1; }}
        .card .label {{ color: #666; font-size: 12px; margin-top: 5px; }}
        .section {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .section h2 {{ color: #333; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #6366f1; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; color: #333; }}
        .status-pass {{ color: #10b981; font-weight: bold; }}
        .status-fail {{ color: #ef4444; font-weight: bold; }}
        .status-error {{ color: #ef4444; }}
        .status-skip {{ color: #f59e0b; }}
        .impact-critical {{ color: #ef4444; font-weight: bold; }}
        .impact-high {{ color: #f97316; font-weight: bold; }}
        .impact-medium {{ color: #f59e0b; }}
        .impact-low {{ color: #10b981; }}
        .progress-bar {{ height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; margin-top: 10px; }}
        .progress-fill {{ height: 100%; border-radius: 4px; }}
        .progress-fill.high {{ background: #10b981; }}
        .progress-fill.medium {{ background: #f59e0b; }}
        .progress-fill.low {{ background: #ef4444; }}
        .chart-container {{ margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px; }}
        .metric-item {{ padding: 15px; background: #f8f9fa; border-radius: 8px; text-align: center; }}
        .metric-item .metric-value {{ font-size: 24px; font-weight: bold; color: #6366f1; }}
        .metric-item .metric-label {{ font-size: 12px; color: #666; margin-top: 5px; }}
        .retry-stats {{ background: #fef3c7; padding: 15px; border-radius: 8px; margin-top: 15px; }}
        .badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
        .badge-success {{ background: #d1fae5; color: #065f46; }}
        .badge-warning {{ background: #fef3c7; color: #92400e; }}
        .badge-danger {{ background: #fee2e2; color: #991b1b; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔄 回归测试报告 - 增强版</h1>
            <p>生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>并行工作线程: {suite.parallel_workers} | 重试启用: {'是' if self.config.retry_failed else '否'}</p>
        </div>
        
        <div class="summary">
            <div class="card">
                <h3>总测试数</h3>
                <div class="value">{suite.total_tests}</div>
                <div class="label">测试用例</div>
            </div>
            <div class="card">
                <h3>通过</h3>
                <div class="value" style="color: #10b981;">{suite.passed}</div>
                <div class="label">成功</div>
            </div>
            <div class="card">
                <h3>失败</h3>
                <div class="value" style="color: #ef4444;">{suite.failed}</div>
                <div class="label">失败</div>
            </div>
            <div class="card">
                <h3>跳过/错误</h3>
                <div class="value" style="color: #f59e0b;">{suite.skipped}/{suite.errors}</div>
                <div class="label">跳过/错误</div>
            </div>
            <div class="card">
                <h3>通过率</h3>
                <div class="value">{pass_rate}%</div>
                <div class="label">成功率</div>
                <div class="progress-bar">
                    <div class="progress-fill {'high' if pass_rate >= 80 else 'medium' if pass_rate >= 60 else 'low'}" style="width: {min(pass_rate, 100)}%"></div>
                </div>
            </div>
        </div>
        
        {performance_html}
        
        {retry_html}
        
        {trend_html}
        
        <div class="section">
            <h2>📝 代码变更</h2>
            {changes_html}
        </div>
        
        <div class="section">
            <h2>📊 影响分析</h2>
            {impact_html}
        </div>
        
        <div class="section">
            <h2>🧪 测试结果</h2>
            {results_html}
        </div>
    </div>
</body>
</html>'''

    def _generate_results_table(self, results: List[RegressionTestResult]) -> str:
        rows = ""
        for r in results:
            status_class = f"status-{r.status.value}"
            status_icon = {
                TestStatus.PASSED: "✓",
                TestStatus.FAILED: "✗",
                TestStatus.ERROR: "⚠",
                TestStatus.SKIPPED: "○"
            }.get(r.status, "?")
            
            retry_badge = ""
            if r.retry_count > 0:
                retry_badge = f' <span class="badge badge-warning">重试{r.retry_count}次</span>'
                if r.status == TestStatus.PASSED:
                    retry_badge = f' <span class="badge badge-success">重试成功</span>'
            
            rows += f'''
            <tr>
                <td>{r.test_name}{retry_badge}</td>
                <td class="{status_class}">{status_icon} {r.status.value}</td>
                <td>{r.duration:.2f}s</td>
                <td>{r.error_message[:100] if r.error_message else '-'}</td>
            </tr>'''
        
        if not rows:
            return "<p>无测试结果</p>"
        
        return f'''<table>
            <thead>
                <tr>
                    <th>测试名称</th>
                    <th>状态</th>
                    <th>耗时</th>
                    <th>错误信息</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>'''

    def _generate_changes_table(self, changes: List[CodeChange]) -> str:
        if not changes:
            return "<p>无代码变更</p>"
        
        rows = ""
        for c in changes:
            ast_info = ""
            if c.ast_changes:
                if c.ast_changes.get("removed_functions"):
                    ast_info += f'删除函数: {len(c.ast_changes["removed_functions"])} '
                if c.ast_changes.get("added_functions"):
                    ast_info += f'新增函数: {len(c.ast_changes["added_functions"])} '
            
            rows += f'''
            <tr>
                <td>{c.file_path}</td>
                <td>{c.change_type.value}</td>
                <td>{len(c.affected_functions)}</td>
                <td>{', '.join(c.affected_functions[:5])}</td>
                <td>{ast_info or '-'}</td>
            </tr>'''
        
        return f'''<table>
            <thead>
                <tr>
                    <th>文件路径</th>
                    <th>变更类型</th>
                    <th>影响函数数</th>
                    <th>函数列表</th>
                    <th>AST分析</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>'''

    def _generate_impact_table(self, impact_analyses: List[ImpactAnalysis]) -> str:
        if not impact_analyses:
            return "<p>无影响分析</p>"
        
        rows = ""
        for a in impact_analyses:
            impact_class = f"impact-{a.impact_level.value}"
            
            api_impact = ""
            if a.api_impact:
                api_impact = f'<br><small>API: {len(a.api_impact)} 个</small>'
            
            db_impact = ""
            if a.db_impact:
                db_impact = f'<br><small>DB: {len(a.db_impact)} 项</small>'
            
            rows += f'''
            <tr>
                <td>{a.changed_file}</td>
                <td>{len(a.affected_files)}</td>
                <td>{len(a.affected_tests)}</td>
                <td class="{impact_class}">{a.impact_level.value}</td>
                <td>{a.risk_score:.1f}</td>
                <td>{a.reasoning[:80]}...{api_impact}{db_impact}</td>
            </tr>'''
        
        return f'''<table>
            <thead>
                <tr>
                    <th>变更文件</th>
                    <th>影响文件数</th>
                    <th>影响测试数</th>
                    <th>影响级别</th>
                    <th>风险评分</th>
                    <th>详细说明</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>'''
    
    def _generate_retry_stats(self, retry_stats: Dict[str, int]) -> str:
        if not retry_stats or retry_stats.get("total_retries", 0) == 0:
            return ""
        
        return f'''
        <div class="section">
            <h2>🔄 重试统计</h2>
            <div class="retry-stats">
                <p><strong>总重试次数:</strong> {retry_stats.get("total_retries", 0)}</p>
                <p><strong>重试测试数:</strong> {retry_stats.get("tests_retried", 0)}</p>
                <p><strong>重试成功数:</strong> {retry_stats.get("retries_passed", 0)}</p>
            </div>
        </div>'''
    
    def _generate_trend_section(self, trend_data: List[TrendData]) -> str:
        if not trend_data or len(trend_data) < 2:
            return ""
        
        recent_trends = trend_data[-10:] if len(trend_data) >= 10 else trend_data
        
        trend_rows = ""
        for t in reversed(recent_trends):
            trend_rows += f'''
            <tr>
                <td>{t.date}</td>
                <td>{t.total_tests}</td>
                <td>{t.passed}</td>
                <td>{t.failed}</td>
                <td>{t.pass_rate}%</td>
                <td>{t.duration:.2f}s</td>
            </tr>'''
        
        return f'''
        <div class="section">
            <h2>📈 历史趋势</h2>
            <table>
                <thead>
                    <tr>
                        <th>时间</th>
                        <th>总测试数</th>
                        <th>通过</th>
                        <th>失败</th>
                        <th>通过率</th>
                        <th>耗时</th>
                    </tr>
                </thead>
                <tbody>
                    {trend_rows}
                </tbody>
            </table>
        </div>'''
    
    def _generate_performance_section(self, suite: RegressionTestSuite) -> str:
        if suite.total_tests == 0:
            return ""
        
        avg_duration = suite.duration / suite.total_tests if suite.total_tests > 0 else 0
        
        return f'''
        <div class="section">
            <h2>⚡ 性能指标</h2>
            <div class="metric-grid">
                <div class="metric-item">
                    <div class="metric-value">{suite.duration:.2f}s</div>
                    <div class="metric-label">总耗时</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{avg_duration:.2f}s</div>
                    <div class="metric-label">平均测试耗时</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{suite.parallel_workers}</div>
                    <div class="metric-label">并行工作线程</div>
                </div>
            </div>
        </div>'''


class RegressionTestReporter:
    def __init__(self, base_path: str, config: RegressionTestConfig):
        self.base_path = base_path
        self.config = config
        self.html_generator = HTMLReportGenerator(base_path)
        self.trend_analyzer = TrendAnalyzer(base_path)

    def generate_report(
        self,
        suite: RegressionTestSuite,
        impact_analyses: List[ImpactAnalysis],
        changes: List[CodeChange],
        output_path: str
    ) -> Dict[str, Any]:
        avg_risk_score = sum(a.risk_score for a in impact_analyses) / len(impact_analyses) if impact_analyses else 0
        
        self.trend_analyzer.load_trend_data()
        self.trend_analyzer.add_trend_point(suite, avg_risk_score)
        self.trend_analyzer.save_trend_data()
        
        trend_analysis = self.trend_analyzer.analyze_trends()
        
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "config": {
                "source_dirs": self.config.source_dirs,
                "test_dirs": self.config.test_dirs,
                "fail_fast": self.config.fail_fast,
                "parallel": self.config.parallel,
                "max_workers": self.config.max_workers,
                "retry_enabled": self.config.retry_failed
            },
            "summary": {
                "total_tests": suite.total_tests,
                "passed": suite.passed,
                "failed": suite.failed,
                "skipped": suite.skipped,
                "errors": suite.errors,
                "pass_rate": round(suite.passed / max(suite.total_tests, 1) * 100, 2),
                "duration": round(suite.duration, 2),
                "changes_detected": len(changes),
                "high_impact_changes": sum(1 for a in impact_analyses if a.impact_level in [ImpactLevel.CRITICAL, ImpactLevel.HIGH]),
                "avg_risk_score": round(avg_risk_score, 2)
            },
            "retry_stats": suite.retry_stats,
            "changes": [
                {
                    "file_path": c.file_path,
                    "change_type": c.change_type.value,
                    "affected_functions": c.affected_functions,
                    "ast_changes": c.ast_changes
                }
                for c in changes
            ],
            "impact_analysis": [
                {
                    "changed_file": a.changed_file,
                    "affected_files": a.affected_files,
                    "affected_tests": a.affected_tests,
                    "impact_level": a.impact_level.value,
                    "risk_score": a.risk_score,
                    "reasoning": a.reasoning,
                    "api_impact": a.api_impact,
                    "db_impact": a.db_impact
                }
                for a in impact_analyses
            ],
            "test_results": [
                {
                    "test_name": r.test_name,
                    "status": r.status.value,
                    "duration": round(r.duration, 4),
                    "error_message": r.error_message,
                    "retry_count": r.retry_count
                }
                for r in suite.results
            ],
            "trend_analysis": trend_analysis,
            "recommendations": self._generate_recommendations(suite, impact_analyses, trend_analysis)
        }

        full_output_path = Path(self.base_path) / output_path
        full_output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        if "html" in self.config.output_formats:
            html_path = str(full_output_path).replace(".json", ".html")
            self.html_generator.generate(
                suite, 
                impact_analyses, 
                changes, 
                html_path,
                self.trend_analyzer.trend_data
            )

        return report

    def _generate_recommendations(
        self,
        suite: RegressionTestSuite,
        impact_analyses: List[ImpactAnalysis],
        trend_analysis: Dict[str, Any]
    ) -> List[str]:
        recommendations = []
        
        if suite.failed > 0:
            recommendations.append(f"有 {suite.failed} 个测试失败，请检查以下变更:")
            for result in suite.results:
                if result.status == TestStatus.FAILED:
                    recommendations.append(f"  - {result.test_name}")
        
        if suite.retry_stats and suite.retry_stats.get("total_retries", 0) > 0:
            retry_success_rate = suite.retry_stats.get("retries_passed", 0) / max(suite.retry_stats.get("tests_retried", 1), 1) * 100
            if retry_success_rate > 50:
                recommendations.append(f"重试成功率为 {retry_success_rate:.1f}%，建议检查测试稳定性")
        
        critical_changes = [a for a in impact_analyses if a.impact_level == ImpactLevel.CRITICAL]
        if critical_changes:
            recommendations.append(f"发现 {len(critical_changes)} 个关键变更，需要全面测试")
        
        high_risk = [a for a in impact_analyses if a.risk_score > 50]
        if high_risk:
            recommendations.append(f"发现 {len(high_risk)} 个高风险变更，建议增加测试覆盖")
        
        trend_direction = trend_analysis.get("trend_direction", "stable")
        if trend_direction == "declining":
            recommendations.append("测试通过率呈下降趋势，建议关注代码质量")
        elif trend_direction == "improving":
            recommendations.append("测试通过率呈上升趋势，继续保持")
        
        if not recommendations:
            recommendations.append("回归测试通过，未发现问题")
        
        recommendations.extend([
            "建议在每次提交前运行回归测试",
            "保持测试用例与代码同步更新",
            "关注高风险变更的测试覆盖",
            "定期检查测试稳定性，减少flaky测试"
        ])
        
        return recommendations

    def print_report(self, report: Dict[str, Any]):
        print("\n" + "=" * 80)
        print("回归测试报告 - 增强版")
        print("=" * 80)
        
        summary = report["summary"]
        print(f"\n测试摘要:")
        print(f"  总测试数: {summary['total_tests']}")
        print(f"  通过: {summary['passed']}")
        print(f"  失败: {summary['failed']}")
        print(f"  跳过: {summary['skipped']}")
        print(f"  错误: {summary['errors']}")
        print(f"  通过率: {summary['pass_rate']}%")
        print(f"  检测变更: {summary['changes_detected']}")
        print(f"  高影响变更: {summary['high_impact_changes']}")
        print(f"  平均风险分: {summary['avg_risk_score']}")
        
        if report.get("retry_stats"):
            retry_stats = report["retry_stats"]
            print(f"\n重试统计:")
            print(f"  总重试次数: {retry_stats.get('total_retries', 0)}")
            print(f"  重试测试数: {retry_stats.get('tests_retried', 0)}")
            print(f"  重试成功数: {retry_stats.get('retries_passed', 0)}")
        
        if report.get("trend_analysis"):
            trend = report["trend_analysis"]
            print(f"\n趋势分析:")
            print(f"  平均通过率: {trend.get('avg_pass_rate', 0)}%")
            print(f"  趋势方向: {trend.get('trend_direction', 'unknown')}")
        
        print(f"\n建议:")
        for i, rec in enumerate(report["recommendations"][:5], 1):
            print(f"  {i}. {rec}")


class RegressionTestExecutor:
    def __init__(self, base_path: str, config: Optional[RegressionTestConfig] = None):
        self.base_path = base_path
        self.config = config or RegressionTestConfig()
        self.change_detector = ChangeDetector(base_path, self.config)
        self.impact_analyzer = ImpactAnalyzer(base_path, self.config)
        self.test_selector = TestSelector(base_path, self.config)
        self.test_runner = RegressionTestRunner(base_path, self.config)
        self.reporter = RegressionTestReporter(base_path, self.config)

    def execute(
        self,
        since: str = "HEAD~1",
        run_all: bool = False,
        output_path: str = "docs/reports/regression_test.json",
        strategy: str = "balanced"
    ) -> Dict[str, Any]:
        print("=" * 60)
        print("回归测试智能执行 - 增强版")
        print("=" * 60)
        
        self.test_selector.load_history()
        
        print("\n1. 检测代码变更...")
        changes = self.change_detector.detect_from_git(since)
        print(f"   检测到 {len(changes)} 个文件变更")
        
        print("\n2. 构建依赖图...")
        self.impact_analyzer.build_dependency_graph(self.config.source_dirs)
        
        print("\n3. 分析变更影响...")
        impact_analyses = self.impact_analyzer.analyze_impact(changes)
        print(f"   分析了 {len(impact_analyses)} 个变更的影响")
        
        print("\n4. 选择测试用例...")
        if run_all:
            selected_tests = self.test_selector.select_all_tests()
            print(f"   选择全部 {len(selected_tests)} 个测试")
        else:
            selection_result = self.test_selector.smart_selection(impact_analyses, strategy)
            selected_tests = selection_result["selected_tests"]
            print(f"   使用 '{strategy}' 策略选择 {len(selected_tests)} 个测试")
            print(f"   预计耗时: {selection_result['estimated_duration']:.1f}s")
            print(f"   覆盖率估计: {selection_result['coverage_estimate']:.1f}%")
        
        print("\n5. 执行回归测试...")
        if self.config.parallel:
            print(f"   启用并行执行 (工作线程: {self.config.max_workers})")
        if self.config.retry_failed:
            print(f"   启用失败重试 (重试次数: {self.config.retry_count})")
        
        suite = self.test_runner.run_tests(selected_tests)
        
        for result in suite.results:
            self.test_selector.update_test_history(result.test_name, {
                "status": result.status.value,
                "duration": result.duration
            })
        
        self.test_selector.save_history()
        
        print("\n6. 生成测试报告...")
        report = self.reporter.generate_report(suite, impact_analyses, changes, output_path)
        
        report["selection_info"] = {
            "strategy": strategy,
            "total_available": len(self.test_selector.select_all_tests()),
            "selected": len(selected_tests)
        }
        
        self.reporter.print_report(report)
        
        return report

    def analyze_only(self, since: str = "HEAD~1") -> Dict[str, Any]:
        print("=" * 60)
        print("变更影响分析 - 增强版")
        print("=" * 60)
        
        print("\n1. 检测代码变更...")
        changes = self.change_detector.detect_from_git(since)
        print(f"   检测到 {len(changes)} 个文件变更")
        
        print("\n2. 构建依赖图...")
        self.impact_analyzer.build_dependency_graph(self.config.source_dirs)
        
        print("\n3. 分析变更影响...")
        impact_analyses = self.impact_analyzer.analyze_impact(changes)
        
        return {
            "changes": [
                {
                    "file": c.file_path,
                    "type": c.change_type.value,
                    "affected_functions": c.affected_functions,
                    "ast_changes": c.ast_changes
                }
                for c in changes
            ],
            "impact_analyses": [
                {
                    "file": a.changed_file,
                    "impact_level": a.impact_level.value,
                    "risk_score": a.risk_score,
                    "affected_files": len(a.affected_files),
                    "affected_tests": len(a.affected_tests),
                    "reasoning": a.reasoning,
                    "api_impact": a.api_impact,
                    "db_impact": a.db_impact
                }
                for a in impact_analyses
            ],
            "summary": {
                "total_changes": len(changes),
                "critical_impact": len([a for a in impact_analyses if a.impact_level == ImpactLevel.CRITICAL]),
                "high_impact": len([a for a in impact_analyses if a.impact_level == ImpactLevel.HIGH]),
                "medium_impact": len([a for a in impact_analyses if a.impact_level == ImpactLevel.MEDIUM]),
                "low_impact": len([a for a in impact_analyses if a.impact_level == ImpactLevel.LOW]),
                "avg_risk_score": sum(a.risk_score for a in impact_analyses) / len(impact_analyses) if impact_analyses else 0
            }
        }

    def get_transitive_impact(self, file_path: str, depth: int = 3) -> Dict[str, Any]:
        self.impact_analyzer.build_dependency_graph(self.config.source_dirs)
        return self.impact_analyzer.get_transitive_impact(file_path, depth)

    def quick_check(self, files: List[str]) -> Dict[str, Any]:
        print("=" * 60)
        print("快速回归检查 - 增强版")
        print("=" * 60)
        
        changes = [
            CodeChange(file_path=f, change_type=ChangeType.MODIFIED)
            for f in files
        ]
        
        self.impact_analyzer.build_dependency_graph(self.config.source_dirs)
        impact_analyses = self.impact_analyzer.analyze_impact(changes)
        
        all_tests = set()
        for analysis in impact_analyses:
            all_tests.update(analysis.affected_tests)
        
        return {
            "files_checked": len(files),
            "tests_to_run": list(all_tests),
            "total_tests": len(all_tests),
            "impact_summary": {
                a.changed_file: {
                    "level": a.impact_level.value,
                    "risk": a.risk_score,
                    "tests": len(a.affected_tests),
                    "api_impact": a.api_impact,
                    "db_impact": a.db_impact
                }
                for a in impact_analyses
            }
        }

    def get_test_recommendations(self, since: str = "HEAD~1") -> Dict[str, Any]:
        changes = self.change_detector.detect_from_git(since)
        self.impact_analyzer.build_dependency_graph(self.config.source_dirs)
        impact_analyses = self.impact_analyzer.analyze_impact(changes)
        
        recommendations = {
            "must_run": [],
            "should_run": [],
            "nice_to_run": [],
            "skip": []
        }
        
        for analysis in impact_analyses:
            for test in analysis.affected_tests:
                test_info = {
                    "test": test,
                    "reason": f"受 {analysis.changed_file} 变更影响",
                    "risk_score": analysis.risk_score,
                    "api_impact": analysis.api_impact,
                    "db_impact": analysis.db_impact
                }
                
                if analysis.impact_level == ImpactLevel.CRITICAL:
                    recommendations["must_run"].append(test_info)
                elif analysis.impact_level == ImpactLevel.HIGH:
                    recommendations["should_run"].append(test_info)
                elif analysis.impact_level == ImpactLevel.MEDIUM:
                    recommendations["nice_to_run"].append(test_info)
                else:
                    recommendations["skip"].append(test_info)
        
        return recommendations


def main():
    parser = argparse.ArgumentParser(description="回归测试智能执行 - 增强版")
    parser.add_argument(
        "--config",
        help="配置文件路径 (YAML/JSON)"
    )
    parser.add_argument(
        "--since",
        default="HEAD~1",
        help="检测变更的起始点"
    )
    parser.add_argument(
        "--run-all",
        action="store_true",
        help="运行所有测试"
    )
    parser.add_argument(
        "--output",
        default="docs/reports/regression_test.json",
        help="输出报告路径"
    )
    parser.add_argument(
        "--generate-config",
        action="store_true",
        help="生成配置文件模板"
    )
    parser.add_argument(
        "--strategy",
        choices=["fast", "thorough", "balanced", "risk_based", "ml_based"],
        default="balanced",
        help="测试选择策略"
    )
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="仅分析变更影响，不执行测试"
    )
    parser.add_argument(
        "--quick-check",
        nargs="+",
        help="快速检查指定文件的影响"
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=4,
        help="并行工作线程数"
    )
    parser.add_argument(
        "--no-retry",
        action="store_true",
        help="禁用失败重试"
    )
    
    args = parser.parse_args()
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    config_loader = ConfigLoader(base_path)
    
    if args.generate_config:
        config_loader.save_template("regression_test_config.yaml")
        print("配置文件模板已生成: regression_test_config.yaml")
        return 0
    
    config = config_loader.load(args.config)
    
    if args.parallel:
        config.max_workers = args.parallel
        config.parallel = True
    
    if args.no_retry:
        config.retry_failed = False
    
    executor = RegressionTestExecutor(base_path, config)
    
    if args.analyze_only:
        result = executor.analyze_only(args.since)
        print(f"\n变更影响分析完成:")
        print(f"  总变更: {result['summary']['total_changes']}")
        print(f"  关键影响: {result['summary']['critical_impact']}")
        print(f"  高影响: {result['summary']['high_impact']}")
        print(f"  平均风险分: {result['summary']['avg_risk_score']:.1f}")
        return 0
    
    if args.quick_check:
        result = executor.quick_check(args.quick_check)
        print(f"\n快速检查完成:")
        print(f"  检查文件数: {result['files_checked']}")
        print(f"  需运行测试: {result['total_tests']}")
        return 0
    
    report = executor.execute(
        args.since,
        args.run_all,
        args.output,
        args.strategy
    )
    
    return 0 if report["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
