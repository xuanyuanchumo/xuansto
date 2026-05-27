# 编码规范参考文档

> 版本: 1.9.0 | 更新日期: 2026-04-17 | 编码: UTF-8 without BOM | 行尾: LF

---

## 目录

1. [命名规范](#命名规范)
2. [代码风格](#代码风格)
3. [注释规范](#注释规范)
   - [注释语言规范](#注释语言规范)
4. [文件编码规范](#文件编码规范)

---

## 命名规范

### 通用原则

- **有意义**: 名称应清晰表达意图，避免缩写
- **一致性**: 同一项目中保持命名风格统一
- **可搜索**: 使用可搜索的名称，避免魔法数字和字符串

### 变量命名

| 类型 | 规范 | 示例 |
|------|------|------|
| 局部变量 | camelCase | `userName`, `itemCount` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT` |
| 私有变量 | _camelCase | `_internalState`, `_cache` |
| 布尔变量 | is/has/can前缀 | `isActive`, `hasPermission`, `canEdit` |

### 函数命名

| 类型 | 规范 | 示例 |
|------|------|------|
| 普通函数 | camelCase | `getUserById()`, `calculateTotal()` |
| 事件处理 | handle前缀 | `handleClick()`, `handleSubmit()` |
| 异步函数 | async后缀或动词 | `fetchUserData()`, `saveAsync()` |
| 工厂函数 | create前缀 | `createUser()`, `createConnection()` |
| 转换函数 | to前缀 | `toString()`, `toJSON()` |

### 类命名

| 类型 | 规范 | 示例 |
|------|------|------|
| 普通类 | PascalCase | `UserService`, `OrderProcessor` |
| 接口 | I前缀(可选)或PascalCase | `IRepository`, `Logger` |
| 抽象类 | Abstract前缀或Base后缀 | `AbstractHandler`, `RepositoryBase` |
| 异常类 | Exception后缀 | `ValidationException`, `NotFoundException` |

### 文件命名

| 类型 | 规范 | 示例 |
|------|------|------|
| 组件文件 | PascalCase | `UserProfile.tsx`, `NavBar.vue` |
| 工具文件 | kebab-case | `date-utils.ts`, `string-helper.js` |
| 配置文件 | kebab-case | `eslint-config.js`, `tsconfig.json` |
| 测试文件 | 源文件名.test | `user-service.test.ts` |

### 数据库命名

| 类型 | 规范 | 示例 |
|------|------|------|
| 表名 | snake_case复数 | `users`, `order_items` |
| 字段名 | snake_case | `created_at`, `user_id` |
| 索引 | idx_表_字段 | `idx_users_email` |
| 外键 | fk_表_引用表 | `fk_orders_users` |

---

## 代码风格

### 缩进与空格

```javascript
// 使用2空格缩进(推荐)或4空格
function example() {
  if (condition) {
    doSomething();
  }
}

// 运算符两侧空格
const result = a + b * c;

// 逗号后空格
const arr = [1, 2, 3];
const obj = { name: 'test', value: 100 };
```

### 大括号风格

```javascript
// 推荐: 同行大括号(K&R风格)
if (condition) {
  doSomething();
} else {
  doOther();
}

// 函数定义
function calculate(a, b) {
  return a + b;
}

// 箭头函数
const add = (a, b) => {
  return a + b;
};

// 单行箭头函数可省略大括号
const double = x => x * 2;
```

### 行长度与换行

```javascript
// 最大行长度: 100-120字符
// 长链式调用换行
const result = users
  .filter(user => user.isActive)
  .map(user => user.name)
  .sort()
  .join(', ');

// 长参数换行
function createOrder(
  customer,
  items,
  shippingAddress,
  paymentMethod
) {
  // ...
}

// 长条件表达式换行
if (
  user.isAuthenticated &&
  user.hasPermission('admin') &&
  !user.isSuspended
) {
  grantAccess();
}
```

### 语句规范

```javascript
// 变量声明: 使用const优先，let次之，避免var
const MAX_SIZE = 100;
let currentIndex = 0;

// 多变量声明分行
const firstName = 'John';
const lastName = 'Doe';

// 避免连续赋值
// 错误: a = b = c = 0;
// 正确:
const c = 0;
const b = c;
const a = b;

// 使用严格相等
if (value === null) { }
if (value !== undefined) { }
```

### 代码组织

```javascript
// 模块导入顺序
// 1. 标准库
import fs from 'fs';
import path from 'path';

// 2. 第三方库
import express from 'express';
import lodash from 'lodash';

// 3. 项目内部模块
import { UserService } from './services';
import { formatDate } from './utils';

// 4. 类型导入(如果有)
import type { User } from './types';

// 类成员顺序
class Example {
  // 1. 静态属性
  static instance = null;
  
  // 2. 实例属性
  private name: string;
  protected count: number;
  
  // 3. 构造函数
  constructor(name: string) {
    this.name = name;
  }
  
  // 4. 公共方法
  public getName(): string {
    return this.name;
  }
  
  // 5. 受保护方法
  protected validate(): boolean {
    return true;
  }
  
  // 6. 私有方法
  private log(): void {
    console.log(this.name);
  }
}
```

---

## 注释规范

### 文件头注释

```javascript
/**
 * @file 用户服务模块
 * @description 提供用户相关的业务逻辑处理
 * @author 开发团队
 * @version 1.0.0
 * @date 2026-04-17
 * @copyright Copyright (c) 2026
 */
```

### 函数注释(JSDoc)

```javascript
/**
 * 根据ID获取用户信息
 * 
 * @param {string} userId - 用户唯一标识符
 * @param {Object} options - 查询选项
 * @param {boolean} options.includeProfile - 是否包含用户档案
 * @returns {Promise<User>} 用户信息对象
 * @throws {NotFoundError} 用户不存在时抛出
 * @throws {DatabaseError} 数据库错误时抛出
 * 
 * @example
 * const user = await getUserById('user-123', { includeProfile: true });
 * console.log(user.name);
 */
async function getUserById(userId, options = {}) {
  // 实现...
}
```

### 类注释

```javascript
/**
 * 用户服务类
 * 
 * 负责处理用户相关的业务逻辑，包括:
 * - 用户注册与登录
 * - 用户信息管理
 * - 权限验证
 * 
 * @class UserService
 * @extends BaseService
 * 
 * @example
 * const service = new UserService();
 * await service.register({ email: 'test@example.com' });
 */
class UserService extends BaseService {
  // ...
}
```

### 行内注释

```javascript
// 单行注释: 解释复杂逻辑
const result = complexCalculation(); // 计算最终得分

// TODO注释: 标记待办事项
// TODO: 添加缓存机制以提升性能
// FIXME: 此处存在内存泄漏问题
// HACK: 临时解决方案，需要重构

// 多行注释: 解释代码块
/*
 * 以下代码实现了以下功能:
 * 1. 验证用户输入
 * 2. 检查权限
 * 3. 执行操作
 */
```

### 注释原则

| 原则 | 说明 |
|------|------|
| 解释为什么 | 注释应解释代码意图，而非代码本身 |
| 保持更新 | 代码修改时同步更新注释 |
| 避免冗余 | 不注释显而易见的代码 |
| 使用标准格式 | 遵循JSDoc/JavaDoc等标准 |
| 标注作者 | 复杂逻辑标注作者便于追踪 |

### 注释语言规范

**质量门禁**: COMMENT-LANGUAGE（WARN初期/BLOCK稳定期）

**强制要求**: 业务注释包含中文说明

**适用范围**: 所有业务逻辑代码

**例外情况**:
- 第三方库接口的注释可使用英文
- 国际标准算法实现的注释可使用英文
- 开源贡献代码遵循目标项目语言规范

**规范细则**:

1. 业务逻辑注释必须包含中文说明，解释"为什么这样做"而非"做了什么"
2. 函数/方法的文档注释（JSDoc/Docstring等）应包含中文的业务含义描述
3. 复杂算法或业务规则的行内注释应使用中文解释核心逻辑
4. 变量/常量的命名使用英文，但首次声明时可附带中文说明
5. TODO/FIXME/HACK等标记注释应使用中文描述待办事项
6. 英文技术术语（如JWT、DTO、Redis、IPC、Electron）可直接使用英文，但解释性语句须用中文。
7. 公开API的文档注释（如JSDoc、Python docstring）建议中英双语（中文描述 + 英文参数名）。纯内部工具函数可仅用中文。

**示例**:

```javascript
// ❌ 不好的实践: 纯英文注释，中文开发者难以快速理解业务含义
// Calculate the discount based on VIP level and purchase history
function applyDiscount(user, order) {
  const discount = user.isVip ? 0.1 : 0;
  return order.total * (1 - discount);
}

// ✅ 好的实践: 业务注释包含中文说明
// 根据VIP等级和购买历史计算折扣金额
function applyDiscount(user, order) {
  const discount = user.isVip ? 0.1 : 0;
  return order.total * (1 - discount);
}
```

```python
# ❌ 不好的实践: 纯英文注释
# Validate user permissions before processing
def check_access(user, resource):
    if user.role not in resource.allowed_roles:
        raise PermissionDenied()

# ✅ 好的实践: 业务注释包含中文说明
# 验证用户是否有权访问指定资源，防止越权操作
def check_access(user, resource):
    if user.role not in resource.allowed_roles:
        raise PermissionDenied()
```

---

## 文件编码规范

### 编码格式

| 项目 | 规范 |
|------|------|
| 文件编码 | UTF-8 without BOM |
| 行尾符 | LF (Unix风格) |
| 文件末尾 | 空行结束 |

### Python编码声明禁止

Python 3.x 文件禁止使用 `# -*- coding: utf-8 -*-` 或 `# coding: utf-8` 编码声明。Python 3 默认UTF-8编码，PEP 263声明冗余且部分工具链会产生非预期行为。

### 编辑器配置

```json
// .editorconfig
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 2

[*.md]
trim_trailing_whitespace = false

[Makefile]
indent_style = tab
```

### Git配置

```gitattributes
# .gitattributes
* text=auto eol=lf
*.bat text eol=crlf
```

### 特殊字符处理

```javascript
// 使用Unicode转义处理特殊字符
const message = '用户\u00A0名称'; // 不间断空格

// 使用模板字符串处理多行文本
const sql = `
  SELECT *
  FROM users
  WHERE status = 'active'
`;

// 避免在代码中硬编码非ASCII字符
// 使用国际化方案
const labels = {
  'zh-CN': '用户名',
  'en-US': 'Username'
};
```

---

## Git提交规范

Git commit message 遵循约定式提交规范，主体内容须使用中文描述变更意图（type和scope仍用英文）。格式：`<类型>(<范围>): <中文描述>`

---

## CI编码合规检查

编码合规性检查脚本：`scripts/check-encoding.py`（文件编码检查）、`scripts/check-comment-lang.py`（注释语言检查）。CI流水线中通过FILE-ENCODING和COMMENT-LANGUAGE门禁强制执行。

---

## 检查清单

### 提交前检查

- [ ] 所有变量和函数使用有意义的名称
- [ ] 遵循项目统一的命名规范
- [ ] 代码缩进和格式一致
- [ ] 复杂逻辑有适当的注释
- [ ] 文件编码为UTF-8 without BOM
- [ ] 行尾为LF
- [ ] 文件末尾有空行
- [ ] 无多余空白字符

### 代码审查检查

- [ ] 命名是否清晰表达意图
- [ ] 是否有重复代码可抽取
- [ ] 注释是否准确且必要
- [ ] 是否遵循SOLID原则
- [ ] 是否有潜在的性能问题

---

## 参考资料

- [Google JavaScript Style Guide](https://google.github.io/styleguide/jsguide.html)
- [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- [TypeScript Deep Dive - Coding Guidelines](https://basarat.gitbook.io/typescript/styleguide)
- [Clean Code by Robert C. Martin](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)

---

> 本文档由 Multi-Agent SDD/TDD Orchestrator 维护 | 最后更新: 2026-04-28
