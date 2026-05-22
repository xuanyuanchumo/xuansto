---
name: bingbu
description: 兵部，负责安全测试和测试先行，包括安全测试、渗透测试、防御策略、测试驱动开发等。
---
# 兵部技能指令

## 职责

| 职责领域 | 说明 |
|----------|------|
| 测试先行 | 在开发前编写测试用例驱动开发 |
| 单元测试 | 编写和执行单元测试 |
| 集成测试 | 编写和执行集成测试 |
| E2E测试 | 编写和执行端到端测试 |
| 性能测试 | 执行性能测试和基准测试 |
| 安全测试 | 进行漏洞扫描和安全测试 |
| 渗透测试 | 模拟攻击测试系统安全 |
| 防御策略 | 制定安全防御方案 |
| 规范驱动测试 | 从结构化规范自动生成测试用例 |
| 覆盖率验证 | 验证测试是否覆盖规范中的所有业务规则 |

## 工作流程

```
1. 执行环境检测，确保服务就绪（调用 ../../subskills/huanjing_jiance.md）
2. 接收尚书省的开发任务
3. 获取并解析结构化规范文档（SDD）
4. 分析需求，设计测试用例
5. 基于规范自动生成测试用例（详见 ../../subskills/sdd_liucheng.md）
6. 基于需求编写测试用例，确保测试独立于具体实现
7. 编写单元测试、集成测试、E2E测试用例
8. 执行规范覆盖率验证，确保测试覆盖所有规范定义
9. 测试用例移交门下省评审
10. 评审通过后移交工部开发
11. 工部开发完成后执行测试验证
12. 执行突变测试，验证测试用例的有效性
13. 输出详细测试执行日志
14. 识别需要外部安全技能支持的场景
15. 调用对应的外部安全技能
16. 整合安全测试结果
17. 测试通过后移交刑部重构
18. 生成测试报告和质量评估
```

## 测试策略决策流程（增强版）

### 测试需求分析

```
测试需求分析步骤:
  1. 测试类型识别
     - 功能测试
     - 性能测试
     - 安全测试
     - 兼容性测试
     - 回归测试
  
  2. 测试优先级评估
     - P0: 核心功能，必须100%通过
     - P1: 重要功能，影响用户体验
     - P2: 一般功能，影响范围有限
     - P3: 次要功能，边缘场景
  
  3. 测试范围界定
     - 新增功能测试
     - 回归测试范围
     - 集成测试范围
  
  4. 测试资源评估
     - 测试环境需求
     - 测试数据需求
     - 测试工具需求
```

### 测试策略制定

```json
{
  "test_strategy": {
    "strategy_id": "TS-001",
    "timestamp": "2024-01-01T00:00:00Z",
    "project": "project-name",
    "test_types": [
      {
        "type": "unit",
        "coverage_target": 0.85,
        "priority": "high",
        "estimated_effort_hours": 16
      },
      {
        "type": "integration",
        "coverage_target": 0.75,
        "priority": "high",
        "estimated_effort_hours": 24
      },
      {
        "type": "e2e",
        "coverage_target": 0.60,
        "priority": "medium",
        "estimated_effort_hours": 32
      }
    ],
    "test_environments": [
      {
        "name": "development",
        "purpose": "开发阶段测试",
        "services": ["db", "cache", "queue"]
      },
      {
        "name": "staging",
        "purpose": "预发布测试",
        "services": ["db", "cache", "queue", "external-api"]
      }
    ],
    "risk_assessment": {
      "high_risk_areas": ["支付模块", "认证模块"],
      "mitigation_strategies": ["增加测试用例", "安全测试"]
    }
  }
}
```

### 测试执行计划

| 阶段 | 测试类型 | 执行时机 | 通过标准 |
|------|----------|----------|----------|
| 开发阶段 | 单元测试 | 每次提交 | 覆盖率≥80%，全部通过 |
| 合并阶段 | 集成测试 | 每次合并 | 全部通过，无阻塞问题 |
| 发布阶段 | E2E测试 | 发布前 | 核心流程100%通过 |
| 运维阶段 | 回归测试 | 定期/变更后 | 无新引入问题 |

### 测试报告输出

```json
{
  "test_report": {
    "report_id": "TR-001",
    "timestamp": "2024-01-01T00:00:00Z",
    "execution_summary": {
      "total_tests": 250,
      "passed": 245,
      "failed": 3,
      "skipped": 2,
      "duration_seconds": 180
    },
    "coverage": {
      "line": 0.85,
      "branch": 0.78,
      "function": 0.92,
      "by_module": [
        {"module": "auth", "coverage": 0.95},
        {"module": "payment", "coverage": 0.88}
      ]
    },
    "failures": [
      {
        "test_name": "test_payment_process",
        "error": "Timeout waiting for response",
        "severity": "major",
        "location": "tests/test_payment.py:45"
      }
    ],
    "quality_metrics": {
      "test_quality_score": 0.88,
      "mutation_score": 0.82,
      "flaky_tests": 1
    },
    "recommendations": [
      "修复支付模块超时问题",
      "提高分支覆盖率"
    ]
  }
}
```

## 环境检测与测试前置

### 服务依赖检测流程

```
检测步骤:
  1. 检查数据库服务状态
  2. 检查缓存服务状态（如Redis）
  3. 检查消息队列服务状态（如RabbitMQ）
  4. 检查外部API服务可达性
  5. 检查文件系统权限
  6. 检查网络连接状态
输出: 环境检测报告
```

