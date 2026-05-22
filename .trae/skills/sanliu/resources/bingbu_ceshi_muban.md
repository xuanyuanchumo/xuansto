# 测试用例模板

## 单元测试用例模板

```python
import pytest
from module import function_to_test

class TestFunctionName:
    """测试 function_to_test 函数"""
    
    def test_normal_case(self):
        """测试正常输入场景"""
        # Arrange
        input_data = "normal_input"
        expected = "expected_output"
        
        # Act
        result = function_to_test(input_data)
        
        # Assert
        assert result == expected
    
    def test_edge_case_empty_input(self):
        """测试空输入边界条件"""
        # Arrange
        input_data = ""
        expected = None
        
        # Act
        result = function_to_test(input_data)
        
        # Assert
        assert result == expected
    
    def test_edge_case_max_input(self):
        """测试最大输入边界条件"""
        # Arrange
        input_data = "x" * 1000
        
        # Act & Assert
        with pytest.raises(ValueError):
            function_to_test(input_data)
    
    def test_invalid_input_type(self):
        """测试无效输入类型"""
        # Arrange
        input_data = 123  # 错误类型
        
        # Act & Assert
        with pytest.raises(TypeError):
            function_to_test(input_data)
    
    @pytest.mark.parametrize("input_data,expected", [
        ("case1", "result1"),
        ("case2", "result2"),
        ("case3", "result3"),
    ])
    def test_multiple_cases(self, input_data, expected):
        """参数化测试多个场景"""
        result = function_to_test(input_data)
        assert result == expected
```

## 集成测试用例模板

```python
import pytest
from module_a import ServiceA
from module_b import ServiceB
from database import Database

class TestServiceIntegration:
    """测试 ServiceA 和 ServiceB 的集成"""
    
    @pytest.fixture
    def setup_services(self):
        """设置测试环境"""
        db = Database(test_mode=True)
        service_a = ServiceA(db)
        service_b = ServiceB(db)
        yield service_a, service_b
        db.cleanup()
    
    def test_service_interaction(self, setup_services):
        """测试服务间正常交互"""
        service_a, service_b = setup_services
        
        # ServiceA 调用 ServiceB
        result_a = service_a.process("data")
        result_b = service_b.handle(result_a)
        
        assert result_b.status == "success"
    
    def test_database_transaction(self, setup_services):
        """测试数据库事务一致性"""
        service_a, service_b = setup_services
        
        # 执行事务操作
        service_a.create_record({"name": "test"})
        service_b.update_related("test")
        
        # 验证数据一致性
        records = service_a.query_all()
        assert len(records) == 1
```

## E2E测试用例模板

```python
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By

class TestUserFlow:
    """测试用户完整业务流程"""
    
    @pytest.fixture
    def browser(self):
        """设置浏览器"""
        driver = webdriver.Chrome()
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    def test_user_login_flow(self, browser):
        """测试用户登录流程"""
        # 访问登录页面
        browser.get("https://app.example.com/login")
        
        # 输入用户名密码
        browser.find_element(By.ID, "username").send_keys("testuser")
        browser.find_element(By.ID, "password").send_keys("password123")
        
        # 点击登录
        browser.find_element(By.ID, "login-btn").click()
        
        # 验证登录成功
        welcome = browser.find_element(By.CLASS_NAME, "welcome")
        assert "欢迎" in welcome.text
    
    def test_order_creation_flow(self, browser):
        """测试订单创建完整流程"""
        # 登录
        self.test_user_login_flow(browser)
        
        # 添加商品到购物车
        browser.get("https://app.example.com/products")
        browser.find_element(By.CLASS_NAME, "add-to-cart").click()
        
        # 结算
        browser.get("https://app.example.com/cart")
        browser.find_element(By.ID, "checkout-btn").click()
        
        # 确认订单
        browser.find_element(By.ID, "confirm-btn").click()
        
        # 验证订单创建成功
        success_msg = browser.find_element(By.CLASS_NAME, "success")
        assert "订单创建成功" in success_msg.text
```

## 测试用例文档模板

```markdown
# 测试用例文档

## 用例编号: TC-XXX-001

### 基本信息
- **用例名称**: 用户登录功能测试
- **所属模块**: 用户管理模块
- **优先级**: P1
- **测试类型**: 功能测试
- **编写人**: xxx
- **编写日期**: 2024-01-01

### 前置条件
1. 系统已部署
2. 测试用户已创建
3. 数据库连接正常

### 测试步骤

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 打开登录页面 | 页面正常显示 |
| 2 | 输入正确的用户名 | 输入框显示用户名 |
| 3 | 输入正确的密码 | 密码以密文显示 |
| 4 | 点击登录按钮 | 跳转到首页 |

### 测试数据
| 字段 | 值 | 说明 |
|------|-----|------|
| username | testuser | 有效用户名 |
| password | Pass@123 | 有效密码 |

### 预期结果
- 登录成功
- 跳转到首页
- 显示用户信息

### 实际结果
（测试执行时填写）

### 测试状态
- [ ] 通过
- [ ] 失败
- [ ] 阻塞

### 备注
其他需要说明的内容
```

## 测试覆盖率报告示例

```
File                    | % Stmts | % Branch | % Funcs | % Lines |
------------------------|---------|----------|---------|---------|
All files               |   85.23 |    78.45 |   90.12 |   84.56 |
 src/                   |   88.34 |    82.12 |   92.45 |   87.23 |
  service.js            |   92.15 |    88.34 |   95.67 |   91.23 |
  utils.js              |   78.45 |    65.23 |   85.12 |   76.89 |
 src/api/               |   82.12 |    75.34 |   88.23 |   81.45 |
  user.js               |   85.67 |    78.12 |   90.45 |   84.23 |
  order.js              |   78.45 |    72.34 |   86.12 |   78.67 |
------------------------|---------|----------|---------|---------|
```
