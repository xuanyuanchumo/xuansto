# 测试框架司 自主操作指南 (Autonomous Operation Guide)

## 概述

测试框架司（test_framework_si）是尚书省兵部下属基础设施管理机构，负责测试技术栈的选型、配置、维护与演化。本司的核心使命是：**为整个兵部的测试活动提供稳定、高效、可扩展的测试基础设施，使TDD执行司、覆盖率分析司和回归测试司能够专注于各自的核心职责而无后顾之忧**。

本司不负责编写具体的业务测试用例（归属TDD执行司），不负责设定覆盖率目标（归属覆盖率分析司），也不负责决定回归范围（归属回归测试司）。本司的职责边界清晰聚焦于**测试基础设施的全生命周期管理**。

## 核心原则

1. **框架中立原则**：本司维护多语言、多框架的适配能力，不偏向任何单一技术栈。
2. **渐进演化原则**：测试基础设施的变更必须平滑过渡，禁止破坏性切换。
3. **隔离性第一原则**：测试之间必须完全隔离，共享状态是最高优先级的缺陷。
4. **可观测性原则**：所有测试框架配置和运行行为必须有清晰的日志和报告输出。
5. **最小侵入原则**：测试基础设施对业务代码的侵入应降至最低。
6. **社区同步原则**：跟踪主流测试框架的版本更新和安全公告，及时评估升级必要性。

## 自主操作流程

### 阶段一：感知（Perceive）

#### 1.1 项目技术栈感知
- 扫描项目根目录识别编程语言及版本（package.json/pyproject.toml/go.mod/pom.xml/Gemfile等）
- 识别项目已安装的测试相关依赖及其版本号
- 检测项目中现有的测试文件分布模式和命名约定
- 分析项目的构建系统和CI/CD流水线配置
- 识别项目的代码风格工具（linter/formatter）配置

#### 1.2 测试现状感知
- 统计现有测试文件数量和测试用例总数
- 识别当前使用的测试框架和断言库组合
- 检测测试配置文件的完整性和合理性
- 评估现有Mock/Stub/Spy的使用模式是否规范
- 识别测试执行中的性能瓶颈（启动时间、并行能力）

#### 1.3 痛点感知
- 收集来自TDD执行司的框架使用反馈
- 接收覆盖率分析司的基础设施层面问题报告
- 监听回归测试司关于测试稳定性方面的诉求
- 主动检测测试套件中的反模式和不规范用法

### 阶段二：决策（Decide）

#### 2.1 测试框架适配器选择决策

本司维护6种主流测试框架的标准化适配器，根据项目技术栈自动匹配：

| 框架适配器 | 适用语言 | 核心特性 | 典型配置文件 | 并行执行 |
|-----------|---------|---------|------------|---------|
| pytest | Python | 插件生态丰富、参数化强大 | pytest.ini / pyproject.toml | pytest-xdist |
| jest | JavaScript/TypeScript | 内置Mock、快照测试、零配置 | jest.config.js/ts | 内置Worker池 |
| go-test | Go | 官方工具链、表格驱动测试 | 无(约定优先) | 内置-race |
| JUnit5 | Java | 分层架构、扩展模型、参数化 | junit-platform.properties | 并行执行扩展 |
| RSpec | Ruby | DSL风格、内置Mock、上下文管理 | .spec_helper.rb | 并行测试 |
| Vitest | TypeScript/JavaScript | Vite原生、ESM支持、极速 | vitest.config.ts | 内置Worker池 |

**框架选择决策流程**：
```
检测项目语言
  │
  ├─ Python → 默认pytest，备选unittest（遗留项目兼容）
  ├─ JS/TS(Node) → 默认jest，Vite项目优选vitest
  ├─ Go → 固定go-test（官方标准）
  ├─ Java → 默认JUnit5，Spring项目可结合Spring Test
  └─ Ruby → 默认RSpec，Minitest用于简单场景
```

