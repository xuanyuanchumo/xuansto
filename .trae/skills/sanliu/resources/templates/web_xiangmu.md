# Web 项目模板

本文档提供 Web 项目的标准模板，包含前端、后端和数据库设计模板。

## 一、前端项目结构模板

### 1.1 Vue 项目结构

```
project-frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── api/                    # API 接口层
│   │   ├── index.ts            # API 统一导出
│   │   ├── request.ts          # Axios 封装
│   │   └── modules/            # API 模块
│   │       ├── user.ts
│   │       └── project.ts
│   ├── assets/                 # 静态资源
│   │   ├── images/
│   │   └── styles/
│   │       ├── variables.scss
│   │       └── global.scss
│   ├── components/             # 公共组件
│   │   ├── common/
│   │   │   ├── Button.vue
│   │   │   └── Modal.vue
│   │   └── business/
│   │       └── UserCard.vue
│   ├── composables/            # 组合式函数
│   │   ├── useAuth.ts
│   │   └── useNotification.ts
│   ├── directives/             # 自定义指令
│   │   └── permission.ts
│   ├── layouts/                # 布局组件
│   │   ├── DefaultLayout.vue
│   │   └── BlankLayout.vue
│   ├── router/                 # 路由配置
│   │   ├── index.ts
│   │   └── guards.ts
│   ├── stores/                 # 状态管理 (Pinia)
│   │   ├── index.ts
│   │   ├── user.ts
│   │   └── app.ts
│   ├── types/                  # TypeScript 类型定义
│   │   ├── api.d.ts
│   │   └── global.d.ts
│   ├── utils/                  # 工具函数
│   │   ├── storage.ts
│   │   ├── date.ts
│   │   └── validate.ts
│   ├── views/                  # 页面视图
│   │   ├── home/
│   │   │   └── Index.vue
│   │   └── user/
│   │       ├── List.vue
│   │       └── Detail.vue
│   ├── App.vue
│   └── main.ts
├── .env                        # 环境变量
├── .env.development
├── .env.production
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

### 1.2 React 项目结构

```
project-frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── api/                    # API 接口层
│   │   ├── index.ts
│   │   ├── request.ts
│   │   └── modules/
│   ├── assets/                 # 静态资源
│   ├── components/             # 组件
│   │   ├── common/             # 通用组件
│   │   ├── layout/             # 布局组件
│   │   └── business/           # 业务组件
│   ├── hooks/                  # 自定义 Hooks
│   │   ├── useAuth.ts
│   │   └── useRequest.ts
│   ├── pages/                  # 页面
│   │   ├── Home/
│   │   │   ├── index.tsx
│   │   │   └── styles.module.css
│   │   └── User/
│   ├── router/                 # 路由配置
│   │   ├── index.tsx
│   │   └── routes.ts
│   ├── store/                  # 状态管理 (Redux/Zustand)
│   │   ├── index.ts
│   │   ├── slices/
│   │   └── hooks.ts
│   ├── styles/                 # 全局样式
│   │   ├── variables.css
│   │   └── global.css
│   ├── types/                  # TypeScript 类型
│   ├── utils/                  # 工具函数
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
├── .env
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## 二、后端项目结构模板

### 2.1 FastAPI 项目结构

```
project-backend/
├── app/
│   ├── api/                    # API 路由
│   │   ├── __init__.py
│   │   ├── deps.py             # 依赖注入
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── endpoints/
│   │       │   ├── __init__.py
│   │       │   ├── users.py
│   │       │   └── projects.py
│   │       └── router.py
│   ├── core/                   # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py           # 配置管理
│   │   ├── security.py         # 安全相关
│   │   └── exceptions.py       # 异常处理
│   ├── models/                 # 数据库模型
│   │   ├── __init__.py
│   │   ├── base.py             # 基础模型
│   │   ├── user.py
│   │   └── project.py
│   ├── schemas/                # Pydantic 模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── project.py
│   ├── services/               # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   └── project_service.py
│   ├── repositories/           # 数据访问层
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── user_repo.py
│   ├── utils/                  # 工具函数
│   │   ├── __init__.py
│   │   └── helpers.py
│   ├── db/                     # 数据库相关
│   │   ├── __init__.py
│   │   ├── session.py          # 数据库会话
│   │   └── migrations/         # 迁移文件
│   ├── main.py                 # 应用入口
│   └── __init__.py
├── tests/                      # 测试
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api/
│   └── test_services/
├── alembic.ini                 # Alembic 配置
├── requirements.txt
├── pyproject.toml
├── .env.example
├── Dockerfile
└── README.md
```

### 2.2 Express 项目结构

```
project-backend/
├── src/
│   ├── config/                 # 配置
│   │   ├── index.ts
│   │   ├── database.ts
│   │   └── logger.ts
│   ├── controllers/            # 控制器
│   │   ├── userController.ts
│   │   └── projectController.ts
│   ├── middlewares/            # 中间件
│   │   ├── auth.ts
│   │   ├── error.ts
│   │   └── validate.ts
│   ├── models/                 # 数据模型
│   │   ├── User.ts
│   │   └── Project.ts
│   ├── routes/                 # 路由
│   │   ├── index.ts
│   │   ├── userRoutes.ts
│   │   └── projectRoutes.ts
│   ├── services/               # 业务逻辑
│   │   ├── userService.ts
│   │   └── projectService.ts
│   ├── repositories/           # 数据访问
│   │   ├── userRepository.ts
│   │   └── projectRepository.ts
│   ├── types/                  # TypeScript 类型
│   │   ├── express.d.ts
│   │   └── models.d.ts
│   ├── utils/                  # 工具函数
│   │   ├── response.ts
│   │   └── validation.ts
│   ├── validators/             # 请求验证
│   │   ├── userValidator.ts
│   │   └── projectValidator.ts
│   └── app.ts                  # 应用入口
├── tests/                      # 测试
│   ├── unit/
│   └── integration/
├── package.json
├── tsconfig.json
├── .env.example
├── Dockerfile
└── README.md
```

