"""
脚本分类管理模块
提供脚本自动分类、依赖分析、迁移建议和报告生成功能
"""

import ast
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from skillscripts.core.path_config_center import get_path_config


class ScriptCategory(Enum):
    PIPELINE = "pipeline"
    TEST = "test"
    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"
    REQUIREMENTS = "requirements"
    UTILS = "utils"
    CORE = "core"
    UNKNOWN = "unknown"


class MigrationPriority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass
class ImportInfo:
    module_name: str
    import_type: str
    alias: Optional[str] = None
    imported_names: List[str] = field(default_factory=list)
    is_local: bool = False
    line_number: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_name": self.module_name,
            "import_type": self.import_type,
            "alias": self.alias,
            "imported_names": self.imported_names,
            "is_local": self.is_local,
            "line_number": self.line_number
        }


@dataclass
class ScriptInfo:
    file_path: Path
    category: ScriptCategory
    suggested_category: Optional[ScriptCategory] = None
    imports: List[ImportInfo] = field(default_factory=list)
    local_imports: List[ImportInfo] = field(default_factory=list)
    external_imports: List[ImportInfo] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    lines_count: int = 0
    needs_migration: bool = False
    migration_priority: MigrationPriority = MigrationPriority.NONE
    migration_reason: str = ""
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": str(self.file_path),
            "category": self.category.value,
            "suggested_category": self.suggested_category.value if self.suggested_category else None,
            "imports": [imp.to_dict() for imp in self.imports],
            "local_imports": [imp.to_dict() for imp in self.local_imports],
            "external_imports": [imp.to_dict() for imp in self.external_imports],
            "functions": self.functions,
            "classes": self.classes,
            "docstring": self.docstring,
            "lines_count": self.lines_count,
            "needs_migration": self.needs_migration,
            "migration_priority": self.migration_priority.value,
            "migration_reason": self.migration_reason,
            "dependencies": list(self.dependencies),
            "dependents": list(self.dependents)
        }


@dataclass
class DependencyEdge:
    source: str
    target: str
    import_info: ImportInfo
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "import_info": self.import_info.to_dict()
        }


@dataclass
class CycleInfo:
    nodes: List[str]
    edges: List[DependencyEdge]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": self.nodes,
            "edges": [edge.to_dict() for edge in self.edges]
        }


@dataclass
class MigrationSuggestion:
    script_path: Path
    current_category: ScriptCategory
    suggested_category: ScriptCategory
    priority: MigrationPriority
    reason: str
    affected_scripts: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "script_path": str(self.script_path),
            "current_category": self.current_category.value,
            "suggested_category": self.suggested_category.value,
            "priority": self.priority.value,
            "reason": self.reason,
            "affected_scripts": self.affected_scripts
        }


@dataclass
class ClassificationReport:
    generated_at: str
    total_scripts: int
    category_counts: Dict[str, int]
    scripts: Dict[str, ScriptInfo]
    dependency_graph: Dict[str, List[str]]
    cycles: List[CycleInfo]
    isolated_scripts: List[str]
    migration_suggestions: List[MigrationSuggestion]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "total_scripts": self.total_scripts,
            "category_counts": self.category_counts,
            "scripts": {k: v.to_dict() for k, v in self.scripts.items()},
            "dependency_graph": self.dependency_graph,
            "cycles": [c.to_dict() for c in self.cycles],
            "isolated_scripts": self.isolated_scripts,
            "migration_suggestions": [s.to_dict() for s in self.migration_suggestions]
        }


