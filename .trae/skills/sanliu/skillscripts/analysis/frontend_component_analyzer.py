#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前端组件分析器 - Sanliu 技能

提供全面的前端组件分析功能，包括：
- 目录结构和组件作用分析
- 冗余和相似组件识别
- 组件依赖关系分析
- 前端优化建议报告生成

使用示例:
    python frontend_component_analyzer.py --frontend ./frontend
    python frontend_component_analyzer.py --frontend ./frontend --output html
"""

import json
import logging
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class ComponentType(Enum):
    """组件类型枚举"""
    VIEW = "view"
    COMPONENT = "component"
    STORE = "store"
    COMPOSABLE = "composable"
    UTILITY = "utility"
    API = "api"
    ROUTER = "router"
    STYLE = "style"
    TEST = "test"
    UNKNOWN = "unknown"


class IssueSeverity(Enum):
    """问题严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SimilarityType(Enum):
    """相似类型"""
    DUPLICATE = "duplicate"
    SIMILAR = "similar"
    RELATED = "related"


@dataclass
class PropInfo:
    """组件属性信息"""
    name: str
    prop_type: str
    required: bool = False
    default_value: Optional[str] = None
    description: str = ""


@dataclass
class EmitInfo:
    """组件事件信息"""
    name: str
    parameters: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class MethodInfo:
    """方法信息"""
    name: str
    parameters: List[str] = field(default_factory=list)
    is_async: bool = False
    line_number: int = 0


@dataclass
class ComponentInfo:
    """组件信息"""
    path: str
    name: str
    component_type: ComponentType
    description: str = ""
    props: List[PropInfo] = field(default_factory=list)
    emits: List[EmitInfo] = field(default_factory=list)
    methods: List[MethodInfo] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    lines_of_code: int = 0
    file_size_bytes: int = 0
    has_typescript: bool = False
    has_scoped_style: bool = False
    api_calls: List[str] = field(default_factory=list)


@dataclass
class SimilarityResult:
    """相似性检测结果"""
    file1: str
    file2: str
    similarity_type: SimilarityType
    similarity_score: float
    similar_parts: List[Dict[str, Any]] = field(default_factory=list)
    recommendation: str = ""


@dataclass
class DependencyEdge:
    """依赖边"""
    source: str
    target: str
    dependency_type: str
    strength: int = 1


@dataclass
class OptimizationIssue:
    """优化问题"""
    issue_type: str
    severity: IssueSeverity
    location: str
    description: str
    recommendation: str
    impact: str = ""


@dataclass
class FrontendAnalysisReport:
    """前端分析报告"""
    timestamp: str
    frontend_path: str
    total_components: int
    total_lines_of_code: int
    components: List[ComponentInfo] = field(default_factory=list)
    similarities: List[SimilarityResult] = field(default_factory=list)
    dependencies: List[DependencyEdge] = field(default_factory=list)
    issues: List[OptimizationIssue] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "frontend_path": self.frontend_path,
            "total_components": self.total_components,
            "total_lines_of_code": self.total_lines_of_code,
            "components": [
                {
                    "path": c.path,
                    "name": c.name,
                    "component_type": c.component_type.value,
                    "description": c.description,
                    "lines_of_code": c.lines_of_code,
                    "dependencies": list(c.dependencies),
                    "dependents": list(c.dependents),
                    "props_count": len(c.props),
                    "methods_count": len(c.methods),
                    "api_calls_count": len(c.api_calls),
                    "has_typescript": c.has_typescript,
                    "has_scoped_style": c.has_scoped_style
                }
                for c in self.components
            ],
            "similarities": [
                {
                    "file1": s.file1,
                    "file2": s.file2,
                    "similarity_type": s.similarity_type.value,
                    "similarity_score": s.similarity_score,
                    "recommendation": s.recommendation
                }
                for s in self.similarities
            ],
            "dependencies": [
                {
                    "source": d.source,
                    "target": d.target,
                    "dependency_type": d.dependency_type,
                    "strength": d.strength
                }
                for d in self.dependencies
            ],
            "issues": [
                {
                    "issue_type": i.issue_type,
                    "severity": i.severity.value,
                    "location": i.location,
                    "description": i.description,
                    "recommendation": i.recommendation,
                    "impact": i.impact
                }
                for i in self.issues
            ],
            "recommendations": self.recommendations,
            "statistics": self.statistics
        }


