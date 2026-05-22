#!/usr/bin/env python3
"""
覆盖率阈值检查脚本
检查后端和前端覆盖率是否达标
后端阈值: >= 80%
前端阈值: >= 70%
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree


BACKEND_THRESHOLD = 80
FRONTEND_THRESHOLD = 70


def get_sanliu_root() -> Path:
    return Path(__file__).parent.parent


def check_backend_coverage() -> dict:
    print("\n" + "=" * 60)
    print("检查后端覆盖率...")
    print("=" * 60)
    
    sanliu_root = get_sanliu_root()
    backend_dir = sanliu_root / "backend"
    
    os.chdir(backend_dir)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "--cov=app",
        "--cov-report=xml:coverage.xml",
        "--cov-report=json:coverage.json",
        "-q"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    coverage_file = backend_dir / "coverage.json"
    line_rate = 0
    
    if coverage_file.exists():
        with open(coverage_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            totals = data.get("totals", {})
            line_rate = totals.get("percent_covered", 0)
    else:
        xml_file = backend_dir / "coverage.xml"
        if xml_file.exists():
            tree = ElementTree.parse(xml_file)
            root = tree.getroot()
            line_rate = float(root.attrib.get("line-rate", 0)) * 100
    
    passed = line_rate >= BACKEND_THRESHOLD
    
    print(f"后端行覆盖率: {line_rate:.2f}%")
    print(f"阈值要求: >= {BACKEND_THRESHOLD}%")
    
    if passed:
        print("✅ 后端覆盖率达标")
    else:
        print("❌ 后端覆盖率未达标")
    
    return {
        "name": "backend",
        "line_rate": round(line_rate, 2),
        "threshold": BACKEND_THRESHOLD,
        "passed": passed,
        "test_success": result.returncode == 0
    }


def check_frontend_coverage() -> dict:
    print("\n" + "=" * 60)
    print("检查前端覆盖率...")
    print("=" * 60)
    
    sanliu_root = get_sanliu_root()
    frontend_dir = sanliu_root / "frontend"
    
    if not (frontend_dir / "package.json").exists():
        print("警告: 前端目录不存在package.json")
        return {
            "name": "frontend",
            "line_rate": 0,
            "threshold": FRONTEND_THRESHOLD,
            "passed": False,
            "test_success": False
        }
    
    os.chdir(frontend_dir)
    
    try:
        result = subprocess.run(
            ["npm", "run", "test:coverage", "--", "--reporter=json", "--reporter=text"],
            capture_output=True,
            text=True,
            shell=True
        )
    except FileNotFoundError:
        print("警告: npm未安装或不在PATH中")
        return {
            "name": "frontend",
            "line_rate": 0,
            "threshold": FRONTEND_THRESHOLD,
            "passed": False,
            "test_success": False
        }
    
    coverage_file = frontend_dir / "coverage" / "coverage-summary.json"
    line_rate = 0
    
    if coverage_file.exists():
        with open(coverage_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            total = data.get("total", {})
            lines = total.get("lines", {})
            line_rate = lines.get("pct", 0)
    else:
        final_coverage = frontend_dir / "coverage" / "coverage-final.json"
        if final_coverage.exists():
            with open(final_coverage, "r", encoding="utf-8") as f:
                data = json.load(f)
                total_lines = 0
                covered_lines = 0
                for file_data in data.values():
                    if file_data.get("l"):
                        for hits in file_data["l"].values():
                            total_lines += 1
                            if hits > 0:
                                covered_lines += 1
                if total_lines > 0:
                    line_rate = (covered_lines / total_lines) * 100
    
    passed = line_rate >= FRONTEND_THRESHOLD
    
    print(f"前端行覆盖率: {line_rate:.2f}%")
    print(f"阈值要求: >= {FRONTEND_THRESHOLD}%")
    
    if passed:
        print("✅ 前端覆盖率达标")
    else:
        print("❌ 前端覆盖率未达标")
    
    return {
        "name": "frontend",
        "line_rate": round(line_rate, 2),
        "threshold": FRONTEND_THRESHOLD,
        "passed": passed,
        "test_success": True
    }


def generate_report(backend_result: dict, frontend_result: dict) -> dict:
    sanliu_root = get_sanliu_root()
    reports_dir = sanliu_root / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = reports_dir / f"coverage_check_{timestamp}.json"
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "project": "sanliu",
        "backend": backend_result,
        "frontend": frontend_result,
        "overall_passed": backend_result["passed"] and frontend_result["passed"],
        "summary": {
            "backend_threshold": BACKEND_THRESHOLD,
            "frontend_threshold": FRONTEND_THRESHOLD
        }
    }
    
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n检查报告已生成: {report_file}")
    return report


def print_final_summary(backend_result: dict, frontend_result: dict):
    print("\n" + "=" * 60)
    print("覆盖率检查总结")
    print("=" * 60)
    
    print(f"\n后端: {backend_result['line_rate']:.2f}% (阈值: {BACKEND_THRESHOLD}%) - {'✅ 通过' if backend_result['passed'] else '❌ 未通过'}")
    print(f"前端: {frontend_result['line_rate']:.2f}% (阈值: {FRONTEND_THRESHOLD}%) - {'✅ 通过' if frontend_result['passed'] else '❌ 未通过'}")
    
    overall = backend_result["passed"] and frontend_result["passed"]
    
    print("\n" + "-" * 60)
    if overall:
        print("🎉 所有覆盖率检查通过!")
    else:
        print("⚠️ 部分覆盖率检查未通过，请查看详情")
    
    return overall


def main():
    print("覆盖率阈值检查工具")
    print("=" * 60)
    print(f"后端阈值: >= {BACKEND_THRESHOLD}%")
    print(f"前端阈值: >= {FRONTEND_THRESHOLD}%")
    
    backend_result = check_backend_coverage()
    frontend_result = check_frontend_coverage()
    
    generate_report(backend_result, frontend_result)
    overall_passed = print_final_summary(backend_result, frontend_result)
    
    return 0 if overall_passed else 1


if __name__ == "__main__":
    sys.exit(main())
