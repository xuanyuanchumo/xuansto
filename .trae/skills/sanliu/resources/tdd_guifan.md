# TDD编码规范

## 测试命名规范

### 单元测试命名

#### 命名格式
```
[被测试方法]_[测试场景]_[预期结果]
```

#### 示例
```python
# 好的命名
def test_calculate_discount_when_amount_over_1000_returns_10_percent():
    pass

def test_login_with_invalid_password_throws_exception():
    pass

def test_get_user_by_id_when_user_not_found_returns_none():
    pass

# 不好的命名
def test_login():
    pass

def test_case_1():
    pass

def test_something():
    pass
```

### 测试类命名

#### 命名规则
- 测试类名称以 `Test` 开头或以 `Tests` 结尾
- 测试类名称应清晰表达被测试的单元

#### 示例
```python
# 好的命名
class UserServiceTests:
    pass

class TestPaymentProcessor:
    pass

class OrderControllerTests:
    pass

# 不好的命名
class Test1:
    pass

class MyTests:
    pass
```

### 测试文件命名

#### 命名规则
- 测试文件名称应与被测试文件对应
- 使用 `_test.py` 或 `test_*.py` 后缀/前缀

#### 示例
```
被测试文件: user_service.py
测试文件:   user_service_test.py 或 test_user_service.py

被测试文件: payment_processor.py
测试文件:   payment_processor_test.py 或 test_payment_processor.py
```

---

## 测试组织结构规范

### AAA模式

每个测试方法应遵循 Arrange-Act-Assert 模式：

```python
def test_withdraw_money_when_balance_sufficient_reduces_balance():
    # Arrange (准备)
    account = Account(balance=1000)
    withdrawal_amount = 500
    
    # Act (执行)
    result = account.withdraw(withdrawal_amount)
    
    # Assert (断言)
    assert result == True
    assert account.balance == 500
```

### 测试类结构

```python
class UserServiceTests:
    """用户服务测试类"""
    
    # ===== 初始化测试 =====
    def test_init_with_valid_config_creates_instance(self):
        pass
    
    # ===== 核心功能测试 =====
    def test_create_user_with_valid_data_returns_user(self):
        pass
    
    def test_create_user_with_invalid_email_throws_exception(self):
        pass
    
    # ===== 边界条件测试 =====
    def test_create_user_with_empty_name_throws_exception(self):
        pass
    
    def test_create_user_with_duplicate_email_throws_exception(self):
        pass
    
    # ===== 辅助方法 =====
    def _create_valid_user_data(self):
        """创建有效的用户测试数据"""
        return {
            "name": "张三",
            "email": "zhangsan@example.com",
            "age": 25
        }
```

### 测试文件组织

```
tests/
├── unit/                    # 单元测试
│   ├── services/
│   │   ├── user_service_test.py
│   │   └── payment_service_test.py
│   ├── models/
│   │   └── user_test.py
│   └── utils/
│       └── date_utils_test.py
├── integration/             # 集成测试
│   └── api/
│       └── user_api_test.py
├── fixtures/                # 测试数据
│   └── user_fixtures.py
├── conftest.py              # pytest配置和共享fixtures
└── __init__.py
```

### 测试分组原则

| 分组类型 | 说明 | 示例 |
|---------|------|------|
| 正向测试 | 验证正常输入的预期行为 | 有效用户创建成功 |
| 负向测试 | 验证异常输入的处理 | 无效邮箱抛出异常 |
| 边界测试 | 验证边界值处理 | 空字符串、最大长度 |
| 状态测试 | 验证对象状态变化 | 余额更新正确 |

---

## 测试代码质量标准

### FIRST原则

| 原则 | 说明 | 示例 |
|-----|------|------|
| **F**ast | 测试应快速执行 | 避免真实数据库调用，使用内存数据库 |
| **I**ndependent | 测试之间相互独立 | 每个测试独立准备数据，不依赖执行顺序 |
| **R**epeatable | 测试结果可重复 | 相同输入产生相同输出，避免随机数据 |
| **S**elf-validating | 测试自动验证结果 | 使用断言，而非人工检查输出 |
| **T**imely | 测试及时编写 | 在编写生产代码前或同时编写测试 |

### 测试覆盖要求

#### 最低覆盖率标准
- 整体项目覆盖率: ≥ 80%
- 核心业务逻辑: ≥ 90%
- 工具类/辅助函数: ≥ 85%
- 配置类: ≥ 60%

