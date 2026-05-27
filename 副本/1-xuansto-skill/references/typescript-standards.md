# TypeScript/JavaScript 开发规范

> 版本: 1.0.0 | 更新日期: 2026-04-17
> 编码: UTF-8 without BOM | 行尾: LF

---

## 目录

1. [TypeScript 命名规范与代码风格](#1-typescript-命名规范与代码风格)
2. [项目结构规范](#2-项目结构规范)
3. [依赖管理规范](#3-依赖管理规范)
4. [测试规范](#4-测试规范)
5. [前端框架规范](#5-前端框架规范)
6. [Node.js 后端规范](#6-nodejs-后端规范)
7. [检查清单](#7-检查清单)

---

## 1. TypeScript 命名规范与代码风格

### 1.1 命名约定

| 类型 | 命名风格 | 示例 |
|------|----------|------|
| 类/接口/类型别名/枚举 | PascalCase | `UserService`, `IUser`, `UserRole` |
| 变量/函数/方法 | camelCase | `getUserById`, `isActive` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` |
| 私有成员 | _前缀 + camelCase | `_privateMethod` |
| 文件名 | kebab-case | `user-service.ts` |
| 组件文件 | PascalCase | `UserProfile.tsx` |
| 工具函数文件 | camelCase | `formatDate.ts` |

### 1.2 接口与类型别名

```typescript
interface IUser {
  id: string;
  name: string;
  email: string;
  createdAt: Date;
  updatedAt?: Date;
}

type UserRole = 'admin' | 'user' | 'guest';

type UserResponse = {
  success: boolean;
  data: IUser | null;
  error?: string;
};

interface IUserService {
  getUserById(id: string): Promise<IUser | null>;
  createUser(data: Omit<IUser, 'id' | 'createdAt'>): Promise<IUser>;
  updateUser(id: string, data: Partial<IUser>): Promise<IUser>;
  deleteUser(id: string): Promise<boolean>;
}
```

### 1.3 类定义规范

```typescript
@Injectable()
export class UserService implements IUserService {
  private readonly userRepository: IUserRepository;
  private readonly logger: ILogger;
  private static instance: UserService | null = null;

  constructor(
    userRepository: IUserRepository,
    logger: ILogger,
  ) {
    this.userRepository = userRepository;
    this.logger = logger;
  }

  static getInstance(): UserService {
    if (!UserService.instance) {
      UserService.instance = new UserService(
        new UserRepository(),
        new ConsoleLogger(),
      );
    }
    return UserService.instance;
  }

  async getUserById(id: string): Promise<IUser | null> {
    this.logger.info(`Fetching user with id: ${id}`);
    return this.userRepository.findById(id);
  }

  async createUser(data: Omit<IUser, 'id' | 'createdAt'>): Promise<IUser> {
    const user: IUser = {
      ...data,
      id: this.generateId(),
      createdAt: new Date(),
    };
    return this.userRepository.save(user);
  }

  private generateId(): string {
    return crypto.randomUUID();
  }
}
```

### 1.4 函数定义规范

```typescript
type AsyncResult<T, E = Error> = Promise<
  | { success: true; data: T }
  | { success: false; error: E }
>;

async function fetchUser(id: string): AsyncResult<IUser> {
  try {
    const response = await fetch(`/api/users/${id}`);
    if (!response.ok) {
      return { success: false, error: new Error('User not found') };
    }
    const data = await response.json();
    return { success: true, data };
  } catch (error) {
    return { success: false, error: error as Error };
  }
}

const formatUserName = (user: Pick<IUser, 'name'>): string => {
  return user.name.trim().toUpperCase();
};

const debounce = <T extends (...args: unknown[]) => unknown>(
  fn: T,
  delay: number,
): ((...args: Parameters<T>) => void) => {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;
  return (...args: Parameters<T>) => {
    if (timeoutId) clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
};
```

### 1.5 枚举与常量

```typescript
enum HttpStatusCode {
  OK = 200,
  CREATED = 201,
  BAD_REQUEST = 400,
  UNAUTHORIZED = 401,
  FORBIDDEN = 403,
  NOT_FOUND = 404,
  INTERNAL_SERVER_ERROR = 500,
}

const enum CacheKey {
  USER_SESSION = 'user_session',
  APP_SETTINGS = 'app_settings',
  FEATURE_FLAGS = 'feature_flags',
}

const API_CONFIG = {
  BASE_URL: 'https://api.example.com',
  TIMEOUT_MS: 5000,
  MAX_RETRIES: 3,
  RETRY_DELAY_MS: 1000,
} as const;

const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024;
const ALLOWED_FILE_TYPES = ['image/jpeg', 'image/png', 'image/gif'] as const;
```

### 1.6 泛型使用规范

```typescript
interface IRepository<T extends { id: string }> {
  findById(id: string): Promise<T | null>;
  findAll(): Promise<T[]>;
  save(entity: T): Promise<T>;
  delete(id: string): Promise<boolean>;
}

class BaseRepository<T extends { id: string }> implements IRepository<T> {
  constructor(private readonly collection: Map<string, T>) {}

  async findById(id: string): Promise<T | null> {
    return this.collection.get(id) ?? null;
  }

  async findAll(): Promise<T[]> {
    return Array.from(this.collection.values());
  }

  async save(entity: T): Promise<T> {
    this.collection.set(entity.id, entity);
    return entity;
  }

  async delete(id: string): Promise<boolean> {
    return this.collection.delete(id);
  }
}

function createRepository<T extends { id: string }>(
  initialData: T[] = [],
): IRepository<T> {
  const collection = new Map<string, T>();
  initialData.forEach((item) => collection.set(item.id, item));
  return new BaseRepository(collection);
}
```

### 1.7 ESLint 配置示例

```json
{
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:@typescript-eslint/recommended-requiring-type-checking",
    "prettier"
  ],
  "parser": "@typescript-eslint/parser",
  "parserOptions": {
    "ecmaVersion": 2022,
    "sourceType": "module",
    "project": "./tsconfig.json"
  },
  "plugins": ["@typescript-eslint"],
  "rules": {
    "@typescript-eslint/explicit-function-return-type": "error",
    "@typescript-eslint/explicit-module-boundary-types": "error",
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
    "@typescript-eslint/no-non-null-assertion": "warn",
    "@typescript-eslint/prefer-nullish-coalescing": "error",
    "@typescript-eslint/prefer-optional-chain": "error",
    "@typescript-eslint/strict-boolean-expressions": "error",
    "no-console": ["warn", { "allow": ["warn", "error"] }],
    "prefer-const": "error",
    "no-var": "error"
  }
}
```

### 1.8 Prettier 配置示例

```json
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5",
  "tabWidth": 2,
  "useTabs": false,
  "printWidth": 100,
  "bracketSpacing": true,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

---

## 2. 项目结构规范

### 2.1 Monorepo 目录结构

```
project-root/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── release.yml
│   │   └── deploy.yml
│   └── ISSUE_TEMPLATE/
├── .vscode/
│   ├── settings.json
│   ├── extensions.json
│   └── launch.json
├── apps/
│   ├── web/
│   │   ├── src/
│   │   │   ├── app/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── pages/
│   │   │   ├── styles/
│   │   │   └── main.tsx
│   │   ├── public/
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── vite.config.ts
│   ├── api/
│   │   ├── src/
│   │   │   ├── controllers/
│   │   │   ├── services/
│   │   │   ├── repositories/
│   │   │   ├── middleware/
│   │   │   ├── models/
│   │   │   ├── routes/
│   │   │   └── main.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── admin/
│       └── ...
├── packages/
│   ├── shared/
│   │   ├── src/
│   │   │   ├── types/
│   │   │   ├── utils/
│   │   │   ├── constants/
│   │   │   └── index.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   ├── ui/
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   └── index.ts
│   │   └── package.json
│   └── config/
│       ├── eslint/
│       ├── typescript/
│       └── prettier/
├── tools/
│   ├── scripts/
│   └── generators/
├── docs/
│   ├── api/
│   ├── architecture/
│   └── guides/
├── .eslintrc.js
├── .prettierrc.js
├── tsconfig.base.json
├── package.json
├── pnpm-workspace.yaml
├── turbo.json
└── README.md
```

### 2.2 单体应用结构

```
src/
├── app/
│   ├── app.module.ts
│   ├── app.controller.ts
│   └── app.service.ts
├── common/
│   ├── decorators/
│   ├── filters/
│   ├── guards/
│   ├── interceptors/
│   ├── middleware/
│   └── pipes/
├── config/
│   ├── config.module.ts
│   ├── database.config.ts
│   └── app.config.ts
├── modules/
│   ├── users/
│   │   ├── dto/
│   │   ├── entities/
│   │   ├── users.controller.ts
│   │   ├── users.service.ts
│   │   └── users.module.ts
│   └── auth/
│       ├── dto/
│       ├── strategies/
│       ├── auth.controller.ts
│       ├── auth.service.ts
│       └── auth.module.ts
├── database/
│   ├── migrations/
│   ├── seeds/
│   └── data-source.ts
├── types/
│   └── global.d.ts
└── main.ts
```

### 2.3 Workspace 配置

#### pnpm-workspace.yaml

```yaml
packages:
  - 'apps/*'
  - 'packages/*'
  - 'tools/*'
```

#### turbo.json

```json
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": ["**/.env.*local"],
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", ".next/**", "!.next/cache/**"]
    },
    "lint": {
      "outputs": []
    },
    "test": {
      "dependsOn": ["build"],
      "outputs": ["coverage/**"]
    },
    "typecheck": {
      "outputs": []
    },
    "dev": {
      "cache": false,
      "persistent": true
    }
  }
}
```

#### tsconfig.base.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "lib": ["ES2022"],
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@shared/*": ["./packages/shared/src/*"],
      "@ui/*": ["./packages/ui/src/*"]
    }
  }
}
```

---

## 3. 依赖管理规范

### 3.1 包管理器对比

| 特性 | npm | pnpm | yarn |
|------|-----|------|------|
| 安装速度 | 中等 | 最快 | 快 |
| 磁盘空间 | 高 | 低（硬链接） | 中 |
| 幽灵依赖 | 有 | 无 | 有（v1） |
| Monorepo | 支持 | 原生支持 | 支持 |
| 锁文件 | package-lock.json | pnpm-lock.yaml | yarn.lock |

### 3.2 npm 规范

#### package.json

```json
{
  "name": "@org/project-name",
  "version": "1.0.0",
  "description": "Project description",
  "type": "module",
  "main": "./dist/index.js",
  "module": "./dist/index.mjs",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "import": "./dist/index.mjs",
      "require": "./dist/index.js",
      "types": "./dist/index.d.ts"
    },
    "./utils": {
      "import": "./dist/utils.mjs",
      "require": "./dist/utils.js",
      "types": "./dist/utils.d.ts"
    }
  },
  "files": ["dist", "README.md", "LICENSE"],
  "scripts": {
    "dev": "tsx watch src/main.ts",
    "build": "tsup src/index.ts --format cjs,esm --dts",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage",
    "lint": "eslint src --ext .ts,.tsx",
    "lint:fix": "eslint src --ext .ts,.tsx --fix",
    "typecheck": "tsc --noEmit",
    "format": "prettier --write \"src/**/*.{ts,tsx,json,md}\"",
    "clean": "rimraf dist coverage node_modules",
    "prepare": "husky install"
  },
  "dependencies": {
    "zod": "^3.22.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "^5.3.0",
    "vitest": "^1.0.0",
    "eslint": "^8.56.0",
    "prettier": "^3.2.0",
    "tsup": "^8.0.0",
    "tsx": "^4.7.0"
  },
  "peerDependencies": {
    "react": ">=18.0.0"
  },
  "engines": {
    "node": ">=20.0.0",
    "npm": ">=10.0.0"
  },
  "keywords": ["typescript", "library"],
  "author": "Author Name",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/org/project-name"
  },
  "bugs": {
    "url": "https://github.com/org/project-name/issues"
  },
  "homepage": "https://github.com/org/project-name#readme"
}
```

#### .npmrc

```ini
# Registry
registry=https://registry.npmjs.org/

# Scoped registry
@org:registry=https://npm.pkg.github.com/

# Authentication
//npm.pkg.github.com/:_authToken=${NPM_TOKEN}

# Security
audit=true
fund=false

# Install behavior
save-exact=false
save-prefix=^
package-lock=true

# Scripts
ignore-scripts=false
```

### 3.3 pnpm 规范

#### .npmrc (pnpm)

```ini
shamefully-hoist=true
strict-peer-dependencies=true
auto-install-peers=true
node-linker=hoisted
```

#### 常用命令

```bash
# 安装依赖
pnpm install

# 添加依赖
pnpm add lodash
pnpm add -D typescript
pnpm add -w typescript

# 更新依赖
pnpm update
pnpm update --interactive
pnpm update --latest

# 清理
pnpm store prune
pnpm -r exec rm -rf node_modules

# Monorepo
pnpm -r run build
pnpm -F @org/web run dev
pnpm -F @org/api run test
```

### 3.4 依赖版本规范

```json
{
  "dependencies": {
    "exact-version": "1.2.3",
    "patch-updates": "^1.2.3",
    "minor-updates": "~1.2.0",
    "any-version": "*",
    "range": ">=1.0.0 <2.0.0",
    "or": "1.x || 2.x"
  }
}
```

### 3.5 依赖安全检查

```bash
# npm
npm audit
npm audit fix
npm audit fix --force

# pnpm
pnpm audit
pnpm audit --fix

# yarn
yarn npm audit
```

---

## 4. 测试规范

### 4.1 测试文件命名

| 测试类型 | 文件命名 | 位置 |
|----------|----------|------|
| 单元测试 | `*.test.ts` | 同目录或 `__tests__/` |
| 集成测试 | `*.integration.test.ts` | `tests/integration/` |
| E2E 测试 | `*.e2e.test.ts` | `tests/e2e/` |
| 快照测试 | `*.snapshot.test.ts` | 同目录 |

### 4.2 Vitest 配置

```typescript
import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['src/**/*.test.ts'],
    exclude: ['node_modules', 'dist'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules',
        'dist',
        '**/*.d.ts',
        '**/*.config.ts',
        '**/index.ts',
      ],
      statements: 80,
      branches: 80,
      functions: 80,
      lines: 80,
    },
    setupFiles: ['./tests/setup.ts'],
    testTimeout: 10000,
    hookTimeout: 10000,
    retry: 2,
    reporters: ['default', 'html'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

### 4.3 单元测试示例

```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { UserService } from './user.service';
import type { IUserRepository } from './user.repository';

describe('UserService', () => {
  let service: UserService;
  let mockRepository: IUserRepository;

  beforeEach(() => {
    mockRepository = {
      findById: vi.fn(),
      findAll: vi.fn(),
      save: vi.fn(),
      delete: vi.fn(),
    };
    service = new UserService(mockRepository);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('getUserById', () => {
    it('should return user when found', async () => {
      const mockUser = {
        id: '1',
        name: 'John Doe',
        email: 'john@example.com',
        createdAt: new Date(),
      };
      vi.mocked(mockRepository.findById).mockResolvedValue(mockUser);

      const result = await service.getUserById('1');

      expect(result).toEqual(mockUser);
      expect(mockRepository.findById).toHaveBeenCalledWith('1');
      expect(mockRepository.findById).toHaveBeenCalledTimes(1);
    });

    it('should return null when user not found', async () => {
      vi.mocked(mockRepository.findById).mockResolvedValue(null);

      const result = await service.getUserById('999');

      expect(result).toBeNull();
    });

    it('should throw error when repository fails', async () => {
      vi.mocked(mockRepository.findById).mockRejectedValue(
        new Error('Database error'),
      );

      await expect(service.getUserById('1')).rejects.toThrow('Database error');
    });
  });

  describe('createUser', () => {
    it('should create user with generated id and timestamp', async () => {
      const input = { name: 'Jane Doe', email: 'jane@example.com' };
      vi.mocked(mockRepository.save).mockImplementation(async (user) => user);

      const result = await service.createUser(input);

      expect(result.id).toBeDefined();
      expect(result.name).toBe(input.name);
      expect(result.email).toBe(input.email);
      expect(result.createdAt).toBeInstanceOf(Date);
    });
  });
});
```

### 4.4 Jest 配置

```typescript
import type { Config } from 'jest';

const config: Config = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src'],
  testMatch: ['**/*.test.ts'],
  moduleFileExtensions: ['ts', 'js', 'json'],
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
    '!src/**/index.ts',
  ],
  coverageDirectory: 'coverage',
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  testTimeout: 10000,
  verbose: true,
};

export default config;
```

### 4.5 Playwright E2E 测试

#### playwright.config.ts

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['html'], ['junit', { outputFile: 'results.xml' }]],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
```

#### E2E 测试示例

```typescript
import { test, expect, Page } from '@playwright/test';

test.describe('User Authentication', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display login form', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Login' })).toBeVisible();
    await expect(page.getByLabel('Email')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sign In' })).toBeVisible();
  });

  test('should login successfully with valid credentials', async ({ page }) => {
    await page.getByLabel('Email').fill('test@example.com');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: 'Sign In' }).click();

    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.getByText('Welcome, Test User')).toBeVisible();
  });

  test('should show error with invalid credentials', async ({ page }) => {
    await page.getByLabel('Email').fill('wrong@example.com');
    await page.getByLabel('Password').fill('wrongpassword');
    await page.getByRole('button', { name: 'Sign In' }).click();

    await expect(page.getByText('Invalid credentials')).toBeVisible();
  });

  test('should validate email format', async ({ page }) => {
    await page.getByLabel('Email').fill('invalid-email');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: 'Sign In' }).click();

    await expect(page.getByText('Invalid email format')).toBeVisible();
  });
});

