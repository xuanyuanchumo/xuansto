# TDD 最佳实践指南

## 概述

测试驱动开发（Test-Driven Development，TDD）是一种软件开发方法，通过先编写测试再编写代码的方式，确保代码质量和可维护性。本文档提供红-绿-重构循环的执行指南、常见问题解决方案和测试覆盖率最佳实践。

## 红-绿-重构执行指南

### TDD循环概述

```
┌─────────────────────────────────────────────────────────────────┐
│                    TDD 循环流程                                  │
│                                                                  │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐                │
│   │  红 🔴   │───▶│  绿 🟢   │───▶│ 重构 🔵  │──┐             │
│   │ 编写失败 │    │ 编写通过 │    │ 优化代码 │  │             │
│   │ 的测试   │    │ 的代码   │    │ 保持通过 │  │             │
│   └──────────┘    └──────────┘    └──────────┘  │             │
│        ▲                                          │             │
│        └──────────────────────────────────────────┘             │
│                                                                  │
│   兵部负责红 🔴  →  工部负责绿 🟢  →  刑部负责重构 🔵           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 红色阶段：编写失败的测试

#### 详细步骤

**步骤1：理解需求**
1. 分析功能需求，明确预期行为
2. 识别边界条件和异常情况
3. 确定测试覆盖范围

**步骤2：编写测试用例**
1. 遵循 AAA 模式（Arrange-Act-Assert）
2. 使用清晰的命名规范
3. 确保测试独立性

**步骤3：运行测试确认失败**
1. 执行测试，确认测试失败
2. 验证失败原因符合预期
3. 确保错误信息清晰明确

#### 示例：用户注册功能测试

```python
# tests/unit/test_user.py

def test_create_user_with_valid_data_returns_user():
    """测试：使用有效数据创建用户应返回用户对象"""
    
    # Arrange (准备)
    user_data = {
        "username": "zhangsan",
        "email": "zhangsan@example.com",
        "password": "SecurePass123!"
    }
    user_service = UserService()
    
    # Act (执行)
    user = user_service.create_user(user_data)
    
    # Assert (断言)
    assert user is not None
    assert user.username == "zhangsan"
    assert user.email == "zhangsan@example.com"
    assert user.password != "SecurePass123!"  # 密码应加密


def test_create_user_with_duplicate_email_raises_exception():
    """测试：使用重复邮箱创建用户应抛出异常"""
    
    # Arrange
    user_service = UserService()
    user_service.create_user({
        "username": "user1",
        "email": "same@example.com",
        "password": "Pass123!"
    })
    
    # Act & Assert
    with pytest.raises(DuplicateEmailException) as exc_info:
        user_service.create_user({
            "username": "user2",
            "email": "same@example.com",
            "password": "Pass456!"
        })
    
    assert "邮箱已被注册" in str(exc_info.value)
```

### 绿色阶段：编写通过的代码

#### 详细步骤

**步骤1：编写最小实现**
1. 只编写使测试通过的最少代码
2. 不要过度设计或添加额外功能
3. 保持代码简单直接

**步骤2：运行测试确认通过**
1. 执行测试，确认测试通过
2. 检查是否有副作用
3. 确保没有破坏现有测试

**步骤3：提交代码**
1. 确认所有测试通过
2. 提交代码到版本控制
3. 记录实现决策

#### 示例：用户注册功能实现

```python
# src/services/user_service.py

from werkzeug.security import generate_password_hash
from exceptions import DuplicateEmailException

class UserService:
    def __init__(self, db_session):
        self.db_session = db_session
    
    def create_user(self, user_data):
        """创建新用户"""
        
        # 检查邮箱是否已存在
        existing_user = self.db_session.query(User).filter_by(
            email=user_data["email"]
        ).first()
        
        if existing_user:
            raise DuplicateEmailException("邮箱已被注册")
        
        # 创建用户
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            password=generate_password_hash(user_data["password"])
        )
        
        self.db_session.add(user)
        self.db_session.commit()
        
        return user