#### 2.2 测试替身（Test Double）模式选择决策

**四大替身模式选择指南**：

##### Mock — 外部依赖隔离
**适用场景**：
- 需要验证被测代码与外部依赖的交互方式
- 外部依赖不可用或成本过高（数据库、API、文件系统）
- 需要模拟异常情况来测试错误处理路径

**使用规范**：
```python
# Mock使用示例：验证外部API调用
def test_order_service_calls_payment_api():
    payment_api_mock = Mock(spec=PaymentAPIClient)
    payment_api_mock.charge.return_value = PaymentResult(success=True, transaction_id="tx_123")

    service = OrderService(payment_client=payment_api_mock)
    result = service.process_order(Order(amount=100))

    assert result.success is True
    payment_api_mock.charge.assert_called_once_with(amount=100)
    # Mock的核心价值：验证交互行为，而非仅验证结果
```

**Mock违规检测**：
- 过度Mock：Mock了不应被Mock的对象（如值对象、纯函数）
- Mock泄漏：Mock状态在测试间泄漏导致不稳定测试
- 不精确断言：使用assert_any_call代替assert_called_once_with

##### Stub — 固定响应替身
**适用场景**：
- 被测代码依赖某个接口的返回值，但不关心调用细节
- 需要构造复杂的测试数据但不想依赖真实数据源
- 需要模拟确定的返回序列

**使用规范**：
```javascript
// Stub使用示例：固定数据响应
const userStub = {
  findById: (id) => ({
    id,
    name: 'Test User',
    email: `test${id}@example.com`,
    role: 'admin'
  })
};

test('should display user profile', () => {
  const controller = new UserController(userRepository: userStub);
  const view = controller.showProfile('user_42');
  
  expect(view.userName).toBe('Test User');
  // Stub仅提供数据，不验证调用行为
});
```

##### Spy — 行为记录验证
**适用场景**：
- 需要保留原始实现的同时记录调用信息
- 验证函数是否被调用、调用次数、调用参数
- 调试阶段临时替换真实实现以观察行为

**使用规范**：
```java
// Spy使用示例：包装真实对象记录行为
@Test
void shouldLogNotificationOnOrderCompletion() {
    NotificationService realService = new EmailNotificationService();
    NotificationService spy = spy(realService);

    OrderProcessor processor = new OrderProcessor(spy);
    processor.completeOrder(order);

    verify(spy, times(1)).send(order.getCustomer(), contains("completed"));
    // Spy保留真实实现能力，同时增加验证能力
}
```

##### Factory — 测试数据构建
**适用场景**：
- 需要频繁创建复杂测试对象
- 测试对象有多个必填字段和可选字段
- 需要保证测试数据的合理性和一致性
- 多个测试需要相似但有差异的测试数据

**使用规范**：
```ruby
# Factory使用示例：Ruby FactoryBot风格
FactoryBot.define do
  factory :order do
    sequence(:id) { |n| "ORD-#{n.to_s.rjust(6, '0')}" }
    status { 'pending' }
    association :customer
    
    trait :completed do
      status { 'completed' }
      completed_at { Time.current }
    end
    
    trait :with_items do
      transient { item_count { 3 } }
      after(:create) do |order, evaluator|
        create_list(:order_item, evaluator.item_count, order: order)
      end
    end
  end
end

# 使用：灵活组合构建测试数据
order = create(:order, :completed, :with_items, item_count: 5)
```

**替身模式选择决策树**：
```
需要隔离外部依赖？
  ├─ 是 → 需要验证交互行为？
  │        ├─ 是 → Mock
  │        └─ 否 → Stub
  └─ 否 → 需要记录调用信息？
           ├─ 是 → Spy
           └─ 否 → 需要构建复杂数据？
                    ├─ 是 → Factory
                    └─ 否 → 直接使用真实对象
```

#### 2.3 参数化测试策略决策

**自动生成规则**：
从函数签名自动推导参数化测试的组合空间：

