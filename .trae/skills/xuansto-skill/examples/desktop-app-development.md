# 桌面应用开发示例：跨平台笔记应用

## 场景描述

开发一款基于Electron的跨平台笔记应用，支持Markdown编辑、笔记分类管理、全文搜索、云同步和离线使用。应用需要发布到Windows、macOS和Linux三大平台，包含代码签名、自动更新和原生安装包。技术栈：Electron + React + TypeScript（渲染进程）、SQLite（本地存储）、Electron Builder（打包）。

---

## Phase 0：需求分析与项目启动

### Agent分配

| Agent | 职责 |
|-------|------|
| Product Manager | 需求收集、用户故事编写、优先级排序 |
| System Architect | 技术可行性评估、桌面架构初步规划 |
| Desktop Developer | 桌面技术选型评估、可行性验证 |
| Specification Keeper | 规格文档管理、需求追踪 |

### 工作流程

1. **Product Manager** 收集笔记应用需求，编写用户故事：
   - US-001：用户创建/编辑/删除Markdown笔记
   - US-002：用户通过文件夹和标签分类管理笔记
   - US-003：用户全文搜索笔记内容
   - US-004：用户离线使用应用，联网后自动同步
   - US-005：用户自定义编辑器主题和快捷键
   - US-006：应用自动检查并安装更新

2. **System Architect** 评估桌面架构方案：
   - 主进程与渲染进程职责划分
   - IPC通信架构设计
   - 本地存储方案选型（SQLite vs IndexedDB）
   - 自动更新方案选型（electron-updater）

3. **Desktop Developer** 验证技术可行性：
   - Electron版本选型与兼容性验证
   - 原生模块需求评估
   - 跨平台UI一致性方案验证
   - 性能基准测试（启动时间、内存占用）

4. **Specification Keeper** 创建规格文档，建立需求追踪矩阵

### 关键输出

- 产品需求文档（PRD）
- 用户故事列表（含验收标准）
- 桌面架构可行性报告
- 技术选型评估报告
- 需求追踪矩阵

### 质量门禁

- ✅ **REQ-COMPLETE**：所有用户故事具备验收标准
- ✅ **FEASIBILITY**：桌面技术方案通过可行性评估
- ✅ **DESKTOP-FEASIBILITY**：Electron跨平台方案验证通过

---

## Phase 1：架构设计与规格定义

### Agent分配

| Agent | 职责 |
|-------|------|
| System Architect | 系统架构设计、模块划分 |
| Desktop Developer | Electron架构设计、IPC通道规划 |
| Desktop UI Adapter | 桌面UI适配架构设计 |
| Data Modeler | 数据模型设计 |
| Security Auditor | 安全架构评审（含Electron安全） |
| Specification Keeper | SDD文档编写与维护 |

### 工作流程

1. **System Architect** 设计笔记应用整体架构：
   - 主进程：窗口管理、IPC桥接、文件系统访问、自动更新
   - 渲染进程：React UI层、状态管理、Markdown编辑器
   - Preload脚本：安全上下文桥接
   - 本地服务：SQLite数据库、全文搜索索引

2. **Desktop Developer** 设计Electron架构与IPC通道：
   - IPC通道定义：
     - `notes:create` / `notes:read` / `notes:update` / `notes:delete`
     - `folders:manage` / `tags:manage`
     - `search:fulltext`
     - `sync:status` / `sync:push` / `sync:pull`
     - `app:update-check` / `app:install-update`
     - `fs:read-file` / `fs:write-file` / `fs:export`
   - 上下文隔离策略
   - 原生模块集成方案

3. **Desktop UI Adapter** 设计桌面UI适配架构：
   - 原生窗口行为（最小化、最大化、关闭）
   - 原生菜单栏设计（应用菜单、编辑菜单、视图菜单）
   - 系统托盘集成
   - 平台特定UI适配（macOS Dock、Windows任务栏）
   - 快捷键系统设计

