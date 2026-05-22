#!/usr/bin/env python3
"""
Sanliu 技能集成测试主入口

运行所有测试模块并生成综合报告
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

TEST_DIR = Path(__file__).parent
SKILLSCRIPTS_DIR = TEST_DIR.parent / "skillscripts"
BACKEND_DIR = TEST_DIR.parent / "backend"

sys.path.insert(0, str(TEST_DIR))
sys.path.insert(0, str(SKILLSCRIPTS_DIR))
sys.path.insert(0, str(BACKEND_DIR))

from test_runner import (
    TestRunner, TestReport, TestResult,
    print_header, print_result, save_report
)

REPORT_DIR = TEST_DIR / "reports"


def run_all_tests():
    print_header("Sanliu 技能集成测试套件")
    print(f"测试目录: {TEST_DIR}")
    print(f"开始时间: {datetime.now().isoformat()}")
    print()
    
    all_results = []
    total_passed = 0
    total_failed = 0
    start_time = time.time()
    
    test_modules = [
        ("永久演化模式", "test_evolution"),
        ("跨项目服务", "test_cross_project"),
        ("统一脚本接口", "test_unified_script"),
        ("文档自动生成", "test_doc_generator"),
        ("监控仪表板", "test_monitor_dashboard"),
        ("知识库功能", "test_knowledge_base"),
    ]
    
    for module_name, module_file in test_modules:
        print_header(f"运行测试: {module_name}")
        
        try:
            module = __import__(module_file)
            run_func = getattr(module, f"run_{module_file.replace('test_', '')}_tests", None)
            
            if run_func:
                report = run_func()
                
                for result in report.results:
                    all_results.append(result)
                    if result.passed:
                        total_passed += 1
                    else:
                        total_failed += 1
                
                print(f"\n{module_name} 完成: {report.passed}/{report.total_tests} 通过")
            else:
                print(f"警告: 未找到测试函数 run_{module_file.replace('test_', '')}_tests")
        
        except ImportError as e:
            print(f"警告: 无法导入测试模块 {module_file}: {e}")
            all_results.append(TestResult(
                test_name=module_name,
                module="导入错误",
                passed=False,
                message=f"无法导入测试模块: {e}"
            ))
            total_failed += 1
        except Exception as e:
            print(f"错误: 运行测试模块 {module_file} 时发生异常: {e}")
            all_results.append(TestResult(
                test_name=module_name,
                module="运行错误",
                passed=False,
                message=f"运行测试时发生异常: {e}"
            ))
            total_failed += 1
    
    end_time = time.time()
    duration = end_time - start_time
    
    print_header("测试汇总")
    print(f"总测试数: {total_passed + total_failed}")
    print(f"通过: {total_passed}")
    print(f"失败: {total_failed}")
    print(f"通过率: {(total_passed / (total_passed + total_failed) * 100):.1f}%" if (total_passed + total_failed) > 0 else "0%")
    print(f"总耗时: {duration:.2f} 秒")
    
    final_report = TestReport(
        start_time=datetime.fromtimestamp(start_time).isoformat(),
        end_time=datetime.fromtimestamp(end_time).isoformat()
    )
    final_report.results = all_results
    final_report.total_tests = total_passed + total_failed
    final_report.passed = total_passed
    final_report.failed = total_failed
    
    json_file, md_file = save_report(final_report, REPORT_DIR)
    
    print_header("报告已生成")
    print(f"JSON 报告: {json_file}")
    print(f"Markdown 报告: {md_file}")
    
    return final_report


def run_specific_module(module_name: str):
    module_map = {
        "evolution": "test_evolution",
        "cross_project": "test_cross_project",
        "unified_script": "test_unified_script",
        "doc_generator": "test_doc_generator",
        "monitor_dashboard": "test_monitor_dashboard",
        "knowledge_base": "test_knowledge_base",
    }
    
    if module_name not in module_map:
        print(f"错误: 未知的测试模块 '{module_name}'")
        print(f"可用模块: {', '.join(module_map.keys())}")
        return None
    
    module_file = module_map[module_name]
    
    try:
        module = __import__(module_file)
        run_func = getattr(module, f"run_{module_name}_tests", None)
        
        if run_func:
            report = run_func()
            
            final_report = TestReport(
                start_time=datetime.now().isoformat(),
                end_time=datetime.now().isoformat()
            )
            final_report.results = report.results
            final_report.total_tests = report.total_tests
            final_report.passed = report.passed
            final_report.failed = report.failed
            
            json_file, md_file = save_report(final_report, REPORT_DIR)
            
            print(f"\n报告已生成:")
            print(f"  JSON: {json_file}")
            print(f"  Markdown: {md_file}")
            
            return final_report
        else:
            print(f"错误: 未找到测试函数")
            return None
    
    except ImportError as e:
        print(f"错误: 无法导入测试模块: {e}")
        return None


def print_usage():
    print("用法:")
    print("  python run_all_tests.py              # 运行所有测试")
    print("  python run_all_tests.py <module>     # 运行指定模块测试")
    print()
    print("可用模块:")
    print("  evolution          - 永久演化模式测试")
    print("  cross_project      - 跨项目服务测试")
    print("  unified_script     - 统一脚本接口测试")
    print("  doc_generator      - 文档自动生成测试")
    print("  monitor_dashboard  - 监控仪表板测试")
    print("  knowledge_base     - 知识库功能测试")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help", "help"]:
            print_usage()
            sys.exit(0)
        
        module_name = sys.argv[1]
        report = run_specific_module(module_name)
    else:
        report = run_all_tests()
    
    if report:
        sys.exit(0 if report.failed == 0 else 1)
    else:
        sys.exit(1)
