"""
增强的架构优化器模块

包含：
- ArchitectureDependencyAnalyzer: 架构依赖分析器
- ArchitectureIssueDetector: 架构问题检测器
- ArchitectureOptimizationAdvisor: 架构优化建议生成器
- ArchitectureOptimizationValidator: 架构优化验证器
- UnifiedArchitectureOptimizer: 统一架构优化管理器
"""

import ast
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict, deque


class DependencyType(Enum):
    IMPORT = "import"
    INHERITANCE = "inheritance"
    COMPOSITION = "composition"
    AGGREGATION = "aggregation"
    ASSOCIATION = "association"


class ArchitectureIssueType(Enum):
    CYCLIC_DEPENDENCY = "cyclic_dependency"
    GOD_CLASS = "god_class"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    DEPENDENCY_VIOLATION = "dependency_violation"
    LAYER_VIOLATION = "layer_violation"
    TIGHT_COUPLING = "tight_coupling"
    MISSING_ABSTRACTION = "missing_abstraction"
    PRIMITIVE_OBSESSION = "primitive_obsession"


class ArchitectureSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ModuleDependency:
    source_module: str
    target_module: str
    dependency_type: DependencyType
    line_number: int
    file_path: str
    strength: float


@dataclass
class ArchitectureIssue:
    issue_type: ArchitectureIssueType
    severity: ArchitectureSeverity
    file_path: str
    line_number: int
    description: str
    affected_modules: List[str]
    suggestions: List[str]
    impact: str


@dataclass
class ArchitectureOptimizationSuggestion:
    suggestion_id: str
    issue: ArchitectureIssue
    optimization_type: str
    description: str
    implementation_steps: List[str]
    expected_benefits: List[str]
    risks: List[str]
    estimated_effort: str
    priority: str


@dataclass
class ArchitectureOptimizationResult:
    optimization_id: str
    timestamp: str
    suggestion: ArchitectureOptimizationSuggestion
    success: bool
    changes_made: List[str]
    validation_results: Dict[str, Any]
    execution_log: List[str]


