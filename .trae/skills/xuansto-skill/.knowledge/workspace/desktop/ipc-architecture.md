---
id: "KP-WS-DSK-IPC-001"
type: "architecture"
project: "xuansto-skill"
version: "1.0.0"
tags: ["ipc", "electron", "tauri", "main-process", "renderer-process", "preload"]
confidence: 0.95
---

# IPC架构设计 - 桌面应用进程间通信

## 1. IPC架构概述

桌面应用（Electron / Tauri）采用多进程架构，核心分为三个层次：

- **主进程（Main Process）**：应用入口，管理窗口生命周期、原生API调用、文件系统访问。拥有完整Node.js或Rust运行时能力。
- **渲染进程（Renderer Process）**：运行Web内容（HTML/CSS/JS），负责UI渲染与用户交互。受沙箱限制，无法直接访问系统资源。
- **预加载脚本（Preload Script）**：桥接主进程与渲染进程的安全中间层。在渲染进程的Web内容加载前执行，可选择性暴露受控API给渲染进程。

```
┌─────────────────────────────────────────────────┐
│                  Main Process                    │
│  (Node.js / Rust)                               │
│  - 窗口管理  - 文件系统  - 原生API              │
└──────────┬──────────────────────┬───────────────┘
           │ IPC                  │ IPC
┌──────────▼──────────┐  ┌───────▼───────────────┐
│   Preload Script    │  │   Preload Script      │
│   contextBridge     │  │   contextBridge       │
└──────────┬──────────┘  └───────┬───────────────┘
           │ expose               │ expose
┌──────────▼──────────┐  ┌───────▼───────────────┐
│  Renderer Process   │  │  Renderer Process     │
│  (Chromium / WebView)│  │ (Chromium / WebView) │
└─────────────────────┘  └───────────────────────┘
```

IPC通信的本质：渲染进程无法直接调用系统API，必须通过预定义的通道（Channel）与主进程交换消息，由主进程代为执行特权操作后返回结果。

## 2. Electron IPC模式

### 2.1 Request-Response（ipcMain.handle / ipcRenderer.invoke）

适用于需要返回值的异步操作，如读取文件、调用系统对话框。

主进程注册handler：

```typescript
import { ipcMain, dialog } from "electron";

ipcMain.handle("dialog:openFile", async (_event, options: { filters?: FileFilter[] }) => {
  const result = await dialog.showOpenDialog({
    properties: ["openFile"],
    filters: options.filters,
  });
  return result.filePaths;
});

ipcMain.handle("fs:readFile", async (_event, filePath: string, encoding: BufferEncoding = "utf-8") => {
  const fs = await import("fs/promises");
  return fs.readFile(filePath, { encoding });
});
```

预加载脚本暴露API：

```typescript
import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("electronAPI", {
  openFile: (options?: { filters?: FileFilter[] }) =>
    ipcRenderer.invoke("dialog:openFile", options),
  readFile: (filePath: string, encoding?: BufferEncoding) =>
    ipcRenderer.invoke("fs:readFile", filePath, encoding),
});
```

渲染进程调用：

```typescript
const filePaths = await window.electronAPI.openFile({
  filters: [{ name: "Images", extensions: ["png", "jpg"] }],
});
```

### 2.2 Fire-and-Forget（ipcMain.on / ipcRenderer.send）

适用于不需要返回值的单向通知，如日志记录、状态变更通知。

```typescript
import { ipcMain } from "electron";

ipcMain.on("analytics:trackEvent", (_event, eventName: string, payload: Record<string, unknown>) => {
  persistEvent(eventName, payload);
});
```

```typescript
import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("electronAPI", {
  trackEvent: (eventName: string, payload: Record<string, unknown>) => {
    ipcRenderer.send("analytics:trackEvent", eventName, payload);
  },
});
```

### 2.3 Main→Renderer Push（webContents.send）

主进程主动推送消息到渲染进程，如下载进度、系统通知、实时数据更新。

```typescript
import { BrowserWindow } from "electron";

function sendDownloadProgress(win: BrowserWindow, percent: number) {
  win.webContents.send("download:progress", { percent, timestamp: Date.now() });
}
```

```typescript
import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("electronAPI", {
  onDownloadProgress: (callback: (progress: { percent: number; timestamp: number }) => void) => {
    const handler = (_event: Electron.IpcRendererEvent, data: { percent: number; timestamp: number }) => callback(data);
    ipcRenderer.on("download:progress", handler);
    return () => ipcRenderer.removeListener("download:progress", handler);
  },
});
```

渲染进程使用：

```typescript
const unsubscribe = window.electronAPI.onDownloadProgress((progress) => {
  updateProgressBar(progress.percent);
});
```

## 3. Tauri IPC模式

### 3.1 Tauri Command（Request-Response）

使用Rust函数标注`#[tauri::command]`，自动生成TypeScript绑定。

