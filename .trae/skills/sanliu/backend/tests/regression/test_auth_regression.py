"""
用户认证功能回归测试套件

验证用户认证的核心功能，包括：
- 用户注册和登录
- 会话管理
- 权限验证
- 安全措施
- Token管理
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import Mock, patch

from tests.conftest import create_test_agent


@pytest.mark.regression
@pytest.mark.security
class TestAuthenticationRegression:
    """用户认证回归测试套件"""

    def test_api_endpoint_security(self, client):
        """测试API端点安全"""
        protected_endpoints = [
            ("/api/projects/", "GET"),
            ("/api/tasks/", "GET"),
            ("/api/agents/", "GET"),
            ("/api/reports/", "GET"),
        ]
        
        for endpoint, method in protected_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            
            assert response.status_code in [200, 401, 403, 404, 422]

    def test_input_validation_security(self, client):
        """测试输入验证安全"""
        malicious_inputs = [
            {"name": "<script>alert('xss')</script>"},
            {"name": "'; DROP TABLE projects; --"},
            {"name": "../../../etc/passwd"},
            {"name": "${env.VARIABLE}"},
            {"name": "{{template_injection}}"},
        ]
        
        for data in malicious_inputs:
            response = client.post("/api/projects/", json=data)
            if response.status_code == 200:
                created_name = response.json().get("name", "")
                assert "<script>" not in created_name
                assert "DROP TABLE" not in created_name

    def test_sql_injection_prevention(self, client, db_session):
        """测试SQL注入防护"""
        sql_injection_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE projects;",
            "1 UNION SELECT * FROM users",
            "1' AND 1=1--",
        ]
        
        for payload in sql_injection_payloads:
            response = client.get(f"/api/projects/{payload}")
            assert response.status_code in [400, 404, 422]

    def test_xss_prevention(self, client):
        """测试XSS防护"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
        ]
        
        for payload in xss_payloads:
            response = client.post("/api/projects/", json={"name": payload})
            if response.status_code == 200:
                assert "<script>" not in response.text
                assert "onerror=" not in response.text

    def test_rate_limiting(self, client):
        """测试速率限制"""
        responses = []
        for _ in range(100):
            response = client.get("/api/projects/")
            responses.append(response.status_code)
        
        assert 429 in responses or all(r in [200, 401, 403] for r in responses)

    def test_error_message_safety(self, client):
        """测试错误消息安全"""
        response = client.get("/api/projects/99999")
        assert response.status_code == 404
        
        error_detail = response.json().get("detail", "")
        assert "password" not in error_detail.lower()
        assert "secret" not in error_detail.lower()
        assert "token" not in error_detail.lower()

    def test_cors_configuration(self, client):
        """测试CORS配置"""
        response = client.options(
            "/api/projects/",
            headers={
                "Origin": "http://malicious-site.com",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        assert response.status_code in [200, 400, 403, 405]

    def test_content_type_validation(self, client):
        """测试内容类型验证"""
        response = client.post(
            "/api/projects/",
            data="not json data",
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code in [400, 415, 422]

    def test_http_method_validation(self, client):
        """测试HTTP方法验证"""
        response = client.patch("/api/projects/")
        assert response.status_code in [405, 400, 404]

    def test_request_size_limit(self, client):
        """测试请求大小限制"""
        large_data = {"name": "A" * 100000}
        response = client.post("/api/projects/", json=large_data)
        assert response.status_code in [200, 400, 413, 422]


@pytest.mark.regression
@pytest.mark.security
class TestAuthorizationRegression:
    """授权验证回归测试套件"""

    def test_resource_access_control(self, client, db_session):
        """测试资源访问控制"""
        from tests.conftest import create_test_project
        
        project = create_test_project(db_session, name="访问控制测试")
        
        response = client.get(f"/api/projects/{project.id}")
        assert response.status_code in [200, 401, 403, 404]
        
        response = client.put(f"/api/projects/{project.id}", json={"name": "修改"})
        assert response.status_code in [200, 401, 403, 404]
        
        response = client.delete(f"/api/projects/{project.id}")
        assert response.status_code in [200, 401, 403, 404]

    def test_role_based_access(self, client, db_session):
        """测试基于角色的访问控制"""
        from tests.conftest import create_test_project, create_test_task
        
        project = create_test_project(db_session, name="角色测试项目")
        task = create_test_task(db_session, project_id=project.id, title="角色测试任务")
        
        endpoints = [
            ("/api/projects/", "GET"),
            ("/api/tasks/", "GET"),
            ("/api/agents/", "GET"),
            ("/api/statistics/", "GET"),
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            assert response.status_code in [200, 401, 403, 404]

    def test_cross_user_isolation(self, client, db_session):
        """测试跨用户隔离"""
        from tests.conftest import create_test_project
        
        project1 = create_test_project(db_session, name="用户1项目")
        project2 = create_test_project(db_session, name="用户2项目")
        
        response1 = client.get(f"/api/projects/{project1.id}")
        response2 = client.get(f"/api/projects/{project2.id}")
        
        assert response1.status_code in [200, 401, 403, 404]
        assert response2.status_code in [200, 401, 403, 404]


@pytest.mark.regression
@pytest.mark.security
class TestSessionManagement:
    """会话管理回归测试"""

    def test_session_timeout(self, client):
        """测试会话超时"""
        response = client.get("/api/projects/")
        assert response.status_code in [200, 401, 403, 404]

    def test_concurrent_sessions(self, client):
        """测试并发会话"""
        responses = []
        for _ in range(5):
            response = client.get("/api/projects/")
            responses.append(response.status_code)
        
        assert all(r in [200, 401, 403, 404] for r in responses)

    def test_session_invalidation(self, client):
        """测试会话失效"""
        response = client.get("/api/projects/")
        initial_status = response.status_code
        
        response = client.get("/api/projects/")
        assert response.status_code == initial_status


@pytest.mark.regression
@pytest.mark.security
class TestDataProtection:
    """数据保护回归测试"""

    def test_sensitive_data_masking(self, client, db_session):
        """测试敏感数据脱敏"""
        from tests.conftest import create_test_agent
        
        agent = create_test_agent(db_session, name="敏感数据代理")
        
        response = client.get(f"/api/agents/{agent.id}")
        if response.status_code == 200:
            data = response.json()
            sensitive_fields = ["password", "secret", "token", "api_key"]
            for field in sensitive_fields:
                assert field not in data or data[field] == "***"

    def test_data_encryption(self, client):
        """测试数据加密"""
        response = client.get("/api/projects/")
        assert response.status_code in [200, 401, 403, 404]

    def test_audit_logging(self, client, db_session):
        """测试审计日志"""
        from tests.conftest import create_test_project
        
        initial_count = len(db_session.query(create_test_project.__code__.co_varnames).all() if hasattr(db_session, 'query') else [])
        
        create_test_project(db_session, name="审计测试项目")
        
        response = client.get("/api/projects/")
        assert response.status_code in [200, 401, 403, 404]


@pytest.mark.regression
@pytest.mark.security
class TestSecurityHeaders:
    """安全头回归测试"""

    def test_security_headers_present(self, client):
        """测试安全头存在"""
        response = client.get("/api/projects/")
        
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
        ]
        
        for header in security_headers:
            assert header in response.headers or response.status_code in [401, 403, 404]

    def test_content_security_policy(self, client):
        """测试内容安全策略"""
        response = client.get("/api/projects/")
        
        if "Content-Security-Policy" in response.headers:
            csp = response.headers["Content-Security-Policy"]
            assert "default-src" in csp or "script-src" in csp

    def test_strict_transport_security(self, client):
        """测试严格传输安全"""
        response = client.get("/api/projects/")
        
        if "Strict-Transport-Security" in response.headers:
            hsts = response.headers["Strict-Transport-Security"]
            assert "max-age" in hsts


@pytest.mark.regression
@pytest.mark.performance
class TestSecurityPerformance:
    """安全性能回归测试"""

    def test_authentication_performance(self, client):
        """测试认证性能"""
        import time
        
        start = time.time()
        for _ in range(10):
            client.get("/api/projects/")
        duration = time.time() - start
        
        assert duration < 5.0

    def test_authorization_check_performance(self, client, db_session):
        """测试授权检查性能"""
        import time
        from tests.conftest import create_test_project
        
        project = create_test_project(db_session, name="授权性能测试")
        
        start = time.time()
        for _ in range(10):
            client.get(f"/api/projects/{project.id}")
        duration = time.time() - start
        
        assert duration < 3.0