## 三、数据库设计模板

### 3.1 关系型数据库设计规范

```sql
-- 用户表
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- 项目表
CREATE TABLE projects (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    owner_id BIGINT NOT NULL REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_projects_owner ON projects(owner_id);
CREATE INDEX idx_projects_status ON projects(status);
```

### 3.2 MongoDB 设计规范

```javascript
// 用户集合
db.createCollection("users", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["username", "email", "password_hash"],
            properties: {
                username: {
                    bsonType: "string",
                    minLength: 3,
                    maxLength: 50
                },
                email: {
                    bsonType: "string",
                    pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
                },
                password_hash: {
                    bsonType: "string"
                },
                status: {
                    enum: ["active", "inactive", "suspended"],
                    default: "active"
                },
                created_at: {
                    bsonType: "date"
                },
                updated_at: {
                    bsonType: "date"
                }
            }
        }
    }
});

// 索引
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "username": 1 }, { unique: true });
```

## 四、技术栈选型建议

### 4.1 前端技术栈

| 场景 | 推荐技术栈 | 说明 |
|------|-----------|------|
| 企业级应用 | Vue 3 + TypeScript + Pinia + Element Plus | 适合中大型项目，生态完善 |
| 高性能应用 | React + TypeScript + Zustand + Ant Design | 适合复杂交互场景 |
| 移动端应用 | Vue 3 + Vant / React + Ant Design Mobile | 跨平台移动端开发 |
| 轻量级应用 | Vue 3 + Vite + TailwindCSS | 快速开发，体积小 |

### 4.2 后端技术栈

| 场景 | 推荐技术栈 | 说明 |
|------|-----------|------|
| 高性能 API | FastAPI + PostgreSQL + Redis | 异步支持好，自动文档 |
| 企业级服务 | Express/NestJS + MySQL + Redis | 生态成熟，社区活跃 |
| 微服务架构 | FastAPI + gRPC + PostgreSQL | 服务间通信高效 |
| 实时应用 | FastAPI + WebSocket + Redis Pub/Sub | 支持实时通信 |

### 4.3 数据库选型

| 场景 | 推荐数据库 | 说明 |
|------|-----------|------|
| 关系型数据 | PostgreSQL | 功能强大，扩展性好 |
| 简单关系型 | MySQL | 生态成熟，运维简单 |
| 文档存储 | MongoDB | 灵活的数据结构 |
| 缓存层 | Redis | 高性能键值存储 |
| 搜索引擎 | Elasticsearch | 全文搜索，日志分析 |

## 五、配置文件示例

### 5.1 前端配置文件

**package.json**
```json
{
    "name": "project-frontend",
    "version": "1.0.0",
    "type": "module",
    "scripts": {
        "dev": "vite",
        "build": "vue-tsc && vite build",
        "preview": "vite preview",
        "lint": "eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx --fix",
        "test": "vitest"
    },
    "dependencies": {
        "vue": "^3.4.0",
        "vue-router": "^4.2.0",
        "pinia": "^2.1.0",
        "axios": "^1.6.0"
    },
    "devDependencies": {
        "@vitejs/plugin-vue": "^5.0.0",
        "typescript": "^5.3.0",
        "vite": "^5.0.0",
        "vue-tsc": "^1.8.0"
    }
}
```

**vite.config.ts**
```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            '@': resolve(__dirname, 'src')
        }
    },
    server: {
        port: 3000,
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true
            }
        }
    }
})
```

### 5.2 后端配置文件

**requirements.txt (FastAPI)**
```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
sqlalchemy>=2.0.0
asyncpg>=0.29.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
alembic>=1.13.0
redis>=5.0.0
httpx>=0.26.0
```

**pyproject.toml**
```toml
[project]
name = "project-backend"
version = "1.0.0"
description = "Project Backend API"
requires-python = ">=3.10"

[tool.black]
line-length = 88
target-version = ['py310']

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.10"
strict = true
```

**.env.example**
```env
APP_NAME=ProjectAPI
APP_ENV=development
APP_DEBUG=true
APP_SECRET_KEY=your-secret-key-here

DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0

CORS_ORIGINS=["http://localhost:3000"]
```

## 六、开发流程说明

### 6.1 项目初始化流程

1. **创建项目仓库**
   - 初始化 Git 仓库
   - 配置 .gitignore
   - 创建开发分支

2. **搭建项目骨架**
   - 初始化前端项目
   - 初始化后端项目
   - 配置开发环境

3. **配置 CI/CD**
   - 配置自动化测试
   - 配置代码检查
   - 配置部署流程

### 6.2 开发规范

1. **分支管理**
   - main: 生产环境
   - develop: 开发环境
   - feature/*: 功能分支
   - hotfix/*: 紧急修复分支

2. **提交规范**
   - feat: 新功能
   - fix: 修复 Bug
   - docs: 文档更新
   - refactor: 代码重构
   - test: 测试相关

3. **代码审查**
   - 必须通过 CI 检查
   - 至少一人审核通过
   - 解决所有讨论问题

### 6.3 部署流程

1. **开发环境**
   - 本地开发调试
   - 运行单元测试
   - 代码格式检查

2. **测试环境**
   - 合并到 develop 分支
   - 自动部署到测试环境
   - 运行集成测试

3. **生产环境**
   - 合并到 main 分支
   - 创建版本标签
   - 自动部署到生产环境
