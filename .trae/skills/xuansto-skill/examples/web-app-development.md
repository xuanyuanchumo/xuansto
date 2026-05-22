# Web应用开发示例：用户认证系统

## 场景描述

开发一个完整的用户认证系统，包括注册、登录、密码重置、多因素认证（MFA）和会话管理功能。系统需要支持OAuth2.0社交登录，并满足OWASP安全标准。技术栈：React + TypeScript（前端）、Node.js + Express（后端）、PostgreSQL（数据库）。

---

## Phase 0：需求分析与项目启动

### Agent分配

| Agent | 职责 |
|-------|------|
| Product Manager | 需求收集、用户故事编写、优先级排序 |
| System Architect | 技术可行性评估、架构初步规划 |
| Specification Keeper | 规格文档管理、需求追踪 |

### 工作流程

1. **Product Manager** 收集认证系统需求，编写用户故事：
   - US-001：用户通过邮箱注册账户
   - US-002：用户通过邮箱/密码登录
   - US-003：用户通过OAuth2.0社交登录（Google、GitHub）
   - US-004：用户重置密码
   - US-005：用户启用/禁用MFA
   - US-006：管理员管理用户会话

2. **System Architect** 评估技术方案，确认技术栈选型，输出架构概要

3. **Specification Keeper** 创建规格文档，建立需求追踪矩阵

### 关键输出

- 产品需求文档（PRD）
- 用户故事列表（含验收标准）
- 技术可行性报告
- 需求追踪矩阵

### 质量门禁

- ✅ **REQ-COMPLETE**：所有用户故事具备验收标准
- ✅ **FEASIBILITY**：技术方案通过可行性评估

---

## Phase 1：架构设计与规格定义

### Agent分配

| Agent | 职责 |
|-------|------|
| System Architect | 系统架构设计、模块划分 |
| Data Modeler | 数据模型设计 |
| Security Auditor | 安全架构评审 |
| Specification Keeper | SDD文档编写与维护 |

### 工作流程

1. **System Architect** 设计认证系统架构：
   - 前端：React组件层 + 状态管理（Auth Context）
   - 后端：Express路由层 + 认证中间件 + 服务层
   - 数据层：PostgreSQL + Redis（会话缓存）
   - 安全层：JWT + CSRF防护 + Rate Limiting

2. **Data Modeler** 设计数据模型：
   - users表（id, email, password_hash, mfa_enabled, created_at...）
   - sessions表（id, user_id, token, expires_at...）
   - oauth_accounts表（id, user_id, provider, provider_id...）
   - mfa_secrets表（id, user_id, secret, backup_codes...）

3. **Security Auditor** 审查安全架构，提出安全要求：
   - 密码存储使用bcrypt（cost factor ≥ 12）
   - JWT使用RS256算法签名
   - 所有认证端点启用Rate Limiting
   - CSRF Token双重验证

4. **Specification Keeper** 编写规格驱动开发文档（SDD）

### 关键输出

- 系统架构设计文档
- 数据模型ER图
- API契约定义（OpenAPI 3.0）
- 安全架构评审报告
- SDD规格文档

### 质量门禁

- ✅ **ARCH-REVIEW**：架构设计通过评审
- ✅ **SEC-ARCH**：安全架构通过审计
- ✅ **API-CONTRACT**：API契约定义完整且无歧义

---

## Phase 2：测试先行（TDD）

### Agent分配

| Agent | 职责 |
|-------|------|
| Test Architect | 测试策略制定、测试架构设计 |
| Unit Tester | 单元测试编写 |
| Integration Tester | 集成测试编写 |
| Security Tester | 安全测试用例编写 |
| Specification Keeper | 测试规格同步 |

### 工作流程

1. **Test Architect** 制定测试策略：
   - 单元测试覆盖率目标：≥ 80%
   - 集成测试覆盖率目标：≥ 70%
   - 高风险模块（认证、密码处理）覆盖率：≥ 90%
   - 安全测试覆盖OWASP Top 10

2. **Unit Tester** 编写单元测试（先于实现代码）：
   - `auth.service.test.ts`：注册、登录、密码验证逻辑
   - `jwt.util.test.ts`：Token生成、验证、刷新逻辑
   - `password.util.test.ts`：密码哈希、验证、强度检查
   - `mfa.service.test.ts`：MFA启用、验证、备份码逻辑
   - `session.service.test.ts`：会话创建、验证、销毁逻辑

3. **Integration Tester** 编写集成测试：
   - `auth.api.test.ts`：注册/登录API端到端测试
   - `oauth.api.test.ts`：OAuth流程集成测试
   - `session.api.test.ts`：会话管理集成测试
   - `password-reset.api.test.ts`：密码重置流程测试

