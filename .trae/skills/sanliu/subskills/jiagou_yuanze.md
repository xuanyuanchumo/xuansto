---
name: jiagou_yuanze
description: 软件架构设计原则指导，包含MVVM模式、模块化分层、SOLID原则、DRY/YAGNI/KISS原则及质量评估方法。
---
# 架构原则 (Architecture Principles)

## 概述

良好的软件架构是系统可维护性、可扩展性和稳定性的基础。本文档涵盖主流架构模式和设计原则，帮助开发者构建高质量的软件系统。

## 1. MVVM架构模式

### 架构分层

```
┌─────────────────────────────────────────────────────┐
│                    MVVM 架构                         │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │                   View                       │   │
│  │            (UI展示、用户交互)                  │   │
│  └─────────────────────┬───────────────────────┘   │
│                        │ 数据绑定                    │
│  ┌─────────────────────▼───────────────────────┐   │
│  │                ViewModel                     │   │
│  │       (状态管理、命令、数据转换)               │   │
│  └─────────────────────┬───────────────────────┘   │
│                        │ 数据通知                    │
│  ┌─────────────────────▼───────────────────────┐   │
│  │                  Model                       │   │
│  │        (数据模型、业务逻辑、存储)              │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Model-View-ViewModel 分层

#### Model层

**职责：** 数据模型和业务逻辑

```python
class User:
    def __init__(self, user_id: int, name: str, email: str):
        self.user_id = user_id
        self.name = name
        self.email = email

class UserRepository:
    def __init__(self, db_connection):
        self._db = db_connection
    
    def get_user(self, user_id: int) -> User:
        row = self._db.query("SELECT * FROM users WHERE id = ?", user_id)
        return User(**row) if row else None
    
    def save_user(self, user: User) -> bool:
        return self._db.execute(
            "UPDATE users SET name = ?, email = ? WHERE id = ?",
            user.name, user.email, user.user_id
        )
```

#### View层

**职责：** UI展示和用户交互

```python
class UserView:
    def __init__(self, view_model: 'UserViewModel'):
        self._vm = view_model
        self._setup_bindings()
    
    def _setup_bindings(self):
        self._vm.bind('name', self._update_name_display)
        self._vm.bind('email', self._update_email_display)
        self._vm.bind('is_saving', self._update_saving_indicator)
    
    def _update_name_display(self, name: str):
        self.name_label.text = name
    
    def _update_email_display(self, email: str):
        self.email_input.value = email
    
    def on_save_button_click(self):
        self._vm.save_user()
```

#### ViewModel层

**职责：** 状态管理、命令处理、数据转换

```python
from typing import Callable, Dict, Any

class UserViewModel:
    def __init__(self, user_repository: UserRepository):
        self._repo = user_repository
        self._user: User = None
        self._bindings: Dict[str, list] = {}
        self._is_saving = False
    
    @property
    def name(self) -> str:
        return self._user.name if self._user else ""
    
    @name.setter
    def name(self, value: str):
        if self._user:
            self._user.name = value
            self._notify('name', value)
    
    @property
    def email(self) -> str:
        return self._user.email if self._user else ""
    
    @email.setter
    def email(self, value: str):
        if self._user:
            self._user.email = value
            self._notify('email', value)
    
    def load_user(self, user_id: int):
        self._user = self._repo.get_user(user_id)
        self._notify('name', self.name)
        self._notify('email', self.email)
    
    def save_user(self):
        self._is_saving = True
        self._notify('is_saving', True)
        
        success = self._repo.save_user(self._user)
        
        self._is_saving = False
        self._notify('is_saving', False)
        self._notify('save_result', success)
    
    def bind(self, property_name: str, callback: Callable):
        if property_name not in self._bindings:
            self._bindings[property_name] = []
        self._bindings[property_name].append(callback)
    
    def _notify(self, property_name: str, value: Any):
        for callback in self._bindings.get(property_name, []):
            callback(value)