4. **Data Modeler** 设计数据模型：
   - notes表（id, title, content, folder_id, created_at, updated_at...）
   - folders表（id, name, parent_id, sort_order...）
   - tags表（id, name, color...）
   - note_tags表（note_id, tag_id）
   - sync_status表（id, entity_type, entity_id, sync_state, last_synced...）

5. **Security Auditor** 审查Electron安全架构：
   - contextIsolation: true
   - nodeIntegration: false
   - sandbox: true
   - preload脚本最小权限原则
   - 远程内容加载限制
   - 自动更新签名验证

6. **Specification Keeper** 编写SDD规格文档

### 关键输出

- 系统架构设计文档
- IPC通道契约文档
- 桌面UI适配方案
- 数据模型ER图
- Electron安全架构报告
- SDD规格文档

### 质量门禁

- ✅ **ARCH-REVIEW**：架构设计通过评审
- ✅ **IPC-CONTRACT**：IPC通道契约定义完整且类型安全
- ✅ **SEC-ARCH**：安全架构通过审计（含Electron专项）
- ✅ **DESKTOP-ARCH**：桌面架构方案通过评审

---

## Phase 2：测试先行（TDD）

### Agent分配

| Agent | 职责 |
|-------|------|
| Test Architect | 测试策略制定、测试架构设计 |
| Unit Tester | 单元测试编写 |
| Integration Tester | 集成测试编写 |
| Desktop Tester | 桌面专项测试编写 |
| Security Tester | 安全测试用例编写 |
| Specification Keeper | 测试规格同步 |

### 工作流程

1. **Test Architect** 制定测试策略：
   - 单元测试覆盖率目标：≥ 80%
   - 集成测试覆盖率目标：≥ 70%
   - 高风险模块（IPC通信、数据同步、文件操作）覆盖率：≥ 90%
   - 桌面专项测试：窗口管理、原生菜单、自动更新、安装包

2. **Unit Tester** 编写单元测试：
   - `note.service.test.ts`：笔记CRUD逻辑
   - `folder.service.test.ts`：文件夹管理逻辑
   - `search.service.test.ts`：全文搜索逻辑
   - `sync.service.test.ts`：同步状态管理逻辑
   - `markdown.renderer.test.ts`：Markdown渲染逻辑
   - `ipc.handler.test.ts`：IPC消息处理逻辑

3. **Integration Tester** 编写集成测试：
   - `ipc.integration.test.ts`：主进程↔渲染进程IPC通信
   - `database.integration.test.ts`：SQLite数据库操作
   - `sync.integration.test.ts`：同步流程端到端
   - `file-operation.integration.test.ts`：文件导入/导出

4. **Desktop Tester** 编写桌面专项测试：
   - 窗口生命周期测试（创建、最小化、恢复、关闭）
   - 原生菜单交互测试
   - 系统托盘功能测试
   - 自动更新流程测试
   - 跨平台快捷键测试

5. **Security Tester** 编写安全测试：
   - contextIsolation验证测试
   - preload脚本权限边界测试
   - IPC消息注入测试
   - 远程代码执行防护测试
   - 自动更新签名验证测试

### 关键输出

- 测试策略文档（含桌面专项）
- 单元测试套件（全部RED状态）
- 集成测试套件（全部RED状态）
- 桌面专项测试套件
- 安全测试套件
- IPC契约验证脚本

### 质量门禁

- ✅ **TEST-FIRST**：所有核心功能具备先行的测试用例
- ✅ **TEST-COV-TARGET**：测试覆盖率目标已设定
- ✅ **IPC-TEST**：IPC通道测试覆盖完整
- ✅ **DESKTOP-TEST-PLAN**：桌面专项测试计划完整

---

## Phase 3：核心实现

### Agent分配

| Agent | 职责 |
|-------|------|
| Desktop Developer | Electron主进程实现、IPC处理 |
| Frontend Developer | 渲染进程UI实现 |
| Desktop UI Adapter | 桌面原生功能适配 |
| Database Engineer | SQLite数据库实现 |
| Code Reviewer | 代码审查 |

### 工作流程

