# SDD 项目模板

## 一、SDD 项目概述

SDD（Specification-Driven Development，规范驱动开发）项目是一种以规范文件为核心驱动开发流程的项目结构。通过将业务需求、技术规范、接口定义等内容以结构化的方式组织，实现开发过程的标准化和可追溯性。

### 核心理念

1. **规范先行**：在编码之前先定义规范，确保需求清晰
2. **文档驱动**：规范文件作为开发的核心依据
3. **结构化组织**：规范文件按类型和模块分类管理
4. **版本可控**：规范文件纳入版本管理，便于追溯

---

## 二、项目目录结构

```
project_name/
├── .sdd/                          # SDD 配置目录
│   ├── config.yaml               # SDD 配置文件
│   └── templates/                # 规范模板目录
│       ├── requirement.md        # 需求规范模板
│       ├── design.md             # 设计规范模板
│       └── api.md                # API 规范模板
│
├── specs/                         # 规范文件目录
│   ├── requirements/             # 需求规范
│   │   ├── overview.md           # 需求概述
│   │   ├── functional/           # 功能需求
│   │   │   ├── user-module.md
│   │   │   └── order-module.md
│   │   └── non-functional/       # 非功能需求
│   │       ├── performance.md
│   │       └── security.md
│   │
│   ├── designs/                  # 设计规范
│   │   ├── architecture.md       # 架构设计
│   │   ├── database/             # 数据库设计
│   │   │   ├── schema.md
│   │   │   └── migrations.md
│   │   └── modules/              # 模块设计
│   │       ├── user-service.md
│   │       └── order-service.md
│   │
│   ├── apis/                     # API 规范
│   │   ├── rest/                 # REST API
│   │   │   ├── user-api.md
│   │   │   └── order-api.md
│   │   └── graphql/              # GraphQL 规范
│   │       └── schema.graphql
│   │
│   ├── contracts/                # 契约规范
│   │   ├── events/               # 事件契约
│   │   └── messages/             # 消息契约
│   │
│   └── tests/                    # 测试规范
│       ├── test-plan.md          # 测试计划
│       ├── test-cases/           # 测试用例
│       └── test-data/            # 测试数据规范
│
├── src/                          # 源码目录
│   ├── modules/                  # 业务模块
│   │   ├── user/
│   │   └── order/
│   ├── core/                     # 核心模块
│   ├── shared/                   # 共享模块
│   └── main/                     # 入口文件
│
├── tests/                        # 测试目录
│   ├── unit/                     # 单元测试
│   ├── integration/              # 集成测试
│   └── e2e/                      # 端到端测试
│
├── docs/                         # 文档目录
│   ├── guides/                   # 开发指南
│   └── references/               # 参考文档
│
├── scripts/                      # 脚本目录
│   ├── setup.sh                  # 项目初始化脚本
│   └── validate-specs.sh         # 规范验证脚本
│
├── .sddignore                    # SDD 忽略文件
├── README.md                     # 项目说明
└── CHANGELOG.md                  # 变更日志
```

---

## 三、规范文件存放位置

### 3.1 规范目录说明

| 目录路径 | 用途 | 说明 |
|---------|------|------|
| `specs/requirements/` | 需求规范 | 存放业务需求、功能需求、非功能需求等规范文件 |
| `specs/designs/` | 设计规范 | 存放架构设计、数据库设计、模块设计等规范文件 |
| `specs/apis/` | API 规范 | 存放 REST API、GraphQL、RPC 接口规范文件 |
| `specs/contracts/` | 契约规范 | 存放事件契约、消息契约等接口契约文件 |
| `specs/tests/` | 测试规范 | 存放测试计划、测试用例、测试数据规范文件 |

### 3.2 规范文件层级

```
specs/
├── {规范类型}/
│   ├── {模块名}/
│   │   ├── {子模块名}/
│   │   │   └── {规范文件}.md
│   │   └── {规范文件}.md
│   └── {规范文件}.md
```

---

## 四、规范文件命名规范

### 4.1 命名规则

| 规范类型 | 命名格式 | 示例 |
|---------|---------|------|
| 需求规范 | `{模块名}-requirement.md` | `user-requirement.md` |
| 功能需求 | `{功能名}-functional.md` | `login-functional.md` |
| 设计规范 | `{模块名}-design.md` | `user-service-design.md` |
| 数据库设计 | `{表名}-schema.md` | `user-schema.md` |
| API 规范 | `{资源名}-api.md` | `user-api.md` |
| 测试规范 | `{模块名}-test.md` | `user-test.md` |

### 4.2 文件命名约定

- 使用小写字母
- 使用连字符（-）分隔单词
- 文件名应具有描述性
- 使用 `.md` 扩展名（Markdown 格式）
- 特殊格式文件使用对应扩展名（如 `.graphql`、`.yaml`）

### 4.3 版本标识

当规范文件需要版本管理时，可采用以下命名方式：

```
{规范名}-v{版本号}.md

示例：
user-api-v1.0.0.md
user-api-v1.1.0.md
```

---

## 五、项目初始化流程

### 5.1 初始化步骤