```

### 数据绑定机制

```
┌─────────────────────────────────────────────────────┐
│                  数据绑定流程                        │
│                                                     │
│   View                ViewModel           Model    │
│     │                     │                  │      │
│     │  1. 用户输入         │                  │      │
│     │ ─────────────────►  │                  │      │
│     │                     │  2. 更新数据      │      │
│     │                     │ ───────────────► │      │
│     │                     │                  │      │
│     │                     │  3. 返回结果      │      │
│     │                     │ ◄─────────────── │      │
│     │  4. 通知更新         │                  │      │
│     │ ◄─────────────────  │                  │      │
│     │  5. UI刷新          │                  │      │
│     │                     │                  │      │
└─────────────────────────────────────────────────────┘
```

### ViewModel职责定义

| 职责 | 说明 | 示例 |
|------|------|------|
| 状态管理 | 维护UI状态数据 | 加载状态、选中项 |
| 命令处理 | 响应用户操作 | 保存、删除、刷新 |
| 数据转换 | Model到View的数据转换 | 格式化日期、货币 |
| 验证逻辑 | 输入数据验证 | 表单校验 |
| 导航控制 | 页面跳转逻辑 | 路由管理 |

## 2. 模块化分层架构

### 分层架构设计

```
┌─────────────────────────────────────────────────────┐
│                  分层架构示意                        │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │              表现层 (Presentation)           │   │
│  │          Controller / View / API            │   │
│  └─────────────────────┬───────────────────────┘   │
│                        │                           │
│  ┌─────────────────────▼───────────────────────┐   │
│  │              应用层 (Application)            │   │
│  │          Service / Use Case / DTO           │   │
│  └─────────────────────┬───────────────────────┘   │
│                        │                           │
│  ┌─────────────────────▼───────────────────────┐   │
│  │              领域层 (Domain)                 │   │
│  │       Entity / Value Object / Repository    │   │
│  └─────────────────────┬───────────────────────┘   │
│                        │                           │
│  ┌─────────────────────▼───────────────────────┐   │
│  │              基础设施层 (Infrastructure)      │   │
│  │      Database / External API / Messaging    │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### 各层职责

```python
class OrderService:
    def __init__(self, order_repo: OrderRepository, payment_gateway: PaymentGateway):
        self._order_repo = order_repo
        self._payment_gateway = payment_gateway
    
    def create_order(self, user_id: int, items: list) -> OrderDTO:
        order = Order(user_id=user_id, items=items)
        order.calculate_total()
        self._order_repo.save(order)
        return OrderDTO.from_entity(order)

class Order:
    def __init__(self, user_id: int, items: list):
        self.id = None
        self.user_id = user_id
        self.items = items
        self.total = 0
        self.status = "pending"
    
    def calculate_total(self):
        self.total = sum(item.price * item.quantity for item in items)
    
    def can_cancel(self) -> bool:
        return self.status == "pending"

class SqlOrderRepository(OrderRepository):
    def __init__(self, db: Database):
        self._db = db
    
    def save(self, order: Order) -> Order:
        pass
    
    def find_by_id(self, order_id: int) -> Order:
        pass
```

### 模块边界定义

```
┌─────────────────────────────────────────────────────┐
│                  模块边界示意                        │
│                                                     │
│  ┌───────────────┐     ┌───────────────┐           │
│  │   用户模块     │     │   订单模块     │           │
│  │ ┌───────────┐ │     │ ┌───────────┐ │           │
│  │ │  UserAPI  │ │     │ │ OrderAPI  │ │           │
│  │ ├───────────┤ │     │ ├───────────┤ │           │
│  │ │UserServie │ │     │ │OrderServie│ │           │
│  │ ├───────────┤ │     │ ├───────────┤ │           │
│  │ │UserRepo   │ │     │ │OrderRepo  │ │           │
│  │ └───────────┘ │     │ └───────────┘ │           │
│  └───────┬───────┘     └───────┬───────┘           │
│          │                     │                    │
│          │    公共接口层        │                    │
│          │ ◄─────────────────► │                    │
│          │                     │                    │
│  ┌───────▼─────────────────────▼───────┐           │
│  │            共享内核 (Shared Kernel)  │           │
│  │     Value Objects / Interfaces      │           │
│  └─────────────────────────────────────┘           │
└─────────────────────────────────────────────────────┘
```

### 依赖关系管理

| 依赖方向 | 规则 | 说明 |
|---------|------|------|
| 上层→下层 | 允许 | 表现层依赖应用层，应用层依赖领域层 |
| 下层→上层 | 禁止 | 领域层不应依赖应用层或表现层 |
| 同层之间 | 谨慎 | 同层模块间通过接口通信 |
| 跨层访问 | 通过接口 | 使用依赖倒置解耦 |