```

### 重构阶段：优化代码质量

#### 详细步骤

**步骤1：识别代码异味**
1. 检查重复代码
2. 识别过长方法
3. 发现复杂条件逻辑

**步骤2：小步重构**
1. 每次只做一个小的改动
2. 改动后立即运行测试
3. 测试通过则保留，失败则回滚

**步骤3：验证重构效果**
1. 确认所有测试仍然通过
2. 验证代码可读性提升
3. 检查性能是否改善

#### 示例：用户注册功能重构

```python
# src/services/user_service.py (重构后)

from werkzeug.security import generate_password_hash
from exceptions import DuplicateEmailException

class UserService:
    """用户服务类"""
    
    def __init__(self, db_session):
        self.db_session = db_session
    
    def create_user(self, user_data):
        """创建新用户"""
        self._validate_email_uniqueness(user_data["email"])
        
        user = self._build_user(user_data)
        self._save_user(user)
        
        return user
    
    def _validate_email_uniqueness(self, email):
        """验证邮箱唯一性"""
        if self._email_exists(email):
            raise DuplicateEmailException("邮箱已被注册")
    
    def _email_exists(self, email):
        """检查邮箱是否已存在"""
        return self.db_session.query(User).filter_by(
            email=email
        ).first() is not None
    
    def _build_user(self, user_data):
        """构建用户对象"""
        return User(
            username=user_data["username"],
            email=user_data["email"],
            password=self._hash_password(user_data["password"])
        )
    
    def _hash_password(self, password):
        """加密密码"""
        return generate_password_hash(password)
    
    def _save_user(self, user):
        """保存用户到数据库"""
        self.db_session.add(user)
        self.db_session.commit()
```

### TDD循环时间控制

| 阶段 | 建议时间 | 最大时间 | 说明 |
|------|----------|----------|------|
| 红 🔴 | 5-10分钟 | 15分钟 | 编写一个测试用例 |
| 绿 🟢 | 5-15分钟 | 30分钟 | 实现最小可行代码 |
| 重构 🔵 | 5-10分钟 | 20分钟 | 优化代码结构 |

**注意**：如果一个循环超过上述时间，说明任务粒度太大，需要进一步拆分。

## 常见问题和解决方案

### 问题1：测试难以编写

#### 症状
- 不知道如何开始编写测试
- 测试代码比生产代码还复杂
- 测试经常因为外部依赖失败

#### 解决方案

**方案1：使用测试替身（Test Double）**

```python
from unittest.mock import Mock, patch

# 使用 Mock 隔离外部依赖
def test_send_welcome_email():
    # Arrange
    mock_email_service = Mock()
    mock_email_service.send.return_value = True
    
    user_service = UserService(email_service=mock_email_service)
    user = User(email="test@example.com")
    
    # Act
    result = user_service.send_welcome_email(user)
    
    # Assert
    assert result is True
    mock_email_service.send.assert_called_once_with(
        to="test@example.com",
        subject="欢迎加入",
        body=any(str)  # 使用 any 匹配任意内容
    )
```

**方案2：使用 Fixture 简化测试数据**

```python
import pytest

@pytest.fixture
def sample_user():
    """提供测试用户数据"""
    return User(
        id=1,
        username="testuser",
        email="test@example.com"
    )

@pytest.fixture
def user_service():
    """提供用户服务实例"""
    return UserService(db_session=Mock())

def test_get_user_by_id(user_service, sample_user):
    """测试：根据ID获取用户"""
    # 使用 fixture 提供的测试数据
    user_service.db_session.query.return_value.filter_by.return_value.first.return_value = sample_user
    
    result = user_service.get_user_by_id(1)
    
    assert result.username == "testuser"
```

### 问题2：测试运行太慢

#### 症状
- 测试套件运行时间超过5分钟
- 开发者不愿意频繁运行测试
- CI/CD 流水线经常超时

#### 解决方案

**方案1：分类测试**

```python
import pytest

# 标记测试类型
@pytest.mark.unit
def test_password_hashing():
    """单元测试：密码加密"""
    pass