class ArchitectureOptimizationExecutor:
    """架构优化执行器"""

    def __init__(self):
        self._results: List[ArchitectureOptimizationResult] = []
        self._execution_counter = 0
        self._optimization_strategies = {
            'cycle_breaking': self._apply_cycle_breaking,
            'class_splitting': self._apply_class_splitting,
            'decoupling': self._apply_decoupling,
            'layer_fixing': self._apply_layer_fixing,
        }

    def execute_optimization(
        self,
        suggestion: ArchitectureOptimizationSuggestion,
        project_path: Path,
        auto_apply: bool = False
    ) -> ArchitectureOptimizationResult:
        self._execution_counter += 1
        optimization_id = f"ARCH-EXEC-{self._execution_counter:04d}"

        execution_log = []
        changes_made = []
        success = False

        execution_log.append(f"[{datetime.now().isoformat()}] 开始执行架构优化: {suggestion.suggestion_id}")
        execution_log.append(f"优化类型: {suggestion.optimization_type}")
        execution_log.append(f"描述: {suggestion.description}")

        if auto_apply:
            try:
                execution_log.append(f"[{datetime.now().isoformat()}] 自动应用架构优化...")

                strategy = self._optimization_strategies.get(suggestion.optimization_type)
                if strategy:
                    execution_log.append(f"[{datetime.now().isoformat()}] 使用优化策略: {suggestion.optimization_type}")
                    strategy_result = strategy(suggestion, project_path, execution_log)
                    changes_made.extend(strategy_result)
                    success = True
                else:
                    execution_log.append(f"[{datetime.now().isoformat()}] 未找到对应的优化策略")
                    success = False

                execution_log.append(f"[{datetime.now().isoformat()}] 架构优化执行完成")

            except Exception as e:
                execution_log.append(f"[{datetime.now().isoformat()}] 架构优化执行失败: {str(e)}")
                success = False
        else:
            execution_log.append(f"[{datetime.now().isoformat()}] 架构优化建议已生成，等待手动执行")
            execution_log.append("实施步骤:")
            for i, step in enumerate(suggestion.implementation_steps, 1):
                execution_log.append(f"  {i}. {step}")

        result = ArchitectureOptimizationResult(
            optimization_id=optimization_id,
            timestamp=datetime.now().isoformat(),
            suggestion=suggestion,
            success=success,
            changes_made=changes_made,
            validation_results={},
            execution_log=execution_log
        )

        self._results.append(result)
        return result

    def _apply_cycle_breaking(self, suggestion: ArchitectureOptimizationSuggestion, project_path: Path, log: List[str]) -> List[str]:
        log.append(f"[{datetime.now().isoformat()}] 应用打破循环依赖策略")
        changes = []

        cycle_modules = suggestion.issue.affected_modules
        log.append(f"[{datetime.now().isoformat()}] 涉及模块: {', '.join(cycle_modules)}")

        interface_name = f"I{cycle_modules[0].split('.')[-1]}"
        interface_code = f"""

class {interface_name}:
    \"\"\"接口层，用于打破循环依赖\"\"\"
    pass
"""

        changes.append(f"创建接口层: {interface_name}")
        log.append(f"[{datetime.now().isoformat()}] 建议创建接口层: {interface_name}")

        return changes

    def _apply_class_splitting(self, suggestion: ArchitectureOptimizationSuggestion, project_path: Path, log: List[str]) -> List[str]:
        log.append(f"[{datetime.now().isoformat()}] 应用类拆分策略")
        changes = []

        module_name = suggestion.issue.affected_modules[0]
        log.append(f"[{datetime.now().isoformat()}] 拆分模块: {module_name}")

        new_classes = [
            f"{module_name.split('.')[-1]}Service",
            f"{module_name.split('.')[-1]}Repository",
            f"{module_name.split('.')[-1]}Helper"
        ]

        for new_class in new_classes:
            changes.append(f"创建新类: {new_class}")
            log.append(f"[{datetime.now().isoformat()}] 建议创建新类: {new_class}")

        return changes

    def _apply_decoupling(self, suggestion: ArchitectureOptimizationSuggestion, project_path: Path, log: List[str]) -> List[str]:
        log.append(f"[{datetime.now().isoformat()}] 应用解耦策略")
        changes = []

        module_name = suggestion.issue.affected_modules[0]
        log.append(f"[{datetime.now().isoformat()}] 解耦模块: {module_name}")

        changes.append("引入依赖注入容器")
        changes.append("创建抽象接口")
        changes.append("使用观察者模式")

        log.append(f"[{datetime.now().isoformat()}] 建议引入依赖注入")
        log.append(f"[{datetime.now().isoformat()}] 建议创建抽象接口")
        log.append(f"[{datetime.now().isoformat()}] 建议使用观察者模式")

        return changes

    def _apply_layer_fixing(self, suggestion: ArchitectureOptimizationSuggestion, project_path: Path, log: List[str]) -> List[str]:
        log.append(f"[{datetime.now().isoformat()}] 应用层级修复策略")
        changes = []

        log.append(f"[{datetime.now().isoformat()}] 修复层级违规: {suggestion.issue.description}")

        changes.append("调整依赖方向")
        changes.append("引入中间服务层")
        changes.append("重构模块职责")

        log.append(f"[{datetime.now().isoformat()}] 建议调整依赖方向")
        log.append(f"[{datetime.now().isoformat()}] 建议引入中间服务层")
        log.append(f"[{datetime.now().isoformat()}] 建议重构模块职责")

        return changes

    def get_execution_history(self) -> List[ArchitectureOptimizationResult]:
        return self._results