```python
from abc import ABC, abstractmethod

class NotificationService(ABC):
    @abstractmethod
    def send(self, user_id: int, message: str) -> bool:
        pass

class EmailNotificationService(NotificationService):
    def __init__(self, email_client: EmailClient):
        self._client = email_client
    
    def send(self, user_id: int, message: str) -> bool:
        return self._client.send(user_id, message)

class OrderService:
    def __init__(self, notification: NotificationService):
        self._notification = notification
    
    def complete_order(self, order_id: int):
        self._notification.send(user_id, "订单已完成")
```

## 3. SOLID原则

### 原则概览

```
┌─────────────────────────────────────────────────────┐
│                  SOLID 原则                          │
│                                                     │
│   S ─► 单一职责原则 (Single Responsibility)         │
│   O ─► 开放封闭原则 (Open/Closed)                   │
│   L ─► 里氏替换原则 (Liskov Substitution)           │
│   I ─► 接口隔离原则 (Interface Segregation)         │
│   D ─► 依赖倒置原则 (Dependency Inversion)          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 单一职责原则 (SRP)

**定义：** 一个类应该只有一个引起它变化的原因

```python
class User:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

class UserRepository:
    def save(self, user: User) -> None:
        pass
    
    def find_by_id(self, user_id: int) -> User:
        pass

class UserValidator:
    def validate(self, user: User) -> bool:
        return self._validate_email(user.email) and self._validate_name(user.name)
    
    def _validate_email(self, email: str) -> bool:
        return "@" in email
    
    def _validate_name(self, name: str) -> bool:
        return len(name) >= 2

class UserNotifier:
    def send_welcome(self, user: User) -> None:
        pass
```

### 开放封闭原则 (OCP)

**定义：** 软件实体应该对扩展开放，对修改关闭

```python
from abc import ABC, abstractmethod

class DiscountStrategy(ABC):
    @abstractmethod
    def calculate(self, price: float) -> float:
        pass

class NoDiscount(DiscountStrategy):
    def calculate(self, price: float) -> float:
        return price

class PercentageDiscount(DiscountStrategy):
    def __init__(self, rate: float):
        self.rate = rate
    
    def calculate(self, price: float) -> float:
        return price * (1 - self.rate)

class FixedDiscount(DiscountStrategy):
    def __init__(self, amount: float):
        self.amount = amount
    
    def calculate(self, price: float) -> float:
        return max(0, price - self.amount)

class PriceCalculator:
    def __init__(self, strategy: DiscountStrategy):
        self._strategy = strategy
    
    def calculate(self, price: float) -> float:
        return self._strategy.calculate(price)
```

### 里氏替换原则 (LSP)

**定义：** 子类对象必须能够替换其父类对象，且程序行为正确

```python
class Bird:
    def move(self) -> str:
        pass

class FlyingBird(Bird):
    def move(self) -> str:
        return "flying"

class Sparrow(FlyingBird):
    pass

class Penguin(Bird):
    def move(self) -> str:
        return "swimming"

def make_bird_move(bird: Bird) -> str:
    return bird.move()

assert make_bird_move(Sparrow()) == "flying"
assert make_bird_move(Penguin()) == "swimming"
```

### 接口隔离原则 (ISP)

**定义：** 客户端不应该依赖它不需要的接口

```python
from abc import ABC, abstractmethod

class Readable(ABC):
    @abstractmethod
    def read(self) -> str:
        pass

class Writable(ABC):
    @abstractmethod
    def write(self, data: str) -> None:
        pass

class ReadWriteFile(Readable, Writable):
    def read(self) -> str:
        return "file content"
    
    def write(self, data: str) -> None:
        pass

class ReadOnlyFile(Readable):
    def read(self) -> str:
        return "read only content"