### Docker环境测试说明

```
Docker环境检测:
  1. 检查Docker服务运行状态
  2. 检查测试容器是否就绪
  3. 检查容器间网络连通性
  4. 检查挂载卷权限
  5. 检查端口映射正确性
```

### 环境检测命令示例

```bash
docker info                                          # 检查Docker服务状态
docker ps -a                                         # 检查容器运行状态
docker exec <db_container> pg_isready -U <username>  # 检查数据库连接
docker exec <redis_container> redis-cli ping         # 检查Redis连接
docker network inspect <network_name>                # 检查网络连通性
```

### 环境检测失败处理

```
处理流程:
  1. 记录失败原因和错误信息
  2. 尝试自动修复（如重启服务）
  3. 若无法自动修复，通知相关人员
  4. 等待环境恢复后重新检测
  5. 环境就绪后继续测试流程
```

## 测试类型说明

| 测试类型 | 说明 | 编写时机 | 测试范围 | 执行频率 |
|----------|------|----------|----------|----------|
| 单元测试 | 测试单个函数/方法 | 开发每个函数前编写 | 函数/类级别 | 每次提交 |
| 集成测试 | 测试模块间交互 | 模块集成前编写 | 模块/服务级别 | 每次合并 |
| E2E测试 | 测试完整业务流程 | 部署前编写 | 完整系统 | 每日/发布前 |
| 性能测试 | 测试系统性能指标 | 功能稳定后 | 关键路径 | 每周/发布前 |
| 安全测试 | 测试安全漏洞 | 开发完成后 | 全系统 | 每月/发布前 |

## 单元测试编写指南

### 单元测试原则

```
FIRST原则:
  - Fast（快速）: 测试应该快速执行
  - Independent（独立）: 测试之间不应相互依赖
  - Repeatable（可重复）: 在任何环境下结果一致
  - Self-validating（自验证）: 测试应该明确返回通过/失败
  - Timely（及时）: 在开发过程中及时编写

单元测试特点:
  - 测试范围小，只测试一个单元
  - 执行速度快，毫秒级
  - 不依赖外部资源（数据库、网络等）
  - 使用Mock/Stub隔离依赖
```

### 单元测试编写流程

```
1. 识别被测单元
   - 确定要测试的函数/方法
   - 分析输入输出
   - 识别依赖项

2. 设计测试场景
   - 正常场景（Happy Path）
   - 边界条件
   - 异常情况
   - 错误处理

3. 准备测试环境
   - 初始化测试数据
   - 配置Mock对象
   - 设置前置条件

4. 执行测试
   - 调用被测方法
   - 捕获返回值/异常

5. 验证结果
   - 断言返回值
   - 验证状态变化
   - 确认Mock交互
```

### 单元测试模板

```python
# Python示例
import unittest
from unittest.mock import Mock, patch

class TestUserService(unittest.TestCase):
    def setUp(self):
        """测试前置准备"""
        self.user_repo = Mock()
        self.email_service = Mock()
        self.user_service = UserService(self.user_repo, self.email_service)
    
    def test_create_user_success(self):
        """测试创建用户成功"""
        # Arrange
        user_data = {"username": "testuser", "email": "test@example.com"}
        self.user_repo.find_by_username.return_value = None
        self.user_repo.save.return_value = User(id=1, **user_data)
        
        # Act
        result = self.user_service.create_user(user_data)
        
        # Assert
        self.assertEqual(result.username, "testuser")
        self.user_repo.save.assert_called_once()
        self.email_service.send_welcome_email.assert_called_once()
    
    def test_create_user_duplicate_username(self):
        """测试创建用户-用户名已存在"""
        # Arrange
        user_data = {"username": "existing", "email": "test@example.com"}
        self.user_repo.find_by_username.return_value = User(id=1, **user_data)
        
        # Act & Assert
        with self.assertRaises(DuplicateUserError):
            self.user_service.create_user(user_data)
```

```javascript
// JavaScript示例
const { UserService } = require('./userService');

describe('UserService', () => {
  let userService;
  let mockUserRepo;
  let mockEmailService;

  beforeEach(() => {
    mockUserRepo = {
      findByUsername: jest.fn(),
      save: jest.fn()
    };
    mockEmailService = {
      sendWelcomeEmail: jest.fn()
    };
    userService = new UserService(mockUserRepo, mockEmailService);
  });

  describe('createUser', () => {
    it('should create user successfully', async () => {
      // Arrange
      const userData = { username: 'testuser', email: 'test@example.com' };
      mockUserRepo.findByUsername.mockResolvedValue(null);
      mockUserRepo.save.mockResolvedValue({ id: 1, ...userData });

      // Act
      const result = await userService.createUser(userData);

      // Assert
      expect(result.username).toBe('testuser');
      expect(mockUserRepo.save).toHaveBeenCalledTimes(1);
      expect(mockEmailService.sendWelcomeEmail).toHaveBeenCalledTimes(1);
    });

    it('should throw error when username exists', async () => {
      // Arrange
      const userData = { username: 'existing', email: 'test@example.com' };
      mockUserRepo.findByUsername.mockResolvedValue({ id: 1, ...userData });

      // Act & Assert
      await expect(userService.createUser(userData))
        .rejects.toThrow('Username already exists');
    });
  });
});
```

### 单元测试最佳实践

