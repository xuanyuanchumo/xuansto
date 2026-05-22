"""
优化的智能测试选择器

基于代码变更分析和历史数据，智能选择回归测试用例
支持多种选择策略和优先级排序
"""

import os
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class SelectionStrategy(Enum):
    FULL = "full"
    IMPACT_BASED = "impact_based"
    PRIORITY_BASED = "priority_based"
    INCREMENTAL = "incremental"
    SMART = "smart"


class TestCategory(Enum):
    PROJECT_MANAGEMENT = "project_management"
    TASK_MANAGEMENT = "task_management"
    USER_AUTHENTICATION = "user_authentication"
    REPORT_GENERATION = "report_generation"
    WORKFLOW = "workflow"
    INTEGRATION = "integration"


@dataclass
class TestInfo:
    test_id: str
    test_name: str
    test_file: str
    category: TestCategory
    priority: int
    execution_time: float = 0.0
    last_run: Optional[datetime] = None
    last_result: Optional[str] = None
    failure_count: int = 0
    success_count: int = 0
    covered_files: Set[str] = field(default_factory=set)
    covered_functions: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)


@dataclass
class CodeChange:
    file_path: str
    change_type: str
    changed_functions: Set[str] = field(default_factory=set)
    changed_classes: Set[str] = field(default_factory=set)
    impact_score: float = 0.0


@dataclass
class SelectionResult:
    selected_tests: List[str]
    skipped_tests: List[str]
    execution_order: List[str]
    estimated_time: float
    coverage_estimate: float
    selection_reason: Dict[str, str]
    priority_scores: Dict[str, float]


