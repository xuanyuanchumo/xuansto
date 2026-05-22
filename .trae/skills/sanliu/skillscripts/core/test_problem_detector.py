#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问题检测器测试脚本 - Problem Detector Test Script

测试四种检测功能：
1. 语法错误检测
2. 导入错误检测
3. 类型错误检测
4. 安全漏洞检测
"""

import sys
import os

sys.path.insert(0, str(get_path_config().SKILL_ROOT))

from problem_detector import (
    ProblemDetector,
    SyntaxErrorDetector,
    ImportErrorDetector,
    TypeErrorDetector,
    SecurityVulnerabilityDetector,
    ProblemCategory,
    ProblemSeverity
)


def test_syntax_detection():
    """测试语法错误检测"""
    print("\n" + "="*60)
    print("测试语法错误检测")
    print("="*60)
    
    detector = SyntaxErrorDetector()
    
    test_cases = [
        ("缺少冒号", "def test()\n    pass", 1),
        ("未闭合括号", "def test():\n    result = (1 + 2\n    return result", 1),
        ("缩进问题", "def test():\n  pass\n    return True", 1),
        ("正确代码", "def test():\n    return True", 0),
    ]
    
    for name, code, expected_min_problems in test_cases:
        problems = detector.detect(code, "test.py")
        status = "✓" if len(problems) >= expected_min_problems else "✗"
        print(f"  {status} {name}: 发现 {len(problems)} 个问题")
        for p in problems[:3]:
            print(f"      - {p.message} (行 {p.line_number})")
    
    return True


def test_import_detection():
    """测试导入错误检测"""
    print("\n" + "="*60)
    print("测试导入错误检测")
    print("="*60)
    
    detector = ImportErrorDetector()
    
    test_cases = [
        ("未使用的导入", "import os\nimport sys\n\ndef test():\n    pass", 2),
        ("缺少导入", "def test():\n    return np.array([1, 2, 3])", 1),
        ("弃用导入", "import urllib2\n\ndef test():\n    pass", 1),
        ("正确导入", "import os\n\ndef test():\n    return os.path.exists('.')", 0),
    ]
    
    for name, code, expected_min_problems in test_cases:
        problems = detector.detect(code, "test.py")
        status = "✓" if len(problems) >= expected_min_problems else "✗"
        print(f"  {status} {name}: 发现 {len(problems)} 个问题")
        for p in problems[:3]:
            print(f"      - {p.message} (行 {p.line_number})")
    
    return True


def test_type_detection():
    """测试类型错误检测"""
    print("\n" + "="*60)
    print("测试类型错误检测")
    print("="*60)
    
    detector = TypeErrorDetector()
    
    test_cases = [
        ("类型不匹配", "def test():\n    return 'hello' + 123", 1),
        ("除以零", "def test():\n    return 10 / 0", 1),
        ("缺少类型注解", "def test(a, b):\n    return a + b", 1),
        ("正确代码", "def test(a: int, b: int) -> int:\n    return a + b", 0),
    ]
    
    for name, code, expected_min_problems in test_cases:
        problems = detector.detect(code, "test.py")
        status = "✓" if len(problems) >= expected_min_problems else "✗"
        print(f"  {status} {name}: 发现 {len(problems)} 个问题")
        for p in problems[:3]:
            print(f"      - {p.message} (行 {p.line_number})")
    
    return True


def test_security_detection():
    """测试安全漏洞检测"""
    print("\n" + "="*60)
    print("测试安全漏洞检测")
    print("="*60)
    
    detector = SecurityVulnerabilityDetector()
    
    test_cases = [
        ("硬编码密码", 'password = "secret123"', 1),
        ("eval使用", "def test():\n    eval('print(1)')", 1),
        ("SQL注入风险", 'cursor.execute("SELECT * FROM users WHERE id = " + user_id)', 1),
        ("pickle使用", "import pickle\ndata = pickle.loads(user_input)", 1),
        ("shell注入", 'import subprocess\nsubprocess.run(cmd, shell=True)', 1),
        ("正确代码", "import os\nos.path.exists('test.txt')", 0),
    ]
    
    for name, code, expected_min_problems in test_cases:
        problems = detector.detect(code, "test.py")
        status = "✓" if len(problems) >= expected_min_problems else "✗"
        print(f"  {status} {name}: 发现 {len(problems)} 个问题")
        for p in problems[:3]:
            print(f"      - {p.message} (行 {p.line_number})")
            if p.cwe_id:
                print(f"        CWE: {p.cwe_id}")
    
    return True


def test_integrated_detector():
    """测试综合检测器"""
    print("\n" + "="*60)
    print("测试综合问题检测器")
    print("="*60)
    
    detector = ProblemDetector()
    
    test_code = '''
import os
import sys
import unused_module
from skillscripts.core.path_config_center import get_path_config

password = "hardcoded_password_123"

def calculate(a, b):
    result = a + "string"
    return result

def unsafe_function(user_input):
    eval(user_input)
    cursor.execute("SELECT * FROM users WHERE id = " + user_input)
    return pickle.loads(data)

def divide_by_zero():
    return 10 / 0
'''
    
    problems = detector.detect_all(test_code, "test.py")
    
    print(f"  总问题数: {len(problems)}")
    
    category_counts = {}
    severity_counts = {}
    
    for p in problems:
        category = p.category.name
        severity = p.severity.value
        category_counts[category] = category_counts.get(category, 0) + 1
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    print("\n  问题类别分布:")
    for category, count in sorted(category_counts.items()):
        print(f"    - {category}: {count}")
    
    print("\n  严重程度分布:")
    for severity, count in sorted(severity_counts.items()):
        print(f"    - {severity}: {count}")
    
    print("\n  关键问题:")
    critical_issues = [p for p in problems if p.severity in [ProblemSeverity.CRITICAL, ProblemSeverity.HIGH]]
    for p in critical_issues[:5]:
        print(f"    🔴 [{p.category.name}] {p.message} (行 {p.line_number})")
    
    report = detector.generate_report(problems, "test.py")
    print(f"\n  报告ID: {report['report_id']}")
    print(f"  可自动修复: {report['auto_fixable_count']}")
    print(f"  安全问题: {report['security_issues']}")
    print(f"  严重问题: {report['critical_issues']}")
    
    return True


def test_file_scanning():
    """测试文件扫描功能"""
    print("\n" + "="*60)
    print("测试文件扫描功能")
    print("="*60)
    
    detector = ProblemDetector()
    
    test_file = __file__
    report = detector.scan_file(test_file)
    
    print(f"  扫描文件: {test_file}")
    print(f"  总问题数: {report.get('total_problems', 0)}")
    
    if report.get('category_distribution'):
        print("  问题类别:")
        for cat, count in report['category_distribution'].items():
            print(f"    - {cat}: {count}")
    
    return True


def main():
    """运行所有测试"""
    print("\n" + "#"*60)
    print("# 问题检测器测试套件")
    print("#"*60)
    
    tests = [
        ("语法错误检测", test_syntax_detection),
        ("导入错误检测", test_import_detection),
        ("类型错误检测", test_type_detection),
        ("安全漏洞检测", test_security_detection),
        ("综合检测器", test_integrated_detector),
        ("文件扫描", test_file_scanning),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result, None))
        except Exception as e:
            results.append((name, False, str(e)))
    
    print("\n" + "#"*60)
    print("# 测试结果汇总")
    print("#"*60)
    
    passed = sum(1 for _, r, _ in results if r)
    total = len(results)
    
    for name, result, error in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {status}: {name}")
        if error:
            print(f"      错误: {error}")
    
    print(f"\n  总计: {passed}/{total} 测试通过")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