```
1. 测试命名
   - 清晰描述被测行为
   - 包含输入条件和期望结果
   - 使用自然语言风格

2. 测试组织
   - 按功能模块组织测试
   - 使用describe/context分组
   - 保持测试文件结构清晰

3. 断言使用
   - 使用具体的断言方法
   - 一个测试验证一个概念
   - 避免过多断言

4. Mock使用
   - 只Mock外部依赖
   - 验证Mock交互
   - 避免过度Mock
```

## 集成测试策略

### 集成测试原则

```
集成测试目标:
  - 验证模块间交互正确
  - 检测接口契约问题
  - 验证数据流完整性
  - 确保配置正确

集成测试范围:
  - 模块间接口
  - 数据库交互
  - 外部服务调用
  - 消息队列通信
```

### 集成测试策略类型

#### 大爆炸集成
```
特点:
  - 所有模块一次性集成
  - 测试整个系统
  - 适合小型项目

优缺点:
  + 简单直接
  - 问题定位困难
  - 风险集中
```

#### 增量集成
```
自顶向下:
  - 从主控模块开始
  - 逐步集成下层模块
  - 使用桩模块替代未集成模块

自底向上:
  - 从底层模块开始
  - 逐步集成上层模块
  - 使用驱动模块调用未集成模块

三明治集成:
  - 自顶向下和自底向上结合
  - 中间层最后集成
  - 适合分层架构
```

### 集成测试编写指南

```python
# 数据库集成测试示例
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TestUserRepositoryIntegration:
    @pytest.fixture
    def db_session(self):
        # 使用测试数据库
        engine = create_engine('postgresql://test:test@localhost/test_db')
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.rollback()
        session.close()
    
    def test_save_and_find_user(self, db_session):
        """测试用户保存和查询"""
        # Arrange
        user_repo = UserRepository(db_session)
        user = User(username="test", email="test@example.com")
        
        # Act
        saved_user = user_repo.save(user)
        found_user = user_repo.find_by_id(saved_user.id)
        
        # Assert
        assert found_user is not None
        assert found_user.username == "test"
        assert found_user.email == "test@example.com"
```

```javascript
// API集成测试示例
const request = require('supertest');
const app = require('../app');

describe('User API Integration', () => {
  let authToken;

  beforeAll(async () => {
    // 获取认证token
    const response = await request(app)
      .post('/api/auth/login')
      .send({ username: 'admin', password: 'password' });
    authToken = response.body.token;
  });

  describe('POST /api/users', () => {
    it('should create user with valid data', async () => {
      const userData = {
        username: 'newuser',
        email: 'new@example.com',
        password: 'password123'
      };

      const response = await request(app)
        .post('/api/users')
        .set('Authorization', `Bearer ${authToken}`)
        .send(userData)
        .expect(201);

      expect(response.body.username).toBe(userData.username);
      expect(response.body.email).toBe(userData.email);
    });

    it('should return 400 for invalid data', async () => {
      const invalidData = { username: 'ab' }; // 太短

      await request(app)
        .post('/api/users')
        .set('Authorization', `Bearer ${authToken}`)
        .send(invalidData)
        .expect(400);
    });
  });
});
```

## E2E测试能力

### E2E测试原则

```
E2E测试目标:
  - 验证完整业务流程
  - 模拟真实用户操作
  - 确保系统各组件协同工作
  - 验证端到端数据流

E2E测试范围:
  - 用户界面交互
  - 完整业务场景
  - 多系统集成
  - 真实环境配置
```

### E2E测试框架选择

| 框架 | 适用场景 | 特点 |
|------|----------|------|
| Cypress | Web应用 | 现代、易用、调试友好 |
| Selenium | 多浏览器 | 成熟、支持广泛 |
| Playwright | 现代Web | 多浏览器、自动等待 |
| Puppeteer | Chrome | 无头浏览器、性能好 |

### E2E测试编写指南

```javascript
// Cypress示例
describe('User Registration Flow', () => {
  beforeEach(() => {
    cy.visit('/register');
  });

  it('should complete registration successfully', () => {
    // 填写注册表单
    cy.get('[data-testid="username"]').type('testuser');
    cy.get('[data-testid="email"]').type('test@example.com');
    cy.get('[data-testid="password"]').type('Password123!');
    cy.get('[data-testid="confirm-password"]').type('Password123!');

    // 提交表单
    cy.get('[data-testid="submit-button"]').click();

    // 验证跳转和成功消息
    cy.url().should('include', '/dashboard');
    cy.get('[data-testid="welcome-message"]')
      .should('contain', 'Welcome, testuser');

    // 验证用户已登录
    cy.get('[data-testid="user-menu"]').should('be.visible');
  });

  it('should show validation errors', () => {
    // 提交空表单
    cy.get('[data-testid="submit-button"]').click();

    // 验证错误消息
    cy.get('[data-testid="username-error"]')
      .should('contain', 'Username is required');
    cy.get('[data-testid="email-error"]')
      .should('contain', 'Email is required');
  });
});
```

```python
# Playwright示例
from playwright.sync_api import sync_playwright

def test_purchase_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # 访问商城
        page.goto('https://shop.example.com')
        
        # 浏览商品
        page.click('text=Products')
        page.click('text=Add to Cart', timeout=5000)
        
        # 查看购物车
        page.click('[data-testid="cart-icon"]')
        expect(page.locator('[data-testid="cart-count"]')).to_have_text('1')
        
        # 结算
        page.click('text=Checkout')
        page.fill('[name="email"]', 'customer@example.com')
        page.fill('[name="card"]', '4111111111111111')
        page.click('text=Complete Purchase')
        
        # 验证订单成功
        expect(page.locator('[data-testid="order-confirmation"]')
               ).to_be_visible()
        
        browser.close()
```

