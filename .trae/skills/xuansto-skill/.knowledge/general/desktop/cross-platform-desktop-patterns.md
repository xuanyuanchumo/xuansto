---
id: cross-platform-desktop-patterns
type: knowledge
category: desktop
tags: [跨平台, Electron, Tauri, Flutter Desktop, 共享代码, 平台差异]
version: 1.0.0
confidence: high
---

## 跨平台桌面开发模式 (版本: 1.0 | 适用: Electron/Tauri/Flutter)

### 核心规则
- 分层架构：Platform UI → Shared UI → Business Logic → Platform Adapter
- 核心业务逻辑 90%+ 共享，UI 组件 60-80% 共享，平台适配层 10-20% 独立
- 文件路径使用 `path.join()` / `app.getPath()` 处理分隔符差异
- 快捷键运行时检测平台：macOS 用 Cmd，Windows/Linux 用 Ctrl
- 自动启动：Windows 注册表 / macOS LaunchAgent / Linux desktop entry

### 代码示例

```typescript
import { app } from 'electron';
import path from 'path';

function getDataDir(): string {
  if (process.platform === 'win32') return path.join(process.env.APPDATA!, 'MyApp');
  if (process.platform === 'darwin') return path.join(app.getPath('home'), 'Library', 'Application Support', 'MyApp');
  return path.join(app.getPath('home'), '.myapp');
}
```

### 反模式
- ❌ 硬编码路径分隔符 `'assets\\images\\logo.png'` — macOS 无法解析
- ❌ 文件名大小写不敏感假设 — Linux 部署后模块找不到
- ❌ 直接依赖 `process.platform` 散布在业务代码中 — 应封装平台抽象层
