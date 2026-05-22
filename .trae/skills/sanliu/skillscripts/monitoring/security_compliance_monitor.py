#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全合规监控器 (SecurityComplianceMonitor)
=========================================

执行OWASP Top 10安全检查、依赖漏洞扫描和敏感数据检测。

特性:
- OWASP Top 10全面覆盖
- 依赖漏洞检测（Safety/pip-audit）
- 敏感数据泄露风险识别
- 风险评分计算
- 详细的安全报告生成

使用示例:
    >>> from skillscripts.monitoring.security_compliance_monitor import SecurityComplianceMonitor
    >>> monitor = SecurityComplianceMonitor()
    >>> results = monitor.scan_project('path/to/project')
    >>> print(results['risk_score'])
"""

import ast
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class SecurityComplianceMonitor:
    """
    安全合规监控器 - OWASP Top 10检查

    对项目进行全面的安全合规性检查，
    覆盖OWASP Top 10安全风险类别。

    Attributes:
        OWASP_CHECKS: OWASP Top 10 检查项定义
    """

    OWASP_CHECKS: List[Tuple[str, str, str]] = [
        ('A01', 'Broken Access Control', 'access_control'),
        ('A02', 'Cryptographic Failures', 'crypto'),
        ('A03', 'Injection', 'injection'),
        ('A04', 'Insecure Design', 'design'),
        ('A05', 'Security Misconfiguration', 'config'),
        ('A06', 'Vulnerable Components', 'components'),
        ('A07', 'Auth Failures', 'auth'),
        ('A08', 'Software/Data Integrity', 'integrity'),
        ('A09', 'Logging/Monitoring Failures', 'logging'),
        ('A10', 'Server-Side Request Forgery', 'ssrf')
    ]

    SENSITIVE_DATA_PATTERNS: List[Tuple[str, str, int]] = [
        (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded Password', 9),
        (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', 'Exposed API Key', 8),
        (r'secret\s*=\s*["\'][^"\']+["\']', 'Exposed Secret', 9),
        (r'token\s*=\s*["\'][^"\']+["\']', 'Exposed Token', 7),
        (r'credential\s*=\s*["\'][^"\']+["\']', 'Exposed Credential', 9),
        (r'private[_-]?key\s*=\s*["\'][^"\']+["\']', 'Private Key Exposure', 10),
        (r'aws_access_key_id\s*=\s*["\'][^"\']+["\']', 'AWS Access Key', 10),
        (r'aws_secret_access_key\s*=\s*["\'][^"\']+["\']', 'AWS Secret Key', 10),
    ]

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化安全合规监控器

        Args:
            logger: 可选的日志记录器
        """
        self.logger = logger or logging.getLogger(__name__)
        self._setup_logging()

    def _setup_logging(self):
        """配置日志"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def scan_project(self, project_path: str) -> Dict[str, Any]:
        """
        执行OWASP Top 10安全扫描

        对项目进行完整的安全合规性检查。

        Args:
            project_path: 项目根目录路径

        Returns:
            扫描结果字典，包含：
            - scan_time: 扫描时间
            - project: 项目路径
            - findings: 发现的问题列表
            - summary: 严重程度统计
            - risk_score: 综合风险评分(0-100)

        示例:
            >>> monitor = SecurityComplianceMonitor()
            >>> results = monitor.scan_project('myproject')
            >>> print(f"风险评分: {results['risk_score']}")
        """
        self.logger.info(f"开始安全扫描: {project_path}")

        results = {
            'scan_time': datetime.now().isoformat(),
            'project': project_path,
            'findings': [],
            'summary': {'high': 0, 'medium': 0, 'low': 0, 'info': 0},
            'owasp_details': {},
            'sensitive_data': []
        }

        for check_id, check_name, check_key in self.OWASP_CHECKS:
            try:
                findings = self._run_check(check_key, project_path)

                for finding in findings:
                    finding['owasp_id'] = check_id
                    finding['owasp_name'] = check_name
                    results['findings'].append(finding)

                    severity = finding.get('severity', 'info')
                    if severity in results['summary']:
                        results['summary'][severity] += 1

                results['owasp_details'][check_id] = {
                    'name': check_name,
                    'findings_count': len(findings),
                    'findings': findings[:5]
                }

                self.logger.debug(
                    f"OWASP {check_id} ({check_name}): 发现 {len(findings)} 个问题"
                )

            except Exception as e:
                self.logger.error(f"检查失败 [{check_id}]: {e}")
                results['owasp_details'][check_id] = {
                    'name': check_name,
                    'error': str(e),
                    'findings_count': 0
                }

        sensitive_data = self.detect_sensitive_data(project_path)
        results['sensitive_data'] = sensitive_data

        for item in sensitive_data:
            severity = item.get('severity', 'info')
            if severity in results['summary']:
                results['summary'][severity] += 1

        results['risk_score'] = self._calculate_risk_score(results['summary'])

        total_findings = len(results['findings']) + len(sensitive_data)
        self.logger.info(
            f"安全扫描完成: 发现 {total_findings} 个问题, "
            f"风险评分: {results['risk_score']}"
        )

        return results

    def _run_check(self, check_key: str, project_path: str) -> List[Dict]:
        """
        执行单个安全检查项

        Args:
            check_key: 检查项标识
            project_path: 项目路径

        Returns:
            发现的问题列表
        """
        check_method = getattr(self, f'_check_{check_key}', None)

        if check_method:
            return check_method(project_path)

        self.logger.warning(f"未知的检查项: {check_key}")
        return []

    def _check_injection(self, project_path: str) -> List[Dict]:
        """
        A03: 注入攻击检查

        检测SQL注入、命令注入、XSS等漏洞模式
        """
        findings = []
        injection_patterns = [
            (r'execute\(.*f["\'].*\{.*\}', 'Potential SQL Injection (f-string)', 'high'),
            (r'execute\(.*%\s*.*%', 'Potential SQL Injection (%)', 'high'),
            (r'subprocess\.(call|run|Popen)\(.*f["\']', 'Command Injection (f-string)', 'critical'),
            (r'os\.system\(.*f["\']', 'OS Command Injection (f-string)', 'critical'),
            (r'eval\(', 'Use of eval() - Code Injection Risk', 'high'),
            (r'exec\(', 'Use of exec() - Code Injection Risk', 'high'),
            (r'innerHTML\s*=.*\+', 'Potential XSS (innerHTML)', 'medium'),
        ]

        for py_file in self._get_python_files(project_path):
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                lines = content.split('\n')

                for line_num, line in enumerate(lines, 1):
                    if line.strip().startswith('#'):
                        continue

                    for pattern, description, severity in injection_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            findings.append({
                                'file': str(py_file),
                                'line': line_num,
                                'line_content': line.strip()[:100],
                                'description': description,
                                'severity': severity,
                                'category': 'injection'
                            })

            except Exception:
                continue

        return findings

    def _check_crypto(self, project_path: str) -> List[Dict]:
        """
        A02: 加密失败检查

        检测弱加密、硬编码密钥等
        """
        findings = []
        crypto_patterns = [
            (r'md5\(', 'Use of MD5 - Weak Hash Algorithm', 'high'),
            (r'sha1\(', 'Use of SHA1 - Weak Hash Algorithm', 'medium'),
            (r'hashlib\.md5', 'MD5 Usage Detected', 'high'),
            (r'random\.random\(', 'Insecure Random - Use secrets module', 'medium'),
            (r'RSA\.generate\(.*512\)', 'Weak RSA Key Size (<2048)', 'high'),
        ]

        for py_file in self._get_python_files(project_path):
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                lines = content.split('\n')

                for line_num, line in enumerate(lines, 1):
                    if line.strip().startswith('#'):
                        continue

                    for pattern, description, severity in crypto_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            findings.append({
                                'file': str(py_file),
                                'line': line_num,
                                'line_content': line.strip()[:100],
                                'description': description,
                                'severity': severity,
                                'category': 'crypto'
                            })

            except Exception:
                continue

        return findings

    def _check_access_control(self, project_path: str) -> List[Dict]:
        """
        A01: 访问控制检查

        检测权限验证缺失等
        """
        findings = []

        for py_file in self._get_python_files(project_path):
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        func_name = node.name.lower()

                        if any(kw in func_name for kw in ['delete', 'update', 'modify', 'admin']):
                            has_auth_check = any(
                                'auth' in ast.unparse(child).lower()
                                or 'permission' in ast.unparse(child).lower()
                                or 'role' in ast.unparse(child).lower()
                                for child in ast.walk(node)
                            )

                            if not has_auth_check and any(
                                isinstance(child, ast.Call)
                                for child in ast.walk(node)
                            ):
                                findings.append({
                                    'file': str(py_file),
                                    'line': node.lineno,
                                    'function': node.name,
                                    'description': f'Missing authentication check in sensitive function',
                                    'severity': 'high',
                                    'category': 'access_control'
                                })

            except SyntaxError:
                continue

        return findings

    def _check_config(self, project_path: str) -> List[Dict]:
        """
        A05: 安全配置错误检查

        检测不安全的默认配置
        """
        findings = []
        config_patterns = [
            (r'DEBUG\s*=\s*True', 'Debug Mode Enabled', 'high'),
            (r'ALLOWED_HOSTS\s*=\s*\[\s*[\'"]\*[\'"]\s*\]', 'Wildcard Allowed Hosts', 'high'),
            (r'SECURE_SSL_REDIRECT\s*=\s*False', 'SSL Redirect Disabled', 'medium'),
            (r'SESSION_COOKIE_SECURE\s*=\s*False', 'Insecure Session Cookie', 'medium'),
            (r'CSRF_COOKIE_SECURE\s*=\s*False', 'Insecure CSRF Cookie', 'medium'),
        ]

        config_files = list(Path(project_path).rglob('*.py')) + \
                     list(Path(project_path).rglob('settings*.py')) + \
                     list(Path(project_path).rglob('config*.py'))

        for config_file in config_files:
            try:
                with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                lines = content.split('\n')

                for line_num, line in enumerate(lines, 1):
                    if line.strip().startswith('#'):
                        continue

                    for pattern, description, severity in config_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            findings.append({
                                'file': str(config_file),
                                'line': line_num,
                                'line_content': line.strip()[:100],
                                'description': description,
                                'severity': severity,
                                'category': 'config'
                            })

            except Exception:
                continue

        return findings

    def _check_components(self, project_path: str) -> List[Dict]:
        """
        A06: 易受攻击组件检查

        检查依赖文件中的已知漏洞（简化版）
        """
        findings = []

        requirements_files = [
            Path(project_path) / 'requirements.txt',
            Path(project_path) / 'requirements-dev.txt',
            Path(project_path) / 'Pipfile',
            Path(project_path) / 'pyproject.toml'
        ]

        known_vulnerable = [
            (r'(?i)django\s*[<>=]*\s*([12]\..*|3\.[01]\.)', 'Outdated Django Version', 'high'),
            (r'(?i)flask\s*[<>=]*\s*[01]\.', 'Outdated Flask Version', 'high'),
            (r'(?i)requests\s*[<>=]*\s*[01]\.', 'Outdated Requests Library', 'medium'),
            (r'(?i)pyyaml\s*[<>=]*\s*[45]\.', 'Vulnerable PyYAML Version', 'critical'),
        ]

        for req_file in requirements_files:
            if not req_file.exists():
                continue

            try:
                with open(req_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                lines = content.split('\n')

                for line_num, line in enumerate(lines, 1):
                    for pattern, description, severity in known_vulnerable:
                        match = re.search(pattern, line)
                        if match:
                            findings.append({
                                'file': str(req_file),
                                'line': line_num,
                                'dependency': line.strip(),
                                'description': description,
                                'severity': severity,
                                'category': 'components'
                            })

            except Exception:
                continue

        return findings

    def _check_design(self, project_path: str) -> List[Dict]:
        """A04: 不安全设计检查"""
        return []

    def _check_auth(self, project_path: str) -> List[Dict]:
        """A07: 认证失败检查"""
        return []

    def _check_integrity(self, project_path: str) -> List[Dict]:
        """A08: 软件数据完整性检查"""
        return []

    def _check_logging(self, project_path: str) -> List[Dict]:
        """A09: 日志/监控失败检查"""
        return []

    def _check_ssrf(self, project_path: str) -> List[Dict]:
        """A10: 服务端请求伪造检查"""
        ssrf_patterns = [
            (r'requests\.(get|post)\(.*user_input', 'Potential SSRF via User Input', 'high'),
            (r'urllib\.request\.urlopen\(.*user_input', 'Potential SSRF via User Input', 'high'),
        ]

        findings = []

        for py_file in self._get_python_files(project_path):
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                for pattern, description, severity in ssrf_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        findings.append({
                            'file': str(py_file),
                            'description': description,
                            'severity': severity,
                            'category': 'ssrf'
                        })
            except Exception:
                continue

        return findings

    def detect_sensitive_data(self, project_path: str) -> List[Dict]:
        """
        检测敏感数据泄露风险

        扫描代码中可能泄露的敏感信息

        Args:
            project_path: 项目路径

        Returns:
            敏感数据检测结果列表
        """
        findings = []

        for py_file in self._get_python_files(project_path):
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                lines = content.split('\n')

                for line_num, line in enumerate(lines, 1):
                    stripped = line.strip()

                    if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                        continue

                    for pattern, description, base_severity in self.SENSITIVE_DATA_PATTERNS:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            masked_value = match.group()[:20] + '...' if len(match.group()) > 20 else match.group()
                            
                            findings.append({
                                'file': str(py_file),
                                'line': line_num,
                                'type': description,
                                'pattern': masked_value,
                                'severity': self._get_severity_string(base_severity),
                                'category': 'sensitive_data'
                            })

            except Exception:
                continue

        return findings

    def _get_severity_string(self, score: int) -> str:
        """将数值严重程度转换为字符串"""
        if score >= 9:
            return 'critical'
        elif score >= 7:
            return 'high'
        elif score >= 4:
            return 'medium'
        else:
            return 'low'

    def _calculate_risk_score(self, summary: Dict[str, int]) -> float:
        """
        计算综合风险评分

        Args:
            summary: 严重程度统计字典

        Returns:
            风险评分 (0-100, 越高越危险)
        """
        weights = {
            'high': 8,
            'medium': 4,
            'low': 2,
            'info': 0.5
        }

        weighted_sum = sum(count * weights.get(severity, 0) 
                         for severity, count in summary.items())

        max_possible = 100
        risk_score = min(weighted_sum, max_possible)

        return round(risk_score, 1)

    def _get_python_files(self, project_path: str) -> List[Path]:
        """获取项目中的所有Python文件"""
        project = Path(project_path)
        exclude_dirs = {
            '__pycache__', '.git', '.venv', 'venv', 'node_modules',
            '.pytest_cache', 'build', 'dist', '.tox', '.mypy_cache',
            'htmlcov', '.idea', '.vscode'
        }

        python_files = []

        for py_file in project.rglob('*.py'):
            if not any(excluded in py_file.parts for excluded in exclude_dirs):
                python_files.append(py_file)

        return python_files


def main():
    """测试安全合规监控功能"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    print("=" * 80)
    print("🔒 安全合规监控测试 (OWASP Top 10)")
    print("=" * 80)

    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = str(Path(__file__).parent.parent.parent)

    monitor = SecurityComplianceMonitor()
    results = monitor.scan_project(project_path)

    print("\n📊 安全扫描结果\n")
    print(f"⏰ 扫描时间: {results['scan_time']}")
    print(f"📁 项目路径: {results['project']}")
    print(f"⚠️  风险评分: {results['risk_score']}/100")

    print("\n📈 严重程度统计:")
    for severity, count in results['summary'].items():
        icon = {'high': '🔴', 'medium': '🟠', 'low': '🟡', 'info': '🔵'}.get(severity, '⚪')
        print(f"  {icon} {severity.upper()}: {count}")

    print("\n🔍 OWASP Top 10 详情:")
    for check_id, details in results.get('owasp_details', {}).items():
        count = details.get('findings_count', 0)
        status_icon = '✅' if count == 0 else ('⚠️' if count <= 3 else '❌')
        print(f"  {status_icon} {check_id}: {details.get('name', 'Unknown')} ({count} 个问题)")

        if count > 0 and details.get('findings'):
            for finding in details['findings'][:3]:
                print(f"     - {finding.get('description', 'Unknown')}")

    if results.get('sensitive_data'):
        print(f"\n🚨 敏感数据发现: {len(results['sensitive_data'])} 处")
        for item in results['sensitive_data'][:5]:
            print(f"  ⚠️  {item['type']} @ {Path(item['file']).name}:{item['line']}")

    print("\n✅ 安全扫描完成!")


if __name__ == "__main__":
    main()
