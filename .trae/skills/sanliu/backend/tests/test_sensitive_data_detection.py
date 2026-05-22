"""
敏感数据暴露检测测试

检测API响应、日志、配置中的敏感数据泄露风险
"""

import pytest
import re
import os
import json
from typing import Dict, List, Any, Tuple
from pathlib import Path
from tests.conftest import create_test_project, create_test_task, create_test_agent


class SensitiveDataPatterns:
    CREDIT_CARD_PATTERNS = [
        (r'\b4[0-9]{12}(?:[0-9]{3})?\b', 'Visa卡号'),
        (r'\b5[1-5][0-9]{14}\b', 'MasterCard卡号'),
        (r'\b3[47][0-9]{13}\b', 'American Express卡号'),
        (r'\b6(?:011|5[0-9]{2})[0-9]{12}\b', 'Discover卡号'),
        (r'\b(?:2131|1800|35\d{3})\d{11}\b', 'JCB卡号'),
    ]

    SSN_PATTERNS = [
        (r'\b\d{3}-\d{2}-\d{4}\b', '美国社保号'),
        (r'\b\d{6}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b', '中国身份证号'),
    ]

    API_KEY_PATTERNS = [
        (r'(?i)(?:api[_-]?key|apikey)["\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?', 'API Key'),
        (r'(?i)(?:secret[_-]?key|secretkey)["\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?', 'Secret Key'),
        (r'(?i)(?:access[_-]?token|accesstoken)["\s:=]+["\']?([a-zA-Z0-9_\-\.]{20,})["\']?', 'Access Token'),
        (r'(?i)(?:private[_-]?key|privatekey)["\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?', 'Private Key'),
        (r'sk-[a-zA-Z0-9]{48}', 'OpenAI API Key'),
        (r'ghp_[a-zA-Z0-9]{36}', 'GitHub Personal Access Token'),
        (r'gho_[a-zA-Z0-9]{36}', 'GitHub OAuth Access Token'),
        (r'ghu_[a-zA-Z0-9]{36}', 'GitHub User-to-Server Token'),
        (r'ghs_[a-zA-Z0-9]{36}', 'GitHub Server-to-Server Token'),
        (r'ghr_[a-zA-Z0-9]{36}', 'GitHub Refresh Token'),
        (r'AKIA[0-9A-Z]{16}', 'AWS Access Key ID'),
        (r"(?i)aws(.{0,20})?[\'\"][0-9a-zA-Z\/+]{40}[\'\"]", 'AWS Secret Access Key'),
        (r'ya29\.[0-9A-Za-z\-_]+', 'Google OAuth Access Token'),
        (r'AIza[0-9A-Za-z\-_]{35}', 'Google API Key'),
        (r'xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24}', 'Slack Token'),
        (r'eyJ[a-zA-Z0-9\-_]+\.eyJ[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+', 'JWT Token'),
    ]

    PASSWORD_PATTERNS = [
        (r'(?i)(?:password|passwd|pwd)["\s:=]+["\']?([^"\s\'<>]{4,})["\']?', 'Password'),
        (r'(?i)(?:db[_-]?password|database[_-]?password)["\s:=]+["\']?([^"\s\'<>]{4,})["\']?', 'Database Password'),
        (r'(?i)(?:smtp[_-]?password|email[_-]?password)["\s:=]+["\']?([^"\s\'<>]{4,})["\']?', 'SMTP Password'),
    ]

    EMAIL_PATTERNS = [
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'Email地址'),
    ]

    PHONE_PATTERNS = [
        (r'\b(?:\+?86)?1[3-9]\d{9}\b', '中国手机号'),
        (r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', '美国电话号码'),
    ]

    IP_ADDRESS_PATTERNS = [
        (r'\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', '私有IP (10.x.x.x)'),
        (r'\b(?:172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b', '私有IP (172.16-31.x.x)'),
        (r'\b(?:192\.168\.\d{1,3}\.\d{1,3})\b', '私有IP (192.168.x.x)'),
        (r'\b(?:127\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', '本地回环IP'),
    ]

    DATABASE_CONNECTION_PATTERNS = [
        (r'(?:mysql|postgres|postgresql|mongodb|redis)://[^\s\'"<>]+', '数据库连接字符串'),
        (r'jdbc:[a-z]+://[^\s\'"<>]+', 'JDBC连接字符串'),
    ]

    SENSITIVE_FILE_PATTERNS = [
        (r'\.env$', '环境变量文件'),
        (r'\.pem$', 'PEM证书文件'),
        (r'\.key$', '密钥文件'),
        (r'id_rsa$', 'SSH私钥'),
        (r'\.p12$', 'PKCS12证书'),
        (r'\.pfx$', 'PFX证书'),
        (r'credentials\.json$', '凭证文件'),
        (r'secrets\.json$', '密钥文件'),
    ]


class SensitiveDataDetector:
    def __init__(self):
        self.patterns = SensitiveDataPatterns()
        self.findings: List[Dict[str, Any]] = []

    def scan_text(self, text: str, context: str = "") -> List[Dict[str, Any]]:
        findings = []

        all_patterns = [
            ('credit_card', self.patterns.CREDIT_CARD_PATTERNS),
            ('ssn', self.patterns.SSN_PATTERNS),
            ('api_key', self.patterns.API_KEY_PATTERNS),
            ('password', self.patterns.PASSWORD_PATTERNS),
            ('email', self.patterns.EMAIL_PATTERNS),
            ('phone', self.patterns.PHONE_PATTERNS),
            ('ip_address', self.patterns.IP_ADDRESS_PATTERNS),
            ('database', self.patterns.DATABASE_CONNECTION_PATTERNS),
        ]

        for category, patterns in all_patterns:
            for pattern, description in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    for match in matches if isinstance(matches[0], tuple) else [(matches[0],)]:
                        finding = {
                            'category': category,
                            'type': description,
                            'pattern': pattern,
                            'match': str(match[0]) if isinstance(match, tuple) else str(match),
                            'context': context,
                            'severity': self._get_severity(category)
                        }
                        findings.append(finding)

        return findings

    def _get_severity(self, category: str) -> str:
        high_severity = ['credit_card', 'ssn', 'password', 'api_key', 'database']
        medium_severity = ['email', 'phone', 'ip_address']

        if category in high_severity:
            return 'HIGH'
        elif category in medium_severity:
            return 'MEDIUM'
        return 'LOW'

    def scan_file(self, file_path: str) -> List[Dict[str, Any]]:
        findings = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                findings = self.scan_text(content, f"文件: {file_path}")
        except Exception:
            pass
        return findings


@pytest.mark.security
@pytest.mark.sensitive_data
class TestAPIResponseSensitiveData:
    """测试API响应中的敏感数据泄露"""

    def test_project_api_no_sensitive_data(self, client, db_session):
        """测试项目API响应不包含敏感数据"""
        detector = SensitiveDataDetector()
        project = create_test_project(db_session, name="敏感数据测试项目")

        response = client.get(f"/api/projects/{project.id}")
        assert response.status_code == 200

        findings = detector.scan_text(response.text, "Project API响应")

        critical_findings = [f for f in findings if f['severity'] == 'HIGH']
        assert len(critical_findings) == 0, f"发现敏感数据泄露: {critical_findings}"

    def test_task_api_no_sensitive_data(self, client, db_session):
        """测试任务API响应不包含敏感数据"""
        detector = SensitiveDataDetector()
        project = create_test_project(db_session, name="任务敏感数据测试")
        task = create_test_task(db_session, title="测试任务", project_id=project.id)

        response = client.get(f"/api/tasks/{task.id}")
        assert response.status_code == 200

        findings = detector.scan_text(response.text, "Task API响应")

        critical_findings = [f for f in findings if f['severity'] == 'HIGH']
        assert len(critical_findings) == 0, f"发现敏感数据泄露: {critical_findings}"

    def test_agent_api_no_sensitive_data(self, client, db_session):
        """测试代理API响应不包含敏感数据"""
        detector = SensitiveDataDetector()
        agent = create_test_agent(db_session, name="测试代理")

        response = client.get(f"/api/agents/{agent.id}")
        assert response.status_code == 200

        findings = detector.scan_text(response.text, "Agent API响应")

        critical_findings = [f for f in findings if f['severity'] == 'HIGH']
        assert len(critical_findings) == 0, f"发现敏感数据泄露: {critical_findings}"

    def test_list_endpoints_no_sensitive_data(self, client, db_session):
        """测试列表端点不泄露敏感数据"""
        detector = SensitiveDataDetector()

        endpoints = [
            "/api/projects/",
            "/api/tasks/",
            "/api/agents/",
            "/api/departments/",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                findings = detector.scan_text(response.text, f"{endpoint} 响应")
                critical_findings = [f for f in findings if f['severity'] == 'HIGH']
                assert len(critical_findings) == 0, f"{endpoint} 发现敏感数据: {critical_findings}"


@pytest.mark.security
@pytest.mark.sensitive_data
class TestConfigFileSensitiveData:
    """测试配置文件中的敏感数据"""

    def test_env_file_not_exposed(self, client, db_session):
        """测试.env文件不被暴露"""
        env_paths = [
            "/.env",
            "/.env.local",
            "/.env.production",
            "/api/.env",
            "/backend/.env",
        ]

        for path in env_paths:
            response = client.get(path)
            assert response.status_code in [404, 403], f".env文件可能被访问: {path}"

    def test_config_files_not_exposed(self, client, db_session):
        """测试配置文件不被暴露"""
        config_paths = [
            "/config.json",
            "/config.yml",
            "/config.yaml",
            "/settings.py",
            "/api/config.py",
            "/backend/config.py",
        ]

        for path in config_paths:
            response = client.get(path)
            assert response.status_code in [404, 403], f"配置文件可能被访问: {path}"

    def test_credential_files_not_exposed(self, client, db_session):
        """测试凭证文件不被暴露"""
        credential_paths = [
            "/credentials.json",
            "/secrets.json",
            "/keys.json",
            "/.aws/credentials",
            "/.ssh/id_rsa",
        ]

        for path in credential_paths:
            response = client.get(path)
            assert response.status_code in [404, 403], f"凭证文件可能被访问: {path}"


@pytest.mark.security
@pytest.mark.sensitive_data
class TestErrorMessagesSensitiveData:
    """测试错误消息中的敏感数据泄露"""

    def test_error_no_stack_trace(self, client, db_session):
        """测试错误响应不包含堆栈跟踪"""
        response = client.get("/api/projects/invalid_id_format")

        if response.status_code >= 400:
            response_text = response.text.lower()
            assert "traceback" not in response_text
            assert "file \"" not in response_text
            assert "line " not in response_text or response.status_code != 500

    def test_error_no_database_info(self, client, db_session):
        """测试错误响应不包含数据库信息"""
        response = client.get("/api/projects/999999999")

        if response.status_code >= 400:
            response_text = response.text.lower()
            assert "sqlalchemy" not in response_text
            assert "psycopg2" not in response_text
            assert "sqlite" not in response_text
            assert "select " not in response_text
            assert "insert " not in response_text
            assert "update " not in response_text

    def test_error_no_internal_paths(self, client, db_session):
        """测试错误响应不包含内部路径"""
        response = client.post("/api/projects/", json={"invalid": "data"})

        if response.status_code >= 400:
            response_text = response.text
            assert "/home/" not in response_text
            assert "/var/" not in response_text
            assert "C:\\" not in response_text
            assert "/etc/" not in response_text


@pytest.mark.security
@pytest.mark.sensitive_data
class TestLoggingSensitiveData:
    """测试日志中的敏感数据"""

    def test_request_logs_no_passwords(self, client, db_session):
        """测试请求日志不记录密码"""
        login_data = {
            "username": "testuser",
            "password": "testpassword123"
        }

        response = client.post("/api/auth/login", json=login_data)

        log_files = [
            "app.log",
            "error.log",
            "access.log",
            "debug.log",
        ]

        detector = SensitiveDataDetector()

        for log_file in log_files:
            if os.path.exists(log_file):
                findings = detector.scan_file(log_file)
                password_findings = [f for f in findings if f['category'] == 'password']
                assert len(password_findings) == 0, f"日志中发现密码: {log_file}"


@pytest.mark.security
@pytest.mark.sensitive_data
class TestDataMasking:
    """测试数据脱敏"""

    def test_email_masking_in_list(self, client, db_session):
        """测试邮箱在列表中被脱敏"""
        response = client.get("/api/agents/")

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                for item in data:
                    if 'email' in item:
                        email = item['email']
                        if '@' in email:
                            local_part = email.split('@')[0]
                            assert '*' in email or len(local_part) <= 2, \
                                f"邮箱未脱敏: {email}"

    def test_phone_masking(self, client, db_session):
        """测试电话号码被脱敏"""
        response = client.get("/api/agents/")

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                for item in data:
                    if 'phone' in item:
                        phone = item['phone']
                        assert '*' in phone or len(phone.replace('*', '')) <= 4, \
                            f"电话号码未脱敏: {phone}"


@pytest.mark.security
@pytest.mark.sensitive_data
class TestResponseHeaders:
    """测试响应头中的敏感数据"""

    def test_no_server_version(self, client, db_session):
        """测试不暴露服务器版本"""
        response = client.get("/api/projects/")

        server_header = response.headers.get("Server", "")
        assert "/" not in server_header or server_header == "", \
            f"服务器版本暴露: {server_header}"

    def test_no_powered_by(self, client, db_session):
        """测试不暴露技术栈信息"""
        response = client.get("/api/projects/")

        powered_by = response.headers.get("X-Powered-By", "")
        assert powered_by == "", f"技术栈信息暴露: {powered_by}"

    def test_no_php_version(self, client, db_session):
        """测试不暴露PHP版本"""
        response = client.get("/api/projects/")

        php_version = response.headers.get("X-PHP-Version", "")
        assert php_version == "", f"PHP版本暴露: {php_version}"

    def test_no_aspnet_version(self, client, db_session):
        """测试不暴露ASP.NET版本"""
        response = client.get("/api/projects/")

        aspnet_version = response.headers.get("X-AspNet-Version", "")
        assert aspnet_version == "", f"ASP.NET版本暴露: {aspnet_version}"


@pytest.mark.security
@pytest.mark.sensitive_data
class TestDebugInfoExposure:
    """测试调试信息泄露"""

    def test_no_debug_info_in_production(self, client, db_session):
        """测试生产环境不暴露调试信息"""
        response = client.get("/api/projects/")

        debug_indicators = [
            "debug",
            "DEBUG",
            "stack_trace",
            "stacktrace",
            "backtrace",
            "exception_details",
        ]

        response_text = response.text
        for indicator in debug_indicators:
            if indicator in response_text:
                assert False, f"响应中包含调试信息: {indicator}"

    def test_no_sql_query_in_response(self, client, db_session):
        """测试响应不包含SQL查询"""
        response = client.get("/api/projects/")

        sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "FROM", "WHERE"]
        response_text = response.text.upper()

        for keyword in sql_keywords:
            if f" {keyword} " in response_text:
                assert False, f"响应中包含SQL关键字: {keyword}"

    def test_no_internal_ip_in_response(self, client, db_session):
        """测试响应不包含内部IP"""
        detector = SensitiveDataDetector()
        response = client.get("/api/projects/")

        findings = detector.scan_text(response.text, "API响应")
        ip_findings = [f for f in findings if f['category'] == 'ip_address']

        assert len(ip_findings) == 0, f"响应中包含内部IP: {ip_findings}"


@pytest.mark.security
@pytest.mark.sensitive_data
class TestJSONResponseSecurity:
    """测试JSON响应安全性"""

    def test_no_null_byte_injection(self, client, db_session):
        """测试空字节注入防护"""
        project_data = {
            "name": "test\x00project",
            "description": "test",
            "tech_stack": [],
            "status": "REQUIREMENT"
        }

        response = client.post("/api/projects/", json=project_data)

        if response.status_code in [200, 201]:
            data = response.json()
            assert "\x00" not in str(data), "响应中包含空字节"

    def test_no_unicode_bypass(self, client, db_session):
        """测试Unicode绕过防护"""
        unicode_payloads = [
            "test\u0000project",
            "test\uff00project",
            "test\ufeffproject",
        ]

        for payload in unicode_payloads:
            project_data = {
                "name": payload,
                "description": "test",
                "tech_stack": [],
                "status": "REQUIREMENT"
            }

            response = client.post("/api/projects/", json=project_data)

            if response.status_code in [200, 201]:
                data = response.json()
                assert "\u0000" not in str(data)
                assert "\uff00" not in str(data)
                assert "\ufeff" not in str(data)

    def test_json_content_type_enforced(self, client, db_session):
        """测试JSON内容类型强制执行"""
        response = client.get("/api/projects/")

        content_type = response.headers.get("Content-Type", "")
        assert "application/json" in content_type, \
            f"响应Content-Type不正确: {content_type}"