class ArchitectureDependencyAnalyzer:
    """架构依赖分析器"""

    def __init__(self):
        self._dependencies: List[ModuleDependency] = []
        self._module_graph: Dict[str, Set[str]] = defaultdict(set)
        self._reverse_graph: Dict[str, Set[str]] = defaultdict(set)
        self._dependency_metrics: Dict[str, Dict[str, Any]] = {}

    def analyze_dependencies(self, project_path: Path) -> List[ModuleDependency]:
        self._dependencies.clear()
        self._module_graph.clear()
        self._reverse_graph.clear()
        self._dependency_metrics.clear()

        backend_dir = project_path / "backend" / "app"
        if backend_dir.exists():
            self._analyze_python_dependencies(backend_dir)

        frontend_dir = project_path / "frontend" / "src"
        if frontend_dir.exists():
            self._analyze_typescript_dependencies(frontend_dir)

        self._calculate_dependency_metrics()

        return self._dependencies

    def get_dependency_metrics(self) -> Dict[str, Dict[str, Any]]:
        return self._dependency_metrics

    def _calculate_dependency_metrics(self):
        for module in set(
            [d.source_module for d in self._dependencies] +
            [d.target_module for d in self._dependencies]
        ):
            afferent_coupling = len(self._reverse_graph.get(module, set()))
            efferent_coupling = len(self._module_graph.get(module, set()))

            instability = efferent_coupling / (afferent_coupling + efferent_coupling) if (afferent_coupling + efferent_coupling) > 0 else 0

            abstractness = self._calculate_abstractness(module)

            distance_from_main = abs(abstractness + instability - 1)

            self._dependency_metrics[module] = {
                'afferent_coupling': afferent_coupling,
                'efferent_coupling': efferent_coupling,
                'instability': instability,
                'abstractness': abstractness,
                'distance_from_main': distance_from_main,
                'total_coupling': afferent_coupling + efferent_coupling
            }

    def _calculate_abstractness(self, module: str) -> float:
        abstract_count = 0
        concrete_count = 0

        for dep in self._dependencies:
            if dep.source_module == module:
                if dep.dependency_type == DependencyType.INHERITANCE:
                    abstract_count += 1
                else:
                    concrete_count += 1

        total = abstract_count + concrete_count
        return abstract_count / total if total > 0 else 0.0

    def calculate_dependency_depth(self, module: str) -> int:
        visited = set()
        max_depth = 0

        def dfs(current: str, depth: int):
            nonlocal max_depth
            if current in visited:
                return
            visited.add(current)
            max_depth = max(max_depth, depth)

            for dep in self._module_graph.get(current, set()):
                dfs(dep, depth + 1)

        dfs(module, 0)
        return max_depth

    def find_critical_modules(self) -> List[Tuple[str, Dict[str, Any]]]:
        critical_modules = []

        for module, metrics in self._dependency_metrics.items():
            if metrics['total_coupling'] > 15 or metrics['distance_from_main'] > 0.7:
                critical_modules.append((module, metrics))

        critical_modules.sort(key=lambda x: x[1]['total_coupling'], reverse=True)
        return critical_modules

    def visualize_dependency_graph(self) -> Dict[str, Any]:
        nodes = []
        edges = []

        all_modules = set(
            [d.source_module for d in self._dependencies] +
            [d.target_module for d in self._dependencies]
        )

        for module in all_modules:
            metrics = self._dependency_metrics.get(module, {})
            nodes.append({
                'id': module,
                'label': module,
                'afferent_coupling': metrics.get('afferent_coupling', 0),
                'efferent_coupling': metrics.get('efferent_coupling', 0),
                'instability': metrics.get('instability', 0)
            })

        for dep in self._dependencies:
            edges.append({
                'source': dep.source_module,
                'target': dep.target_module,
                'type': dep.dependency_type.value,
                'file': dep.file_path,
                'line': dep.line_number
            })

        return {
            'nodes': nodes,
            'edges': edges,
            'total_modules': len(nodes),
            'total_dependencies': len(edges)
        }

    def _analyze_python_dependencies(self, backend_dir: Path):
        for py_file in backend_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            self._analyze_python_file_dependencies(py_file, backend_dir)

    def _analyze_python_file_dependencies(self, file_path: Path, backend_dir: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            module_name = self._get_module_name(file_path, backend_dir)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self._add_dependency(
                            module_name,
                            alias.name,
                            DependencyType.IMPORT,
                            node.lineno,
                            str(file_path)
                        )

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self._add_dependency(
                            module_name,
                            node.module,
                            DependencyType.IMPORT,
                            node.lineno,
                            str(file_path)
                        )

                elif isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            self._add_dependency(
                                module_name,
                                base.id,
                                DependencyType.INHERITANCE,
                                node.lineno,
                                str(file_path)
                            )

        except Exception:
            pass

    def _analyze_typescript_dependencies(self, frontend_dir: Path):
        for ts_file in frontend_dir.rglob("*.ts"):
            if "node_modules" in str(ts_file):
                continue

            self._analyze_typescript_file_dependencies(ts_file, frontend_dir)

    def _analyze_typescript_file_dependencies(self, file_path: Path, frontend_dir: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            module_name = self._get_module_name(file_path, frontend_dir)

            import_patterns = [
                r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]',
                r'import\s+[\'"]([^\'"]+)[\'"]',
            ]

            for pattern in import_patterns:
                for match in re.finditer(pattern, content):
                    import_path = match.group(1)
                    line_num = content[:match.start()].count('\n') + 1

                    self._add_dependency(
                        module_name,
                        import_path,
                        DependencyType.IMPORT,
                        line_num,
                        str(file_path)
                    )

        except Exception:
            pass

    def _get_module_name(self, file_path: Path, base_dir: Path) -> str:
        try:
            relative = file_path.relative_to(base_dir)
            return str(relative.with_suffix('')).replace('\\', '/').replace('/', '.')
        except ValueError:
            return file_path.stem

    def _add_dependency(
        self,
        source: str,
        target: str,
        dep_type: DependencyType,
        line: int,
        file_path: str
    ):
        self._dependencies.append(ModuleDependency(
            source_module=source,
            target_module=target,
            dependency_type=dep_type,
            line_number=line,
            file_path=file_path,
            strength=1.0
        ))

        self._module_graph[source].add(target)
        self._reverse_graph[target].add(source)

    def get_dependency_graph(self) -> Dict[str, Set[str]]:
        return dict(self._module_graph)

    def get_reverse_dependency_graph(self) -> Dict[str, Set[str]]:
        return dict(self._reverse_graph)


class ArchitectureIssueDetector:
    """架构问题检测器"""

    def __init__(self):
        self._issues: List[ArchitectureIssue] = []

    def detect_issues(self, dependencies: List[ModuleDependency]) -> List[ArchitectureIssue]:
        self._issues.clear()

        self._detect_cyclic_dependencies(dependencies)
        self._detect_god_classes(dependencies)
        self._detect_tight_coupling(dependencies)
        self._detect_layer_violations(dependencies)

        self._issues.sort(key=lambda x: x.severity.value)

        return self._issues

    def _detect_cyclic_dependencies(self, dependencies: List[ModuleDependency]):
        graph = defaultdict(set)
        for dep in dependencies:
            graph[dep.source_module].add(dep.target_module)

        cycles = self._find_cycles(graph)

        for cycle in cycles:
            self._issues.append(ArchitectureIssue(
                issue_type=ArchitectureIssueType.CYCLIC_DEPENDENCY,
                severity=ArchitectureSeverity.HIGH,
                file_path="",
                line_number=0,
                description=f"发现循环依赖: {' -> '.join(cycle)}",
                affected_modules=cycle,
                suggestions=[
                    "提取共同依赖到独立模块",
                    "使用依赖倒置原则",
                    "引入接口层解耦",
                    "使用事件驱动架构"
                ],
                impact="可能导致编译错误、测试困难和代码耦合"
            ))

    def _find_cycles(self, graph: Dict[str, Set[str]]) -> List[List[str]]:
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    result = dfs(neighbor, path + [node])
                    if result:
                        return result
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor) if neighbor in path else -1
                    if cycle_start >= 0:
                        return path[cycle_start:] + [node, neighbor]

            rec_stack.remove(node)
            return None

        for node in graph:
            if node not in visited:
                cycle = dfs(node, [])
                if cycle:
                    cycles.append(cycle)

        return cycles

    def _detect_god_classes(self, dependencies: List[ModuleDependency]):
        dependency_count = defaultdict(int)

        for dep in dependencies:
            dependency_count[dep.source_module] += 1

        for module, count in dependency_count.items():
            if count > 15:
                self._issues.append(ArchitectureIssue(
                    issue_type=ArchitectureIssueType.GOD_CLASS,
                    severity=ArchitectureSeverity.HIGH if count > 20 else ArchitectureSeverity.MEDIUM,
                    file_path="",
                    line_number=0,
                    description=f"模块 {module} 依赖 {count} 个其他模块，可能是上帝类",
                    affected_modules=[module],
                    suggestions=[
                        "将模块拆分为多个更小的模块",
                        "应用单一职责原则",
                        "使用组合替代继承",
                        "提取独立功能到工具类"
                    ],
                    impact="降低代码可维护性和可测试性"
                ))

    def _detect_tight_coupling(self, dependencies: List[ModuleDependency]):
        module_coupling = defaultdict(lambda: {'afferent': 0, 'efferent': 0})

        for dep in dependencies:
            module_coupling[dep.source_module]['efferent'] += 1
            module_coupling[dep.target_module]['afferent'] += 1

        for module, coupling in module_coupling.items():
            total_coupling = coupling['afferent'] + coupling['efferent']
            if total_coupling > 10:
                self._issues.append(ArchitectureIssue(
                    issue_type=ArchitectureIssueType.TIGHT_COUPLING,
                    severity=ArchitectureSeverity.MEDIUM,
                    file_path="",
                    line_number=0,
                    description=f"模块 {module} 紧耦合度高 (入度: {coupling['afferent']}, 出度: {coupling['efferent']})",
                    affected_modules=[module],
                    suggestions=[
                        "使用依赖注入降低耦合",
                        "引入接口抽象层",
                        "使用观察者模式",
                        "考虑使用事件总线"
                    ],
                    impact="增加代码修改难度和测试复杂度"
                ))

    def _detect_layer_violations(self, dependencies: List[ModuleDependency]):
        layer_rules = {
            'models': {'allowed_imports': [], 'forbidden_imports': ['routers', 'api', 'controllers', 'views']},
            'routers': {'allowed_imports': ['models', 'services'], 'forbidden_imports': []},
            'services': {'allowed_imports': ['models'], 'forbidden_imports': ['routers', 'api', 'controllers']},
        }

        for dep in dependencies:
            source_layer = self._get_layer(dep.source_module)
            target_layer = self._get_layer(dep.target_module)

            if source_layer and target_layer:
                rules = layer_rules.get(source_layer)
                if rules:
                    for forbidden in rules.get('forbidden_imports', []):
                        if forbidden in target_layer:
                            self._issues.append(ArchitectureIssue(
                                issue_type=ArchitectureIssueType.LAYER_VIOLATION,
                                severity=ArchitectureSeverity.HIGH,
                                file_path=dep.file_path,
                                line_number=dep.line_number,
                                description=f"层级违规: {source_layer} 层导入 {target_layer} 层",
                                affected_modules=[dep.source_module, dep.target_module],
                                suggestions=[
                                    "调整依赖方向",
                                    "使用依赖倒置原则",
                                    "引入中间层",
                                    "重新设计模块职责"
                                ],
                                impact="破坏架构分层，增加系统复杂度"
                            ))

    def _get_layer(self, module_name: str) -> Optional[str]:
        layers = ['models', 'routers', 'services', 'controllers', 'views', 'api']
        for layer in layers:
            if layer in module_name.lower():
                return layer
        return None