@pytest.mark.integration
def test_user_database_operations():
    """集成测试：数据库操作"""
    pass

@pytest.mark.e2e
def test_user_registration_flow():
    """端到端测试：用户注册流程"""
    pass

# 运行特定类型的测试
# pytest -m unit          # 只运行单元测试
# pytest -m "not e2e"     # 跳过E2E测试
```

**方案2：使用内存数据库**

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def in_memory_db():
    """使用内存数据库加速测试"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()
```

**方案3：并行执行测试**

```bash
# 安装 pytest-xdist
pip install pytest-xdist

# 并行运行测试
pytest -n auto  # 自动检测CPU核心数
pytest -n 4     # 使用4个进程
```

### 问题3：测试脆弱易碎

#### 症状
- 测试偶尔失败，重试又通过
- 修改无关代码导致测试失败
- 测试结果依赖执行顺序

#### 解决方案

**方案1：确保测试隔离**

```python
# 错误示例：测试间有依赖
class BadTests:
    saved_user_id = None
    
    def test_create_user(self):
        user = create_user("张三")
        BadTests.saved_user_id = user.id  # 污染类状态
    
    def test_get_user(self):
        user = get_user(BadTests.saved_user_id)  # 依赖上一个测试

# 正确示例：测试独立
class GoodTests:
    def test_create_user(self):
        user = create_user("张三")
        assert user.id is not None
    
    def test_get_user(self):
        user = create_user("李四")  # 独立准备测试数据
        fetched = get_user(user.id)
        assert fetched.name == "李四"
```

**方案2：避免使用固定时间**

```python
from datetime import datetime
from unittest.mock import patch

# 错误示例：使用固定时间
def test_order_creation_bad():
    order = create_order()
    assert order.created_at == datetime(2024, 1, 1, 12, 0, 0)  # 脆弱

# 正确示例：使用 Mock 时间
def test_order_creation_good():
    fixed_time = datetime(2024, 1, 1, 12, 0, 0)
    
    with patch('module.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_time
        
        order = create_order()
        assert order.created_at == fixed_time
```

**方案3：使用参数化测试**

```python
@pytest.mark.parametrize("input,expected", [
    ("admin", True),
    ("user", False),
    ("guest", False),
    ("", False),
])
def test_is_admin(input, expected):
    """参数化测试：检查管理员权限"""
    user = User(role=input)
    assert user.is_admin() == expected
```

### 问题4：测试覆盖不足

#### 症状
- 测试通过但生产环境出bug
- 边界条件未覆盖
- 异常路径未测试

#### 解决方案

**方案1：使用覆盖率工具**

```bash
# 生成覆盖率报告
pytest --cov=src --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

**方案2：边界值测试**

```python
@pytest.mark.parametrize("age,valid", [
    (0, False),      # 边界：最小值
    (1, True),       # 边界：最小有效值
    (17, True),      # 边界：接近成年
    (18, True),      # 边界：成年
    (120, True),     # 边界：最大合理值
    (121, False),    # 边界：超出合理范围
    (-1, False),     # 异常：负数
])
def test_validate_age(age, valid):
    """测试年龄验证边界值"""
    assert validate_age(age) == valid
```

**方案3：异常路径测试**

```python
def test_withdraw_insufficient_balance():
    """测试：余额不足时取款应抛出异常"""
    account = Account(balance=100)
    
    with pytest.raises(InsufficientBalanceException) as exc_info:
        account.withdraw(200)
    
    assert "余额不足" in str(exc_info.value)
    assert account.balance == 100  # 余额不应改变
```

## 测试覆盖率最佳实践

### 覆盖率目标

| 代码类型 | 最低覆盖率 | 推荐覆盖率 | 说明 |
|----------|------------|------------|------|
| 核心业务逻辑 | 90% | 95% | 关键功能必须充分测试 |
| 工具类/辅助函数 | 85% | 90% | 工具函数应全面覆盖 |
| API接口 | 80% | 85% | 包含正常和异常路径 |
| 配置类 | 60% | 70% | 配置代码可适当降低 |
| 整体项目 | 80% | 85% | 项目整体覆盖率目标 |

### 覆盖率类型

#### 1. 语句覆盖（Statement Coverage）

```python
# 被测代码
def calculate_discount(price, is_member):
    if is_member:
        return price * 0.9
    return price

