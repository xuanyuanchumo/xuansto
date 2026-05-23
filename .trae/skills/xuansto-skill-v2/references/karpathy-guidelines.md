# Karpathy Guidelines 参考文档

> 版本: 1.9.0 | 更新日期: 2026-04-17 | 编码: UTF-8 without BOM | 行尾: LF

---

## 概述

Karpathy Guidelines 源自 Andrej Karpathy (前Tesla AI总监、OpenAI创始成员) 的软件开发经验总结。这些准则强调代码质量、开发效率和工程实践，特别适用于AI辅助开发场景。

---

## 命名映射

本文档使用中文名称描述四条准则，而 SKILL.md 中使用英文名称。两者表达的是同一核心原则，仅因文化语境不同而采用不同表述方式。

| 英文名称 (SKILL.md) | 中文名称 (本文档) | 核心思想 |
|---------------------|------------------|---------|
| Think Before Coding | 编码前思考 | 编码前完成完整思考，记录决策过程 |
| Simplicity First | 简洁优先 | 选择最简单有效的解决方案 |
| Surgical Changes | 外科手术式修改 | 精准最小化变更，只触碰必须触碰的内容 |
| Goal-Driven Execution | 目标驱动执行 | 所有行动服务于明确的业务目标 |

> **说明**：中文名称采用与需求文档对齐的直译方式，确保中英文映射的一致性与可追溯性。此前曾使用价值主张式命名作为补充视角——"代码即文档"（强调思考结果应成为决策记录）、"简单优于复杂"（强调简洁的收益）、"精准最小变更"（强调变更的精确与克制）、"迭代式开发"（强调渐进式推进）——这些表述有助于理解准则背后的价值理念，但为避免歧义，本文档以直译名称为准。

---

## 目录