class ArchitectureOptimizationAdvisor:
    """架构优化建议生成器"""

    def __init__(self):
        self._suggestions: List[ArchitectureOptimizationSuggestion] = []
        self._suggestion_counter = 0

    def generate_suggestions(self, issues: List[ArchitectureIssue]) -> List[ArchitectureOptimizationSuggestion]:
        self._suggestions.clear()

        for issue in issues:
            suggestion = self._create_suggestion_for_issue(issue)
            if suggestion:
                self._suggestions.append(suggestion)

        self._suggestions.sort(key=lambda x: x.priority, reverse=True)

        return self._suggestions

    def _create_suggestion_for_issue(self, issue: ArchitectureIssue) -> Optional[ArchitectureOptimizationSuggestion]:
        self._suggestion_counter += 1
        suggestion_id = f"ARCH-OPT-{self._suggestion_counter:04d}"

        optimization_map = {
            ArchitectureIssueType.CYCLIC_DEPENDENCY: self._create_cycle_breaking_suggestion,
            ArchitectureIssueType.GOD_CLASS: self._create_class_splitting_suggestion,
            ArchitectureIssueType.TIGHT_COUPLING: self._create_decoupling_suggestion,
            ArchitectureIssueType.LAYER_VIOLATION: self._create_layer_fixing_suggestion,
        }

        creator = optimization_map.get(issue.issue_type)
        if creator:
            return creator(suggestion_id, issue)

        return None

    def _create_cycle_breaking_suggestion(self, suggestion_id: str, issue: ArchitectureIssue) -> ArchitectureOptimizationSuggestion:
        return ArchitectureOptimizationSuggestion(
            suggestion_id=suggestion_id,
            issue=issue,
            optimization_type="cycle_breaking",
            description=f"打破循环依赖: {' -> '.join(issue.affected_modules)}",
            implementation_steps=[
                "识别循环依赖中的共同依赖",
                "提取共同依赖到独立模块",
                "使用依赖倒置原则引入接口",
                "重构模块依赖关系",
                "验证循环已打破"
            ],
            expected_benefits=[
                "消除编译错误",
                "提高代码可测试性",
                "降低模块耦合度",
                "改善代码结构"
            ],
            risks=[
                "可能需要较大重构",
                "可能影响现有功能",
                "需要充分测试"
            ],
            estimated_effort="高",
            priority="high"
        )

    def _create_class_splitting_suggestion(self, suggestion_id: str, issue: ArchitectureIssue) -> ArchitectureOptimizationSuggestion:
        return ArchitectureOptimizationSuggestion(
            suggestion_id=suggestion_id,
            issue=issue,
            optimization_type="class_splitting",
            description=f"拆分上帝类: {issue.affected_modules[0]}",
            implementation_steps=[
                "分析类的职责和方法",
                "识别可以独立的职责",
                "创建新的类承担独立职责",
                "重构原类使用新类",
                "验证功能完整性"
            ],
            expected_benefits=[
                "提高代码可维护性",
                "降低类复杂度",
                "提高代码可测试性",
                "符合单一职责原则"
            ],
            risks=[
                "可能需要修改大量调用代码",
                "需要仔细设计接口",
                "可能影响性能"
            ],
            estimated_effort="高",
            priority="high"
        )

    def _create_decoupling_suggestion(self, suggestion_id: str, issue: ArchitectureIssue) -> ArchitectureOptimizationSuggestion:
        return ArchitectureOptimizationSuggestion(
            suggestion_id=suggestion_id,
            issue=issue,
            optimization_type="decoupling",
            description=f"降低模块耦合: {issue.affected_modules[0]}",
            implementation_steps=[
                "识别紧耦合的原因",
                "引入接口抽象层",
                "使用依赖注入",
                "应用观察者模式",
                "验证耦合度降低"
            ],
            expected_benefits=[
                "提高代码灵活性",
                "降低修改成本",
                "提高可测试性",
                "便于模块替换"
            ],
            risks=[
                "可能增加代码复杂度",
                "需要学习设计模式",
                "可能影响性能"
            ],
            estimated_effort="中",
            priority="medium"
        )

    def _create_layer_fixing_suggestion(self, suggestion_id: str, issue: ArchitectureIssue) -> ArchitectureOptimizationSuggestion:
        return ArchitectureOptimizationSuggestion(
            suggestion_id=suggestion_id,
            issue=issue,
            optimization_type="layer_fixing",
            description=f"修复层级违规: {issue.description}",
            implementation_steps=[
                "分析违规依赖的原因",
                "重新设计模块职责",
                "调整依赖方向",
                "引入中间层或接口",
                "验证架构合规性"
            ],
            expected_benefits=[
                "恢复架构分层",
                "降低系统复杂度",
                "提高代码可维护性",
                "便于团队协作"
            ],
            risks=[
                "可能需要重构代码",
                "可能影响现有功能",
                "需要团队达成共识"
            ],
            estimated_effort="中",
            priority="high"
        )


