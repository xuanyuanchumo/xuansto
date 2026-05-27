# 错误类型标签索引

> 按错误类型分类索引所有错误类知识条目，便于快速定位相关经验。

## TypeError 类

| 条目ID | 标题 | 简短描述 |
|--------|------|----------|
| KP-EXP-ERR-003 | API 契约不匹配 | 前后端字段名/类型不一致导致 TypeError 读取 undefined 属性 |
| KP-EXP-ERR-002 | 空指针异常 | 访问 null/undefined/None 属性导致 TypeError |

## ReferenceError 类

| 条目ID | 标题 | 简短描述 |
|--------|------|----------|
| KP-EXP-ERR-003 | API 契约不匹配 | 接口变更后引用不存在的字段导致 ReferenceError |

## ImportError 类

| 条目ID | 标题 | 简短描述 |
|--------|------|----------|
| KP-EXP-DSK-BUILD-001 | Electron Builder 构建错误 | 原生模块 node-gyp 编译失败导致 import 错误 |
| KP-EXP-DSK-PLAT-001 | Windows/macOS 平台差异 | 文件名大小写不一致导致 Linux 上模块找不到 |

## OOM 类

| 条目ID | 标题 | 简短描述 |
|--------|------|----------|
| KP-EXP-ERR-DESK-001 | Electron 渲染进程崩溃 | V8 heap out of memory，未清理事件监听器/闭包导致内存泄漏 |
| KP-EXP-PERF-DB-001 | 数据库查询优化 | 连接池耗尽导致 OOM，N+1 查询内存膨胀 |

## Timeout 类

| 条目ID | 标题 | 简短描述 |
|--------|------|----------|
| KP-EXP-ERR-001 | 数据库连接超时 | 连接池耗尽/泄漏导致 acquire timeout |
| KP-EXP-PAT-API-001 | API 集成模式 | 第三方 API 调用超时，缺少重试/熔断机制 |

## ConnectionError 类

| 条目ID | 标题 | 简短描述 |
|--------|------|----------|
| KP-EXP-ERR-001 | 数据库连接超时 | 数据库连接池耗尽/网络问题导致连接失败 |
| KP-EXP-PAT-API-001 | API 集成模式 | 第三方 API 服务不可用 503 导致级联故障 |
| KP-EXP-INT-001 | 第三方 OAuth 集成问题 | CORS 阻止 token 交换端点请求 |

## 框架特定错误类

### Electron 错误

| 条目ID | 标题 | 简短描述 |
|--------|------|----------|
| KP-EXP-ERR-DESK-001 | Electron 渲染进程崩溃 | GPU 进程崩溃(exit_code=133)、V8 栈溢出 |
| KP-EXP-DSK-001 | Electron 上下文隔离配置 | contextIsolation 关闭导致原型链污染 RCE |
| KP-EXP-DSK-BUILD-001 | Electron Builder 构建错误 | NSIS 打包失败、DMG 创建超时、node-gyp 编译失败 |
| KP-EXP-DSK-SIGN-001 | 代码签名故障 | SmartScreen 警告、Gatekeeper 阻止、签名失败 |

### Tauri 错误

| 条目ID | 标题 | 简短描述 |
|--------|------|----------|
| KP-EXP-ERR-DESK-002 | Tauri 权限拒绝 | Capabilities 配置缺失、Scope 未覆盖、Allowlist 未开启 |

### Express/FastAPI 错误

| 条目ID | 标题 | 简短描述 |
|--------|------|----------|
| KP-EXP-PAT-ERR-001 | 错误处理中间件 | 500 无结构化错误、堆栈泄露、格式不一致 |

### 安全漏洞类

| 条目ID | 标题 | 简短描述 |
|--------|------|----------|
| KP-EXP-SEC-XSS-001 | XSS 跨站脚本攻击防护 | 用户输入未编码导致脚本注入 |
| KP-EXP-INT-001 | 第三方 OAuth 集成问题 | Implicit Grant 废弃、state 校验失败、CORS 问题 |
