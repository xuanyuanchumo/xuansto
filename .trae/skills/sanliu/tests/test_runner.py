#!/usr/bin/env python3
"""
Sanliu 技能集成测试套件

测试模块：
1. 永久演化模式测试
2. 跨项目服务测试
3. 统一脚本接口测试
4. 文档自动生成测试
5. 监控仪表板测试
6. 知识库功能测试
"""

import os
import sys
import json
import time
import asyncio
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
SKILLSCRIPTS_DIR = BASE_DIR.parent / "skillscripts"
BACKEND_DIR = BASE_DIR.parent / "backend"
FRONTEND_DIR = BASE_DIR.parent / "frontend"

sys.path.insert(0, str(SKILLSCRIPTS_DIR))
sys.path.insert(0, str(BACKEND_DIR))


@dataclass
class TestResult:
    test_name: str
    module: str
    passed: bool
    message: str
    duration: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_name": self.test_name,
            "module": self.module,
            "passed": self.passed,
            "message": self.message,
            "duration": self.duration,
            "details": self.details,
            "error": self.error
        }


@dataclass
class TestReport:
    start_time: str
    end_time: str = ""
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    results: List[TestResult] = field(default_factory=list)
    
    def add_result(self, result: TestResult):
        self.results.append(result)
        self.total_tests += 1
        if result.passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "pass_rate": f"{(self.passed / self.total_tests * 100):.1f}%" if self.total_tests > 0 else "0%",
            "results": [r.to_dict() for r in self.results]
        }


class TestRunner:
    def __init__(self):
        self.report = TestReport(start_time=datetime.now().isoformat())
    
    def run_test(self, test_func, module: str, test_name: str) -> TestResult:
        start = time.time()
        try:
            result_data = test_func()
            duration = time.time() - start
            
            if isinstance(result_data, tuple):
                passed, message, details = result_data
            elif isinstance(result_data, dict):
                passed = result_data.get("passed", True)
                message = result_data.get("message", "")
                details = result_data.get("details", {})
            elif isinstance(result_data, bool):
                passed = result_data
                message = "测试通过" if passed else "测试失败"
                details = {}
            else:
                passed = True
                message = str(result_data)
                details = {}
            
            return TestResult(
                test_name=test_name,
                module=module,
                passed=passed,
                message=message,
                duration=duration,
                details=details
            )
        except Exception as e:
            duration = time.time() - start
            return TestResult(
                test_name=test_name,
                module=module,
                passed=False,
                message=f"测试异常: {str(e)}",
                duration=duration,
                error=traceback.format_exc()
            )
    
    async def run_async_test(self, test_func, module: str, test_name: str) -> TestResult:
        start = time.time()
        try:
            result_data = await test_func()
            duration = time.time() - start
            
            if isinstance(result_data, tuple):
                passed, message, details = result_data
            elif isinstance(result_data, dict):
                passed = result_data.get("passed", True)
                message = result_data.get("message", "")
                details = result_data.get("details", {})
            elif isinstance(result_data, bool):
                passed = result_data
                message = "测试通过" if passed else "测试失败"
                details = {}
            else:
                passed = True
                message = str(result_data)
                details = {}
            
            return TestResult(
                test_name=test_name,
                module=module,
                passed=passed,
                message=message,
                duration=duration,
                details=details
            )
        except Exception as e:
            duration = time.time() - start
            return TestResult(
                test_name=test_name,
                module=module,
                passed=False,
                message=f"测试异常: {str(e)}",
                duration=duration,
                error=traceback.format_exc()
            )
    
    def finalize(self):
        self.report.end_time = datetime.now().isoformat()
        return self.report


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_result(result: TestResult):
    status = "✓ 通过" if result.passed else "✗ 失败"
    print(f"  [{status}] {result.test_name} ({result.duration:.2f}s)")
    if result.message:
        print(f"         {result.message}")
    if result.error:
        print(f"         错误: {result.error[:100]}...")


def save_report(report: TestReport, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    json_file = output_dir / f"test_report_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
    
    md_file = output_dir / f"test_report_{timestamp}.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# Sanliu 技能集成测试报告\n\n")
        f.write(f"- **测试时间**: {report.start_time}\n")
        f.write(f"- **结束时间**: {report.end_time}\n")
        f.write(f"- **总测试数**: {report.total_tests}\n")
        f.write(f"- **通过**: {report.passed}\n")
        f.write(f"- **失败**: {report.failed}\n")
        f.write(f"- **通过率**: {(report.passed / report.total_tests * 100):.1f}%\n\n")
        
        modules = {}
        for r in report.results:
            if r.module not in modules:
                modules[r.module] = []
            modules[r.module].append(r)
        
        for module, results in modules.items():
            f.write(f"## {module}\n\n")
            for r in results:
                status = "✓" if r.passed else "✗"
                f.write(f"- {status} **{r.test_name}** ({r.duration:.2f}s)\n")
                if r.message:
                    f.write(f"  - {r.message}\n")
                if r.error:
                    f.write(f"  - 错误: `{r.error[:200]}`\n")
            f.write("\n")
    
    return json_file, md_file


if __name__ == "__main__":
    print_header("Sanliu 技能集成测试套件")
    print(f"测试目录: {BASE_DIR}")
    print(f"开始时间: {datetime.now().isoformat()}")