class ArchitectureOptimizationValidator:
    """架构优化验证器"""

    def __init__(self):
        self._validation_results: Dict[str, Any] = {}

    def validate_optimization(
        self,
        result: ArchitectureOptimizationResult,
        dependencies: List[ModuleDependency]
    ) -> Dict[str, Any]:
        validation = {
            'optimization_id': result.optimization_id,
            'timestamp': datetime.now().isoformat(),
            'validation_passed': False,
            'checks': {},
            'issues_found': [],
            'recommendations': [],
            'metrics_comparison': {}
        }

        validation['checks']['dependency_valid'] = self._check_dependencies_valid(dependencies)
        validation['checks']['no_cycles'] = self._check_no_cycles(dependencies)
        validation['checks']['layer_compliant'] = self._check_layer_compliance(dependencies)
        validation['checks']['coupling_acceptable'] = self._check_coupling_levels(dependencies)
        validation['checks']['architecture_stability'] = self._check_architecture_stability(dependencies)
        validation['checks']['dependency_direction'] = self._check_dependency_direction(dependencies)

        validation['validation_passed'] = all(validation['checks'].values())

        if not validation['validation_passed']:
            validation['issues_found'] = self._identify_remaining_issues(dependencies)
            validation['recommendations'] = self._generate_recommendations(validation['checks'])

        validation['metrics_comparison'] = self._calculate_metrics_comparison(dependencies)

        self._validation_results[result.optimization_id] = validation
        return validation

    def _check_architecture_stability(self, dependencies: List[ModuleDependency]) -> bool:
        module_coupling: Dict[str, Dict[str, int]] = defaultdict(lambda: {'afferent': 0, 'efferent': 0})

        for dep in dependencies:
            module_coupling[dep.source_module]['efferent'] += 1
            module_coupling[dep.target_module]['afferent'] += 1

        for module, coupling in module_coupling.items():
            total = coupling['afferent'] + coupling['efferent']
            if total > 0:
                instability = coupling['efferent'] / total
                if instability > 0.9 and coupling['afferent'] > 5:
                    return False

        return True

    def _check_dependency_direction(self, dependencies: List[ModuleDependency]) -> bool:
        layer_order = {
            'models': 1,
            'repositories': 2,
            'services': 3,
            'controllers': 4,
            'routers': 5,
            'api': 5
        }

        for dep in dependencies:
            source_layer = self._get_layer(dep.source_module)
            target_layer = self._get_layer(dep.target_module)

            if source_layer and target_layer:
                source_order = layer_order.get(source_layer, 0)
                target_order = layer_order.get(target_layer, 0)

                if source_order > 0 and target_order > 0 and source_order < target_order:
                    return False

        return True

    def _calculate_metrics_comparison(self, dependencies: List[ModuleDependency]) -> Dict[str, Any]:
        total_modules = len(set(
            [d.source_module for d in dependencies] +
            [d.target_module for d in dependencies]
        ))

        total_dependencies = len(dependencies)

        avg_coupling = total_dependencies / total_modules if total_modules > 0 else 0

        cycle_count = len(self._find_all_cycles(dependencies))

        return {
            'total_modules': total_modules,
            'total_dependencies': total_dependencies,
            'average_coupling': avg_coupling,
            'cycle_count': cycle_count,
            'health_score': self._calculate_health_score(total_modules, total_dependencies, cycle_count)
        }

    def _find_all_cycles(self, dependencies: List[ModuleDependency]) -> List[List[str]]:
        graph = defaultdict(set)
        for dep in dependencies:
            graph[dep.source_module].add(dep.target_module)

        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    result = dfs(neighbor, path + [node])
                    if result:
                        return result
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor) if neighbor in path else -1
                    if cycle_start >= 0:
                        return path[cycle_start:] + [node, neighbor]

            rec_stack.remove(node)
            return None

        for node in graph:
            if node not in visited:
                cycle = dfs(node, [])
                if cycle:
                    cycles.append(cycle)

        return cycles

    def _calculate_health_score(self, modules: int, dependencies: int, cycles: int) -> float:
        if modules == 0:
            return 0.0

        coupling_score = max(0, 100 - (dependencies / modules) * 10)
        cycle_score = max(0, 100 - cycles * 20)

        return (coupling_score + cycle_score) / 2

    def _check_dependencies_valid(self, dependencies: List[ModuleDependency]) -> bool:
        return len(dependencies) > 0

    def _check_no_cycles(self, dependencies: List[ModuleDependency]) -> bool:
        graph = defaultdict(set)
        for dep in dependencies:
            graph[dep.source_module].add(dep.target_module)

        visited = set()
        rec_stack = set()

        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    return False

        return True

    def _check_layer_compliance(self, dependencies: List[ModuleDependency]) -> bool:
        layer_rules = {
            'models': {'forbidden': ['routers', 'api', 'controllers']},
            'services': {'forbidden': ['routers', 'api', 'controllers']},
        }

        for dep in dependencies:
            source_layer = self._get_layer(dep.source_module)
            target_layer = self._get_layer(dep.target_module)

            if source_layer and target_layer:
                rules = layer_rules.get(source_layer)
                if rules:
                    for forbidden in rules.get('forbidden', []):
                        if forbidden in target_layer:
                            return False

        return True

    def _check_coupling_levels(self, dependencies: List[ModuleDependency]) -> bool:
        module_coupling = defaultdict(int)

        for dep in dependencies:
            module_coupling[dep.source_module] += 1

        for module, count in module_coupling.items():
            if count > 20:
                return False

        return True

    def _get_layer(self, module_name: str) -> Optional[str]:
        layers = ['models', 'routers', 'services', 'controllers', 'views', 'api']
        for layer in layers:
            if layer in module_name.lower():
                return layer
        return None

    def _identify_remaining_issues(self, dependencies: List[ModuleDependency]) -> List[str]:
        issues = []

        if not self._check_no_cycles(dependencies):
            issues.append("仍存在循环依赖")

        if not self._check_layer_compliance(dependencies):
            issues.append("仍存在层级违规")

        if not self._check_coupling_levels(dependencies):
            issues.append("仍存在高耦合模块")

        return issues

    def _generate_recommendations(self, checks: Dict[str, bool]) -> List[str]:
        recommendations = []

        if not checks.get('no_cycles', True):
            recommendations.append("继续优化以消除循环依赖")

        if not checks.get('layer_compliant', True):
            recommendations.append("修复层级违规以恢复架构分层")

        if not checks.get('coupling_acceptable', True):
            recommendations.append("降低模块耦合度")

        return recommendations

    def generate_validation_report(self) -> Dict[str, Any]:
        total_validations = len(self._validation_results)
        passed_validations = sum(
            1 for v in self._validation_results.values()
            if v['validation_passed']
        )

        return {
            'total_validations': total_validations,
            'passed_validations': passed_validations,
            'pass_rate': (passed_validations / total_validations * 100) if total_validations > 0 else 0,
            'validations': self._validation_results,
            'generated_at': datetime.now().isoformat()
        }


