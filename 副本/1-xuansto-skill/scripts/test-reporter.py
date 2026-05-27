#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试报告生成脚本
功能：聚合测试结果生成HTML报告
"""

import argparse
import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from xml.etree import ElementTree as ET


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='测试报告生成脚本 - 聚合测试结果生成HTML报告'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='test-results',
        help='测试结果目录（默认：test-results）'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='test-report',
        help='输出目录名称（默认：test-report）'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['html', 'json', 'all'],
        default='html',
        help='报告格式（默认：html）'
    )
    parser.add_argument(
        '--title',
        type=str,
        default='测试报告',
        help='报告标题（默认：测试报告）'
    )
    parser.add_argument(
        '--include-screenshots',
        action='store_true',
        help='包含截图（如果有）'
    )
    return parser.parse_args()


class TestResultParser:
    """测试结果解析器"""
    
    def __init__(self, input_dir: str):
        """
        初始化解析器
        
        参数:
            input_dir: 测试结果目录
        """
        self.input_dir = Path(input_dir)
        self.results = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0,
            'duration': 0,
            'test_suites': []
        }
    
    def parse_all(self) -> Dict[str, Any]:
        """
        解析所有测试结果
        
        返回:
            测试结果字典
        """
        if not self.input_dir.exists():
            print(f"测试结果目录不存在: {self.input_dir}")
            return self.results
        
        junit_files = list(self.input_dir.glob('**/*.xml'))
        for junit_file in junit_files:
            self._parse_junit_xml(junit_file)
        
        json_files = list(self.input_dir.glob('**/*.json'))
        for json_file in json_files:
            if 'test' in json_file.name.lower() or 'result' in json_file.name.lower():
                self._parse_json_result(json_file)
        
        self._calculate_totals()
        
        return self.results
    
    def _parse_junit_xml(self, xml_path: Path):
        """
        解析JUnit XML格式测试结果
        
        参数:
            xml_path: XML文件路径
        """
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            test_suites = root.findall('.//testsuite')
            if not test_suites:
                test_suites = [root]
            
            for suite in test_suites:
                suite_result = {
                    'name': suite.get('name', 'Unknown Suite'),
                    'tests': int(suite.get('tests', 0)),
                    'failures': int(suite.get('failures', 0)),
                    'errors': int(suite.get('errors', 0)),
                    'skipped': int(suite.get('skipped', 0)),
                    'time': float(suite.get('time', 0)),
                    'test_cases': []
                }
                
                for testcase in suite.findall('testcase'):
                    case_result = {
                        'name': testcase.get('name', 'Unknown Test'),
                        'classname': testcase.get('classname', ''),
                        'time': float(testcase.get('time', 0)),
                        'status': 'passed'
                    }
                    
                    failure = testcase.find('failure')
                    error = testcase.find('error')
                    skipped = testcase.find('skipped')
                    
                    if failure is not None:
                        case_result['status'] = 'failed'
                        case_result['message'] = failure.get('message', '')
                        case_result['details'] = failure.text or ''
                    elif error is not None:
                        case_result['status'] = 'error'
                        case_result['message'] = error.get('message', '')
                        case_result['details'] = error.text or ''
                    elif skipped is not None:
                        case_result['status'] = 'skipped'
                        case_result['message'] = skipped.get('message', '')
                    
                    suite_result['test_cases'].append(case_result)
                
                self.results['test_suites'].append(suite_result)
                
        except Exception as e:
            print(f"解析JUnit XML失败 {xml_path}: {e}")
    
    def _parse_json_result(self, json_path: Path):
        """
        解析JSON格式测试结果
        
        参数:
            json_path: JSON文件路径
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict):
                if 'testResults' in data:
                    results = data['testResults']
                elif 'results' in data:
                    results = data['results']
                else:
                    results = [data]
            elif isinstance(data, list):
                results = data
            else:
                return
            
            for result in results:
                suite_result = {
                    'name': result.get('name', json_path.stem),
                    'tests': result.get('numPassingTests', 0) + result.get('numFailingTests', 0),
                    'failures': result.get('numFailingTests', 0),
                    'errors': 0,
                    'skipped': result.get('numPendingTests', 0),
                    'time': result.get('duration', 0) / 1000,
                    'test_cases': []
                }
                
                assertion_results = result.get('assertionResults', [])
                for assertion in assertion_results:
                    case_result = {
                        'name': assertion.get('fullName', assertion.get('title', 'Unknown')),
                        'classname': assertion.get('ancestorTitles', [''])[0] if assertion.get('ancestorTitles') else '',
                        'time': 0,
                        'status': 'passed' if assertion.get('status') == 'passed' else 'failed'
                    }
                    
                    if assertion.get('failureMessages'):
                        case_result['message'] = assertion['failureMessages'][0]
                    
                    suite_result['test_cases'].append(case_result)
                
                self.results['test_suites'].append(suite_result)
                
        except Exception as e:
            print(f"解析JSON失败 {json_path}: {e}")
    
    def _calculate_totals(self):
        """计算总计"""
        for suite in self.results['test_suites']:
            self.results['total'] += suite['tests']
            self.results['failed'] += suite['failures']
            self.results['errors'] += suite['errors']
            self.results['skipped'] += suite['skipped']
            self.results['duration'] += suite['time']
        
        self.results['passed'] = (
            self.results['total'] - 
            self.results['failed'] - 
            self.results['errors'] - 
            self.results['skipped']
        )


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, results: Dict[str, Any], title: str):
        """
        初始化生成器
        
        参数:
            results: 测试结果
            title: 报告标题
        """
        self.results = results
        self.title = title
    
    def generate_html(self) -> str:
        """
        生成HTML报告
        
        返回:
            HTML字符串
        """
        pass_rate = 0
        if self.results['total'] > 0:
            pass_rate = (self.results['passed'] / self.results['total']) * 100
        
        status_color = '#28a745' if pass_rate >= 80 else '#ffc107' if pass_rate >= 50 else '#dc3545'
        
        suite_rows = ''
        for suite in self.results['test_suites']:
            suite_pass = suite['tests'] - suite['failures'] - suite['errors'] - suite['skipped']
            suite_status = '✅' if suite['failures'] == 0 and suite['errors'] == 0 else '❌'
            
            case_rows = ''
            for case in suite['test_cases']:
                status_icon = {'passed': '✅', 'failed': '❌', 'skipped': '⏭️', 'error': '⚠️'}.get(case['status'], '❓')
                case_rows += f'''
                <tr class="test-case {case['status']}">
                    <td>{status_icon}</td>
                    <td>{case['name']}</td>
                    <td>{case['time']:.3f}s</td>
                    <td>{case.get('message', '')[:100] if case.get('message') else ''}</td>
                </tr>
                '''
            
            suite_rows += f'''
            <tr class="suite-header" onclick="toggleSuite('{suite['name'].replace(' ', '-')}')">
                <td>{suite_status}</td>
                <td colspan="4"><strong>{suite['name']}</strong> ({suite_pass}/{suite['tests']} 通过)</td>
            </tr>
            {case_rows}
            '''
        
        html = f'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.title}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: #f5f5f5; 
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #333; margin-bottom: 20px; }}
        .summary {{ 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
            margin-bottom: 20px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
            gap: 15px; 
        }}
        .summary-item {{ text-align: center; padding: 10px; }}
        .summary-item .value {{ font-size: 2em; font-weight: bold; }}
        .summary-item .label {{ color: #666; font-size: 0.9em; }}
        .passed .value {{ color: #28a745; }}
        .failed .value {{ color: #dc3545; }}
        .skipped .value {{ color: #6c757d; }}
        .pass-rate .value {{ color: {status_color}; }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th {{ background: #007bff; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f8f9fa; }}
        .suite-header {{ cursor: pointer; background: #f8f9fa; }}
        .suite-header:hover {{ background: #e9ecef; }}
        .test-case.passed {{ color: #28a745; }}
        .test-case.failed {{ color: #dc3545; }}
        .test-case.skipped {{ color: #6c757d; }}
        .test-case.error {{ color: #fd7e14; }}
        .footer {{ 
            margin-top: 20px; 
            text-align: center; 
            color: #666; 
            font-size: 0.9em; 
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 {self.title}</h1>
        
        <div class="summary">
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="value">{self.results['total']}</div>
                    <div class="label">总测试数</div>
                </div>
                <div class="summary-item passed">
                    <div class="value">{self.results['passed']}</div>
                    <div class="label">通过</div>
                </div>
                <div class="summary-item failed">
                    <div class="value">{self.results['failed']}</div>
                    <div class="label">失败</div>
                </div>
                <div class="summary-item skipped">
                    <div class="value">{self.results['skipped']}</div>
                    <div class="label">跳过</div>
                </div>
                <div class="summary-item pass-rate">
                    <div class="value">{pass_rate:.1f}%</div>
                    <div class="label">通过率</div>
                </div>
                <div class="summary-item">
                    <div class="value">{self.results['duration']:.2f}s</div>
                    <div class="label">总耗时</div>
                </div>
            </div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th width="50">状态</th>
                    <th>测试名称</th>
                    <th width="100">耗时</th>
                    <th>错误信息</th>
                </tr>
            </thead>
            <tbody>
                {suite_rows}
            </tbody>
        </table>
        
        <div class="footer">
            生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
    
    <script>
        function toggleSuite(name) {{
            // 切换测试套件展开/折叠
            console.log('Toggle suite:', name);
        }}
    </script>
</body>
</html>
        '''
        
        return html
    
    def generate_json(self) -> str:
        """
        生成JSON报告
        
        返回:
            JSON字符串
        """
        report = {
            'title': self.title,
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total': self.results['total'],
                'passed': self.results['passed'],
                'failed': self.results['failed'],
                'skipped': self.results['skipped'],
                'errors': self.results['errors'],
                'duration': self.results['duration'],
                'pass_rate': (self.results['passed'] / self.results['total'] * 100) if self.results['total'] > 0 else 0
            },
            'test_suites': self.results['test_suites']
        }
        
        return json.dumps(report, ensure_ascii=False, indent=2)


def main():
    """主函数"""
    args = parse_args()
    
    parser = TestResultParser(args.input)
    results = parser.parse_all()
    
    generator = ReportGenerator(results, args.title)
    
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if args.format in ['html', 'all']:
        html_content = generator.generate_html()
        html_file = output_path / f'test-report-{timestamp}.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"HTML报告已生成: {html_file}")
    
    if args.format in ['json', 'all']:
        json_content = generator.generate_json()
        json_file = output_path / f'test-report-{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            f.write(json_content)
        print(f"JSON报告已生成: {json_file}")
    
    print(f"\n{'='*50}")
    print("测试报告摘要")
    print(f"{'='*50}")
    print(f"总测试数: {results['total']}")
    print(f"通过: {results['passed']}")
    print(f"失败: {results['failed']}")
    print(f"跳过: {results['skipped']}")
    print(f"总耗时: {results['duration']:.2f}s")
    
    if results['total'] > 0:
        pass_rate = (results['passed'] / results['total']) * 100
        print(f"通过率: {pass_rate:.1f}%")
    print(f"{'='*50}")
    
    if results['failed'] > 0 or results['errors'] > 0:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