#### 覆盖类型
```python
# 语句覆盖 - 每行代码至少执行一次
def test_statement_coverage():
    calculator = Calculator()
    result = calculator.add(1, 2)
    assert result == 3

# 分支覆盖 - 每个条件分支都执行
def test_branch_coverage_positive():
    result = calculate_grade(95)
    assert result == "A"

def test_branch_coverage_negative():
    result = calculate_grade(55)
    assert result == "F"

# 边界覆盖 - 测试边界值
def test_boundary_coverage():
    assert calculate_grade(90) == "A"
    assert calculate_grade(89) == "B"
    assert calculate_grade(60) == "D"
    assert calculate_grade(59) == "F"
```

### 断言规范

#### 使用明确的断言
```python
# 好的断言
assert user.name == "张三"
assert len(users) == 3
assert "错误" in exception.message

# 不好的断言
assert user  # 不够明确
assert users  # 不够明确
```

#### 断言消息
```python
# 关键断言添加消息
assert user.balance == 1000, f"余额应为1000，实际为{user.balance}"

assert len(orders) == 5, f"订单数量应为5，实际为{len(orders)}"
```

#### 异常断言
```python
import pytest

# 测试异常抛出
def test_withdraw_insufficient_balance_raises_exception():
    account = Account(balance=100)
    
    with pytest.raises(InsufficientBalanceException) as exc_info:
        account.withdraw(200)
    
    assert "余额不足" in str(exc_info.value)
```

### 测试隔离

#### 避免测试间依赖
```python
# 错误示例 - 测试间有依赖
class BadTests:
    saved_user_id = None
    
    def test_create_user(self):
        user = create_user("张三")
        BadTests.saved_user_id = user.id  # 污染类状态
    
    def test_get_user(self):
        user = get_user(BadTests.saved_user_id)  # 依赖上一个测试

# 正确示例 - 测试独立
class GoodTests:
    def test_create_user(self):
        user = create_user("张三")
        assert user.id is not None
    
    def test_get_user(self):
        # 独立准备测试数据
        user = create_user("李四")
        fetched = get_user(user.id)
        assert fetched.name == "李四"
```

#### 使用Fixture隔离
```python
import pytest

@pytest.fixture
def clean_database():
    """每个测试前清理数据库"""
    db.clear()
    yield
    db.clear()

@pytest.fixture
def sample_user():
    """提供测试用户数据"""
    return User(name="测试用户", email="test@example.com")

def test_user_creation(clean_database, sample_user):
    # 使用fixture提供的干净环境和数据
    pass
```

### Mock使用规范

#### 何时使用Mock
- 外部服务调用（API、数据库）
- 时间相关操作
- 文件系统操作
- 昂贵的资源操作

#### Mock示例
```python
from unittest.mock import Mock, patch

# Mock外部服务
def test_send_notification():
    mock_email_service = Mock()
    mock_email_service.send.return_value = True
    
    notification = NotificationService(mock_email_service)
    result = notification.notify("test@example.com", "消息内容")
    
    assert result == True
    mock_email_service.send.assert_called_once_with(
        "test@example.com", 
        "消息内容"
    )

# 使用patch装饰器
@patch('module.external_api')
def test_with_patched_api(mock_api):
    mock_api.get_data.return_value = {"status": "ok"}
    
    result = process_data()
    
    assert result == "processed"
```

### 测试代码可读性

#### 避免魔法数字
```python
# 不好的示例
def test_discount():
    price = calculate_price(1000, 0.1)
    assert price == 900

# 好的示例
def test_discount():
    original_price = 1000
    discount_rate = 0.1  # 10%折扣
    expected_price = 900
    
    actual_price = calculate_price(original_price, discount_rate)
    
    assert actual_price == expected_price
```

#### 使用有意义的测试数据
```python
# 不好的示例
def test_user_age_validation():
    validate_age(25)  # 魔法数字

# 好的示例
def test_user_age_validation():
    VALID_AGE = 25
    MIN_AGE = 18
    MAX_AGE = 120
    
    validate_age(VALID_AGE)
    validate_age(MIN_AGE)
    validate_age(MAX_AGE)
```

### 测试维护原则

1. **测试代码与生产代码同等重要**
   - 遵循相同的编码规范
   - 定期重构测试代码
   - 保持测试代码整洁

2. **测试失败时的处理**
   - 测试失败应提供清晰的错误信息
   - 错误信息应包含预期值和实际值
   - 错误信息应便于定位问题

3. **持续维护**
   - 删除过时的测试
   - 更新因需求变更而失效的测试
   - 避免禁用测试（使用skip并说明原因）

```python
import pytest

# 临时跳过测试的正确方式
@pytest.mark.skip(reason="等待API接口更新后恢复")
def test_new_api_feature():
    pass
```