1. **Desktop Developer** 实现Electron主进程：
   - 应用入口与窗口管理
   - IPC Handler注册与实现：
     - 笔记CRUD IPC处理
     - 文件夹/标签管理IPC处理
     - 搜索IPC处理
     - 同步状态IPC处理
     - 文件操作IPC处理
   - Preload脚本（contextBridge API暴露）
   - 自动更新模块集成
   - 系统托盘模块

2. **Frontend Developer** 实现渲染进程UI：
   - NoteEditor组件（Markdown编辑器集成）
   - NoteList组件（笔记列表与搜索）
   - FolderTree组件（文件夹树形结构）
   - TagManager组件（标签管理）
   - SearchBar组件（全文搜索）
   - SyncStatus组件（同步状态指示器）
   - SettingsPanel组件（设置面板）
   - App状态管理（Zustand store）

3. **Desktop UI Adapter** 实现桌面原生适配：
   - 原生菜单栏构建（Mac/Windows/Linux适配）
   - 窗口行为适配（关闭到托盘、记住窗口位置/大小）
   - 快捷键注册与处理
   - 拖放文件导入支持
   - 原生通知集成
   - 平台特定样式适配

4. **Database Engineer** 实现SQLite数据层：
   - 数据库初始化与迁移
   - 笔记CRUD Repository
   - 文件夹/标签Repository
   - 全文搜索索引（FTS5）
   - 同步状态追踪
   - 数据库备份与恢复

5. **Code Reviewer** 进行代码审查，确保桌面开发规范

### 关键输出

- Electron主进程实现代码
- 渲染进程UI实现代码
- Preload脚本
- 桌面原生适配代码
- SQLite数据层实现
- 代码审查报告
- 单元测试转为GREEN状态

### 质量门禁

- ✅ **UNIT-PASS**：所有单元测试通过
- ✅ **CODE-REVIEW**：代码通过审查
- ✅ **SEC-CODE**：代码通过安全扫描
- ✅ **IPC-IMPLEMENT**：IPC通道实现与契约一致
- ✅ **COVERAGE**：测试覆盖率达标

---

## Phase 4：集成与端到端测试

### Agent分配

| Agent | 职责 |
|-------|------|
| Integration Tester | 集成测试执行与修复 |
| E2E Tester | 端到端测试编写与执行 |
| Desktop Tester | 桌面专项测试执行 |
| Performance Tester | 性能测试 |
| Security Tester | 渗透测试 |

### 工作流程

1. **Integration Tester** 执行集成测试：
   - 主进程↔渲染进程IPC通信完整性
   - 数据库操作与UI状态同步
   - 文件导入/导出流程
   - 同步状态流转

2. **E2E Tester** 编写并执行端到端测试（Spectron/Playwright）：
   - 创建笔记→编辑→保存→重新打开验证
   - 文件夹创建→移动笔记→删除文件夹
   - 全文搜索→结果点击→笔记打开
   - 设置修改→主题切换→快捷键自定义
   - 窗口关闭→托盘恢复→完全退出

3. **Desktop Tester** 执行桌面专项测试：
   - 窗口生命周期完整测试
   - 原生菜单功能测试
   - 系统托盘交互测试
   - 自动更新模拟测试（本地更新服务器）
   - 安装/卸载流程测试
   - 跨平台UI一致性测试

4. **Performance Tester** 执行性能测试：
   - 应用冷启动时间 < 3s
   - 笔记列表渲染（1000条）< 500ms
   - 全文搜索响应时间 < 200ms
   - 内存占用 < 200MB（空闲状态）
   - IPC消息延迟 < 10ms

5. **Security Tester** 执行渗透测试：
   - Electron安全最佳实践验证
   - IPC消息篡改测试
   - preload脚本越权测试
   - 本地数据库安全测试
   - 自动更新中间人攻击测试

### 关键输出

- 集成测试报告（全部GREEN）
- E2E测试报告
- 桌面专项测试报告
- 性能测试报告
- 渗透测试报告
- 缺陷列表与修复记录

### 质量门禁

- ✅ **INTEGRATION-PASS**：所有集成测试通过
- ✅ **E2E-PASS**：所有端到端测试通过
- ✅ **DESKTOP-CROSS**：跨平台功能测试通过
- ✅ **PERF-BENCHMARK**：性能指标达标
- ✅ **SEC-PENTEST**：渗透测试通过

