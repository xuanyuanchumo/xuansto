#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""运行所有新增测试文件并生成汇总报告"""

import subprocess
import sys
import re
import io
from pathlib import Path

# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def run_test_file(test_file):
    """运行单个测试文件并返回结果"""
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', test_file, '-q', '--tb=line'],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=Path(__file__).parent
    )
    
    output = result.stdout + result.stderr
    
    passed = 0
    failed = 0
    
    if 'passed' in output.lower():
        passed_match = re.search(r'(\d+) passed', output)
        failed_match = re.search(r'(\d+) failed', output)
        
        if passed_match:
            passed = int(passed_match.group(1))
        if failed_match:
            failed = int(failed_match.group(1))
    
    return {
        'file': test_file,
        'passed': passed,
        'failed': failed,
        'total': passed + failed,
        'output': output[:300]
    }

def main():
    """主函数"""
    print("=" * 70)
    print("三省六部技能系统 - 测试基础设施完善报告")
    print("=" * 70)
    
    # 新增的测试文件列表
    new_test_files = [
        ('skillscripts/core/test_path_config_center_v33.py', 
         'PathConfigCenter模块边界条件测试'),
        ('skillscripts/pipeline/test_sdd_tdd_fusion_engine_v33.py',
         'SDD-TDD融合引擎完整循环测试'),
        ('skillscripts/monitoring/test_quality_monitoring_v33.py',
         '持续质量监控六维体系集成测试'),
        ('skillscripts/core/test_evolution_system_v33.py',
         '自演化四大能力端到端测试'),
        ('backend/tests/test_monitoring_system_v33.py',
         '前后端监控系统API和组件测试')
    ]
    
    total_passed = 0
    total_failed = 0
    total_tests = 0
    results = []
    
    for file_path, description in new_test_files:
        print(f"\n{'-' * 70}")
        print(f"📋 {description}")
        print(f"   文件: {file_path}")
        print("-" * 70)
        
        try:
            result = run_test_file(file_path)
            results.append(result)
            
            total_passed += result['passed']
            total_failed += result['failed']
            total_tests += result['total']
            
            status = "✅ 通过" if result['failed'] == 0 else "⚠️ 部分失败"
            print(f"   结果: {result['passed']} 通过, {result['failed']} 失败 | {status}")
            
            if result['failed'] > 0 and len(result['output']) > 50:
                print(f"   输出: {result['output'][:200]}...")
                
        except Exception as e:
            print(f"   ❌ 错误: {str(e)}")
            results.append({
                'file': file_path,
                'passed': 0,
                'failed': 1,
                'total': 1,
                'output': str(e)
            })
            total_failed += 1
            total_tests += 1
    
    # 输出汇总报告
    print("\n" + "=" * 70)
    print("📊 测试运行结果汇总")
    print("=" * 70)
    
    print(f"\n{'文件':<55} {'通过':>6} {'失败':>6} {'总计':>6}")
    print("-" * 75)
    
    for r in results:
        filename = Path(r['file']).name
        print(f"{filename:<55} {r['passed']:>6} {r['failed']:>6} {r['total']:>6}")
    
    print("-" * 75)
    print(f"{'总计':<55} {total_passed:>6} {total_failed:>6} {total_tests:>6}")
    
    if total_tests > 0:
        pass_rate = (total_passed / total_tests) * 100
        print(f"\n✨ 总体通过率: {pass_rate:.2f}%")
        
        if pass_rate >= 98.0:
            print("🎉 达标! 通过率 >= 98%")
        elif pass_rate >= 95.0:
            print("👍 良好! 通过率 >= 95%")
        else:
            print("⚠️ 需要改进，目标是通过率 >= 98%")
    
    print("\n" + "=" * 70)
    print("📁 创建/修改的测试文件列表:")
    print("=" * 70)
    
    for i, (file_path, description) in enumerate(new_test_files, 1):
        full_path = Path.cwd() / file_path
        exists = "✅ 已创建" if full_path.exists() else "❌ 未找到"
        print(f"{i}. [{exists}] {description}")
        print(f"   路径: {full_path}")
    
    print("\n" + "=" * 70)
    print("📈 新增测试用例统计:")
    print("=" * 70)
    print(f"• 新增测试文件数量: {len(new_test_files)} 个")
    print(f"• 新增测试用例总数: {total_tests} 个 (目标: 150+)")
    print(f"• 测试通过数量: {total_passed} 个")
    print(f"• 测试失败数量: {total_failed} 个")
    
    coverage_categories = [
        ("PathConfigCenter边界条件", 20),
        ("SDD-TDD融合引擎循环", 30),
        ("质量监控六维体系", 40),
        ("自演化四大能力", 25),
        ("前后端监控系统", 35)
    ]
    
    print("\n按类别统计:")
    for category, target in coverage_categories:
        print(f"  • {category}: 目标 {target}+ 用例")
    
    return total_failed == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
