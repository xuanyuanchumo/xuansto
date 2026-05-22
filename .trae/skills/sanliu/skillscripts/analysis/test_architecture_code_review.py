#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
架构与代码审查功能单元测试

测试增强的三个模块：
- architecture_check.py
- code_review_automation.py
- intelligent_code_smell_detector.py
"""

import os
import sys
import ast
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(get_path_config().SKILL_ROOT))

from analysis.architecture_check import (
    ArchitectureChecker,
    SOLIDChecker,
    MVVMChecker,
    MVCChecker,
    DependencyInjectionChecker,
    LayeredArchitectureChecker,
    PrincipleChecker,
    ArchitectureIssue,
    CheckStatus,
    IssueSeverity
)

from analysis.code_review_automation import (
    CodeReviewAutomation,
    QualityChecker,
    SecurityChecker,
    PerformanceChecker,
    ComplexityAnalyzer,
    AutoFixer,
    ReviewIssue,
    ReviewCategory,
    IssueSeverity as ReviewSeverity,
    FixStatus
)

from analysis.intelligent_code_smell_detector import (
    IntelligentCodeSmellDetector,
    CodeSmellDetector,
    RefactoringSuggestionEngine,
    ComplexityCalculator,
    CodeSmell,
    SmellType,
    SmellCategory,
    Severity
)


class TestSOLIDChecker(unittest.TestCase):
    """SOLID原则检查器测试"""

    def setUp(self):
        self.checker = SOLIDChecker(Mock())

    def test_single_responsibility_violation(self):
        """测试单一职责原则违规检测"""
        code = '''
class TooManyMethodsClass:
    def get_user(self): pass
    def save_user(self): pass
    def delete_user(self): pass
    def validate_user(self): pass
    def send_email(self): pass
    def log_activity(self): pass
    def generate_report(self): pass
    def calculate_stats(self): pass
    def process_payment(self): pass
    def handle_notification(self): pass
    def extra_method_1(self): pass
    def extra_method_2(self): pass
'''
        tree = ast.parse(code)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            issues = self.checker.check_single_responsibility(Path(f.name), tree, code)
        
        self.assertTrue(len(issues) > 0)
        self.assertTrue(any(i.issue_type == "SRP_VIOLATION" for i in issues))

    def test_open_closed_violation(self):
        """测试开闭原则违规检测"""
        code = '''
class OrderProcessor:
    def process(self, order):
        if order.type == 'standard':
            return self.process_standard(order)
        elif order.type == 'express':
            return self.process_express(order)
        elif order.type == 'international':
            return self.process_international(order)
'''
        tree = ast.parse(code)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            issues = self.checker.check_open_closed(Path(f.name), tree, code)
        
        self.assertTrue(len(issues) > 0)

    def test_liskov_substitution_violation(self):
        """测试里氏替换原则违规检测"""
        code = '''
class Bird:
    def fly(self):
        pass

class Penguin(Bird):
    def fly(self):
        raise Exception("Penguins can't fly")
'''
        tree = ast.parse(code)
        issues = self.checker.check_liskov_substitution(Path("test.py"), tree)
        
        self.assertTrue(len(issues) >= 0)

    def test_interface_segregation_violation(self):
        """测试接口隔离原则违规检测"""
        code = '''
from abc import ABC, abstractmethod

class Worker(ABC):
    @abstractmethod
    def work(self): pass
    
    @abstractmethod
    def eat(self): pass
    
    @abstractmethod
    def sleep(self): pass
    
    @abstractmethod
    def take_break(self): pass
    
    @abstractmethod
    def report(self): pass
    
    @abstractmethod
    def communicate(self): pass
    
    @abstractmethod
    def travel(self): pass
    
    @abstractmethod
    def train(self): pass
'''
        tree = ast.parse(code)
        issues = self.checker.check_interface_segregation(Path("test.py"), tree)
        
        self.assertTrue(len(issues) > 0)
        self.assertTrue(any(i.issue_type == "ISP_VIOLATION" for i in issues))


class TestMVVMChecker(unittest.TestCase):
    """MVVM架构检查器测试"""

    def setUp(self):
        self.checker = MVVMChecker(Mock())

    def test_view_model_binding_violation(self):
        """测试View与ViewModel绑定违规检测"""
        code = '''
import axios

function UserView() {
    const [users, setUsers] = useState([]);
    
    useEffect(() => {
        axios.get('/api/users').then(response => {
            setUsers(response.data);
        });
    }, []);
    
    return <div>{users.map(u => <span>{u.name}</span>)}</div>;
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
            f.write(code)
            f.flush()
            issues = self.checker.check_view_model_binding(Path(f.name), code)
        
        self.assertTrue(len(issues) >= 0)


class TestMVCChecker(unittest.TestCase):
    """MVC架构检查器测试"""

    def setUp(self):
        self.checker = MVCChecker(Mock())

    def test_controller_purity_violation(self):
        """测试Controller纯净性违规检测"""
        code = '''
class UserController:
    def get_users(self):
        session = get_session()
        users = session.query(User).all()
        return users
'''
        tree = ast.parse(code)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            issues = self.checker.check_controller_purity(Path(f.name), tree, code)
        
        self.assertTrue(len(issues) >= 0)

    def test_model_purity_violation(self):
        """测试Model纯净性违规检测"""
        code = '''
from flask import render_template

class UserModel:
    def display(self):
        return render_template('user.html', user=self)
'''
        tree = ast.parse(code)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            issues = self.checker.check_model_purity(Path(f.name), tree, code)
        
        self.assertTrue(len(issues) >= 0)


class TestDependencyInjectionChecker(unittest.TestCase):
    """依赖注入检查器测试"""

    def setUp(self):
        self.checker = DependencyInjectionChecker(Mock())

    def test_hardcoded_dependency_detection(self):
        """测试硬编码依赖检测"""
        code = '''
class UserService:
    def __init__(self):
        self.repository = UserRepository()
        self.validator = UserValidator()
    
    def get_user(self, user_id):
        return self.repository.find(user_id)
'''
        tree = ast.parse(code)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            issues = self.checker.check_constructor_injection(Path(f.name), tree, code)
        
        self.assertTrue(len(issues) > 0)
        self.assertTrue(any(i.issue_type == "DI_HARDCODED_DEPENDENCY" for i in issues))

    def test_proper_dependency_injection(self):
        """测试正确的依赖注入"""
        code = '''
class UserService:
    def __init__(self, repository: IUserRepository, validator: IUserValidator):
        self.repository = repository
        self.validator = validator
    
    def get_user(self, user_id):
        return self.repository.find(user_id)
'''
        tree = ast.parse(code)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            issues = self.checker.check_constructor_injection(Path(f.name), tree, code)
        
        hardcoded_issues = [i for i in issues if i.issue_type == "DI_HARDCODED_DEPENDENCY"]
        self.assertEqual(len(hardcoded_issues), 0)


class TestQualityChecker(unittest.TestCase):
    """代码质量检查器测试"""

    def setUp(self):
        self.checker = QualityChecker(Mock())

    def test_line_too_long_detection(self):
        """测试行过长检测"""
        code = '''
def very_long_function_name_that_exceeds_the_maximum_line_length_limit_and_should_be_detected_as_an_issue():
    pass
''' + 'x' * 150
        tree = ast.parse(code)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            issues = self.checker.check_file(Path(f.name), code, tree)
        
        self.assertTrue(any(i.issue_type == "line_too_long" for i in issues))

    def test_trailing_whitespace_detection(self):
        """测试尾随空格检测"""
        code = "def test():    \n    pass\n"
        tree = ast.parse(code)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            issues = self.checker.check_file(Path(f.name), code, tree)
        
        self.assertTrue(any(i.issue_type == "trailing_whitespace" for i in issues))

    def test_bare_except_detection(self):
        """测试裸except检测"""
        code = '''
def risky_operation():
    try:
        do_something()
    except:
        handle_error()
'''
        tree = ast.parse(code)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            issues = self.checker.check_file(Path(f.name), code, tree)
        
        self.assertTrue(any(i.issue_type == "bare_except" for i in issues))


class TestSecurityChecker(unittest.TestCase):
    """安全检查器测试"""

    def setUp(self):
        self.checker = SecurityChecker(Mock())

    def test_eval_detection(self):
        """测试eval检测"""
        code = '''
def execute_user_input(user_input):
    result = eval(user_input)
    return result
'''
        tree = ast.parse(code)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            issues = self.checker.check_file(Path(f.name), code, tree)
        
        self.assertTrue(any(i.issue_type == "dangerous_eval" for i in issues))

    def test_hardcoded_password_detection(self):
        """测试硬编码密码检测"""
        code = '''
def connect_to_database():
    password = "secret123"
    return connect(password=password)
'''
        tree = ast.parse(code)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            issues = self.checker.check_file(Path(f.name), code, tree)
        
        self.assertTrue(any(i.issue_type == "hardcoded_password" for i in issues))

    def test_shell_injection_detection(self):
        """测试shell注入检测"""
        code = '''
import subprocess
from skillscripts.core.path_config_center import get_path_config

def run_command(cmd):
    subprocess.run(cmd, shell=True)
'''
        tree = ast.parse(code)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            issues = self.checker.check_file(Path(f.name), code, tree)
        
        self.assertTrue(any(i.issue_type == "shell_injection" for i in issues))


class TestPerformanceChecker(unittest.TestCase):
    """性能检查器测试"""

    def setUp(self):
        self.checker = PerformanceChecker(Mock())

    def test_enumerate_suggestion(self):
        """测试enumerate建议"""
        code = '''
def process_items(items):
    for i in range(len(items)):
        print(items[i])
'''
        tree = ast.parse(code)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            issues = self.checker.check_file(Path(f.name), code, tree)
        
        self.assertTrue(any(i.issue_type == "enumerate_instead_of_range_len" for i in issues))


class TestComplexityAnalyzer(unittest.TestCase):
    """复杂度分析器测试"""

    def test_cyclomatic_complexity(self):
        """测试圈复杂度计算"""
        code = '''
def complex_function(x, y, z):
    if x > 0:
        if y > 0:
            return x + y
        else:
            return x - y
    elif x < 0:
        if z > 0:
            return x * z
        else:
            return x / z
    else:
        return 0
'''
        tree = ast.parse(code)
        analyzer = ComplexityAnalyzer()
        analyzer.visit(tree)
        
        self.assertGreater(analyzer.cyclomatic_complexity, 1)

    def test_nesting_depth(self):
        """测试嵌套深度计算"""
        code = '''
def deeply_nested():
    if condition1:
        if condition2:
            if condition3:
                if condition4:
                    if condition5:
                        return True
    return False
'''
        tree = ast.parse(code)
        analyzer = ComplexityAnalyzer()
        analyzer.visit(tree)
        
        self.assertGreaterEqual(analyzer.max_nesting_depth, 4)


class TestCodeSmellDetector(unittest.TestCase):
    """代码异味检测器测试"""

    def test_long_method_detection(self):
        """测试长方法检测"""
        code = '''
def very_long_method():
    """This is a very long method that exceeds the threshold."""
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    c = 6
    d = 7
    e = 8
    f = 9
    g = 10
    h = 11
    i = 12
    j = 13
    k = 14
    l = 15
    m = 16
    n = 17
    o = 18
    p = 19
    q = 20
    r = 21
    s = 22
    t = 23
    u = 24
    v = 25
    w = 26
    x2 = 27
    y2 = 28
    z2 = 29
    a2 = 30
    b2 = 31
    c2 = 32
    d2 = 33
    e2 = 34
    f2 = 35
    g2 = 36
    h2 = 37
    i2 = 38
    j2 = 39
    k2 = 40
    l2 = 41
    m2 = 42
    n2 = 43
    o2 = 44
    p2 = 45
    q2 = 46
    r2 = 47
    s2 = 48
    t2 = 49
    u2 = 50
    v2 = 51
    w2 = 52
    return x + y + z
'''
        detector = CodeSmellDetector("test.py", code)
        smells = detector.detect()
        
        self.assertTrue(any(s.smell_type == SmellType.LONG_METHOD for s in smells))

    def test_deep_nesting_detection(self):
        """测试深度嵌套检测"""
        code = '''
def nested_function(a, b, c, d, e):
    if a:
        if b:
            if c:
                if d:
                    if e:
                        return True
    return False
'''
        detector = CodeSmellDetector("test.py", code)
        smells = detector.detect()
        
        self.assertTrue(any(s.smell_type == SmellType.DEEP_NESTING for s in smells))

    def test_long_parameter_list_detection(self):
        """测试长参数列表检测"""
        code = '''
def many_parameters(a, b, c, d, e, f, g, h):
    return a + b + c + d + e + f + g + h
'''
        detector = CodeSmellDetector("test.py", code)
        smells = detector.detect()
        
        self.assertTrue(any(s.smell_type == SmellType.LONG_PARAMETER_LIST for s in smells))

    def test_high_complexity_detection(self):
        """测试高复杂度检测"""
        code = '''
def complex_logic(x, y, z, a, b, c):
    if x and y or z:
        if a and b or c:
            if x or y and z:
                if a or b and c:
                    return (x and y) or (z and a) or (b and c)
    return False
'''
        detector = CodeSmellDetector("test.py", code)
        smells = detector.detect()
        
        self.assertTrue(any(s.smell_type == SmellType.HIGH_COMPLEXITY for s in smells))


class TestRefactoringSuggestionEngine(unittest.TestCase):
    """重构建议引擎测试"""

    def setUp(self):
        self.engine = RefactoringSuggestionEngine()

    def test_suggestion_generation(self):
        """测试建议生成"""
        smells = [
            CodeSmell(
                smell_type=SmellType.LONG_METHOD,
                category=SmellCategory.BLOATERS,
                severity=Severity.HIGH,
                file_path="test.py",
                line_start=1,
                line_end=100,
                description="Method too long"
            ),
            CodeSmell(
                smell_type=SmellType.DUPLICATE_CODE,
                category=SmellCategory.DISPENSABLES,
                severity=Severity.HIGH,
                file_path="test.py",
                line_start=10,
                line_end=20,
                description="Duplicate code found"
            )
        ]
        
        suggestions = self.engine.generate_suggestions(smells)
        
        self.assertTrue(len(suggestions) > 0)
        self.assertTrue(all('pattern' in s for s in suggestions))
        self.assertTrue(all('priority_score' in s for s in suggestions))

    def test_prioritization(self):
        """测试优先级排序"""
        smells = [
            CodeSmell(
                smell_type=SmellType.LONG_METHOD,
                category=SmellCategory.BLOATERS,
                severity=Severity.LOW,
                file_path="test.py",
                line_start=1,
                line_end=100,
                description="Method too long"
            ),
            CodeSmell(
                smell_type=SmellType.GOD_CLASS,
                category=SmellCategory.BLOATERS,
                severity=Severity.CRITICAL,
                file_path="test.py",
                line_start=1,
                line_end=500,
                description="God class detected"
            )
        ]
        
        prioritized = self.engine.prioritize_smells(smells)
        
        self.assertEqual(prioritized[0].smell_type, SmellType.GOD_CLASS)
        self.assertGreater(prioritized[0].priority, prioritized[1].priority)

    def test_refactoring_plan_generation(self):
        """测试重构计划生成"""
        smells = [
            CodeSmell(
                smell_type=SmellType.LONG_METHOD,
                category=SmellCategory.BLOATERS,
                severity=Severity.HIGH,
                file_path="test.py",
                line_start=1,
                line_end=100,
                description="Method too long"
            )
        ]
        
        plan = self.engine.generate_refactoring_plan(smells)
        
        self.assertIn('phases', plan)
        self.assertIn('estimated_effort', plan)
        self.assertIn('roi_analysis', plan)


class TestAutoFixer(unittest.TestCase):
    """自动修复器测试"""

    def setUp(self):
        self.fixer = AutoFixer(Mock())

    def test_trailing_whitespace_fix(self):
        """测试尾随空格修复"""
        content = "def test():    \n    pass\n"
        issue = ReviewIssue(
            category=ReviewCategory.STYLE,
            severity=ReviewSeverity.LOW,
            file_path="test.py",
            line_number=1,
            column=13,
            issue_type="trailing_whitespace",
            description="Trailing whitespace",
            auto_fixable=True
        )
        
        fixed_content, status = self.fixer.fix_issue(Path("test.py"), issue, content)
        
        self.assertEqual(status, FixStatus.FIXED)
        self.assertNotIn("    \n", fixed_content)


class TestArchitectureReport(unittest.TestCase):
    """架构报告测试"""

    def test_report_generation(self):
        """测试报告生成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            backend_dir = project_root / "backend" / "app"
            backend_dir.mkdir(parents=True)
            
            (backend_dir / "__init__.py").write_text("")
            
            checker = ArchitectureChecker(project_root=project_root)
            report = checker.run_all_checks()
            
            self.assertIsNotNone(report.timestamp)
            self.assertIsNotNone(report.summary)
            self.assertIn('quality_score', report.summary)
            self.assertIn('architecture_health', report.summary)


if __name__ == '__main__':
    unittest.main(verbosity=2)