test.describe('User Profile', () => {
  test.use({ storageState: 'tests/auth/user.json' });

  test('should update profile picture', async ({ page }) => {
    await page.goto('/profile');

    const fileInput = page.getByLabel('Profile Picture');
    await fileInput.setInputFiles('tests/fixtures/avatar.png');

    await expect(page.getByAltText('Profile picture')).toBeVisible();
  });
});
```

### 4.6 测试最佳实践

```typescript
import { describe, it, expect, vi } from 'vitest';

describe('Testing Best Practices', () => {
  it('should use descriptive test names', () => {
    expect(true).toBe(true);
  });

  it('should test one thing at a time', () => {
    const result = 1 + 1;
    expect(result).toBe(2);
  });

  it('should use Arrange-Act-Assert pattern', () => {
    const input = 5;
    const expected = 25;

    const result = input * input;

    expect(result).toBe(expected);
  });

  it('should mock external dependencies', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ data: 'test' }),
    });

    global.fetch = mockFetch;

    const response = await fetch('/api/test');
    const data = await response.json();

    expect(data).toEqual({ data: 'test' });
    expect(mockFetch).toHaveBeenCalledWith('/api/test');
  });

  it('should test edge cases', () => {
    const sum = (a: number, b: number): number => a + b;

    expect(sum(0, 0)).toBe(0);
    expect(sum(-1, 1)).toBe(0);
    expect(sum(Number.MAX_SAFE_INTEGER, 1)).toBe(Number.MAX_SAFE_INTEGER + 1);
  });

  it('should test error conditions', () => {
    const divide = (a: number, b: number): number => {
      if (b === 0) throw new Error('Division by zero');
      return a / b;
    };

    expect(() => divide(1, 0)).toThrow('Division by zero');
  });
});
```

---

## 5. 前端框架规范

### 5.1 React 规范

#### 组件结构

```typescript
import { useState, useCallback, useMemo, useEffect } from 'react';
import type { FC, ReactNode, ChangeEvent, FormEvent } from 'react';