1. **提取参数类型**：解析函数签名的参数类型注解
2. **生成边界值**：为每种类型生成典型值集
   - 数值型：0, 1, -1, MAX, MIN, 边界±1
   - 字符串：空串, 单字符, 长字符串, 特殊字符, Unicode
   - 布尔型：true, false
   - 集合：空集合, 单元素, 多元素, null/None
   - 枚举：每个枚举值
3. **组合策略**：默认每对组合（Pairwise），高风险路径全组合
4. **过滤排除**：排除已知无效组合和重复等价类

**参数化测试框架对照表**：

| 框架 | 参数化语法 | 标记语法 | 数据源格式 |
|-----|----------|---------|----------|
| pytest | @pytest.mark.parametrize | @pytest.mark.* | 列表/CSV/YAML |
| jest | test.each\`\` | .concurrent / .skip | 模板字面量数组 |
| go-test | 子测试 t.Run() | +build tags | 表格驱动 |
| JUnit5 | @ParameterizedTest | @Tag | @CsvSource / @MethodSource |
| RSpec | shared_examples / let | metadata | Hash数组 |
| Vitest | it.each\`\` | .concurrent / .skip | 模板字面量数组 |

#### 2.4 测试分组标记机制

**标准标记体系**：

| 标记 | 含义 | 执行策略 | 典型场景 |
|-----|------|---------|---------|
| @unit | 单元测试 | 每次全量执行 | 纯逻辑、无外部依赖 |
| @integration | 集成测试 | PR触发+每日构建 | 数据库访问、服务间调用 |
| @e2e | 端到端测试 | 发布前/每日夜间 | 全链路用户场景 |
| @slow | 慢速测试 | 按需执行 | 大数据处理、IO密集 |
| @security | 安全测试 | 安全扫描周期 | 权限校验、注入防护 |

**自定义标记扩展规则**：
- 项目级标记需在框架配置文件中注册
- 标记命名采用snake_case格式
- 标记应具有排他性或明确的包含关系
- 禁止创建语义重叠的冗余标记

### 阶段三：执行（Execute）

#### 3.1 测试框架初始化与配置

**标准化初始化清单**：
1. 创建/更新测试框架配置文件
2. 配置测试文件发现规则（glob模式）
3. 设置测试超时阈值（单测试/总套件）
4. 配置覆盖率收集插件（与覆盖率分析司对接）
5. 配置并行执行参数
6. 设置测试报告输出格式和路径
7. 配置环境变量注入机制
8. 设置全局Setup/Teardown钩子

**各框架标准配置模板**：

pytest标准配置（pyproject.toml）：
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_functions = ["test_*"]
python_classes = ["Test*"]
addopts = [
    "-v",
    "--tb=short",
    "--strict-markers",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html:coverage_html",
]
markers = [
    "unit: unit tests (run always)",
    "integration: integration tests (PR + daily)",
    "e2e: end-to-end tests (pre-release)",
    "slow: slow running tests (on-demand)",
    "security: security-related tests",
]
timeout = 30
asyncio_mode = "auto"
```

jest标准配置（jest.config.js）：
```javascript
module.exports = {
  roots: ['<rootDir>/tests'],
  testMatch: ['**/*.test.ts', '**/*.spec.ts'],
  collectCoverageFrom: ['src/**/*.{ts,js}', '!src/**/*.d.ts'],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1'
  },
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  testTimeout: 10000,
  maxWorkers: '50%',
};
```

#### 3.2 测试替身基础设施搭建

**统一替身注册中心**：
建立项目级别的替身注册和管理机制，避免散乱的Mock定义：

