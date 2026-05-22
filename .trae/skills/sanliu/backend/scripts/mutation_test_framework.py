"""
变异测试框架 - 三省六部技能
实现变异测试以验证测试套件的质量
"""
import ast
import copy
import os
import sys
import subprocess
import random
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import time


class MutationType(Enum):
    ARITHMETIC = "arithmetic"
    COMPARISON = "comparison"
    LOGICAL = "logical"
    CONSTANT = "constant"
    BOOLEAN = "boolean"


@dataclass
class MutationResult:
    file_path: str
    line_number: int
    original_code: str
    mutated_code: str
    mutation_type: MutationType
    killed: bool = False
    error: str = ""


class MutationOperator(ast.NodeTransformer):
    def __init__(self, mutation_type: MutationType, target_line: int = None):
        self.mutation_type = mutation_type
        self.target_line = target_line
        self.mutations_made = 0
        self.original_node = None
        self.mutated_node = None
        
    def visit_BinOp(self, node):
        if self.mutations_made > 0:
            return node
        
        if self.target_line and node.lineno != self.target_line:
            return node
        
        if self.mutation_type == MutationType.ARITHMETIC:
            original_op = node.op
            new_op = self._mutate_arithmetic_op(node.op)
            if new_op and new_op != original_op:
                self.original_node = ast.unparse(node)
                node.op = new_op
                self.mutated_node = ast.unparse(node)
                self.mutations_made += 1
        
        self.generic_visit(node)
        return node
    
    def visit_Compare(self, node):
        if self.mutations_made > 0:
            return node
        
        if self.target_line and node.lineno != self.target_line:
            return node
        
        if self.mutation_type == MutationType.COMPARISON:
            new_ops = []
            changed = False
            for op in node.ops:
                new_op = self._mutate_comparison_op(op)
                if new_op:
                    new_ops.append(new_op)
                    if new_op != op:
                        changed = True
                else:
                    new_ops.append(op)
            
            if changed:
                self.original_node = ast.unparse(node)
                node.ops = new_ops
                self.mutated_node = ast.unparse(node)
                self.mutations_made += 1
        
        self.generic_visit(node)
        return node
    
    def visit_BoolOp(self, node):
        if self.mutations_made > 0:
            return node
        
        if self.target_line and node.lineno != self.target_line:
            return node
        
        if self.mutation_type == MutationType.LOGICAL:
            original_op = node.op
            new_op = self._mutate_logical_op(node.op)
            if new_op and new_op != original_op:
                self.original_node = ast.unparse(node)
                node.op = new_op
                self.mutated_node = ast.unparse(node)
                self.mutations_made += 1
        
        self.generic_visit(node)
        return node
    
    def visit_UnaryOp(self, node):
        if self.mutations_made > 0:
            return node
        
        if self.target_line and node.lineno != self.target_line:
            return node
        
        if self.mutation_type == MutationType.LOGICAL:
            if isinstance(node.op, ast.Not):
                self.original_node = ast.unparse(node)
                node.operand = node.operand
                self.mutated_node = ast.unparse(node)
                self.mutations_made += 1
        
        self.generic_visit(node)
        return node
    
    def visit_Constant(self, node):
        if self.mutations_made > 0:
            return node
        
        if self.target_line and hasattr(node, 'lineno') and node.lineno != self.target_line:
            return node
        
        if self.mutation_type == MutationType.CONSTANT:
            if isinstance(node.value, int):
                self.original_node = str(node.value)
                node.value = node.value + 1 if node.value >= 0 else node.value - 1
                self.mutated_node = str(node.value)
                self.mutations_made += 1
            elif isinstance(node.value, float):
                self.original_node = str(node.value)
                node.value = node.value * 1.1
                self.mutated_node = str(node.value)
                self.mutations_made += 1
            elif isinstance(node.value, str) and node.value:
                self.original_node = repr(node.value)
                node.value = ""
                self.mutated_node = repr(node.value)
                self.mutations_made += 1
        
        if self.mutation_type == MutationType.BOOLEAN:
            if isinstance(node.value, bool):
                self.original_node = str(node.value)
                node.value = not node.value
                self.mutated_node = str(node.value)
                self.mutations_made += 1
        
        return node
    
    def _mutate_arithmetic_op(self, op):
        mutations = {
            ast.Add: [ast.Sub, ast.Mult, ast.Div],
            ast.Sub: [ast.Add, ast.Mult, ast.Div],
            ast.Mult: [ast.Add, ast.Sub, ast.Div],
            ast.Div: [ast.Add, ast.Sub, ast.Mult],
            ast.FloorDiv: [ast.Div, ast.Mod],
            ast.Mod: [ast.FloorDiv, ast.Div],
            ast.Pow: [ast.Mult, ast.Add],
        }
        if type(op) in mutations:
            return random.choice(mutations[type(op)])()
        return None
    
    def _mutate_comparison_op(self, op):
        mutations = {
            ast.Eq: [ast.NotEq, ast.Lt, ast.Gt],
            ast.NotEq: [ast.Eq, ast.Lt, ast.Gt],
            ast.Lt: [ast.LtE, ast.Gt, ast.Eq],
            ast.LtE: [ast.Lt, ast.GtE, ast.NotEq],
            ast.Gt: [ast.GtE, ast.Lt, ast.Eq],
            ast.GtE: [ast.Gt, ast.LtE, ast.NotEq],
        }
        if type(op) in mutations:
            return random.choice(mutations[type(op)])()
        return None
    
    def _mutate_logical_op(self, op):
        if isinstance(op, ast.And):
            return ast.Or()
        elif isinstance(op, ast.Or):
            return ast.And()
        return None