interface UserFormProps {
  initialData?: Partial<IUser>;
  onSubmit: (data: IUser) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
  children?: ReactNode;
}

interface FormData {
  name: string;
  email: string;
  role: UserRole;
}

const DEFAULT_FORM_DATA: FormData = {
  name: '',
  email: '',
  role: 'user',
};

export const UserForm: FC<UserFormProps> = ({
  initialData,
  onSubmit,
  onCancel,
  isLoading = false,
  children,
}) => {
  const [formData, setFormData] = useState<FormData>({
    ...DEFAULT_FORM_DATA,
    ...initialData,
  });
  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({});

  const isValid = useMemo(() => {
    return (
      formData.name.trim() !== '' &&
      formData.email.includes('@') &&
      Object.keys(errors).length === 0
    );
  }, [formData, errors]);

  const handleChange = useCallback(
    (field: keyof FormData) => (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      setFormData((prev) => ({
        ...prev,
        [field]: event.target.value,
      }));
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    },
    [],
  );

  const handleSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();

      if (!isValid) return;

      try {
        await onSubmit({
          ...formData,
          id: initialData?.id ?? crypto.randomUUID(),
          createdAt: initialData?.createdAt ?? new Date(),
        });
      } catch (error) {
        console.error('Submit error:', error);
      }
    },
    [formData, initialData, isValid, onSubmit],
  );

  useEffect(() => {
    return () => {
      setFormData(DEFAULT_FORM_DATA);
      setErrors({});
    };
  }, []);

  return (
    <form onSubmit={handleSubmit} className="user-form">
      <div className="form-group">
        <label htmlFor="name">Name</label>
        <input
          id="name"
          type="text"
          value={formData.name}
          onChange={handleChange('name')}
          disabled={isLoading}
          aria-invalid={!!errors.name}
          aria-describedby={errors.name ? 'name-error' : undefined}
        />
        {errors.name && (
          <span id="name-error" className="error">
            {errors.name}
          </span>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={formData.email}
          onChange={handleChange('email')}
          disabled={isLoading}
        />
      </div>

      <div className="form-actions">
        <button type="submit" disabled={!isValid || isLoading}>
          {isLoading ? 'Saving...' : 'Save'}
        </button>
        <button type="button" onClick={onCancel} disabled={isLoading}>
          Cancel
        </button>
      </div>

      {children}
    </form>
  );
};
```

#### 自定义 Hook

```typescript
import { useState, useEffect, useCallback, useRef } from 'react';

interface UseAsyncOptions<T> {
  immediate?: boolean;
  initialData?: T;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
}

interface UseAsyncResult<T> {
  data: T | null;
  error: Error | null;
  isLoading: boolean;
  execute: (...args: unknown[]) => Promise<T>;
  reset: () => void;
}

function useAsync<T>(
  asyncFunction: (...args: unknown[]) => Promise<T>,
  options: UseAsyncOptions<T> = {},
): UseAsyncResult<T> {
  const { immediate = false, initialData, onSuccess, onError } = options;

  const [data, setData] = useState<T | null>(initialData ?? null);
  const [error, setError] = useState<Error | null>(null);
  const [isLoading, setIsLoading] = useState(immediate);

  const isMounted = useRef(true);

  const execute = useCallback(
    async (...args: unknown[]): Promise<T> => {
      setIsLoading(true);
      setError(null);

      try {
        const result = await asyncFunction(...args);

        if (isMounted.current) {
          setData(result);
          onSuccess?.(result);
        }

        return result;
      } catch (err) {
        const error = err as Error;

        if (isMounted.current) {
          setError(error);
          onError?.(error);
        }

        throw error;
      } finally {
        if (isMounted.current) {
          setIsLoading(false);
        }
      }
    },
    [asyncFunction, onSuccess, onError],
  );

  const reset = useCallback(() => {
    setData(initialData ?? null);
    setError(null);
    setIsLoading(false);
  }, [initialData]);

  useEffect(() => {
    if (immediate) {
      execute();
    }

    return () => {
      isMounted.current = false;
    };
  }, [immediate, execute]);

  return { data, error, isLoading, execute, reset };
}

export { useAsync };
```

### 5.2 Vue 规范

#### 组合式 API

```vue
<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import type { PropType } from 'vue';

interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user' | 'guest';
}

