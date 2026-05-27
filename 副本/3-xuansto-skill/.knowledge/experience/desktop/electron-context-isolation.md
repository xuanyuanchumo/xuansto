---
id: "KP-EXP-DSK-001"
type: "desktop-experience"
category: "electron-security"
tags: ["Electron", "contextIsolation", "安全", "preload", "contextBridge", "IPC", "桌面应用"]
version: "1.0.0"
confidence: 0.92
---

## Electron 上下文隔离配置 (置信度: 0.92 | 技术栈: Electron)

### 现象
渲染进程直接使用 Node.js API，存在原型链污染 RCE 风险；preload 暴露过多能力绕过隔离。

### 根因
早期 Electron 默认关闭 contextIsolation，旧代码在渲染进程直接调用 require('fs')，或 contextBridge 暴露过于宽泛的 API。

### 解决方案

```javascript
const { contextBridge, ipcRenderer } = require("electron");
contextBridge.exposeInMainWorld("appAPI", {
  getConfig: () => ipcRenderer.invoke("app:getConfig"),
  saveConfig: (key, value) => ipcRenderer.invoke("app:saveConfig", key, value),
});
```

```javascript
ipcMain.handle("fs:readFile", async (event, filePath) => {
  if (!isPathAllowed(filePath, ALLOWED_READ_DIRS)) throw new Error("路径不允许");
  if (path.resolve(filePath).includes("..")) throw new Error("路径遍历");
  return fs.readFile(path.resolve(filePath), "utf-8");
});
```

### 验证
检查 BrowserWindow 配置：contextIsolation=true, nodeIntegration=false, sandbox=true。