### E2E测试最佳实践

```
1. 测试数据管理
   - 使用测试专用数据
   - 测试前清理数据
   - 避免测试间数据冲突

2. 选择器策略
   - 使用data-testid属性
   - 避免使用CSS类选择器
   - 保持选择器稳定

3. 等待策略
   - 使用智能等待
   - 避免固定等待时间
   - 等待元素可见/可点击

4. 测试隔离
   - 每个测试独立运行
   - 测试后清理状态
   - 使用测试钩子
```

## 性能测试指南

### 性能测试类型

| 类型 | 目的 | 指标 | 工具 |
|------|------|------|------|
| 负载测试 | 测试正常负载下的性能 | 响应时间、吞吐量 | JMeter, k6 |
| 压力测试 | 测试极限负载下的行为 | 最大并发、错误率 | JMeter, Locust |
| 容量测试 | 确定系统容量上限 | 最大用户数、数据量 | 自定义脚本 |
| 稳定性测试 | 测试长时间运行的稳定性 | 内存泄漏、性能衰减 | 持续监控 |
| 基准测试 | 建立性能基线 | 各项性能指标 | 自动化工具 |

### 性能测试指标

```
响应时间指标:
  - 平均响应时间: < 200ms
  - P50响应时间: < 100ms
  - P95响应时间: < 500ms
  - P99响应时间: < 1000ms

吞吐量指标:
  - QPS (Queries Per Second): > 1000
  - TPS (Transactions Per Second): > 500

资源使用指标:
  - CPU使用率: < 70%
  - 内存使用率: < 80%
  - 磁盘I/O: < 80%
  - 网络带宽: < 70%

错误率指标:
  - HTTP 5xx错误率: < 0.1%
  - 超时率: < 0.5%
  - 失败率: < 0.1%
```

### 性能测试脚本示例

```javascript
// k6性能测试脚本
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },  // 逐步增加到100用户
    { duration: '5m', target: 100 },  // 保持100用户5分钟
    { duration: '2m', target: 200 },  // 增加到200用户
    { duration: '5m', target: 200 },  // 保持200用户5分钟
    { duration: '2m', target: 0 },    // 逐步减少到0
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95%请求响应时间<500ms
    http_req_failed: ['rate<0.1'],     // 错误率<0.1%
  },
};

export default function () {
  const response = http.get('https://api.example.com/users');
  
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
    'response has users': (r) => r.json().users !== undefined,
  });
  
  sleep(1);
}
```

```python
# Locust性能测试脚本
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 5)
    
    def on_start(self):
        """用户启动时登录"""
        self.client.post("/api/auth/login", {
            "username": "testuser",
            "password": "password"
        })
    
    @task(3)
    def browse_products(self):
        """浏览商品 - 权重3"""
        self.client.get("/api/products")
    
    @task(1)
    def view_product_detail(self):
        """查看商品详情 - 权重1"""
        self.client.get("/api/products/1")
    
    @task(1)
    def add_to_cart(self):
        """添加到购物车"""
        self.client.post("/api/cart/items", {
            "product_id": 1,
            "quantity": 1
        })
```

## 安全测试指南

### 安全测试类型

| 类型 | 说明 | 工具 | 频率 |
|------|------|------|------|
| 静态分析 | 代码安全扫描 | SonarQube, Checkmarx | 每次提交 |
| 依赖扫描 | 检查依赖漏洞 | Snyk, OWASP DC | 每日 |
| 动态扫描 | 运行时安全测试 | OWASP ZAP, Burp Suite | 每周 |
| 渗透测试 | 模拟攻击测试 | Metasploit, 手工测试 | 每月 |
| 配置审计 | 安全配置检查 | CIS Benchmarks | 每月 |

### OWASP Top 10 测试

```
1. 注入攻击 (Injection)
   - SQL注入测试
   - NoSQL注入测试
   - 命令注入测试
   - LDAP注入测试

2. 失效的身份认证 (Broken Authentication)
   - 弱密码策略测试
   - 会话管理测试
   - 多因素认证测试
   - 密码重置测试

3. 敏感数据泄露 (Sensitive Data Exposure)
   - 传输加密测试
   - 存储加密测试
   - 密钥管理测试
   - 敏感信息过滤测试

4. XML外部实体 (XXE)
   - XML解析器配置测试
   - DTD处理测试
   - 外部实体引用测试

5. 失效的访问控制 (Broken Access Control)
   - 水平越权测试
   - 垂直越权测试
   - 目录遍历测试
   - 未授权访问测试

6. 安全配置错误 (Security Misconfiguration)
   - 默认配置检查
   - 错误信息泄露检查
   - 不必要功能检查
   - 安全头检查

7. 跨站脚本 (XSS)
   - 反射型XSS测试
   - 存储型XSS测试
   - DOM型XSS测试
   - CSP策略测试

8. 不安全的反序列化 (Insecure Deserialization)
   - 反序列化漏洞测试
   - 对象注入测试

9. 使用含有已知漏洞的组件 (Using Components with Known Vulnerabilities)
   - 依赖扫描
   - 版本检查
   - 漏洞数据库比对

10. 不足的日志记录和监控 (Insufficient Logging and Monitoring)
    - 日志完整性检查
    - 监控覆盖检查
    - 告警机制测试
```

### 安全测试检查清单

