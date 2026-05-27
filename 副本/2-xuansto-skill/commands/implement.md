---
name: /implement
aliases:
  - i
  - impl
category: workflow
description: TDD实现与代码编写
trigger: 需要编写代码实现功能时
---

# /implement 命令

## 命令描述

执行TDD（测试驱动开发）实施阶段，按照红-绿-重构循环进行代码开发。该命令是SDD+TDD流程的核心实现环节，确保代码质量和测试覆盖率。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/implement` |
| 关键词触发 | 用户提及"TDD实现"、"代码实现"、"开发实现" |
| 自动触发 | `/sprint` 命令执行时自动调用Implement阶段 |
| 流程触发 | `/design` 完成后自动进入Implement阶段 |

## 命令名称与语法

```
/implement [--task=<任务ID>] [--mode=<模式>] [--coverage=<覆盖率>]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--task` | string | 否 | all | 指定任务ID，多个用逗号分隔 |
| `--mode` | enum | 否 | tdd | 开发模式：tdd/standard/rapid |
| `--coverage` | int | 否 | 80 | 最低测试覆盖率要求 |
| `--watch` | flag | 否 | false | 监听模式，文件变化自动运行测试 |
| `--parallel` | flag | 否 | true | 并行执行测试 |
| `--bail` | flag | 否 | false | 首个测试失败即停止 |
| `--update-snapshot` | flag | 否 | false | 更新快照测试 |

## 执行流程

> 标准四步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证

```
┌─────────────────────────────────────────────────────────────┐
│                    TDD实施流程                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐                                          │
│  │  加载任务     │                                          │
│  └──────┬───────┘                                          │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────┐          │
│  │              TDD 红-绿-重构循环               │          │
│  │                                              │          │
│  │    ┌─────────┐                              │          │
│  │    │   RED   │ 编写失败的测试                │          │
│  │    │  🔴     │                              │          │
│  │    └────┬────┘                              │          │
│  │         │                                   │          │
│  │         ▼                                   │          │
│  │    ┌─────────┐                              │          │
│  │    │  GREEN  │ 编写最少代码使测试通过        │          │
│  │    │  🟢     │                              │          │
│  │    └────┬────┘                              │          │
│  │         │                                   │          │
│  │         ▼                                   │          │
│  │    ┌─────────┐                              │          │
│  │    │REFACTOR │ 重构代码，优化结构            │          │
│  │    │  🔵     │                              │          │
│  │    └────┬────┘                              │          │
│  │         │                                   │          │
│  │         └────────────┐                      │          │
│  │                      │                      │          │
│  │         ┌────────────▼────────────┐        │          │
│  │         │     所有功能完成？       │        │          │
│  │         └────────────┬────────────┘        │          │
│  │                      │                      │          │
│  │            ┌────────┴────────┐             │          │
│  │            │ 否              │ 是          │          │
│  │            ▼                 ▼             │          │
│  │      返回RED           ┌──────────┐        │          │
│  │                        │  完成     │        │          │
│  │                        └──────────┘        │          │
│  └──────────────────────────────────────────────┘          │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐                      │
│  │  代码审查     │───▶│  输出产物     │                      │
│  └──────────────┘    └──────────────┘                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### TDD循环详解

1. **RED（红灯阶段）**
   - 分析需求，确定测试用例
   - 编写失败的测试代码
   - 运行测试确认失败
   - 记录预期行为

2. **GREEN（绿灯阶段）**
   - 编写最少代码使测试通过
   - 不追求完美，先通过测试
   - 确认测试通过
   - 提交可工作代码

3. **REFACTOR（重构阶段）**
   - 优化代码结构
   - 消除重复代码
   - 提高可读性
   - 确保测试仍然通过

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| fullstack-engineer | 主导 | 核心代码实现 |
| backend-developer | 辅助 | 后端服务开发 |
| frontend-developer | 辅助 | 前端界面开发 |
| unit-tester | 辅助 | 测试用例编写 |
| code-reviewer | 辅助 | 代码质量审查 |
| database-engineer | 辅助 | 数据层实现 |
| desktop-developer | 辅助 | 桌面应用核心开发 |
| desktop-ui-adapter | 辅助 | 桌面端UI适配与交互 |

