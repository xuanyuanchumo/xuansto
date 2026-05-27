---
id: "KP-EXP-DSK-001"
type: "desktop-experience"
category: "electron-security"
tags: ["Electron", "contextIsolation", "安全", "preload", "contextBridge", "IPC", "桌面应用"]
version: "1.0.0"
created: "2026-04-28T10:00:00Z"
updated: "2026-04-28T10:00:00Z"
source: "auto_precipitation"
confidence: 0.92
last_validated: "2026-04-28T10:00:00Z"
success_count: 0
failure_count: 0
trigger: "pattern_validated"
references:
  - id: "KP-GEN-030"
    relation: "refines"
  - id: "KP-GEN-020"
    relation: "complies"
---

# Electron 上下文隔离经验

## 问题描述

在 Electron 应用开发中，早期版本默认关闭 `contextIsolation`，允许渲染进程直接访问 Node.js API。这导致严重的安全风险：加载的远程内容可以通过原型链污染获取 Node.js 访问权限，实现远程代码执行（RCE）。

### 典型问题场景

1. **渲染进程直接使用 Node.js API**：旧代码在渲染进程中直接调用 `require('fs')` 等
2. **Preload 脚本暴露过多能力**：通过 `window` 对象直接挂载 Node.js 模块
3. **contextBridge 使用不当**：暴露过于宽泛的 API，绕过隔离保护
4. **第三方依赖注入**：npm 包中的恶意代码利用不安全的上下文配置

---

## 解决方案

### 1. 启用上下文隔离并使用 contextBridge

```javascript
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("appAPI", {
  readFile: (path) => ipcRenderer.invoke("fs:readFile", path),
  writeFile: (path, content) =>
    ipcRenderer.invoke("fs:writeFile", path, content),
  selectFile: () => ipcRenderer.invoke("dialog:openFile"),
  onSettingsChanged: (callback) => {
    const handler = (event, data) => callback(data);
    ipcRenderer.on("settings:changed", handler);
    return () => ipcRenderer.removeListener("settings:changed", handler);
  },
});
```

### 2. 限制暴露的 API 粒度

#### 错误做法：暴露过于宽泛的 API

```javascript
contextBridge.exposeInMainWorld("nodeAPI", {
  require: (module) => require(module),
  exec: (cmd) => require("child_process").exec(cmd),
  fs: require("fs"),
});
```

#### 正确做法：暴露最小化的具体 API

```javascript
contextBridge.exposeInMainWorld("appAPI", {
  getConfig: () => ipcRenderer.invoke("app:getConfig"),
  saveConfig: (key, value) => ipcRenderer.invoke("app:saveConfig", key, value),
  getDocumentsPath: () => ipcRenderer.invoke("path:documents"),
});
```

### 3. 主进程实现安全 IPC 处理

```javascript
const { ipcMain, dialog, app } = require("electron");
const fs = require("fs/promises");
const path = require("path");

const ALLOWED_READ_DIRS = [
  app.getPath("documents"),
  app.getPath("desktop"),
  app.getPath("downloads"),
];

function isPathAllowed(filePath, allowedDirs) {
  const resolved = path.resolve(filePath);
  return allowedDirs.some((dir) => resolved.startsWith(dir));
}

ipcMain.handle("fs:readFile", async (event, filePath) => {
  if (!isPathAllowed(filePath, ALLOWED_READ_DIRS)) {
    throw new Error("路径不在允许的目录范围内");
  }
  const resolved = path.resolve(filePath);
  if (resolved.includes("..")) {
    throw new Error("不允许使用路径遍历");
  }
  return fs.readFile(resolved, "utf-8");
});

ipcMain.handle("dialog:openFile", async () => {
  const result = await dialog.showOpenDialog({
    properties: ["openFile"],
    filters: [
      { name: "文本文件", extensions: ["txt", "md", "json"] },
      { name: "所有文件", extensions: ["*"] },
    ],
  });
  if (result.canceled) return null;
  return result.filePaths[0];
});

ipcMain.handle("app:getConfig", async () => {
  const configPath = path.join(app.getPath("userData"), "config.json");
  try {
    const content = await fs.readFile(configPath, "utf-8");
    return JSON.parse(content);
  } catch {
    return {};
  }
});

ipcMain.handle("app:saveConfig", async (event, key, value) => {
  const configPath = path.join(app.getPath("userData"), "config.json");
  let config = {};
  try {
    const content = await fs.readFile(configPath, "utf-8");
    config = JSON.parse(content);
  } catch {
    // 配置文件不存在，使用默认值
  }
  config[key] = value;
  await fs.writeFile(configPath, JSON.stringify(config, null, 2), "utf-8");
  return true;
});
```