class ClassificationRules:
    DEFAULT_KEYWORDS: Dict[ScriptCategory, List[str]] = {
        ScriptCategory.PIPELINE: [
            "pipeline", "orchestrat", "workflow", "automat", "tdd", "sdd",
            "integrat", "deploy", "build", "ci", "cd"
        ],
        ScriptCategory.TEST: [
            "test", "spec", "coverage", "pytest", "unittest", "mock",
            "assert", "fixture", "benchmark", "regression"
        ],
        ScriptCategory.ANALYSIS: [
            "analy", "detect", "check", "validat", "inspect", "scan",
            "report", "metric", "quality", "smell", "debt"
        ],
        ScriptCategory.OPTIMIZATION: [
            "optim", "refactor", "improve", "enhance", "fix", "repair",
            "tune", "perform"
        ],
        ScriptCategory.REQUIREMENTS: [
            "requirement", "spec", "trace", "business", "rule", "feature",
            "user_story", "acceptance"
        ],
        ScriptCategory.UTILS: [
            "util", "helper", "common", "shared", "tool", "manager",
            "handler", "converter", "formatter"
        ],
        ScriptCategory.CORE: [
            "core", "main", "init", "config", "service", "server",
            "start", "stop", "health", "docker", "environment"
        ]
    }
    
    DEFAULT_IMPORT_PATTERNS: Dict[ScriptCategory, List[str]] = {
        ScriptCategory.TEST: [
            "pytest", "unittest", "mock", "hypothesis", "coverage"
        ],
        ScriptCategory.PIPELINE: [
            "celery", "airflow", "prefect", "luigi", "dag"
        ],
        ScriptCategory.ANALYSIS: [
            "radon", "pylint", "flake8", "mypy", "bandit"
        ],
        ScriptCategory.OPTIMIZATION: [
            "refactor", "optimize"
        ],
        ScriptCategory.CORE: [
            "fastapi", "flask", "django", "uvicorn", "gunicorn"
        ]
    }
    
    DEFAULT_FUNCTION_PATTERNS: Dict[ScriptCategory, List[str]] = {
        ScriptCategory.TEST: [
            "test_", "_test", "setup", "teardown", "given", "when", "then"
        ],
        ScriptCategory.PIPELINE: [
            "run_pipeline", "execute", "orchestrate", "schedule"
        ],
        ScriptCategory.ANALYSIS: [
            "analyze", "detect", "check", "validate", "inspect"
        ],
        ScriptCategory.OPTIMIZATION: [
            "optimize", "refactor", "improve", "fix", "repair"
        ],
        ScriptCategory.CORE: [
            "main", "run", "start", "stop", "init", "configure"
        ]
    }
    
    def __init__(
        self,
        custom_keywords: Optional[Dict[ScriptCategory, List[str]]] = None,
        custom_import_patterns: Optional[Dict[ScriptCategory, List[str]]] = None,
        custom_function_patterns: Optional[Dict[ScriptCategory, List[str]]] = None
    ):
        self.keywords = self._merge_dicts(
            self.DEFAULT_KEYWORDS,
            custom_keywords or {}
        )
        self.import_patterns = self._merge_dicts(
            self.DEFAULT_IMPORT_PATTERNS,
            custom_import_patterns or {}
        )
        self.function_patterns = self._merge_dicts(
            self.DEFAULT_FUNCTION_PATTERNS,
            custom_function_patterns or {}
        )
    
    def _merge_dicts(
        self,
        default: Dict[ScriptCategory, List[str]],
        custom: Dict[ScriptCategory, List[str]]
    ) -> Dict[ScriptCategory, List[str]]:
        result = {}
        for category in ScriptCategory:
            if category == ScriptCategory.UNKNOWN:
                continue
            result[category] = default.get(category, []) + custom.get(category, [])
        return result


class ImportParser:
    def parse_file(self, file_path: Path) -> Tuple[List[ImportInfo], List[str], List[str], Optional[str], int]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines_count = content.count('\n') + 1
            
            try:
                tree = ast.parse(content)
            except SyntaxError:
                return [], [], [], None, lines_count
            
            imports = []
            functions = []
            classes = []
            docstring = ast.get_docstring(tree)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(ImportInfo(
                            module_name=alias.name,
                            import_type="import",
                            alias=alias.asname,
                            line_number=node.lineno,
                            is_local=self._is_local_import(alias.name, file_path)
                        ))
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(ImportInfo(
                            module_name=module,
                            import_type="from",
                            alias=alias.asname,
                            imported_names=[alias.name],
                            line_number=node.lineno,
                            is_local=self._is_local_import(module, file_path)
                        ))
                
                elif isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
            
            return imports, functions, classes, docstring, lines_count
            
        except Exception:
            return [], [], [], None, 0
    
    def _is_local_import(self, module_name: str, file_path: Path) -> bool:
        if not module_name:
            return False
        
        project_root = self._find_project_root(file_path)
        if not project_root:
            return False
        
        module_path = project_root / module_name.replace('.', '/')
        if module_path.exists() or (module_path.parent / f"{module_path.name}.py").exists():
            return True
        
        return False
    
    def _find_project_root(self, file_path: Path) -> Optional[Path]:
        current = file_path.parent
        while current != current.parent:
            if (current / "pyproject.toml").exists() or \
               (current / "setup.py").exists() or \
               (current / "requirements.txt").exists():
                return current
            current = current.parent
        return None