```python
# tests/conftest.py — pytest统一替身注册
import pytest
from unittest.mock import Mock, MagicMock, patch

# === 外部服务Mock工厂 ===
@pytest.fixture
def mock_database():
    """数据库连接Mock，自动回滚事务"""
    db = MagicMock()
    db.commit.return_value = None
    db.rollback.return_value = None
    yield db
    db.reset_mock()

@pytest.fixture
def mock_external_api():
    """外部API客户端Mock"""
    api = Mock()
    # 注册通用响应模式
    api.get.return_value = {"status": "ok"}
    api.post.return_value = {"id": "generated_id"}
    yield api
    api.reset_mock()

# === 测试数据Factory ===
@pytest.fixture
def sample_user_factory():
    """用户对象Factory"""
    def _create(**overrides):
        defaults = {
            "id": "user_001",
            "name": "Test User",
            "email": "test@example.com",
            "role": "member",
            "is_active": True,
        }
        return type('User', (), {**defaults, **overrides})()
    return _create
```

#### 3.3 参数化测试基础设施

**参数化测试辅助模块**：
```python
# tests/helpers/parametrize.py
from typing import Any, List, Tuple, Type
from dataclasses import fields
from enum import Enum

class BoundaryValueGenerator:
    """从类型注解自动生成边界测试值"""

    @staticmethod
    def for_type(type_hint: type) -> List[Any]:
        generators = {
            int: [0, 1, -1, 2**31-1, -2**31, 2**31, -2**31-1],
            float: [0.0, 1.0, -1.0, float('inf'), float('-inf'), float('nan')],
            str: ["", "a", " "*100, "\n\t", "中文", "emoji🎉"],
            bool: [True, False],
            list: [[], [1], [1,2,3]],
            type(None): [None],
        }
        # 处理Optional/Union类型
        if hasattr(type_hint, '__origin__'):
            import typing
            if type_hint.__origin__ is typing.Union:
                results = []
                for arg in type_hint.__args__:
                    results.extend(BoundaryValueGenerator.for_type(arg))
                return results
        return generators.get(type_hint, [None])

    @staticmethod
    def pairwise(params_dict: dict) -> List[Tuple]:
        """生成配对组合（Pairwise）减少组合爆炸"""
        # 简化版配对组合算法
        import itertools
        keys = list(params_dict.keys())
        values = list(params_dict.values())
        
        pairs = []
        for i in range(len(keys)):
            for j in range(i+1, len(keys)):
                for v_i in values[i]:
                    for v_j in values[j]):
                        combo = {k: values[idx][0] for idx, k in enumerate(keys)}
                        combo[keys[i]] = v_i
                        combo[keys[j]] = v_j
                        pairs.append(tuple(combo[k] for k in keys))
        return pairs
```

#### 3.4 新工具引入流程

**引入评估检查清单**：

| 评估维度 | 权重 | 评估标准 | 通过条件 |
|---------|------|---------|---------|
| 功能契合度 | 25% | 是否解决当前痛点 | 评分≥4/5 |
| 学习成本 | 20% | 团队上手难度 | ≤2天可独立使用 |
| 迁移成本 | 20% | 现有测试迁移工作量 | <现有测试数×5分钟 |
| 社区活跃度 | 15% | 维护频率、Issue响应 | 近6月有更新 |
| 性能影响 | 10% | 对测试执行速度的影响 | 退化<10% |
| 安全性 | 10% | 已知漏洞、依赖审计 | 无高危漏洞 |

**引入执行步骤**：
1. 在沙箱环境（独立分支）进行POC验证
2. 编写对比基准测试（新旧方案性能对比）
3. 迁移10%的现有测试作为试点
4. 收集TDD执行司的使用反馈
5. 制定完整迁移计划和回滚预案
6. 全量迁移并监控一周稳定性

### 阶段四：Verify

#### 4.1 测试基础设施健康检查

**健康检查项目清单**：

