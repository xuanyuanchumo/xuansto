<!--
  模板说明: CHANGELOG (变更日志)
  用途: 按版本记录项目的所有变更，遵循 [Keep a Changelog](https://keepachangelog.com/) 标准
  变量列表:
    {{project_name}}           - 项目名称
    {{version}}                - 当前版本号
    {{date}}                   - 发布日期
    {{changes_added}}          - 新增功能列表
    {{changes_changed}}        - 变更/改进列表
    {{changes_deprecated}}     - 废弃功能列表
    {{changes_removed}}        - 移除功能列表
    {{changes_fixed}}          - 修复问题列表
    {{changes_security}}       - 安全修复列表
  使用方式: 放在项目根目录的 CHANGELOG.md，每次发布时在顶部添加新版本条目。
         格式: ## [版本号] - YYYY-MM-DD → 分类(Added/Changed/...) → 变更项
  参考: https://keepachangelog.com/en/1.1.0/
-->

# Changelog

All notable changes to the **{{project_name | default('project')}}** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
<!-- COMMENT: 正在开发中但尚未发布的变更写在这里 -->

- <!-- COMMENT: 示例: 新增用户头像裁剪功能 (#123) by @zhangsan -->
- <!-- COMMENT: 示例: 支持订单导出为Excel格式 (#124) by @lisi -->

### Changed
- <!-- COMMENT: 示例: 优化首页加载性能，FCP从3s降低至1.5s (#125) -->

### Deprecated
- <!-- COMMENT: 示例: `GET /api/v1/users/list` 接口将在 v2.0 中移除，请改用 `POST /api/v1/users/search` -->

### Removed
- <!-- COMMENT: (Unreleased阶段通常不会有Removed) -->

### Fixed
- <!-- COMMENT: 示例: 修复支付回调偶发超时的问题 (#126) -->

### Security
- <!-- COMMENT: 示例: 升级spring-framework至5.3.30修复CVE-2024-XXXXX (#127) -->

---

## [{{version | default('1.0.0')}}] - {{date | default('2024-03-21')}}

### 🎉 Added (新增功能)

#### 用户认证模块
- 完整的用户注册流程（手机号+验证码注册）(#001) by @dev-zhang
- 手机号+密码登录功能，支持JWT双Token机制（Access 15min + Refresh 7d）(#002) by @dev-zhang
- 忘记密码通过短信验证码重置功能(#003) by @dev-zhang
- 短信验证码发送与校验（支持注册/登录/重置密码/换绑等场景）(#004) by @dev-li
- 登录安全防护：连续失败5次锁定15分钟、Token黑名单机制(#005) by @dev-zhang

#### 用户管理模块
- 个人信息查看与编辑（昵称/简介/性别/地区等）(#010) by @dev-wang
- 头像上传功能（支持JPG/PNG/GIF，≤2MB，自动裁剪压缩）(#011) by @dev-wang
- 密码修改功能（需验证旧密码）(#012) by @dev-zhang
- 绑定手机号/邮箱更换（二次身份验证）(#013) by @dev-zhang

#### 订单系统
- 订单完整生命周期管理：创建→支付→发货→签收→完成→取消/退款(#020) by @dev-li
- 订单状态机引擎（7种状态+合法流转规则）(#021) by @dev-li
- 订单列表分页查询（支持多维度筛选：状态/时间范围/关键词）(#022) by @dev-li
- 订单详情展示（含商品快照、时间线、物流信息）(#023) by @dev-wang
- 超时未支付订单自动关闭（定时任务，默认30分钟）(#024) by @dev-li

#### 支付集成
- 支付宝即时到账支付接入(#030) by @dev-zhang
- 微信支付(JSAPI/H5)接入(#031) by @dev-zhang
- 支付结果异步通知回调处理（含签名验签防篡改）(#032) by @dev-zhang
- 支付幂等性保障（防止重复扣款）(#033) by @dev-zhang
- 余额支付功能(#034) by @dev-li

#### 文件服务
- 通用文件上传接口（支持多格式，OSS存储）(#040) by @dev-wang
- 文件下载与预览(#041) by @dev-wang
- 图片处理服务（自动生成缩略图：48px/96px/192px）(#042) by @dev-wang

#### 数据统计
- 运营数据概览Dashboard（新增用户/活跃用户/订单量/收入等核心指标）(#050) by @dev-wang
- 数据报表导出功能（支持Excel/CSV格式）(#051) by @dev-wang
- 趋势图表数据API（按日/周/月聚合）(#052) by @dev-wang

#### 管理后台
- RBAC权限管理系统（角色/菜单/按钮级权限控制）(#060) by @dev-li
- 用户管理CRUD（查看/搜索/封禁/解禁）(#061) by @dev-li
- 内容审核功能(#062) by @dev-wang
- 系统配置管理（动态参数调整，无需重启）(#063) by @dev-zhang

### 🔧 Changed (改进与优化)

#### 性能优化
- 首页接口响应时间从800ms优化至150ms（Redis缓存热点数据 + SQL索引优化）(#100) by @dev-li
- 商品列表查询引入Elasticsearch，复杂筛选条件响应时间<200ms(#101) by @dev-zhang
- 前端构建产物体积减少40%（Tree Shaking + 代码分割 + Gzip压缩）(#102) by @fe-zhao
- 数据库连接池优化（HikariCP调优，连接等待从5s降至500ms）(#103) by @dev-li
- API网关层增加本地缓存（Nginx proxy_cache，静态资源命中率>90%）(#104) by @ops-sun

#### 代码质量
- 引入SonarQube代码质量门禁（新代码覆盖率≥80%，无Blocker/Vulnerability）(#110) by @dev-all
- 统一异常处理体系（GlobalExceptionHandler + 错误码规范）(#111) by @dev-zhang
- API响应格式标准化（统一ApiResponse包装结构）(#112) by @dev-li
- 日志规范化（结构化JSON日志 + TraceId全链路追踪）(#113) by @dev-zhang
- 引入MapStruct替代手工Bean拷贝（减少样板代码约500行）(#114) by @dev-wang

#### 安全加固
- 全站强制HTTPS（HSTS + SSL证书自动续期Let's Encrypt）(#120) by @ops-sun
- CORS策略收紧（白名单模式替代通配符*）(#121) by @dev-zhang
- SQL注入防护增强（所有MyBatis查询使用#{}参数化）(#122) by @dev-li
- XSS防护升级（DOMPurify前端过滤 + CSP策略后端设置）(#123) by @fe-zhao & @dev-zhang
- 敏感数据脱敏（手机号/身份证号/银行卡号返回时掩码显示）(#124) by @dev-zhang
- 接口限流升级（令牌桶算法 + IP维度的滑动窗口限流）(#125) by @dev-zhang

#### 用户体验
- 注册/登录表单实时字段校验（输入即反馈，无需提交后报错）(#130) by @fe-zhao
- 全局Loading骨架屏替代Spinner（感知加载速度提升）(#131) by @fe-zhao
- 操作成功/失败Toast提示全局统一风格(#132) by @fe-zhao
- 表格组件增加虚拟滚动（万级数据渲染不卡顿）(#133) by @fe-zhao
- 移动端响应式适配完善（375px~428px屏幕全覆盖）(#134) by @fe-qian

### ⚠️ Deprecated (已废弃)

- `GET /api/v1/users` — 用户列表接口将在 **v2.0** 中移除，请迁移至 `POST /api/v1/users/search` (#200)
- `Basic Auth` 认证方式 — 将在 **v1.2** 中移除，请全面切换至 JWT Bearer Token 认证 (#201)
- `order.status` 字段值 `'UNPAID'` — 将在 **v1.1** 中替换为 `'PENDING_PAYMENT'`，建议提前适配 (#202)
- 前端 `antd@4.x` 组件库依赖 — 将在 **v2.0** 升级至 antd@5.x (#203)
- MySQL 数据库支持 — 将在 **v2.0** 中完全迁移至 PostgreSQL，新功能不再兼容MySQL (#204)

### ❌ Removed (已移除)

- ~~旧版用户Session管理（基于Cookie的Session）~~ — 已被JWT Token方案完全替代 (#300)
- ~~硬编码的配置文件~~ — 已全部外部化至环境变量/K8s ConfigMap (#301)
- ~~Swagger UI（生产环境）~~ — 生产环境移除API文档暴露，保留开发/测试环境 (#302)
- ~~console.log调试语句~~ — 代码清理，所有debug日志改为Logger级别控制 (#303) by @fe-zhao

### 🐛 Fixed (Bug修复)

#### 高优先级修复
- **修复**: 支付金额在极端并发场景下计算错误的严重Bug（金额精度丢失导致分差）(#400) by @dev-zhang
- **修复**: 订单库存扣减存在竞态条件（并发下单导致超卖）— 引入分布式锁+数据库乐观锁双重保障(#401) by @dev-li
- **修复**: JWT Token在密码修改后未失效的安全漏洞(#402) by @dev-zhang
- **修复**: 文件上传路径穿越漏洞（可通过../访问非授权目录）(#403) by @dev-wang
- **修复**: Redis缓存与数据库不一致导致的用户信息显示错误(#404) by @dev-li

#### 中优先级修复
- **修复**: 订单列表分页在大量数据下查询缓慢（添加复合索引后从5s降至200ms）(#410) by @dev-li
- **修复**: 导出Excel文件名中文乱码（URL编码处理）(#411) by @dev-wang
- **修复**: 移动端键盘弹出时遮挡输入框的问题(#412) by @fe-qian
- **修复**: 验证码倒计时不准确的UI问题(#413) by @fe-zhao
- **修复**: 浏览器后退按钮导致重复提交表单(#414) by @fe-zhao
- **修复**: 时区处理错误导致日期显示偏差8小时(#415) by @dev-zhang

#### 低优先级修复
- **修复**: 某些浏览器下滚动条样式不一致(#420) by @fe-qian
- **修复**: 暗色模式下部分图标颜色对比度不足(WCAG AA不达标)(#421) by @fe-zhao
- **修复**: 表格排序在空数据时报错(#422) by @fe-zhao
- **修复**: 长文本自动省略号截断位置不准确(#423) by @fe-qian

### 🔒 Security (安全修复)

- 升级 `spring-framework` 至 5.3.30 修复 [CVE-2024-XXXXX](https://cve.mitre.org/) (DoS漏洞) (#500) by @dev-zhang
- 升级 `jackson-databind` 至 2.15.3 修复反序列化漏洞(CVE-2023-XXX) (#501) by @dev-zhang
- 升级 `nginx` 至 1.24.0 修复 HTTP/2 快速流重置漏洞(CVE-2024-XXX) (#502) by @ops-sun
- 修复 OSS AccessKey 泄露风险（改用STS临时凭证 + RAM子账号最小权限）(#503) by @ops-sun
- 新增 Security Headers: Content-Security-Policy / X-Content-Type-Options / X-Frame-Options (#504) by @dev-zhang

---

## Migration Guide (迁移指南)

<!-- COMMENT: 当有Breaking Change时，在此提供详细的迁移指南 -->

### 从 v0.x 升级到 v1.0.0

本版本包含以下**破坏性变更(Breaking Changes)**，升级前请仔细阅读：

#### 1. 认证方式变更

**之前**:
```http
Authorization: Basic dXNlcjpwYXNzd29yZA==
```

**现在**:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**迁移步骤**:
1. 更新所有API客户端的认证头格式
2. 登录接口返回新的Token结构体
3. 实现 Token 自动刷新逻辑（Refresh Token轮换）

#### 2. 订单状态枚举值变更

| 旧值 | 新值 | 说明 |
|------|------|------|
| `UNPAID` | `PENDING_PAYMENT` | 待支付 |
| `PAID` | `PAID` | 已付款（不变） |
| `SHIPPED` | `SHIPPED` | 已发货（不变） |

**影响**: 如果有代码硬编码了 `"UNPAID"` 字符串，需要更新为 `"PENDING_PAYMENT"`

```python
# Before
if order.status == "UNPAID":
    # ...

# After
if order.status == "PENDING_PAYMENT":
    # ...
```

#### 3. 数据库迁移

本次升级需要执行数据库迁移脚本：

```bash
# 使用Flyway自动迁移（推荐）
flyway migrate -url=jdbc:postgresql://localhost:5432/skiller_db \
               -user=flyway \
               -password=xxx \
               -locations=classpath:db/migration

# 或手动执行SQL
psql -U skiller_user -d skiller_db -f sql/migrations/V1.0.0__upgrade_from_v0.sql
```

**主要DDL变更**:
- `orders` 表新增 `payment_method` 列
- `users` 表 `status` 列类型从 TINYINTINT 改为 ENUM
- 新增 `operation_logs` 操作审计表
- 新增 `user_roles` 多对多关联表

#### 4. 配置文件变更

新增以下必填环境变量（之前使用默认值即可）：

```bash
# 新增必须配置
export JWT_SECRET=<your-32-char-random-secret>
export ALIPAY_APP_ID=<your-alipay-app-id>
export ALIPAY_PRIVATE_KEY=<your-alipay-private-key>
export OSS_ACCESS_KEY_ID=<your-oss-ak>
export OSS_ACCESS_KEY_SECRET=<your-oss-sk>
```

---

## [0.9.0-beta] - 2024-02-15

### Added
- Beta版首次发布，包含核心MVP功能
- 用户注册/登录基础功能
- 商品浏览和搜索
- 基础购物车功能

### Fixed
- 修复了若干Beta测试期间发现的稳定性问题

---

## [0.1.0-alpha] - 2024-01-10

### Added
- 项目初始化
- 基础脚手架搭建
- CI/CD流水线初始配置

---

*Changelog format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).*
