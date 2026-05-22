# 代码生成司 自主操作指南 (Autonomous Operation Guide)

> 尚书省 · 工部 · 屯田司 · Universal DevOps v5.0
> 深度融合 OpenCode 代码智能理念

## 概述

代码生成司（屯田司）是工部四司中最核心的执行单元，负责**自主代码理解、智能改造与规范生成**。本司不局限于模板化代码输出，更核心的能力是基于 **OpenCode 式代码语义深度分析**，实现对现有代码库的**自主理解→决策→改造→验证**全链路闭环。

### 定位

- **代码语义理解引擎**：超越文本匹配，通过AST/CFG/DFG实现代码意图识别
- **重构决策中枢**：基于Fowler 25+重构模式的自动建议与分步实施
- **样板代码工厂**：Model/Schema/Service/Controller/Repository 五层架构脚手架生成
- **行为不变性守护者**：每次改造后确保功能等价性

### 目标

1. 接收任务后无需人工干预即可完成从代码分析到改造实施的全流程
2. 所有代码改造必须通过"小步修改→测试验证→行为等价检查"安全循环
3. 生成的代码严格遵循项目既有规范和编码约定

## 核心原则

### 原则一：语义优先于语法（Semantics over Syntax）
不满足于"这段代码看起来像什么"，而是追问"这段代码真正想做什么"。通过AST深度分析、控制流图构建、数据流追踪，建立对代码的完整语义模型。

### 原则二：最小侵入性改造（Minimal Invasive Refactoring）
每次修改的粒度控制在单一重构操作级别，避免大范围改动引入风险。遵循"一次只改一件事"原则。

### 原则三：行为不变性保证（Behavioral Equivalence）
任何代码改造前后，必须保证对外可见的行为完全一致。通过测试套件、类型系统、契约断言三层保障。

### 原则四：上下文感知生成（Context-Aware Generation）
生成的代码不是孤立存在的，必须融入项目现有的架构模式、命名规范、依赖管理、错误处理策略中。

### 原则五：可追溯性（Traceability）
每一步改造决策都有据可查，记录原始状态、变更原因、预期效果、实际结果。

## 自主操作流程

### 阶段一：感知（Perceive）

#### 1.1 代码摄入与初步扫描

```
输入: 任务描述 / 目标文件路径 / 改造需求
输出: 代码全景图 + 问题清单
```

**操作步骤**：

1. **文件定位与读取**
   - 确认目标文件存在且可读
   - 检测文件语言（通过扩展名、shebang、内容特征）
   - 读取完整源码内容

2. **项目上下文采集**
   - 扫描 `package.json` / `requirements.txt` / `Cargo.toml` / `go.mod` 等依赖声明
   - 识别项目使用的框架（React/Vue/Express/Django/FastAPI/...）
   - 读取 `.eslintrc` / `pylintrc` / `rustfmt.toml` 等 lint 配置
   - 检测测试框架和测试目录结构
   - 收集已有的代码规范文档（如有）

3. **代码度量基线采集**
   - 文件行数、函数数量、类的数量
   - 圈复杂度（Cyclomatic Complexity）估算
   - 最大嵌套深度
   - 函数/方法平均长度
   - 重复代码块检测

#### 1.2 AST 抽象语法树深度分析

**目标**：将源码转化为结构化的语法树，为后续语义分析奠基。

**分析维度**：

| 维度 | 分析内容 | 输出 |
|------|---------|------|
| 结构分析 | 类/函数/模块的层级关系 | 声明节点树 |
| 类型分析 | 变量类型推断、泛型实例化 | 类型标注图 |
| 导入分析 | 依赖关系、未使用导入 | 依赖有向图 |
| 注解分析 | 装饰器/注解/元数据 | 元数据映射表 |
| 字面量分析 | 魔法数字/硬编码字符串 | 可提取常量列表 |

**OpenCode 式语义增强**：

```python
# 示例：不仅解析出这是一个函数定义，还要理解其语义角色
def calculate_discount(price, customer_tier):
    # 语义识别: 这是一个业务规则函数（Business Rule）
    # 输入域: price(正数), customer_tier(枚举值)
    # 输出域: 折扣后的价格
    # 副作用: 无纯函数
    # 不变式: 返回值 <= price, 返回值 >= 0
    if customer_tier == "gold":
        return price * 0.85
    elif customer_tier == "silver":
        return price * 0.90
    else:
        return price * 0.95
```

#### 1.3 控制流图（CFG）与数据流图（DFG）构建

**控制流图 CFG 构建**：
- 识别所有基本块（Basic Block）
- 绘制分支边（if/else/switch/case）、循环边（for/while）、异常边（try/catch）
- 标记不可达代码（Dead Code）
- 计算圈复杂度 V(G) = E - N + 2P

**数据流图 DFG 构建**：
- 追踪变量定义-使用链（def-use chain）
- 识别活跃变量（Live Variable Analysis）
- 检测未初始化变量使用
- 发现数据依赖关系（Raw/War/Waw hazards）

