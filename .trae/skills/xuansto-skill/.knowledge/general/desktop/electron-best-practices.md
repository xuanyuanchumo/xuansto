---
id: "KP-GEN-030"
type: "desktop"
category: "electron"
tags: ["Electron", "桌面应用", "contextIsolation", "nodeIntegration", "sandbox", "IPC", "性能优化", "安全"]
version: "1.0.0"
confidence: 0.88
---

## Electron 最佳实践 (版本: 1.0 | 适用: Electron 12+)

### 核心规则
- 启用 `contextIsolation: true`，隔离预加载脚本与渲染进程上下文
- 禁用 `nodeIntegration: false`，禁止渲染进程直接访问 Node.js
- 启用 `sandbox: true`，使用 OS 级沙箱限制渲染进程权限
- 配置 CSP 安全头，限制资源加载来源
- 使用 `contextBridge.exposeInMainWorld` 暴露最小 API，禁止直接暴露 `ipcRenderer`
- 异步 IPC 通信（`invoke/handle`），避免同步 IPC 阻塞渲染
- 延迟显示窗口（`show: false` + `ready-to-show`），优化启动体验

### 代码示例

```javascript
const mainWindow = new BrowserWindow({
  show: false,
  webPreferences: {
    contextIsolation: true,
    nodeIntegration: false,
    sandbox: true,
    preload: path.join(__dirname, "preload.js"),
  },
});
mainWindow.once("ready-to-show", () => mainWindow.show());
```

Preload 脚本：
```javascript
const { contextBridge, ipcRenderer } = require("electron");
contextBridge.exposeInMainWorld("electronAPI", {
  readFile: (path) => ipcRenderer.invoke("fs:readFile", path),
  onFileChanged: (cb) => {
    const handler = (_, data) => cb(data);
    ipcRenderer.on("file:changed", handler);
    return () => ipcRenderer.removeListener("file:changed", handler);
  },
});
```

### 反模式
- ❌ `nodeIntegration: true` — 远程内容可直接访问系统资源，导致 RCE
- ❌ 直接暴露 `ipcRenderer` — 等于绕过上下文隔离
- ❌ 同步 IPC `ipcRenderer.sendSync` — 阻塞渲染进程
- ❌ 未配置 CSP — 允许加载任意外部脚本