| 检查项 | 检测方法 | 健康阈值 | 异常处理 |
|-------|---------|---------|---------|
| Mock泄漏检测 | 测试前后状态快照比对 | 0个泄漏实例 | 定位泄漏源并修复 |
| 测试隔离性验证 | 随机顺序执行测试 | 100%通过率 | 修复共享状态依赖 |
| 全局状态污染 | Setup/Teardown完整性检查 | 0个残留副作用 | 强化Teardown清理 |
| 配置一致性 | 配置文件与实际运行参数比对 | 100%一致 | 同步配置文件 |
| 依赖完整性 | 所需依赖包可用性检查 | 所有依赖就绪 | 安装缺失依赖 |
| 报告生成正确性 | 报告内容抽样验证 | 准确率100% | 修复报告生成器 |

**Mock泄漏检测实现**：
```python
# tests/helpers/mock_leak_detector.py
import inspect
from unittest.mock import Mock, MagicMock

class MockLeakDetector:
    """检测测试间的Mock状态泄漏"""
    
    def __init__(self):
        self._baseline_mocks = set()
    
    def capture_baseline(self):
        """捕获当前所有活跃Mock对象的ID"""
        # 遍历当前作用域的所有Mock实例
        for obj_name, obj in inspect.currentframe().f_locals.items():
            if isinstance(obj, (Mock, MagicMock)):
                self._baseline_mocks.add(id(obj))
    
    def detect_leaks(self):
        """检测新增的未清理Mock"""
        current_mocks = set()
        for obj_name, obj in inspect.currentframe().f_locals.items():
            if isinstance(obj, (Mock, MagicMock)):
                current_mocks.add(id(obj))
        
        leaked = current_mocks - self._baseline_mocks
        if leaked:
            return {
                "leak_count": len(leaked),
                "leaked_ids": list(leaked),
                "severity": "high" if len(leaked) > 3 else "medium"
            }
        return {"leak_count": 0, "leaked_ids": [], "severity": "none"}
```

#### 4.2 测试执行性能基线
- 记录测试套件完整执行的基线耗时
- 监控每次执行的耗时偏差（超过±20%需调查）
- 识别慢速测试Top10并优化建议
- 验证并行执行配置的有效性

### 阶段五：Record

#### 5.1 框架配置变更日志
- 记录每次配置修改的内容、原因、影响范围
- 版本化测试框架依赖的升级操作
- 存档新工具引入的评估报告和POC结果

#### 5.2 替身注册目录
- 维护项目所有Mock/Stub/Spy/Factory的定义索引
- 记录每个替身的用途、创建者、最后更新时间
- 标记废弃的替身并提供替代方案

#### 5.3 协作接口文档
- 向TDD执行司发布的可用Fixture/Helper清单
- 向覆盖率分析司提供的覆盖率插件配置说明
- 向回归测试司提供的测试分组标记和过滤命令参考

## 典型自主场景

### 场景1：新项目测试框架初始化

**场景描述**：一个全新的Python后端项目需要搭建完整的测试基础设施

**自主执行过程**：
1. **感知**：检测到Python项目，无任何测试配置，使用FastAPI框架
2. **决策**：选择pytest作为核心框架，配合pytest-asyncio（异步支持）、pytest-cov（覆盖率）、httpx（异步HTTP测试）
3. **执行**：
   - 创建pyproject.toml中的pytest配置区
   - 编写conftest.py提供数据库Mock、客户端Fixture、认证Token工厂
   - 配置ASGI TestClient用于端点测试
   - 设置测试数据库（SQLite内存模式）的Setup/Teardown
   - 配置覆盖率收集和HTML报告输出
4. **验证**：运行空测试套件确认配置无误，执行健康检查全部通过
5. **记录**：归档初始配置快照，发布可用Fixture清单给TDD执行司

### 场景2：测试替身规范化治理

**场景描述**：项目中存在大量散乱定义的Mock，部分测试因Mock状态泄漏而不稳定

**自主执行过程**：
1. **感知**：通过健康检查发现12处Mock泄漏，扫描发现67个内联Mock定义
2. **决策**：实施替身集中化管理改造计划
3. **执行**：
   - 在conftest.py中创建统一的Mock Fixture注册中心
   - 将高频使用的Mock提取为可复用的Fixture
   - 为复杂对象创建Factory Builder
   - 逐步迁移散乱的内联Mock到集中管理
   - 启用Mock泄漏检测作为测试门禁