class ScriptClassifier:
    def __init__(self, rules: Optional[ClassificationRules] = None):
        self.rules = rules or ClassificationRules()
        self.import_parser = ImportParser()
    
    def classify(self, file_path: Path) -> ScriptInfo:
        imports, functions, classes, docstring, lines_count = self.import_parser.parse_file(file_path)
        
        current_category = self._determine_category_from_path(file_path)
        
        suggested_category = self._suggest_category(
            file_path, imports, functions, classes, docstring
        )
        
        local_imports = [imp for imp in imports if imp.is_local]
        external_imports = [imp for imp in imports if not imp.is_local]
        
        return ScriptInfo(
            file_path=file_path,
            category=current_category,
            suggested_category=suggested_category,
            imports=imports,
            local_imports=local_imports,
            external_imports=external_imports,
            functions=functions,
            classes=classes,
            docstring=docstring,
            lines_count=lines_count
        )
    
    def _determine_category_from_path(self, file_path: Path) -> ScriptCategory:
        path_parts = [p.lower() for p in file_path.parts]
        
        for category in ScriptCategory:
            if category.value in path_parts:
                return category
        
        return ScriptCategory.UNKNOWN
    
    def _suggest_category(
        self,
        file_path: Path,
        imports: List[ImportInfo],
        functions: List[str],
        classes: List[str],
        docstring: Optional[str]
    ) -> ScriptCategory:
        scores: Dict[ScriptCategory, int] = defaultdict(int)
        
        filename = file_path.stem.lower()
        for category, keywords in self.rules.keywords.items():
            for keyword in keywords:
                if keyword.lower() in filename:
                    scores[category] += 3
        
        if docstring:
            docstring_lower = docstring.lower()
            for category, keywords in self.rules.keywords.items():
                for keyword in keywords:
                    if keyword.lower() in docstring_lower:
                        scores[category] += 2
        
        for imp in imports:
            module_lower = imp.module_name.lower()
            for category, patterns in self.rules.import_patterns.items():
                for pattern in patterns:
                    if pattern.lower() in module_lower:
                        scores[category] += 2
        
        for func in functions:
            func_lower = func.lower()
            for category, patterns in self.rules.function_patterns.items():
                for pattern in patterns:
                    if pattern.lower() in func_lower:
                        scores[category] += 1
        
        for cls in classes:
            cls_lower = cls.lower()
            for category, keywords in self.rules.keywords.items():
                for keyword in keywords:
                    if keyword.lower() in cls_lower:
                        scores[category] += 1
        
        if scores:
            return max(scores, key=scores.get)
        
        return ScriptCategory.UNKNOWN


