"""
架构优化建议模块

包含：
- ModuleCouplingAnalyzer: 模块耦合度分析
- DependencyOptimizer: 依赖关系优化
- DesignPatternSuggester: 设计模式建议
- RefactoringSuggester: 重构建议生成
"""

import ast
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class CouplingType(Enum):
    DATA_COUPLING = "data_coupling"
    STAMP_COUPLING = "stamp_coupling"
    CONTROL_COUPLING = "control_coupling"
    COMMON_COUPLING = "common_coupling"
    CONTENT_COUPLING = "content_coupling"


class CouplingLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class ModuleInfo:
    name: str
    path: str
    imports: Set[str] = field(default_factory=set)
    exports: Set[str] = field(default_factory=set)
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    coupling_score: float = 0.0
    cohesion_score: float = 0.0


@dataclass
class CouplingIssue:
    source_module: str
    target_module: str
    coupling_type: CouplingType
    level: CouplingLevel
    description: str
    suggestions: List[str]
    line_number: int = 0


@dataclass
class ArchitectureSuggestion:
    suggestion_type: str
    priority: str
    description: str
    affected_modules: List[str]
    implementation_steps: List[str]
    benefits: List[str]
    risks: List[str]


class ModuleCouplingAnalyzer:
    """模块耦合度分析器"""

    def __init__(self):
        self._modules: Dict[str, ModuleInfo] = {}
        self._coupling_matrix: Dict[str, Dict[str, float]] = {}
        self._issues: List[CouplingIssue] = []

    def analyze(self, project_path: Path) -> Dict[str, Any]:
        self._modules.clear()
        self._coupling_matrix.clear()
        self._issues.clear()

        self._collect_modules(project_path)
        self._analyze_dependencies()
        self._calculate_coupling_scores()
        self._detect_coupling_issues()

        return self._generate_report()

    def _collect_modules(self, project_path: Path):
        backend_dir = project_path / "backend" / "app"
        if backend_dir.exists():
            for py_file in backend_dir.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                self._analyze_module(py_file, "backend")

        frontend_dir = project_path / "frontend" / "src"
        if frontend_dir.exists():
            for ts_file in frontend_dir.rglob("*.ts"):
                if "node_modules" in str(ts_file):
                    continue
                self._analyze_module(ts_file, "frontend")

    def _analyze_module(self, file_path: Path, layer: str):
        module_name = f"{layer}:{file_path.stem}"
        module_info = ModuleInfo(
            name=module_name,
            path=str(file_path)
        )

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if file_path.suffix == '.py':
                self._analyze_python_module(content, module_info)
            elif file_path.suffix == '.ts':
                self._analyze_typescript_module(content, module_info)

            self._modules[module_name] = module_info

        except Exception:
            pass

    def _analyze_python_module(self, content: str, module_info: ModuleInfo):
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_info.imports.add(alias.name)
                    module_info.dependencies.add(alias.name.split('.')[0])

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_info.imports.add(node.module)
                    module_info.dependencies.add(node.module.split('.')[0])

            elif isinstance(node, ast.ClassDef):
                module_info.classes.append(node.name)
                module_info.exports.add(node.name)

            elif isinstance(node, ast.FunctionDef):
                if not node.name.startswith('_'):
                    module_info.functions.append(node.name)
                    module_info.exports.add(node.name)

    def _analyze_typescript_module(self, content: str, module_info: ModuleInfo):
        import_patterns = [
            r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]',
            r'import\s+[\'"]([^\'"]+)[\'"]',
        ]

        for pattern in import_patterns:
            for match in re.finditer(pattern, content):
                module_info.imports.add(match.group(1))
                if not match.group(1).startswith('.'):
                    module_info.dependencies.add(match.group(1).split('/')[0])

        export_pattern = r'export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)'
        for match in re.finditer(export_pattern, content):
            module_info.exports.add(match.group(1))

    def _analyze_dependencies(self):
        for module_name, module_info in self._modules.items():
            for dep in module_info.dependencies:
                for other_name, other_info in self._modules.items():
                    if other_name != module_name:
                        if dep in other_name or dep in other_info.exports:
                            module_info.dependents.add(other_name)
                            other_info.dependencies.add(module_name)

    def _calculate_coupling_scores(self):
        for module_name, module_info in self._modules.items():
            afferent_coupling = len(module_info.dependents)
            efferent_coupling = len(module_info.dependencies)

            if afferent_coupling + efferent_coupling > 0:
                module_info.coupling_score = (
                    (afferent_coupling * 0.7 + efferent_coupling * 0.3) /
                    (afferent_coupling + efferent_coupling)
                )

            self._coupling_matrix[module_name] = {}
            for other_name in module_info.dependencies:
                if other_name in self._modules:
                    self._coupling_matrix[module_name][other_name] = 1.0

    def _detect_coupling_issues(self):
        for module_name, module_info in self._modules.items():
            if len(module_info.dependencies) > 10:
                self._issues.append(CouplingIssue(
                    source_module=module_name,
                    target_module="multiple",
                    coupling_type=CouplingType.COMMON_COUPLING,
                    level=CouplingLevel.HIGH,
                    description=f"模块依赖过多 ({len(module_info.dependencies)} 个)，违反单一职责原则",
                    suggestions=[
                        "将模块拆分为更小的功能模块",
                        "使用依赖注入替代直接导入",
                        "考虑使用接口/抽象层解耦"
                    ]
                ))

            if len(module_info.dependents) > 15:
                self._issues.append(CouplingIssue(
                    source_module=module_name,
                    target_module="multiple",
                    coupling_type=CouplingType.CONTENT_COUPLING,
                    level=CouplingLevel.VERY_HIGH,
                    description=f"模块被过多模块依赖 ({len(module_info.dependents)} 个)，可能是上帝模块",
                    suggestions=[
                        "检查模块职责是否过于宽泛",
                        "考虑拆分为多个专门模块",
                        "使用发布-订阅模式减少直接依赖"
                    ]
                ))

            for dep in module_info.dependencies:
                if dep in self._modules:
                    dep_info = self._modules[dep]
                    if module_name in dep_info.dependencies:
                        self._issues.append(CouplingIssue(
                            source_module=module_name,
                            target_module=dep,
                            coupling_type=CouplingType.CONTENT_COUPLING,
                            level=CouplingLevel.HIGH,
                            description=f"循环依赖: {module_name} <-> {dep}",
                            suggestions=[
                                "提取共同依赖到独立模块",
                                "使用依赖倒置原则",
                                "引入接口层解耦"
                            ]
                        ))

    def _generate_report(self) -> Dict[str, Any]:
        return {
            'summary': {
                'total_modules': len(self._modules),
                'total_issues': len(self._issues),
                'high_coupling_modules': len([
                    m for m in self._modules.values()
                    if m.coupling_score > 0.7
                ]),
                'average_coupling': sum(
                    m.coupling_score for m in self._modules.values()
                ) / len(self._modules) if self._modules else 0
            },
            'modules': {
                name: {
                    'path': info.path,
                    'dependencies': list(info.dependencies),
                    'dependents': list(info.dependents),
                    'coupling_score': round(info.coupling_score, 3),
                    'exports': list(info.exports)
                }
                for name, info in self._modules.items()
            },
            'issues': [
                {
                    'source': issue.source_module,
                    'target': issue.target_module,
                    'type': issue.coupling_type.value,
                    'level': issue.level.value,
                    'description': issue.description,
                    'suggestions': issue.suggestions
                }
                for issue in self._issues
            ],
            'recommendations': self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        recommendations = []

        high_coupling = [m for m in self._modules.values() if m.coupling_score > 0.7]
        if high_coupling:
            recommendations.append(
                f"发现 {len(high_coupling)} 个高耦合模块，建议优先重构"
            )

        circular_deps = [i for i in self._issues if '循环依赖' in i.description]
        if circular_deps:
            recommendations.append(
                f"发现 {len(circular_deps)} 处循环依赖，建议使用依赖倒置原则解耦"
            )

        return recommendations


class DependencyOptimizer:
    """依赖关系优化器"""

    def __init__(self):
        self._dependency_graph: Dict[str, Set[str]] = {}
        self._optimization_suggestions: List[Dict[str, Any]] = []

    def analyze(self, project_path: Path) -> Dict[str, Any]:
        self._dependency_graph.clear()
        self._optimization_suggestions.clear()

        self._build_dependency_graph(project_path)
        self._detect_unused_dependencies(project_path)
        self._detect_version_conflicts(project_path)
        self._detect_circular_dependencies()
        self._suggest_optimizations()

        return self._generate_report()

    def _build_dependency_graph(self, project_path: Path):
        requirements_file = project_path / "backend" / "requirements.txt"
        if requirements_file.exists():
            self._parse_requirements(requirements_file, "backend")

        package_json = project_path / "frontend" / "package.json"
        if package_json.exists():
            self._parse_package_json(package_json, "frontend")

    def _parse_requirements(self, file_path: Path, layer: str):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = re.split(r'[<>=!~]+', line)
                        package = parts[0].strip().lower()
                        self._dependency_graph[f"{layer}:{package}"] = set()
        except Exception:
            pass

    def _parse_package_json(self, file_path: Path, layer: str):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for dep_type in ['dependencies', 'devDependencies']:
                if dep_type in data:
                    for package in data[dep_type]:
                        self._dependency_graph[f"{layer}:{package}"] = set()
        except Exception:
            pass

    def _detect_unused_dependencies(self, project_path: Path):
        backend_dir = project_path / "backend"
        if backend_dir.exists():
            self._check_unused_python_deps(backend_dir)

        frontend_dir = project_path / "frontend"
        if frontend_dir.exists():
            self._check_unused_js_deps(frontend_dir)

    def _check_unused_python_deps(self, backend_dir: Path):
        used_imports = set()

        for py_file in backend_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            used_imports.add(alias.name.split('.')[0].lower())
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            used_imports.add(node.module.split('.')[0].lower())
            except Exception:
                pass

        for dep in self._dependency_graph:
            if dep.startswith("backend:"):
                package = dep.split(":")[1]
                if package not in used_imports:
                    self._optimization_suggestions.append({
                        'type': 'unused_dependency',
                        'package': package,
                        'layer': 'backend',
                        'suggestion': f"依赖 {package} 可能未被使用，建议检查并移除"
                    })

    def _check_unused_js_deps(self, frontend_dir: Path):
        used_imports = set()

        for ts_file in frontend_dir.rglob("*.ts"):
            if "node_modules" in str(ts_file):
                continue
            try:
                with open(ts_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                import_pattern = r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]'
                for match in re.finditer(import_pattern, content):
                    package = match.group(1)
                    if not package.startswith('.'):
                        used_imports.add(package.split('/')[0])
            except Exception:
                pass

        for dep in self._dependency_graph:
            if dep.startswith("frontend:"):
                package = dep.split(":")[1]
                if package not in used_imports:
                    self._optimization_suggestions.append({
                        'type': 'unused_dependency',
                        'package': package,
                        'layer': 'frontend',
                        'suggestion': f"依赖 {package} 可能未被使用，建议检查并移除"
                    })

    def _detect_version_conflicts(self, project_path: Path):
        pass

    def _detect_circular_dependencies(self):
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self._dependency_graph.get(node, set()):
                if neighbor not in visited:
                    cycle = dfs(neighbor, path + [node])
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [node, neighbor]

            rec_stack.remove(node)
            return None

        for node in self._dependency_graph:
            if node not in visited:
                cycle = dfs(node, [])
                if cycle:
                    cycles.append(cycle)

        for cycle in cycles:
            self._optimization_suggestions.append({
                'type': 'circular_dependency',
                'cycle': cycle,
                'suggestion': f"发现循环依赖: {' -> '.join(cycle)}，建议重构"
            })

    def _suggest_optimizations(self):
        self._optimization_suggestions.append({
            'type': 'general',
            'suggestion': "建议定期更新依赖版本以获取安全补丁"
        })

        self._optimization_suggestions.append({
            'type': 'general',
            'suggestion': "建议使用依赖锁定文件 (requirements.lock, package-lock.json)"
        })

    def _generate_report(self) -> Dict[str, Any]:
        return {
            'dependency_count': len(self._dependency_graph),
            'dependencies': {
                dep: list(targets) for dep, targets in self._dependency_graph.items()
            },
            'optimizations': self._optimization_suggestions,
            'summary': {
                'total_dependencies': len(self._dependency_graph),
                'unused_count': len([
                    s for s in self._optimization_suggestions
                    if s['type'] == 'unused_dependency'
                ]),
                'circular_count': len([
                    s for s in self._optimization_suggestions
                    if s['type'] == 'circular_dependency'
                ])
            }
        }


class DesignPatternSuggester:
    """设计模式建议器"""

    def __init__(self):
        self._pattern_detectors = {
            'singleton': self._detect_singleton_opportunity,
            'factory': self._detect_factory_opportunity,
            'strategy': self._detect_strategy_opportunity,
            'observer': self._detect_observer_opportunity,
            'decorator': self._detect_decorator_opportunity,
            'adapter': self._detect_adapter_opportunity,
            'facade': self._detect_facade_opportunity,
            'repository': self._detect_repository_opportunity,
            'dependency_injection': self._detect_di_opportunity,
        }

    def analyze(self, project_path: Path) -> Dict[str, Any]:
        suggestions = []

        backend_dir = project_path / "backend" / "app"
        if backend_dir.exists():
            for py_file in backend_dir.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                file_suggestions = self._analyze_file(py_file)
                suggestions.extend(file_suggestions)

        return {
            'suggestions': suggestions,
            'summary': {
                'total_suggestions': len(suggestions),
                'by_pattern': self._count_by_pattern(suggestions)
            }
        }

    def _analyze_file(self, file_path: Path) -> List[Dict[str, Any]]:
        suggestions = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            for pattern_name, detector in self._pattern_detectors.items():
                pattern_suggestions = detector(file_path, content, tree)
                suggestions.extend(pattern_suggestions)

        except Exception:
            pass

        return suggestions

    def _detect_singleton_opportunity(self, file_path: Path, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        suggestions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                has_init = any(
                    isinstance(n, ast.FunctionDef) and n.name == '__init__'
                    for n in node.body
                )

                global_vars = [
                    n for n in ast.walk(tree)
                    if isinstance(n, ast.Name) and n.id == f'_{node.name}_instance'
                ]

                if has_init and not global_vars:
                    if any('config' in node.name.lower() or 'manager' in node.name.lower()
                           for _ in [1]):
                        suggestions.append({
                            'pattern': 'singleton',
                            'file': str(file_path),
                            'class_name': node.name,
                            'line': node.lineno,
                            'reason': f"类 {node.name} 可能适合使用单例模式",
                            'implementation': self._get_singleton_template(node.name)
                        })

        return suggestions

    def _detect_factory_opportunity(self, file_path: Path, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        suggestions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                conditions = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Compare):
                        if isinstance(child.left, ast.Name):
                            conditions.append(child.left.id)

                if len(conditions) >= 3:
                    for cond in conditions:
                        if 'type' in cond.lower() or 'kind' in cond.lower():
                            suggestions.append({
                                'pattern': 'factory',
                                'file': str(file_path),
                                'line': node.lineno,
                                'reason': "多个条件分支创建对象，建议使用工厂模式",
                                'implementation': self._get_factory_template()
                            })
                            break

        return suggestions

    def _detect_strategy_opportunity(self, file_path: Path, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        suggestions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if 'strategy' in node.name.lower() or 'algorithm' in node.name.lower():
                    continue

                if node.args.args:
                    first_param = node.args.args[0].arg
                    if 'strategy' in first_param.lower() or 'algorithm' in first_param.lower():
                        suggestions.append({
                            'pattern': 'strategy',
                            'file': str(file_path),
                            'line': node.lineno,
                            'reason': f"函数 {node.name} 接受策略参数，建议使用策略模式",
                            'implementation': self._get_strategy_template()
                        })

        return suggestions

    def _detect_observer_opportunity(self, file_path: Path, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        suggestions = []

        observer_keywords = ['notify', 'subscribe', 'publish', 'emit', 'listen', 'callback']

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for keyword in observer_keywords:
                    if keyword in node.name.lower():
                        suggestions.append({
                            'pattern': 'observer',
                            'file': str(file_path),
                            'line': node.lineno,
                            'reason': f"函数 {node.name} 涉及事件通知，建议使用观察者模式",
                            'implementation': self._get_observer_template()
                        })
                        break

        return suggestions

    def _detect_decorator_opportunity(self, file_path: Path, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        suggestions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.decorator_list:
                    for dec in node.decorator_list:
                        if isinstance(dec, ast.Name):
                            if dec.id in ['log', 'timer', 'cache', 'retry', 'validate']:
                                suggestions.append({
                                    'pattern': 'decorator',
                                    'file': str(file_path),
                                    'line': node.lineno,
                                    'reason': f"函数 {node.name} 使用装饰器，建议封装为可复用装饰器",
                                    'implementation': self._get_decorator_template(dec.id)
                                })

        return suggestions

    def _detect_adapter_opportunity(self, file_path: Path, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        suggestions = []

        adapter_keywords = ['adapter', 'wrapper', 'convert', 'transform']

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for keyword in adapter_keywords:
                    if keyword in node.name.lower():
                        suggestions.append({
                            'pattern': 'adapter',
                            'file': str(file_path),
                            'line': node.lineno,
                            'reason': f"类 {node.name} 可能是适配器，建议明确接口定义",
                            'implementation': self._get_adapter_template()
                        })
                        break

        return suggestions

    def _detect_facade_opportunity(self, file_path: Path, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        suggestions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                method_count = sum(1 for n in node.body if isinstance(n, ast.FunctionDef))

                external_calls = 0
                for n in ast.walk(node):
                    if isinstance(n, ast.Call):
                        if isinstance(n.func, ast.Attribute):
                            if isinstance(n.func.value, ast.Name):
                                if n.func.value.id not in ['self', node.name]:
                                    external_calls += 1

                if method_count > 5 and external_calls > 10:
                    suggestions.append({
                        'pattern': 'facade',
                        'file': str(file_path),
                        'line': node.lineno,
                        'reason': f"类 {node.name} 可能适合作为门面类",
                        'implementation': self._get_facade_template()
                    })

        return suggestions

    def _detect_repository_opportunity(self, file_path: Path, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        suggestions = []

        db_operations = ['query', 'save', 'delete', 'update', 'find', 'get']

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                db_methods = []
                for n in node.body:
                    if isinstance(n, ast.FunctionDef):
                        for op in db_operations:
                            if op in n.name.lower():
                                db_methods.append(n.name)
                                break

                if len(db_methods) >= 3:
                    suggestions.append({
                        'pattern': 'repository',
                        'file': str(file_path),
                        'line': node.lineno,
                        'reason': f"类 {node.name} 包含多个数据库操作方法，建议使用仓储模式",
                        'implementation': self._get_repository_template()
                    })

        return suggestions

    def _detect_di_opportunity(self, file_path: Path, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        suggestions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name == '__init__':
                    hard_coded_deps = []
                    for n in ast.walk(node):
                        if isinstance(n, ast.Assign):
                            if isinstance(n.value, ast.Call):
                                if isinstance(n.value.func, ast.Name):
                                    hard_coded_deps.append(n.value.func.id)

                    if len(hard_coded_deps) >= 2:
                        suggestions.append({
                            'pattern': 'dependency_injection',
                            'file': str(file_path),
                            'line': node.lineno,
                            'reason': "构造函数中硬编码依赖，建议使用依赖注入",
                            'implementation': self._get_di_template()
                        })

        return suggestions

    def _count_by_pattern(self, suggestions: List[Dict[str, Any]]) -> Dict[str, int]:
        counts = {}
        for s in suggestions:
            pattern = s['pattern']
            counts[pattern] = counts.get(pattern, 0) + 1
        return counts

    def _get_singleton_template(self, class_name: str) -> str:
        return f'''
class {class_name}:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
'''

    def _get_factory_template(self) -> str:
        return '''
class Factory:
    @staticmethod
    def create(type_name: str, *args, **kwargs):
        creators = {
            'type_a': TypeA,
            'type_b': TypeB,
        }
        return creators.get(type_name, DefaultType)(*args, **kwargs)
'''

    def _get_strategy_template(self) -> str:
        return '''
from abc import ABC, abstractmethod

class Strategy(ABC):
    @abstractmethod
    def execute(self, data):
        pass

class ConcreteStrategyA(Strategy):
    def execute(self, data):
        pass

class Context:
    def __init__(self, strategy: Strategy):
        self._strategy = strategy

    def execute_strategy(self, data):
        return self._strategy.execute(data)
'''

    def _get_observer_template(self) -> str:
        return '''
class Observer(ABC):
    @abstractmethod
    def update(self, subject):
        pass

class Subject:
    def __init__(self):
        self._observers = []

    def attach(self, observer: Observer):
        self._observers.append(observer)

    def detach(self, observer: Observer):
        self._observers.remove(observer)

    def notify(self):
        for observer in self._observers:
            observer.update(self)
'''

    def _get_decorator_template(self, decorator_type: str) -> str:
        return f'''
def {decorator_type}(func):
    def wrapper(*args, **kwargs):
        # Pre-processing
        result = func(*args, **kwargs)
        # Post-processing
        return result
    return wrapper
'''

    def _get_adapter_template(self) -> str:
        return '''
class TargetInterface(ABC):
    @abstractmethod
    def request(self):
        pass

class Adapter(TargetInterface):
    def __init__(self, adaptee):
        self._adaptee = adaptee

    def request(self):
        return self._adaptee.specific_request()
'''

    def _get_facade_template(self) -> str:
        return '''
class Facade:
    def __init__(self):
        self._subsystem_a = SubsystemA()
        self._subsystem_b = SubsystemB()

    def operation(self):
        self._subsystem_a.operation_a()
        self._subsystem_b.operation_b()
'''

    def _get_repository_template(self) -> str:
        return '''
from abc import ABC, abstractmethod

class Repository(ABC):
    @abstractmethod
    def find_by_id(self, id):
        pass

    @abstractmethod
    def save(self, entity):
        pass

    @abstractmethod
    def delete(self, entity):
        pass

class ConcreteRepository(Repository):
    def __init__(self, db_session):
        self._session = db_session

    def find_by_id(self, id):
        return self._session.query(Entity).get(id)
'''

    def _get_di_template(self) -> str:
        return '''
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    service_a = providers.Singleton(
        ServiceA,
        param=config.param_a,
    )

    service_b = providers.Factory(
        ServiceB,
        service_a=service_a,
    )
'''


class RefactoringSuggester:
    """重构建议生成器"""

    def __init__(self):
        self._refactoring_rules = {
            'extract_method': self._check_extract_method,
            'extract_class': self._check_extract_class,
            'move_method': self._check_move_method,
            'inline_method': self._check_inline_method,
            'replace_conditional_with_polymorphism': self._check_polymorphism,
            'introduce_parameter_object': self._check_parameter_object,
            'replace_magic_number': self._check_magic_numbers,
            'consolidate_duplicate': self._check_duplicate_code,
        }

    def analyze(self, project_path: Path) -> Dict[str, Any]:
        suggestions = []

        backend_dir = project_path / "backend" / "app"
        if backend_dir.exists():
            for py_file in backend_dir.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                file_suggestions = self._analyze_file(py_file)
                suggestions.extend(file_suggestions)

        return {
            'suggestions': suggestions,
            'summary': {
                'total_suggestions': len(suggestions),
                'by_type': self._count_by_type(suggestions),
                'priority_breakdown': self._count_by_priority(suggestions)
            }
        }

    def _analyze_file(self, file_path: Path) -> List[Dict[str, Any]]:
        suggestions = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            for rule_name, checker in self._refactoring_rules.items():
                rule_suggestions = checker(file_path, content, tree)
                suggestions.extend(rule_suggestions)

        except Exception:
            pass

        return suggestions

    def _check_extract_method(self, file_path: Path, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        suggestions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                lines_in_function = len(content.split('\n')[node.lineno - 1:node.end_lineno]) if hasattr(node, 'end_lineno') else 0

                if lines_in_function > 30:
                    comments = [n for n in ast.walk(node) if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)]
                    if len(comments) > 2:
                        suggestions.append({
                            'type': 'extract_method',
                            'file': str(file_path),
                            'line': node.lineno,
                            'function': node.name,
                            'priority': 'high',
                            'reason': f"函数 {node.name} 过长 ({lines_in_function} 行) 且有多个注释分隔，建议拆分",
                            'steps': [
                                "识别函数中的独立功能块",
                                "为每个功能块创建新方法",
                                "用方法调用替换原代码块",
                                "确保方法命名清晰表达意图"
                            ]
                        })

        return suggestions

    def _check_extract_class(self, file_path: Path, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        suggestions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                method_prefixes = {}

                for method in methods:
                    prefix = method.name.split('_')[0] if '_' in method.name else method.name
                    if prefix not in method_prefixes:
                        method_prefixes[prefix] = []
                    method_prefixes[prefix].append(method.name)

                for prefix, method_list in method_prefixes.items():
                    if len(method_list) >= 3:
                        suggestions.append({
                            'type': 'extract_class',
                            'file': str(file_path),
                            'line': node.lineno,
                            'class': node.name,
                            'priority': 'medium',
                            'reason': f"类 {node.name} 中有 {len(method_list)} 个方法以 '{prefix}' 开头，可能需要提取为新类",
                            'steps': [
                                f"创建新类处理 {prefix} 相关功能",
                                "将相关方法和属性移至新类",
                                "在原类中创建新类的实例",
                                "更新所有调用点"
                            ]
                        })

        return suggestions

    def _check_move_method(self, file_path: Path, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        suggestions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for method in node.body:
                    if isinstance(method, ast.FunctionDef):
                        other_class_refs = set()

                        for n in ast.walk(method):
                            if isinstance(n, ast.Attribute):
                                if isinstance(n.value, ast.Name):
                                    if n.value.id != 'self' and n.value.id != node.name:
                                        other_class_refs.add(n.value.id)

                        if len(other_class_refs) == 1:
                            suggestions.append({
                                'type': 'move_method',
                                'file': str(file_path),
                                'line': method.lineno,
                                'method': method.name,
                                'priority': 'low',
                                'reason': f"方法 {method.name} 主要操作其他类的数据，考虑移动",
                                'steps': [
                                    f"将方法移至 {list(other_class_refs)[0]} 类",
                                    "在原类中委托调用",
                                    "考虑是否需要保留原方法"
                                ]
                            })

        return suggestions

    def _check_inline_method(self, file_path: Path, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        suggestions = []

        function_calls = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    function_calls[func_name] = function_calls.get(func_name, 0) + 1

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name in function_calls:
                    call_count = function_calls[node.name]
                    body_lines = len(node.body)

                    if call_count == 1 and body_lines <= 3:
                        suggestions.append({
                            'type': 'inline_method',
                            'file': str(file_path),
                            'line': node.lineno,
                            'method': node.name,
                            'priority': 'low',
                            'reason': f"方法 {node.name} 仅被调用一次且代码简短，考虑内联",
                            'steps': [
                                "将方法体复制到调用点",
                                "删除原方法定义",
                                "确保行为一致"
                            ]
                        })

        return suggestions

    def _check_polymorphism(self, file_path: Path, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        suggestions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                comparisons = []
                for n in ast.walk(node):
                    if isinstance(n, ast.Compare):
                        if isinstance(n.left, ast.Attribute):
                            if 'type' in n.left.attr.lower() or 'kind' in n.left.attr.lower():
                                comparisons.append(n)

                if len(comparisons) >= 3:
                    suggestions.append({
                        'type': 'replace_conditional_with_polymorphism',
                        'file': str(file_path),
                        'line': node.lineno,
                        'priority': 'high',
                        'reason': "发现基于类型的多分支条件，建议使用多态替代",
                        'steps': [
                            "为每种类型创建子类",
                            "将条件分支逻辑移至对应子类",
                            "使用工厂方法创建实例",
                            "调用统一的接口方法"
                        ]
                    })

        return suggestions

    def _check_parameter_object(self, file_path: Path, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        suggestions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                param_count = len(node.args.args)
                if node.args.kwonlyargs:
                    param_count += len(node.args.kwonlyargs)

                if param_count > 4:
                    related_params = []
                    for arg in node.args.args:
                        if any(prefix in arg.arg.lower() for prefix in ['start', 'end', 'min', 'max', 'from', 'to']):
                            related_params.append(arg.arg)

                    if len(related_params) >= 2:
                        suggestions.append({
                            'type': 'introduce_parameter_object',
                            'file': str(file_path),
                            'line': node.lineno,
                            'function': node.name,
                            'priority': 'medium',
                            'reason': f"函数 {node.name} 有 {param_count} 个参数，其中 {related_params} 相关，建议引入参数对象",
                            'steps': [
                                "创建参数类封装相关参数",
                                "更新函数签名使用参数对象",
                                "更新所有调用点"
                            ]
                        })

        return suggestions

    def _check_magic_numbers(self, file_path: Path, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        suggestions = []

        lines = content.split('\n')
        magic_numbers = {}

        for i, line in enumerate(lines, 1):
            numbers = re.findall(r'(?<!["\'])\b(\d{2,})\b(?!["\'])', line)
            for num in numbers:
                if num not in ['0', '1', '2', '10', '100', '1000']:
                    if num not in magic_numbers:
                        magic_numbers[num] = []
                    magic_numbers[num].append(i)

        for num, line_nums in magic_numbers.items():
            if len(line_nums) >= 2:
                suggestions.append({
                    'type': 'replace_magic_number',
                    'file': str(file_path),
                    'line': line_nums[0],
                    'priority': 'low',
                    'reason': f"魔法数字 {num} 出现 {len(line_nums)} 次，建议提取为常量",
                    'steps': [
                        f"定义常量 MAGIC_NUMBER_{num} = {num}",
                        "用常量替换所有出现位置",
                        "添加注释说明常量含义"
                    ]
                })

        return suggestions[:5]

    def _check_duplicate_code(self, file_path: Path, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        suggestions = []

        lines = content.split('\n')
        seen_blocks = {}

        for i in range(len(lines) - 5):
            block = '\n'.join(lines[i:i + 5])
            normalized = re.sub(r'\s+', ' ', block.strip())
            normalized = re.sub(r'\b\w+\b', 'x', normalized)

            if normalized in seen_blocks:
                original_line = seen_blocks[normalized]
                if abs(original_line - i) > 5:
                    suggestions.append({
                        'type': 'consolidate_duplicate',
                        'file': str(file_path),
                        'line': i + 1,
                        'priority': 'medium',
                        'reason': f"发现重复代码块，与第 {original_line + 1} 行相似",
                        'steps': [
                            "提取重复代码为独立方法",
                            "在两处调用新方法",
                            "确保参数化差异部分"
                        ]
                    })
            else:
                seen_blocks[normalized] = i

        return suggestions[:3]

    def _count_by_type(self, suggestions: List[Dict[str, Any]]) -> Dict[str, int]:
        counts = {}
        for s in suggestions:
            ref_type = s['type']
            counts[ref_type] = counts.get(ref_type, 0) + 1
        return counts

    def _count_by_priority(self, suggestions: List[Dict[str, Any]]) -> Dict[str, int]:
        counts = {'high': 0, 'medium': 0, 'low': 0}
        for s in suggestions:
            priority = s.get('priority', 'low')
            counts[priority] = counts.get(priority, 0) + 1
        return counts
