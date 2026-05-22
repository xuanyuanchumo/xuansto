---
name: ceshi
description: 进行软件测试，包括单元测试、集成测试、E2E 测试。
---
# 测试流程

## 测试类型
1. **单元测试**：测试单个函数/方法
2. **集成测试**：测试模块间交互
3. **E2E 测试**：测试完整业务流程
4. **回归测试**：确保修改不影响现有功能

## 测试流程
1. 分析测试需求
2. 设计测试用例
3. 编写测试代码
4. 执行测试
5. 记录测试结果
6. 报告问题

## 测试目录结构规范

所有项目测试相关文件都放在项目文件夹下新建的 `/tests/` 目录里，具体结构如下：

```
tests/
├── fixtures/                   # 测试夹具
│   ├── backend/                # 后端测试夹具
│   └── frontend/               # 前端测试夹具
├── frontend/                   # 前端测试
│   ├── unit/                   # 前端单元测试
│   └── integration/            # 前端集成测试
├── backend/                    # 后端测试
│   ├── unit/                   # 后端单元测试
│   └── integration/            # 后端集成测试
├── e2e/                        # E2E测试
├── report/                     # 测试最终报告
├── coverage/                   # 覆盖率报告
└── scripts/                    # 测试脚本
```

## 测试夹具管理规范

### 测试夹具概述
测试夹具（Fixtures）是测试中使用的预设数据和配置，用于创建一致的测试环境。

### 夹具存放路径
| 夹具类型 | 存放路径 | 说明 |
|----------|----------|------|
| 后端测试夹具 | `tests/fixtures/backend/` | 数据库数据、API响应等 |
| 前端测试夹具 | `tests/fixtures/frontend/` | Mock数据、测试状态等 |

### 夹具使用示例

#### 后端夹具示例
```python
# tests/fixtures/backend/users.json
[
    {"id": 1, "username": "testuser", "email": "test@example.com"},
    {"id": 2, "username": "admin", "email": "admin@example.com"}
]

# tests/fixtures/backend/database.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="module")
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
```

## 前端夹具示例
```typescript
// tests/fixtures/frontend/mockApi.ts
export const mockUsers = [
    { id: 1, name: 'Test User', email: 'test@example.com' },
    { id: 2, name: 'Admin User', email: 'admin@example.com' }
];

// tests/fixtures/frontend/testStore.ts
import { createStore } from 'vuex';

export const createTestStore = (initialState = {}) => {
    return createStore({
        state: {
            user: null,
            ...initialState
        }
    });
};
```

## 测试脚本使用

测试脚本统一存放在 `tests/scripts/` 目录下：

| 脚本 | 用途 |
|------|------|
| `run_all_tests.py` | 运行所有测试 |
| `run_backend_tests.py` | 运行后端测试 |
| `run_frontend_tests.py` | 运行前端测试 |
| `run_e2e_tests.py` | 运行E2E测试 |
| `generate_coverage_report.py` | 生成覆盖率报告 |

## TDD测试流程

### 红灯-绿灯-重构循环
1. **红灯阶段**：先编写失败的测试用例
2. **绿灯阶段**：编写最少代码使测试通过
3. **重构阶段**：优化代码结构，保持测试通过

### TDD核心原则
- 测试先行，代码后置
- 每次只写一个失败的测试
- 只编写恰好能让测试通过的代码
- 重构时保持测试通过

## 测试先行原则

### 核心理念
- 需求即测试，测试即需求
- 在编写功能代码之前，先编写测试代码
- 测试用例是对需求的最佳诠释

### 实施要点
1. 理解需求后，立即编写测试用例
2. 测试用例应覆盖正常流程和边界条件
3. 测试先行能帮助发现设计问题
4. 测试文档化功能预期行为

## 三种测试类型调用

### 单元测试
- **兵部编写**：兵部负责编写单元测试用例
- **工部执行**：工部负责执行单元测试
- **刑部验证**：刑部负责验证测试结果并确认质量标准

### 集成测试
- **兵部编写**：兵部负责编写集成测试用例
- **工部执行**：工部负责执行集成测试
- **刑部验证**：刑部负责验证模块间交互的正确性

### E2E测试
- **兵部编写**：兵部负责编写端到端测试用例
- **工部执行**：工部负责执行E2E测试
- **门下省审议**：门下省负责审议完整业务流程的测试结果

## 持续测试

### 持续集成中的测试
- 每次代码提交自动触发测试
- 测试失败阻断合并流程
- 测试覆盖率作为质量门禁

### 测试自动化
- 自动化测试脚本维护
- 测试环境自动部署
- 测试结果自动报告

### 测试监控
- 实时监控测试执行状态
- 测试失败即时通知
- 测试趋势分析报告

## 输出物
- 测试计划
- 测试用例
- 测试报告

## 核心测试命令

### 后端测试
```bash
# 运行所有后端测试
pytest tests/ -v

# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

## 前端测试
```bash
# 运行前端测试
npm run test

# 运行覆盖率测试
npm run test:coverage
```

## E2E测试
```bash
# 运行E2E测试
npx playwright test
```

## 测试覆盖率目标

| 测试类型 | 覆盖率目标 |
|----------|------------|
| 单元测试 | ≥ 85% |
| 集成测试 | ≥ 70% |
| 分支覆盖 | ≥ 75% |
| E2E测试 | 覆盖关键路径 |