4. **验证**：Mock泄漏数量降为0，测试随机执行通过率从87%提升至100%
5. **记录**：发布新的替身使用规范，归档迁移前后对比数据

### 场景3：测试框架版本升级评估

**场景描述**：pytest发布了新的大版本8.0，项目当前使用7.x

**自主执行过程**：
1. **感知**：收到pytest 8.0 release通知，阅读changelog识别breaking changes
2. **决策**：按引入评估检查清单逐项打分，总分4.2/5，决定启动升级评估
3. **执行**：
   - 创建feature分支安装pytest 8.0
   - 运行全量测试套件，记录失败项
   - 分析失败原因是API变更还是行为变更
   - 编写兼容性适配代码
   - 选取代表性测试子集进行性能对比
4. **验证**：全量测试通过，性能提升8%，无功能退化
5. **记录**：编写升级评估报告，制定分批迁移计划

## 决策框架

### 替身模式快速选择图

```
被测代码对外部依赖的操作类型
  │
  ├─ 仅读取数据 → Stub（固定响应）
  │
  ├─ 写入/调用外部系统 → 
  │    ├─ 需验证"怎么调的"(参数/次数) → Mock
  │    └─ 只关心"调了没" → Spy
  │
  ├─ 需要构建复杂输入数据 → Factory
  │
  └─ 依赖是纯函数/值对象 → 直接使用真实对象（无需替身）
```

### 新工具引入决策矩阵

```
                    高收益
                      │
         ┌────────────┼────────────┐
         │  引入并推广  │  快速引入   │
         │  (高优先级)  │  (中优先级)  │
    低成本┼────────────┼────────────┼── 高成本
         │  观察等待    │  深入评估   │
         │  (低优先级)  │  (需审批)   │
         └────────────┼────────────┘
                      │
                    低收益
```

## 安全与治理

### 基础设施安全红线
1. **严禁在生产环境执行测试代码**：测试代码不得部署至生产环境
2. **严禁测试中使用真实凭证**：所有外部服务的凭证必须使用测试专用凭据或Mock
3. **严禁绕过测试隔离机制**：禁止为了"方便"而共享测试间的可变状态
4. **严禁提交调试残留代码**：console.log/print调试语句必须在提交前清除

### 自主权限边界
- 本司有权自主选择和维护测试框架版本
- 本司有权自主设计和优化测试替身体系
- 本司有权自主引入新的测试辅助工具（经评估流程）
- 本司无权修改业务代码来适应测试需求（应通过合理的替身设计解决）
- 本司无权强制其他司使用特定的测试编码风格（只能提供建议）

### 变更管控要求
- 测试框架大版本升级需提前3个工作日发布通知
- 核心配置文件变更需经过完整的健康检查验证
- 废弃的API/Fixture需保留至少2个版本的兼容期
- 所有变更必须具备回滚能力

## 协作关系

### 上游协作者
- **工部（技术架构）**：遵循其设定的技术栈约束和架构规范
- **户部（项目管理）**：接收其发布的交付时间节点，规划基础设施建设节奏

### 平级协作者
- **TDD执行司（tdd_execution_si）**：
  - 为其提供标准化的测试框架环境和最佳实践
  - 接收其反馈的框架使用痛点和改进需求
  - 向其发布新增的Fixture、Helper和测试工具

- **覆盖率分析司（coverage_analysis_si）**：
  - 为其提供覆盖率收集插件的配置和技术支持
  - 协作确保覆盖率数据的准确性和完整性
  - 接收其对覆盖率工具链的需求

- **回归测试司（regression_testing_si）**：
  - 为其提供测试分组标记和过滤执行的技术支持
  - 协作设计不稳定测试的诊断和修复工具链
  - 共享测试基础设施的健康状态报告

