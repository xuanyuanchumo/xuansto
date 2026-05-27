---
id: "KP-GEN-030"
type: "desktop"
category: "electron"
tags: ["Electron", "桌面应用", "contextIsolation", "nodeIntegration", "sandbox", "IPC", "性能优化", "安全"]
version: "1.0.0"
created: "2026-04-28T10:00:00Z"
updated: "2026-04-28T10:00:00Z"
source: "Electron 官方文档 / 社区最佳实践总结"
confidence: 0.88
last_validated: "2026-04-28T10:00:00Z"
success_count: 0
failure_count: 0
references:
  - id: "KP-GEN-020"
    relation: "complies"
  - id: "KP-GEN-021"
    relation: "complies"
  - id: "KP-EXP-DSK-001"
    relation: "extends"
---

# Electron 最佳实践

## 概述

Electron 是基于 Chromium 和 Node.js 的跨平台桌面应用框架。其双进程架构（主进程 + 渲染进程）带来独特的安全和性能考量。本文涵盖安全配置、性能优化和 IPC 通信三大核心领域。

---

## 安全最佳实践

### 1. 启用上下文隔离 (contextIsolation)

上下文隔离是 Electron 最重要的安全特性，确保预加载脚本与渲染进程的 JavaScript 运行在不同上下文中。

```javascript
const mainWindow = new BrowserWindow({
  webPreferences: {
    contextIsolation: true,
    nodeIntegration: false,
    sandbox: true,
    preload: path.join(__dirname, "preload.js"),
  },
});
```

### 2. 禁用 Node.js 集成 (nodeIntegration)

渲染进程中绝不应启用 Node.js 集成，否则加载的远程内容可直接访问系统资源。

```javascript
const mainWindow = new BrowserWindow({
  webPreferences: {
    nodeIntegration: false,
    nodeIntegrationInWorker: false,
    nodeIntegrationInSubFrames: false,
    enableRemoteModule: false,
  },
});
```

### 3. 启用沙箱模式 (sandbox)

沙箱模式使用操作系统级别的沙箱限制渲染进程权限，即使存在代码执行漏洞也无法访问系统资源。

```javascript
const mainWindow = new BrowserWindow({
  webPreferences: {
    sandbox: true,
  },
});
```

### 4. 安全头配置

```javascript
session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
  callback({
    responseHeaders: {
      ...details.responseHeaders,
      "Content-Security-Policy": [
        "default-src 'self'; " +
          "script-src 'self'; " +
          "style-src 'self' 'unsafe-inline'; " +
          "img-src 'self' data:; " +
          "connect-src 'self' https://api.example.com",
      ],
    },
  });
});
```

### 5. 防止导航劫持

```javascript
mainWindow.webContents.on("will-navigate", (event, url) => {
  const allowedOrigins = ["file://", "https://app.example.com"];
  const isAllowed = allowedOrigins.some((origin) => url.startsWith(origin));
  if (!isAllowed) {
    event.preventDefault();
  }
});

mainWindow.webContents.setWindowOpenHandler(() => {
  return { action: "deny" };
});
```

---

## 性能优化

### 1. 进程模型优化

| 策略 | 说明 |
|------|------|
| 延迟加载窗口 | 不立即显示窗口，等 `did-finish-load` 后再显示 |
| 后台窗口休眠 | 不可见时降低渲染频率 |
| 合理使用 UtilityProcess | CPU 密集任务移至 Utility 进程 |
| 避免同步 IPC | 使用异步通信避免阻塞渲染 |

### 2. 窗口创建优化

```javascript
const mainWindow = new BrowserWindow({
  show: false,
  backgroundColor: "#ffffff",
  webPreferences: {
    sandbox: true,
    contextIsolation: true,
    nodeIntegration: false,
    preload: path.join(__dirname, "preload.js"),
  },
});

mainWindow.once("ready-to-show", () => {
  mainWindow.show();
});

mainWindow.loadFile("index.html");
```

### 3. 后台资源管理

