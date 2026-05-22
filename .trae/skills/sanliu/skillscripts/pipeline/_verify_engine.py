#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SDD-TDD融合引擎验证测试脚本"""
import sys
import os
import tempfile
import shutil
import json
from datetime import datetime

sys.path.insert(0, '.')

import importlib.util

spec = importlib.util.spec_from_file_location('engine', 'skillscripts/pipeline/sdd_tdd_fusion_engine.py')
engine_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine_module)

SDDSpec = engine_module.SDDSpec
TestCase = engine_module.TestCase
CycleReport = engine_module.CycleReport
FusionPhase = engine_module.FusionPhase
SDDSpecParser = engine_module.SDDSpecParser
TestSkeletonGenerator = engine_module.TestSkeletonGenerator
FailureAnalyzer = engine_module.FailureAnalyzer
TestResult = engine_module.TestResult
ImplementationGuideGenerator = engine_module.ImplementationGuideGenerator
RefactoringAnalyzer = engine_module.RefactoringAnalyzer
ArtifactTracer = engine_module.ArtifactTracer
ReportGenerator = engine_module.ReportGenerator
FusionEngineConfig = engine_module.FusionEngineConfig
SDDTDDFusionEngine = engine_module.SDDTDDFusionEngine
Path = engine_module.Path

print('=' * 60)
print('SDD-TDD 融合引擎 验证测试')
print('=' * 60)

tmpdir = tempfile.mkdtemp()
passed = 0
failed = 0

def test(name, func):
    global passed, failed
    print(f'\n[{name}] {func.__doc__}...')
    try:
        func()
        print(f'  ✅ 通过')
        passed += 1
    except Exception as e:
        print(f'  ❌ 失败: {e}')
        failed += 1

def test_data_models():
    """测试数据模型"""
    spec = SDDSpec(spec_id='TEST-001', title='Test Spec', version='v1.0')
    assert spec.spec_id == 'TEST-001'
    assert spec.title == 'Test Spec'

    tc = TestCase(test_id='TC-001', name='test_func', description='desc',
                 given='g', when='w', then='t')
    assert tc.test_id == 'TC-001'
    assert tc.status == 'pending'