const props = defineProps({
  userId: {
    type: String,
    required: true,
  },
  editable: {
    type: Boolean,
    default: false,
  },
  initialData: {
    type: Object as PropType<Partial<User>>,
    default: () => ({}),
  },
});

const emit = defineEmits<{
  (e: 'update', user: User): void;
  (e: 'delete', id: string): void;
  (e: 'cancel'): void;
}>();

const user = ref<User | null>(null);
const isLoading = ref(false);
const error = ref<string | null>(null);

const displayName = computed(() => {
  if (!user.value) return 'Unknown User';
  return user.value.name.trim() || user.value.email.split('@')[0];
});

const isAdmin = computed(() => user.value?.role === 'admin');

const fetchUser = async (id: string): Promise<void> => {
  isLoading.value = true;
  error.value = null;

  try {
    const response = await fetch(`/api/users/${id}`);
    if (!response.ok) throw new Error('User not found');
    user.value = await response.json();
  } catch (err) {
    error.value = (err as Error).message;
  } finally {
    isLoading.value = false;
  }
};

const handleUpdate = (): void => {
  if (user.value) {
    emit('update', user.value);
  }
};

const handleDelete = (): void => {
  if (user.value && confirm('Are you sure?')) {
    emit('delete', user.value.id);
  }
};

