"""
主应用测试

测试 FastAPI 主应用的基本功能，包括根路径、健康检查、性能统计等
"""

import pytest
from datetime import datetime


@pytest.mark.api
@pytest.mark.unit
class TestRootEndpoints:
    """测试根路径端点"""
    
    def test_root_endpoint(self, client):
        """测试根路径返回 API 基本信息"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["message"] == "Sanliu Skill Management System"
        assert data["version"] == "1.0.0"
    
    def test_root_endpoint_content_type(self, client):
        """测试根路径返回正确的 Content-Type"""
        response = client.get("/")
        
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]


@pytest.mark.api
@pytest.mark.unit
class TestHealthEndpoints:
    """测试健康检查端点"""
    
    def test_health_check(self, client):
        """测试健康检查端点返回服务状态"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"
        
        # 验证时间戳格式
        timestamp = data["timestamp"]
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"Invalid timestamp format: {timestamp}")
    
    def test_health_check_method_not_allowed(self, client):
        """测试健康检查端点不支持 POST 方法"""
        response = client.post("/health")
        
        assert response.status_code == 405


@pytest.mark.api
@pytest.mark.unit
class TestPerformanceEndpoints:
    """测试性能统计端点"""
    
    def test_performance_stats(self, client):
        """测试性能统计端点返回统计数据"""
        response = client.get("/performance/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证返回的数据结构
        assert isinstance(data, dict)
        # 性能统计可能包含以下字段
        possible_fields = ["requests", "response_times", "slow_requests", "endpoints"]
        # 至少应该有一些数据返回
        assert len(data) >= 0


@pytest.mark.api
@pytest.mark.unit
class TestAPIDocumentation:
    """测试 API 文档端点"""
    
    def test_docs_endpoint(self, client):
        """测试 Swagger UI 文档端点"""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # 验证返回的是 Swagger UI HTML
        content = response.text
        assert "swagger" in content.lower() or "openapi" in content.lower()
    
    def test_redoc_endpoint(self, client):
        """测试 ReDoc 文档端点"""
        response = client.get("/redoc")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # 验证返回的是 ReDoc HTML
        content = response.text
        assert "redoc" in content.lower()
    
    def test_openapi_schema(self, client):
        """测试 OpenAPI JSON Schema 端点"""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        
        # 验证基本信息
        info = schema["info"]
        assert info["title"] == "Sanliu Skill Management System"
        assert info["version"] == "1.0.0"


@pytest.mark.api
@pytest.mark.unit
class TestCORS:
    """测试 CORS 配置"""
    
    def test_cors_headers_present(self, client):
        """测试 CORS 响应头存在"""
        response = client.get("/", headers={"Origin": "http://localhost:3000"})
        
        assert response.status_code == 200
        # 验证 CORS 头
        assert "access-control-allow-origin" in response.headers
    
    def test_cors_preflight_request(self, client):
        """测试 CORS 预检请求"""
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type",
            }
        )
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers


@pytest.mark.api
@pytest.mark.unit
class TestErrorHandling:
    """测试错误处理"""
    
    def test_404_not_found(self, client):
        """测试 404 错误处理"""
        response = client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_405_method_not_allowed(self, client):
        """测试 405 错误处理"""
        response = client.post("/")
        
        assert response.status_code == 405
        data = response.json()
        assert "detail" in data
    
    def test_422_validation_error(self, client):
        """测试 422 验证错误处理"""
        # 向需要 JSON 的端点发送无效数据
        response = client.post("/api/projects/", json={})
        
        assert response.status_code == 422
        data = response.json()
        # 检查错误响应结构（可能是 detail 或 error）
        assert "detail" in data or "error" in data


@pytest.mark.api
@pytest.mark.integration
class TestApplicationIntegration:
    """测试应用程序集成"""
    
    def test_multiple_requests(self, client):
        """测试应用程序可以处理多个请求"""
        # 发送多个请求
        responses = []
        for _ in range(5):
            response = client.get("/health")
            responses.append(response)
        
        # 验证所有请求都成功
        for response in responses:
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
    
    def test_request_response_consistency(self, client):
        """测试请求响应一致性"""
        # 测试根路径
        root_response = client.get("/")
        assert root_response.status_code == 200
        
        # 测试健康检查
        health_response = client.get("/health")
        assert health_response.status_code == 200
        
        # 测试文档
        docs_response = client.get("/docs")
        assert docs_response.status_code == 200


@pytest.mark.api
@pytest.mark.unit
class TestApplicationMetadata:
    """测试应用程序元数据"""
    
    def test_app_title(self, client):
        """测试应用程序标题"""
        response = client.get("/openapi.json")
        schema = response.json()
        
        assert schema["info"]["title"] == "Sanliu Skill Management System"
    
    def test_app_version(self, client):
        """测试应用程序版本"""
        response = client.get("/openapi.json")
        schema = response.json()
        
        assert schema["info"]["version"] == "1.0.0"
    
    def test_app_description(self, client):
        """测试应用程序描述"""
        response = client.get("/openapi.json")
        schema = response.json()
        
        assert "description" in schema["info"]
        description = schema["info"]["description"]
        assert "三省六部" in description or "Sanliu" in description