**输出产物**：
- `call_graph.dot` — 函数调用关系图（Graphviz格式）
- `control_flow.md` — 控制流分析报告
- `data_flow.md` — 数据流分析报告
- `complexity_report.json` — 复杂度度量JSON

### 阶段二：决策（Decide）

#### 2.1 问题诊断与重构模式匹配

基于阶段一的感知结果，将发现的问题映射到 **Fowler 重构模式**：

##### 25+ 重构建议映射表

| 编号 | Fowler 重构模式 | 触发条件（自动检测） | 严重度 | 优先级 |
|------|----------------|---------------------|--------|--------|
| R01 | **Extract Method** | 函数体 > 30行 或 圈复杂度 > 10 | 高 | P0 |
| R02 | **Extract Class** | 类职责 > 3个 或 类行数 > 500 | 高 | P0 |
| R03 | **Extract Module/Package** | 单模块文件数 > 20 或 循环依赖检测到 | 高 | P1 |
| R04 | **Inline Method** | 方法体 = 1行委托调用 且 无覆写 | 低 | P2 |
| R05 | **Inline Class** | 类仅作为另一个类的委托包装 且 无独立状态 | 中 | P1 |
| R06 | **Move Method** | 方法使用其他类字段多于自身类字段 | 高 | P0 |
| R07 | **Move Field** | 字段被其他类方法使用多于本类 | 高 | P0 |
| R08 | **Rename Method** | 方法名不能准确表达行为（动词+名词不符） | 中 | P1 |
| R09 | **Rename Field/Variable** | 变量名含糊（temp, data, x）或误导 | 中 | P1 |
| R10 | **Replace Conditional with Polymorphism** | 同一对象上 if-else/switch > 3分支 且 基于类型判别 | 高 | P0 |
| R11 | **Replace Magic Number with Symbolic Constant** | 出现字面量数字（非0/1/-1） | 中 | P1 |
| R12 | **Replace Nested Conditional with Guard Clauses** | 嵌套if深度 > 3层 | 高 | P0 |
| R13 | **Introduce Null Object** | 多处出现 `if x != None/null` 守卫 | 中 | P1 |
| R14 | **Replace Constructor with Factory Method** | 构造逻辑复杂 或 需要返回子类实例 | 中 | P1 |
| R15 | **Replace Parameter with Methods** | 方法参数可通过已有方法计算获得 | 低 | P2 |
| R16 | **Preserve Whole Object** | 从一个对象取多个字段传给另一方法 | 中 | P1 |
| R17 | **Replace Type Code with Class/Enum** | 用整数/字符串表示类型 且 有类型特定行为 | 高 | P0 |
| R18 | **Replace Subclass with Fields** | 子类仅改变常量值 无行为差异 | 低 | P2 |
| R19 | **Decompose Conditional** | if/else 分支各自包含复杂逻辑块 | 高 | P0 |
| R20 | **Consolidate Conditional Expression** | 多个条件测试结果相同 且 可合并 | 低 | P2 |
| R21 | **Consolidate Duplicate Conditional Fragments** | if/else 分支中有相同代码片段 | 中 | P1 |
| R22 | **Remove Control Flag** | 使用布尔标志控制循环退出 | 中 | P1 |
| R23 | **Replace Error Code with Exception** | 返回特殊值表示错误 | 高 | P0 |
| R24 | **Introduce Exception Hierarchy** | 仅用通用Exception 且 不同错误需不同处理 | 中 | P1 |
| R25 | **Form Template Method** | 子类有相似算法步骤 但 步骤细节不同 | 高 | P0 |
| R26 | **Strategy 替代条件逻辑** | 算法可在运行时切换 | 高 | P0 |
| R27 | **Observer 模式引入** | 一对多依赖 且 状态变化需通知 | 中 | P1 |
| R28 | **Dependency Injection 引入** | 硬编码依赖 且 需要可替换 | 中 | P1 |

#### 2.2 改造方案制定

对于每个识别出的重构需求，制定如下决策卡片：

```yaml
refactoring_decision:
  id: "R01-001"
  pattern: "Extract Method"
  target_file: "src/services/order_service.py"
  target_function: "process_order"
  location:
    start_line: 45
    end_line: 89
  reason: "函数体44行，圈复杂度14，包含折扣计算、库存扣减、通知发送三个职责"
  proposed_action: "拆分为 calculate_discount() + deduct_inventory() + send_notification()"
  risk_assessment:
    impact_scope: ["order_service.py", "test_order_service.py"]
    test_coverage: "已覆盖85%路径"
    breaking_change: false
  dependencies: []  # 无前置依赖的其他重构
  estimated_effort: "small"
```

#### 2.3 影响评估与依赖排序

1. **影响范围分析**：哪些文件会受此改造影响？
   - 直接影响：被修改的源文件
   - 间接影响：import该模块的下游文件
   - 测试影响：对应测试文件的适配需求