watch(
  () => props.userId,
  (newId) => {
    if (newId) {
      fetchUser(newId);
    }
  },
  { immediate: true },
);

onMounted(() => {
  console.log('UserCard mounted');
});

onUnmounted(() => {
  console.log('UserCard unmounted');
});
</script>

<template>
  <div class="user-card" :class="{ 'is-admin': isAdmin }">
    <div v-if="isLoading" class="loading">Loading...</div>

    <div v-else-if="error" class="error">
      {{ error }}
    </div>

    <div v-else-if="user" class="user-content">
      <h2 class="user-name">{{ displayName }}</h2>
      <p class="user-email">{{ user.email }}</p>
      <span class="user-role">{{ user.role }}</span>

      <div v-if="editable" class="actions">
        <button @click="handleUpdate" :disabled="isLoading">Update</button>
        <button @click="handleDelete" class="danger">Delete</button>
        <button @click="$emit('cancel')">Cancel</button>
      </div>
    </div>

    <slot name="footer" :user="user" :loading="isLoading" />
  </div>
</template>

<style scoped>
.user-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
}

.user-card.is-admin {
  border-color: #1976d2;
}

.loading {
  text-align: center;
  padding: 20px;
}

.error {
  color: #d32f2f;
}

.actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

.actions button.danger {
  background-color: #d32f2f;
  color: white;
}
</style>
```

#### Pinia Store

```typescript
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

interface User {
  id: string;
  name: string;
  email: string;
}

export const useUserStore = defineStore('user', () => {
  const users = ref<User[]>([]);
  const currentUser = ref<User | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  const userCount = computed(() => users.value.length);
  const isAuthenticated = computed(() => currentUser.value !== null);

  const fetchUsers = async (): Promise<void> => {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await fetch('/api/users');
      if (!response.ok) throw new Error('Failed to fetch users');
      users.value = await response.json();
    } catch (err) {
      error.value = (err as Error).message;
    } finally {
      isLoading.value = false;
    }
  };

  const login = async (email: string, password: string): Promise<boolean> => {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) throw new Error('Invalid credentials');

      currentUser.value = await response.json();
      return true;
    } catch (err) {
      error.value = (err as Error).message;
      return false;
    } finally {
      isLoading.value = false;
    }
  };

  const logout = (): void => {
    currentUser.value = null;
  };

  const $reset = (): void => {
    users.value = [];
    currentUser.value = null;
    isLoading.value = false;
    error.value = null;
  };

  return {
    users,
    currentUser,
    isLoading,
    error,
    userCount,
    isAuthenticated,
    fetchUsers,
    login,
    logout,
    $reset,
  };
});
```

### 5.3 Angular 规范

#### 组件

```typescript
import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit,
  OnDestroy,
  ChangeDetectionStrategy,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';

interface User {
  id: string;
  name: string;
  email: string;
}