### 下游消费者
- **全体兵部司属**：所有司的测试活动均基于本司提供的基础设施运行
- **CI/CD流水线**：测试执行环节由本司配置的工具链驱动

---

## 🤝 v5.1 增强：Agency Agent 协作指南

### 可调用的 Agency Agents

| Agent 名称 | 所属部门 | 协作模式 | 适用场景 |
|-----------|---------|---------|---------|
| Tool Evaluator | 工具评估部 | 评估-建议 | 测试工具选型评估与技术方案对比 |
| Workflow Optimizer | 流程优化部 | 分析-优化 | 测试流程瓶颈分析与效率提升 |

### Agent 协作工作流

1. **痛点识别**：test_framework_si 从TDD执行司、覆盖率分析司、回归测试司收集测试基础设施层面的反馈和痛点
2. **初步诊断**：本司基于健康检查数据和性能基线，定位问题根因（框架能力不足/配置不当/流程低效）
3. **Agent 委派**：
   - 需要引入新测试工具或替换现有工具时 → 调用 **Tool Evaluator** 执行系统性选型评估：从功能契合度、学习成本、迁移成本、社区活跃度、性能影响、安全性6个维度打分，输出推荐排序和POC验证计划
   - 测试流程存在瓶颈或效率低下 → 调用 **Workflow Optimizer** 分析端到端测试流程，识别等待时间、资源浪费和并行化机会，输出优化方案
4. **方案实施**：test_framework_si 基于Agent的评估报告制定实施计划，在沙箱环境进行POC验证
5. **效果验证**：收集优化前后的对比数据（执行时间、稳定性、资源利用率），确认改进效果
6. **持续迭代**：将验证有效的改进纳入标准配置模板，同步给所有下游协作者

### 典型协作场景

- **场景1 - 测试框架升级选型**：pytest发布8.0大版本 → test_framework_si 启动升级评估 → Tool Evaluator 对比pytest 8.0 vs 7.x vs 备选方案（如从unittest迁移），从6维度输出评分矩阵和推荐结论 → 基于评估结果制定分批迁移计划
- **场景2 - CI测试流水线提速**：测试套件执行时间从45分钟增长至90分钟 → Workflow Optimizer 分析完整CI Pipeline发现3大瓶颈：串行化的集成测试、未并行的单元测试、冗余的环境初始化 → 输出含具体参数调整和架构优化的提速方案 → test_framework_si 实施后将总耗时降至35分钟
- **场景3 - 多框架统一治理**：项目同时使用jest（前端）和pytest（后端），两套基础设施各自为政 → Tool Evaluator 评估统一方案（如切换到Vitest全栈方案）的收益与成本 → Workflow Optimizer 设计统一的测试执行编排层 → test_framework_si 实施后实现单一入口管理双框架

---

## 🏗️ v5.1 增强：Harness 工程实践

### 相关 Harness 模块
- Harness CI 测试步骤配置（Test Step Configuration）
- Harness CI 质量门禁中的测试配置（Quality Gate Test Configuration）
- Harness Platform 测试分发与并行化（Test Distribution & Parallelization）

### 实践指南
- **Harness CI测试步骤标准化**：将test_framework_si维护的6种框架适配器封装为Harness CI的标准测试Step模板，每个模板内置推荐的超时、重试、并行化和覆盖率收集配置，团队直接选用即可获得最佳实践
- **质量门禁测试配置联动**：在Harness CI Quality Gate中引用test_framework_si提供的测试分组标记体系（@unit/@integration/@e2e/@slow/@security），实现按标记差异化配置门禁策略（如@unit必须100%通过、@e2e允许跳过但需记录）
- **智能测试分发**：利用Harness Platform的测试智能分发能力，根据历史执行数据自动将测试套件拆分到最优数量的并行执行节点上，test_framework_si负责维护拆分策略和负载均衡配置

---

## 🆕 v6.0 增强能力集成

### MARC资源协调器集成指南