## 输出格式

### 代码结构

```
src/
├── modules/
│   └── user/
│       ├── user.module.ts
│       ├── user.controller.ts
│       ├── user.service.ts
│       ├── user.repository.ts
│       ├── dto/
│       │   ├── create-user.dto.ts
│       │   └── update-user.dto.ts
│       ├── entities/
│       │   └── user.entity.ts
│       └── __tests__/
│           ├── user.controller.spec.ts
│           ├── user.service.spec.ts
│           └── user.repository.spec.ts
├── common/
│   ├── decorators/
│   ├── filters/
│   ├── guards/
│   ├── interceptors/
│   └── pipes/
└── config/
    └── configuration.ts
```

### 测试文件示例

```typescript
import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { UserService } from './user.service';
import { UserRepository } from './user.repository';

describe('UserService', () => {
  let service: UserService;
  let repository: jest.Mocked<UserRepository>;

  beforeEach(() => {
    repository = {
      findById: jest.fn(),
      findByEmail: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      delete: jest.fn(),
    } as any;
    service = new UserService(repository);
  });

  describe('createUser', () => {
    it('应该成功创建用户', async () => {
      const dto = {
        email: 'test@example.com',
        password: 'Password123!',
        name: 'Test User',
      };

      repository.findByEmail.mockResolvedValue(null);
      repository.create.mockResolvedValue({
        id: 'user-1',
        ...dto,
        password: 'hashed-password',
        status: 'active',
        createdAt: new Date(),
      });

      const result = await service.createUser(dto);

      expect(result.email).toBe(dto.email);
      expect(result.name).toBe(dto.name);
      expect(repository.findByEmail).toHaveBeenCalledWith(dto.email);
      expect(repository.create).toHaveBeenCalled();
    });

    it('邮箱已存在时应该抛出错误', async () => {
      const dto = {
        email: 'existing@example.com',
        password: 'Password123!',
      };

      repository.findByEmail.mockResolvedValue({
        id: 'existing-user',
        email: dto.email,
      } as any);

      await expect(service.createUser(dto)).rejects.toThrow('邮箱已被注册');
    });

    it('密码不符合要求时应该抛出错误', async () => {
      const dto = {
        email: 'test@example.com',
        password: 'weak',
      };

      await expect(service.createUser(dto)).rejects.toThrow('密码强度不足');
    });
  });

  describe('getUserById', () => {
    it('应该返回用户信息', async () => {
      const mockUser = {
        id: 'user-1',
        email: 'test@example.com',
        name: 'Test User',
      };

      repository.findById.mockResolvedValue(mockUser as any);

      const result = await service.getUserById('user-1');

      expect(result).toEqual(mockUser);
    });

    it('用户不存在时应该抛出错误', async () => {
      repository.findById.mockResolvedValue(null);

      await expect(service.getUserById('non-existent')).rejects.toThrow('用户不存在');
    });
  });
});
```

### 实现代码示例

