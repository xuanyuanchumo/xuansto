# Karpathy Guidelines 参考文档

> 版本: 1.0.0 | 更新日期: 2026-04-17 | 编码: UTF-8 | 行尾: LF

---

## 概述

Karpathy Guidelines 源自 Andrej Karpathy (前Tesla AI总监、OpenAI创始成员) 的软件开发经验总结。这些准则强调代码质量、开发效率和工程实践，特别适用于AI辅助开发场景。

---

## 目录

1. [准则一：代码即文档](#准则一代码即文档)
2. [准则二：简单优于复杂](#准则二简单优于复杂)
3. [准则三：测试驱动思考](#准则三测试驱动思考)
4. [准则四：迭代式开发](#准则四迭代式开发)

---

## 准则一：代码即文档

### 核心原则

> "最好的文档是自解释的代码。当代码需要大量注释来解释时，通常意味着代码本身需要重构。"

### 详细说明

代码应该具有自解释性，通过清晰的命名、合理的结构和良好的组织来传达意图，而非依赖大量注释。

### 实践指南

#### 1. 命名即文档

```python
# ❌ 不好的实践: 需要注释解释
def calc(d):
    # d是日期列表，计算平均值
    return sum(d) / len(d)

# ✅ 好的实践: 命名自解释
def calculate_average_daily_temperature(daily_temperatures: list[float]) -> float:
    return sum(daily_temperatures) / len(daily_temperatures)
```

#### 2. 结构即文档

```python
# ❌ 不好的实践: 扁平化结构
def process_order(order):
    # 验证订单
    if not order.items:
        return False
    if order.total < 0:
        return False
    # 计算折扣
    discount = 0
    if order.customer.vip:
        discount = order.total * 0.1
    # 更新库存
    for item in order.items:
        item.product.stock -= item.quantity
    # 发送通知
    send_email(order.customer.email, "订单已处理")
    return True

# ✅ 好的实践: 结构化分解
def process_order(order: Order) -> OrderResult:
    if not validate_order(order):
        return OrderResult.INVALID
    
    apply_discounts(order)
    update_inventory(order)
    notify_customer(order)
    
    return OrderResult.SUCCESS

def validate_order(order: Order) -> bool:
    return bool(order.items) and order.total >= 0

def apply_discounts(order: Order) -> None:
    if order.customer.is_vip:
        order.discount = order.subtotal * VIP_DISCOUNT_RATE

def update_inventory(order: Order) -> None:
    for item in order.items:
        item.product.decrease_stock(item.quantity)

def notify_customer(order: Order) -> None:
    send_order_confirmation(order.customer.email, order.id)
```

#### 3. 类型即文档

```python
# ❌ 不好的实践: 缺乏类型信息
def get_user(id):
    return db.query(f"SELECT * FROM users WHERE id = {id}")

# ✅ 好的实践: 类型作为文档
from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: int
    name: str
    email: str
    is_active: bool

def get_user_by_id(user_id: int) -> Optional[User]:
    """根据ID获取用户，不存在则返回None"""
    return db.query_one("SELECT * FROM users WHERE id = ?", [user_id])
```

#### 4. 注释的使用原则

```python
# ✅ 适当的注释: 解释"为什么"
def calculate_compound_interest(principal: float, rate: float, years: int) -> float:
    # 使用连续复利公式，因为这是银行标准计算方式
    return principal * math.exp(rate * years)

# ✅ 适当的注释: 解释非显而易见的决策
def process_payment(amount: float) -> PaymentResult:
    # 使用分而非元来避免浮点精度问题
    amount_cents = int(amount * 100)
    return payment_gateway.charge(amount_cents)

# ✅ 适当的注释: TODO和FIXME
# TODO: 添加缓存机制以提升性能
# FIXME: 当前实现在大数据集下存在内存问题
```

### 检查清单

- [ ] 变量和函数名称是否清晰表达意图
- [ ] 是否需要注释来解释代码做什么
- [ ] 类型注解是否完整
- [ ] 代码结构是否反映业务逻辑
- [ ] 注释是否解释"为什么"而非"做什么"

---

## 准则二：简单优于复杂

### 核心原则

> "简单的代码更容易理解、维护和调试。复杂性是软件质量的最大敌人。"

### 详细说明

在满足需求的前提下，选择最简单的解决方案。避免过度工程化，保持代码的最小复杂度。

### 实践指南

#### 1. 避免过度抽象

```python
# ❌ 过度抽象: 不必要的工厂模式
class UserFactory:
    @staticmethod
    def create_user(type: str, data: dict) -> User:
        if type == "admin":
            return AdminUser(data)
        elif type == "regular":
            return RegularUser(data)
        elif type == "guest":
            return GuestUser(data)
        else:
            raise ValueError(f"Unknown user type: {type}")

# ✅ 简单直接: 只在需要时抽象
def create_user(role: str, data: dict) -> User:
    return User(role=role, **data)
```

#### 2. 选择最简单的数据结构

```python
# ❌ 过度设计: 使用复杂类
class UserCollection:
    def __init__(self):
        self._users = []
        self._by_id = {}
        self._by_email = {}
    
    def add(self, user):
        self._users.append(user)
        self._by_id[user.id] = user
        self._by_email[user.email] = user
    
    def find_by_id(self, id):
        return self._by_id.get(id)
    
    def find_by_email(self, email):
        return self._by_email.get(email)

# ✅ 简单设计: 使用内置数据结构
users_by_id: dict[int, User] = {}
users_by_email: dict[str, User] = {}

def add_user(user: User) -> None:
    users_by_id[user.id] = user
    users_by_email[user.email] = user
```

#### 3. 避免过早优化

```python
# ❌ 过早优化: 复杂的缓存机制
class CachedDataProcessor:
    def __init__(self):
        self._cache = LRUCache(maxsize=1000)
        self._lock = threading.Lock()
        self._stats = CacheStats()
    
    def process(self, data: str) -> Result:
        cache_key = hashlib.md5(data.encode()).hexdigest()
        
        with self._lock:
            if cache_key in self._cache:
                self._stats.hits += 1
                return self._cache[cache_key]
        
        result = self._compute(data)
        
        with self._lock:
            self._cache[cache_key] = result
            self._stats.misses += 1
        
        return result

# ✅ 简单优先: 先实现，后优化
def process_data(data: str) -> Result:
    return compute_result(data)

# 只有在确认性能问题后才添加缓存
@lru_cache(maxsize=1000)
def process_data(data: str) -> Result:
    return compute_result(data)
```

#### 4. 减少嵌套层次

```python
# ❌ 深层嵌套
def process_order(order):
    if order:
        if order.items:
            if order.customer:
                if order.customer.is_active:
                    for item in order.items:
                        if item.product:
                            if item.product.in_stock:
                                process_item(item)

# ✅ 早返回减少嵌套
def process_order(order: Optional[Order]) -> None:
    if not order:
        return
    if not order.items:
        return
    if not order.customer or not order.customer.is_active:
        return
    
    for item in order.items:
        if item.product and item.product.in_stock:
            process_item(item)
```

#### 5. 单一职责

```python
# ❌ 多重职责
class UserManager:
    def create_user(self, data): pass
    def send_email(self, user): pass
    def generate_report(self): pass
    def backup_database(self): pass

# ✅ 单一职责
class UserRepository:
    def create(self, data: UserData) -> User: pass
    def find_by_id(self, id: int) -> Optional[User]: pass
    def update(self, user: User) -> None: pass

class EmailService:
    def send_welcome_email(self, user: User) -> None: pass

class ReportGenerator:
    def generate_user_report(self) -> Report: pass
```

### 复杂度度量

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 函数长度 | ≤50行 | 超过则考虑拆分 |
| 嵌套深度 | ≤3层 | 超过则使用早返回 |
| 参数数量 | ≤4个 | 超过则使用对象封装 |
| 圈复杂度 | ≤10 | 分支过多则拆分 |

### 检查清单

- [ ] 是否存在不必要的抽象
- [ ] 是否使用了最简单的数据结构
- [ ] 是否在解决真实问题而非假想问题
- [ ] 嵌套层次是否过深
- [ ] 每个函数是否只做一件事

---

## 准则三：测试驱动思考

### 核心原则

> "测试不仅是验证工具，更是设计工具。编写测试帮助你思考代码应该如何工作。"

### 详细说明

在编写代码之前思考如何测试它，这会引导你设计出更模块化、更可测试、更健壮的代码。

### 实践指南

#### 1. 测试先行思考

```python
# 在编写函数之前，先思考如何测试
# 问题: 如何验证这个函数的正确性？

# 需求: 计算购物车总价
# 测试场景:
# 1. 空购物车返回0
# 2. 单个商品返回正确价格
# 3. 多个商品返回总价
# 4. 有折扣时正确计算
# 5. 负数量应抛出异常

def calculate_cart_total(cart: Cart, discount: float = 0.0) -> float:
    if not cart.items:
        return 0.0
    
    subtotal = sum(
        item.price * item.quantity 
        for item in cart.items
        if item.quantity > 0
    )
    
    return subtotal * (1 - discount)
```

#### 2. 边界条件思考

```python
# 测试驱动你考虑边界条件
def divide(a: float, b: float) -> float:
    # 测试场景: b=0时会发生什么？
    if b == 0:
        raise ValueError("Division by zero")
    return a / b

def get_first_element(items: list[T]) -> Optional[T]:
    # 测试场景: 空列表时会发生什么？
    return items[0] if items else None

def parse_age(age_str: str) -> int:
    # 测试场景: 非数字、负数、过大值？
    try:
        age = int(age_str)
        if age < 0:
            raise ValueError("Age cannot be negative")
        if age > 150:
            raise ValueError("Age seems unrealistic")
        return age
    except ValueError as e:
        raise ValueError(f"Invalid age: {age_str}") from e
```

#### 3. 依赖注入提高可测试性

```python
# ❌ 难以测试: 硬编码依赖
class OrderProcessor:
    def process(self, order: Order) -> None:
        # 直接调用数据库，难以mock
        db.save(order)
        # 直接发送邮件，难以测试
        email.send(order.customer.email, "Order confirmed")

# ✅ 易于测试: 依赖注入
class OrderProcessor:
    def __init__(
        self, 
        repository: OrderRepository,
        notifier: Notifier
    ):
        self.repository = repository
        self.notifier = notifier
    
    def process(self, order: Order) -> None:
        self.repository.save(order)
        self.notifier.notify(order.customer, "Order confirmed")

# 测试
def test_order_processor():
    mock_repo = Mock(OrderRepository)
    mock_notifier = Mock(Notifier)
    
    processor = OrderProcessor(mock_repo, mock_notifier)
    order = Order(id=1, customer=Customer(email="test@example.com"))
    
    processor.process(order)
    
    mock_repo.save.assert_called_once_with(order)
    mock_notifier.notify.assert_called_once()
```

#### 4. 测试命名即文档

```python
# ❌ 不好的测试命名
def test_1():
    assert add(1, 2) == 3

def test_2():
    assert add(-1, -1) == -2

# ✅ 好的测试命名: 描述行为
def test_should_return_sum_when_adding_two_positive_numbers():
    assert add(1, 2) == 3

def test_should_return_negative_sum_when_adding_two_negative_numbers():
    assert add(-1, -1) == -2

def test_should_return_zero_when_adding_opposite_numbers():
    assert add(5, -5) == 0

# 或使用中文命名
def test_应当返回正确和值_当两个正数相加():
    assert add(1, 2) == 3
```

#### 5. 测试金字塔

```
                    /\
                   /  \
                  / E2E\        端到端测试 (慢，少)
                 /------\
                /        \
               /Integration\   集成测试 (中速，适量)
              /------------\
             /              \
            /   Unit Tests   \  单元测试 (快，多)
           /------------------\
```

```python
# 单元测试: 测试单个函数
def test_calculate_discount():
    customer = Customer(is_vip=True)
    order = Order(subtotal=100.0)
    
    discount = calculate_discount(customer, order)
    
    assert discount == 10.0  # VIP 10% discount

# 集成测试: 测试组件协作
def test_order_persistence():
    repo = SqlOrderRepository(test_db)
    order = Order(id=1, total=100.0)
    
    repo.save(order)
    found = repo.find_by_id(1)
    
    assert found.total == 100.0

# E2E测试: 测试完整流程
def test_complete_order_flow():
    # 使用真实数据库和外部服务
    response = client.post("/api/orders", json={
        "items": [{"product_id": 1, "quantity": 2}]
    })
    
    assert response.status_code == 201
    assert response.json()["status"] == "created"
```

### 检查清单

- [ ] 是否在编码前思考测试场景
- [ ] 是否考虑了所有边界条件
- [ ] 代码是否易于测试(依赖注入)
- [ ] 测试命名是否清晰描述行为
- [ ] 是否遵循测试金字塔原则

---

## 准则四：迭代式开发

### 核心原则

> "先让它工作，再让它正确，最后让它快。过早优化是万恶之源。"

### 详细说明

通过小步迭代逐步完善代码，每个迭代都产生可工作的代码。避免一次性编写完整系统。

### 实践指南

#### 1. 迭代开发流程

```
迭代1: 最小可行实现
   ↓
迭代2: 添加错误处理
   ↓
迭代3: 优化性能
   ↓
迭代4: 重构改进
   ↓
迭代N: 持续优化
```

#### 2. 迭代示例: 用户认证

```python
# 迭代1: 最小可行实现 - 让它工作
def authenticate(username: str, password: str) -> bool:
    user = db.find_user(username)
    return user and user.password == password

# 迭代2: 安全性改进 - 让它正确
import bcrypt

def authenticate(username: str, password: str) -> Optional[User]:
    user = db.find_user(username)
    if not user:
        return None
    
    if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        return None
    
    return user

# 迭代3: 添加限流 - 让它安全
from functools import lru_cache
from datetime import datetime, timedelta

login_attempts: dict[str, list[datetime]] = {}

def authenticate(username: str, password: str) -> Optional[User]:
    # 检查登录尝试次数
    attempts = login_attempts.get(username, [])
    recent = [a for a in attempts if a > datetime.now() - timedelta(minutes=15)]
    
    if len(recent) >= 5:
        raise AccountLockedError("Too many failed attempts")
    
    user = db.find_user(username)
    if not user or not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        login_attempts[username] = recent + [datetime.now()]
        return None
    
    # 清除失败记录
    login_attempts.pop(username, None)
    return user

# 迭代4: 性能优化 - 让它快
@lru_cache(maxsize=1000)
def get_user_permissions(user_id: int) -> set[str]:
    return db.get_permissions(user_id)

def authenticate(username: str, password: str) -> AuthResult:
    # ... 认证逻辑 ...
    
    # 预加载权限
    permissions = get_user_permissions(user.id)
    
    return AuthResult(user=user, permissions=permissions)
```

#### 3. 小步提交

```bash
# 每个迭代一个提交
git commit -m "feat(auth): 基本认证功能"
git commit -m "feat(auth): 添加密码哈希"
git commit -m "feat(auth): 添加登录限流"
git commit -m "perf(auth): 添加权限缓存"
```

#### 4. 持续重构

```python
# 重构时机:
# 1. 添加新功能前
# 2. 发现重复代码时
# 3. 代码难以理解时
# 4. 测试难以编写时

# 重构前
def process_order(order):
    # 100行代码...

# 重构后
def process_order(order: Order) -> OrderResult:
    validate_order(order)
    apply_pricing(order)
    update_inventory(order)
    send_confirmation(order)
    return OrderResult.SUCCESS
```

#### 5. 迭代规划

```
Sprint 1 (Week 1-2):
  [x] 基础架构搭建
  [x] 核心数据模型
  [x] 基本CRUD操作

Sprint 2 (Week 3-4):
  [x] 用户认证
  [x] 权限控制
  [x] API接口

Sprint 3 (Week 5-6):
  [x] 业务逻辑
  [x] 性能优化
  [ ] 文档完善
```

### 检查清单

- [ ] 是否从最小可行实现开始
- [ ] 每次迭代是否产生可工作代码
- [ ] 是否在需要时才优化
- [ ] 是否有持续重构习惯
- [ ] 是否使用小步提交

---

## 四条准则关系图

```
                    ┌─────────────────────────────────────┐
                    │        Karpathy Guidelines          │
                    └─────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│  代码即文档   │         │ 简单优于复杂  │         │ 测试驱动思考  │
│               │         │               │         │               │
│ - 清晰命名    │         │ - 最小抽象    │         │ - 边界思考    │
│ - 结构化      │         │ - 简单数据    │         │ - 可测试设计  │
│ - 类型注解    │         │ - 避免过早优化│         │ - 依赖注入    │
└───────────────┘         └───────────────┘         └───────────────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────────────┐
                    │         迭代式开发                  │
                    │                                     │
                    │  先工作 → 再正确 → 最后快           │
                    └─────────────────────────────────────┘
```

---

## 实践案例

### 案例: 构建用户管理模块

**迭代1: 最小可行实现**

```python
# 简单的用户存储
users: dict[int, User] = {}

def create_user(name: str, email: str) -> User:
    user = User(id=len(users) + 1, name=name, email=email)
    users[user.id] = user
    return user

def get_user(user_id: int) -> Optional[User]:
    return users.get(user_id)
```

**迭代2: 添加验证**

```python
def create_user(name: str, email: str) -> User:
    if not name or len(name) < 2:
        raise ValueError("名称至少2个字符")
    if "@" not in email:
        raise ValueError("邮箱格式无效")
    
    user = User(id=generate_id(), name=name, email=email)
    users[user.id] = user
    return user
```

**迭代3: 持久化存储**

```python
class UserRepository:
    def __init__(self, db: Database):
        self.db = db
    
    def create(self, name: str, email: str) -> User:
        self._validate(name, email)
        user = User(id=self._next_id(), name=name, email=email)
        self.db.execute(
            "INSERT INTO users (id, name, email) VALUES (?, ?, ?)",
            [user.id, user.name, user.email]
        )
        return user
```

**迭代4: 完善功能**

```python
class UserService:
    def __init__(self, repository: UserRepository, cache: Cache):
        self.repository = repository
        self.cache = cache
    
    def get_user(self, user_id: int) -> Optional[User]:
        cached = self.cache.get(f"user:{user_id}")
        if cached:
            return cached
        
        user = self.repository.find_by_id(user_id)
        if user:
            self.cache.set(f"user:{user_id}", user, ttl=3600)
        return user
```

---

## 参考资料

- [Andrej Karpathy's Blog](https://karpathy.github.io/)
- [Software Engineering at Google](https://abseil.io/resources/swe-book)
- [Clean Code by Robert C. Martin](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)
- [The Pragmatic Programmer](https://pragprog.com/titles/tpp20/)

---

> 本文档由 Multi-Agent SDD/TDD Orchestrator 维护 | 最后更新: 2026-04-17