```bash
# 1. 创建项目目录
mkdir project_name && cd project_name

# 2. 创建 SDD 配置目录
mkdir -p .sdd/templates

# 3. 创建规范目录结构
mkdir -p specs/{requirements/{functional,non-functional},designs/{database,modules},apis/{rest,graphql},contracts/{events,messages},tests/{test-cases,test-data}}

# 4. 创建源码目录
mkdir -p src/{modules,core,shared,main}

# 5. 创建测试目录
mkdir -p tests/{unit,integration,e2e}

# 6. 创建文档目录
mkdir -p docs/{guides,references}

# 7. 创建脚本目录
mkdir scripts

# 8. 创建配置文件
touch .sdd/config.yaml
touch .sddignore
touch README.md
touch CHANGELOG.md
```

### 5.2 配置文件示例

**.sdd/config.yaml**

```yaml
sdd:
  version: "1.0.0"
  project:
    name: "project_name"
    description: "项目描述"
  
  specs:
    root: "specs"
    templates: ".sdd/templates"
  
  validation:
    enabled: true
    strict: true
  
  output:
    docs: "docs"
    tests: "tests"
```

**.sddignore**

```
# 临时文件
*.tmp
*.temp

# 编译输出
dist/
build/

# 依赖目录
node_modules/
vendor/

# IDE 配置
.idea/
.vscode/
```

---

## 六、完整示例项目结构

### 6.1 电商系统示例

```
ecommerce-system/
├── .sdd/
│   ├── config.yaml
│   └── templates/
│       ├── requirement.md
│       ├── design.md
│       └── api.md
│
├── specs/
│   ├── requirements/
│   │   ├── overview.md
│   │   ├── functional/
│   │   │   ├── user-management.md
│   │   │   ├── product-catalog.md
│   │   │   ├── shopping-cart.md
│   │   │   ├── order-processing.md
│   │   │   └── payment-integration.md
│   │   └── non-functional/
│   │       ├── performance.md
│   │       ├── security.md
│   │       └── scalability.md
│   │
│   ├── designs/
│   │   ├── architecture.md
│   │   ├── database/
│   │   │   ├── user-schema.md
│   │   │   ├── product-schema.md
│   │   │   ├── order-schema.md
│   │   │   └── payment-schema.md
│   │   └── modules/
│   │       ├── user-service-design.md
│   │       ├── product-service-design.md
│   │       ├── order-service-design.md
│   │       └── payment-service-design.md
│   │
│   ├── apis/
│   │   ├── rest/
│   │   │   ├── user-api.md
│   │   │   ├── product-api.md
│   │   │   ├── order-api.md
│   │   │   └── payment-api.md
│   │   └── graphql/
│   │       └── schema.graphql
│   │
│   ├── contracts/
│   │   ├── events/
│   │   │   ├── order-events.md
│   │   │   └── payment-events.md
│   │   └── messages/
│   │       ├── notification-messages.md
│   │       └── integration-messages.md
│   │
│   └── tests/
│       ├── test-plan.md
│       ├── test-cases/
│       │   ├── user-test-cases.md
│       │   ├── product-test-cases.md
│       │   └── order-test-cases.md
│       └── test-data/
│           ├── user-test-data.md
│           └── product-test-data.md
│
├── src/
│   ├── modules/
│   │   ├── user/
│   │   ├── product/
│   │   ├── order/
│   │   └── payment/
│   ├── core/
│   ├── shared/
│   └── main/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/
│   ├── guides/
│   │   ├── getting-started.md
│   │   └── development-guide.md
│   └── references/
│       └── api-reference.md
│
├── scripts/
│   ├── setup.sh
│   └── validate-specs.sh
│
├── .sddignore
├── README.md
└── CHANGELOG.md
```

### 6.2 规范文件示例

**specs/requirements/functional/user-management.md**

```markdown
# 用户管理功能需求

## 概述

用户管理模块负责处理用户注册、登录、信息管理等核心功能。

## 功能列表

### 1. 用户注册

- 支持邮箱注册
- 支持手机号注册
- 支持第三方账号注册（微信、支付宝）

### 2. 用户登录

- 支持账号密码登录
- 支持验证码登录
- 支持第三方账号登录

### 3. 用户信息管理

- 查看个人信息
- 修改个人信息
- 修改密码

## 业务规则

1. 用户名长度：4-20 个字符
2. 密码强度：至少包含大小写字母和数字
3. 手机号格式：中国大陆手机号

## 验收标准

- [ ] 用户注册功能正常
- [ ] 用户登录功能正常
- [ ] 用户信息管理功能正常
```

---

## 七、最佳实践

### 7.1 规范文件编写建议

1. **清晰简洁**：规范内容应清晰明了，避免歧义
2. **结构化**：使用标题、列表、表格等结构化元素
3. **可追溯**：规范文件应包含版本信息和变更记录
4. **可验证**：规范内容应可测试、可验证

### 7.2 目录管理建议

1. **按模块组织**：规范文件按业务模块分类存放
2. **按类型区分**：不同类型的规范存放在对应目录
3. **保持一致**：项目间目录结构保持一致
4. **定期清理**：及时清理过时的规范文件

### 7.3 版本控制建议

1. 规范文件纳入 Git 版本控制
2. 使用语义化版本号管理规范变更
3. 重要变更记录在 CHANGELOG.md
4. 使用 Git 分支管理规范开发

---

## 八、附录

### 8.1 常用命令

```bash
# 验证规范文件
./scripts/validate-specs.sh

# 生成文档
sdd generate-docs

# 同步规范
sdd sync-specs
```

### 8.2 相关资源

- [SDD 规范模板](./sdd_guifan_muban.md)
- [项目初始化指南](./ai_xiangmu.md)
- [Web 项目模板](./web_xiangmu.md)
