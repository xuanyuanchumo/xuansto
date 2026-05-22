#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本相似度分析器 - Script Similarity Analyzer

识别并分析项目中的冗余和相似脚本，支持：
- 代码相似度检测
- 功能重复识别
- 合并建议生成
- 脚本清理报告

使用示例:
    python script_similarity_analyzer.py --dir ./skillscripts --threshold 0.7
    python script_similarity_analyzer.py --compare ./backend/scripts ./skillscripts
    python script_similarity_analyzer.py --report similarity_report.md
"""

import argparse
import ast
import difflib
import hashlib
import json
import logging
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ScriptInfo:
    path: Path
    name: str
    size: int
    lines: int
    functions: List[str]
    classes: List[str]
    imports: List[str]
    hash: str
    docstring: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": str(self.path),
            "name": self.name,
            "size": self.size,
            "lines": self.lines,
            "functions": self.functions,
            "classes": self.classes,
            "imports": self.imports,
            "hash": self.hash,
            "docstring": self.docstring
        }


@dataclass
class SimilarityResult:
    script1: ScriptInfo
    script2: ScriptInfo
    similarity_score: float
    similarity_type: str
    common_functions: List[str]
    common_classes: List[str]
    common_imports: List[str]
    merge_recommendation: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "script1": self.script1.to_dict(),
            "script2": self.script2.to_dict(),
            "similarity_score": self.similarity_score,
            "similarity_type": self.similarity_type,
            "common_functions": self.common_functions,
            "common_classes": self.common_classes,
            "common_imports": self.common_imports,
            "merge_recommendation": self.merge_recommendation
        }


@dataclass
class AnalysisReport:
    total_scripts: int
    total_similar_pairs: int
    high_similarity_pairs: List[SimilarityResult]
    medium_similarity_pairs: List[SimilarityResult]
    duplicate_scripts: List[Tuple[ScriptInfo, ScriptInfo]]
    recommendations: List[str]
    generated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_scripts": self.total_scripts,
            "total_similar_pairs": self.total_similar_pairs,
            "high_similarity_pairs": [p.to_dict() for p in self.high_similarity_pairs],
            "medium_similarity_pairs": [p.to_dict() for p in self.medium_similarity_pairs],
            "duplicate_scripts": [
                {"script1": s1.to_dict(), "script2": s2.to_dict()}
                for s1, s2 in self.duplicate_scripts
            ],
            "recommendations": self.recommendations,
            "generated_at": self.generated_at.isoformat()
        }


class ScriptParser:
    def parse(self, file_path: Path) -> Optional[ScriptInfo]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"无法读取文件 {file_path}: {e}")
            return None
        
        hash_value = hashlib.sha256(content.encode()).hexdigest()[:16]
        lines = content.count('\n') + 1
        size = len(content)
        
        functions = []
        classes = []
        imports = []
        docstring = None
        
        try:
            tree = ast.parse(content)
            
            docstring = ast.get_docstring(tree)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.AsyncFunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except SyntaxError as e:
            logger.warning(f"语法错误 {file_path}: {e}")
        
        return ScriptInfo(
            path=file_path,
            name=file_path.name,
            size=size,
            lines=lines,
            functions=functions,
            classes=classes,
            imports=imports,
            hash=hash_value,
            docstring=docstring
        )


class SimilarityCalculator:
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
    
    def calculate(self, script1: ScriptInfo, script2: ScriptInfo) -> SimilarityResult:
        if script1.hash == script2.hash:
            return SimilarityResult(
                script1=script1,
                script2=script2,
                similarity_score=1.0,
                similarity_type="exact_duplicate",
                common_functions=script1.functions,
                common_classes=script1.classes,
                common_imports=script1.imports,
                merge_recommendation="完全重复，建议删除其中一个"
            )
        
        common_functions = list(set(script1.functions) & set(script2.functions))
        common_classes = list(set(script1.classes) & set(script2.classes))
        common_imports = list(set(script1.imports) & set(script2.imports))
        
        func_similarity = self._calculate_set_similarity(
            set(script1.functions), set(script2.functions)
        )
        class_similarity = self._calculate_set_similarity(
            set(script1.classes), set(script2.classes)
        )
        import_similarity = self._calculate_set_similarity(
            set(script1.imports), set(script2.imports)
        )
        
        content_similarity = self._calculate_content_similarity(
            script1.path, script2.path
        )
        
        weights = {
            "functions": 0.35,
            "classes": 0.25,
            "imports": 0.15,
            "content": 0.25
        }
        
        total_similarity = (
            func_similarity * weights["functions"] +
            class_similarity * weights["classes"] +
            import_similarity * weights["imports"] +
            content_similarity * weights["content"]
        )
        
        similarity_type = self._determine_similarity_type(
            total_similarity,
            common_functions,
            common_classes
        )
        
        merge_recommendation = self._generate_merge_recommendation(
            total_similarity,
            similarity_type,
            common_functions,
            common_classes,
            script1,
            script2
        )
        
        return SimilarityResult(
            script1=script1,
            script2=script2,
            similarity_score=total_similarity,
            similarity_type=similarity_type,
            common_functions=common_functions,
            common_classes=common_classes,
            common_imports=common_imports,
            merge_recommendation=merge_recommendation
        )
    
    def _calculate_set_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0
    
    def _calculate_content_similarity(self, path1: Path, path2: Path) -> float:
        try:
            with open(path1, 'r', encoding='utf-8') as f:
                content1 = f.read()
            with open(path2, 'r', encoding='utf-8') as f:
                content2 = f.read()
        except Exception:
            return 0.0
        
        lines1 = content1.splitlines()
        lines2 = content2.splitlines()
        
        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        return matcher.ratio()
    
    def _determine_similarity_type(
        self,
        similarity: float,
        common_functions: List[str],
        common_classes: List[str]
    ) -> str:
        if similarity >= 0.9:
            return "near_duplicate"
        elif similarity >= 0.7:
            if len(common_functions) > 3:
                return "functional_overlap"
            elif len(common_classes) > 0:
                return "class_overlap"
            return "high_similarity"
        elif similarity >= 0.5:
            return "medium_similarity"
        else:
            return "low_similarity"
    
    def _generate_merge_recommendation(
        self,
        similarity: float,
        similarity_type: str,
        common_functions: List[str],
        common_classes: List[str],
        script1: ScriptInfo,
        script2: ScriptInfo
    ) -> str:
        if similarity_type == "near_duplicate":
            if script1.lines >= script2.lines:
                return f"建议保留 {script1.name}，删除 {script2.name}"
            else:
                return f"建议保留 {script2.name}，删除 {script1.name}"
        
        if similarity_type == "functional_overlap":
            return f"建议合并共同功能: {', '.join(common_functions[:5])}"
        
        if similarity_type == "class_overlap":
            return f"建议合并共同类: {', '.join(common_classes)}"
        
        if similarity_type == "high_similarity":
            return "建议审查代码结构，考虑提取公共模块"
        
        return "建议保持独立，但可考虑共享部分导入"


class ScriptSimilarityAnalyzer:
    def __init__(
        self,
        threshold: float = 0.7,
        exclude_patterns: Optional[List[str]] = None
    ):
        self.threshold = threshold
        self.exclude_patterns = exclude_patterns or [
            "__pycache__",
            ".git",
            "node_modules",
            "venv",
            ".venv",
            "test_",
            "_test.py"
        ]
        self.parser = ScriptParser()
        self.calculator = SimilarityCalculator(threshold)
        self._scripts: List[ScriptInfo] = []
    
    def scan_directory(self, directory: Path) -> List[ScriptInfo]:
        logger.info(f"扫描目录: {directory}")
        scripts = []
        
        for py_file in directory.rglob("*.py"):
            if self._should_exclude(py_file):
                continue
            
            script_info = self.parser.parse(py_file)
            if script_info:
                scripts.append(script_info)
                logger.debug(f"解析脚本: {py_file.name}")
        
        self._scripts = scripts
        logger.info(f"共扫描 {len(scripts)} 个脚本")
        return scripts
    
    def compare_directories(
        self,
        dir1: Path,
        dir2: Path
    ) -> List[SimilarityResult]:
        scripts1 = self.scan_directory(dir1)
        scripts2 = self.scan_directory(dir2)
        
        results = []
        
        for s1 in scripts1:
            for s2 in scripts2:
                if s1.path == s2.path:
                    continue
                
                result = self.calculator.calculate(s1, s2)
                if result.similarity_score >= self.threshold:
                    results.append(result)
        
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results
    
    def analyze(self, scripts: Optional[List[ScriptInfo]] = None) -> AnalysisReport:
        scripts = scripts or self._scripts
        
        similar_pairs = []
        for i, s1 in enumerate(scripts):
            for s2 in scripts[i+1:]:
                result = self.calculator.calculate(s1, s2)
                if result.similarity_score >= self.threshold:
                    similar_pairs.append(result)
        
        similar_pairs.sort(key=lambda x: x.similarity_score, reverse=True)
        
        high_similarity = [
            p for p in similar_pairs
            if p.similarity_score >= 0.8
        ]
        medium_similarity = [
            p for p in similar_pairs
            if 0.7 <= p.similarity_score < 0.8
        ]
        
        duplicates = [
            (p.script1, p.script2)
            for p in similar_pairs
            if p.similarity_type == "exact_duplicate"
        ]
        
        recommendations = self._generate_recommendations(
            high_similarity,
            medium_similarity,
            duplicates
        )
        
        return AnalysisReport(
            total_scripts=len(scripts),
            total_similar_pairs=len(similar_pairs),
            high_similarity_pairs=high_similarity,
            medium_similarity_pairs=medium_similarity,
            duplicate_scripts=duplicates,
            recommendations=recommendations,
            generated_at=datetime.now()
        )
    
    def _should_exclude(self, path: Path) -> bool:
        path_str = str(path)
        for pattern in self.exclude_patterns:
            if pattern in path_str:
                return True
        return False
    
    def _generate_recommendations(
        self,
        high_similarity: List[SimilarityResult],
        medium_similarity: List[SimilarityResult],
        duplicates: List[Tuple[ScriptInfo, ScriptInfo]]
    ) -> List[str]:
        recommendations = []
        
        if duplicates:
            recommendations.append(
                f"发现 {len(duplicates)} 个完全重复的脚本，建议立即清理"
            )
        
        if high_similarity:
            recommendations.append(
                f"发现 {len(high_similarity)} 对高度相似脚本，建议合并或重构"
            )
        
        if medium_similarity:
            recommendations.append(
                f"发现 {len(medium_similarity)} 对中等相似脚本，建议审查代码结构"
            )
        
        function_counts = defaultdict(int)
        for pair in high_similarity + medium_similarity:
            for func in pair.common_functions:
                function_counts[func] += 1
        
        hot_functions = [
            (func, count) for func, count in function_counts.items()
            if count >= 3
        ]
        if hot_functions:
            hot_functions.sort(key=lambda x: x[1], reverse=True)
            recommendations.append(
                f"高频重复函数: {', '.join([f'{f}({c}次)' for f, c in hot_functions[:5]])}，建议提取为公共模块"
            )
        
        return recommendations
    
    def generate_report(
        self,
        report: AnalysisReport,
        output_path: Optional[str] = None,
        format: str = "markdown"
    ) -> str:
        if format == "json":
            return self._generate_json_report(report, output_path)
        return self._generate_markdown_report(report, output_path)
    
    def _generate_markdown_report(
        self,
        report: AnalysisReport,
        output_path: Optional[str] = None
    ) -> str:
        lines = [
            "# 脚本相似度分析报告",
            "",
            f"**生成时间**: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**扫描脚本数**: {report.total_scripts}",
            f"**相似脚本对数**: {report.total_similar_pairs}",
            "",
            "## 摘要",
            "",
        ]
        
        for rec in report.recommendations:
            lines.append(f"- {rec}")
        
        lines.append("")
        
        if report.duplicate_scripts:
            lines.extend([
                "## 完全重复脚本",
                "",
                "| 脚本1 | 脚本2 | 操作建议 |",
                "|-------|-------|----------|",
            ])
            for s1, s2 in report.duplicate_scripts:
                lines.append(f"| {s1.path} | {s2.path} | 删除其中一个 |")
            lines.append("")
        
        if report.high_similarity_pairs:
            lines.extend([
                "## 高度相似脚本 (>80%)",
                "",
                "| 脚本1 | 脚本2 | 相似度 | 类型 | 建议 |",
                "|-------|-------|--------|------|------|",
            ])
            for pair in report.high_similarity_pairs[:20]:
                lines.append(
                    f"| {pair.script1.name} | {pair.script2.name} | "
                    f"{pair.similarity_score:.1%} | {pair.similarity_type} | "
                    f"{pair.merge_recommendation[:30]}... |"
                )
            lines.append("")
        
        if report.medium_similarity_pairs:
            lines.extend([
                "## 中等相似脚本 (70-80%)",
                "",
                "| 脚本1 | 脚本2 | 相似度 | 共同函数 |",
                "|-------|-------|--------|----------|",
            ])
            for pair in report.medium_similarity_pairs[:20]:
                common_funcs = ", ".join(pair.common_functions[:3])
                lines.append(
                    f"| {pair.script1.name} | {pair.script2.name} | "
                    f"{pair.similarity_score:.1%} | {common_funcs} |"
                )
            lines.append("")
        
        report_content = "\n".join(lines)
        
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"报告已保存: {output_path}")
        
        return report_content
    
    def _generate_json_report(
        self,
        report: AnalysisReport,
        output_path: Optional[str] = None
    ) -> str:
        report_json = json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
        
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_json)
            logger.info(f"报告已保存: {output_path}")
        
        return report_json


def main():
    parser = argparse.ArgumentParser(
        description="脚本相似度分析器",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--dir",
        type=str,
        help="要扫描的目录"
    )
    parser.add_argument(
        "--compare",
        nargs=2,
        type=str,
        help="比较两个目录的脚本相似度"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="相似度阈值 (默认: 0.7)"
    )
    parser.add_argument(
        "--report",
        type=str,
        help="报告输出路径"
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="报告格式"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    analyzer = ScriptSimilarityAnalyzer(threshold=args.threshold)
    
    if args.compare:
        dir1 = Path(args.compare[0])
        dir2 = Path(args.compare[1])
        
        print(f"\n比较目录:")
        print(f"  目录1: {dir1}")
        print(f"  目录2: {dir2}")
        
        results = analyzer.compare_directories(dir1, dir2)
        
        print(f"\n发现 {len(results)} 对相似脚本:")
        for result in results[:10]:
            print(f"  {result.script1.name} <-> {result.script2.name}: {result.similarity_score:.1%}")
        
        if args.report:
            report = AnalysisReport(
                total_scripts=len(analyzer._scripts),
                total_similar_pairs=len(results),
                high_similarity_pairs=[r for r in results if r.similarity_score >= 0.8],
                medium_similarity_pairs=[r for r in results if 0.7 <= r.similarity_score < 0.8],
                duplicate_scripts=[],
                recommendations=analyzer._generate_recommendations(
                    [r for r in results if r.similarity_score >= 0.8],
                    [r for r in results if 0.7 <= r.similarity_score < 0.8],
                    []
                ),
                generated_at=datetime.now()
            )
            analyzer.generate_report(report, args.report, args.format)
    
    elif args.dir:
        directory = Path(args.dir)
        scripts = analyzer.scan_directory(directory)
        report = analyzer.analyze(scripts)
        
        print(f"\n{'='*60}")
        print("脚本相似度分析结果")
        print(f"{'='*60}")
        print(f"扫描脚本数: {report.total_scripts}")
        print(f"相似脚本对数: {report.total_similar_pairs}")
        print(f"高度相似: {len(report.high_similarity_pairs)}")
        print(f"中等相似: {len(report.medium_similarity_pairs)}")
        print(f"完全重复: {len(report.duplicate_scripts)}")
        print(f"{'='*60}\n")
        
        if args.report:
            analyzer.generate_report(report, args.report, args.format)
        else:
            print(analyzer.generate_report(report, format=args.format))
    
    else:
        parser.print_help()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
