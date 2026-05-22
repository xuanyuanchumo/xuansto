#!/usr/bin/env python3
"""
综合测试报告生成脚本
生成包含后端和前端测试结果的完整报告
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree


def get_sanliu_root() -> Path:
    return Path(__file__).parent.parent


def run_backend_tests() -> dict:
    print("\n" + "=" * 60)
    print("运行后端测试...")
    print("=" * 60)
    
    sanliu_root = get_sanliu_root()
    backend_dir = sanliu_root / "backend"
    os.chdir(backend_dir)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "--cov=app",
        "--cov-report=xml:coverage.xml",
        "--cov-report=json:coverage.json",
        "--junitxml=junit.xml",
        "-v",
        "--tb=short"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    junit_file = backend_dir / "junit.xml"
    test_results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": 0,
        "duration": 0
    }
    
    if junit_file.exists():
        tree = ElementTree.parse(junit_file)
        root = tree.getroot()
        
        test_suites = root.findall(".//testsuite")
        for suite in test_suites:
            test_results["total"] += int(suite.attrib.get("tests", 0))
            test_results["failed"] += int(suite.attrib.get("failures", 0))
            test_results["errors"] += int(suite.attrib.get("errors", 0))
            test_results["skipped"] += int(suite.attrib.get("skipped", 0))
            test_results["duration"] += float(suite.attrib.get("time", 0))
        
        test_results["passed"] = test_results["total"] - test_results["failed"] - test_results["errors"] - test_results["skipped"]
    
    coverage_file = backend_dir / "coverage.json"
    coverage_rate = 0
    
    if coverage_file.exists():
        with open(coverage_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            totals = data.get("totals", {})
            coverage_rate = totals.get("percent_covered", 0)
    
    return {
        "name": "backend",
        "tests": test_results,
        "coverage": round(coverage_rate, 2),
        "success": result.returncode == 0,
        "output": result.stdout[-5000:] if len(result.stdout) > 5000 else result.stdout
    }


def run_frontend_tests() -> dict:
    print("\n" + "=" * 60)
    print("运行前端测试...")
    print("=" * 60)
    
    sanliu_root = get_sanliu_root()
    frontend_dir = sanliu_root / "frontend"
    
    if not (frontend_dir / "package.json").exists():
        return {
            "name": "frontend",
            "tests": {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0, "duration": 0},
            "coverage": 0,
            "success": False,
            "output": "前端目录不存在"
        }
    
    os.chdir(frontend_dir)
    
    try:
        result = subprocess.run(
            ["npm", "run", "test:coverage", "--", "--reporter=json", "--reporter=verbose"],
            capture_output=True,
            text=True,
            shell=True
        )
    except FileNotFoundError:
        return {
            "name": "frontend",
            "tests": {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0, "duration": 0},
            "coverage": 0,
            "success": False,
            "output": "npm未安装"
        }
    
    test_results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": 0,
        "duration": 0
    }
    
    json_output_file = frontend_dir / "test-results.json"
    if json_output_file.exists():
        with open(json_output_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            test_results["total"] = data.get("numTotalTests", 0)
            test_results["passed"] = data.get("numPassedTests", 0)
            test_results["failed"] = data.get("numFailedTests", 0)
            test_results["skipped"] = data.get("numPendingTests", 0)
    else:
        output = result.stdout + result.stderr
        passed_match = re.search(r"(\d+)\s+passed", output)
        failed_match = re.search(r"(\d+)\s+failed", output)
        skipped_match = re.search(r"(\d+)\s+skipped", output)
        
        if passed_match:
            test_results["passed"] = int(passed_match.group(1))
        if failed_match:
            test_results["failed"] = int(failed_match.group(1))
        if skipped_match:
            test_results["skipped"] = int(skipped_match.group(1))
        
        test_results["total"] = test_results["passed"] + test_results["failed"] + test_results["skipped"]
    
    coverage_file = frontend_dir / "coverage" / "coverage-summary.json"
    coverage_rate = 0
    
    if coverage_file.exists():
        with open(coverage_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            total = data.get("total", {})
            lines = total.get("lines", {})
            coverage_rate = lines.get("pct", 0)
    
    return {
        "name": "frontend",
        "tests": test_results,
        "coverage": round(coverage_rate, 2),
        "success": result.returncode == 0,
        "output": result.stdout[-5000:] if len(result.stdout) > 5000 else result.stdout
    }


def generate_html_report(backend_result: dict, frontend_result: dict) -> str:
    sanliu_root = get_sanliu_root()
    reports_dir = sanliu_root / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_file = reports_dir / f"test_report_{timestamp}.html"
    
    backend_tests = backend_result["tests"]
    frontend_tests = frontend_result["tests"]
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>三省六部测试报告 - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }}
        .card {{ background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .card h3 {{ color: #333; margin-bottom: 15px; font-size: 16px; }}
        .stat {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }}
        .stat:last-child {{ border-bottom: none; }}
        .stat-label {{ color: #666; }}
        .stat-value {{ font-weight: 600; }}
        .stat-value.success {{ color: #10b981; }}
        .stat-value.error {{ color: #ef4444; }}
        .stat-value.warning {{ color: #f59e0b; }}
        .progress-bar {{ height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; margin-top: 10px; }}
        .progress-fill {{ height: 100%; border-radius: 4px; transition: width 0.3s; }}
        .progress-fill.high {{ background: #10b981; }}
        .progress-fill.medium {{ background: #f59e0b; }}
        .progress-fill.low {{ background: #ef4444; }}
        .section {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .section h2 {{ color: #333; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #667eea; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }}
        .badge.success {{ background: #d1fae5; color: #065f46; }}
        .badge.error {{ background: #fee2e2; color: #991b1b; }}
        .timestamp {{ color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 三省六部测试报告</h1>
            <p class="timestamp">生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        
        <div class="summary">
            <div class="card">
                <h3>📊 后端测试</h3>
                <div class="stat">
                    <span class="stat-label">总计</span>
                    <span class="stat-value">{backend_tests['total']}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">通过</span>
                    <span class="stat-value success">{backend_tests['passed']}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">失败</span>
                    <span class="stat-value {'error' if backend_tests['failed'] > 0 else ''}">{backend_tests['failed']}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">跳过</span>
                    <span class="stat-value warning">{backend_tests['skipped']}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">覆盖率</span>
                    <span class="stat-value {'success' if backend_result['coverage'] >= 80 else 'error'}">{backend_result['coverage']}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill {'high' if backend_result['coverage'] >= 80 else 'medium' if backend_result['coverage'] >= 60 else 'low'}" style="width: {backend_result['coverage']}%"></div>
                </div>
            </div>
            
            <div class="card">
                <h3>📊 前端测试</h3>
                <div class="stat">
                    <span class="stat-label">总计</span>
                    <span class="stat-value">{frontend_tests['total']}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">通过</span>
                    <span class="stat-value success">{frontend_tests['passed']}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">失败</span>
                    <span class="stat-value {'error' if frontend_tests['failed'] > 0 else ''}">{frontend_tests['failed']}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">跳过</span>
                    <span class="stat-value warning">{frontend_tests['skipped']}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">覆盖率</span>
                    <span class="stat-value {'success' if frontend_result['coverage'] >= 70 else 'error'}">{frontend_result['coverage']}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill {'high' if frontend_result['coverage'] >= 70 else 'medium' if frontend_result['coverage'] >= 50 else 'low'}" style="width: {frontend_result['coverage']}%"></div>
                </div>
            </div>
            
            <div class="card">
                <h3>📋 总体状态</h3>
                <div class="stat">
                    <span class="stat-label">后端状态</span>
                    <span class="badge {'success' if backend_result['success'] else 'error'}">{'✅ 通过' if backend_result['success'] else '❌ 失败'}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">前端状态</span>
                    <span class="badge {'success' if frontend_result['success'] else 'error'}">{'✅ 通过' if frontend_result['success'] else '❌ 失败'}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">后端覆盖率</span>
                    <span class="badge {'success' if backend_result['coverage'] >= 80 else 'error'}">{'✅ 达标' if backend_result['coverage'] >= 80 else '❌ 未达标'} (≥80%)</span>
                </div>
                <div class="stat">
                    <span class="stat-label">前端覆盖率</span>
                    <span class="badge {'success' if frontend_result['coverage'] >= 70 else 'error'}">{'✅ 达标' if frontend_result['coverage'] >= 70 else '❌ 未达标'} (≥70%)</span>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return str(html_file)


def generate_json_report(backend_result: dict, frontend_result: dict) -> str:
    sanliu_root = get_sanliu_root()
    reports_dir = sanliu_root / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = reports_dir / f"test_report_{timestamp}.json"
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "project": "sanliu",
        "backend": {
            "tests": backend_result["tests"],
            "coverage": backend_result["coverage"],
            "success": backend_result["success"]
        },
        "frontend": {
            "tests": frontend_result["tests"],
            "coverage": frontend_result["coverage"],
            "success": frontend_result["success"]
        },
        "thresholds": {
            "backend_coverage": 80,
            "frontend_coverage": 70
        },
        "overall_success": backend_result["success"] and frontend_result["success"],
        "coverage_passed": backend_result["coverage"] >= 80 and frontend_result["coverage"] >= 70
    }
    
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return str(json_file)


def print_summary(backend_result: dict, frontend_result: dict):
    print("\n" + "=" * 60)
    print("测试报告总结")
    print("=" * 60)
    
    backend_tests = backend_result["tests"]
    frontend_tests = frontend_result["tests"]
    
    print(f"\n后端测试:")
    print(f"  总计: {backend_tests['total']} | 通过: {backend_tests['passed']} | 失败: {backend_tests['failed']} | 跳过: {backend_tests['skipped']}")
    print(f"  覆盖率: {backend_result['coverage']}% {'✅' if backend_result['coverage'] >= 80 else '❌'}")
    
    print(f"\n前端测试:")
    print(f"  总计: {frontend_tests['total']} | 通过: {frontend_tests['passed']} | 失败: {frontend_tests['failed']} | 跳过: {frontend_tests['skipped']}")
    print(f"  覆盖率: {frontend_result['coverage']}% {'✅' if frontend_result['coverage'] >= 70 else '❌'}")
    
    overall = backend_result["success"] and frontend_result["success"]
    coverage_ok = backend_result["coverage"] >= 80 and frontend_result["coverage"] >= 70
    
    print("\n" + "-" * 60)
    if overall and coverage_ok:
        print("🎉 所有测试通过，覆盖率达标!")
    elif overall:
        print("⚠️ 测试通过，但覆盖率未达标")
    else:
        print("❌ 部分测试失败")


def main():
    print("综合测试报告生成器")
    print("=" * 60)
    
    backend_result = run_backend_tests()
    frontend_result = run_frontend_tests()
    
    json_report = generate_json_report(backend_result, frontend_result)
    html_report = generate_html_report(backend_result, frontend_result)
    
    print_summary(backend_result, frontend_result)
    
    print(f"\n报告已生成:")
    print(f"  JSON: {json_report}")
    print(f"  HTML: {html_report}")
    
    overall = backend_result["success"] and frontend_result["success"]
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