@Component({
  selector: 'app-user-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <form [formGroup]="userForm" (ngSubmit)="onSubmit()" class="user-form">
      <div class="form-group">
        <label for="name">Name</label>
        <input
          id="name"
          type="text"
          formControlName="name"
          [class.is-invalid]="isFieldInvalid('name')"
        />
        <div *ngIf="isFieldInvalid('name')" class="error">
          <span *ngIf="userForm.get('name')?.errors?.['required']">Name is required</span>
          <span *ngIf="userForm.get('name')?.errors?.['minlength']">
            Name must be at least 2 characters
          </span>
        </div>
      </div>

      <div class="form-group">
        <label for="email">Email</label>
        <input
          id="email"
          type="email"
          formControlName="email"
          [class.is-invalid]="isFieldInvalid('email')"
        />
        <div *ngIf="isFieldInvalid('email')" class="error">
          <span *ngIf="userForm.get('email')?.errors?.['required']">Email is required</span>
          <span *ngIf="userForm.get('email')?.errors?.['email']">Invalid email format</span>
        </div>
      </div>

      <div class="actions">
        <button type="submit" [disabled]="userForm.invalid || isLoading">
          {{ isLoading ? 'Saving...' : 'Save' }}
        </button>
        <button type="button" (click)="onCancel.emit()">Cancel</button>
      </div>
    </form>
  `,
  styles: [
    `
      .user-form {
        display: flex;
        flex-direction: column;
        gap: 16px;
      }
      .form-group {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }
      .is-invalid {
        border-color: #dc3545;
      }
      .error {
        color: #dc3545;
        font-size: 12px;
      }
    `,
  ],
})
export class UserFormComponent implements OnInit, OnDestroy {
  @Input() initialData: Partial<User> | null = null;
  @Input() isLoading = false;

  @Output() submitForm = new EventEmitter<User>();
  @Output() onCancel = new EventEmitter<void>();

  private readonly fb = inject(FormBuilder);
  private readonly destroy$ = new Subject<void>();

  userForm: FormGroup = this.fb.group({
    name: ['', [Validators.required, Validators.minLength(2)]],
    email: ['', [Validators.required, Validators.email]],
  });

  ngOnInit(): void {
    if (this.initialData) {
      this.userForm.patchValue(this.initialData);
    }

    this.userForm.valueChanges
      .pipe(takeUntil(this.destroy$))
      .subscribe((value) => {
        console.log('Form value changed:', value);
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  isFieldInvalid(fieldName: string): boolean {
    const field = this.userForm.get(fieldName);
    return !!(field?.invalid && (field.dirty || field.touched));
  }

  onSubmit(): void {
    if (this.userForm.valid) {
      this.submitForm.emit({
        ...this.initialData,
        ...this.userForm.value,
        id: this.initialData?.id ?? crypto.randomUUID(),
      } as User);
    } else {
      this.userForm.markAllAsTouched();
    }
  }
}
```

#### Service

```typescript
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, catchError, retry, throwError } from 'rxjs';

interface User {
  id: string;
  name: string;
  email: string;
}

interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
}

@Injectable({
  providedIn: 'root',
})
export class UserService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/users';

  getUsers(
    page = 1,
    pageSize = 10,
    search?: string,
  ): Observable<PaginatedResponse<User>> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('pageSize', pageSize.toString());

    if (search) {
      params = params.set('search', search);
    }

    return this.http.get<PaginatedResponse<User>>(this.baseUrl, { params }).pipe(
      retry(2),
      catchError((error) => {
        console.error('Failed to fetch users:', error);
        return throwError(() => new Error('Failed to fetch users'));
      }),
    );
  }

  getUserById(id: string): Observable<User> {
    return this.http.get<User>(`${this.baseUrl}/${id}`).pipe(
      catchError((error) => {
        console.error(`Failed to fetch user ${id}:`, error);
        return throwError(() => new Error('User not found'));
      }),
    );
  }

  createUser(user: Omit<User, 'id'>): Observable<User> {
    return this.http.post<User>(this.baseUrl, user).pipe(
      catchError((error) => {
        console.error('Failed to create user:', error);
        return throwError(() => new Error('Failed to create user'));
      }),
    );
  }

  updateUser(id: string, user: Partial<User>): Observable<User> {
    return this.http.patch<User>(`${this.baseUrl}/${id}`, user).pipe(
      catchError((error) => {
        console.error(`Failed to update user ${id}:`, error);
        return throwError(() => new Error('Failed to update user'));
      }),
    );
  }

  deleteUser(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}`).pipe(
      catchError((error) => {
        console.error(`Failed to delete user ${id}:`, error);
        return throwError(() => new Error('Failed to delete user'));
      }),
    );
  }
}
```

---

## 6. Node.js 后端规范

### 6.1 Express 规范

#### 项目结构

```
src/
├── controllers/
│   ├── user.controller.ts
│   └── auth.controller.ts
├── middleware/
│   ├── auth.middleware.ts
│   ├── error.middleware.ts
│   └── validation.middleware.ts
├── models/
│   ├── user.model.ts
│   └── index.ts
├── routes/
│   ├── index.ts
│   ├── user.routes.ts
│   └── auth.routes.ts
├── services/
│   ├── user.service.ts
│   └── auth.service.ts
├── utils/
│   ├── logger.ts
│   └── response.ts
├── validators/
│   └── user.validator.ts
├── app.ts
└── server.ts
```

#### 应用入口

```typescript
import express, { Express, Request, Response, NextFunction } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import rateLimit from 'express-rate-limit';
import { router } from './routes';
import { errorHandler } from './middleware/error.middleware';
import { logger } from './utils/logger';

const app: Express = express();

app.use(helmet());
app.use(cors({ origin: process.env.ALLOWED_ORIGINS?.split(',') }));
app.use(compression());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  message: 'Too many requests from this IP',
});
app.use('/api/', limiter);

app.use('/api', router);

app.get('/health', (_req: Request, res: Response) => {
  res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.use((_req: Request, res: Response) => {
  res.status(404).json({ error: 'Not Found' });
});

app.use((err: Error, _req: Request, res: Response, _next: NextFunction) => {
  errorHandler(err, _req, res, _next);
});

const PORT = process.env.PORT ?? 3000;

app.listen(PORT, () => {
  logger.info(`Server running on port ${PORT}`);
});

export { app };
```

#### Controller

```typescript
import { Request, Response, NextFunction } from 'express';
import { UserService } from '../services/user.service';
import { AppError } from '../middleware/error.middleware';

export class UserController {
  constructor(private readonly userService: UserService) {}

  getAll = async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      const { page = 1, limit = 10, search } = req.query;

      const result = await this.userService.findAll({
        page: Number(page),
        limit: Number(limit),
        search: search as string | undefined,
      });

      res.status(200).json(result);
    } catch (error) {
      next(error);
    }
  };

  getById = async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      const { id } = req.params;

      const user = await this.userService.findById(id);

      if (!user) {
        throw new AppError('User not found', 404);
      }

      res.status(200).json(user);
    } catch (error) {
      next(error);
    }
  };

  create = async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      const user = await this.userService.create(req.body);

      res.status(201).json(user);
    } catch (error) {
      next(error);
    }
  };

  update = async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      const { id } = req.params;

      const user = await this.userService.update(id, req.body);

      if (!user) {
        throw new AppError('User not found', 404);
      }

      res.status(200).json(user);
    } catch (error) {
      next(error);
    }
  };

  delete = async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      const { id } = req.params;

      const deleted = await this.userService.delete(id);

      if (!deleted) {
        throw new AppError('User not found', 404);
      }

      res.status(204).send();
    } catch (error) {
      next(error);
    }
  };
}
```

### 6.2 NestJS 规范

#### 模块结构

```typescript
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { UserController } from './user.controller';
import { UserService } from './user.service';
import { User } from './entities/user.entity';
import { UserRepository } from './repositories/user.repository';