class DependencyAnalyzer:
    def __init__(self):
        self.import_parser = ImportParser()
    
    def analyze(self, scripts: Dict[str, ScriptInfo]) -> Tuple[Dict[str, Set[str]], List[CycleInfo], List[str]]:
        self._build_dependency_graph(scripts)
        
        cycles = self._detect_cycles(scripts)
        
        isolated = self._find_isolated_scripts(scripts)
        
        dependency_graph = {
            path: list(info.dependencies)
            for path, info in scripts.items()
        }
        
        return dependency_graph, cycles, isolated
    
    def _build_dependency_graph(self, scripts: Dict[str, ScriptInfo]) -> None:
        script_modules = {}
        for path, info in scripts.items():
            module_name = self._path_to_module(info.file_path)
            script_modules[module_name] = path
            
            relative_module = self._get_relative_module_name(info.file_path)
            if relative_module:
                script_modules[relative_module] = path
        
        for path, info in scripts.items():
            for imp in info.local_imports:
                target_path = self._resolve_import_path(imp, script_modules, info.file_path)
                if target_path and target_path in scripts:
                    info.dependencies.add(target_path)
                    scripts[target_path].dependents.add(path)
    
    def _path_to_module(self, file_path: Path) -> str:
        parts = list(file_path.parts)
        if parts[-1].endswith('.py'):
            parts[-1] = parts[-1][:-3]
        if parts[-1] == '__init__':
            parts = parts[:-1]
        return '.'.join(parts)
    
    def _get_relative_module_name(self, file_path: Path) -> Optional[str]:
        parts = list(file_path.parts)
        try:
            scripts_idx = parts.index('skillscripts')
            relevant_parts = parts[scripts_idx:]
            if relevant_parts[-1].endswith('.py'):
                relevant_parts[-1] = relevant_parts[-1][:-3]
            if relevant_parts[-1] == '__init__':
                relevant_parts = relevant_parts[:-1]
            return '.'.join(relevant_parts)
        except ValueError:
            return None
    
    def _resolve_import_path(
        self,
        imp: ImportInfo,
        script_modules: Dict[str, str],
        source_path: Path
    ) -> Optional[str]:
        if imp.import_type == "import":
            return script_modules.get(imp.module_name)
        
        module = imp.module_name
        if module in script_modules:
            return script_modules[module]
        
        for name in imp.imported_names:
            full_module = f"{module}.{name}"
            if full_module in script_modules:
                return script_modules[full_module]
        
        return None
    
    def _detect_cycles(self, scripts: Dict[str, ScriptInfo]) -> List[CycleInfo]:
        cycles = []
        visited = set()
        rec_stack = []
        rec_stack_set = set()
        
        def dfs(node: str, edges: List[DependencyEdge]) -> None:
            visited.add(node)
            rec_stack.append(node)
            rec_stack_set.add(node)
            
            for dep in scripts[node].dependencies:
                if dep not in visited:
                    edge = DependencyEdge(
                        source=node,
                        target=dep,
                        import_info=ImportInfo(module_name=dep, import_type="local")
                    )
                    dfs(dep, edges + [edge])
                elif dep in rec_stack_set:
                    cycle_start = rec_stack.index(dep)
                    cycle_nodes = rec_stack[cycle_start:]
                    
                    cycle_edges = []
                    for i in range(len(cycle_nodes)):
                        src = cycle_nodes[i]
                        tgt = cycle_nodes[(i + 1) % len(cycle_nodes)]
                        cycle_edges.append(DependencyEdge(
                            source=src,
                            target=tgt,
                            import_info=ImportInfo(module_name=tgt, import_type="local")
                        ))
                    
                    cycles.append(CycleInfo(nodes=cycle_nodes, edges=cycle_edges))
            
            rec_stack.pop()
            rec_stack_set.remove(node)
        
        for path in scripts:
            if path not in visited:
                dfs(path, [])
        
        unique_cycles = []
        seen_cycle_sets = []
        for cycle in cycles:
            cycle_set = frozenset(cycle.nodes)
            if cycle_set not in seen_cycle_sets:
                seen_cycle_sets.append(cycle_set)
                unique_cycles.append(cycle)
        
        return unique_cycles
    
    def _find_isolated_scripts(self, scripts: Dict[str, ScriptInfo]) -> List[str]:
        isolated = []
        for path, info in scripts.items():
            if not info.dependencies and not info.dependents:
                if not info.file_path.name.startswith('__'):
                    isolated.append(path)
        return isolated