---

## Phase 5：代码审查与重构

### Agent分配

| Agent | 职责 |
|-------|------|
| Code Reviewer | 全面代码审查 |
| Refactoring Specialist | 代码重构优化 |
| Security Auditor | 安全代码审计（Electron专项） |
| Doc Reviewer | 文档审查 |

### 工作流程

1. **Code Reviewer** 执行全面代码审查：
   - IPC通道实现规范性
   - 主进程/渲染进程职责边界
   - 内存泄漏风险检查（事件监听器清理）
   - 原生模块使用规范性

2. **Refactoring Specialist** 执行重构：
   - IPC通信层抽象与统一
   - 数据库查询优化
   - 窗口管理逻辑简化
   - 编辑器性能优化（大文件处理）

3. **Security Auditor** 执行Electron专项安全审计：
   - contextIsolation有效性验证
   - nodeIntegration禁用确认
   - preload脚本最小权限确认
   - 远程模块禁用确认
   - webSecurity启用确认
   - 自动更新HTTPS与签名验证确认

4. **Doc Reviewer** 审查文档完整性：
   - IPC通道文档与实现一致性
   - 桌面构建文档完整性
   - 安全配置文档完整性

### 关键输出

- 代码审查报告
- 重构变更记录
- Electron安全审计报告
- 文档审查报告

### 质量门禁

- ✅ **REFACTOR-CLEAN**：重构后所有测试仍通过
- ✅ **SEC-AUDIT**：安全审计通过（含Electron专项）
- ✅ **IPC-CONTRACT**：IPC实现与契约一致
- ✅ **DOC-COMPLETE**：文档完整且与实现一致

---

## Phase 6：桌面构建与打包

### Agent分配

| Agent | 职责 |
|-------|------|
| Build & Release Engineer | 构建配置、打包、代码签名 |
| Desktop Developer | 构建问题修复、原生模块适配 |
| DevOps Engineer | CI/CD流水线配置 |

### 工作流程

1. **Build & Release Engineer** 配置构建与打包：
   - Electron Builder配置：
     - Windows：NSIS安装包 + MSI安装包
     - macOS：DMG安装包（含通用二进制）
     - Linux：DEB包 + AppImage
   - 代码签名配置：
     - Windows：Authenticode证书签名
     - macOS：Developer ID证书签名 + 公证（Notarization）
   - 自动更新配置：
     - 更新服务器地址配置
     - 更新通道（stable/beta）配置
     - 增量更新支持

2. **Desktop Developer** 处理构建问题：
   - 原生模块rebuild（better-sqlite3等）
   - 平台特定代码路径处理
   - 资源文件打包优化
   - 构建错误修复

3. **DevOps Engineer** 配置CI/CD流水线：
   - 多平台并行构建（Windows/macOS/Linux）
   - 代码签名集成
   - 自动更新清单生成
   - 构建产物上传与分发

### 关键输出

- Electron Builder配置文件
- 代码签名配置
- 自动更新配置文件
- 多平台安装包
- CI/CD流水线配置

### 质量门禁

- ✅ **DESKTOP-BUILD**：三平台构建成功
- ✅ **DESKTOP-SIGN**：代码签名验证通过
- ✅ **DESKTOP-UPDATE**：自动更新配置验证通过
- ✅ **DESKTOP-CROSS**：跨平台安装包功能正常

---

## Phase 7：部署与交付

### Agent分配

| Agent | 职责 |
|-------|------|
| Build & Release Engineer | 发布管理、版本分发 |
| DevOps Engineer | 发布流水线执行 |
| Runtime Supervisor | 运行时监控配置 |
| Technical Writer | 用户文档编写 |

### 工作流程

1. **Build & Release Engineer** 执行发布：
   - 版本号确认与标签创建
   - 正式构建执行（Release模式）
   - 代码签名与公证
   - 安装包上传到分发平台
   - 更新清单发布