@Module({
  imports: [TypeOrmModule.forFeature([User])],
  controllers: [UserController],
  providers: [UserService, UserRepository],
  exports: [UserService],
})
export class UserModule {}
```

#### Controller

```typescript
import {
  Controller,
  Get,
  Post,
  Body,
  Patch,
  Param,
  Delete,
  Query,
  ParseIntPipe,
  HttpStatus,
  HttpCode,
} from '@nestjs/common';
import { UserService } from './user.service';
import { CreateUserDto } from './dto/create-user.dto';
import { UpdateUserDto } from './dto/update-user.dto';
import { User } from './entities/user.entity';

@Controller('users')
export class UserController {
  constructor(private readonly userService: UserService) {}

  @Post()
  async create(@Body() createUserDto: CreateUserDto): Promise<User> {
    return this.userService.create(createUserDto);
  }

  @Get()
  async findAll(
    @Query('page', ParseIntPipe) page = 1,
    @Query('limit', ParseIntPipe) limit = 10,
  ): Promise<{ data: User[]; total: number }> {
    return this.userService.findAll(page, limit);
  }

  @Get(':id')
  async findOne(@Param('id') id: string): Promise<User> {
    return this.userService.findOne(id);
  }

  @Patch(':id')
  async update(
    @Param('id') id: string,
    @Body() updateUserDto: UpdateUserDto,
  ): Promise<User> {
    return this.userService.update(id, updateUserDto);
  }

  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  async remove(@Param('id') id: string): Promise<void> {
    return this.userService.remove(id);
  }
}
```

#### Service

```typescript
import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { User } from './entities/user.entity';
import { CreateUserDto } from './dto/create-user.dto';
import { UpdateUserDto } from './dto/update-user.dto';

@Injectable()
export class UserService {
  constructor(
    @InjectRepository(User)
    private readonly userRepository: Repository<User>,
  ) {}

  async create(createUserDto: CreateUserDto): Promise<User> {
    const user = this.userRepository.create(createUserDto);
    return this.userRepository.save(user);
  }

  async findAll(page: number, limit: number): Promise<{ data: User[]; total: number }> {
    const [data, total] = await this.userRepository.findAndCount({
      skip: (page - 1) * limit,
      take: limit,
      order: { createdAt: 'DESC' },
    });

    return { data, total };
  }

  async findOne(id: string): Promise<User> {
    const user = await this.userRepository.findOne({ where: { id } });

    if (!user) {
      throw new NotFoundException(`User with ID ${id} not found`);
    }

    return user;
  }

  async update(id: string, updateUserDto: UpdateUserDto): Promise<User> {
    const user = await this.findOne(id);
    Object.assign(user, updateUserDto);
    return this.userRepository.save(user);
  }

  async remove(id: string): Promise<void> {
    const user = await this.findOne(id);
    await this.userRepository.remove(user);
  }
}
```

#### DTO

```typescript
import { IsString, IsEmail, IsOptional, MinLength, MaxLength } from 'class-validator';

export class CreateUserDto {
  @IsString()
  @MinLength(2)
  @MaxLength(100)
  readonly name!: string;

  @IsEmail()
  readonly email!: string;

  @IsString()
  @MinLength(8)
  readonly password!: string;
}

export class UpdateUserDto {
  @IsOptional()
  @IsString()
  @MinLength(2)
  @MaxLength(100)
  readonly name?: string;

  @IsOptional()
  @IsEmail()
  readonly email?: string;
}
```

### 6.3 Fastify 规范

#### 应用入口

```typescript
import Fastify, { FastifyInstance } from 'fastify';
import cors from '@fastify/cors';
import helmet from '@fastify/helmet';
import rateLimit from '@fastify/rate-limit';
import { userRoutes } from './routes/user.routes';
import { errorHandler } from './middleware/error.handler';

const buildServer = async (): Promise<FastifyInstance> => {
  const fastify = Fastify({
    logger: {
      level: process.env.LOG_LEVEL ?? 'info',
      transport: {
        target: 'pino-pretty',
        options: { colorize: true },
      },
    },
  });

  await fastify.register(helmet);
  await fastify.register(cors, {
    origin: process.env.ALLOWED_ORIGINS?.split(','),
  });

  await fastify.register(rateLimit, {
    max: 100,
    timeWindow: '15 minutes',
  });

  fastify.register(userRoutes, { prefix: '/api/users' });

  fastify.get('/health', async () => ({
    status: 'ok',
    timestamp: new Date().toISOString(),
  }));

  fastify.setErrorHandler(errorHandler);

  return fastify;
};

const start = async (): Promise<void> => {
  const fastify = await buildServer();

  try {
    const port = Number(process.env.PORT) ?? 3000;
    await fastify.listen({ port, host: '0.0.0.0' });
    fastify.log.info(`Server listening on port ${port}`);
  } catch (error) {
    fastify.log.error(error);
    process.exit(1);
  }
};

start();
```

#### 路由

```typescript
import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { UserController } from '../controllers/user.controller';
import { createUserSchema, updateUserSchema } from '../schemas/user.schema';

interface IdParams {
  id: string;
}

interface QueryString {
  page?: number;
  limit?: number;
  search?: string;
}