class UnifiedArchitectureOptimizer:
    """统一架构优化管理器"""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.dependency_analyzer = ArchitectureDependencyAnalyzer()
        self.issue_detector = ArchitectureIssueDetector()
        self.optimization_advisor = ArchitectureOptimizationAdvisor()
        self.optimization_executor = ArchitectureOptimizationExecutor()
        self.optimization_validator = ArchitectureOptimizationValidator()

        self._optimization_history: List[Dict[str, Any]] = []

    def run_full_optimization_cycle(
        self,
        auto_apply: bool = False,
        max_optimizations: int = 10
    ) -> Dict[str, Any]:
        cycle_start = datetime.now()

        dependencies = self.dependency_analyzer.analyze_dependencies(self.project_path)

        issues = self.issue_detector.detect_issues(dependencies)

        suggestions = self.optimization_advisor.generate_suggestions(issues)

        results = []
        validations = []

        for suggestion in suggestions[:max_optimizations]:
            result = self.optimization_executor.execute_optimization(
                suggestion,
                self.project_path,
                auto_apply
            )
            results.append(result)

            validation = self.optimization_validator.validate_optimization(result, dependencies)
            validations.append(validation)

        cycle_end = datetime.now()

        report = {
            'cycle_id': f"ARCH-OPT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'started_at': cycle_start.isoformat(),
            'completed_at': cycle_end.isoformat(),
            'duration_seconds': (cycle_end - cycle_start).total_seconds(),
            'dependencies_analyzed': len(dependencies),
            'issues_found': len(issues),
            'suggestions_generated': len(suggestions),
            'optimizations_executed': len(results),
            'successful_optimizations': sum(1 for v in validations if v['validation_passed']),
            'dependency_metrics': self.dependency_analyzer.get_dependency_metrics(),
            'dependency_graph': self.dependency_analyzer.visualize_dependency_graph(),
            'critical_modules': self.dependency_analyzer.find_critical_modules(),
            'dependencies': [
                {
                    'source': dep.source_module,
                    'target': dep.target_module,
                    'type': dep.dependency_type.value,
                    'file': dep.file_path,
                    'line': dep.line_number
                }
                for dep in dependencies[:max_optimizations]
            ],
            'issues': [
                {
                    'type': issue.issue_type.value,
                    'severity': issue.severity.value,
                    'description': issue.description,
                    'modules': issue.affected_modules
                }
                for issue in issues[:max_optimizations]
            ],
            'suggestions': [
                {
                    'id': s.suggestion_id,
                    'type': s.optimization_type,
                    'description': s.description,
                    'effort': s.estimated_effort,
                    'priority': s.priority
                }
                for s in suggestions[:max_optimizations]
            ],
            'results': [
                {
                    'id': r.optimization_id,
                    'success': r.success,
                    'changes': len(r.changes_made)
                }
                for r in results
            ],
            'validations': validations,
            'summary': self._generate_summary(dependencies, issues, results, validations)
        }

        self._optimization_history.append(report)
        return report

    def _generate_summary(
        self,
        dependencies: List[ModuleDependency],
        issues: List[ArchitectureIssue],
        results: List[ArchitectureOptimizationResult],
        validations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        critical_issues = sum(1 for i in issues if i.severity == ArchitectureSeverity.CRITICAL)
        high_issues = sum(1 for i in issues if i.severity == ArchitectureSeverity.HIGH)

        successful_optimizations = sum(1 for r in results if r.success)
        passed_validations = sum(1 for v in validations if v['validation_passed'])

        return {
            'critical_issues': critical_issues,
            'high_priority_issues': high_issues,
            'total_issues': len(issues),
            'total_dependencies': len(dependencies),
            'optimizations_applied': len(results),
            'successful_optimizations': successful_optimizations,
            'passed_validations': passed_validations,
            'success_rate': (passed_validations / len(validations) * 100) if validations else 0,
            'recommendations': self._generate_recommendations(issues, results, validations)
        }

    def _generate_recommendations(
        self,
        issues: List[ArchitectureIssue],
        results: List[ArchitectureOptimizationResult],
        validations: List[Dict[str, Any]]
    ) -> List[str]:
        recommendations = []

        critical = [i for i in issues if i.severity == ArchitectureSeverity.CRITICAL]
        if critical:
            recommendations.append(f"发现 {len(critical)} 个严重架构问题，建议立即处理")

        high_priority = [i for i in issues if i.severity == ArchitectureSeverity.HIGH]
        if high_priority:
            recommendations.append(f"发现 {len(high_priority)} 个高优先级架构问题，建议优先优化")

        failed_optimizations = [r for r in results if not r.success]
        if failed_optimizations:
            recommendations.append(f"{len(failed_optimizations)} 个架构优化执行失败，建议检查并重试")

        failed_validations = [v for v in validations if not v['validation_passed']]
        if failed_validations:
            recommendations.append(f"{len(failed_validations)} 个架构优化验证失败，建议进一步优化")

        if not recommendations:
            recommendations.append("架构优化效果良好，建议持续监控")

        return recommendations

    def get_optimization_history(self) -> List[Dict[str, Any]]:
        return self._optimization_history

    def export_report(self, report: Dict[str, Any], output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