2. **DevOps Engineer** 执行发布流水线：
   - 触发正式构建流水线
   - 多平台并行构建与签名
   - 构建产物校验
   - 分发渠道发布

3. **Runtime Supervisor** 配置运行时监控：
   - 应用崩溃监控（Sentry/Electron-crash-reporter）
   - 自动更新成功率监控
   - 性能指标收集
   - 用户反馈收集

4. **Technical Writer** 编写用户文档：
   - 安装指南（三平台）
   - 使用手册
   - 常见问题（FAQ）
   - 更新日志

### 关键输出

- 正式版安装包（Windows/macOS/Linux）
- 更新清单文件
- 发布说明
- 监控仪表盘
- 用户文档

### 质量门禁

- ✅ **DEPLOY-RELEASE**：正式版本发布成功
- ✅ **DESKTOP-SIGN**：正式版签名验证通过
- ✅ **DESKTOP-UPDATE**：自动更新端到端验证通过
- ✅ **MONITOR-READY**：运行时监控就绪
- ✅ **DOC-PUBLISH**：用户文档发布完成

---

## Phase 8：验收与知识沉淀

### Agent分配

| Agent | 职责 |
|-------|------|
| Product Manager | 验收确认 |
| QA Engineer | 最终验收测试 |
| Desktop Tester | 桌面专项验收 |
| Specification Keeper | 规格文档归档 |
| Documentation Engineer | 知识库更新 |

### 工作流程

1. **Product Manager** 执行验收：
   - 逐项验证用户故事完成情况
   - 三平台功能一致性确认
   - 签署验收确认

2. **QA Engineer** 执行最终验收测试：
   - 回归测试全量执行
   - 关键路径冒烟测试（三平台）
   - 安装/卸载/升级流程验证

3. **Desktop Tester** 执行桌面专项验收：
   - 三平台安装包安装测试
   - 代码签名验证（Windows SmartScreen、macOS Gatekeeper）
   - 自动更新流程端到端验证
   - 跨平台功能一致性最终确认

4. **Specification Keeper** 归档规格文档：
   - SDD文档最终版本归档
   - IPC通道契约文档归档
   - 需求追踪矩阵最终状态
   - 变更记录归档

5. **Documentation Engineer** 更新知识库：
   - Electron架构经验入库
   - 跨平台构建经验提取
   - 代码签名与公证流程入库
   - 自动更新方案经验入库
   - 桌面性能优化经验入库
   - 常见构建错误与解决方案入库

### 关键输出

- 验收确认报告
- 最终测试报告（含桌面专项）
- 归档规格文档
- 知识库更新记录

### 质量门禁

- ✅ **ACCEPTANCE**：产品验收通过
- ✅ **REGRESSION-PASS**：回归测试通过
- ✅ **DESKTOP-CROSS**：跨平台最终验收通过
- ✅ **KB-UPDATED**：知识库已更新（含桌面开发经验）
- ✅ **DOC-ARCHIVED**：文档已归档

---

## 总结

本示例展示了使用xuansto-skill进行桌面应用开发的完整流程：

- **9个阶段**：从需求分析到验收交付，包含桌面特有的构建打包阶段
- **桌面专项Agent**：Desktop Developer、Desktop UI Adapter、Desktop Tester、Build & Release Engineer协同工作
- **桌面特有关注点**：
  - **IPC通道契约**：主进程与渲染进程通信的类型安全保证
  - **代码签名**：Windows Authenticode + macOS Developer ID + 公证
  - **自动更新**：electron-updater集成与端到端验证
  - **跨平台一致性**：三平台功能、UI、行为一致性保障
  - **Electron安全**：contextIsolation、sandbox、最小权限preload
- **桌面质量门禁**：DESKTOP-BUILD、DESKTOP-SIGN、DESKTOP-UPDATE、DESKTOP-CROSS、IPC-CONTRACT五大专项门禁
- **知识沉淀**：桌面开发经验自动提取并沉淀到知识库，为后续项目提供参考

通过xuansto-skill的多Agent编排能力，跨平台桌面应用的开发过程实现了从架构设计到三平台构建发布的全流程自动化管理。