```

### 依赖倒置原则 (DIP)

**定义：** 高层模块不应依赖低层模块，两者都应依赖抽象

```
┌─────────────────────────────────────────────────────┐
│              依赖倒置示意                            │
│                                                     │
│   传统方式：                    依赖倒置后：         │
│                                                     │
│   ┌─────────┐                  ┌─────────┐         │
│   │高层模块  │                  │高层模块  │         │
│   └────┬────┘                  └────┬────┘         │
│        │                            │              │
│        ▼                            ▼              │
│   ┌─────────┐                  ┌─────────┐         │
│   │低层模块  │                  │ 抽象接口 │         │
│   └─────────┘                  └────┬────┘         │
│                                     │              │
│                                     ▼              │
│                                ┌─────────┐         │
│                                │低层模块  │         │
│                                └─────────┘         │
└─────────────────────────────────────────────────────┘
```

```python
from abc import ABC, abstractmethod

class ILogger(ABC):
    @abstractmethod
    def log(self, message: str) -> None:
        pass

class ConsoleLogger(ILogger):
    def log(self, message: str) -> None:
        print(message)

class FileLogger(ILogger):
    def __init__(self, file_path: str):
        self._file_path = file_path
    
    def log(self, message: str) -> None:
        with open(self._file_path, 'a') as f:
            f.write(message + '\n')

class UserService:
    def __init__(self, logger: ILogger):
        self._logger = logger
    
    def create_user(self, name: str) -> None:
        self._logger.log(f"Creating user: {name}")
```

## 4. DRY、YAGNI、KISS原则

### 原则对比

```
┌─────────────────────────────────────────────────────┐
│              三大简化原则                            │
│                                                     │
│   DRY ─► Don't Repeat Yourself (不重复)            │
│          消除重复代码，提取公共逻辑                  │
│                                                     │
│   YAGNI ─► You Aren't Gonna Need It (不过度设计)   │
│            只实现当前需要的功能                      │
│                                                     │
│   KISS ─► Keep It Simple, Stupid (保持简单)        │
│           用最简单的方式解决问题                    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### DRY原则（不重复）

**核心思想：** 每一部分知识在系统中必须有单一、明确、权威的表示

```python
def validate_email(email: str) -> bool:
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_user_email(email: str) -> bool:
    return validate_email(email)

def validate_company_email(email: str) -> bool:
    return validate_email(email) and email.endswith('@company.com')

class EmailValidator:
    _pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    @classmethod
    def is_valid(cls, email: str) -> bool:
        import re
        return bool(re.match(cls._pattern, email))
```

### YAGNI原则（不过度设计）

**核心思想：** 只实现当前需要的功能，不要为未来可能的需求预先设计

```python
class User:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

class UserRepository:
    def __init__(self, db):
        self._db = db
    
    def save(self, user: User) -> None:
        pass
    
    def find_by_id(self, user_id: int) -> User:
        pass

class UserRepository:
    def __init__(self, db):
        self._db = db
    
    def save(self, user: User) -> None:
        pass
    
    def find_by_id(self, user_id: int) -> User:
        pass
    
    def find_by_name(self, name: str) -> User:
        pass
    
    def find_by_email(self, email: str) -> User:
        pass
    
    def find_all(self) -> list:
        pass
    
    def find_active(self) -> list:
        pass
```

### KISS原则（保持简单）

**核心思想：** 简单的解决方案通常优于复杂的解决方案

```python
def calculate_discount(price: float, customer_type: str) -> float:
    if customer_type == "vip":
        return price * 0.8
    elif customer_type == "gold":
        return price * 0.9
    elif customer_type == "silver":
        return price * 0.95
    else:
        return price

DISCOUNT_RATES = {
    "vip": 0.8,
    "gold": 0.9,
    "silver": 0.95,
    "regular": 1.0
}

def calculate_discount(price: float, customer_type: str) -> float:
    rate = DISCOUNT_RATES.get(customer_type, 1.0)
    return price * rate
```

### 原则应用决策

| 场景 | 推荐原则 | 说明 |
|------|---------|------|
| 发现重复代码 | DRY | 提取公共方法或类 |
| 设计新功能 | YAGNI | 只实现当前需求 |
| 解决复杂问题 | KISS | 寻找最简单方案 |
| 代码重构 | 三者结合 | 先简化，再消除重复 |

## 5. 高内聚低耦合评估方法

### 内聚度评估

