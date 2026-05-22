#!/usr/bin/env python3
"""
后端覆盖率报告生成脚本
生成详细的测试覆盖率报告，包括HTML、JSON和XML格式
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree


def get_project_root() -> Path:
    return Path(__file__).parent.parent


def run_coverage() -> bool:
    print("=" * 60)
    print("运行后端测试覆盖率分析...")
    print("=" * 60)
    
    backend_dir = get_project_root()
    os.chdir(backend_dir)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "--cov=app",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--cov-report=json:coverage.json",
        "-v"
    ]
    
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0


def parse_coverage_json() -> dict:
    backend_dir = get_project_root()
    coverage_file = backend_dir / "coverage.json"
    
    if not coverage_file.exists():
        print(f"警告: 覆盖率文件不存在: {coverage_file}")
        return {}
    
    with open(coverage_file, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_coverage_xml() -> dict:
    backend_dir = get_project_root()
    coverage_file = backend_dir / "coverage.xml"
    
    if not coverage_file.exists():
        return {}
    
    tree = ElementTree.parse(coverage_file)
    root = tree.getroot()
    
    line_rate = float(root.attrib.get("line-rate", 0)) * 100
    branch_rate = float(root.attrib.get("branch-rate", 0)) * 100
    
    packages = root.findall(".//package")
    file_coverage = []
    
    for package in packages:
        name = package.attrib.get("name", "")
        classes = package.findall("classes/class")
        for cls in classes:
            filename = cls.attrib.get("filename", "")
            file_line_rate = float(cls.attrib.get("line-rate", 0)) * 100
            file_branch_rate = float(cls.attrib.get("branch-rate", 0)) * 100
            
            lines = cls.findall("lines/line")
            covered_lines = sum(1 for line in lines if line.attrib.get("hits", "0") != "0")
            total_lines = len(lines)
            
            file_coverage.append({
                "file": f"{name}/{filename}" if name else filename,
                "line_rate": round(file_line_rate, 2),
                "branch_rate": round(file_branch_rate, 2),
                "covered_lines": covered_lines,
                "total_lines": total_lines
            })
    
    return {
        "line_rate": round(line_rate, 2),
        "branch_rate": round(branch_rate, 2),
        "files": file_coverage
    }


def generate_summary_report(coverage_data: dict) -> str:
    backend_dir = get_project_root()
    reports_dir = backend_dir / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = reports_dir / f"coverage_summary_{timestamp}.json"
    
    summary = {
        "timestamp": datetime.now().isoformat(),
        "project": "sanliu-backend",
        "coverage": coverage_data,
        "threshold": {
            "minimum": 80,
            "passed": coverage_data.get("line_rate", 0) >= 80
        }
    }
    
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n摘要报告已生成: {report_file}")
    return str(report_file)


def print_coverage_summary(coverage_data: dict):
    print("\n" + "=" * 60)
    print("覆盖率摘要")
    print("=" * 60)
    
    line_rate = coverage_data.get("line_rate", 0)
    branch_rate = coverage_data.get("branch_rate", 0)
    
    print(f"行覆盖率: {line_rate:.2f}%")
    print(f"分支覆盖率: {branch_rate:.2f}%")
    
    threshold = 80
    if line_rate >= threshold:
        print(f"\n✅ 覆盖率达标 (>= {threshold}%)")
    else:
        print(f"\n❌ 覆盖率未达标 (需要 >= {threshold}%)")
    
    files = coverage_data.get("files", [])
    if files:
        print(f"\n文件覆盖率详情 (共 {len(files)} 个文件):")
        print("-" * 60)
        
        sorted_files = sorted(files, key=lambda x: x["line_rate"])
        low_coverage = [f for f in sorted_files if f["line_rate"] < 80]
        
        if low_coverage:
            print("\n低覆盖率文件 (< 80%):")
            for f in low_coverage[:10]:
                print(f"  {f['file']}: {f['line_rate']:.2f}%")


def main():
    print("后端覆盖率报告生成器")
    print("=" * 60)
    
    success = run_coverage()
    
    coverage_data = parse_coverage_xml()
    
    if coverage_data:
        print_coverage_summary(coverage_data)
        generate_summary_report(coverage_data)
    
    html_report = get_project_root() / "htmlcov" / "index.html"
    if html_report.exists():
        print(f"\nHTML报告: {html_report}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
