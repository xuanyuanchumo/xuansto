#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试运行器 - 运行完整测试套件并生成报告
"""
import sys
import os
import subprocess
import json
from datetime import datetime
from pathlib import Path

def run_tests():
    """运行测试套件并返回结果"""
    backend_dir = Path(__file__).parent.parent / "backend"
    os.chdir(backend_dir)
    
    print("=" * 80)
    print("开始运行测试套件...")
    print("=" * 80)
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "--json-report", "--json-report-file=../reports/test_results.json"],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result

def generate_report(test_result):
    """生成测试报告"""
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "exit_code": test_result.returncode,
        "success": test_result.returncode == 0,
        "output": test_result.stdout,
        "errors": test_result.stderr
    }
    
    report_file = reports_dir / "test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n报告已生成: {report_file}")
    return report_file

if __name__ == "__main__":
    result = run_tests()
    report_file = generate_report(result)
    sys.exit(result.returncode)