```
┌─────────────────────────────────────────────────────┐
│                  内聚度等级                          │
│                                                     │
│   低 ◄──────────────────────────────────► 高       │
│                                                     │
│   偶然性 < 逻辑性 < 时间性 < 过程性 < 通信性 < 顺序性 < 功能性 │
│                                                     │
│   ┌─────────────────────────────────────────────┐  │
│   │ 低内聚：类中方法关联性弱                       │  │
│   │ 高内聚：类中方法共同完成单一职责               │  │
│   └─────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### 内聚度评估指标

| 指标 | 低内聚表现 | 高内聚表现 |
|------|-----------|-----------|
| 方法数量 | 过多不相关方法 | 方法数量适中 |
| 字段使用 | 方法使用不同字段 | 方法共享核心字段 |
| 职责数量 | 多个不相关职责 | 单一明确职责 |
| 命名难度 | 难以用一词描述 | 名称清晰准确 |

```python
class LowCohesion:
    def __init__(self):
        self.user_data = {}
        self.log_file = ""
        self.config = {}
    
    def save_user(self, user): pass
    def read_log(self): pass
    def parse_config(self): pass
    def send_email(self): pass
    def calculate_tax(self): pass

class HighCohesion:
    def __init__(self, db):
        self._db = db
    
    def save(self, user: User) -> None: pass
    def find_by_id(self, user_id: int) -> User: pass
    def find_by_email(self, email: str) -> User: pass
    def delete(self, user_id: int) -> None: pass
```

### 耦合度评估

```
┌─────────────────────────────────────────────────────┐
│                  耦合度等级                          │
│                                                     │
│   紧 ◄──────────────────────────────────► 松       │
│                                                     │
│   内容耦合 < 公共耦合 < 外部耦合 < 控制耦合 < 标记耦合 < 数据耦合 < 无耦合 │
│                                                     │
│   ┌─────────────────────────────────────────────┐  │
│   │ 紧耦合：模块间依赖具体实现                    │  │
│   │ 松耦合：模块间依赖抽象接口                    │  │
│   └─────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### 耦合度评估指标

| 指标 | 紧耦合表现 | 松耦合表现 |
|------|-----------|-----------|
| 依赖方式 | 依赖具体类 | 依赖接口/抽象 |
| 数据传递 | 传递大量数据 | 传递必要数据 |
| 调用方式 | 直接调用内部方法 | 通过公共接口调用 |
| 变更影响 | 修改影响多个模块 | 修改影响范围小 |

```python
class TightCoupling:
    def __init__(self):
        self.db = MySqlDatabase("localhost", "root", "password")
    
    def get_user(self, user_id: int):
        return self.db.execute_query(f"SELECT * FROM users WHERE id = {user_id}")

class LooseCoupling:
    def __init__(self, db: IDatabase):
        self._db = db
    
    def get_user(self, user_id: int) -> User:
        return self._db.find(User, user_id)
```

### 重构建议

```
┌─────────────────────────────────────────────────────┐
│                  重构决策流程                        │
│                                                     │
│   评估内聚度                                        │
│       │                                             │
│       ▼                                             │
│   ┌─────────────┐                                   │
│   │ 内聚度低？   │──是──► 提取类，单一职责            │
│   └─────┬───────┘                                   │
│         │ 否                                        │
│         ▼                                           │
│   评估耦合度                                        │
│       │                                             │
│       ▼                                             │
│   ┌─────────────┐                                   │
│   │ 耦合度高？   │──是──► 引入接口，依赖注入          │
│   └─────┬───────┘                                   │
│         │ 否                                        │
│         ▼                                           │
│   保持现状                                          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## 6. 可扩展性、可维护性评估方法

### 扩展点识别

```
┌─────────────────────────────────────────────────────┐
│                  扩展点类型                          │
│                                                     │
│   1. 策略扩展点 ─► 可替换的算法/策略                 │
│   2. 插件扩展点 ─► 可插拔的功能模块                  │
│   3. 配置扩展点 ─► 通过配置改变行为                  │
│   4. 数据扩展点 ─► 支持新的数据类型                  │
│   5. 接口扩展点 ─► 新的集成方式                      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 扩展性评估清单

| 评估项 | 良好表现 | 改进建议 |
|--------|---------|---------|
| 新增功能 | 无需修改现有代码 | 使用策略模式 |
| 配置变更 | 无需重新编译 | 外部化配置 |
| 数据源切换 | 只改配置 | 使用Repository模式 |
| UI变更 | 不影响业务逻辑 | MVVM分离 |
| 第三方集成 | 通过适配器 | 定义统一接口 |