4. **Security Tester** 编写安全测试：
   - SQL注入测试
   - XSS攻击测试
   - CSRF防护测试
   - 暴力破解防护测试
   - JWT篡改测试

### 关键输出

- 测试策略文档
- 单元测试套件（全部RED状态）
- 集成测试套件（全部RED状态）
- 安全测试套件
- 测试覆盖率配置

### 质量门禁

- ✅ **TEST-FIRST**：所有核心功能具备先行的测试用例
- ✅ **TEST-COV-TARGET**：测试覆盖率目标已设定
- ✅ **SEC-TEST-PLAN**：安全测试计划完整

---

## Phase 3：核心实现

### Agent分配

| Agent | 职责 |
|-------|------|
| Backend Developer | 后端API实现 |
| Frontend Developer | 前端组件实现 |
| Database Engineer | 数据库迁移脚本 |
| Code Reviewer | 代码审查 |

### 工作流程

1. **Backend Developer** 实现后端服务：
   - 认证中间件（JWT验证、权限检查）
   - 注册服务（邮箱验证、密码强度校验）
   - 登录服务（凭证验证、Token签发）
   - OAuth服务（社交登录回调处理）
   - MFA服务（TOTP生成/验证、备份码管理）
   - 会话服务（会话创建/刷新/销毁）

2. **Frontend Developer** 实现前端组件：
   - LoginForm组件（邮箱/密码登录表单）
   - RegisterForm组件（注册表单含验证）
   - OAuthButtons组件（社交登录按钮组）
   - MFASetup组件（MFA绑定/解绑流程）
   - MFAVerify组件（MFA验证码输入）
   - PasswordReset组件（密码重置流程）
   - AuthContext（全局认证状态管理）
   - useAuth Hook（认证操作封装）

3. **Database Engineer** 编写数据库迁移：
   - `001_create_users_table.sql`
   - `002_create_sessions_table.sql`
   - `003_create_oauth_accounts_table.sql`
   - `004_create_mfa_secrets_table.sql`
   - `005_create_password_resets_table.sql`

4. **Code Reviewer** 进行代码审查，确保编码规范和安全标准

### 关键输出

- 后端API实现代码
- 前端组件实现代码
- 数据库迁移脚本
- 代码审查报告
- 单元测试转为GREEN状态

### 质量门禁

- ✅ **UNIT-PASS**：所有单元测试通过
- ✅ **CODE-REVIEW**：代码通过审查
- ✅ **SEC-CODE**：代码通过安全扫描（无高危漏洞）
- ✅ **COVERAGE**：测试覆盖率达标

---

## Phase 4：集成与端到端测试

### Agent分配

| Agent | 职责 |
|-------|------|
| Integration Tester | 集成测试执行与修复 |
| E2E Tester | 端到端测试编写与执行 |
| Performance Tester | 性能测试 |
| Security Tester | 渗透测试 |

### 工作流程

1. **Integration Tester** 执行集成测试，验证模块间协作：
   - 注册→邮箱验证→登录完整流程
   - OAuth授权→回调→用户创建/关联流程
   - MFA启用→登录验证→MFA校验流程
   - 密码重置→邮件发送→重置确认流程

2. **E2E Tester** 编写并执行端到端测试：
   - 用户注册完整流程（含邮箱验证）
   - 用户登录→访问受保护资源→登出
   - 社交登录完整流程
   - MFA启用→登录验证流程
   - 密码重置完整流程

3. **Performance Tester** 执行性能测试：
   - 登录接口响应时间 < 200ms（P95）
   - 注册接口响应时间 < 300ms（P95）
   - 并发登录支持 1000 QPS
   - Token验证响应时间 < 50ms（P95）

4. **Security Tester** 执行渗透测试：
   - 认证绕过测试
   - 权限提升测试
   - 会话劫持测试
   - OWASP Top 10全面检查

### 关键输出

- 集成测试报告（全部GREEN）
- E2E测试报告
- 性能测试报告
- 渗透测试报告
- 缺陷列表与修复记录

### 质量门禁

- ✅ **INTEGRATION-PASS**：所有集成测试通过
- ✅ **E2E-PASS**：所有端到端测试通过
- ✅ **PERF-BENCHMARK**：性能指标达标
- ✅ **SEC-PENTEST**：渗透测试通过（无高危漏洞）

---

## Phase 5：代码审查与重构

### Agent分配