```
认证与授权:
  □ 强密码策略实施
  □ 多因素认证支持
  □ 会话超时处理
  □ 权限最小化原则
  □ 敏感操作二次确认

输入验证:
  □ 所有输入都经过验证
  □ 使用白名单验证
  □ 输出编码处理
  □ 参数化查询使用

会话管理:
  □ 安全会话ID生成
  □ 会话固定防护
  □ 并发会话控制
  □ 安全注销功能

数据传输:
  □ HTTPS强制使用
  □ 敏感数据加密传输
  □ HSTS头配置
  □ 证书有效性检查

错误处理:
  □ 不泄露敏感信息
  □ 统一错误处理
  □ 详细日志记录
  □ 安全事件告警
```

## 测试编写流程

### 1. 环境检测与准备

```
检测内容:
  1. 执行环境检测（调用 ../../subskills/huanjing_jiance.md）
  2. 确认测试环境就绪
  3. 准备测试数据
  4. 配置测试参数
输出: 环境就绪确认
```

### 2. 需求分析与测试设计

```
输入: 需求文档、用户故事、验收标准
分析步骤:
  1. 识别功能点
  2. 确定测试范围
  3. 设计测试场景
  4. 划分测试类型（单元/集成/E2E）
  5. 确定测试优先级
输出: 测试设计文档
```

### 3. 测试用例设计

```
设计原则:
  - 基于需求，而非实现
  - 覆盖正常路径和异常路径
  - 考虑边界条件
  - 考虑性能和安全

设计方法:
  - 等价类划分
  - 边界值分析
  - 决策表
  - 状态转换
  - 错误推测
```

## 测试用例设计规范

### 测试用例结构规范

```
测试用例基本结构:
  1. 用例标识: 唯一标识符，如 UT-001, IT-001, ET-001
  2. 用例名称: 清晰描述测试场景和预期结果
  3. 前置条件: 测试执行前必须满足的条件
  4. 测试步骤: 具体的操作步骤
  5. 测试数据: 输入数据和预期输出
  6. 预期结果: 期望的测试结果
  7. 后置处理: 测试完成后的清理工作
  8. 优先级: P0/P1/P2/P3
  9. 关联需求: 对应的需求编号
```

### 测试命名规范

```
单元测试命名:
  格式: test_<方法名>_<场景描述>_<预期结果>
  示例: test_create_user_when_username_exists_should_throw_exception

集成测试命名:
  格式: test_<模块名>_<集成场景>_<预期结果>
  示例: test_user_service_database_integration_should_persist_user

E2E测试命名:
  格式: test_<业务流程>_<用户场景>_<预期结果>
  示例: test_user_registration_flow_with_valid_data_should_succeed
```

### 测试数据设计规范

```
测试数据类型:
  1. 正常数据: 符合业务规则的正常输入
  2. 边界数据: 边界值和临界值
  3. 异常数据: 不符合规则的异常输入
  4. 空值数据: null、空字符串、空集合
  5. 极端数据: 超大值、超长字符串、特殊字符

测试数据管理:
  - 使用测试数据构建器（Builder Pattern）
  - 测试数据与测试代码分离
  - 使用Fixture管理测试数据
  - 避免硬编码测试数据
```

### 断言规范

```
断言原则:
  1. 一个测试验证一个行为
  2. 断言信息清晰明确
  3. 使用具体的断言方法
  4. 避免过多断言

断言示例:
  # 推荐
  assert result.status == 200, f"Expected status 200, got {result.status}"
  assert result.data["username"] == "testuser"
  
  # 不推荐
  assert result == expected  # 信息不够明确
```

## 测试优先级策略

### 优先级定义

| 优先级 | 名称 | 说明 | 执行频率 | 覆盖率要求 |
|--------|------|------|----------|------------|
| P0 | 核心功能 | 系统核心业务流程，必须100%通过 | 每次提交 | 100% |
| P1 | 重要功能 | 重要业务功能，影响用户体验 | 每次合并 | 90% |
| P2 | 一般功能 | 常规功能，影响范围有限 | 每日构建 | 80% |
| P3 | 次要功能 | 边缘场景，低频使用功能 | 发布前 | 70% |

### 优先级判定标准

```
P0（核心功能）判定标准:
  - 核心业务流程关键节点
  - 涉及资金交易或敏感数据
  - 用户高频使用功能
  - 系统稳定性关键点
  - 安全关键功能

P1（重要功能）判定标准:
  - 主要业务功能
  - 用户常用功能
  - 影响用户体验的功能
  - 数据一致性关键点

P2（一般功能）判定标准:
  - 常规业务功能
  - 用户偶尔使用功能
  - 非关键业务流程
  - 辅助功能

P3（次要功能）判定标准:
  - 边缘场景
  - 低频使用功能
  - 非核心业务
  - 可降级功能
```

### 测试执行顺序策略

```
执行顺序原则:
  1. 先执行P0测试，确保核心功能正常
  2. 再执行P1测试，验证重要功能
  3. 然后执行P2测试，覆盖一般功能
  4. 最后执行P3测试，完成全面覆盖

快速反馈策略:
  - 本地开发: 只执行P0和P1测试
  - 提交代码: 执行P0、P1、P2测试
  - 合并代码: 执行全部测试
  - 发布前: 执行全部测试 + E2E测试
```

### 测试用例优先级分配示例