class MigrationAdvisor:
    def analyze(
        self,
        scripts: Dict[str, ScriptInfo],
        cycles: List[CycleInfo]
    ) -> List[MigrationSuggestion]:
        suggestions = []
        
        for path, info in scripts.items():
            suggestion = self._analyze_script(path, info, scripts)
            if suggestion:
                suggestions.append(suggestion)
        
        cycle_suggestions = self._analyze_cycles(cycles, scripts)
        suggestions.extend(cycle_suggestions)
        
        suggestions.sort(key=lambda s: (
            {"high": 0, "medium": 1, "low": 2, "none": 3}[s.priority.value]
        ))
        
        return suggestions
    
    def _analyze_script(
        self,
        path: str,
        info: ScriptInfo,
        scripts: Dict[str, ScriptInfo]
    ) -> Optional[MigrationSuggestion]:
        if info.category == info.suggested_category:
            return None
        
        if info.suggested_category == ScriptCategory.UNKNOWN:
            return None
        
        priority = self._determine_migration_priority(info, scripts)
        
        reason = self._generate_migration_reason(info)
        
        affected = self._find_affected_scripts(path, info, scripts)
        
        info.needs_migration = True
        info.migration_priority = priority
        info.migration_reason = reason
        
        return MigrationSuggestion(
            script_path=info.file_path,
            current_category=info.category,
            suggested_category=info.suggested_category,
            priority=priority,
            reason=reason,
            affected_scripts=affected
        )
    
    def _determine_migration_priority(
        self,
        info: ScriptInfo,
        scripts: Dict[str, ScriptInfo]
    ) -> MigrationPriority:
        if info.dependents:
            return MigrationPriority.HIGH
        
        if info.dependencies:
            return MigrationPriority.MEDIUM
        
        return MigrationPriority.LOW
    
    def _generate_migration_reason(self, info: ScriptInfo) -> str:
        reasons = []
        
        filename = info.file_path.stem.lower()
        for keyword in ["test", "spec", "coverage"]:
            if keyword in filename and info.suggested_category == ScriptCategory.TEST:
                reasons.append(f"文件名包含'{keyword}'关键词")
                break
        
        if info.docstring:
            docstring_lower = info.docstring.lower()
            for keyword in ["test", "pipeline", "analysis"]:
                if keyword in docstring_lower:
                    reasons.append(f"文档字符串包含'{keyword}'关键词")
                    break
        
        for imp in info.imports:
            if "pytest" in imp.module_name.lower():
                reasons.append("使用了pytest测试框架")
                break
            elif "unittest" in imp.module_name.lower():
                reasons.append("使用了unittest测试框架")
                break
        
        if not reasons:
            reasons.append("基于代码结构和依赖分析的建议")
        
        return "; ".join(reasons)
    
    def _find_affected_scripts(
        self,
        path: str,
        info: ScriptInfo,
        scripts: Dict[str, ScriptInfo]
    ) -> List[str]:
        affected = []
        
        for dep_path in info.dependents:
            if dep_path in scripts:
                affected.append(dep_path)
        
        return affected
    
    def _analyze_cycles(
        self,
        cycles: List[CycleInfo],
        scripts: Dict[str, ScriptInfo]
    ) -> List[MigrationSuggestion]:
        suggestions = []
        
        for cycle in cycles:
            for node in cycle.nodes:
                if node in scripts:
                    info = scripts[node]
                    suggestions.append(MigrationSuggestion(
                        script_path=info.file_path,
                        current_category=info.category,
                        suggested_category=ScriptCategory.UTILS,
                        priority=MigrationPriority.HIGH,
                        reason="参与循环依赖，建议重构为工具模块",
                        affected_scripts=[n for n in cycle.nodes if n != node]
                    ))
        
        return suggestions