| Agent | 职责 |
|-------|------|
| Code Reviewer | 全面代码审查 |
| Refactoring Specialist | 代码重构优化 |
| Security Auditor | 安全代码审计 |
| Doc Reviewer | 文档审查 |

### 工作流程

1. **Code Reviewer** 执行全面代码审查：
   - 编码规范一致性检查
   - 设计模式使用合理性
   - 错误处理完整性
   - 代码复杂度分析

2. **Refactoring Specialist** 执行重构：
   - 提取公共认证逻辑为工具函数
   - 优化错误处理中间件
   - 简化OAuth回调处理流程
   - 优化数据库查询性能

3. **Security Auditor** 执行安全代码审计：
   - 密码处理安全性确认
   - Token管理安全性确认
   - 输入验证完整性确认
   - 敏感数据保护确认

4. **Doc Reviewer** 审查文档完整性：
   - API文档与实现一致性
   - 部署文档完整性
   - 安全配置文档完整性

### 关键输出

- 代码审查报告
- 重构变更记录
- 安全审计报告
- 文档审查报告

### 质量门禁

- ✅ **REFACTOR-CLEAN**：重构后所有测试仍通过
- ✅ **SEC-AUDIT**：安全审计通过
- ✅ **DOC-COMPLETE**：文档完整且与实现一致

---

## Phase 6：部署与交付

### Agent分配

| Agent | 职责 |
|-------|------|
| DevOps Engineer | CI/CD流水线配置 |
| Build & Release Engineer | 构建与发布 |
| Runtime Supervisor | 运行时监控配置 |
| Technical Writer | 用户文档编写 |

### 工作流程

1. **DevOps Engineer** 配置CI/CD流水线：
   - 代码提交→自动测试→安全扫描→构建→部署
   - Staging环境自动部署
   - Production环境手动审批部署
   - 数据库迁移自动执行

2. **Build & Release Engineer** 执行构建与发布：
   - Docker镜像构建
   - 环境变量配置管理
   - 发布版本打标签
   - 部署到Staging验证

3. **Runtime Supervisor** 配置运行时监控：
   - 认证成功率监控
   - 登录失败告警（异常频率检测）
   - API响应时间监控
   - 会话活跃度监控

4. **Technical Writer** 编写用户文档：
   - API使用文档
   - 集成指南
   - 安全最佳实践文档

### 关键输出

- CI/CD流水线配置
- Docker镜像
- 部署配置文件
- 监控仪表盘
- 用户文档

### 质量门禁

- ✅ **DEPLOY-STAGING**：Staging环境部署成功
- ✅ **SMOKE-TEST**：冒烟测试通过
- ✅ **MONITOR-READY**：监控配置就绪
- ✅ **DOC-PUBLISH**：文档发布完成

---

## Phase 7：验收与知识沉淀

### Agent分配

| Agent | 职责 |
|-------|------|
| Product Manager | 验收确认 |
| QA Engineer | 最终验收测试 |
| Specification Keeper | 规格文档归档 |
| Documentation Engineer | 知识库更新 |

### 工作流程

1. **Product Manager** 执行验收：
   - 逐项验证用户故事完成情况
   - 确认验收标准全部满足
   - 签署验收确认

2. **QA Engineer** 执行最终验收测试：
   - 回归测试全量执行
   - 关键路径冒烟测试
   - 兼容性测试（浏览器覆盖）

3. **Specification Keeper** 归档规格文档：
   - SDD文档最终版本归档
   - 需求追踪矩阵最终状态
   - 变更记录归档

4. **Documentation Engineer** 更新知识库：
   - 认证系统架构知识入库
   - 安全方案经验提取
   - 常见问题与解决方案入库
   - 性能优化经验入库

### 关键输出

- 验收确认报告
- 最终测试报告
- 归档规格文档
- 知识库更新记录

### 质量门禁

- ✅ **ACCEPTANCE**：产品验收通过
- ✅ **REGRESSION-PASS**：回归测试通过
- ✅ **KB-UPDATED**：知识库已更新
- ✅ **DOC-ARCHIVED**：文档已归档

---

## 总结

本示例展示了使用xuansto-skill进行Web应用开发的完整流程：

- **8个阶段**：从需求分析到验收交付的完整生命周期
- **多Agent协作**：产品、架构、开发、测试、安全、运维等多角色协同
- **SDD+TDD融合**：规格驱动与测试驱动双轨保障质量
- **质量门禁**：每个阶段设有明确的质量检查点
- **知识沉淀**：项目经验自动提取并沉淀到知识库

通过xuansto-skill的编排能力，用户认证系统的开发过程实现了高度自动化、质量可追溯、安全有保障的目标。