class FrontendComponentAnalyzer:
    """前端组件分析器"""
    
    COMPONENT_TYPE_PATTERNS = {
        ComponentType.VIEW: [r'/views/', r'View\.vue$', r'Page\.vue$'],
        ComponentType.COMPONENT: [r'/components/', r'\.vue$'],
        ComponentType.STORE: [r'/stores/', r'store\.ts$', r'Store\.ts$'],
        ComponentType.COMPOSABLE: [r'/composables/', r'use[A-Z]', r'/hooks/'],
        ComponentType.UTILITY: [r'/utils/', r'/helpers/', r'util\.ts$', r'helper\.ts$'],
        ComponentType.API: [r'/api/', r'api\.ts$', r'service\.ts$'],
        ComponentType.ROUTER: [r'/router/', r'router\.ts$', r'route\.ts$'],
        ComponentType.STYLE: [r'/styles/', r'/css/', r'\.css$', r'\.scss$'],
        ComponentType.TEST: [r'/tests/', r'/__tests__/', r'\.test\.ts$', r'\.spec\.ts$'],
    }
    
    SIMILARITY_THRESHOLDS = {
        SimilarityType.DUPLICATE: 0.90,
        SimilarityType.SIMILAR: 0.70,
        SimilarityType.RELATED: 0.45
    }
    
    VUE_IMPORT_PATTERNS = [
        r"import\s+(\w+)\s+from\s+['\"](@?[/\w\-\.]+)['\"]",
        r"import\s+\{([^}]+)\}\s+from\s+['\"](@?[/\w\-\.]+)['\"]",
    ]
    
    API_CALL_PATTERNS = [
        r"api\.(get|post|put|delete|patch)\s*\(\s*['\"`]([^'\"`]+)['\"`]",
        r"axios\.(get|post|put|delete|patch)\s*\(\s*['\"`]([^'\"`]+)['\"`]",
        r"fetch\s*\(\s*['\"`]([^'\"`]+)['\"`]",
        r"request\.(get|post|put|delete)\s*\(\s*['\"`]([^'\"`]+)['\"`]",
    ]
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self.components: Dict[str, ComponentInfo] = {}
        self.import_graph: Dict[str, Set[str]] = defaultdict(set)
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("FrontendComponentAnalyzer")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def analyze(self, frontend_path: Path) -> FrontendAnalysisReport:
        """执行前端组件分析"""
        self.logger.info(f"开始分析前端目录: {frontend_path}")
        
        self.components = {}
        self.import_graph = defaultdict(set)
        
        vue_files = list(frontend_path.rglob("*.vue"))
        ts_files = list(frontend_path.rglob("*.ts"))
        js_files = list(frontend_path.rglob("*.js"))
        
        all_files = vue_files + ts_files + js_files
        
        for file_path in all_files:
            if self._should_skip_file(file_path):
                continue
            self._analyze_file(file_path, frontend_path)
        
        self._build_dependency_graph()
        
        similarities = self._detect_similarities()
        
        dependencies = self._analyze_dependencies()
        
        issues = self._identify_issues()
        
        recommendations = self._generate_recommendations(similarities, issues)
        
        statistics = self._calculate_statistics()
        
        total_loc = sum(c.lines_of_code for c in self.components.values())
        
        report = FrontendAnalysisReport(
            timestamp=datetime.now().isoformat(),
            frontend_path=str(frontend_path),
            total_components=len(self.components),
            total_lines_of_code=total_loc,
            components=list(self.components.values()),
            similarities=similarities,
            dependencies=dependencies,
            issues=issues,
            recommendations=recommendations,
            statistics=statistics
        )
        
        self.logger.info(f"前端分析完成: {len(self.components)} 个组件, {total_loc} 行代码")
        
        return report
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """判断是否应该跳过文件"""
        skip_patterns = [
            'node_modules', 'dist', '.git', 'coverage',
            '__pycache__', '.nuxt', '.output', 'build'
        ]
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _analyze_file(self, file_path: Path, frontend_path: Path) -> None:
        """分析单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            rel_path = str(file_path.relative_to(frontend_path))
            name = file_path.stem
            
            component_type = self._determine_component_type(rel_path)
            
            if file_path.suffix == '.vue':
                component_info = self._analyze_vue_file(rel_path, name, component_type, content, file_path)
            else:
                component_info = self._analyze_ts_js_file(rel_path, name, component_type, content, file_path)
            
            self.components[rel_path] = component_info
            
        except Exception as e:
            self.logger.warning(f"分析文件失败 {file_path}: {e}")
    
    def _determine_component_type(self, path: str) -> ComponentType:
        """确定组件类型"""
        path_lower = path.lower()
        
        for component_type, patterns in self.COMPONENT_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, path_lower):
                    return component_type
        
        return ComponentType.UNKNOWN
    
    def _analyze_vue_file(
        self,
        rel_path: str,
        name: str,
        component_type: ComponentType,
        content: str,
        file_path: Path
    ) -> ComponentInfo:
        """分析Vue文件"""
        imports = self._extract_imports(content)
        
        props = self._extract_vue_props(content)
        
        emits = self._extract_vue_emits(content)
        
        methods = self._extract_vue_methods(content)
        
        api_calls = self._extract_api_calls(content)
        
        has_typescript = '<script setup lang="ts"' in content or '<script lang="ts"' in content
        has_scoped_style = '<style scoped' in content
        
        lines_of_code = len(content.splitlines())
        file_size = file_path.stat().st_size
        
        description = self._extract_description(content)
        
        return ComponentInfo(
            path=rel_path,
            name=name,
            component_type=component_type,
            description=description,
            props=props,
            emits=emits,
            methods=methods,
            imports=imports,
            lines_of_code=lines_of_code,
            file_size_bytes=file_size,
            has_typescript=has_typescript,
            has_scoped_style=has_scoped_style,
            api_calls=api_calls
        )
    
    def _analyze_ts_js_file(
        self,
        rel_path: str,
        name: str,
        component_type: ComponentType,
        content: str,
        file_path: Path
    ) -> ComponentInfo:
        """分析TypeScript/JavaScript文件"""
        imports = self._extract_imports(content)
        
        methods = self._extract_ts_methods(content)
        
        api_calls = self._extract_api_calls(content)
        
        has_typescript = file_path.suffix == '.ts'
        
        lines_of_code = len(content.splitlines())
        file_size = file_path.stat().st_size
        
        description = self._extract_js_description(content)
        
        return ComponentInfo(
            path=rel_path,
            name=name,
            component_type=component_type,
            description=description,
            methods=methods,
            imports=imports,
            lines_of_code=lines_of_code,
            file_size_bytes=file_size,
            has_typescript=has_typescript,
            api_calls=api_calls
        )
    
    def _extract_imports(self, content: str) -> List[str]:
        """提取导入信息"""
        imports = []
        
        for pattern in self.VUE_IMPORT_PATTERNS:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                if len(match.groups()) >= 2:
                    module_path = match.group(2)
                    imports.append(module_path)
        
        return list(set(imports))
    
    def _extract_vue_props(self, content: str) -> List[PropInfo]:
        """提取Vue组件的props"""
        props = []
        
        props_pattern = r'defineProps<\s*\{([^}]+)\}\s*\>'
        matches = re.finditer(props_pattern, content, re.DOTALL)
        for match in matches:
            props_content = match.group(1)
            prop_lines = props_content.split('\n')
            for line in prop_lines:
                prop_match = re.match(r'\s*(\w+)\s*(?:\?|:)\s*(\w+)', line.strip())
                if prop_match:
                    props.append(PropInfo(
                        name=prop_match.group(1),
                        prop_type=prop_match.group(2),
                        required='?' not in line
                    ))
        
        props_pattern2 = r'defineProps\s*\(\s*\[([^\]]+)\]\s*\)'
        matches = re.finditer(props_pattern2, content)
        for match in matches:
            props_content = match.group(1)
            prop_names = re.findall(r"'(\w+)'", props_content)
            for prop_name in prop_names:
                props.append(PropInfo(name=prop_name, prop_type="unknown"))
        
        return props
    
    def _extract_vue_emits(self, content: str) -> List[EmitInfo]:
        """提取Vue组件的emits"""
        emits = []
        
        emits_pattern = r'defineEmits<\s*\{([^}]+)\}\s*>'
        matches = re.finditer(emits_pattern, content, re.DOTALL)
        for match in matches:
            emits_content = match.group(1)
            emit_lines = emits_content.split('\n')
            for line in emit_lines:
                emit_match = re.match(r'\s*["\'](\w+)["\']\s*:', line.strip())
                if emit_match:
                    emits.append(EmitInfo(name=emit_match.group(1)))
        
        emits_pattern2 = r'defineEmits\s*\(\s*\[([^\]]+)\]\s*\)'
        matches = re.finditer(emits_pattern2, content)
        for match in matches:
            emits_content = match.group(1)
            emit_names = re.findall(r"'(\w+)'", emits_content)
            for emit_name in emit_names:
                emits.append(EmitInfo(name=emit_name))
        
        return emits
    
    def _extract_vue_methods(self, content: str) -> List[MethodInfo]:
        """提取Vue组件的方法"""
        methods = []
        
        script_match = re.search(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
        if not script_match:
            return methods
        
        script_content = script_match.group(1)
        
        func_pattern = r'(?:const|function)\s+(\w+)\s*(?:=\s*(?:async\s*)?\(|\()'
        matches = re.finditer(func_pattern, script_content)
        for match in matches:
            methods.append(MethodInfo(
                name=match.group(1),
                is_async='async' in match.group(0),
                line_number=script_content[:match.start()].count('\n') + 1
            ))
        
        return methods
    
    def _extract_ts_methods(self, content: str) -> List[MethodInfo]:
        """提取TypeScript文件的方法"""
        methods = []
        
        func_pattern = r'(?:export\s+)?(?:async\s+)?(?:function\s+(\w+)|(?:const|let)\s+(\w+)\s*=\s*(?:async\s*)?\()'
        matches = re.finditer(func_pattern, content)
        for match in matches:
            name = match.group(1) or match.group(2)
            if name:
                methods.append(MethodInfo(
                    name=name,
                    is_async='async' in match.group(0),
                    line_number=content[:match.start()].count('\n') + 1
                ))
        
        return methods
    
    def _extract_api_calls(self, content: str) -> List[str]:
        """提取API调用"""
        api_calls = []
        
        for pattern in self.API_CALL_PATTERNS:
            matches = re.finditer(pattern, content)
            for match in matches:
                if len(match.groups()) >= 2:
                    api_path = match.group(2)
                else:
                    api_path = match.group(1)
                if api_path:
                    api_calls.append(api_path)
        
        return list(set(api_calls))
    
    def _extract_description(self, content: str) -> str:
        """提取组件描述"""
        comment_pattern = r'<!--\s*(.+?)\s*-->'
        match = re.search(comment_pattern, content)
        if match:
            return match.group(1).strip()
        
        docstring_pattern = r'/\*\*\s*\n?\s*\*\s*(.+?)\s*\n?\s*\*/'
        match = re.search(docstring_pattern, content)
        if match:
            return match.group(1).strip()
        
        return ""
    
    def _extract_js_description(self, content: str) -> str:
        """提取JS/TS文件描述"""
        docstring_pattern = r'/\*\*\s*\n?\s*\*\s*(.+?)\s*\n?\s*\*/'
        match = re.search(docstring_pattern, content)
        if match:
            return match.group(1).strip()
        
        return ""
    
    def _build_dependency_graph(self) -> None:
        """构建依赖图"""
        for comp_path, comp_info in self.components.items():
            for imp in comp_info.imports:
                resolved = self._resolve_import(imp, comp_path)
                if resolved and resolved in self.components:
                    comp_info.dependencies.add(resolved)
                    self.components[resolved].dependents.add(comp_path)
    
    def _resolve_import(self, import_path: str, source_path: str) -> Optional[str]:
        """解析导入路径"""
        if import_path.startswith('@/'):
            rel_path = import_path[2:]
            
            extensions = ['.vue', '.ts', '.js', '/index.ts', '/index.js']
            for ext in extensions:
                candidate = rel_path + ext if not rel_path.endswith(ext) else rel_path
                if candidate in self.components:
                    return candidate
            
            if rel_path in self.components:
                return rel_path
        
        return None
    
    def _detect_similarities(self) -> List[SimilarityResult]:
        """检测相似组件"""
        similarities = []
        processed_pairs = set()
        
        comp_paths = list(self.components.keys())
        
        for i, path1 in enumerate(comp_paths):
            for path2 in comp_paths[i+1:]:
                pair_key = tuple(sorted([path1, path2]))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)
                
                similarity = self._calculate_similarity(path1, path2)
                
                if similarity >= self.SIMILARITY_THRESHOLDS[SimilarityType.RELATED]:
                    sim_type = self._get_similarity_type(similarity)
                    
                    similar_parts = self._find_similar_parts(path1, path2)
                    
                    recommendation = self._generate_similarity_recommendation(
                        path1, path2, sim_type, similarity
                    )
                    
                    similarities.append(SimilarityResult(
                        file1=path1,
                        file2=path2,
                        similarity_type=sim_type,
                        similarity_score=similarity,
                        similar_parts=similar_parts,
                        recommendation=recommendation
                    ))
        
        similarities.sort(key=lambda x: x.similarity_score, reverse=True)
        return similarities
    
    def _calculate_similarity(self, path1: str, path2: str) -> float:
        """计算两个组件的相似度"""
        comp1 = self.components[path1]
        comp2 = self.components[path2]
        
        props1 = set(p.name for p in comp1.props)
        props2 = set(p.name for p in comp2.props)
        
        if props1 or props2:
            prop_similarity = len(props1 & props2) / max(len(props1 | props2), 1)
        else:
            prop_similarity = 0
        
        methods1 = set(m.name for m in comp1.methods)
        methods2 = set(m.name for m in comp2.methods)
        
        if methods1 or methods2:
            method_similarity = len(methods1 & methods2) / max(len(methods1 | methods2), 1)
        else:
            method_similarity = 0
        
        imports1 = set(comp1.imports)
        imports2 = set(comp2.imports)
        
        if imports1 or imports2:
            import_similarity = len(imports1 & imports2) / max(len(imports1 | imports2), 1)
        else:
            import_similarity = 0
        
        api1 = set(comp1.api_calls)
        api2 = set(comp2.api_calls)
        
        if api1 or api2:
            api_similarity = len(api1 & api2) / max(len(api1 | api2), 1)
        else:
            api_similarity = 0
        
        name_similarity = SequenceMatcher(None, path1, path2).ratio()
        
        weights = {
            'prop': 0.20,
            'method': 0.25,
            'import': 0.20,
            'api': 0.15,
            'name': 0.20
        }
        
        total_similarity = (
            prop_similarity * weights['prop'] +
            method_similarity * weights['method'] +
            import_similarity * weights['import'] +
            api_similarity * weights['api'] +
            name_similarity * weights['name']
        )
        
        return total_similarity
    
    def _get_similarity_type(self, score: float) -> SimilarityType:
        """根据分数获取相似类型"""
        if score >= self.SIMILARITY_THRESHOLDS[SimilarityType.DUPLICATE]:
            return SimilarityType.DUPLICATE
        elif score >= self.SIMILARITY_THRESHOLDS[SimilarityType.SIMILAR]:
            return SimilarityType.SIMILAR
        else:
            return SimilarityType.RELATED
    
    def _find_similar_parts(self, path1: str, path2: str) -> List[Dict[str, Any]]:
        """找出相似的部分"""
        similar_parts = []
        
        comp1 = self.components[path1]
        comp2 = self.components[path2]
        
        props1 = {p.name: p for p in comp1.props}
        props2 = {p.name: p for p in comp2.props}
        
        common_props = set(props1.keys()) & set(props2.keys())
        for prop_name in common_props:
            similar_parts.append({
                "type": "prop",
                "name": prop_name
            })
        
        methods1 = {m.name: m for m in comp1.methods}
        methods2 = {m.name: m for m in comp2.methods}
        
        common_methods = set(methods1.keys()) & set(methods2.keys())
        for method_name in common_methods:
            similar_parts.append({
                "type": "method",
                "name": method_name
            })
        
        return similar_parts
    
    def _generate_similarity_recommendation(
        self,
        path1: str,
        path2: str,
        sim_type: SimilarityType,
        score: float
    ) -> str:
        """生成相似性建议"""
        if sim_type == SimilarityType.DUPLICATE:
            return f"检测到重复组件 ({score:.0%})，建议合并或提取公共组件"
        elif sim_type == SimilarityType.SIMILAR:
            return f"检测到相似组件 ({score:.0%})，建议提取公共逻辑或创建基础组件"
        else:
            return f"检测到相关组件 ({score:.0%})，可考虑统一管理"
    
    def _analyze_dependencies(self) -> List[DependencyEdge]:
        """分析依赖关系"""
        dependencies = []
        
        for comp_path, comp_info in self.components.items():
            for dep in comp_info.dependencies:
                dependencies.append(DependencyEdge(
                    source=comp_path,
                    target=dep,
                    dependency_type="import",
                    strength=1
                ))
        
        return dependencies
    
    def _identify_issues(self) -> List[OptimizationIssue]:
        """识别优化问题"""
        issues = []
        
        for path, comp in self.components.items():
            if comp.lines_of_code > 400:
                issues.append(OptimizationIssue(
                    issue_type="large_component",
                    severity=IssueSeverity.MEDIUM if comp.lines_of_code > 600 else IssueSeverity.LOW,
                    location=path,
                    description=f"组件过大 ({comp.lines_of_code} 行)",
                    recommendation="考虑拆分为更小的组件",
                    impact="影响代码可读性和维护性"
                ))
            
            if len(comp.methods) > 15:
                issues.append(OptimizationIssue(
                    issue_type="too_many_methods",
                    severity=IssueSeverity.LOW,
                    location=path,
                    description=f"方法数量过多 ({len(comp.methods)})",
                    recommendation="考虑提取可复用逻辑到composables",
                    impact="降低代码组织性"
                ))
            
            if len(comp.props) > 10:
                issues.append(OptimizationIssue(
                    issue_type="too_many_props",
                    severity=IssueSeverity.LOW,
                    location=path,
                    description=f"Props数量过多 ({len(comp.props)})",
                    recommendation="考虑使用对象形式传递或拆分组件",
                    impact="增加组件复杂度"
                ))
            
            if comp.component_type in [ComponentType.VIEW, ComponentType.COMPONENT]:
                if not comp.has_typescript:
                    issues.append(OptimizationIssue(
                        issue_type="missing_typescript",
                        severity=IssueSeverity.LOW,
                        location=path,
                        description="组件未使用TypeScript",
                        recommendation="添加TypeScript支持以提高类型安全",
                        impact="降低代码健壮性"
                    ))
            
            if comp.component_type == ComponentType.COMPONENT:
                if not comp.has_scoped_style:
                    issues.append(OptimizationIssue(
                        issue_type="unscoped_style",
                        severity=IssueSeverity.INFO,
                        location=path,
                        description="组件样式未使用scoped",
                        recommendation="使用scoped样式避免样式污染",
                        impact="可能导致样式冲突"
                    ))
            
            if len(comp.dependencies) > 8:
                issues.append(OptimizationIssue(
                    issue_type="high_coupling",
                    severity=IssueSeverity.MEDIUM,
                    location=path,
                    description=f"组件依赖过多 ({len(comp.dependencies)})",
                    recommendation="减少依赖，提高组件独立性",
                    impact="增加维护成本"
                ))
        
        for path, comp in self.components.items():
            if len(comp.dependents) == 0 and comp.component_type not in [ComponentType.VIEW, ComponentType.ROUTER, ComponentType.STYLE]:
                issues.append(OptimizationIssue(
                    issue_type="unused_component",
                    severity=IssueSeverity.LOW,
                    location=path,
                    description="组件未被其他组件引用",
                    recommendation="确认组件是否仍在使用",
                    impact="可能是死代码"
                ))
        
        issues.sort(key=lambda x: {
            IssueSeverity.CRITICAL: 0,
            IssueSeverity.HIGH: 1,
            IssueSeverity.MEDIUM: 2,
            IssueSeverity.LOW: 3,
            IssueSeverity.INFO: 4
        }[x.severity])
        
        return issues
    
    def _generate_recommendations(
        self,
        similarities: List[SimilarityResult],
        issues: List[OptimizationIssue]
    ) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        duplicates = [s for s in similarities if s.similarity_type == SimilarityType.DUPLICATE]
        if duplicates:
            recommendations.append(f"发现 {len(duplicates)} 组重复组件，建议合并或提取公共组件")
        
        similar = [s for s in similarities if s.similarity_type == SimilarityType.SIMILAR]
        if similar:
            recommendations.append(f"发现 {len(similar)} 组相似组件，建议提取公共逻辑")
        
        large_components = [i for i in issues if i.issue_type == "large_component"]
        if large_components:
            recommendations.append(f"发现 {len(large_components)} 个过大组件，建议拆分")
        
        high_coupling = [i for i in issues if i.issue_type == "high_coupling"]
        if high_coupling:
            recommendations.append(f"发现 {len(high_coupling)} 个高耦合组件，建议降低依赖")
        
        unused = [i for i in issues if i.issue_type == "unused_component"]
        if unused:
            recommendations.append(f"发现 {len(unused)} 个可能未使用的组件，建议确认是否需要保留")
        
        missing_ts = [i for i in issues if i.issue_type == "missing_typescript"]
        if missing_ts:
            recommendations.append(f"发现 {len(missing_ts)} 个组件未使用TypeScript，建议添加类型支持")
        
        return recommendations
    
    def _calculate_statistics(self) -> Dict[str, Any]:
        """计算统计信息"""
        if not self.components:
            return {}
        
        type_counts = defaultdict(int)
        for comp in self.components.values():
            type_counts[comp.component_type.value] += 1
        
        total_methods = sum(len(c.methods) for c in self.components.values())
        total_props = sum(len(c.props) for c in self.components.values())
        total_loc = sum(c.lines_of_code for c in self.components.values())
        
        typescript_count = sum(1 for c in self.components.values() if c.has_typescript)
        scoped_style_count = sum(1 for c in self.components.values() if c.has_scoped_style)
        
        return {
            "components_by_type": dict(type_counts),
            "total_methods": total_methods,
            "total_props": total_props,
            "total_lines_of_code": total_loc,
            "typescript_coverage": round(typescript_count / len(self.components) * 100, 2) if self.components else 0,
            "scoped_style_coverage": round(scoped_style_count / len(self.components) * 100, 2) if self.components else 0,
            "average_component_size": round(total_loc / len(self.components), 2) if self.components else 0
        }
    
    def generate_report_markdown(self, report: FrontendAnalysisReport) -> str:
        """生成Markdown格式报告"""
        lines = [
            f"# 前端组件分析报告",
            "",
            f"**生成时间**: {report.timestamp}",
            f"**分析路径**: {report.frontend_path}",
            "",
            "## 概览",
            "",
            f"- **总组件数**: {report.total_components}",
            f"- **总代码行数**: {report.total_lines_of_code:,}",
            f"- **方法总数**: {report.statistics.get('total_methods', 0)}",
            f"- **Props总数**: {report.statistics.get('total_props', 0)}",
            f"- **TypeScript覆盖率**: {report.statistics.get('typescript_coverage', 0)}%",
            f"- **Scoped样式覆盖率**: {report.statistics.get('scoped_style_coverage', 0)}%",
            "",
            "## 组件类型分布",
            "",
            "| 类型 | 数量 |",
            "|------|------|",
        ]
        
        for comp_type, count in report.statistics.get('components_by_type', {}).items():
            lines.append(f"| {comp_type} | {count} |")
        
        if report.similarities:
            lines.extend([
                "",
                "## 相似组件检测",
                "",
                "| 文件1 | 文件2 | 相似度 | 类型 | 建议 |",
                "|-------|-------|--------|------|------|",
            ])
            for sim in report.similarities[:20]:
                lines.append(
                    f"| {sim.file1[:30]}... | {sim.file2[:30]}... | "
                    f"{sim.similarity_score:.0%} | {sim.similarity_type.value} | "
                    f"{sim.recommendation[:30]}... |"
                )
        
        if report.issues:
            lines.extend([
                "",
                "## 问题列表",
                "",
                "| 严重程度 | 类型 | 位置 | 描述 | 建议 |",
                "|----------|------|------|------|------|",
            ])
            for issue in report.issues[:30]:
                lines.append(
                    f"| {issue.severity.value} | {issue.issue_type} | "
                    f"{issue.location[:30]}... | {issue.description[:40]}... | "
                    f"{issue.recommendation[:30]}... |"
                )
        
        if report.recommendations:
            lines.extend([
                "",
                "## 优化建议",
                "",
            ])
            for i, rec in enumerate(report.recommendations, 1):
                lines.append(f"{i}. {rec}")
        
        return "\n".join(lines)


def main() -> int:
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="前端组件分析器")
    parser.add_argument("--frontend", type=str, required=True, help="前端代码路径")
    parser.add_argument("--output", type=str, choices=["console", "json", "markdown"], 
                       default="console", help="输出格式")
    parser.add_argument("--report-dir", type=str, default=str(get_path_config().REPORTS_DIR), help="报告输出目录")
    
    args = parser.parse_args()
    
    analyzer = FrontendComponentAnalyzer()
    frontend_path = Path(args.frontend)
    
    if not frontend_path.exists():
        print(f"错误: 路径不存在 {frontend_path}")
        return 1
    
    report = analyzer.analyze(frontend_path)
    
    if args.output == "console":
        print(analyzer.generate_report_markdown(report))
    elif args.output == "json":
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    elif args.output == "markdown":
        report_dir = Path(args.report_dir)
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "frontend_analysis_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(analyzer.generate_report_markdown(report))
        print(f"报告已保存: {report_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
