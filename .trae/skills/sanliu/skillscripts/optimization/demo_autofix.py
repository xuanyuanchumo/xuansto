#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动修复功能演示脚本

演示如何使用增强的自动修复功能来检测和修复代码问题。
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(get_path_config().SCRIPTS_DIR / "optimization"))

from problem_detector_extension import ProblemDetectorExtension
from fix_strategy_extension import FixStrategyExtension
from auto_fix_manager import AutoFixManager


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def demo_problem_detection():
    print_section("1. 问题检测演示")

    test_code = '''
import os
import sys
import json
from urllib2 import urlopen
from ConfigParser import ConfigParser

def calculate_sum(a, b):
    result = a + b
    unused_variable = 42
    return result

def unused_function():
    pass

def main():
    data = "test"
    count = 0
    count = count + 1
    return data
'''

    test_file = "demo_test.py"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_code)

    detector = ProblemDetectorExtension()

    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()

    problems = detector.detect_all(content, test_file)

    print(f"\n检测到 {len(problems)} 个问题:")
    for i, problem in enumerate(problems, 1):
        print(f"\n{i}. [{problem.severity.value}] {problem.message}")
        print(f"   类型: {problem.problem_type}")
        print(f"   位置: 行 {problem.line_number}")
        print(f"   可自动修复: {'是' if problem.auto_fixable else '否'}")
        if problem.suggestion:
            print(f"   建议: {problem.suggestion}")

    os.remove(test_file)


def demo_fix_strategies():
    print_section("2. 修复策略演示")

    library = FixStrategyExtension()

    strategies = library.list_strategies()

    print(f"\n共有 {len(strategies)} 个修复策略:")
    for strategy in strategies:
        print(f"\n  {strategy['name']}:")
        print(f"    描述: {strategy['description']}")
        print(f"    类别: {strategy['category']}")
        print(f"    优先级: {strategy['priority']}")
        print(f"    适用问题: {', '.join(strategy['applicable_problems'])}")


def demo_auto_fix():
    print_section("3. 自动修复演示")

    test_code = '''
import os
import sys
import unused_module
from urllib2 import urlopen

def calculate(a, b):
    result = a + b
    unused_var = 42
    return result

def unused_func():
    pass

def main():
    data = load_data()
    count = 0
    count = count + 1
    return data
'''

    test_file = "demo_autofix_test.py"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_code)

    print("\n原始代码:")
    print(test_code)

    manager = AutoFixManager()

    print("\n检测问题...")
    problems = manager.detect_problems(test_file)
    print(f"发现 {len(problems)} 个问题")

    print("\n自动修复...")
    results = manager.auto_fix_file(test_file, max_fixes=5, create_backup=True, verify=False)

    print(f"\n执行了 {len(results)} 次修复:")
    for result in results:
        print(f"  - {result.fix_result.strategy_name}: {result.fix_result.status.value}")

    print("\n修复后代码:")
    with open(test_file, 'r', encoding='utf-8') as f:
        print(f.read())

    print("\n修复历史:")
    history = manager.get_fix_history(test_file)
    if history:
        print(f"  总修复次数: {history.total_fixes}")
        print(f"  成功修复: {history.successful_fixes}")

    if os.path.exists(".fix_backups"):
        import shutil
        shutil.rmtree(".fix_backups")

    if os.path.exists(".fix_history"):
        import shutil
        shutil.rmtree(".fix_history")

    os.remove(test_file)


def demo_preview_fix():
    print_section("4. 修复预览演示")

    test_code = '''
def calculate(a, b):
    result = a + b
    return result
'''

    test_file = "demo_preview_test.py"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_code)

    manager = AutoFixManager()

    problems = manager.detect_problems(test_file)

    if problems:
        problem = problems[0]
        print(f"\n问题: {problem.message}")
        print(f"位置: 行 {problem.line_number}")

        preview = manager.preview_fix(test_file, problem)

        if preview:
            print(f"\n修复策略: {preview.fix_result.strategy_name}")
            print(f"置信度: {preview.fix_result.confidence:.0%}")
            print(f"\n原始代码片段:")
            print(preview.original_content[:200])
            print(f"\n修复后代码片段:")
            print(preview.fixed_content[:200])

    os.remove(test_file)


def main():
    print_section("三省六部技能 - 自动修复功能演示")

    try:
        demo_problem_detection()
        demo_fix_strategies()
        demo_auto_fix()
        demo_preview_fix()

        print_section("演示完成")
        print("\n所有演示已成功完成！")
        print("\n主要功能:")
        print("  ✓ 问题检测 - 检测导入、类型、未使用代码等问题")
        print("  ✓ 修复策略 - 8种自动修复策略")
        print("  ✓ 自动修复 - 一键修复多个问题")
        print("  ✓ 修复预览 - 预览修复效果")
        print("  ✓ 回滚机制 - 支持修复回滚")
        print("  ✓ 效果验证 - 验证修复效果")
        print("  ✓ 历史记录 - 完整的修复历史")

    except Exception as e:
        print(f"\n演示过程中出现错误: {e}")
        import traceback
from skillscripts.core.path_config_center import get_path_config
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