def test_spec_parser():
    """测试SDD规范解析"""
    parser = SDDSpecParser()
    
    md_content = '''# Test Module

Spec ID: SPEC-TEST-001
Version: v1.0

## 功能需求

- Core Feature: This is a critical feature that must work
- Important Feature: This is an important feature  
- Optional Feature: This is an optional feature

## 验收场景

### Scene 1: Success Case
Given: User is logged in with valid credentials
When: User submits login request
Then: System returns success and redirects to home
'''
    spec_path = os.path.join(tmpdir, 'test.md')
    with open(spec_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    parsed_spec = parser.parse(Path(spec_path))
    assert parsed_spec.spec_id == 'SPEC-TEST-001'
    assert parsed_spec.title == 'Test Module'
    assert len(parsed_spec.requirements) >= 3
    assert len(parsed_spec.acceptance_criteria) >= 1
    
    return parsed_spec, spec_path

def test_skeleton_generation():
    """测试骨架生成"""
    parser = SDDSpecParser()
    generator = TestSkeletonGenerator()
    
    md_content = '''# Test Module
Spec ID: SPEC-SKEL-001
Version: v1.0

## 功能需求
- Core Feature: Implement core functionality
'''
    spec_path = os.path.join(tmpdir, 'skel.md')
    with open(spec_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    parsed_spec = parser.parse(Path(spec_path))
    test_cases = generator.generate(parsed_spec)
    
    assert len(test_cases) > 0
    for tc in test_cases:
        assert tc.test_id.startswith('TC-')
        assert len(tc.code) > 0
        assert 'assert False' in tc.code

def test_failure_analysis():
    """测试失败分析"""
    analyzer = FailureAnalyzer()

    test_result = TestResult(
        total_tests=5, passed=2, failed=3,
        test_results=[
            {'name': 'test_a', 'status': 'failed', 'message': 'AssertionError: assert False'},
            {'name': 'test_b', 'status': 'failed', 'message': 'NotImplementedError: not implemented'},
            {'name': 'test_c', 'status': 'failed', 'message': "NameError: name 'x' is not defined"},
            {'name': 'test_d', 'status': 'passed'},
            {'name': 'test_e', 'status': 'passed'}
        ]
    )
    analysis = analyzer.analyze(test_result)

    assert len(analysis.failures) == 3
    assert 'AssertionError' in analysis.failure_patterns
    assert len(analysis.fix_suggestions) > 0
    
    return analysis

def test_implementation_guide():
    """测试实现引导生成"""
    analyzer = FailureAnalyzer()
    guide_gen = ImplementationGuideGenerator()

    test_result = TestResult(
        total_tests=3, passed=0, failed=3,
        test_results=[
            {'name': 'test_create', 'status': 'failed', 'message': 'NotImplementedError'},
            {'name': 'test_query', 'status': 'failed', 'message': 'NameError'}
        ]
    )
    analysis = analyzer.analyze(test_result)

    test_cases = [
        TestCase(test_id='TC-001', name='test_create_order', description='desc',
                 given='g', when='w', then='t'),
        TestCase(test_id='TC-002', name='test_query_order', description='desc',
                 given='g', when='w', then='t'),
    ]

    guide = guide_gen.generate(analysis, test_cases)

    assert guide.guide_id.startswith('GUIDE-')
    assert len(guide.target_tests) > 0
    assert len(guide.implementation_steps) > 0

def test_refactoring_analysis():
    """测试重构分析"""
    ref_analyzer = RefactoringAnalyzer()

    code_path = os.path.join(tmpdir, 'sample_code.py')
    with open(code_path, 'w', encoding='utf-8') as f:
        f.write('''def very_long_function():
    if condition1:
        if condition2:
            if condition3:
                if condition4:
                    pass

def duplicate_func():
    line = "this is a long line that should be split"
    return line
''')

    suggestions = ref_analyzer.suggest(Path(code_path))

    assert isinstance(suggestions, list)

def test_artifact_tracing():
    """测试产物追溯"""
    tracer = ArtifactTracer()
    tracer.register('test_skeleton', Path(os.path.join(tmpdir, 'test.py')))
    tracer.register('code_implementation', Path(os.path.join(tmpdir, 'code.py')))

    trace = tracer.trace('CYCLE-TRACE-001', 'v1.0')

    assert trace.trace_id.startswith('TRACE-')
    assert trace.completeness_score > 0
    assert 'test_skeleton' in trace.artifacts

def test_report_generation():
    """测试报告生成"""
    report_gen = ReportGenerator()
    from datetime import datetime
    now = datetime.now()

    report = CycleReport(
        cycle_id='CYCLE-RPT-001',
        start_time=now,
        end_time=now,
        phase_results={
            'red': {'status': 'passed', 'duration': 1.5, 'metrics': {'tests': 10}},
            'green': {'status': 'passed', 'duration': 0.5},
            'blue': {'status': 'skipped'},
            'regression': {'status': 'passed', 'output': {'stable': True}}
        },
        artifacts=[],
        quality_metrics={'overall_quality': 80.0},
        status='success'
    )

    md_report = report_gen.generate_markdown(report)
    json_report = report_gen.generate_json(report)

    assert '# SDD-TDD 融合循环报告' in md_report
    assert 'CYCLE-RPT-001' in md_report

    data = json.loads(json_report)
    assert data['cycle_id'] == 'CYCLE-RPT-001'
    assert data['status'] == 'success'

def test_full_cycle_execution():
    """测试完整循环执行"""
    parser = SDDSpecParser()
    
    md_content = '''# Order Module
Spec ID: SPEC-CYCLE-001
Version: v1.0

## 功能需求
- Create Order: User can create new order
- Query Order: User can query order status
'''
    spec_path = os.path.join(tmpdir, 'cycle_spec.md')
    with open(spec_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    config = FusionEngineConfig(
        output_dir=os.path.join(tmpdir, 'output'),
        verbose=False,
        enable_refactoring=False,
        enable_regression=False
    )
    fusion_engine = SDDTDDFusionEngine(config)
    cycle_report = fusion_engine.execute_cycle(Path(spec_path))

    assert cycle_report.cycle_id.startswith('CYCLE-')
    assert cycle_report.status in ['success', 'partial_failure', 'failure']
    assert FusionPhase.RED.value in cycle_report.phase_results
    assert FusionPhase.GREEN.value in cycle_report.phase_results
    assert isinstance(cycle_report.quality_metrics, dict)
    assert 'overall_quality' in cycle_report.quality_metrics
    
    return fusion_engine, spec_path

def test_continuous_cycles():
    """测试连续循环执行"""
    parser = SDDSpecParser()
    
    md_content = '''# Minimal Spec
Spec ID: SPEC-CONT-001
Version: v1.0

## 功能需求
- Basic Function: Implement basic function
'''
    spec_path = os.path.join(tmpdir, 'cont_spec.md')
    with open(spec_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    config = FusionEngineConfig(
        output_dir=os.path.join(tmpdir, 'cont_output'),
        verbose=False,
        enable_refactoring=False,
        enable_regression=False
    )
    fusion_engine = SDDTDDFusionEngine(config)
    cont_report = fusion_engine.execute_continuous_cycles(Path(spec_path), max_cycles=2)

    assert cont_report.total_cycles == 2
    assert len(cont_report.cycles) == 2
    assert len(cont_report.quality_trend) == 2

def test_integration_points():
    """测试集成接口"""
    config = FusionEngineConfig(output_dir=tmpdir, verbose=False)
    engine = SDDTDDFusionEngine(config)

    now = datetime.now()
    dummy_report = CycleReport(
        cycle_id='TEST-INT-001',
        start_time=now,
        end_time=now,
        phase_results={},
        artifacts=[],
        quality_metrics={},
        status='success'
    )

    pc_adapter = engine.integrate_with_provincial_coordinator()
    result = pc_adapter.submit_cycle_report(dummy_report)
    assert result['status'] == 'submitted'

    vi_adapter = engine.integrate_with_version_iterator()
    version = vi_adapter.get_current_version()
    assert isinstance(version, str)

    ec_adapter = engine.integrate_with_evolution_controller()
    state = ec_adapter.get_evolution_state()
    assert state['state'] == 'active'

def run_all_tests():
    global passed, failed
    
    test('1-数据模型', test_data_models)
    test('2-规范解析', test_spec_parser)
    test('3-骨架生成', test_skeleton_generation)
    test('4-失败分析', test_failure_analysis)
    test('5-实现引导', test_implementation_guide)
    test('6-重构分析', test_refactoring_analysis)
    test('7-产物追溯', test_artifact_tracing)
    test('8-报告生成', test_report_generation)
    test('9-完整循环', test_full_cycle_execution)
    test('10-连续循环', test_continuous_cycles)
    test('11-集成接口', test_integration_points)

if __name__ == '__main__':
    try:
        run_all_tests()
        
        print('\n' + '=' * 60)
        total = passed + failed
        print(f'测试结果: {passed}/{total} 通过, {failed} 失败')
        
        if failed == 0:
            print('✅ 所有测试通过! SDD-TDD融合引擎功能完整')
        else:
            print(f'⚠️ {failed} 个测试失败')
        print('=' * 60)
        
        shutil.rmtree(tmpdir, ignore_errors=True)
        
        sys.exit(0 if failed == 0 else 1)
        
    except Exception as e:
        print(f'\n❌ 测试运行异常: {e}')
        import traceback
        traceback.print_exc()
        shutil.rmtree(tmpdir, ignore_errors=True)
        sys.exit(1)
