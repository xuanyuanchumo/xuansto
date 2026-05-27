# 测试指南参考文档

> 版本: 1.0.0 | 更新日期: 2026-04-17 | 编码: UTF-8 | 行尾: LF

---

## 目录

1. [测试金字塔](#测试金字塔)
2. [测试命名](#测试命名)
3. [测试组织](#测试组织)
4. [Mock策略](#mock策略)

---

## 测试金字塔

### 金字塔结构

```
                    /\
                   /  \
                  / E2E\        端到端测试 (10%)
                 /------\
                /        \
               /Integration\   集成测试 (20%)
              /------------\
             /              \
            /   Unit Tests   \  单元测试 (70%)
           /------------------\
```

### 测试类型定义

| 类型 | 范围 | 速度 | 数量占比 | 目的 |
|------|------|------|----------|------|
| 单元测试 | 单个函数/类 | 毫秒级 | 70% | 验证最小单元的正确性 |
| 集成测试 | 模块间交互 | 秒级 | 20% | 验证组件协作的正确性 |
| 端到端测试 | 完整流程 | 分钟级 | 10% | 验证用户场景的正确性 |

### 单元测试

**定义**: 测试单个函数、方法或类的行为

**特点**:
- 快速执行
- 无外部依赖
- 隔离测试
- 确定性结果

**适用场景**:
- 纯函数计算
- 工具类方法
- 业务逻辑处理
- 数据转换函数

```javascript
// 单元测试示例
describe('Calculator', () => {
  describe('add', () => {
    it('should return sum of two numbers', () => {
      expect(add(2, 3)).toBe(5);
    });

    it('should handle negative numbers', () => {
      expect(add(-1, -2)).toBe(-3);
    });

    it('should return zero when adding opposites', () => {
      expect(add(5, -5)).toBe(0);
    });
  });
});
```

### 集成测试

**定义**: 测试多个组件协同工作的行为

**特点**:
- 测试真实交互
- 可能涉及数据库
- 可能涉及API调用
- 执行时间较长

**适用场景**:
- 数据库操作
- API集成
- 服务间通信
- 模块接口

```javascript
// 集成测试示例
describe('UserService Integration', () => {
  let db;
  let userService;

  beforeAll(async () => {
    db = await setupTestDatabase();
    userService = new UserService(db);
  });

  afterAll(async () => {
    await teardownTestDatabase(db);
  });

  it('should create and retrieve user', async () => {
    const userData = { name: 'Test User', email: 'test@example.com' };
    const created = await userService.create(userData);
    
    const found = await userService.findById(created.id);
    
    expect(found.name).toBe(userData.name);
    expect(found.email).toBe(userData.email);
  });
});
```

### 端到端测试

**定义**: 模拟真实用户操作流程的测试

**特点**:
- 最接近用户体验
- 执行最慢
- 维护成本高
- 环境依赖强

**适用场景**:
- 关键业务流程
- 用户登录注册
- 支付流程
- 核心功能验证

```javascript
// E2E测试示例 (Playwright)
describe('User Registration Flow', () => {
  it('should complete registration successfully', async () => {
    await page.goto('/register');
    
    await page.fill('[name="email"]', 'newuser@example.com');
    await page.fill('[name="password"]', 'SecurePass123!');
    await page.fill('[name="confirmPassword"]', 'SecurePass123!');
    
    await page.click('button[type="submit"]');
    
    await expect(page.locator('.success-message')).toBeVisible();
    await expect(page).toHaveURL('/dashboard');
  });
});
```

---

## 测试命名

### 命名原则

- **描述性**: 测试名称应清楚描述测试内容
- **一致性**: 项目内保持命名风格统一
- **可读性**: 测试名称应能作为文档阅读

### 测试文件命名

| 测试类型 | 命名模式 | 示例 |
|----------|----------|------|
| 单元测试 | `{filename}.test.{ext}` | `user-service.test.ts` |
| 集成测试 | `{filename}.integration.test.{ext}` | `api.integration.test.ts` |
| E2E测试 | `{feature}.e2e.test.{ext}` | `login.e2e.test.ts` |
| 规范测试 | `{filename}.spec.{ext}` | `config.spec.ts` |

### 测试套件命名

```javascript
// 使用describe组织测试套件
describe('UserService', () => {
  describe('create', () => {
    // 测试创建用户的各种场景
  });

  describe('update', () => {
    // 测试更新用户的各种场景
  });

  describe('delete', () => {
    // 测试删除用户的各种场景
  });
});
```

### 测试用例命名

**推荐格式**: `should {expected behavior} when {condition}`

```javascript
describe('Calculator', () => {
  describe('divide', () => {
    it('should return quotient when dividing two numbers', () => {
      expect(divide(10, 2)).toBe(5);
    });

    it('should throw error when dividing by zero', () => {
      expect(() => divide(10, 0)).toThrow('Division by zero');
    });

    it('should return decimal when result is not integer', () => {
      expect(divide(7, 2)).toBe(3.5);
    });
  });
});
```

### 中文命名示例

```javascript
describe('用户服务', () => {
  describe('创建用户', () => {
    it('应当成功创建用户当提供有效数据时', async () => {
      // ...
    });

    it('应当抛出验证错误当邮箱格式无效时', async () => {
      // ...
    });

    it('应当抛出重复错误当邮箱已存在时', async () => {
      // ...
    });
  });
});
```

---

## 测试组织

### 目录结构

```
project/
├── src/
│   ├── services/
│   │   ├── user.service.ts
│   │   └── order.service.ts
│   └── utils/
│       └── date.util.ts
├── tests/
│   ├── unit/
│   │   ├── services/
│   │   │   ├── user.service.test.ts
│   │   │   └── order.service.test.ts
│   │   └── utils/
│   │       └── date.util.test.ts
│   ├── integration/
│   │   ├── api/
│   │   │   └── user-api.integration.test.ts
│   │   └── database/
│   │       └── user-repo.integration.test.ts
│   ├── e2e/
│   │   ├── auth.e2e.test.ts
│   │   └── order.e2e.test.ts
│   ├── fixtures/
│   │   ├── users.fixture.ts
│   │   └── orders.fixture.ts
│   ├── helpers/
│   │   ├── db-helper.ts
│   │   └── api-helper.ts
│   └── setup/
│       ├── jest.setup.ts
│       └── global-setup.ts
└── jest.config.js
```

### AAA模式

**Arrange-Act-Assert** 模式是组织测试代码的标准方式:

```javascript
it('should calculate total with discount', () => {
  // Arrange (准备)
  const items = [
    { price: 100, quantity: 2 },
    { price: 50, quantity: 1 }
  ];
  const discount = 0.1;

  // Act (执行)
  const total = calculateTotal(items, discount);

  // Assert (断言)
  expect(total).toBe(225);
});
```

### Given-When-Then模式

适用于BDD风格测试:

```javascript
it('should send notification when order is placed', async () => {
  // Given (给定)
  const user = await createTestUser();
  const order = createTestOrder({ userId: user.id });

  // When (当)
  await processOrder(order);

  // Then (那么)
  const notifications = await getNotifications(user.id);
  expect(notifications).toHaveLength(1);
  expect(notifications[0].type).toBe('ORDER_CONFIRMED');
});
```

### 测试夹具(Fixtures)

```javascript
// tests/fixtures/users.fixture.ts
export const createTestUser = (overrides = {}) => ({
  id: 'user-123',
  name: 'Test User',
  email: 'test@example.com',
  role: 'user',
  createdAt: new Date('2026-01-01'),
  ...overrides
});

export const createTestAdmin = (overrides = {}) => 
  createTestUser({ role: 'admin', ...overrides });

// 使用
import { createTestUser, createTestAdmin } from '../fixtures/users.fixture';

it('should allow admin to delete users', async () => {
  const admin = createTestAdmin();
  const user = createTestUser({ id: 'user-to-delete' });
  
  // 测试逻辑...
});
```

### 测试辅助函数

```javascript
// tests/helpers/db-helper.ts
export class DatabaseHelper {
  private connection;

  async connect() {
    this.connection = await createConnection({
      host: process.env.TEST_DB_HOST,
      database: 'test_db'
    });
    return this.connection;
  }

  async cleanup() {
    await this.connection.query('TRUNCATE TABLE users CASCADE');
  }

  async disconnect() {
    await this.connection.close();
  }

  async seed(data) {
    for (const table of Object.keys(data)) {
      await this.connection.query(
        `INSERT INTO ${table} VALUES ?`,
        [data[table]]
      );
    }
  }
}
```

---

## Mock策略

### Mock原则

| 原则 | 说明 |
|------|------|
| 隔离外部依赖 | 数据库、API、文件系统等应Mock |
| 不Mock被测代码 | 被测单元应使用真实实现 |
| 保持Mock简单 | Mock只返回必要的数据 |
| 验证交互 | 必要时验证方法调用 |

### 函数Mock

```javascript
// Jest函数Mock
const mockCallback = jest.fn();

// 指定返回值
mockCallback.mockReturnValue(42);

// 指定异步返回值
mockCallback.mockResolvedValue({ data: 'success' });

// 指定实现
mockCallback.mockImplementation((x) => x * 2);

// 验证调用
expect(mockCallback).toHaveBeenCalled();
expect(mockCallback).toHaveBeenCalledWith('arg1', 'arg2');
expect(mockCallback).toHaveBeenCalledTimes(3);
```

### 模块Mock

```javascript
// 完全Mock模块
jest.mock('../services/email-service', () => ({
  sendEmail: jest.fn().mockResolvedValue({ success: true }),
  validateEmail: jest.fn().mockReturnValue(true)
}));

// 部分Mock模块
jest.mock('../services/user-service', () => {
  const actual = jest.requireActual('../services/user-service');
  return {
    ...actual,
    sendNotification: jest.fn() // 只Mock这个方法
  };
});
```

### 类Mock

```javascript
// Mock类
class MockDatabase {
  constructor() {
    this.query = jest.fn();
    this.connect = jest.fn().mockResolvedValue(this);
  }
}

// 使用
const db = new MockDatabase();
db.query.mockResolvedValue([{ id: 1, name: 'Test' }]);

const repository = new UserRepository(db);
const users = await repository.findAll();

expect(db.query).toHaveBeenCalledWith('SELECT * FROM users');
```

### 定时器Mock

```javascript
describe('Timer functions', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('should call callback after delay', () => {
    const callback = jest.fn();
    setTimeout(callback, 1000);

    jest.advanceTimersByTime(1000);

    expect(callback).toHaveBeenCalled();
  });

  it('should handle recurring timer', () => {
    const callback = jest.fn();
    setInterval(callback, 100);

    jest.advanceTimersByTime(350);

    expect(callback).toHaveBeenCalledTimes(3);
  });
});
```

### API Mock

```javascript
// 使用MSW (Mock Service Worker)
import { setupServer } from 'msw/node';
import { rest } from 'msw';

const server = setupServer(
  rest.get('/api/users/:id', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({ id: req.params.id, name: 'Test User' })
    );
  }),

  rest.post('/api/users', (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({ id: 'new-user', ...req.body })
    );
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// 测试中使用真实API调用
it('should fetch user', async () => {
  const user = await fetchUser('user-123');
  expect(user.name).toBe('Test User');
});
```

### 数据库Mock

```javascript
// 使用内存数据库
import { createConnection, Connection } from 'typeorm';
import { SqliteConnectionOptions } from 'typeorm/driver/sqlite/SqliteConnectionOptions';

export async function createTestConnection(): Promise<Connection> {
  return createConnection({
    type: 'sqlite',
    database: ':memory:',
    entities: [__dirname + '/../entities/*.ts'],
    synchronize: true,
    dropSchema: true
  } as SqliteConnectionOptions);
}

// 测试中使用
describe('UserRepository', () => {
  let connection: Connection;
  let repository: UserRepository;

  beforeAll(async () => {
    connection = await createTestConnection();
    repository = new UserRepository(connection);
  });

  afterAll(async () => {
    await connection.close();
  });

  it('should save user', async () => {
    const user = await repository.save({ name: 'Test' });
    expect(user.id).toBeDefined();
  });
});
```

---

## 测试覆盖率

### 覆盖率目标

| 类型 | 目标 | 说明 |
|------|------|------|
| 行覆盖率 | ≥80% | 执行的代码行比例 |
| 分支覆盖率 | ≥75% | 执行的分支比例 |
| 函数覆盖率 | ≥85% | 执行的函数比例 |
| 语句覆盖率 | ≥80% | 执行的语句比例 |

### 覆盖率配置

```javascript
// jest.config.js
module.exports = {
  coverageThreshold: {
    global: {
      branches: 75,
      functions: 85,
      lines: 80,
      statements: 80
    },
    './src/services/': {
      branches: 90,
      functions: 95,
      lines: 90
    }
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/index.ts',
    '!src/types/**'
  ]
};
```

---

## 最佳实践

### 测试原则

1. **FIRST原则**
   - **F**ast: 测试要快
   - **I**ndependent: 测试要独立
   - **R**epeatable: 测试要可重复
   - **S**elf-validating: 测试要自验证
   - **T**imely: 测试要及时

2. **单一职责**: 每个测试只验证一个行为

3. **边界测试**: 测试边界条件和异常情况

4. **可读性**: 测试代码要和生产代码一样整洁

### 避免的反模式

```javascript
// ❌ 测试多个行为
it('should validate and save user', async () => {
  const user = { email: 'invalid' };
  await expect(service.save(user)).rejects.toThrow();
  // 然后又测试成功场景...
});

// ✅ 分离测试
it('should throw error for invalid email', async () => {
  const user = { email: 'invalid' };
  await expect(service.save(user)).rejects.toThrow('Invalid email');
});

it('should save valid user', async () => {
  const user = { email: 'valid@example.com' };
  const saved = await service.save(user);
  expect(saved.id).toBeDefined();
});

// ❌ 测试实现细节
it('should call internal method', () => {
  service.process();
  expect(service['internalMethod']).toHaveBeenCalled();
});

// ✅ 测试行为结果
it('should process data correctly', () => {
  const result = service.process({ value: 10 });
  expect(result).toBe(20);
});
```

---

## 参考资料

- [Testing JavaScript by Kent C. Dodds](https://testingjavascript.com/)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Testing Library](https://testing-library.com/)
- [Microsoft Playwright](https://playwright.dev/)
- [Mock Service Worker](https://mswjs.io/)

---

> 本文档由 Multi-Agent SDD/TDD Orchestrator 维护 | 最后更新: 2026-04-17