```
用户登录功能:
  P0:
    - 正确用户名密码登录成功
    - 错误密码登录失败
    - 用户不存在登录失败
  
  P1:
    - 密码错误次数限制
    - 登录超时处理
    - 会话管理
  
  P2:
    - 记住登录状态
    - 多设备登录处理
    - 登录日志记录
  
  P3:
    - 登录页面UI展示
    - 登录动画效果
    - 帮助链接跳转
```

### 测试失败处理优先级

```
P0测试失败:
  - 立即停止当前工作
  - 最高优先级修复
  - 阻止代码合并
  - 通知相关人员

P1测试失败:
  - 当日内修复
  - 阻止代码合并
  - 记录问题跟踪

P2测试失败:
  - 两个工作日内修复
  - 不阻止代码合并
  - 记录技术债务

P3测试失败:
  - 下个迭代修复
  - 不阻止发布
  - 记录改进项
```

### 4. 测试用例编写

```
编写顺序:
  1. 先写失败测试（红）
  2. 确保测试失败原因正确
  3. 记录预期行为

编写规范:
  - 测试名称清晰表达意图
  - 遵循AAA模式（Arrange-Act-Assert）
  - 每个测试只验证一个行为
  - 避免测试间依赖
```

### 5. 测试评审

```
评审内容:
  - 测试覆盖是否完整
  - 测试用例是否合理
  - 断言是否充分
  - 是否有遗漏场景

评审流程:
  1. 自我评审
  2. 同行评审
  3. 门下省评审
  4. 评审通过后移交开发
```

### 6. 测试维护

```
维护场景:
  - 需求变更时更新测试
  - 发现遗漏场景时补充测试
  - 重构时确保测试通过
  - 定期清理过时测试
```

## 测试用例模板

详细测试用例模板（单元测试、集成测试、E2E测试、文档模板）请参考 [测试模板](../../resources/ceshi_muban.md)。

详细测试用例设计方法（边界值分析、等价类划分等）请参考 [测试用例设计](../../subskills/ceshi_yongli_sheji.md)。

详细测试流程（单元测试、集成测试、E2E测试）请参考 [测试流程](../../subskills/ceshi.md)。

详细安全测试流程请参考 [安全测试](../../subskills/anquan_ceshi.md)。

详细突变测试流程请参考 [突变测试](../../subskills/tubian_ceshi.md)。

## 测试覆盖率要求

### 覆盖率类型

| 类型 | 说明 | 最低要求 | 目标值 |
|------|------|----------|--------|
| 行覆盖率 | 代码行执行比例 | 70% | 80% |
| 分支覆盖率 | 分支执行比例 | 60% | 75% |
| 函数覆盖率 | 函数调用比例 | 80% | 90% |
| 语句覆盖率 | 语句执行比例 | 70% | 85% |

### 按模块类型的要求

| 模块类型 | 行覆盖率 | 分支覆盖率 | 说明 |
|----------|----------|------------|------|
| 核心业务逻辑 | 90% | 85% | 关键功能必须高覆盖 |
| API接口 | 85% | 80% | 接口必须充分测试 |
| 工具函数 | 80% | 75% | 工具函数需全面测试 |
| UI组件 | 70% | 60% | UI测试成本较高 |
| 配置模块 | 60% | 50% | 配置相对简单 |

### 覆盖率检查流程

```
1. 本地开发时
   - 提交前运行测试
   - 检查覆盖率报告
   - 确保新增代码有测试

2. 代码评审时
   - CI自动运行覆盖率检查
   - 覆盖率不达标则阻止合并
   - 评审者检查测试质量

3. 合并前
   - 覆盖率必须达标
   - 新增代码覆盖率不低于项目平均
   - 关键路径必须有测试
```

## 外部技能调用

### 安全测试技能

| 技能类型 | 说明 |
|----------|------|
| 安全测试 | 可调用外部安全测试相关技能，支持多种安全测试框架和工具，提供标准化安全测试报告 |
| 渗透测试 | 调用外部渗透测试工具和技能，支持Web应用、网络、社会工程学测试 |
| 漏洞扫描 | 调用外部漏洞扫描技能，支持代码、依赖、配置漏洞扫描，生成修复建议 |

## 测试驱动开发验证流程

```
1. 执行单元测试套件
2. 执行集成测试套件
3. 执行E2E测试套件
4. 生成测试覆盖率报告
5. 分析测试失败原因
6. 反馈给工部修复
7. 重新执行测试验证
8. 所有测试通过后移交刑部
```

## 白盒化测试要求

### 基于需求的测试用例设计

- 测试用例必须基于需求规格编写，而非基于代码实现
- 测试用例应独立于具体实现细节，关注行为契约
- 避免测试与实现耦合，确保重构后测试仍然有效
- 记录每个测试用例对应的需求点

### 突变测试

```
突变测试目标: 检测测试用例是否能发现代码缺陷
突变测试指标:
  - 突变覆盖率：被杀死的突变体比例
  - 存活突变体分析：识别测试盲区
突变测试报告内容:
  - 突变体总数与存活数
  - 各文件突变测试结果
  - 测试盲区分析
  - 改进建议
```

### 测试执行日志

```
日志内容包括:
  - 测试执行时间戳
  - 测试环境信息
  - 执行的测试用例列表
  - 每个测试用例的执行结果（通过/失败/跳过）
  - 失败测试的详细错误信息
  - 测试执行耗时统计
  - 覆盖率数据
```

## 输出物清单