```python
class PaymentProcessor:
    def __init__(self):
        self._strategies: Dict[str, PaymentStrategy] = {}
    
    def register(self, name: str, strategy: PaymentStrategy) -> None:
        self._strategies[name] = strategy
    
    def process(self, method: str, amount: float) -> Result:
        strategy = self._strategies.get(method)
        if not strategy:
            raise ValueError(f"Unknown payment method: {method}")
        return strategy.pay(amount)

processor = PaymentProcessor()
processor.register("alipay", AlipayStrategy())
processor.register("wechat", WechatPayStrategy())
processor.register("credit", CreditCardStrategy())
```

### 维护成本评估

```
┌─────────────────────────────────────────────────────┐
│              维护成本评估维度                        │
│                                                     │
│   ┌─────────────────────────────────────────────┐  │
│   │  代码可读性                                  │  │
│   │  - 命名清晰度                                │  │
│   │  - 注释质量                                  │  │
│   │  - 代码结构                                  │  │
│   └─────────────────────────────────────────────┘  │
│                                                     │
│   ┌─────────────────────────────────────────────┐  │
│   │  测试覆盖率                                  │  │
│   │  - 单元测试                                  │  │
│   │  - 集成测试                                  │  │
│   │  - 端到端测试                                │  │
│   └─────────────────────────────────────────────┘  │
│                                                     │
│   ┌─────────────────────────────────────────────┐  │
│   │  文档完整性                                  │  │
│   │  - API文档                                   │  │
│   │  - 架构文档                                  │  │
│   │  - 部署文档                                  │  │
│   └─────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 维护性评估指标

| 指标 | 计算方式 | 健康值 |
|------|---------|--------|
| 圈复杂度 | 分支数量 | < 10 |
| 方法长度 | 代码行数 | < 30行 |
| 类大小 | 方法数量 | < 10个 |
| 代码重复率 | 重复行/总行数 | < 5% |
| 测试覆盖率 | 覆盖行/总行数 | > 80% |

## 7. 健壮性、稳定性、安全性评估方法

### 异常处理评估

```
┌─────────────────────────────────────────────────────┐
│              异常处理策略                            │
│                                                     │
│   ┌─────────────────────────────────────────────┐  │
│   │  输入验证层                                  │  │
│   │  - 参数类型检查                              │  │
│   │  - 业务规则验证                              │  │
│   │  - 边界条件处理                              │  │
│   └─────────────────────────────────────────────┘  │
│                      │                              │
│                      ▼                              │
│   ┌─────────────────────────────────────────────┐  │
│   │  业务处理层                                  │  │
│   │  - 业务异常捕获                              │  │
│   │  - 状态回滚                                  │  │
│   │  - 日志记录                                  │  │
│   └─────────────────────────────────────────────┘  │
│                      │                              │
│                      ▼                              │
│   ┌─────────────────────────────────────────────┐  │
│   │  输出处理层                                  │  │
│   │  - 错误信息转换                              │  │
│   │  - 用户友好提示                              │  │
│   │  - 错误码映射                                │  │
│   └─────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

```python
class UserService:
    def __init__(self, repo: UserRepository, logger: Logger):
        self._repo = repo
        self._logger = logger
    
    def create_user(self, name: str, email: str) -> Result:
        try:
            self._validate_input(name, email)
            
            if self._repo.exists_by_email(email):
                return Result.failure("邮箱已被注册")
            
            user = User(name=name, email=email)
            self._repo.save(user)
            
            return Result.success(user)
        
        except ValidationError as e:
            self._logger.warning(f"验证失败: {e}")
            return Result.failure(str(e))
        
        except DatabaseError as e:
            self._logger.error(f"数据库错误: {e}")
            return Result.failure("系统繁忙，请稍后重试")
        
        except Exception as e:
            self._logger.error(f"未知错误: {e}")
            return Result.failure("系统错误")
    
    def _validate_input(self, name: str, email: str) -> None:
        if not name or len(name) < 2:
            raise ValidationError("姓名长度不能少于2个字符")
        if not email or "@" not in email:
            raise ValidationError("邮箱格式不正确")
```

### 容错机制评估