class ReportGenerator:
    def generate_json_report(
        self,
        scripts: Dict[str, ScriptInfo],
        dependency_graph: Dict[str, List[str]],
        cycles: List[CycleInfo],
        isolated: List[str],
        suggestions: List[MigrationSuggestion]
    ) -> str:
        category_counts = defaultdict(int)
        for info in scripts.values():
            category_counts[info.category.value] += 1
        
        report = ClassificationReport(
            generated_at=datetime.now().isoformat(),
            total_scripts=len(scripts),
            category_counts=dict(category_counts),
            scripts=scripts,
            dependency_graph=dependency_graph,
            cycles=cycles,
            isolated_scripts=isolated,
            migration_suggestions=suggestions
        )
        
        return json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
    
    def generate_markdown_report(
        self,
        scripts: Dict[str, ScriptInfo],
        dependency_graph: Dict[str, List[str]],
        cycles: List[CycleInfo],
        isolated: List[str],
        suggestions: List[MigrationSuggestion]
    ) -> str:
        lines = []
        
        lines.append("# 脚本分类报告")
        lines.append("")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**脚本总数**: {len(scripts)}")
        lines.append("")
        
        lines.append("## 分类统计")
        lines.append("")
        
        category_counts = defaultdict(int)
        for info in scripts.values():
            category_counts[info.category.value] += 1
        
        lines.append("| 分类 | 数量 |")
        lines.append("|------|------|")
        for category in ScriptCategory:
            count = category_counts.get(category.value, 0)
            lines.append(f"| {category.value} | {count} |")
        lines.append("")
        
        lines.append("## 脚本清单")
        lines.append("")
        
        for category in ScriptCategory:
            category_scripts = [
                (path, info) for path, info in scripts.items()
                if info.category == category
            ]
            
            if category_scripts:
                lines.append(f"### {category.value}")
                lines.append("")
                lines.append("| 脚本 | 行数 | 函数 | 类 | 依赖数 |")
                lines.append("|------|------|------|-----|--------|")
                
                for path, info in sorted(category_scripts, key=lambda x: x[0]):
                    lines.append(
                        f"| `{Path(path).name}` | {info.lines_count} | "
                        f"{len(info.functions)} | {len(info.classes)} | "
                        f"{len(info.dependencies)} |"
                    )
                lines.append("")
        
        if cycles:
            lines.append("## 循环依赖")
            lines.append("")
            lines.append("检测到以下循环依赖：")
            lines.append("")
            
            for i, cycle in enumerate(cycles, 1):
                lines.append(f"### 循环 {i}")
                lines.append("")
                lines.append("```")
                lines.append(" -> ".join(cycle.nodes))
                lines.append("```")
                lines.append("")
        
        if isolated:
            lines.append("## 孤立脚本")
            lines.append("")
            lines.append("以下脚本没有依赖关系：")
            lines.append("")
            for path in sorted(isolated):
                lines.append(f"- `{Path(path).name}`")
            lines.append("")
        
        if suggestions:
            lines.append("## 迁移建议")
            lines.append("")
            
            high_priority = [s for s in suggestions if s.priority == MigrationPriority.HIGH]
            medium_priority = [s for s in suggestions if s.priority == MigrationPriority.MEDIUM]
            low_priority = [s for s in suggestions if s.priority == MigrationPriority.LOW]
            
            if high_priority:
                lines.append("### 高优先级")
                lines.append("")
                for s in high_priority:
                    lines.append(f"- **{s.script_path.name}**")
                    lines.append(f"  - 当前: `{s.current_category.value}` → 建议: `{s.suggested_category.value}`")
                    lines.append(f"  - 原因: {s.reason}")
                    if s.affected_scripts:
                        lines.append(f"  - 影响脚本: {len(s.affected_scripts)} 个")
                    lines.append("")
            
            if medium_priority:
                lines.append("### 中优先级")
                lines.append("")
                for s in medium_priority:
                    lines.append(f"- **{s.script_path.name}**")
                    lines.append(f"  - 当前: `{s.current_category.value}` → 建议: `{s.suggested_category.value}`")
                    lines.append(f"  - 原因: {s.reason}")
                    lines.append("")
            
            if low_priority:
                lines.append("### 低优先级")
                lines.append("")
                for s in low_priority:
                    lines.append(f"- **{s.script_path.name}**: `{s.current_category.value}` → `{s.suggested_category.value}`")
                lines.append("")
        
        return "\n".join(lines)
    
    def generate_dependency_visualization(
        self,
        scripts: Dict[str, ScriptInfo],
        dependency_graph: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        nodes = []
        edges = []
        
        category_colors = {
            ScriptCategory.PIPELINE.value: "#3498db",
            ScriptCategory.TEST.value: "#2ecc71",
            ScriptCategory.ANALYSIS.value: "#9b59b6",
            ScriptCategory.OPTIMIZATION.value: "#e74c3c",
            ScriptCategory.REQUIREMENTS.value: "#f39c12",
            ScriptCategory.UTILS.value: "#1abc9c",
            ScriptCategory.CORE.value: "#34495e",
            ScriptCategory.UNKNOWN.value: "#95a5a6"
        }
        
        for path, info in scripts.items():
            nodes.append({
                "id": path,
                "label": Path(path).name,
                "category": info.category.value,
                "color": category_colors.get(info.category.value, "#95a5a6"),
                "size": max(10, min(30, info.lines_count // 10))
            })
        
        for source, targets in dependency_graph.items():
            for target in targets:
                edges.append({
                    "source": source,
                    "target": target,
                    "type": "depends_on"
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "category_colors": category_colors
            }
        }
    
    def generate_migration_script(
        self,
        suggestions: List[MigrationSuggestion],
        output_path: Path
    ) -> str:
        lines = []
        lines.append('"""脚本迁移执行脚本 - 自动生成"""')
        lines.append("")
        lines.append("import shutil")
        lines.append("from pathlib import Path")
        lines.append("")
        lines.append("MIGRATIONS = [")
        
        for s in suggestions:
            if s.priority != MigrationPriority.NONE:
                lines.append("    {")
                lines.append(f'        "source": r"{s.script_path}",')
                
                new_path = self._calculate_new_path(s.script_path, s.suggested_category)
                lines.append(f'        "target": r"{new_path}",')
                lines.append(f'        "category": "{s.suggested_category.value}",')
                lines.append(f'        "priority": "{s.priority.value}",')
                lines.append("    },")
        
        lines.append("]")
        lines.append("")
        lines.append("def execute_migrations(dry_run: bool = True):")
        lines.append('    """执行迁移操作"""')
        lines.append("    for migration in MIGRATIONS:")
        lines.append("        source = Path(migration['source'])")
        lines.append("        target = Path(migration['target'])")
        lines.append("")
        lines.append("        if not source.exists():")
        lines.append('            print(f"源文件不存在: {source}")')
        lines.append("            continue")
        lines.append("")
        lines.append("        if dry_run:")
        lines.append('            print(f"[预览] 将迁移: {source.name} -> {migration[\'category\']}/")')
        lines.append("        else:")
        lines.append("            target.parent.mkdir(parents=True, exist_ok=True)")
        lines.append("            shutil.move(str(source), str(target))")
        lines.append('            print(f"[执行] 已迁移: {source.name} -> {target}")')
        lines.append("")
        lines.append('if __name__ == "__main__":')
        lines.append("    import argparse")
        lines.append("    parser = argparse.ArgumentParser(description='执行脚本迁移')")
        lines.append("    parser.add_argument('--execute', action='store_true', help='实际执行迁移（默认为预览模式）')")
        lines.append("    args = parser.parse_args()")
        lines.append("    execute_migrations(dry_run=not args.execute)")
        
        return "\n".join(lines)
    
    def _calculate_new_path(
        self,
        current_path: Path,
        new_category: ScriptCategory
    ) -> Path:
        parts = list(current_path.parts)
        
        for i, part in enumerate(parts):
            if part in [c.value for c in ScriptCategory]:
                parts[i] = new_category.value
                return Path(*parts)
        
        try:
            scripts_idx = parts.index('skillscripts')
            parts.insert(scripts_idx + 1, new_category.value)
            return Path(*parts)
        except ValueError:
            return current_path


class ScriptClassificationManager:
    def __init__(
        self,
        scripts_dir: Path,
        custom_rules: Optional[ClassificationRules] = None
    ):
        self.scripts_dir = Path(scripts_dir)
        self.classifier = ScriptClassifier(custom_rules)
        self.dependency_analyzer = DependencyAnalyzer()
        self.migration_advisor = MigrationAdvisor()
        self.report_generator = ReportGenerator()
        self._scripts: Dict[str, ScriptInfo] = {}
    
    def scan_scripts(self) -> Dict[str, ScriptInfo]:
        self._scripts = {}
        
        for py_file in self.scripts_dir.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            
            script_info = self.classifier.classify(py_file)
            self._scripts[str(py_file)] = script_info
        
        return self._scripts
    
    def _should_skip_file(self, file_path: Path) -> bool:
        skip_patterns = [
            ".snapshots",
            "__pycache__",
            ".venv",
            "node_modules",
            "site-packages"
        ]
        
        for pattern in skip_patterns:
            if pattern in file_path.parts:
                return True
        
        return False
    
    def analyze_dependencies(self) -> Tuple[Dict[str, List[str]], List[CycleInfo], List[str]]:
        return self.dependency_analyzer.analyze(self._scripts)
    
    def get_migration_suggestions(self) -> List[MigrationSuggestion]:
        _, cycles, _ = self.analyze_dependencies()
        return self.migration_advisor.analyze(self._scripts, cycles)
    
    def generate_json_report(self, output_path: Optional[Path] = None) -> str:
        dep_graph, cycles, isolated = self.analyze_dependencies()
        suggestions = self.get_migration_suggestions()
        
        report = self.report_generator.generate_json_report(
            self._scripts, dep_graph, cycles, isolated, suggestions
        )
        
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
        
        return report
    
    def generate_markdown_report(self, output_path: Optional[Path] = None) -> str:
        dep_graph, cycles, isolated = self.analyze_dependencies()
        suggestions = self.get_migration_suggestions()
        
        report = self.report_generator.generate_markdown_report(
            self._scripts, dep_graph, cycles, isolated, suggestions
        )
        
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
        
        return report
    
    def generate_visualization_data(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        dep_graph, _, _ = self.analyze_dependencies()
        
        viz_data = self.report_generator.generate_dependency_visualization(
            self._scripts, dep_graph
        )
        
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(viz_data, f, indent=2, ensure_ascii=False)
        
        return viz_data
    
    def generate_migration_script(self, output_path: Path) -> str:
        suggestions = self.get_migration_suggestions()
        
        script = self.report_generator.generate_migration_script(
            suggestions, output_path
        )
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(script)
        
        return script
    
    def preview_migration(self, script_path: Path) -> Optional[MigrationSuggestion]:
        path_str = str(script_path)
        if path_str not in self._scripts:
            return None
        
        info = self._scripts[path_str]
        suggestions = self.get_migration_suggestions()
        
        for s in suggestions:
            if str(s.script_path) == path_str:
                return s
        
        return None
    
    def get_scripts_by_category(self, category: ScriptCategory) -> List[ScriptInfo]:
        return [
            info for info in self._scripts.values()
            if info.category == category
        ]
    
    def get_script_info(self, script_path: Path) -> Optional[ScriptInfo]:
        return self._scripts.get(str(script_path))
    
    def get_statistics(self) -> Dict[str, Any]:
        if not self._scripts:
            return {}
        
        category_counts = defaultdict(int)
        total_lines = 0
        total_functions = 0
        total_classes = 0
        
        for info in self._scripts.values():
            category_counts[info.category.value] += 1
            total_lines += info.lines_count
            total_functions += len(info.functions)
            total_classes += len(info.classes)
        
        dep_graph, cycles, isolated = self.analyze_dependencies()
        
        return {
            "total_scripts": len(self._scripts),
            "total_lines": total_lines,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "category_distribution": dict(category_counts),
            "dependency_count": sum(len(deps) for deps in dep_graph.values()),
            "cycle_count": len(cycles),
            "isolated_count": len(isolated)
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="脚本分类管理工具")
    parser.add_argument(
        "--scripts-dir",
        type=str,
        required=True,
        help="脚本目录路径"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(get_path_config().REPORTS_DIR),
        help="报告输出目录"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "markdown", "all"],
        default="all",
        help="报告格式"
    )
    parser.add_argument(
        "--generate-migration-script",
        action="store_true",
        help="生成迁移执行脚本"
    )
    
    args = parser.parse_args()
    
    scripts_dir = Path(args.scripts_dir)
    output_dir = Path(args.output_dir)
    
    manager = ScriptClassificationManager(scripts_dir)
    
    print(f"正在扫描脚本目录: {scripts_dir}")
    scripts = manager.scan_scripts()
    print(f"找到 {len(scripts)} 个脚本")
    
    print("\n正在分析依赖关系...")
    dep_graph, cycles, isolated = manager.analyze_dependencies()
    print(f"发现 {len(cycles)} 个循环依赖")
    print(f"发现 {len(isolated)} 个孤立脚本")
    
    print("\n正在生成迁移建议...")
    suggestions = manager.get_migration_suggestions()
    print(f"生成 {len(suggestions)} 条迁移建议")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.format in ["json", "all"]:
        json_path = output_dir / "classification_report.json"
        manager.generate_json_report(json_path)
        print(f"\nJSON报告已生成: {json_path}")
    
    if args.format in ["markdown", "all"]:
        md_path = output_dir / "classification_report.md"
        manager.generate_markdown_report(md_path)
        print(f"Markdown报告已生成: {md_path}")
    
    viz_path = output_dir / "dependency_visualization.json"
    manager.generate_visualization_data(viz_path)
    print(f"依赖可视化数据已生成: {viz_path}")
    
    if args.generate_migration_script:
        migration_path = output_dir / "execute_migrations.py"
        manager.generate_migration_script(migration_path)
        print(f"迁移执行脚本已生成: {migration_path}")
    
    stats = manager.get_statistics()
    print("\n=== 统计信息 ===")
    print(f"脚本总数: {stats['total_scripts']}")
    print(f"代码总行数: {stats['total_lines']}")
    print(f"函数总数: {stats['total_functions']}")
    print(f"类总数: {stats['total_classes']}")
    print(f"依赖关系数: {stats['dependency_count']}")
    
    print("\n分类分布:")
    for category, count in stats['category_distribution'].items():
        print(f"  {category}: {count}")


if __name__ == "__main__":
    main()