```javascript
mainWindow.on("show", () => {
  mainWindow.webContents.invalidate();
});

mainWindow.on("hide", () => {
  mainWindow.webContents.setBackgroundThrottling(true);
});
```

### 4. 启动性能

```javascript
const app = require("electron");

app.whenReady().then(async () => {
  await setupProtocolHandlers();

  const mainWindow = createMainWindow();

  mainWindow.loadFile("index.html");

  setupIpcHandlers();

  if (process.platform === "darwin") {
    app.dock.show();
  }
});
```

---

## IPC 通信模式

### 1. 安全的 IPC 通信架构

```
┌─────────────────┐    ipcRenderer.invoke    ┌─────────────────┐
│   渲染进程       │ ──────────────────────► │   主进程         │
│ (Renderer)      │                          │ (Main)          │
│                 │ ◄────────────────────── │                 │
│ preload.js      │    ipcMain.handle        │ Node.js APIs    │
│ contextBridge   │                          │ System Access   │
└─────────────────┘                          └─────────────────┘
```

### 2. Preload 脚本（contextBridge 模式）

```javascript
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  selectDirectory: () => ipcRenderer.invoke("dialog:selectDirectory"),
  readFile: (filePath) => ipcRenderer.invoke("fs:readFile", filePath),
  writeFile: (filePath, content) =>
    ipcRenderer.invoke("fs:writeFile", filePath, content),
  onFileChanged: (callback) => {
    const subscription = (event, data) => callback(data);
    ipcRenderer.on("file:changed", subscription);
    return () => ipcRenderer.removeListener("file:changed", subscription);
  },
});
```

### 3. 主进程 IPC 处理

```javascript
const { ipcMain, dialog } = require("electron");
const fs = require("fs/promises");

ipcMain.handle("dialog:selectDirectory", async () => {
  const result = await dialog.showOpenDialog({
    properties: ["openDirectory"],
  });
  if (result.canceled) return null;
  return result.filePaths[0];
});

ipcMain.handle("fs:readFile", async (event, filePath) => {
  const allowedDir = getAllowedDirectory();
  if (!filePath.startsWith(allowedDir)) {
    throw new Error("路径不在允许的目录范围内");
  }
  return fs.readFile(filePath, "utf-8");
});

ipcMain.handle("fs:writeFile", async (event, filePath, content) => {
  const allowedDir = getAllowedDirectory();
  if (!filePath.startsWith(allowedDir)) {
    throw new Error("路径不在允许的目录范围内");
  }
  await fs.writeFile(filePath, content, "utf-8");
  return true;
});
```

### 4. 渲染进程调用

```typescript
declare global {
  interface Window {
    electronAPI: {
      selectDirectory: () => Promise<string | null>;
      readFile: (filePath: string) => Promise<string>;
      writeFile: (filePath: string, content: string) => Promise<boolean>;
      onFileChanged: (callback: (data: unknown) => void) => () => void;
    };
  }
}

async function handleOpenProject() {
  const dir = await window.electronAPI.selectDirectory();
  if (dir) {
    const content = await window.electronAPI.readFile(
      `${dir}/config.json`,
    );
    console.log("项目配置:", content);
  }
}
```

---

## 安全配置检查清单

| 检查项 | 推荐值 | 说明 |
|--------|--------|------|
| `contextIsolation` | `true` | 隔离预加载脚本与渲染进程上下文 |
| `nodeIntegration` | `false` | 禁止渲染进程直接访问 Node.js |
| `sandbox` | `true` | 操作系统级沙箱保护 |
| `enableRemoteModule` | `false` | 禁用已废弃的 remote 模块 |
| `webSecurity` | `true` | 启用同源策略 |
| `allowRunningInsecureContent` | `false` | 禁止加载混合内容 |
| CSP | 已配置 | 限制资源加载来源 |
| 导航控制 | 已限制 | 防止导航到非预期 URL |

## 相关知识

- [KP-GEN-020] 安全编码基础 — 通用安全编码实践
- [KP-GEN-021] OWASP Top 10 概述 — Web 安全风险参考
- [KP-EXP-DSK-001] Electron 上下文隔离经验 — 上下文隔离实践案例