class IntelligentTestSelector:
    """优化的智能测试选择器"""
    
    def __init__(self, project_path: str, config: Optional[Dict[str, Any]] = None):
        self.project_path = Path(project_path)
        self.config = config or {}
        self.tests: Dict[str, TestInfo] = {}
        self.file_hash_cache: Dict[str, str] = {}
        self.test_history: Dict[str, Dict[str, Any]] = {}
        self.coverage_map: Dict[str, Set[str]] = defaultdict(set)
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        
    def discover_tests(self, test_dirs: List[str]) -> Dict[str, TestInfo]:
        """发现所有测试用例"""
        self.tests = {}
        
        for test_dir in test_dirs:
            test_path = self.project_path / test_dir
            if test_path.exists():
                self._discover_tests_in_dir(test_path)
        
        return self.tests
    
    def _discover_tests_in_dir(self, test_path: Path) -> None:
        """在目录中发现测试"""
        for py_file in test_path.rglob("*.py"):
            if py_file.name.startswith("test_") or py_file.name.endswith("_test.py"):
                self._parse_test_file(py_file)
    
    def _parse_test_file(self, file_path: Path) -> None:
        """解析测试文件"""
        try:
            content = file_path.read_text(encoding="utf-8")
            
            test_methods = self._extract_test_methods(content)
            
            for method_name, line_content in test_methods:
                test_id = f"{file_path.relative_to(self.project_path)}::{method_name}"
                
                category = self._determine_category(file_path, method_name)
                priority = self._determine_priority(method_name, content)
                covered_files = self._extract_covered_files(content)
                covered_functions = self._extract_covered_functions(content)
                
                self.tests[test_id] = TestInfo(
                    test_id=test_id,
                    test_name=method_name,
                    test_file=str(file_path.relative_to(self.project_path)),
                    category=category,
                    priority=priority,
                    covered_files=covered_files,
                    covered_functions=covered_functions
                )
                
                for covered_file in covered_files:
                    self.coverage_map[covered_file].add(test_id)
                    
        except Exception as e:
            print(f"解析测试文件失败 {file_path}: {e}")
    
    def _extract_test_methods(self, content: str) -> List[Tuple[str, str]]:
        """提取测试方法"""
        import re
        methods = []
        
        pattern = r'def\s+(test_\w+)\s*\([^)]*\):'
        for match in re.finditer(pattern, content):
            methods.append((match.group(1), match.group(0)))
        
        return methods
    
    def _determine_category(self, file_path: Path, method_name: str) -> TestCategory:
        """确定测试类别"""
        path_str = str(file_path).lower()
        method_lower = method_name.lower()
        
        if "project" in path_str or "project" in method_lower:
            return TestCategory.PROJECT_MANAGEMENT
        elif "task" in path_str or "task" in method_lower:
            return TestCategory.TASK_MANAGEMENT
        elif "auth" in path_str or "security" in path_str or "login" in method_lower:
            return TestCategory.USER_AUTHENTICATION
        elif "report" in path_str or "statistics" in path_str:
            return TestCategory.REPORT_GENERATION
        elif "workflow" in path_str:
            return TestCategory.WORKFLOW
        else:
            return TestCategory.INTEGRATION
    
    def _determine_priority(self, method_name: str, content: str) -> int:
        """确定测试优先级"""
        method_lower = method_name.lower()
        
        if any(kw in method_lower for kw in ["critical", "smoke", "core", "lifecycle"]):
            return 1
        elif any(kw in method_lower for kw in ["crud", "main", "key", "integration"]):
            return 2
        elif any(kw in method_lower for kw in ["edge", "boundary", "error"]):
            return 3
        else:
            return 4
    
    def _extract_covered_files(self, content: str) -> Set[str]:
        """提取覆盖的文件"""
        import re
        covered = set()
        
        import_pattern = r'from\s+([\w.]+)\s+import|import\s+([\w.]+)'
        for match in re.finditer(import_pattern, content):
            module = match.group(1) or match.group(2)
            if module:
                covered.add(module.replace(".", "/") + ".py")
        
        return covered
    
    def _extract_covered_functions(self, content: str) -> Set[str]:
        """提取覆盖的函数"""
        import re
        functions = set()
        
        call_pattern = r'(\w+)\s*\('
        for match in re.finditer(call_pattern, content):
            func_name = match.group(1)
            if not func_name.startswith(("assert", "self", "client", "mock")):
                functions.add(func_name)
        
        return functions
    
    def detect_changes(self, since: str = "HEAD~1") -> List[CodeChange]:
        """检测代码变更"""
        changes = []
        
        try:
            result = subprocess.run(
                ["git", "diff", "--name-status", since],
                cwd=self.project_path,
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
                        
                        if file_path.endswith(".py"):
                            change = CodeChange(
                                file_path=file_path,
                                change_type=status[0]
                            )
                            
                            if status[0] == "M":
                                change.changed_functions = self._extract_changed_functions(file_path, since)
                            
                            change.impact_score = self._calculate_impact_score(change)
                            changes.append(change)
                            
        except Exception as e:
            print(f"检测变更失败: {e}")
        
        return changes
    
    def _extract_changed_functions(self, file_path: str, since: str) -> Set[str]:
        """提取变更的函数"""
        import re
        functions = set()
        
        try:
            result = subprocess.run(
                ["git", "diff", since, "--", file_path],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                diff = result.stdout
                pattern = r'^[+-].*def\s+(\w+)'
                for match in re.finditer(pattern, diff, re.MULTILINE):
                    functions.add(match.group(1))
                    
        except Exception:
            pass
        
        return functions
    
    def _calculate_impact_score(self, change: CodeChange) -> float:
        """计算变更影响分数"""
        score = 0.0
        
        if change.change_type == "D":
            score += 0.5
        elif change.change_type == "A":
            score += 0.3
        elif change.change_type == "M":
            score += 0.2
        
        score += len(change.changed_functions) * 0.1
        
        affected_tests = self.coverage_map.get(change.file_path, set())
        score += len(affected_tests) * 0.05
        
        return min(score, 1.0)
    
    def select_tests(
        self,
        strategy: SelectionStrategy = SelectionStrategy.SMART,
        changes: Optional[List[CodeChange]] = None,
        max_tests: Optional[int] = None
    ) -> SelectionResult:
        """选择测试用例"""
        if not self.tests:
            self.discover_tests(self.config.get("test_dirs", ["backend/tests"]))
        
        if changes is None:
            changes = self.detect_changes()
        
        if strategy == SelectionStrategy.FULL:
            selected = list(self.tests.keys())
        elif strategy == SelectionStrategy.IMPACT_BASED:
            selected = self._select_by_impact(changes)
        elif strategy == SelectionStrategy.PRIORITY_BASED:
            selected = self._select_by_priority()
        elif strategy == SelectionStrategy.INCREMENTAL:
            selected = self._select_incremental(changes)
        else:
            selected = self._select_smart(changes)
        
        if max_tests and len(selected) > max_tests:
            selected = selected[:max_tests]
        
        skipped = [t for t in self.tests.keys() if t not in selected]
        execution_order = self._optimize_execution_order(selected)
        estimated_time = self._estimate_execution_time(selected)
        coverage_estimate = self._estimate_coverage(selected, changes)
        selection_reason = self._generate_selection_reasons(selected, changes)
        priority_scores = self._calculate_priority_scores(selected, changes)
        
        return SelectionResult(
            selected_tests=selected,
            skipped_tests=skipped,
            execution_order=execution_order,
            estimated_time=estimated_time,
            coverage_estimate=coverage_estimate,
            selection_reason=selection_reason,
            priority_scores=priority_scores
        )
    
    def _select_by_impact(self, changes: List[CodeChange]) -> List[str]:
        """基于影响选择测试"""
        selected = set()
        
        for change in changes:
            affected_tests = self.coverage_map.get(change.file_path, set())
            selected.update(affected_tests)
            
            for func in change.changed_functions:
                for test_id, test_info in self.tests.items():
                    if func in test_info.covered_functions:
                        selected.add(test_id)
        
        return list(selected)
    
    def _select_by_priority(self) -> List[str]:
        """基于优先级选择测试"""
        sorted_tests = sorted(
            self.tests.items(),
            key=lambda x: (x[1].priority, -x[1].failure_count / max(x[1].success_count + 1, 1))
        )
        
        return [t[0] for t in sorted_tests]
    
    def _select_incremental(self, changes: List[CodeChange]) -> List[str]:
        """增量选择测试"""
        selected = set()
        
        for change in changes:
            current_hash = self._get_file_hash(change.file_path)
            cached_hash = self.file_hash_cache.get(change.file_path)
            
            if current_hash != cached_hash:
                affected_tests = self.coverage_map.get(change.file_path, set())
                selected.update(affected_tests)
                self.file_hash_cache[change.file_path] = current_hash
        
        return list(selected)
    
    def _select_smart(self, changes: List[CodeChange]) -> List[str]:
        """智能选择测试"""
        selected = set()
        
        for test_id, test_info in self.tests.items():
            score = 0.0
            
            for change in changes:
                if change.file_path in test_info.covered_files:
                    score += 0.5
                
                if test_info.covered_functions & change.changed_functions:
                    score += 0.3
            
            score += (5 - test_info.priority) * 0.1
            
            if test_info.failure_count > 0:
                failure_rate = test_info.failure_count / max(test_info.success_count + test_info.failure_count, 1)
                score += failure_rate * 0.2
            
            if score > 0.1:
                selected.add(test_id)
        
        for test_id, test_info in self.tests.items():
            if test_info.priority == 1:
                selected.add(test_id)
        
        return list(selected)
    
    def _optimize_execution_order(self, test_ids: List[str]) -> List[str]:
        """优化执行顺序"""
        def sort_key(test_id: str) -> Tuple[int, float]:
            test_info = self.tests.get(test_id)
            if test_info:
                return (test_info.priority, -test_info.execution_time)
            return (4, 0)
        
        return sorted(test_ids, key=sort_key)
    
    def _estimate_execution_time(self, test_ids: List[str]) -> float:
        """估算执行时间"""
        total_time = 0.0
        
        for test_id in test_ids:
            test_info = self.tests.get(test_id)
            if test_info and test_info.execution_time > 0:
                total_time += test_info.execution_time
            else:
                total_time += 2.0
        
        return total_time
    
    def _estimate_coverage(self, test_ids: List[str], changes: List[CodeChange]) -> float:
        """估算覆盖率"""
        if not changes:
            return 100.0
        
        covered_changes = set()
        for test_id in test_ids:
            test_info = self.tests.get(test_id)
            if test_info:
                for change in changes:
                    if change.file_path in test_info.covered_files:
                        covered_changes.add(change.file_path)
        
        return len(covered_changes) / len(changes) * 100 if changes else 100.0
    
    def _generate_selection_reasons(self, test_ids: List[str], changes: List[CodeChange]) -> Dict[str, str]:
        """生成选择原因"""
        reasons = {}
        
        for test_id in test_ids:
            test_info = self.tests.get(test_id)
            if not test_info:
                continue
            
            reasons_list = []
            
            for change in changes:
                if change.file_path in test_info.covered_files:
                    reasons_list.append(f"覆盖变更文件 {change.file_path}")
                
                if test_info.covered_functions & change.changed_functions:
                    reasons_list.append("覆盖变更函数")
            
            if test_info.priority == 1:
                reasons_list.append("关键测试")
            
            reasons[test_id] = "; ".join(reasons_list) if reasons_list else "常规选择"
        
        return reasons
    
    def _calculate_priority_scores(self, test_ids: List[str], changes: List[CodeChange]) -> Dict[str, float]:
        """计算优先级分数"""
        scores = {}
        
        for test_id in test_ids:
            test_info = self.tests.get(test_id)
            if not test_info:
                continue
            
            score = 0.0
            
            score += (5 - test_info.priority) * 20
            
            for change in changes:
                if change.file_path in test_info.covered_files:
                    score += 30
            
            if test_info.failure_count > 0:
                failure_rate = test_info.failure_count / max(test_info.success_count + test_info.failure_count, 1)
                score += failure_rate * 20
            
            scores[test_id] = min(score, 100)
        
        return scores
    
    def _get_file_hash(self, file_path: str) -> str:
        """获取文件哈希"""
        full_path = self.project_path / file_path
        if full_path.exists():
            content = full_path.read_bytes()
            return hashlib.sha256(content).hexdigest()
        return ""
    
    def load_history(self, history_file: str = "test_history.json") -> None:
        """加载测试历史"""
        history_path = self.project_path / history_file
        if history_path.exists():
            try:
                with open(history_path, "r", encoding="utf-8") as f:
                    self.test_history = json.load(f)
                    
                    for test_id, history in self.test_history.items():
                        if test_id in self.tests:
                            self.tests[test_id].execution_time = history.get("avg_time", 0)
                            self.tests[test_id].failure_count = history.get("failures", 0)
                            self.tests[test_id].success_count = history.get("successes", 0)
                            
            except Exception as e:
                print(f"加载测试历史失败: {e}")
    
    def save_history(self, history_file: str = "test_history.json") -> None:
        """保存测试历史"""
        history_path = self.project_path / history_file
        try:
            history = {}
            for test_id, test_info in self.tests.items():
                history[test_id] = {
                    "avg_time": test_info.execution_time,
                    "failures": test_info.failure_count,
                    "successes": test_info.success_count,
                    "last_run": test_info.last_run.isoformat() if test_info.last_run else None,
                    "last_result": test_info.last_result
                }
            
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"保存测试历史失败: {e}")
    
    def generate_pytest_command(self, result: SelectionResult, parallel: bool = False) -> str:
        """生成pytest命令"""
        if not result.execution_order:
            return "echo 'No tests selected'"
        
        cmd_parts = ["pytest", "-v"]
        
        if parallel:
            cmd_parts.extend(["-n", "auto"])
        
        test_files = set()
        for test_id in result.execution_order:
            test_file = test_id.split("::")[0]
            test_files.add(test_file)
        
        cmd_parts.extend(sorted(test_files))
        
        return " ".join(cmd_parts)
    
    def print_selection_report(self, result: SelectionResult) -> None:
        """打印选择报告"""
        print("\n" + "=" * 80)
        print("智能测试选择报告")
        print("=" * 80)
        
        print(f"\n选择统计:")
        print(f"  已选择测试: {len(result.selected_tests)}")
        print(f"  跳过测试: {len(result.skipped_tests)}")
        print(f"  预计执行时间: {result.estimated_time:.2f}秒")
        print(f"  覆盖率估计: {result.coverage_estimate:.1f}%")
        
        print(f"\n执行顺序 (前10个):")
        for i, test_id in enumerate(result.execution_order[:10], 1):
            reason = result.selection_reason.get(test_id, "N/A")
            priority = result.priority_scores.get(test_id, 0.0)
            print(f"  {i}. {test_id}")
            print(f"     原因: {reason}")
            print(f"     优先级分数: {priority:.1f}")
        
        if len(result.execution_order) > 10:
            print(f"  ... 还有 {len(result.execution_order) - 10} 个测试")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="优化的智能测试选择器")
    parser.add_argument("--project-path", default=".", help="项目路径")
    parser.add_argument("--since", default="HEAD~1", help="检测变更的起始点")
    parser.add_argument("--strategy", choices=["full", "impact", "priority", "incremental", "smart"],
                       default="smart", help="选择策略")
    parser.add_argument("--max-tests", type=int, help="最大测试数量")
    parser.add_argument("--parallel", action="store_true", help="生成并行执行命令")
    parser.add_argument("--output", choices=["console", "json", "pytest"], default="console", help="输出格式")
    
    args = parser.parse_args()
    
    selector = IntelligentTestSelector(args.project_path)
    selector.load_history()
    
    changes = selector.detect_changes(args.since)
    
    strategy_map = {
        "full": SelectionStrategy.FULL,
        "impact": SelectionStrategy.IMPACT_BASED,
        "priority": SelectionStrategy.PRIORITY_BASED,
        "incremental": SelectionStrategy.INCREMENTAL,
        "smart": SelectionStrategy.SMART,
    }
    
    result = selector.select_tests(
        strategy=strategy_map[args.strategy],
        changes=changes,
        max_tests=args.max_tests
    )
    
    if args.output == "console":
        selector.print_selection_report(result)
    elif args.output == "json":
        print(json.dumps({
            "selected_tests": result.selected_tests,
            "skipped_tests": result.skipped_tests,
            "execution_order": result.execution_order,
            "estimated_time": result.estimated_time,
            "coverage_estimate": result.coverage_estimate,
            "priority_scores": result.priority_scores
        }, indent=2))
    elif args.output == "pytest":
        print(selector.generate_pytest_command(result, args.parallel))
    
    selector.save_history()


if __name__ == "__main__":
    main()