| 输出物 | 说明 |
|--------|------|
| 测试用例文件 | 单元测试、集成测试、E2E测试 |
| 测试覆盖率报告 | 各维度覆盖率统计 |
| 突变测试报告 | 突变测试结果分析 |
| 测试执行日志 | 详细测试执行记录 |
| 安全测试报告 | 安全测试结果与建议 |
| 性能测试报告 | 性能测试结果与建议 |

## 透明度记录要求

### 测试策略记录

- 记录测试策略推理过程：包括风险分析、测试优先级排序、测试方法选择
- 记录测试用例设计依据：包括需求覆盖分析、边界条件识别、异常场景考虑

### 记录内容规范

```
- 决策时间戳
- 测试目标与范围
- 风险评估结果
- 测试策略选择理由
- 测试用例设计思路
- 预期覆盖率目标
```

## SDD 规范驱动测试

详细的SDD规范驱动测试流程（包括测试用例生成、覆盖率验证、测试数据生成、追溯矩阵）请参考 [SDD规范驱动测试](../../subskills/sdd_liucheng.md)。

## 协同调用接口

### 接口定义

兵部作为测试执行机构，提供以下协同调用接口供其他技能调用：

| 接口名称 | 接口描述 | 调用方 |
|----------|----------|--------|
| `run_tests` | 测试执行接口 | 工部、尚书省 |
| `generate_test_cases` | 测试用例生成接口 | 中书省 |
| `validate_coverage` | 覆盖率验证接口 | 刑部 |
| `run_security_test` | 安全测试执行接口 | 尚书省 |

### 输入参数规范

#### 测试执行接口参数

```json
{
  "interface": "run_tests",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "test_type": "unit|integration|e2e|performance|security",
    "test_path": "测试文件路径",
    "options": {
      "coverage": true,
      "parallel": true,
      "fail_fast": false,
      "timeout_ms": 30000
    },
    "environment": {
      "env_type": "unit-test|integration-test|e2e-test",
      "services": ["依赖服务列表"]
    }
  }
}
```

#### 测试用例生成接口参数

```json
{
  "interface": "generate_test_cases",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "spec_document": {
      "path": "规范文档路径",
      "version": "1.0.0"
    },
    "generation_options": {
      "test_types": ["unit", "integration"],
      "coverage_target": 80,
      "include_edge_cases": true,
      "include_error_scenarios": true
    }
  }
}
```

#### 覆盖率验证接口参数

```json
{
  "interface": "validate_coverage",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "code_path": "代码路径",
    "test_path": "测试路径",
    "thresholds": {
      "line_coverage": 80,
      "branch_coverage": 75,
      "function_coverage": 90
    },
    "report_format": "json|html|markdown"
  }
}
```

### 输出格式规范

```json
{
  "interface": "run_tests",
  "call_id": "TEST-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "status": "passed|failed|partial",
  "result": {
    "summary": {
      "total": 100,
      "passed": 95,
      "failed": 3,
      "skipped": 2
    },
    "coverage": {
      "line": 0.85,
      "branch": 0.78,
      "function": 0.92
    },
    "failures": [
      {
        "test_name": "测试名称",
        "error_message": "错误信息",
        "stack_trace": "堆栈跟踪"
      }
    ],
    "execution_time_ms": 5000
  }
}
```

### 调用示例

```bash
# 调用测试执行接口
调用 ./SKILL.md --interface=run_tests \
  --test-type="unit" \
  --test-path="./tests/" \
  --options='{"coverage":true,"parallel":true}'

# 调用测试用例生成接口
调用 ./SKILL.md --interface=generate_test_cases \
  --spec-document='{"path":"docs/spec.json"}' \
  --generation-options='{"coverage_target":80}'

# 调用覆盖率验证接口
调用 ./SKILL.md --interface=validate_coverage \
  --code-path="./src/" \
  --test-path="./tests/" \
  --thresholds='{"line_coverage":80}'
```

---

## 下属四司

| 司名 | 职责 |
|------|------|
| yibusi（兵部仪司） | 安全规范 |
| zhibusi（职部司） | 渗透测试 |
| jiabucangsi（驾部仓司） | 安全工具 |
| kubucangsi（库部仓司） | 安全资源 |

---

## 测试自动化增强

### 测试流水线配置

```yaml
test_pipeline:
  stages:
    - name: "unit_test"
      parallel: true
      timeout_minutes: 10
      fail_fast: true
      coverage_threshold: 80
      
    - name: "integration_test"
      parallel: false
      timeout_minutes: 30
      dependencies: ["unit_test"]
      
    - name: "e2e_test"
      parallel: false
      timeout_minutes: 60
      dependencies: ["integration_test"]
      retry_count: 2
      
  reporting:
    formats: ["junit", "html", "json"]
    artifacts_retention_days: 30
```

### 测试数据管理

---

## 协同效果评估能力

### 测试先行协同评估指标

兵部作为测试执行机构，负责评估测试先行在三省六部协同中的效果。

| 评估维度 | 指标 | 目标值 | 度量方法 |
|----------|------|--------|----------|
| 测试覆盖率 | 代码覆盖率 | ≥80% | 覆盖率工具统计 |
| 测试先行率 | 先写测试的比例 | 100% | 开发流程统计 |
| 测试通过率 | 一次测试通过率 | ≥85% | 测试结果统计 |
| 缺陷检出率 | 测试发现缺陷比例 | ≥90% | 缺陷来源分析 |
| 测试效率 | 测试执行平均时间 | ≤10分钟 | 时间统计 |

### 测试先行协同评估报告格式