Rust端：

```rust
use tauri::command;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
pub struct FileInfo {
    name: String,
    size: u64,
    modified: String,
}

#[command]
pub async fn read_file_metadata(path: String) -> Result<FileInfo, String> {
    let metadata = std::fs::metadata(&path).map_err(|e| e.to_string())?;
    Ok(FileInfo {
        name: path.split('/').last().unwrap_or("").to_string(),
        size: metadata.len(),
        modified: metadata.modified()
            .map(|t| {
                let datetime: chrono::DateTime<chrono::Utc> = t.into();
                datetime.to_rfc3339()
            })
            .unwrap_or_default(),
    })
}

#[command]
pub fn list_directory(path: String) -> Result<Vec<String>, String> {
    std::fs::read_dir(&path)
        .map_err(|e| e.to_string())?
        .filter_map(|entry| entry.ok())
        .map(|entry| entry.file_name().to_string_lossy().to_string())
        .map(Ok)
        .collect()
}
```

注册命令：

```rust
fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            read_file_metadata,
            list_directory,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

TypeScript端调用：

```typescript
import { invoke } from "@tauri-apps/api/core";

const metadata = await invoke<FileInfo>("read_file_metadata", { path: "/home/user/doc.txt" });
const entries = await invoke<string[]>("list_directory", { path: "/home/user" });
```

### 3.2 Tauri Event（Pub/Sub）

支持进程间的事件发布/订阅，包括Rust→前端、前端→Rust、前端→前端。

Rust端发射事件：

```rust
use tauri::{AppHandle, Emitter};

#[tauri::command]
pub async fn start_sync(app: AppHandle) -> Result<(), String> {
    for i in 0..=100 {
        tokio::time::sleep(std::time::Duration::from_millis(50)).await;
        app.emit("sync:progress", SyncProgress { percent: i, message: format!("Processing {}", i) }).map_err(|e| e.to_string())?;
    }
    Ok(())
}
```

TypeScript端监听事件：

```typescript
import { listen } from "@tauri-apps/api/event";

interface SyncProgress {
  percent: number;
  message: string;
}

const unlisten = await listen<SyncProgress>("sync:progress", (event) => {
  console.log(`Sync: ${event.payload.percent}% - ${event.payload.message}`);
});
```

前端→前端通信：

```typescript
import { emit, listen } from "@tauri-apps/api/event";

await emit("tab:selectionChanged", { tabId: "settings" });

const unlisten = await listen("tab:selectionChanged", (event) => {
  switchTab(event.payload.tabId);
});
```

## 4. IPC安全原则

### 4.1 contextIsolation

必须启用`contextIsolation: true`（Electron默认已启用），防止渲染进程中的恶意代码修改预加载脚本暴露的原型链。

```typescript
const mainWindow = new BrowserWindow({
  webPreferences: {
    contextIsolation: true,
    nodeIntegration: false,
    sandbox: true,
    preload: path.join(__dirname, "preload.js"),
  },
});
```

### 4.2 Channel校验

主进程handler必须校验通道名称与调用来源，防止未授权的IPC调用。

```typescript
const ALLOWED_CHANNELS = new Set([
  "dialog:openFile",
  "fs:readFile",
  "fs:writeFile",
  "analytics:trackEvent",
]);

ipcMain.handle("dialog:openFile", async (event, ...args) => {
  if (!event.senderFrame.url.startsWith("app://")) {
    throw new Error("Unauthorized IPC source");
  }
  return handleOpenFile(args);
});
```

预加载脚本白名单过滤：

```typescript
import { contextBridge, ipcRenderer } from "electron";

const ALLOWED_CHANNELS = new Set(["dialog:openFile", "fs:readFile"]);

contextBridge.exposeInMainWorld("electronAPI", {
  invoke: (channel: string, ...args: unknown[]) => {
    if (!ALLOWED_CHANNELS.has(channel)) {
      throw new Error(`IPC channel not allowed: ${channel}`);
    }
    return ipcRenderer.invoke(channel, ...args);
  },
});
```

### 4.3 输入清洗

所有从渲染进程传入的参数必须进行类型校验与清洗，防止注入攻击。

```typescript
import { ipcMain } from "electron";
import { z } from "zod";

const ReadFileSchema = z.object({
  filePath: z.string().max(512).refine(
    (p) => !p.includes("..") && !p.startsWith("/etc"),
    { message: "Path traversal detected" }
  ),
  encoding: z.enum(["utf-8", "ascii", "base64"]).default("utf-8"),
});

