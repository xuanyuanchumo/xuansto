#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本整合管理器 - Script Integration Manager
整合backend/scripts、frontend/scripts和skillscripts目录中的冗余脚本
实现统一的脚本管理和调用机制

功能:
1. 检测重复脚本并分析相似度
2. 合并功能相似的脚本
3. 创建统一的脚本调用入口
4. 生成整合报告
"""

import os
import sys
import json
import ast
import hashlib
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ScriptType(Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    UNKNOWN = "unknown"


class ScriptCategory(Enum):
    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"
    TEST = "test"
    PIPELINE = "pipeline"
    CORE = "core"
    UTILS = "utils"
    REQUIREMENTS = "requirements"
    FRONTEND = "frontend"
    BACKEND = "backend"
    UNKNOWN = "unknown"


class IntegrationAction(Enum):
    KEEP_ORIGINAL = "keep_original"
    KEEP_SKILLSCRIPTS = "keep_skillscripts"
    MERGE = "merge"
    DEPRECATE = "deprecate"
    MOVE_TO_SKILLSCRIPTS = "move_to_skillscripts"


@dataclass
class ScriptInfo:
    path: str
    name: str
    script_type: ScriptType
    category: ScriptCategory
    size: int
    line_count: int
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    docstring: str = ""
    hash: str = ""
    location: str = ""


@dataclass
class DuplicatePair:
    script1: ScriptInfo
    script2: ScriptInfo
    similarity: float
    recommendation: IntegrationAction
    reason: str


@dataclass
class IntegrationReport:
    timestamp: str
    backend_scripts: List[ScriptInfo] = field(default_factory=list)
    frontend_scripts: List[ScriptInfo] = field(default_factory=list)
    skillscripts: List[ScriptInfo] = field(default_factory=list)
    duplicates: List[DuplicatePair] = field(default_factory=list)
    unique_backend: List[ScriptInfo] = field(default_factory=list)
    unique_frontend: List[ScriptInfo] = field(default_factory=list)
    integration_actions: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


class ScriptIntegrator:
    
    BACKEND_SCRIPTS_DIR = "backend/scripts"
    FRONTEND_SCRIPTS_DIR = "frontend/scripts"
    SKILLSCRIPTS_DIR = "skillscripts"
    
    SCRIPT_CATEGORIES = {
        "analysis": ["analyzer", "analysis", "check", "detect", "validate", "locator", "issue"],
        "optimization": ["fixer", "optimizer", "optimization", "fix", "refactor", "enhance"],
        "test": ["test", "spec", "coverage", "benchmark"],
        "pipeline": ["pipeline", "generator", "doc", "sdd", "tdd"],
        "core": ["manager", "coordinator", "checker", "init", "health", "service"],
        "utils": ["utils", "helper", "history", "tracker", "version"],
        "requirements": ["requirement", "rule", "trace", "business"],
        "frontend": ["gui", "vue", "component", "ui", "adaptation", "consistency"],
        "backend": ["error_handler", "rollback", "iteration", "monitor"]
    }
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.report = IntegrationReport(timestamp=datetime.now().isoformat())
        
    def analyze_all(self) -> IntegrationReport:
        logger.info("开始分析所有脚本目录...")
        
        backend_path = self.base_path / self.BACKEND_SCRIPTS_DIR
        frontend_path = self.base_path / self.FRONTEND_SCRIPTS_DIR
        skillscripts_path = self.base_path / self.SKILLSCRIPTS_DIR
        
        if backend_path.exists():
            self.report.backend_scripts = self._analyze_directory(backend_path, "backend")
            logger.info(f"Backend脚本: {len(self.report.backend_scripts)} 个")
        
        if frontend_path.exists():
            self.report.frontend_scripts = self._analyze_directory(frontend_path, "frontend")
            logger.info(f"Frontend脚本: {len(self.report.frontend_scripts)} 个")
        
        if skillscripts_path.exists():
            self.report.skillscripts = self._analyze_skillscripts(skillscripts_path)
            logger.info(f"Skillscripts脚本: {len(self.report.skillscripts)} 个")
        
        self._find_duplicates()
        self._identify_unique_scripts()
        self._generate_integration_actions()
        self._generate_summary()
        
        return self.report
    
    def _analyze_directory(self, dir_path: Path, location: str) -> List[ScriptInfo]:
        scripts = []
        
        for file_path in dir_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.py', '.ts', '.js']:
                if '__pycache__' in str(file_path) or 'node_modules' in str(file_path):
                    continue
                    
                script_info = self._analyze_script(file_path, location)
                if script_info:
                    scripts.append(script_info)
        
        return scripts
    
    def _analyze_skillscripts(self, dir_path: Path) -> List[ScriptInfo]:
        scripts = []
        
        for category_dir in dir_path.iterdir():
            if category_dir.is_dir() and not category_dir.name.startswith('.'):
                for file_path in category_dir.rglob("*.py"):
                    if '__pycache__' in str(file_path):
                        continue
                    
                    script_info = self._analyze_script(file_path, "skillscripts")
                    if script_info:
                        script_info.category = ScriptCategory(category_dir.name)
                        scripts.append(script_info)
        
        return scripts
    
    def _analyze_script(self, file_path: Path, location: str) -> Optional[ScriptInfo]:
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            script_type = self._detect_script_type(file_path)
            category = self._detect_category(file_path.name)
            
            functions = []
            classes = []
            imports = []
            docstring = ""
            
            if script_type == ScriptType.PYTHON:
                functions, classes, imports, docstring = self._parse_python(content)
            elif script_type in [ScriptType.TYPESCRIPT, ScriptType.JAVASCRIPT]:
                functions, classes, imports, docstring = self._parse_typescript(content)
            
            return ScriptInfo(
                path=str(file_path),
                name=file_path.name,
                script_type=script_type,
                category=category,
                size=file_path.stat().st_size,
                line_count=len(content.splitlines()),
                functions=functions,
                classes=classes,
                imports=imports,
                docstring=docstring[:500] if docstring else "",
                hash=hashlib.md5(content.encode()).hexdigest(),
                location=location
            )
        except Exception as e:
            logger.warning(f"分析脚本 {file_path} 时出错: {e}")
            return None
    
    def _detect_script_type(self, file_path: Path) -> ScriptType:
        suffix = file_path.suffix.lower()
        if suffix == '.py':
            return ScriptType.PYTHON
        elif suffix == '.ts':
            return ScriptType.TYPESCRIPT
        elif suffix == '.js':
            return ScriptType.JAVASCRIPT
        return ScriptType.UNKNOWN
    
    def _detect_category(self, filename: str) -> ScriptCategory:
        filename_lower = filename.lower()
        for category, keywords in self.SCRIPT_CATEGORIES.items():
            for keyword in keywords:
                if keyword in filename_lower:
                    return ScriptCategory(category)
        return ScriptCategory.UNKNOWN
    
    def _parse_python(self, content: str) -> Tuple[List[str], List[str], List[str], str]:
        functions = []
        classes = []
        imports = []
        docstring = ""
        
        try:
            tree = ast.parse(content)
            
            if tree.body and isinstance(tree.body[0], ast.Expr):
                if isinstance(tree.body[0].value, ast.Constant):
                    docstring = tree.body[0].value.value or ""
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    else:
                        imports.append(node.module or "")
        except SyntaxError:
            pass
        
        return functions, classes, imports, docstring
    
    def _parse_typescript(self, content: str) -> Tuple[List[str], List[str], List[str], str]:
        functions = re.findall(r'function\s+(\w+)', content)
        functions.extend(re.findall(r'const\s+(\w+)\s*=\s*(?:async\s*)?\(', content))
        
        classes = re.findall(r'class\s+(\w+)', content)
        
        imports = re.findall(r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]', content)
        imports.extend(re.findall(r'import\s+[\'"]([^\'"]+)[\'"]', content))
        
        doc_match = re.search(r'/\*\*(.*?)\*/', content, re.DOTALL)
        docstring = doc_match.group(1).strip() if doc_match else ""
        
        return functions, classes, imports, docstring
    
    def _find_duplicates(self):
        logger.info("检测重复脚本...")
        
        all_scripts = (
            self.report.backend_scripts + 
            self.report.frontend_scripts + 
            self.report.skillscripts
        )
        
        checked = set()
        
        for i, script1 in enumerate(all_scripts):
            for j, script2 in enumerate(all_scripts):
                if i >= j:
                    continue
                
                pair_key = tuple(sorted([script1.path, script2.path]))
                if pair_key in checked:
                    continue
                checked.add(pair_key)
                
                if script1.name == script2.name:
                    similarity = self._calculate_similarity(script1, script2)
                    
                    if similarity > 0.3:
                        action, reason = self._recommend_action(script1, script2, similarity)
                        
                        self.report.duplicates.append(DuplicatePair(
                            script1=script1,
                            script2=script2,
                            similarity=similarity,
                            recommendation=action,
                            reason=reason
                        ))
    
    def _calculate_similarity(self, script1: ScriptInfo, script2: ScriptInfo) -> float:
        if script1.hash == script2.hash:
            return 1.0
        
        func_similarity = len(set(script1.functions) & set(script2.functions)) / max(
            len(set(script1.functions) | set(script2.functions)), 1
        )
        
        class_similarity = len(set(script1.classes) & set(script2.classes)) / max(
            len(set(script1.classes) | set(script2.classes)), 1
        )
        
        import_similarity = len(set(script1.imports) & set(script2.imports)) / max(
            len(set(script1.imports) | set(script2.imports)), 1
        )
        
        name_score = 1.0 if script1.name == script2.name else 0.0
        
        return (func_similarity * 0.4 + class_similarity * 0.3 + 
                import_similarity * 0.2 + name_score * 0.1)
    
    def _recommend_action(self, script1: ScriptInfo, script2: ScriptInfo, 
                          similarity: float) -> Tuple[IntegrationAction, str]:
        if similarity >= 0.9:
            if script1.location == "skillscripts":
                return IntegrationAction.KEEP_SKILLSCRIPTS, "skillscripts版本更完整，保留"
            elif script2.location == "skillscripts":
                return IntegrationAction.KEEP_SKILLSCRIPTS, "skillscripts版本更完整，保留"
            else:
                return IntegrationAction.MOVE_TO_SKILLSCRIPTS, "完全重复，移动到skillscripts统一管理"
        
        elif similarity >= 0.7:
            if script1.location == "skillscripts" or script2.location == "skillscripts":
                return IntegrationAction.MERGE, "高度相似，建议合并到skillscripts"
            else:
                return IntegrationAction.MOVE_TO_SKILLSCRIPTS, "高度相似，移动到skillscripts统一管理"
        
        else:
            return IntegrationAction.KEEP_ORIGINAL, "功能不同，保留各自版本"
    
    def _identify_unique_scripts(self):
        duplicate_paths = set()
        for dup in self.report.duplicates:
            duplicate_paths.add(dup.script1.path)
            duplicate_paths.add(dup.script2.path)
        
        for script in self.report.backend_scripts:
            if script.path not in duplicate_paths:
                self.report.unique_backend.append(script)
        
        for script in self.report.frontend_scripts:
            if script.path not in duplicate_paths:
                self.report.unique_frontend.append(script)
    
    def _generate_integration_actions(self):
        for dup in self.report.duplicates:
            self.report.integration_actions.append({
                "script1": dup.script1.path,
                "script2": dup.script2.path,
                "similarity": round(dup.similarity, 2),
                "action": dup.recommendation.value,
                "reason": dup.reason
            })
        
        for script in self.report.unique_backend:
            if script.script_type == ScriptType.PYTHON:
                self.report.integration_actions.append({
                    "script": script.path,
                    "action": "keep_unique",
                    "reason": f"Backend独特脚本: {script.name}",
                    "category": script.category.value
                })
        
        for script in self.report.unique_frontend:
            self.report.integration_actions.append({
                "script": script.path,
                "action": "keep_unique",
                "reason": f"Frontend独特脚本: {script.name}",
                "category": script.category.value
            })
    
    def _generate_summary(self):
        self.report.summary = {
            "total_backend_scripts": len(self.report.backend_scripts),
            "total_frontend_scripts": len(self.report.frontend_scripts),
            "total_skillscripts": len(self.report.skillscripts),
            "duplicate_pairs": len(self.report.duplicates),
            "unique_backend_scripts": len(self.report.unique_backend),
            "unique_frontend_scripts": len(self.report.unique_frontend),
            "actions_summary": {
                "keep_skillscripts": sum(1 for d in self.report.duplicates 
                                        if d.recommendation == IntegrationAction.KEEP_SKILLSCRIPTS),
                "move_to_skillscripts": sum(1 for d in self.report.duplicates 
                                           if d.recommendation == IntegrationAction.MOVE_TO_SKILLSCRIPTS),
                "merge": sum(1 for d in self.report.duplicates 
                            if d.recommendation == IntegrationAction.MERGE),
                "keep_original": sum(1 for d in self.report.duplicates 
                                    if d.recommendation == IntegrationAction.KEEP_ORIGINAL)
            }
        }
    
    def generate_report_markdown(self) -> str:
        lines = [
            "# 脚本整合分析报告",
            f"\n生成时间: {self.report.timestamp}",
            "\n## 概述",
            f"\n| 目录 | 脚本数量 |",
            f"|------|----------|",
            f"| Backend/Scripts | {self.report.summary['total_backend_scripts']} |",
            f"| Frontend/Scripts | {self.report.summary['total_frontend_scripts']} |",
            f"| Skillscripts | {self.report.summary['total_skillscripts']} |",
            f"| **重复对数** | **{self.report.summary['duplicate_pairs']}** |",
            "\n## 重复脚本分析",
        ]
        
        for dup in self.report.duplicates:
            lines.extend([
                f"\n### {dup.script1.name}",
                f"- **脚本1**: `{dup.script1.path}` ({dup.script1.location})",
                f"- **脚本2**: `{dup.script2.path}` ({dup.script2.location})",
                f"- **相似度**: {dup.similarity:.1%}",
                f"- **建议操作**: {dup.recommendation.value}",
                f"- **原因**: {dup.reason}"
            ])
        
        lines.extend([
            "\n## 独特脚本",
            "\n### Backend独特脚本",
        ])
        
        for script in self.report.unique_backend:
            lines.append(f"- `{script.name}` - {script.docstring[:100] if script.docstring else '无描述'}")
        
        lines.append("\n### Frontend独特脚本")
        for script in self.report.unique_frontend:
            lines.append(f"- `{script.name}` - {script.docstring[:100] if script.docstring else '无描述'}")
        
        lines.extend([
            "\n## 整合建议",
            "\n| 操作 | 数量 |",
            "|------|------|",
        ])
        
        for action, count in self.report.summary['actions_summary'].items():
            lines.append(f"| {action} | {count} |")
        
        return "\n".join(lines)
    
    def save_report(self, output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        json_report = {
            "timestamp": self.report.timestamp,
            "summary": self.report.summary,
            "duplicates": [
                {
                    "script1": {"path": d.script1.path, "name": d.script1.name, "location": d.script1.location},
                    "script2": {"path": d.script2.path, "name": d.script2.name, "location": d.script2.location},
                    "similarity": d.similarity,
                    "recommendation": d.recommendation.value,
                    "reason": d.reason
                }
                for d in self.report.duplicates
            ],
            "unique_backend": [{"path": s.path, "name": s.name, "category": s.category.value} 
                              for s in self.report.unique_backend],
            "unique_frontend": [{"path": s.path, "name": s.name, "category": s.category.value} 
                               for s in self.report.unique_frontend],
            "integration_actions": self.report.integration_actions
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, ensure_ascii=False, indent=2)
        
        md_path = output_path.with_suffix('.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_report_markdown())
        
        logger.info(f"报告已保存至: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="脚本整合管理器")
    parser.add_argument("--base-path", default=".", help="项目基础路径")
    parser.add_argument("--output", default="script_integration_report.json", help="输出报告路径")
    parser.add_argument("--dry-run", action="store_true", help="仅分析不执行整合")
    
    args = parser.parse_args()
    
    integrator = ScriptIntegrator(args.base_path)
    report = integrator.analyze_all()
    
    output_path = Path(args.output)
    integrator.save_report(output_path)
    
    print("\n" + "="*60)
    print("脚本整合分析完成")
    print("="*60)
    print(f"重复脚本对数: {report.summary['duplicate_pairs']}")
    print(f"Backend独特脚本: {report.summary['unique_backend_scripts']}")
    print(f"Frontend独特脚本: {report.summary['unique_frontend_scripts']}")
    print(f"\n详细报告: {output_path}")


if __name__ == "__main__":
    main()