```json
{
  "evaluation_id": "EVAL-BINGBU-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-07T23:59:59Z"
  },
  "test_metrics": {
    "total_tests": 500,
    "passed_tests": 475,
    "failed_tests": 25,
    "pass_rate": 0.95,
    "avg_execution_time_seconds": 45
  },
  "coverage_metrics": {
    "line_coverage": 0.85,
    "branch_coverage": 0.78,
    "function_coverage": 0.92,
    "statement_coverage": 0.87
  },
  "tdd_metrics": {
    "test_first_rate": 1.0,
    "red_green_cycle_avg_minutes": 22,
    "refactor_after_green_rate": 0.75
  },
  "defect_metrics": {
    "defects_found_in_test": 45,
    "defects_found_in_prod": 5,
    "defect_detection_rate": 0.90,
    "defect_density": 0.05
  },
  "recommendations": [
    {
      "category": "coverage_improvement",
      "priority": "high",
      "description": "提高分支覆盖率至80%以上",
      "expected_impact": "减少生产环境缺陷"
    }
  ]
}
```

---

## 流水线协调能力

### 流水线测试先行节点

兵部在白盒化7阶段流水线中负责测试先行阶段的执行。

| 阶段 | 兵部角色 | 测试内容 | 输出物 |
|------|----------|----------|--------|
| 需求分析 | 支持 | 需求可测试性分析 | 可测试性报告 |
| SDD规范定义 | 支持 | 测试规范定义 | 测试规范 |
| 审议批准 | 支持 | 测试用例评审 | 评审意见 |
| 测试先行 | 主导 | 测试用例编写 | 测试用例 |
| 代码实现 | 支持 | 测试执行验证 | 测试结果 |
| 持续重构 | 支持 | 回归测试执行 | 回归测试报告 |
| 部署发布 | 主导 | E2E测试执行 | E2E测试报告 |

### 流水线测试配置

```yaml
pipeline_test_config:
  test_execution:
    mode: "test_first"
    parallel: true
    fail_fast: false
    
  test_stages:
    - stage: "test_first"
      test_type: "unit"
      coverage_threshold: 0.80
      timeout_minutes: 15
      
    - stage: "implementation"
      test_type: "unit"
      coverage_threshold: 0.85
      timeout_minutes: 10
      
    - stage: "refactoring"
      test_type: "regression"
      coverage_threshold: 0.80
      timeout_minutes: 20
      
    - stage: "deployment"
      test_type: "e2e"
      coverage_threshold: 0.70
      timeout_minutes: 30
```

---

## 增强功能集成

### 与provincial_coordinator集成

兵部通过provincial_coordinator.py实现测试流程的自动化和协同：

```python
from scripts.provincial_coordinator import (
    SmartDispatcher,
    TaskRequirement,
    TaskPriority
)

dispatcher = SmartDispatcher()

def execute_tests_for_task(task_id: str, test_requirements: dict):
    requirement = TaskRequirement(
        task_id=task_id,
        required_capabilities={
            "test_design": 0.9,
            "test_first": 0.85
        },
        preferred_specializations=["bingbu"],
        priority=TaskPriority.HIGH
    )
    
    decision = dispatcher.find_best_match(requirement, "ministry")
    
    return {
        "assigned_entity": decision.assigned_entity,
        "match_score": decision.overall_score,
        "test_execution": test_requirements
    }
```

---

## 测试质量保障

### 测试质量检查清单

```
□ 测试用例覆盖所有需求
□ 测试用例独立可执行
□ 测试用例有清晰的断言
□ 测试覆盖率达标
□ 测试执行时间合理
□ 测试结果可重复
□ 测试失败有清晰诊断信息
□ 测试数据准备完整
```

### 测试质量评分

| 评分项 | 权重 | 评分标准 |
|--------|------|----------|
| 覆盖率 | 30% | 测试覆盖所有必要代码路径 |
| 测试先行率 | 25% | 测试先于实现编写 |
| 通过率 | 20% | 测试一次通过率高 |
| 执行效率 | 15% | 测试执行时间合理 |
| 可维护性 | 10% | 测试代码易于维护 |

```json
{
  "test_data_management": {
    "strategies": {
      "fixtures": {
        "description": "静态测试数据",
        "location": "tests/fixtures/",
        "format": "json|yaml"
      },
      "factories": {
        "description": "动态生成测试数据",
        "library": "factory_boy|faker",
        "locale": "zh_CN"
      },
      "mocks": {
        "description": "模拟外部依赖",
        "tools": ["unittest.mock", "pytest-mock"]
      }
    },
    "cleanup": {
      "strategy": "rollback",
      "verify_clean": true
    }
  }
}
```

### 测试报告增强

```json
{
  "test_report": {
    "report_id": "RPT-001",
    "timestamp": "2024-01-01T00:00:00Z",
    "summary": {
      "total_tests": 150,
      "passed": 145,
      "failed": 3,
      "skipped": 2,
      "duration_seconds": 120
    },
    "coverage": {
      "line": 85.5,
      "branch": 78.2,
      "function": 92.0,
      "uncovered_files": ["src/utils/legacy.py"]
    },
    "quality_metrics": {
      "test_quality_score": 0.88,
      "flaky_tests": 1,
      "slow_tests": [
        {"name": "test_complex_calculation", "duration_ms": 5000}
      ]
    },
    "trends": {
      "coverage_change": "+2.5%",
      "test_count_change": "+10",
      "avg_duration_change": "-5s"
    }
  }
}