# 测试用例
def test_calculate_discount():
    assert calculate_discount(100, True) == 90   # 覆盖 if 分支
    assert calculate_discount(100, False) == 100 # 覆盖 else 分支
```

#### 2. 分支覆盖（Branch Coverage）

```python
# 被测代码
def get_grade(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 60:
        return "C"
    else:
        return "F"

# 测试用例（覆盖所有分支）
@pytest.mark.parametrize("score,grade", [
    (95, "A"),  # score >= 90
    (85, "B"),  # 80 <= score < 90
    (65, "C"),  # 60 <= score < 80
    (55, "F"),  # score < 60
])
def test_get_grade(score, grade):
    assert get_grade(score) == grade
```

#### 3. 路径覆盖（Path Coverage）

```python
# 被测代码
def validate_user(username, age):
    errors = []
    
    if not username:
        errors.append("用户名不能为空")
    
    if age < 0 or age > 120:
        errors.append("年龄无效")
    
    return errors

# 测试用例（覆盖所有路径）
def test_validate_user_all_paths():
    # 路径1：两个条件都为真
    assert validate_user("", -1) == ["用户名不能为空", "年龄无效"]
    
    # 路径2：第一个条件为真，第二个为假
    assert validate_user("", 25) == ["用户名不能为空"]
    
    # 路径3：第一个条件为假，第二个为真
    assert validate_user("user", 150) == ["年龄无效"]
    
    # 路径4：两个条件都为假
    assert validate_user("user", 25) == []
```

### 覆盖率配置

#### pytest 配置

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# 覆盖率配置
addopts = 
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80
```

#### 覆盖率排除配置

```python
# .coveragerc
[run]
source = src
omit =
    */tests/*
    */migrations/*
    */__init__.py
    */config.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

### 覆盖率报告分析

#### 生成覆盖率报告

```bash
# 生成终端报告
pytest --cov=src --cov-report=term-missing

# 生成HTML报告
pytest --cov=src --cov-report=html

# 生成XML报告（用于CI）
pytest --cov=src --cov-report=xml
```

#### 报告解读

```
Name                           Stmts   Miss  Cover   Missing
------------------------------------------------------------
src/services/user_service.py      45      5    89%   23-27
src/models/user.py                30      0   100%
src/utils/validators.py           20      8    60%   15-22
------------------------------------------------------------
TOTAL                            95     13    86%
```

**关键指标**：
- **Stmts**：语句总数
- **Miss**：未覆盖的语句数
- **Cover**：覆盖率百分比
- **Missing**：未覆盖的行号

### 提高覆盖率的策略

#### 策略1：识别未覆盖代码

```bash
# 查看未覆盖的具体行
pytest --cov=src --cov-report=term-missing | grep "Miss"
```

#### 策略2：针对性补充测试

```python
# 假设第23-27行未覆盖
# src/services/user_service.py:23-27
def delete_user(self, user_id):
    user = self.get_user_by_id(user_id)
    if not user:
        raise UserNotFoundException("用户不存在")
    self.db_session.delete(user)
    self.db_session.commit()

# 补充测试
def test_delete_nonexistent_user_raises_exception():
    """测试：删除不存在的用户应抛出异常"""
    user_service = UserService(db_session=Mock())
    user_service.get_user_by_id = Mock(return_value=None)
    
    with pytest.raises(UserNotFoundException):
        user_service.delete_user(999)
```

#### 策略3：持续监控覆盖率

```yaml
# .github/workflows/coverage.yml
name: Coverage Check

on: [push, pull_request]

jobs:
  coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run tests with coverage
        run: |
          pip install pytest pytest-cov
          pytest --cov=src --cov-fail-under=80 --cov-report=xml
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## 与三省六部协作

### TDD协作矩阵

| 阶段 | 主责部门 | 协作部门 | 产出物 |
|------|----------|----------|--------|
| 红 🔴 | 兵部 | 中书省 | 失败的测试用例 |
| 绿 🟢 | 工部 | 刑部 | 通过的功能代码 |
| 重构 🔵 | 刑部 | 兵部 | 优化的代码 |
| 覆盖率验证 | 兵部 | 门下省 | 覆盖率报告 |

### TDD流程协作

```
┌─────────────────────────────────────────────────────────────────┐
│                    TDD三省六部协作流程                            │
│                                                                  │
│   中书省 ────────────────────────────────────────────────────── │
│   │  └─ 需求确认：明确功能需求和验收标准                          │
│   │                                                              │
│   门下省 ────────────────────────────────────────────────────── │
│   │  └─ 测试评审：评审测试用例覆盖率和合理性                       │
│   │                                                              │
│   尚书省 ────────────────────────────────────────────────────── │
│   │  └─ 流程协调：确保TDD循环顺畅执行                              │
│   │                                                              │
│   六部 ──────────────────────────────────────────────────────── │
│   │  ├─ 兵部：编写测试用例（红 🔴）                                │
│   │  ├─ 工部：实现功能代码（绿 🟢）                                │
│   │  ├─ 刑部：重构优化代码（蓝 🔵）                                │
│   │  ├─ 吏部：分配TDD角色                                         │
│   │  ├─ 户部：提供测试环境资源                                    │
│   │  └─ 礼部：提供测试规范模板                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 输出物清单

- [ ] 测试用例文档
- [ ] 测试覆盖率报告
- [ ] 重构记录文档
- [ ] TDD循环时间统计
- [ ] 测试问题追踪表

---

## v2.4.0 新增最佳实践

### 智能测试选择器使用

v2.4.0 新增智能测试选择器，根据代码变更自动选择相关测试用例：

```bash
# 智能选择测试用例
python skillscripts/pipeline/intelligent_test_selector.py \
  --changed-files "src/user_service.py,src/auth_service.py" \
  --output selected_tests.txt

# 带覆盖率预测的测试选择
python skillscripts/pipeline/intelligent_test_selector.py \
  --changed-files "src/" \
  --predict-coverage \
  --min-coverage 0.8
```

### 测试失败诊断增强

新增测试失败诊断工具，自动分析失败原因：

```bash
# 诊断测试失败
python skillscripts/test/test_failure_diagnostician.py \
  --test-results test_results.json \
  --output diagnosis_report.md

# 失败模式学习
python skillscripts/test/failure_pattern_learner.py \
  --history-dir logs/test_history \
  --output patterns.json
```

### UI验证智能模块

新增UI验证智能模块，支持前端UI自动化验证：

```bash
# UI验证测试
python skillscripts/test/ui_validation_intelligence.py \
  --component "UserRegistration" \
  --screenshots-dir ./screenshots

# 视觉回归测试
python skillscripts/test/ui_validation_intelligence.py \
  --visual-regression \
  --baseline-dir ./baselines
```

### TDD蓝阶段重构流水线

优化TDD蓝阶段重构流水线：

```bash
# 执行重构流水线
python skillscripts/pipeline/tdd_blue_refactoring_pipeline.py \
  --source-dir src/ \
  --test-dir tests/ \
  --report-dir reports/

# 重构建议生成
python skillscripts/optimization/refactoring_suggestion_generator.py \
  --code-path src/ \
  --output suggestions.md
```

### 测试意图分析

新增测试意图分析器，理解测试用例的真实意图：

```bash
# 分析测试意图
python skillscripts/test/test_intent_analyzer.py \
  --test-file tests/test_user.py \
  --output intent_analysis.json
```

### 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0 | 2024-01-01 | 初始版本 |
| 2.0 | 2026-03-30 | 新增智能测试选择器、测试失败诊断、UI验证智能模块、TDD蓝阶段重构流水线、测试意图分析 |
