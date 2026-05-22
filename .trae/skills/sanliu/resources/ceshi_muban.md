# 测试模板文档

本文档提供各类测试的标准模板和最佳实践指南。

## 目录

1. [单元测试模板](#单元测试模板)
2. [集成测试模板](#集成测试模板)
3. [数据库测试模板](#数据库测试模板)
4. [API测试模板](#api测试模板)
5. [E2E测试模板](#e2e测试模板)
6. [性能测试模板](#性能测试模板)
7. [安全测试模板](#安全测试模板)

---

## 单元测试模板

### 基本结构

```python
"""
模块描述

测试 XXXService/XXXClass 的功能
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from app.services.xxx import XXXService
from app.models.xxx import XXXModel


@pytest.mark.unit
@pytest.mark.services
class TestXXXService:
    """测试 XXXService 类"""

    def test_method_success(self):
        """测试成功场景"""
        # Arrange
        service = XXXService()
        
        # Act
        result = service.method()
        
        # Assert
        assert result is not None

    def test_method_failure(self):
        """测试失败场景"""
        service = XXXService()
        
        with pytest.raises(ExpectedException):
            service.method()

    def test_method_edge_case(self):
        """测试边界条件"""
        service = XXXService()
        
        result = service.method(edge_value)
        assert result == expected_value
```

### 服务层测试模板

```python
@pytest.mark.unit
@pytest.mark.services
class TestServiceClass:
    """服务类测试模板"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.service = ServiceClass()

    def teardown_method(self):
        """每个测试方法后的清理"""
        pass

    def test_normal_operation(self, db_session):
        """测试正常操作"""
        # 准备测试数据
        entity = Model(field="value")
        db_session.add(entity)
        db_session.commit()

        # 执行测试
        result = self.service.operation(entity.id)

        # 验证结果
        assert result.status == "success"

    def test_with_mock(self):
        """测试使用Mock"""
        with patch('module.function') as mock_func:
            mock_func.return_value = "mocked"
            
            result = self.service.method()
            
            mock_func.assert_called_once()
            assert result == "expected"
```

---

## 集成测试模板

### API集成测试

```python
"""
API集成测试

测试完整的API请求/响应流程
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import create_test_project, create_test_task


@pytest.mark.api
@pytest.mark.integration
class TestXXXIntegration:
    """测试 XXX 集成"""

    def test_full_workflow(self, client: TestClient, db_session: Session):
        """测试完整工作流"""
        # 创建测试数据
        project = create_test_project(db_session)

        # 发送API请求
        response = client.get(f"/api/projects/{project.id}")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project.id

    def test_api_error_handling(self, client: TestClient):
        """测试API错误处理"""
        response = client.get("/api/projects/99999")
        assert response.status_code == 404
```

### 服务间集成测试

```python
@pytest.mark.integration
class TestServiceIntegration:
    """测试服务间集成"""

    def test_service_a_calls_service_b(self, db_session):
        """测试服务A调用服务B"""
        # 准备数据
        data = {"key": "value"}

        # 通过服务A执行操作
        service_a = ServiceA(db_session)
        result = service_a.process(data)

        # 验证服务B被正确调用
        assert result.processed == True
```

---

## 数据库测试模板

### 模型测试

```python
"""
数据模型测试

测试 XXXModel 的CRUD操作和约束
"""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.xxx import XXXModel


@pytest.mark.database
@pytest.mark.models
class TestXXXModel:
    """测试 XXXModel"""

    def test_create_model(self, db_session: Session):
        """测试创建模型"""
        entity = XXXModel(field="value")
        db_session.add(entity)
        db_session.commit()

        assert entity.id is not None

    def test_model_relationships(self, db_session: Session):
        """测试模型关系"""
        parent = ParentModel(name="parent")
        db_session.add(parent)
        db_session.commit()

        child = ChildModel(parent_id=parent.id)
        db_session.add(child)
        db_session.commit()

        db_session.refresh(parent)
        assert len(parent.children) == 1

    def test_unique_constraint(self, db_session: Session):
        """测试唯一约束"""
        entity1 = Model(unique_field="unique_value")
        db_session.add(entity1)
        db_session.commit()

        entity2 = Model(unique_field="unique_value")
        db_session.add(entity2)

        with pytest.raises(IntegrityError):
            db_session.commit()
```

### 迁移测试

```python
@pytest.mark.database
@pytest.mark.migrations
class TestMigrations:
    """测试数据库迁移"""

    def test_migration_up(self, test_db):
        """测试迁移向上"""
        # 执行迁移
        # 验证表结构
        pass

    def test_migration_down(self, test_db):
        """测试迁移向下"""
        # 回滚迁移
        # 验证表结构
        pass

    def test_data_migration(self, test_db):
        """测试数据迁移"""
        # 准备旧数据
        # 执行迁移
        # 验证数据转换
        pass
```

---

## API测试模板

### RESTful API测试

```python
"""
API端点测试

测试 /api/xxx 端点的所有操作
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
class TestXXXEndpoints:
    """测试 XXX API端点"""

    def test_list_endpoint(self, client: TestClient):
        """测试列表端点"""
        response = client.get("/api/xxx/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_endpoint(self, client: TestClient):
        """测试创建端点"""
        data = {"name": "test", "value": 123}
        response = client.post("/api/xxx/", json=data)
        assert response.status_code == 200
        assert response.json()["name"] == "test"

    def test_get_endpoint(self, client: TestClient, db_session):
        """测试获取端点"""
        entity = create_entity(db_session)
        response = client.get(f"/api/xxx/{entity.id}")
        assert response.status_code == 200

    def test_update_endpoint(self, client: TestClient, db_session):
        """测试更新端点"""
        entity = create_entity(db_session)
        response = client.put(
            f"/api/xxx/{entity.id}",
            json={"name": "updated"}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "updated"

    def test_delete_endpoint(self, client: TestClient, db_session):
        """测试删除端点"""
        entity = create_entity(db_session)
        response = client.delete(f"/api/xxx/{entity.id}")
        assert response.status_code == 200

    def test_not_found(self, client: TestClient):
        """测试404响应"""
        response = client.get("/api/xxx/99999")
        assert response.status_code == 404

    def test_validation_error(self, client: TestClient):
        """测试验证错误"""
        response = client.post("/api/xxx/", json={})
        assert response.status_code == 422
```

---

## E2E测试模板

### Playwright测试

```typescript
/**
 * E2E测试 - 用户流程
 * 测试完整的用户交互场景
 */

import { test, expect, Page } from '@playwright/test';

test.describe('用户流程测试', () => {
  test.beforeEach(async ({ page }) => {
    // 测试前设置
    await page.goto('/');
  });

  test('完整登录流程', async ({ page }) => {
    // 导航到登录页
    await page.click('[data-testid="login-button"]');
    
    // 填写表单
    await page.fill('[data-testid="username"]', 'testuser');
    await page.fill('[data-testid="password"]', 'password123');
    
    // 提交表单
    await page.click('[data-testid="submit-login"]');
    
    // 验证结果
    await expect(page.locator('[data-testid="welcome-message"]')).toBeVisible();
  });

  test('项目创建流程', async ({ page }) => {
    // 登录
    await login(page);
    
    // 创建项目
    await page.click('[data-testid="new-project"]');
    await page.fill('[data-testid="project-name"]', '测试项目');
    await page.click('[data-testid="create-project"]');
    
    // 验证项目创建成功
    await expect(page.locator('.project-card')).toContainText('测试项目');
  });
});

async function login(page: Page) {
  await page.goto('/login');
  await page.fill('[data-testid="username"]', 'testuser');
  await page.fill('[data-testid="password"]', 'password123');
  await page.click('[data-testid="submit-login"]');
}
```

---

## 性能测试模板

### 基准测试

```python
"""
性能基准测试

测试系统性能指标
"""

import pytest
import time
from locust import HttpUser, task, between


@pytest.mark.performance
class TestPerformance:
    """性能测试"""

    def test_response_time(self, client: TestClient):
        """测试响应时间"""
        start_time = time.time()
        response = client.get("/api/projects/")
        elapsed = time.time() - start_time

        assert response.status_code == 200
        assert elapsed < 0.5, f"响应时间 {elapsed:.2f}s 超过阈值"

    def test_throughput(self, client: TestClient):
        """测试吞吐量"""
        start_time = time.time()
        requests = 100

        for _ in range(requests):
            client.get("/api/projects/")

        elapsed = time.time() - start_time
        rps = requests / elapsed

        assert rps > 50, f"吞吐量 {rps:.2f} req/s 低于阈值"


class PerformanceUser(HttpUser):
    """Locust性能测试用户"""

    wait_time = between(1, 3)

    @task
    def list_projects(self):
        self.client.get("/api/projects/")

    @task(3)
    def get_project(self):
        self.client.get("/api/projects/1")
```

---

## 安全测试模板

### 安全扫描测试

```python
"""
安全测试

测试系统安全性
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.security
class TestSecurity:
    """安全测试"""

    def test_sql_injection(self, client: TestClient):
        """测试SQL注入"""
        malicious_input = "1; DROP TABLE projects; --"
        response = client.get(f"/api/projects/{malicious_input}")

        # 应该返回400或404，而不是500
        assert response.status_code in [400, 404, 422]

    def test_xss_attack(self, client: TestClient):
        """测试XSS攻击"""
        xss_payload = "<script>alert('xss')</script>"
        response = client.post(
            "/api/projects/",
            json={"name": xss_payload}
        )

        if response.status_code == 200:
            # 确保脚本被转义
            assert "<script>" not in response.json().get("name", "")

    def test_authentication_required(self, client: TestClient):
        """测试认证要求"""
        protected_endpoints = [
            "/api/admin/users",
            "/api/projects/create",
        ]

        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401

    def test_csrf_protection(self, client: TestClient):
        """测试CSRF保护"""
        # 无CSRF token的请求应该被拒绝
        response = client.post(
            "/api/projects/",
            json={"name": "test"},
            headers={"X-Requested-With": "XMLHttpRequest"}
        )
        # 根据实现验证

    def test_rate_limiting(self, client: TestClient):
        """测试速率限制"""
        for _ in range(100):
            client.get("/api/projects/")

        response = client.get("/api/projects/")
        # 应该被限流
        assert response.status_code == 429
```

---

## 测试标记说明

| 标记 | 说明 |
|------|------|
| `@pytest.mark.unit` | 单元测试 |
| `@pytest.mark.integration` | 集成测试 |
| `@pytest.mark.api` | API测试 |
| `@pytest.mark.database` | 数据库测试 |
| `@pytest.mark.performance` | 性能测试 |
| `@pytest.mark.security` | 安全测试 |
| `@pytest.mark.services` | 服务层测试 |
| `@pytest.mark.models` | 模型测试 |
| `@pytest.mark.e2e` | 端到端测试 |
| `@pytest.mark.slow` | 慢速测试 |

## 运行测试

```bash
# 运行所有测试
pytest

# 运行特定标记的测试
pytest -m unit
pytest -m integration
pytest -m "not slow"

# 运行特定文件
pytest tests/test_services.py

# 运行特定测试类
pytest tests/test_services.py::TestXXXService

# 运行特定测试方法
pytest tests/test_services.py::TestXXXService::test_method

# 生成覆盖率报告
pytest --cov=app --cov-report=html

# 并行运行测试
pytest -n auto

# 使用智能测试生成器
python skillscripts/test/intelligent_test_generator.py src/

# 生成测试报告
python skillscripts/test/test_report_generator.py --markdown
```

## 最佳实践

1. **测试命名**: 使用 `test_<功能>_<场景>` 格式
2. **测试隔离**: 每个测试应该独立，不依赖其他测试
3. **数据清理**: 测试后清理创建的数据
4. **Mock外部依赖**: 对外部服务使用Mock
5. **断言明确**: 使用清晰的断言消息
6. **覆盖边界**: 测试正常、异常和边界情况
7. **保持简洁**: 每个测试只验证一个行为