class MutationTester:
    def __init__(self, source_dir: str, test_command: str):
        self.source_dir = source_dir
        self.test_command = test_command
        self.results: List[MutationResult] = []
        
    def find_python_files(self) -> List[str]:
        python_files = []
        for root, dirs, files in os.walk(self.source_dir):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'tests']]
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        return python_files
    
    def get_mutable_lines(self, file_path: str) -> List[int]:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source)
        lines = set()
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.BinOp, ast.Compare, ast.BoolOp, ast.UnaryOp)):
                if hasattr(node, 'lineno'):
                    lines.add(node.lineno)
            elif isinstance(node, ast.Constant):
                if hasattr(node, 'lineno') and isinstance(node.value, (int, float, bool, str)):
                    if node.value != "" and node.value is not None:
                        lines.add(node.lineno)
        
        return sorted(lines)
    
    def apply_mutation(self, file_path: str, line_number: int, mutation_type: MutationType) -> Tuple[str, str]:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source)
        operator = MutationOperator(mutation_type, line_number)
        mutated_tree = operator.visit(copy.deepcopy(tree))
        
        if operator.mutations_made == 0:
            return None, None
        
        ast.fix_missing_locations(mutated_tree)
        mutated_source = ast.unparse(mutated_tree)
        
        return operator.original_node, operator.mutated_node
    
    def run_tests(self) -> Tuple[bool, str]:
        try:
            result = subprocess.run(
                self.test_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode != 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return True, "Timeout"
        except Exception as e:
            return True, str(e)
    
    def test_mutation(self, file_path: str, line_number: int, mutation_type: MutationType) -> MutationResult:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_source = f.read()
        
        original_node, mutated_node = self.apply_mutation(file_path, line_number, mutation_type)
        
        if not original_node:
            return None
        
        tree = ast.parse(original_source)
        operator = MutationOperator(mutation_type, line_number)
        mutated_tree = operator.visit(copy.deepcopy(tree))
        ast.fix_missing_locations(mutated_tree)
        mutated_source = ast.unparse(mutated_tree)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(mutated_source)
            
            killed, error = self.run_tests()
            
            result = MutationResult(
                file_path=file_path,
                line_number=line_number,
                original_code=original_node,
                mutated_code=mutated_node,
                mutation_type=mutation_type,
                killed=killed,
                error=error[:200] if error else ""
            )
        finally:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(original_source)
        
        return result
    
    def run_mutation_tests(self, max_mutations: int = 100) -> Dict[str, Any]:
        python_files = self.find_python_files()
        print(f"Found {len(python_files)} Python files to mutate")
        
        total_mutations = 0
        killed_mutations = 0
        survived_mutations = 0
        
        mutation_types = [
            MutationType.ARITHMETIC,
            MutationType.COMPARISON,
            MutationType.LOGICAL,
            MutationType.CONSTANT,
            MutationType.BOOLEAN
        ]
        
        for file_path in python_files:
            print(f"\nTesting file: {file_path}")
            lines = self.get_mutable_lines(file_path)
            print(f"  Found {len(lines)} mutable lines")
            
            for line in lines:
                if total_mutations >= max_mutations:
                    break
                
                for mutation_type in mutation_types:
                    if total_mutations >= max_mutations:
                        break
                    
                    result = self.test_mutation(file_path, line, mutation_type)
                    
                    if result:
                        self.results.append(result)
                        total_mutations += 1
                        
                        if result.killed:
                            killed_mutations += 1
                            status = "KILLED"
                        else:
                            survived_mutations += 1
                            status = "SURVIVED"
                        
                        print(f"  Line {line} ({mutation_type.value}): {status}")
        
        mutation_score = (killed_mutations / total_mutations * 100) if total_mutations > 0 else 0
        
        return {
            "total_mutations": total_mutations,
            "killed": killed_mutations,
            "survived": survived_mutations,
            "mutation_score": mutation_score,
            "results": self.results
        }


def generate_report(results: Dict[str, Any], output_file: str = None):
    report = []
    report.append("=" * 60)
    report.append("变异测试报告 - 三省六部技能")
    report.append("=" * 60)
    report.append("")
    report.append(f"总变异体数量: {results['total_mutations']}")
    report.append(f"已杀死变异体: {results['killed']}")
    report.append(f"存活变异体: {results['survived']}")
    report.append(f"变异得分: {results['mutation_score']:.2f}%")
    report.append("")
    
    if results['mutation_score'] >= 80:
        report.append("✓ 变异得分达标 (≥80%)")
    else:
        report.append("✗ 变异得分未达标 (<80%)")
    
    report.append("")
    report.append("-" * 60)
    report.append("存活的变异体详情:")
    report.append("-" * 60)
    
    for result in results['results']:
        if not result.killed:
            report.append(f"\n文件: {result.file_path}")
            report.append(f"行号: {result.line_number}")
            report.append(f"类型: {result.mutation_type.value}")
            report.append(f"原始代码: {result.original_code}")
            report.append(f"变异代码: {result.mutated_code}")
    
    report.append("")
    report.append("=" * 60)
    
    report_text = "\n".join(report)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
    
    print(report_text)
    return report_text


if __name__ == "__main__":
    source_dir = "app/services/workflow"
    test_command = "python -m pytest -x -q --tb=short --no-cov tests/unit/test_workflow_services.py"
    
    tester = MutationTester(source_dir, test_command)
    results = tester.run_mutation_tests(max_mutations=50)
    
    generate_report(results, "mutation_test_report.txt")