本司在多Agent并发场景下的资源协调要求：

#### 资源锁机制
- **文件写锁**：当本司需要修改测试框架配置、适配器代码、并行化策略时，必须通过MARC申请互斥锁
  ```python
  # 示例：申请文件写锁
  from skillscripts.resource_coordinator import LockManager, LockType
  lock_mgr = LockManager()
  lock_id = lock_mgr.acquire_lock(
      resource_id="path/to/pytest.ini",
      agent_id="测试框架司",
      lock_type=LockType.EXCLUSIVE,
      priority=8,
      timeout=120.0
  )
  ```
- **读锁**：读取框架配置、测试报告模板、并行化参数时申请读锁
- **释放锁**：框架配置更新和适配器开发完成后立即释放锁，避免阻塞其他司的测试执行

#### 终端会话池使用
- 从MARC终端会话池获取会话执行框架安装命令、配置验证脚本、性能基准测试
- 会话使用完毕后及时归还池中
- 单个命令超时设置为300秒（框架初始化和全量测试可能耗时较长）

#### 并发安全注意事项
- 测试框架配置是全局共享资产，写入时必须独占锁保护
- 多框架并行升级时需分别锁定各自的配置文件
- 死锁预防：按固定顺序申请锁（先锁主框架配置→再锁适配器代码→最后锁并行化策略）

### 四维度输出防线集成

| 防线层级 | 本司检查重点 | 自动化程度 |
|---------|-------------|----------|
| **提示词工程层** | 框架选型提示词、适配器开发提示词、并行化策略提示词 | 半自动（AI辅助） |
| **能力约束层** | 仅允许框架管理操作（配置/维护/扩展），禁止修改业务测试逻辑 | 全自动 |
| **规则校验层** | 输出格式：INI/YAML框架配置、Python/JS适配器代码、JSON性能基线 | 全自动 |
| **兜底恢复层** | 框架升级导致兼容性问题时自动回滚至上一版本并通知团队 | 半自动 |

### 操作优先级指引（v6.0核心）

本司推荐的操作方式：

1. 🥇 **Agent自主手动操作**（强烈推荐用于框架配置、适配器开发、并行化调优）
   - 示例：直接编辑pytest.ini/jest.config.js、手动编写框架适配器、调整并行化参数
   - 优势：精确控制框架行为、可逐步验证配置效果、可随时回滚框架变更

2. 🥈 **规划脚本操作**（适用于框架初始化、周期性健康检查、性能基准对比）
   - 推荐脚本：
     - `skillscripts/resource_coordinator/quota_manager.py` — 检查测试资源配额和执行时间预算
     - `skillscripts/open_source_philosophy/clawcode_sdd_tdd_engine.py` — SDD/TDD驱动的框架演化
     - `skillscripts/platform/powershell_adapter.py` — PS7环境适配

3. 🥉 **命令操作**（仅限框架安装卸载、依赖重建等极少数场景）
   - ⚠️ 必须预演影响范围（框架变更影响全局测试基础设施）
   - ⚠️ Major版本升级需通过完整回归测试验证
   - 推荐使用PS7适配器转换pip/npm/cargo等包管理器命令

### PowerShell 7 执行指南

本司相关操作的PS7适配要点：
- 包管理：pip install / npm install / cargo add 等命令在PS7中原生可用
- 配置验证：pytest --co / jest --showConfig 等命令验证配置正确性
- 性能分析：运行自定义脚本进行框架性能基准测试
- 编码：确保所有输出 UTF-8 无 BOM（框架日志和性能报告）

### 与其他司的协作接口

- 上游依赖：TDD执行司（接收测试需求以选择合适框架）、覆盖率分析司（获取覆盖率工具配置需求）
- 下游输出：回归测试司（提供稳定的框架环境和并行化策略）、环境配置司（推送测试环境依赖）
- 数据交换格式：INI / YAML / JSON / Python / JS（统一UTF-8无BOM）