```typescript
import { Injectable, ConflictException, NotFoundException } from '@nestjs/common';
import { UserRepository } from './user.repository';
import { CreateUserDto, UpdateUserDto } from './dto';
import * as bcrypt from 'bcrypt';

@Injectable()
export class UserService {
  private readonly PASSWORD_MIN_LENGTH = 8;

  constructor(private readonly repository: UserRepository) {}

  async createUser(dto: CreateUserDto) {
    await this.validateEmailUnique(dto.email);
    this.validatePasswordStrength(dto.password);

    const hashedPassword = await bcrypt.hash(dto.password, 10);

    return this.repository.create({
      ...dto,
      password: hashedPassword,
      status: 'active',
    });
  }

  async getUserById(id: string) {
    const user = await this.repository.findById(id);
    if (!user) {
      throw new NotFoundException('用户不存在');
    }
    return user;
  }

  async updateUser(id: string, dto: UpdateUserDto) {
    await this.getUserById(id);

    if (dto.email) {
      await this.validateEmailUnique(dto.email, id);
    }

    if (dto.password) {
      this.validatePasswordStrength(dto.password);
      dto.password = await bcrypt.hash(dto.password, 10);
    }

    return this.repository.update(id, dto);
  }

  async deleteUser(id: string) {
    await this.getUserById(id);
    await this.repository.delete(id);
  }

  private async validateEmailUnique(email: string, excludeId?: string) {
    const existing = await this.repository.findByEmail(email);
    if (existing && existing.id !== excludeId) {
      throw new ConflictException('邮箱已被注册');
    }
  }

  private validatePasswordStrength(password: string) {
    if (password.length < this.PASSWORD_MIN_LENGTH) {
      throw new Error('密码强度不足');
    }

    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumber = /[0-9]/.test(password);

    if (!hasUpperCase || !hasLowerCase || !hasNumber) {
      throw new Error('密码强度不足');
    }
  }
}
```

## 测试类型矩阵

| 测试类型 | 覆盖范围 | 执行速度 | 文件命名 |
|----------|----------|----------|----------|
| 单元测试 | 单个函数/类 | 快 | *.spec.ts |
| 集成测试 | 模块间交互 | 中 | *.integration.spec.ts |
| E2E测试 | 完整流程 | 慢 | *.e2e-spec.ts |
| 快照测试 | UI组件 | 快 | *.spec.ts |
| 性能测试 | 性能指标 | 慢 | *.perf.spec.ts |

## 示例用法

### 示例1：执行所有任务

```
/implement
```

### 示例2：执行特定任务

```
/implement --task=T001,T002
```

### 示例3：高覆盖率要求

```
/implement --coverage=95
```

### 示例4：监听模式

```
/implement --watch
```

### 示例5：快速开发模式

```
/implement --mode=rapid --coverage=60
```

## 开发模式说明

### TDD模式（默认）
- 严格的红-绿-重构循环
- 测试先行
- 高代码质量

### Standard模式
- 先实现后测试
- 适合简单功能
- 较快交付

### Rapid模式
- 最小测试覆盖
- 快速原型开发
- 后续补充测试

## 代码审查清单

实现完成后自动检查：

- [ ] 所有测试通过
- [ ] 测试覆盖率达标
- [ ] 无TypeScript错误
- [ ] 无ESLint警告
- [ ] 代码符合规范
- [ ] 无安全漏洞
- [ ] 无硬编码密钥
- [ ] 错误处理完整

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| GATE-007 | BLOCK | TypeScript严格模式通过、ESLint 0错误0警告、代码重复率 < 5%、圈复杂度 < 15 |
| TEST-PASS | BLOCK | 所有测试通过、测试覆盖率 ≥ 设定值 |
| GATE-009 | BLOCK | 代码审查通过、无安全漏洞、无硬编码密钥 |
| FILE-ENCODING | WARN | 所有源文件使用UTF-8编码、无BOM头 |
| COMMENT-LANGUAGE | WARN | 注释使用项目指定语言、无混合语言注释 |
| SCRIPT-SECURITY | BLOCK | 脚本无危险操作、无未授权文件访问、无明文密钥 |
| 指标 | 要求 |
|------|------|
| 测试覆盖率 | ≥ 设定值 |
| TypeScript严格模式 | 通过 |
| ESLint | 0错误，0警告 |
| 代码重复率 | < 5% |
| 圈复杂度 | < 15 |

## 相关命令

- `/test` - 测试执行与验证
- `/spec` - 规格编写
- `/design` - 设计流程
- `/sprint` - 启动完整冲刺