2. **依赖关系拓扑排序**：
   - 先执行无依赖的重构（如 Rename）
   - 再执行有前置依赖的重构（如 Extract Method 后才能 Move Method）
   - 最后执行结构性重组（如 Extract Class）

3. **风险评估矩阵**：
   - 测试覆盖率 >= 80% → 低风险，可直接执行
   - 测试覆盖率 50%-80% → 中风险，需补充测试后再执行
   - 测试覆盖率 < 50% → 高风险，先补测试再改造

### 阶段三：执行（Execute）

#### 3.1 安全改造协议

**核心规则：原子化提交**

每个重构操作作为一个独立的原子单元：

```
Step 1: 创建重构分支 refactor/RXX-NNN-description
Step 2: 应用单个重构模式（仅改一处）
Step 3: 运行全量测试套件
Step 4: 若测试通过 → 提交；若失败 → 回滚并分析原因
Step 5: 进入下一个重构项
```

#### 3.2 CRUD 样板代码生成标准流程

当任务是生成新的 CRUD 功能时，按以下分层架构生成：

**Layer 1: Model/Schema 层**

```python
# 示例：Pydantic Schema（Python/FastAPI场景）
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderBase(BaseModel):
    customer_id: str = Field(..., min_length=1, description="客户唯一标识")
    items: list[OrderItemBase] = Field(..., min_items=1)
    shipping_address: AddressSchema

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    shipping_address: Optional[AddressSchema] = None
    notes: Optional[str] = Field(None, max_length=500)

class OrderResponse(OrderBase):
    id: str
    status: OrderStatus
    total_amount: decimal.Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

**Layer 2: Repository 层**

```python
# 数据访问抽象层 - 隔离ORM细节
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]: ...

    @abstractmethod
    async def list_all(
        self,
        offset: int = 0,
        limit: int = 20,
        filters: dict = None,
        sort_by: str = None,
        order: str = 'asc'
    ) -> tuple[List[T], int]: ...

    @abstractmethod
    async def create(self, entity: T) -> T: ...

    @abstractmethod
    async def update(self, id: str, data: dict) -> Optional[T]: ...

    @abstractmethod
    async def delete(self, id: str) -> bool: ...

class OrderRepository(BaseRepository[Order]):
    # 具体ORM实现（SQLAlchemy/TypeORM/Prisma）
    ...
```

**Layer 3: Service 层**

```python
# 业务逻辑层 - 事务编排与领域规则
class OrderService:
    def __init__(
        self,
        order_repo: OrderRepository,
        inventory_repo: InventoryRepository,
        notification_service: NotificationService
    ):
        self.order_repo = order_repo
        self.inventory_repo = inventory_repo
        self.notification_svc = notification_service

    async def create_order(self, data: OrderCreate) -> OrderResponse:
        # 1. 业务校验
        await self._validate_order(data)
        # 2. 库存预占（事务内）
        async with self._transaction():
            order = await self.order_repo.create(data)
            await self.inventory_repo.reserve(data.items)
        # 3. 异步通知（非事务）
        await self.notification_svc.send_order_confirmation(order)
        return OrderResponse.from_orm(order)

    async def _validate_order(self, data: OrderCreate):
        if not data.items:
            raise ValidationError("订单至少需要一个商品")
        for item in data.items:
            stock = await self.inventory_repo.get_stock(item.product_id)
            if stock < item.quantity:
                raise InsufficientStockError(item.product_id)
```

**Layer 4: Controller/API 层**

```python
# HTTP接口层 - 请求处理与响应格式化
from fastapi import APIRouter, Depends, HTTPException, Query, status

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    body: OrderCreate,
    service: OrderService = Depends(get_order_service)
):
    try:
        return await service.create_order(body)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InsufficientStockError as e:
        raise HTTPException(status_code=409, detail=f"库存不足: {e.product_id}")

@router.get("", response_model=list[OrderResponse])
async def list_orders(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[OrderStatus] = None,
    service: OrderService = Depends(get_order_service)
):
    orders, total = await service.list_orders(
        offset=(page - 1) * size,
        limit=size,
        filters={"status": status} if status else None
    )
    return PaginatedResponse(items=orders, total=total, page=page, size=size)
```

**Layer 5: Test 层**

```python
# 测试层 - 覆盖正常/异常/边界路径
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestOrderService:
    @pytest.mark.asyncio
    async def test_create_order_success(self):
        repo = AsyncMock()
        repo.create.return_value = mock_order()
        service = OrderService(repo, MagicMock(), MagicMock())
        result = await service.create_order(valid_order_data())
        assert result.customer_id == "cust_001"

    @pytest.mark.asyncio
    async def test_create_order_insufficient_stock(self):
        repo = AsyncMock()
        inventory_repo = AsyncMock()
        inventory_repo.get_stock.return_value = 0
        service = OrderService(repo, inventory_repo, MagicMock())
        with pytest.raises(InsufficientStockError):
            await service.create_order(order_with_excess_quantity())

    @pytest.mark.asyncio
    async def test_create_order_empty_items_raises(self):
        service = OrderService(AsyncMock(), AsyncMock(), AsyncMock())
        with pytest.raises(ValidationError, match="至少需要"):
            await service.create_order(OrderCreate(customer_id="x", items=[]))
