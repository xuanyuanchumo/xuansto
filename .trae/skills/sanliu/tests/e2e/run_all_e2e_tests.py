"""
端到端测试运行器

执行所有端到端测试并生成综合报告
"""

import sys
import time
import json
from datetime import datetime
from pathlib import Path

backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from test_skill_evolution_e2e import test_complete_evolution_flow
from test_skill_auto_repair_e2e import test_complete_repair_flow
from test_skill_knowledge_accumulation_e2e import test_complete_knowledge_flow
from test_realtime_monitoring_e2e import test_complete_realtime_flow


class E2ETestRunner:
    """端到端测试运行器"""
    
    def __init__(self):
        self.results = []
        self.total_passed = 0
        self.total_failed = 0
        self.start_time = None
        self.end_time = None
        
    def run_test_suite(self, suite_name, test_func):
        """运行单个测试套件"""
        print("\n" + "="*80)
        print(f"开始运行测试套件: {suite_name}")
        print("="*80)
        
        suite_start = time.time()
        
        try:
            passed, failed = test_func()
            suite_end = time.time()
            duration = suite_end - suite_start
            
            result = {
                "suite_name": suite_name,
                "passed": passed,
                "failed": failed,
                "total": passed + failed,
                "success_rate": (passed / (passed + failed) * 100) if (passed + failed) > 0 else 0,
                "duration_seconds": round(duration, 2),
                "status": "success" if failed == 0 else "partial_failure"
            }
            
            self.results.append(result)
            self.total_passed += passed
            self.total_failed += failed
            
            print(f"\n{suite_name} 完成:")
            print(f"  通过: {passed}")
            print(f"  失败: {failed}")
            print(f"  成功率: {result['success_rate']:.2f}%")
            print(f"  耗时: {duration:.2f}秒")
            
            return result
            
            return result
            
        except Exception as e:
            suite_end = time.time()
            duration = suite_end - suite_start
            
            result = {
                "suite_name": suite_name,
                "passed": 0,
                "failed": 1,
                "total": 1,
                "success_rate": 0,
                "duration_seconds": round(duration, 2),
                "status": "error",
                "error": str(e)
            }
            
            self.results.append(result)
            self.total_failed += 1
            
            print(f"\n{suite_name} 执行出错:")
            print(f"  错误: {str(e)}")
            
            return result
    
    def generate_report(self):
        """生成测试报告"""
        self.end_time = time.time()
        total_duration = self.end_time - self.start_time
        
        report = {
            "report_id": f"e2e_report_{int(time.time())}",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_suites": len(self.results),
                "total_tests": self.total_passed + self.total_failed,
                "total_passed": self.total_passed,
                "total_failed": self.total_failed,
                "overall_success_rate": (self.total_passed / (self.total_passed + self.total_failed) * 100) if (self.total_passed + self.total_failed) > 0 else 0,
                "total_duration_seconds": round(total_duration, 2)
            },
            "suites": self.results,
            "issues_found": self._identify_issues(),
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _identify_issues(self):
        """识别发现的问题"""
        issues = []
        
        for result in self.results:
            if result["status"] == "error":
                issues.append({
                    "suite": result["suite_name"],
                    "type": "execution_error",
                    "severity": "high",
                    "description": f"测试套件执行出错: {result.get('error', 'Unknown error')}"
                })
            elif result["failed"] > 0:
                issues.append({
                    "suite": result["suite_name"],
                    "type": "test_failures",
                    "severity": "medium",
                    "description": f"有 {result['failed']} 个测试失败"
                })
        
        return issues
    
    def _generate_recommendations(self):
        """生成改进建议"""
        recommendations = []
        
        if self.total_failed > 0:
            recommendations.append("建议检查失败的测试用例，修复相关问题")
        
        for result in self.results:
            if result["success_rate"] < 80:
                recommendations.append(f"建议重点关注 {result['suite_name']} 测试套件，成功率较低")
        
        if not recommendations:
            recommendations.append("所有测试通过，系统运行正常")
        
        return recommendations
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "="*80)
        print("端到端测试总结")
        print("="*80)
        
        print(f"\n总体统计:")
        print(f"  测试套件数: {len(self.results)}")
        print(f"  总测试数: {self.total_passed + self.total_failed}")
        print(f"  通过数: {self.total_passed}")
        print(f"  失败数: {self.total_failed}")
        
        if (self.total_passed + self.total_failed) > 0:
            success_rate = self.total_passed / (self.total_passed + self.total_failed) * 100
            print(f"  总体成功率: {success_rate:.2f}%")
        
        print(f"\n各测试套件详情:")
        for result in self.results:
            status_icon = "[PASS]" if result["status"] == "success" else "[FAIL]"
            print(f"  {status_icon} {result['suite_name']}")
            print(f"     通过: {result['passed']}, 失败: {result['failed']}, 成功率: {result['success_rate']:.2f}%")
            print(f"     耗时: {result['duration_seconds']}秒")
        
        if self._identify_issues():
            print(f"\n发现的问题:")
            for issue in self._identify_issues():
                print(f"  [{issue['severity'].upper()}] {issue['suite']}: {issue['description']}")
        
        print(f"\n改进建议:")
        for rec in self._generate_recommendations():
            print(f"  - {rec}")
        
        print("\n" + "="*80)


def run_all_e2e_tests():
    """运行所有端到端测试"""
    print("\n" + "="*80)
    print("三省六部系统 - 端到端测试套件")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    runner = E2ETestRunner()
    runner.start_time = time.time()
    
    test_suites = [
        ("技能自演化流程测试", test_complete_evolution_flow),
        ("技能内容自动修复流程测试", test_complete_repair_flow),
        ("技能演化知识积累流程测试", test_complete_knowledge_flow),
        ("前后端实时监控流程测试", test_complete_realtime_flow),
    ]
    
    for suite_name, test_func in test_suites:
        runner.run_test_suite(suite_name, test_func)
    
    report = runner.generate_report()
    runner.print_summary()
    
    report_path = Path(__file__).parent / "e2e_test_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n测试报告已保存到: {report_path}")
    
    return runner.total_failed == 0


if __name__ == "__main__":
    success = run_all_e2e_tests()
    sys.exit(0 if success else 1)