### 4. 渲染进程类型安全调用

```typescript
interface AppAPI {
  readFile(path: string): Promise<string>;
  writeFile(path: string, content: string): Promise<void>;
  selectFile(): Promise<string | null>;
  getConfig(): Promise<Record<string, unknown>>;
  saveConfig(key: string, value: unknown): Promise<boolean>;
  onSettingsChanged(callback: (data: unknown) => void): () => void;
}

declare global {
  interface Window {
    appAPI: AppAPI;
  }
}

async function loadUserConfig() {
  const config = await window.appAPI.getConfig();
  return config;
}

async function openAndReadFile() {
  const filePath = await window.appAPI.selectFile();
  if (!filePath) return null;
  return window.appAPI.readFile(filePath);
}
```

### 5. 安全配置检查工具

```javascript
function validateBrowserWindowConfig(webPreferences) {
  const issues = [];

  if (webPreferences.nodeIntegration === true) {
    issues.push("CRITICAL: nodeIntegration 不应为 true");
  }

  if (webPreferences.contextIsolation === false) {
    issues.push("CRITICAL: contextIsolation 不应为 false");
  }

  if (webPreferences.sandbox === false) {
    issues.push("WARNING: sandbox 建议设为 true");
  }

  if (webPreferences.enableRemoteModule === true) {
    issues.push("CRITICAL: enableRemoteModule 不应为 true");
  }

  if (webPreferences.webSecurity === false) {
    issues.push("CRITICAL: webSecurity 不应为 false");
  }

  return issues;
}
```

---

## 经验教训

### 1. 迁移策略

从 `nodeIntegration: true` 迁移到 `contextIsolation: true` 的步骤：

| 步骤 | 说明 |
|------|------|
| 审计渲染进程代码 | 识别所有 `require()` 和 Node.js API 调用 |
| 设计 IPC 接口 | 将 Node.js 调用封装为 IPC 通道 |
| 实现 Preload 脚本 | 使用 `contextBridge` 暴露最小化 API |
| 实现主进程处理 | 为每个 IPC 通道添加安全处理逻辑 |
| 逐步替换 | 将渲染进程中的直接调用替换为 `window.appAPI` 调用 |
| 测试验证 | 确保所有功能正常，无安全配置回退 |

### 2. 常见陷阱

| 陷阱 | 说明 | 解决方案 |
|------|------|---------|
| 暴露 `ipcRenderer` | 直接暴露 `ipcRenderer` 等于绕过隔离 | 仅暴露具体的 IPC 方法 |
| 原型链污染 | 攻击者通过修改原型链访问预加载脚本 | `contextIsolation: true` 防止此攻击 |
| `disableBlinkFeatures` | 禁用安全特性以兼容旧代码 | 不应禁用，应修复代码 |
| 远程内容加载 | 加载不可信内容时未启用沙箱 | 远程内容必须启用 `sandbox: true` |
| 深拷贝限制 | `contextBridge` 无法传递函数和特殊对象 | 仅传递可序列化数据，函数通过 IPC 转发 |

### 3. 安全检查清单

| 检查项 | 必须值 | 说明 |
|--------|--------|------|
| `contextIsolation` | `true` | 隔离预加载脚本与渲染进程 |
| `nodeIntegration` | `false` | 禁止渲染进程访问 Node.js |
| `sandbox` | `true` | 操作系统级沙箱 |
| `worldSafeExecuteJavaScript` | `true` | 安全执行 JavaScript |
| `enableRemoteModule` | `false` | 禁用 remote 模块 |
| Preload 脚本 | 使用 `contextBridge` | 不直接修改 `window` 对象 |
| IPC 通道 | 白名单验证 | 主进程验证所有 IPC 请求参数 |

## 相关知识

- [KP-GEN-030] Electron 最佳实践 — 上下文隔离的通用最佳实践
- [KP-GEN-020] 安全编码基础 — 输入验证与输出编码
- [KP-GEN-021] OWASP Top 10 概述 — 安全配置错误防护