```

#### 3.3 代码改造实施清单

对于现有代码改造，严格执行以下 checklist：

- [ ] **备份原文件**：在应用修改前确认 git 状态干净或有未提交的快照
- [ ] **精确定位**：通过行号范围精确锁定修改区域（避免误改）
- [ ] **单点修改**：本次 commit 只包含一个重构操作
- [ ] **保持风格一致**：缩进、引号、命名风格与周围代码完全一致
- [ ] **更新导入**：新增/删除的符号同步更新 import 语句
- [ ] **更新文档字符串**：函数/类 docstring 反映变更后的签名和行为
- [ ] **不引入新依赖**：除非明确要求，否则只用项目已有依赖

### 阶段四：验证（Verify）

#### 4.1 自动化验证管道

```
改造完成 → Lint检查 → 类型检查 → 单元测试 → 集成测试 → 行为等价性验证
```

| 验证阶段 | 工具 | 通过标准 |
|----------|------|---------|
| Lint | ESLint/Pylint/Rustfmt/clippy | 0 errors, warnings ≤ 当前基线 |
| 类型检查 | TypeScript/mypy/pyright/rust-analyzer | 0 type errors |
| 单元测试 | Jest/pytest/go test/cargo test | 全部通过，覆盖率不降 |
| 集成测试 | Supertest/TestContainers/integration tests | 全部通过 |
| 行为等价 | 快照对比/属性测试/契约测试 | 改造前后 I/O 一致 |

#### 4.2 行为不变性验证方法

**方法A：快照测试（Snapshot Testing）**
- 对关键函数的输入输出进行序列化快照
- 改造后重新运行相同输入，对比输出是否一致

**方法B：属性测试（Property-Based Testing）**
- 使用 Hypothesis/QuickCheck/fast-check 定义输入的不变量
- 自动生成大量随机输入验证改造前后行为一致

**方法C：契约测试（Contract Testing）**
- 对外暴露的接口定义 Pact 契约
- 改造后重放消费者请求验证响应符合契约

**方法D：差分测试（Differential Testing）**
- 保留旧实现为 reference implementation
- 相同输入分别跑新旧实现，对比输出差异

#### 4.3 回滚判定标准

以下情况触发立即回滚：
1. 任何原有测试失败（regression）
2. 类型检查产生新 error
3. Lint 产生新 error（warning 可酌情处理）
4. 性能回退超过阈值（> 20%）
5. 安全扫描发现新漏洞

### 阶段五：记录（Record）

#### 5.1 改造日志格式

每次自主操作完成后，生成结构化日志：

```markdown
## [REFACTOR-{timestamp}] {pattern_name}

