---
id: cross-platform-desktop-patterns
type: knowledge
category: desktop
tags: [跨平台, Electron, Tauri, Flutter Desktop, 共享代码, 平台差异]
version: 1.0.0
created: 2026-04-28
updated: 2026-04-28
confidence: high
---

# 跨平台桌面开发模式

## 框架架构对比

| 维度 | Electron | Tauri | Flutter Desktop |
|------|----------|-------|-----------------|
| 渲染引擎 | Chromium | 系统 WebView | Skia 自绘引擎 |
| 后端语言 | Node.js | Rust | Dart |
| 打包体积 | ~150MB+ | ~5-10MB | ~30-50MB |
| 内存占用 | 较高 | 较低 | 中等 |
| 原生能力 | 通过 Node/IPC | 通过 Rust 命令 | 通过 FFI/Plugin |
| 热更新 | 支持 | 有限支持 | 支持 |
| 生态成熟度 | 高 | 中等 | 中等 |

## 共享代码策略

### 分层架构

```
┌─────────────────────┐
│   Platform UI Layer │  平台特定 UI 代码
├─────────────────────┤
│   Shared UI Layer   │  共享 UI 组件/逻辑
├─────────────────────┤
│   Business Logic    │  纯逻辑层，无平台依赖
├─────────────────────┤
│   Platform Adapter  │  平台能力抽象接口
└─────────────────────┘
```

- Business Logic 层使用纯语言实现，不引入任何平台 API
- Platform Adapter 定义接口（Trait/Protocol），各平台提供实现
- UI 层可共享组件（Web 技术）或分别实现（原生 UI）

### 代码共享比例目标

- 核心业务逻辑：90%+ 共享
- UI 组件：60-80% 共享
- 平台适配层：10-20% 各平台独立

## 平台差异处理

- **文件路径**：使用 `app.getPath()` / `path.join()` 处理路径分隔符差异
- **快捷键**：macOS 使用 Cmd，Windows/Linux 使用 Ctrl，运行时检测平台
- **窗口管理**：macOS 原生菜单栏 vs Windows 菜单栏行为不同
- **通知系统**：各平台通知 API 和权限模型不同，需统一抽象
- **自动启动**：Windows 注册表 / macOS LaunchAgent / Linux desktop entry
- **深色模式**：监听系统主题变更事件，各框架 API 不同

## 选型建议

- Web 技术栈团队 + 复杂 UI → Electron
- 性能敏感 + 安全要求高 + Rust 团队 → Tauri
- 已有 Flutter 移动端 → Flutter Desktop 扩展
