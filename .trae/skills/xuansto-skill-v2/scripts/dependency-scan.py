#!/usr/bin/env python3
"""
依赖漏洞扫描脚本
功能：扫描依赖库的已知漏洞，生成CVE报告
"""

import argparse
import subprocess
import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='依赖漏洞扫描脚本 - 扫描依赖库的已知漏洞'
    )
    parser.add_argument(
        '--project-type',
        type=str,
        choices=['python', 'node', 'auto'],
        default='auto',
        help='项目类型（默认：auto自动检测）'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='vulnerability-report',
        help='输出目录名称（默认：vulnerability-report）'
    )
    parser.add_argument(
        '--severity',
        type=str,
        choices=['low', 'moderate', 'high', 'critical'],
        default='moderate',
        help='最低严重级别（默认：moderate）'
    )
    parser.add_argument(
        '--project-dir',
        type=str,
        default=None,
        help='项目目录路径（默认：当前目录）'
    )
    parser.add_argument(
        '--fail-on-vuln',
        action='store_true',
        help='发现漏洞时返回非零退出码'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='输出JSON格式报告'
    )
    return parser.parse_args()


def detect_project_type() -> str:
    """
    自动检测项目类型
    
    返回:
        项目类型字符串
    """
    cwd = Path.cwd()
    
    if (cwd / 'requirements.txt').exists() or (cwd / 'pyproject.toml').exists():
        return 'python'
    elif (cwd / 'package.json').exists():
        return 'node'
    elif (cwd / 'pom.xml').exists() or (cwd / 'build.gradle').exists():
        return 'java'
    elif (cwd / 'go.mod').exists():
        return 'go'
    
    return 'python'