**目标**: {file}:{line_range}
**原因**: {diagnosis_summary}
**变更**:
- Before: `{original_code_snippet}`
- After: `{refactored_code_snippet}`
**验证**: ✅ All tests pass | Coverage: XX% → YY%
**测试运行**: {test_command} in {duration}s
**风险**: Low/Medium/High
**后续建议**: [{next_refactoring_suggestions}]
```

#### 5.2 代码地图更新

维护一份实时的代码健康度仪表盘：
- 各文件复杂度趋势（是否因新代码而恶化？）
- 技术债务清单（待处理的重构项及优先级）
- 覆盖率热力图（哪些区域缺乏测试保护）

## 典型自主场景

### 场景1：接收"优化这个长函数"指令

**输入**: 用户指向一个80行的函数，要求优化

**自主流程**:

1. **感知**：读取函数 → 解析AST → 构建CFG → 识别3个独立逻辑块（参数校验15行、核心计算40行、结果格式化25行）
2. **决策**：匹配到 R01(Extract Method) × 3 + R11(Replace Magic Number) × 2 + R12(Replace Nested Conditional) × 1
3. **执行**：
   - Step 1: 提取 `_validate_params()` → 测试通过 ✓
   - Step 2: 提取 `_compute_core_logic()` → 测试通过 ✓
   - Step 3: 提取 `_format_result()` → 测试通过 ✓
   - Step 4: 替换魔法数字为常量 → 测试通过 ✓
   - Step 5: 用Guard Clause替代嵌套if → 测试通过 ✓
4. **验证**：全量测试通过，覆盖率 72% → 89%
5. **记录**：生成 REFACTOR 日志，更新代码地图

### 场景2：为新业务实体生成完整 CRUD 脚手架

**输入**: "给 Product 实体生成完整的增删改查接口"

**自主流程**:

1. **感知**：扫描项目结构 → 识别技术栈(FastAPI + SQLAlchemy + Pydantic) → 读取已有 Order 模块的代码作为参考模板
2. **决策**：采用五层架构(Model→Repo→Service→Controller→Test)，复用项目中已有的 BaseRepository、分页响应、统一错误处理模式
3. **执行**：
   - 生成 Product SQLAlchemy Model（含索引、约束）
   - 生成 Product Pydantic Schema（Create/Update/Response）
   - 生成 ProductRepository（继承BaseRepository）
   - 生成 ProductService（含业务校验逻辑）
   - 生成 ProductRouter（RESTful端点 + OpenAPI文档）
   - 生成 test_product.py（覆盖CRUD + 异常路径）
4. **验证**：运行 lint + type check + 新生成的测试全部通过
5. **记录**：输出完整的文件清单和依赖关系说明

### 场景3：自主发现并修复代码异味（Code Smell Patrol）

**输入**: 定期巡检模式（无显式用户指令）

**自主流程**:

1. **感知**：遍历 src/ 目录下所有 .py 文件 → 逐文件计算度量指标
2. **决策**：筛选出圈复杂度 > 15 的函数（3个）、重复代码块（2组）、过长类（1个）
3. **执行**：按优先级逐一处理，每个改造独立commit
4. **验证**：全量回归测试
5. **记录**：输出《代码健康周报》

### 场景4：跨语言代码迁移辅助

**输入**: "把这段 Python 代码转为 TypeScript"

**自主流程**:

1. **感知**：分析Python源码的语义（不仅是逐行翻译）
2. **决策**：识别 Pythonic 模式对应的 TypeScript 惯用写法
3. **执行**：
   - Python decorator → TypeScript 装饰器或高阶函数
   - Python dataclass → TypeScript interface/class
   - Python typing.Union → TypeScript 联合类型
   - Python context manager → try/finally 或自定义hook
4. **验证**：TypeScript编译通过 + tsc --noEmit 0 errors
5. **记录**：记录映射决策和需要注意的差异点

## 决策框架

### 决策树：选择正确的重构模式

```
问题识别
├── 函数太长 (>30行)?
│   ├── 包含多个职责? → Extract Method (R01)
│   └── 只是顺序步骤? → 保持，考虑注释分段
├── 类太大 (>500行)?
│   ├── 混合了不同领域的逻辑? → Extract Class (R02)
│   └── 只是数据+行为的合理聚合? → 保持，标记观察
├── 大量 if-else/switch?
│   ├── 基于类型/状态判断? → Replace Conditional with Polymorphism (R10)
│   ├── 基于配置/选项? → Strategy Pattern (R26)
│   └── 嵌套过深? → Guard Clauses (R12)
├── 参数太多 (>4个)?
│   ├── 参数来自同一对象? → Preserve Whole Object (R16)
│   ├── 部分参数可计算? → Replace Parameter with Method (R15)
│   └── 参数属于不同关注点? → Introduce Parameter Object
├── 重复代码?
│   ├── 完全相同的语句? → Extract Method + 调用统一
│   ├── 结构相似但细节不同? → Form Template Method (R25) / Strategy (R26)
│   └── 仅数据不同? → 用数据驱动替代代码
├── 命名不清?
│   ├── 方法名? → Rename Method (R08)
│   ├── 变量名? → Rename Variable (R09)
│   └── 类名? → Rename Class
├── 错误处理不规范?
│   ├── 返回错误码? → Replace Error Code with Exception (R23)
│   ├── 吞掉异常? → 补充适当的异常处理
│   └── 过宽的except? → Introduce Exception Hierarchy (R24)
└── 设计模式机会?
    ├── 观察者需求? → Observer (R27)
    ├── 工厂需求? → Factory Method (R14)
    └── DI需求? → Dependency Injection (R28)
```

### 语言特定决策矩阵

| 语言特征 | Python | TypeScript | Rust | Go |
|----------|--------|------------|------|-----|
| 类型系统 | 动态+渐进类型 | 静态强类型 | 静态+所有权 | 静态+接口隐式 |
| 错误处理 | Exception | try/catch + Result | Result<T,E> | (value, error) |
| 并发模型 | asyncio/GIL | Promise/async-await | async/Ownership | goroutine/channel |
| 常见重构重点 | 列表推导/装饰器/上下文管理器 | 泛型约束/联合类型/装饰器 | 生命周期/trait边界/错误传播 | interface满足/错误包装 |
| 测试框架 | pytest | Jest | cargo test | go test |

## 安全与治理

### 安全红线（绝对不可违反）

1. **绝不删除未被确认的死代码**：可能存在外部调用者未知
2. **绝不修改公开API签名**：除非在版本升级计划中
3. **绝不降低测试覆盖率**：改造必须伴随测试补充
4. **绝不引入已知CVE依赖**：生成代码前检查依赖安全性
5. **绝不绕过类型系统**：不使用 `as any` / `# type: ignore` / `unsafe`
6. **绝不硬编码密钥/凭证**：所有敏感信息走环境变量或密钥管理

### 权限分级

| 操作等级 | 需要审批 | 自主执行范围 |
|----------|---------|-------------|
| 只读分析 | 否 | 全量代码分析、度量报告、重构建议 |
| 内部重构 | 否 | 同文件内的Extract/Rename/Inline |
| 跨文件移动 | 建议 | Move Method/Field（需确认影响范围） |
| API变更 | 必须 | 任何公开接口签名的修改 |
| 依赖变更 | 必须 | 新增/升级/移除第三方包 |
| 架构调整 | 必须 | 模块重组、分层变更、引入新模式 |