1. [准则一：编码前思考](#准则一编码前思考)
2. [准则二：简洁优先](#准则二简洁优先)
3. [准则三：外科手术式修改](#准则三外科手术式修改)
4. [准则四：目标驱动执行](#准则四目标驱动执行)

---

## 准则一：编码前思考

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

## 准则二：简洁优先

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

## 准则三：外科手术式修改

### 核心原则

> "精准最小化变更、只触碰必须触碰的内容。每一行改动都应有明确的目的，不做附带修改。"

### 详细说明

每次代码变更应像外科手术一样精准：定位病灶、最小切口、精确操作。避免"顺手"修改相邻代码、调整格式或清理无关代码。变更范围越小，引入新缺陷的风险越低，代码审查的效率越高。

### 实践指南

#### 1. 变更范围最小化

```python
# ❌ 过度变更: 修复计算逻辑时"顺手"重构了整个函数
def process_order(order: Order) -> OrderResult:
    if not order.items:
        return OrderResult.INVALID
    subtotal = sum(item.price * item.quantity for item in order.items)
    discount = calculate_discount(order.customer, subtotal)
    total = subtotal - discount
    order.total = total
    update_inventory(order)
    send_confirmation(order)
    return OrderResult.SUCCESS

# ✅ 精准变更: 只修复计算逻辑中的bug（折扣应乘以而非减去）
def process_order(order):
    if not order.items:
        return False
    subtotal = sum(item.price * item.quantity for item in order.items)
    discount = calculate_discount(order.customer, subtotal)
-   total = subtotal - discount
+   total = subtotal * (1 - discount)
    order.total = total
    update_inventory(order)
    send_confirmation(order)
    return True
```

#### 2. 不修改相邻代码或格式

```python
# ❌ 顺带修改: 修复bug时同时调整了命名风格和格式
- def getUser(id):
-     user = db.query(f"SELECT * FROM users WHERE id = {id}")
-     if user == None:
+ def get_user_by_id(user_id: int) -> Optional[User]:
+     user = db.query_one("SELECT * FROM users WHERE id = ?", [user_id])
+     if user is None:
          return None
      return user

# ✅ 精准修改: 只修复SQL注入漏洞，保持原有命名和格式
  def getUser(id):
-     user = db.query(f"SELECT * FROM users WHERE id = {id}")
+     user = db.query("SELECT * FROM users WHERE id = ?", [id])
      if user == None:
          return None
      return user
```

#### 3. 匹配现有代码风格

```python
# 现有代码使用双引号和分号结尾
name = "default";
count = 0;

# ❌ 新增代码使用不同风格
name = 'default';
count = 0;
item_count = 0  # 单引号 + 无分号

# ✅ 新增代码匹配现有风格
name = "default";
count = 0;
item_count = 0;
```

#### 4. 只清理自己变更产生的孤立代码

```python
# 原始代码
import os
import sys
import unused_module

def process(data):
    unused_var = 42
    result = transform(data)
    return result

# ❌ 过度清理: 删除了预先存在的unused_module和unused_var
import os
import sys

def process(data):
    result = transform(data)
    return result

# ✅ 精准清理: 只清理自己变更引入的孤立内容
# 如果你的修改移除了对sys的调用，才删除import sys
# 预先存在的unused_module和unused_var不在本次变更范围内
import os
import sys
import unused_module

def process(data):
    unused_var = 42
    result = transform(data)
    return result
```

#### 5. 不删除预先存在的死代码

```python
# 原始代码中存在被注释的旧逻辑
def calculate_price(item):
    base = item.base_price
    # 旧版折扣逻辑，暂时保留
    # if item.seasonal_discount:
    #     base = base * 0.9
    return base * item.quantity

# ❌ 顺手删除: "既然注释了就不需要了"
def calculate_price(item):
    return item.base_price * item.quantity

# ✅ 保留原样: 除非明确被要求清理，否则不删除预先存在的死代码
def calculate_price(item):
    base = item.base_price
    # 旧版折扣逻辑，暂时保留
    # if item.seasonal_discount:
    #     base = base * 0.9
    return base * item.quantity
```

#### 6. 桌面应用开发示例

**修复IPC通道Bug——只改出问题的处理器**

```typescript
// Electron IPC 处理器注册
ipcMain.handle('config:get', handleConfigGet)
ipcMain.handle('config:set', handleConfigSet)
ipcMain.handle('window:minimize', handleWindowMinimize)
ipcMain.handle('window:close', handleWindowClose)

// ❌ 过度变更: config:set 返回值不对时，重构整个IPC架构
// 将所有handler改为class、统一错误处理、添加日志中间件...

// ✅ 精准变更: 只修复 config:set 的返回值问题
ipcMain.handle('config:set', async (event, key, value) => {
-   store.set(key, value)
+   const result = store.set(key, value)
+   return { success: true, data: result }
})
```

**添加系统托盘功能——不重构窗口管理**

```typescript
// ❌ 过度变更: 添加托盘时顺便重构整个窗口管理
// 将BrowserWindow创建改为工厂模式、统一窗口生命周期、添加窗口池...

// ✅ 精准变更: 只添加托盘相关代码，不动现有窗口管理
import { Tray, Menu } from 'electron'

let tray: Tray | null = null

export function createTray(mainWindow: BrowserWindow): void {
    tray = new Tray(iconPath)
    const contextMenu = Menu.buildFromTemplate([
        { label: '显示窗口', click: () => mainWindow.show() },
        { label: '退出', click: () => app.quit() }
    ])
    tray.setContextMenu(contextMenu)
    tray.on('double-click', () => mainWindow.show())
}
// 现有的 createMainWindow() 函数保持不变
```

**修复渲染进程通信Bug——只改受影响的preload脚本**

```typescript
// ❌ 过度变更: 修复contextBridge暴露的API时，重写整个preload架构
// 将所有API分组、添加类型安全的wrapper、统一错误边界...

// ✅ 精准变更: 只修复有问题的API暴露
contextBridge.exposeInMainWorld('api', {
-   readFile: (path: string) => ipcRenderer.invoke('fs:read', path),
+   readFile: (path: string) => ipcRenderer.invoke('fs:readFile', path),
    // 其他API保持不变
    writeFile: (path: string, data: string) => ipcRenderer.invoke('fs:write', path, data),
})
```

### 检查清单

- [ ] 变更是否只包含解决当前问题所必需的修改
- [ ] 是否避免了"顺手"修改相邻代码或调整格式
- [ ] 新增代码是否匹配现有代码风格（引号、分号、命名等）
- [ ] 是否只清理了自己变更产生的孤立import/变量
- [ ] 是否保留了预先存在的死代码（除非明确被要求清理）
- [ ] 每一行改动是否都有明确的目的和理由

---

## 准则四：目标驱动执行

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

#### 6. 测试驱动迭代质量

测试不仅是验证工具，更是设计工具。在每个迭代中，用测试来驱动代码设计，确保每步交付都有质量保障。

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

**边界条件思考驱动健壮设计**

```python
def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Division by zero")
    return a / b

def get_first_element(items: list[T]) -> Optional[T]:
    return items[0] if items else None
```

**依赖注入提高可测试性**

```python
# ❌ 难以测试: 硬编码依赖
class OrderProcessor:
    def process(self, order: Order) -> None:
        db.save(order)
        email.send(order.customer.email, "Order confirmed")

# ✅ 易于测试: 依赖注入
class OrderProcessor:
    def __init__(self, repository: OrderRepository, notifier: Notifier):
        self.repository = repository
        self.notifier = notifier
    
    def process(self, order: Order) -> None:
        self.repository.save(order)
        self.notifier.notify(order.customer, "Order confirmed")
```

**测试金字塔**

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

### 检查清单

- [ ] 是否从最小可行实现开始
- [ ] 每次迭代是否产生可工作代码
- [ ] 是否在需要时才优化
- [ ] 是否有持续重构习惯
- [ ] 是否使用小步提交
- [ ] 是否在编码前思考测试场景
- [ ] 是否考虑了边界条件
- [ ] 代码是否易于测试（依赖注入）
- [ ] 测试命名是否清晰描述行为
- [ ] 是否遵循测试金字塔原则

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
│  编码前思考   │         │  简洁优先     │         │外科手术式修改 │
│               │         │               │         │               │
│ - 清晰命名    │         │ - 最小抽象    │         │ - 最小变更    │
│ - 结构化      │         │ - 简单数据    │         │ - 精准修改    │
│ - 类型注解    │         │ - 避免过早优化│         │ - 匹配风格    │
└───────────────┘         └───────────────┘         └───────────────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────────────┐
                    │        目标驱动执行                │
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

---

## 增量实施约束（@hivehub/rulebook增量实施规范）

所有Agent在执行复杂任务时必须遵循增量实施规范：

- **工作模式**：分解复杂任务 → 实现单个步骤 → 测试验证 → 重复
- **死循环检测**：若在同一错误上连续3次尝试失败，必须停止执行
- **反模式记录**：将失败模式记录到知识库的anti-patterns目录
- **重启流程**：从头重新开始，而非继续在错误方向上尝试

此约束与Karpathy Guidelines的Goal-Driven Execution原则互补——Goal-Driven要求定义成功标准并循环执行直到验证通过，而增量实施约束确保循环不会陷入死循环。

映射关系：

| Karpathy准则 | 增量实施约束 |
|-------------|-------------|
| Goal-Driven Execution | 定义可验证的步骤级检查点，每步验证通过才继续 |
| Think Before Coding | 3次失败后停下来重新思考，而非盲目重试 |
| Simplicity First | 分解为最小可验证步骤，避免一次性实现过多 |

---

## 增量实施约束与Karpathy准则关联

> 增量实施约束的核心机制——**3次失败强制停止并从头重启**（源自 @hivehub/rulebook）——与四条Karpathy准则形成双向强化闭环：

### 1. Think Before Coding / 编码前思考

3次失败强制停止→迫使Agent在重启前重新审视假设，与"编码前思考"原则形成闭环。失败记录写入anti-patterns知识库，使"编码前思考"从静态自解释扩展为包含失败决策的动态文档，后续Agent可从历史错误中学习而非重复踩坑。

### 2. Simplicity First / 简洁优先

分解→单步实现→验证的渐进方法本身就是简洁优先的体现，避免一次性实现复杂逻辑。3次失败阈值约束每步的复杂度上限——若单步3次不过，说明该步骤本身已过于复杂，需进一步拆分而非加码重试。

### 3. Surgical Changes / 外科手术式修改

每步验证确保变更精准，失败时仅回退当前步骤而非整个方案。3次失败后重启而非继续修补，防止"补丁叠补丁"的变更膨胀，强制Agent回到精准最小化修改而非大范围重构——只触碰必须触碰的内容，不做附带修改。

### 4. Goal-Driven Execution / 目标驱动执行

每步有明确验证标准，3次失败记录反模式后从头重启是"定义成功标准→循环执行→验证通过"的极端保障。重启不是放弃目标，而是以更优路径重新迭代——反模式知识确保新迭代不会重复旧错误，迭代效率随知识积累单调递增。

> 本文档由 Multi-Agent SDD/TDD Orchestrator 维护 | 最后更新: 2026-04-28