def check_safety_installed(project_dir: str = None) -> bool:
    try:
        result = subprocess.run(
            ['pip', 'show', 'safety'],
            capture_output=True,
            text=True,
            cwd=project_dir
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def scan_python_dependencies(severity: str, project_dir: str = None) -> Dict[str, Any]:
    print("\n正在扫描Python依赖...")
    
    vulnerabilities = []
    
    try:
        result = subprocess.run(
            ['safety', 'check', '--json'],
            capture_output=True,
            text=True,
            cwd=project_dir
        )
        
        if result.returncode != 0:
            data = json.loads(result.stdout)
            
            for vuln in data.get('vulnerabilities', []):
                vuln_severity = vuln.get('severity', 'unknown')
                
                severity_order = {'low': 1, 'moderate': 2, 'high': 3, 'critical': 4}
                if severity_order.get(vuln_severity.lower(), 0) >= severity_order.get(severity, 2):
                    vulnerabilities.append({
                        'package': vuln.get('package', 'unknown'),
                        'version': vuln.get('installed_version', 'unknown'),
                        'cve_id': vuln.get('CVE', 'N/A'),
                        'severity': vuln_severity,
                        'description': vuln.get('advisory', '无描述'),
                        'recommendation': f"升级到版本 {vuln.get('safe_versions', '未知')}"
                    })
    
    except json.JSONDecodeError:
        print("无法解析safety输出")
    except FileNotFoundError:
        print("safety工具未找到")
    
    return {
        'type': 'python',
        'scanner': 'safety',
        'vulnerabilities': vulnerabilities,
        'total': len(vulnerabilities)
    }


def scan_node_dependencies(severity: str, project_dir: str = None) -> Dict[str, Any]:
    print("\n正在扫描Node.js依赖...")
    
    vulnerabilities = []
    
    try:
        result = subprocess.run(
            ['npm', 'audit', '--json'],
            capture_output=True,
            text=True,
            cwd=project_dir
        )
        
        data = json.loads(result.stdout)
        
        severity_order = {'low': 1, 'moderate': 2, 'high': 3, 'critical': 4}
        
        advisories = data.get('advisories', {})
        if advisories:
            for advisory in advisories.values():
                vuln_severity = advisory.get('severity', 'unknown')
                
                if severity_order.get(vuln_severity.lower(), 0) >= severity_order.get(severity, 2):
                    vulnerabilities.append({
                        'package': advisory.get('module_name', 'unknown'),
                        'version': advisory.get('findings', [{}])[0].get('version', 'unknown'),
                        'cve_id': advisory.get('cves', ['N/A'])[0],
                        'severity': vuln_severity,
                        'description': advisory.get('overview', '无描述'),
                        'recommendation': advisory.get('recommendation', '更新依赖')
                    })
        
        vulns = data.get('vulnerabilities', {})
        if vulns:
            for pkg_name, vuln_info in vulns.items():
                vuln_severity = vuln_info.get('severity', 'unknown')
                
                if severity_order.get(vuln_severity.lower(), 0) >= severity_order.get(severity, 2):
                    via = vuln_info.get('via', [])
                    cve_id = 'N/A'
                    for v in via:
                        if isinstance(v, dict) and v.get('cve'):
                            cve_id = v['cve']
                            break
                    vulnerabilities.append({
                        'package': pkg_name,
                        'version': vuln_info.get('range', 'unknown'),
                        'cve_id': cve_id,
                        'severity': vuln_severity,
                        'description': vuln_info.get('title', '无描述'),
                        'recommendation': '运行 npm audit fix 修复'
                    })
    
    except json.JSONDecodeError:
        print("无法解析npm audit输出")
    except FileNotFoundError:
        print("npm未找到")
    
    return {
        'type': 'node',
        'scanner': 'npm-audit',
        'vulnerabilities': vulnerabilities,
        'total': len(vulnerabilities)
    }


def generate_report(output_dir: str, report: Dict[str, Any], json_output: bool):
    """
    生成漏洞报告
    
    参数:
        output_dir: 输出目录
        report: 漏洞报告数据
        json_output: 是否输出JSON格式
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if json_output:
        report_file = output_path / f'vulnerability-report-{timestamp}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\nJSON报告已保存: {report_file}")
    
    html_file = output_path / f'vulnerability-report-{timestamp}.html'
    html_content = generate_html_report(report)
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"HTML报告已保存: {html_file}")


def generate_html_report(report: Dict[str, Any]) -> str:
    """
    生成HTML格式报告
    
    参数:
        report: 漏洞报告数据
    
    返回:
        HTML字符串
    """
    severity_colors = {
        'low': '#28a745',
        'moderate': '#ffc107',
        'high': '#fd7e14',
        'critical': '#dc3545'
    }
    
    vuln_rows = ''
    for vuln in report.get('vulnerabilities', []):
        severity = vuln.get('severity', 'unknown').lower()
        color = severity_colors.get(severity, '#6c757d')
        
        vuln_rows += f'''
        <tr>
            <td>{vuln.get('package', 'N/A')}</td>
            <td>{vuln.get('version', 'N/A')}</td>
            <td><span style="background-color: {color}; padding: 2px 8px; border-radius: 4px; color: white;">{severity.upper()}</span></td>
            <td>{vuln.get('cve_id', 'N/A')}</td>
            <td>{vuln.get('description', '无描述')[:100]}...</td>
            <td>{vuln.get('recommendation', 'N/A')}</td>
        </tr>
        '''
    
    html = f'''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>依赖漏洞扫描报告</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; }}
            h1 {{ color: #333; }}
            .summary {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background: #007bff; color: white; }}
            tr:hover {{ background: #f5f5f5; }}
        </style>
    </head>
    <body>
        <h1>🔒 依赖漏洞扫描报告</h1>
        <div class="summary">
            <p><strong>扫描时间:</strong> {report.get('timestamp', 'N/A')}</p>
            <p><strong>项目类型:</strong> {report.get('type', 'N/A')}</p>
            <p><strong>扫描工具:</strong> {report.get('scanner', 'N/A')}</p>
            <p><strong>发现漏洞:</strong> {report.get('total', 0)} 个</p>
        </div>
        <table>
            <thead>
                <tr>
                    <th>包名</th>
                    <th>版本</th>
                    <th>严重级别</th>
                    <th>CVE ID</th>
                    <th>描述</th>
                    <th>建议</th>
                </tr>
            </thead>
            <tbody>
                {vuln_rows}
            </tbody>
        </table>
    </body>
    </html>
    '''
    
    return html


def print_summary(report: Dict[str, Any]):
    """打印漏洞摘要"""
    print(f"\n{'='*60}")
    print("依赖漏洞扫描结果")
    print(f"{'='*60}")
    print(f"项目类型: {report.get('type', 'N/A')}")
    print(f"扫描工具: {report.get('scanner', 'N/A')}")
    print(f"发现漏洞: {report.get('total', 0)} 个")
    
    if report.get('total', 0) > 0:
        print("\n漏洞列表:")
        for i, vuln in enumerate(report.get('vulnerabilities', []), 1):
            print(f"  {i}. {vuln.get('package')} ({vuln.get('version')})")
            print(f"     严重级别: {vuln.get('severity')}")
            print(f"     CVE: {vuln.get('cve_id')}")
    
    print(f"{'='*60}")


def main():
    args = parse_args()
    
    project_dir = args.project_dir
    
    project_type = args.project_type
    if project_type == 'auto':
        project_type = detect_project_type(project_dir)
        print(f"自动检测到项目类型: {project_type}")
    
    if project_type == 'python':
        if not check_safety_installed(project_dir):
            print("safety工具未安装，请运行: pip install safety")
            sys.exit(1)
        report = scan_python_dependencies(args.severity, project_dir)
    elif project_type == 'node':
        report = scan_node_dependencies(args.severity, project_dir)
    else:
        print(f"暂不支持的项目类型: {project_type}")
        sys.exit(1)
    
    report['timestamp'] = datetime.now().isoformat()
    
    generate_report(args.output, report, args.json)
    print_summary(report)
    
    if report.get('total', 0) > 0 and args.fail_on_vuln:
        print("\n发现漏洞，退出码为1")
        sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