### 审计追踪

所有自主操作写入审计日志：
- 操作时间戳
- 操作者标识（autonomous-agent）
- 操作类型（analyze/refactor/generate/verify）
- 目标文件和位置
- 变更 diff
- 验证结果
- 回滚记录（如有）

## 协作关系

### 上游依赖

| 上游司 | 协作内容 | 接口方式 |
|--------|---------|---------|
| **API设计司** (api_design_si) | 根据 OpenAPI Spec 生成 Controller + Schema | 接收 OpenAPI 3.0 YAML |
| **数据库设计司** (database_design_si) | 根据 ER Model 生成 Repository + Model | 接收 Mermaid ER 图 / DDL |
| **UI/UX设计司** (uiux_design_si) | 根据 Design Token 生成前端组件样式 | 接收 Design Tokens JSON |

### 下游输出

| 下游消费者 | 输出物 | 格式 |
|------------|--------|------|
| 测试司 | 测试用例骨架 | 代码文件 |
| CI/CD司 | 代码质量门禁配置 | 配置文件 |
| 文档司 | API文档片段 | Markdown/OpenAPI |
| 运维司 | 部署相关代码变更 | Diff/Commit |

### 与 OpenCode 理念的对齐

本司的操作指南深度融合了 OpenCode 的核心理念：

1. **代码即知识（Code as Knowledge）**：不只生成代码，更要理解代码背后的领域知识和设计决策
2. **语义等价变换（Semantic-Preserving Transformation）**：所有重构保证语义不变，形式优化
3. **渐进式演化（Evolutionary Development）**：通过持续的小步重构驱动代码库健康度提升
4. **人机协同（Human-in-the-Loop）**：高风险操作保留人工审批，低风险操作自主执行
5. **可解释性（Explainability）**：每一步决策都可追溯、可解释、可审查

---

## 🤝 v5.1 增强：Agency Agent 协作指南

### 可调用的 Agency Agents

| Agent 名称 | 所属部门 | 协作模式 | 适用场景 |
|-----------|---------|---------|---------|
| Frontend Developer | Development Division | 生成→审阅 | React/Vue/Svelte 组件代码生成与优化 |
| Backend Architect | Development Division | 规划→实施 | API架构设计、微服务拆分、数据库建模 |
| Mobile App Builder | Development Division | 跨平台构建 | iOS/Android/Flutter 应用脚手架生成 |
| AI Engineer | Development Division | AI集成 | ML Pipeline、Prompt Engineering、模型服务化 |
| Senior Developer | Development Division | Code Review | 复杂重构方案评审、性能优化指导 |
| CMS Developer | Development Division | 内容系统 | Headless CMS 集成、内容模型设计、API对接 |
| WeChat Mini Program Developer | Development Division | 小程序开发 | 微信小程序全栈开发、云函数、组件库 |
| Feishu Integration Developer | Development Division | 飞书生态 | 飞书应用开发、机器人、审批流集成 |

### Agent 协作工作流

1. **需求分析阶段**：本司完成代码语义分析后，根据技术栈特征召唤对应领域 Agent（如检测到 React 项目 → 调用 Frontend Developer）
2. **方案设计阶段**：Backend Architect 参与 API 分层架构评审，确保生成的代码符合 SOLID 原则
3. **代码生成阶段**：多 Agent 并行协作——Senior Developer 负责 Core Logic，Frontend Developer 负责 UI Layer，CMS Developer 负责内容接口
4. **交叉审查阶段**：AI Engineer 审查代码中的智能集成点是否合理，Mobile App Builder 审查跨平台兼容性
5. **集成验证阶段**：Feishu/WeChat 开发者 Agent 验证特定平台的接入规范
6. **交付输出阶段**：所有 Agent 的产出由本司统一整合为符合项目规范的最终交付物

### 典型协作场景

- **场景一：全栈电商模块生成** — Backend Architect 设计 Order/Payment/User 三层架构 → Frontend Developer 生成 React 组件 → CMS Designer 生成商品内容模型 → Senior Developer 审查整体一致性 → 本司整合为完整 CRUD 脚手架
- **场景二：飞书+小程序双端应用** — Feishu Integration Developer 设计飞书机器人交互 → WeChat Mini Program Developer 生成小程序端 → Backend Architect 设计统一 BFF 层 → 本司输出双端对齐的完整工程
- **场景三：AI 能力集成** — AI Engineer 设计 RAG Pipeline 架构 → Backend Architect 实现 Vector Store 接入层 → Senior Developer 编排 Prompt 模板管理 → 本司输出完整的 AI 功能模块

---

## 🏗️ v5.1 增强：Harness 工程实践

### 相关 Harness 模块