| 机制 | 说明 | 实现方式 |
|------|------|---------|
| 重试 | 失败后自动重试 | 指数退避重试 |
| 熔断 | 防止级联故障 | 熔断器模式 |
| 降级 | 服务不可用时的备选方案 | 返回默认值或缓存 |
| 限流 | 防止过载 | 令牌桶/漏桶算法 |
| 超时 | 避免长时间等待 | 设置合理超时时间 |

```python
import time
from functools import wraps

def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        raise
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
        
        return wrapper
    return decorator

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self._failure_count = 0
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._last_failure_time = None
        self._state = "closed"
    
    def call(self, func, *args, **kwargs):
        if self._state == "open":
            if self._should_attempt_recovery():
                self._state = "half-open"
            else:
                raise CircuitBreakerOpenError()
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_recovery(self) -> bool:
        return (time.time() - self._last_failure_time) >= self._recovery_timeout
    
    def _on_success(self):
        self._failure_count = 0
        self._state = "closed"
    
    def _on_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._failure_count >= self._failure_threshold:
            self._state = "open"
```

### 安全漏洞检查

```
┌─────────────────────────────────────────────────────┐
│              安全检查清单                            │
│                                                     │
│   输入安全                                          │
│   ├── [ ] SQL注入防护                               │
│   ├── [ ] XSS攻击防护                               │
│   ├── [ ] CSRF防护                                  │
│   └── [ ] 输入验证和清理                            │
│                                                     │
│   认证授权                                          │
│   ├── [ ] 密码安全存储                              │
│   ├── [ ] 会话管理                                  │
│   ├── [ ] 权限验证                                  │
│   └── [ ] 敏感操作二次验证                          │
│                                                     │
│   数据安全                                          │
│   ├── [ ] 敏感数据加密                              │
│   ├── [ ] 传输加密(HTTPS)                          │
│   ├── [ ] 日志脱敏                                  │
│   └── [ ] 安全配置                                  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 安全编码示例

```python
import hashlib
import secrets
from typing import Optional

class SecureUserService:
    def __init__(self, repo: UserRepository):
        self._repo = repo
    
    def register(self, username: str, password: str, email: str) -> Result:
        if not self._validate_input(username, password, email):
            return Result.failure("输入验证失败")
        
        if self._repo.exists_by_username(username):
            return Result.failure("用户名已存在")
        
        password_hash = self._hash_password(password)
        user = User(
            username=username,
            password_hash=password_hash,
            email=email
        )
        
        self._repo.save(user)
        return Result.success(user)
    
    def _hash_password(self, password: str) -> str:
        salt = secrets.token_hex(16)
        hash_value = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return f"{salt}:{hash_value.hex()}"
    
    def verify_password(self, user: User, password: str) -> bool:
        salt, stored_hash = user.password_hash.split(':')
        hash_value = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return secrets.compare_digest(hash_value.hex(), stored_hash)
    
    def _validate_input(self, username: str, password: str, email: str) -> bool:
        if not username or len(username) < 3:
            return False
        if not password or len(password) < 8:
            return False
        if not email or "@" not in email:
            return False
        return True

def get_user_by_id(user_id: str) -> Optional[User]:
    if not user_id.isdigit():
        return None
    
    query = "SELECT * FROM users WHERE id = ?"
    return db.execute(query, (int(user_id),))
```

## 检查清单

### MVVM架构检查

- [ ] Model层只包含数据和业务逻辑
- [ ] View层只负责UI展示
- [ ] ViewModel不直接引用View
- [ ] 数据绑定正确实现
- [ ] ViewModel可独立测试

### 模块化检查

- [ ] 各层职责清晰分离
- [ ] 模块边界明确
- [ ] 依赖方向正确（向下依赖）
- [ ] 跨层访问通过接口
- [ ] 共享内核最小化

### SOLID原则检查

- [ ] 每个类只有一个职责
- [ ] 新增功能通过扩展实现
- [ ] 子类可替换父类
- [ ] 接口职责单一
- [ ] 依赖抽象而非具体实现

### 简化原则检查

- [ ] 无重复代码
- [ ] 无过度设计
- [ ] 实现方案简洁
- [ ] 代码易于理解

### 质量评估检查

- [ ] 内聚度高
- [ ] 耦合度低
- [ ] 扩展点明确
- [ ] 维护成本低
- [ ] 异常处理完善
- [ ] 容错机制健全
- [ ] 安全措施到位