export async function userRoutes(fastify: FastifyInstance): Promise<void> {
  const controller = new UserController();

  fastify.get('/', {
    schema: {
      querystring: {
        type: 'object',
        properties: {
          page: { type: 'number', default: 1 },
          limit: { type: 'number', default: 10 },
          search: { type: 'string' },
        },
      },
      response: {
        200: {
          type: 'object',
          properties: {
            data: { type: 'array' },
            total: { type: 'number' },
            page: { type: 'number' },
            limit: { type: 'number' },
          },
        },
      },
    },
    handler: async (
      request: FastifyRequest<{ Querystring: QueryString }>,
      reply: FastifyReply,
    ) => {
      const result = await controller.findAll(request.query);
      return reply.send(result);
    },
  });

  fastify.get('/:id', {
    schema: {
      params: {
        type: 'object',
        properties: {
          id: { type: 'string' },
        },
        required: ['id'],
      },
    },
    handler: async (
      request: FastifyRequest<{ Params: IdParams }>,
      reply: FastifyReply,
    ) => {
      const user = await controller.findById(request.params.id);
      return reply.send(user);
    },
  });

  fastify.post('/', {
    schema: createUserSchema,
    handler: async (request: FastifyRequest<{ Body: unknown }>, reply: FastifyReply) => {
      const user = await controller.create(request.body);
      return reply.code(201).send(user);
    },
  });

  fastify.patch('/:id', {
    schema: updateUserSchema,
    handler: async (
      request: FastifyRequest<{ Params: IdParams; Body: unknown }>,
      reply: FastifyReply,
    ) => {
      const user = await controller.update(request.params.id, request.body);
      return reply.send(user);
    },
  });

  fastify.delete('/:id', {
    handler: async (
      request: FastifyRequest<{ Params: IdParams }>,
      reply: FastifyReply,
    ) => {
      await controller.delete(request.params.id);
      return reply.code(204).send();
    },
  });
}
```

---

## 7. 检查清单

### 7.1 代码风格检查清单

- [ ] 使用一致的命名约定（PascalCase/camelCase/kebab-case）
- [ ] 接口以 `I` 前缀命名
- [ ] 类型别名使用描述性名称
- [ ] 常量使用 UPPER_SNAKE_CASE
- [ ] 私有成员使用 `_` 前缀
- [ ] 文件名使用 kebab-case
- [ ] 组件文件使用 PascalCase
- [ ] 函数有明确的返回类型
- [ ] 使用 `const` 优先于 `let`
- [ ] 避免使用 `any` 类型
- [ ] 使用可选链和空值合并
- [ ] 配置 ESLint 和 Prettier

### 7.2 项目结构检查清单

- [ ] 遵循约定的目录结构
- [ ] 模块职责单一
- [ ] 公共代码抽取到 shared 包
- [ ] 配置文件集中管理
- [ ] 测试文件位置正确
- [ ] 文档目录完整
- [ ] 使用 workspace 管理 monorepo
- [ ] 配置正确的路径别名

### 7.3 依赖管理检查清单

- [ ] 锁文件已提交
- [ ] 依赖版本使用语义化版本
- [ ] 开发依赖与生产依赖分离
- [ ] 无未使用的依赖
- [ ] 无已知安全漏洞
- [ ] engines 字段正确配置
- [ ] peerDependencies 正确声明
- [ ] 定期更新依赖

### 7.4 测试检查清单

- [ ] 单元测试覆盖核心逻辑
- [ ] 测试命名清晰描述意图
- [ ] 使用 AAA 模式（Arrange-Act-Assert）
- [ ] Mock 外部依赖
- [ ] 测试边界条件
- [ ] 测试错误处理
- [ ] 测试覆盖率达标（≥80%）
- [ ] E2E 测试覆盖关键流程
- [ ] CI 中运行所有测试

### 7.5 前端框架检查清单

- [ ] 组件职责单一
- [ ] Props 类型完整定义
- [ ] 状态管理合理
- [ ] 副作用正确处理
- [ ] 组件可测试
- [ ] 无障碍性考虑
- [ ] 性能优化（memo、useMemo、useCallback）
- [ ] 错误边界处理

### 7.6 后端规范检查清单

- [ ] API 遵循 RESTful 设计
- [ ] 输入验证完整
- [ ] 错误处理统一
- [ ] 日志记录完善
- [ ] 安全中间件配置
- [ ] 请求限流
- [ ] CORS 配置正确
- [ ] 环境变量管理
- [ ] 数据库连接池配置
- [ ] 优雅关闭处理

### 7.7 安全检查清单

- [ ] 无硬编码密钥
- [ ] 敏感数据加密存储
- [ ] SQL 注入防护
- [ ] XSS 防护
- [ ] CSRF 防护
- [ ] 输入验证和清理
- [ ] 认证和授权正确实现
- [ ] HTTPS 强制使用
- [ ] 安全头部配置
- [ ] 依赖安全审计

---

## 附录

### A. 推荐工具

| 工具 | 用途 | 链接 |
|------|------|------|
| ESLint | 代码检查 | https://eslint.org |
| Prettier | 代码格式化 | https://prettier.io |
| TypeScript | 类型检查 | https://www.typescriptlang.org |
| Vitest | 单元测试 | https://vitest.dev |
| Playwright | E2E 测试 | https://playwright.dev |
| Turborepo | Monorepo 管理 | https://turbo.build |
| pnpm | 包管理 | https://pnpm.io |
| tsup | 构建工具 | https://tsup.egoist.dev |

### B. 参考资源

- [TypeScript 官方文档](https://www.typescriptlang.org/docs/)
- [Node.js 最佳实践](https://github.com/goldbergyoni/nodebestpractices)
- [React 文档](https://react.dev)
- [Vue 文档](https://vuejs.org)
- [Angular 文档](https://angular.io)
- [NestJS 文档](https://docs.nestjs.com)
- [Fastify 文档](https://fastify.dev)