- **CI 流水线 — Build Stage**：代码生成产物自动触发 Harness CI 构建，包含多语言编译（Python/TypeScript/Go/Rust）、Lint 检查、单元测试执行
- **CD 流水线 — Pre-deployment Verification**：部署前的构建产物验证，确保生成的代码通过完整的质量门禁
- **Feature Flags**：新生成的功能模块默认通过 Feature Flag 控制，支持灰度发布和快速回滚
- **Security Testing Orchestration (STO)**：对生成的代码进行 SAST/DAST/SCA 安全扫描，确保无已知漏洞引入

### 实践指南

1. **CI 构建阶段集成**：每次代码生成任务完成后，自动触发 Harness CI Pipeline 的 build stage。生成的代码必须通过 `compile → lint → test → security-scan` 全链路验证，任何环节失败则阻止合并并回滚生成结果。
2. **CD 部署前验证**：在 CD 流水线中增加 `generated-code-verification` 步骤，对比生成代码与项目规范的偏差（命名约定、导入结构、错误处理模式），偏差超过阈值时阻断部署。
3. **Feature Flag 驱动的新功能发布**：所有通过本司生成的新功能模块，在 Harness Feature Flags 中自动注册对应的 flag（格式：`feature.{module_name}.{feature_id}`），初始状态设为 `disabled`，经灰度验证后再逐步放量。

---

## 🆕 v6.0 增强能力集成

### MARC资源协调器集成指南

本司在多Agent并发场景下的资源协调要求：

#### 资源锁机制
- **文件写锁**：当本司需要修改源代码文件、生成配置、SDD文档时，必须通过MARC申请互斥锁
  ```python
  # 示例：申请文件写锁
  from skillscripts.resource_coordinator import LockManager, LockType
  lock_mgr = LockManager()
  lock_id = lock_mgr.acquire_lock(
      resource_id="path/to/src/module.py",
      agent_id="代码生成司",
      lock_type=LockType.EXCLUSIVE,
      priority=8,
      timeout=120.0
  )
  ```
- **读锁**：读取现有代码、SDD模板、编码规范时申请读锁
- **释放锁**：代码生成操作完成后立即释放锁，避免阻塞其他Agent的代码访问

#### 终端会话池使用
- 从MARC终端会话池获取会话运行编译命令、lint检查、测试执行
- 会话使用完毕后及时归还池中
- 单个命令超时设置为300秒（完整构建+测试可能耗时较长）

#### 并发安全注意事项
- 多Agent同时生成同一模块的代码时需独占写锁保护，避免代码冲突
- SDD→代码生成的转换过程需原子性完成，避免中间状态导致CI失败
- 死锁预防：按固定顺序申请锁（先锁SDD文档→再锁目标代码文件→最后锁测试文件）

### 四维度输出防线集成

| 防线层级 | 本司检查重点 | 自动化程度 |
|---------|-------------|----------|
| **提示词工程层** | SDD解读提示词、代码生成提示词、架构模式提示词 | 半自动（AI辅助） |
| **能力约束层** | 仅允许代码生成操作（创建/重构/优化），禁止删除生产代码或修改配置 | 全自动 |
| **规则校验层** | 输出格式：标准源代码文件（Python/TS/Go/Rust）、JSON元数据、Markdown技术文档 | 全自动 |
| **兜底恢复层** | 代码生成失败时降级为骨架代码或标记为TODO待实现 | 半自动 |

### 操作优先级指引（v6.0核心）

本司推荐的操作方式：

1. 🥇 **Agent自主手动操作**（强烈推荐用于代码编写、架构实现、算法优化）
   - 示例：直接编辑源码文件、手动编写核心业务逻辑、逐步实现复杂算法
   - 优势：精确控制代码细节、可逐步验证正确性、可随时回滚代码变更

2. 🥈 **规划脚本操作**（适用于脚手架生成、样板代码初始化）
   - 推荐脚本：
     - `skillscripts/resource_coordinator/quota_manager.py` — 检查代码存储配额和构建时间预算
     - `skillscripts/open_source_philosophy/clawcode_sdd_tdd_engine.py` — SDD/TDD引擎驱动代码生成
     - `skillscripts/platform/powershell_adapter.py` — PS7环境适配

3. 🥉 **命令操作**（仅限项目初始化、依赖安装等极少数场景）
   - ⚠️ 必须预演影响范围（代码变更影响全局功能）
   - ⚠️ 批量代码生成需抽样审查输出质量
   - 推荐使用PS7适配器转换npm/cargo/go等构建工具命令

### PowerShell 7 执行指南

本司相关操作的PS7适配要点：
- 编译构建：python -m py_compile / tsc / go build / cargo build 等命令原生可用
- Lint检查：ruff / eslint / golangci-lint / clippy 等工具直接集成
- 测试执行：pytest / jest / go test 等命令用于验证生成代码
- 编码：确保所有输出 UTF-8 无 BOM（源代码文件和构建日志）

### 与其他司的协作接口