ipcMain.handle("fs:readFile", async (_event, raw: unknown) => {
  const parsed = ReadFileSchema.parse(raw);
  return safeReadFile(parsed.filePath, parsed.encoding);
});
```

## 5. IPC通道命名规范

采用`domain:action`两级命名，确保通道语义清晰、避免冲突。

| 前缀       | 用途                  | 示例                          |
|-----------|----------------------|-------------------------------|
| `app:`    | 应用生命周期          | `app:ready`, `app:quit`       |
| `fs:`     | 文件系统操作          | `fs:readFile`, `fs:writeFile` |
| `dialog:` | 系统对话框            | `dialog:openFile`, `dialog:save` |
| `store:`  | 持久化存储            | `store:get`, `store:set`      |
| `net:`    | 网络请求代理          | `net:fetch`, `net:upload`     |
| `win:`    | 窗口管理              | `win:minimize`, `win:close`   |
| `clip:`   | 剪贴板操作            | `clip:readText`, `clip:write` |
| `notify:` | 系统通知              | `notify:send`                 |
| `auto:`   | 自动更新              | `auto:check`, `auto:download` |
| `shell:`  | Shell/外部程序        | `shell:open`, `shell:execute` |

命名规则：
- 全部使用camelCase命名action部分
- 禁止使用动态拼接的通道名（如`fs:${operation}`）
- 新增通道必须在项目级`ipc-channels.ts`中集中声明

```typescript
export const IPC_CHANNELS = {
  APP_READY: "app:ready",
  APP_QUIT: "app:quit",
  FS_READ_FILE: "fs:readFile",
  FS_WRITE_FILE: "fs:writeFile",
  DIALOG_OPEN_FILE: "dialog:openFile",
  DIALOG_SAVE: "dialog:save",
  STORE_GET: "store:get",
  STORE_SET: "store:set",
  NET_FETCH: "net:fetch",
  WIN_MINIMIZE: "win:minimize",
  WIN_CLOSE: "win:close",
} as const;

export type IpcChannel = typeof IPC_CHANNELS[keyof typeof IPC_CHANNELS];
```

## 6. 性能考量

### 6.1 序列化开销

IPC消息需经过结构化克隆算法（Electron）或JSON序列化（Tauri），以下类型会产生额外开销：

- **DOM对象**：无法直接传递，必须提取原始数据
- **Proxy/Getter**：序列化时触发getter，可能产生副作用
- **循环引用**：结构化克隆会抛出异常
- **TypedArray**：会被复制而非转移

```typescript
const data = new Uint8Array(10 * 1024 * 1024);
await ipcRenderer.invoke("process:largeBuffer", data.buffer);
```

### 6.2 大数据传输策略

**Electron - 使用MessagePort传输流式数据：**

```typescript
import { ipcMain, MessageChannelMain } from "electron";

ipcMain.handle("stream:connect", (event) => {
  const { port1, port2 } = new MessageChannelMain();
  event.senderFrame.postMessage("stream:port", { port: port1 }, [port1]);
  port2.on("message", (msg) => {
    port2.postMessage(processChunk(msg.data));
  });
  port2.start();
});
```

**Tauri - 使用临时文件 + 流式读取：**

```rust
use std::io::Write;

#[tauri::command]
pub async fn export_large_dataset(output_path: String) -> Result<String, String> {
    let mut file = std::fs::File::create(&output_path).map_err(|e| e.to_string())?;
    for chunk in generate_chunks() {
        file.write_all(&chunk).map_err(|e| e.to_string())?;
    }
    Ok(output_path)
}
```

### 6.3 批量合并与节流

高频IPC调用应合并为批量操作，减少通信次数：

```typescript
class IpcBatcher<T> {
  private queue: T[] = [];
  private timer: ReturnType<typeof setTimeout> | null = null;

  constructor(
    private channel: string,
    private flushInterval: number = 16,
    private maxBatchSize: number = 50,
  ) {}

  push(item: T) {
    this.queue.push(item);
    if (this.queue.length >= this.maxBatchSize) {
      this.flush();
      return;
    }
    if (!this.timer) {
      this.timer = setTimeout(() => this.flush(), this.flushInterval);
    }
  }

  private flush() {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    if (this.queue.length === 0) return;
    const batch = this.queue.splice(0);
    ipcRenderer.send(this.channel, batch);
  }
}

const analyticsBatcher = new IpcBatcher<{ event: string; ts: number }>("analytics:batchTrack");
analyticsBatcher.push({ event: "click", ts: Date.now() });
```

### 6.4 性能对比参考

| 操作类型              | Electron (invoke) | Tauri (invoke) | 说明                     |
|----------------------|-------------------|----------------|--------------------------|
| 简单字符串往返        | ~0.3ms            | ~0.1ms         | Tauri FFI开销更低        |
| 1KB JSON序列化        | ~0.5ms            | ~0.2ms         | Rust serde性能优势       |
| 1MB Buffer传输        | ~15ms             | ~8ms           | Tauri零拷贝优化          |
| 1000次连续invoke      | ~300ms            | ~100ms         | 批量合并可显著降低       |