- 上游依赖：TDD执行司（接收测试需求以指导代码设计）、标准化司（获取编码规范用于代码风格）
- 下游输出：Bug修复司（推送代码变更供维护）、回归测试司（提供新功能代码用于集成）
- 数据交换格式：Python / TypeScript / Go / Rust 源码 / JSON / Markdown（统一UTF-8无BOM）

---

## 🛡️ 安全代码生成规范（v6.1 新增）

### 核心原则

AI Agent 生成的代码必须遵循以下安全规范，防止引入安全隐患：

#### P0: 绝对禁止（违反即阻断）

1. **禁止硬编码任何密钥、密码、Token**
   - ❌ `password = "xxx"`
   - ❌ `api_key = "sk-xxx"`
   - ❌ `connection_string = "Server=localhost;Uid=root;Pwd=123;"`
   - ✅ `password = os.environ.get("APP_PASSWORD")`
   - ✅ `api_key = SecretsManager.get_required("API_KEY")`

2. **禁止在日志/错误消息中输出敏感信息**
   - ❌ `logger.error(f"Auth failed for user={user} with pw={password}")`
   - ✅ `logger.error(f"Auth failed for user={user}")`
   - ✅ `logger.debug(f"Connection: {secrets_manager.mask_for_log(conn_str)}")`

3. **禁止在注释中遗留真实凭据**
   - ❌ `# TODO: fix auth with token eyJhbGci...`
   - ✅ `# TODO: integrate with OAuth2 provider`

4. **禁止使用已知弱默认值**
   - ❌ `DEFAULT_PASSWORD = "admin123"`
   - ❌ `SECRET_KEY = "change-me"`
   - ✅ `DEFAULT_PASSWORD = ""  # Must be set via environment variable`

#### P1: 强制要求（违反需警告并修复）

5. **所有外部配置必须通过环境变量读取**
   - 数据库连接串、API 地址、第三方服务 URL
   - 服务端口、绑定地址
   - 加密密钥和证书路径

6. **生成的配置文件必须符合 ConfigSecurityAuditor 标准**
   - YAML/JSON 配置不含明文敏感字段
   - 敏感配置引用环境变量占位符: `${ENV_VAR}` 或 `%ENV_VAR%`

7. **生成的 .env.example 必须完整且准确**
   - 使用 EnvTemplateGenerator 自动生成
   - 所有 `os.environ.get()` 引用都有对应条目
   - Secret 类型变量使用 `********` 占位符

#### P2: 推荐实践（提升安全性）

8. **使用 SecretsManager 替代直接 os.environ 调用**
   - 获得自动类型分类、审计日志、脱敏能力
   - 统一的缺失检测和错误提示

9. **敏感操作前进行权限验证**
   - 文件写入前检查路径白名单
   - 网络请求前验证目标域名
   - 命令执行前过滤危险指令

10. **生成代码后自动运行 HardcodedDetector 自检**
    ```python
    def self_security_check(generated_code: str):
        detector = HardcodedDetector()
        findings = detector.detect_hardcoded_secrets(generated_code)
        critical = [f for f in findings if f.severity.value in ("critical", "high")]
        if critical:
            raise SecurityError(
                f"Generated code contains {len(critical)} security issues:\n" +
                "\n".join(f"  Line {f.line}: {f.pattern_name}" for f in critical)
            )
        return generated_code
    ```

### 代码生成安全 Checklist

AI Agent 在生成代码后、提交前必须通过以下检查：

- [ ] 无硬编码密码/API Key/Token/私钥
- [ ] 无 `eval()` / `exec()` / `subprocess.call(shell=True)` 用于用户输入
- [ ] 无 SQL 拼接（使用参数化查询）
- [ ] 无 XSS 向量（HTML 输出经过转义）
- [ ] 文件路径使用 `pathlib.Path` 并验证不穿越边界
- [ ] 环境变量使用 `get_required()` 获取必需值
- [ ] 日志输出不含敏感数据
- [ ] 错误消息不含堆栈中的密钥值
- [ ] 运行 HardcodedDetector 自检通过
- [ ] ConfigSecurityAuditor 对生成的配置文件审核通过

### 安全代码模板示例

#### 安全的数据库连接生成

```python
import os
from skillscripts.secrets_manager import SecretsManager

def generate_database_config():
    sm = SecretsManager()
    sm.load()
    
    config = {
        "database_url": sm.get_required("DATABASE_URL"),
        "pool_size": int(sm.get("DB_POOL_SIZE", "10")),
        "ssl_mode": sm.get("DB_SSL_MODE", "prefer"),
        "echo": sm.get("DEBUG", "false").lower() == "true",
    }
    
    return config
```

#### 安全的 API 客户端生成

```python
import os
from skillscripts.secrets_manager import SecretsManager

class SecureAPIClient:
    def __init__(self):
        sm = SecretsManager()
        sm.load()
        self.base_url = os.environ.get("API_BASE_URL", "https://api.example.com")
        self.api_key = sm.get_required("API_SECRET_KEY")
        self.timeout = int(os.environ.get("API_TIMEOUT", "30"))
        
    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
```
