# IPC契约规范参考文档
> 版本: 1.9.0 | 更新日期: 2026-04-29 | 编码: UTF-8 | 行尾: LF

## 目录

- [概述](#概述)
- [契约格式规范](#契约格式规范)
- [通道定义Schema](#通道定义schema)
- [常见桌面IPC契约示例](#常见桌面ipc契约示例)
- [验证规则](#验证规则)
- [版本历史](#版本历史)

## 概述

IPC（Inter-Process Communication）契约是桌面应用（Electron/Tauri）中主进程与渲染进程之间通信的正式规范。契约定义了每个IPC通道的名称、方向、参数、返回类型和错误处理方式，确保进程间通信的类型安全和行为可预测。

### 契约目的

1. **类型安全**：确保主进程与渲染进程之间的消息格式一致
2. **文档化**：所有IPC通道必须有明确的契约文档
3. **可验证**：契约可通过 `ipc-contract-validator.js` 自动验证
4. **安全约束**：定义输入验证、速率限制和权限范围
5. **版本管理**：通道变更可追溯，支持向后兼容策略

### 适用范围

- **Electron**：`ipcMain.handle` / `ipcMain.on` ↔ `ipcRenderer.invoke` / `ipcRenderer.send`
- **Tauri**：`#[command]` / `#[tauri::command]` ↔ `invoke()` / `listen()`
- **Preload Bridge**：`contextBridge.exposeInMainWorld` 暴露的API

---

## 契约格式规范

IPC契约采用Markdown格式，每个通道使用 `## Channel: xxx` 级别标题定义。

### 文件结构

```markdown
# IPC契约文档
> 版本: x.y.z | 更新日期: YYYY-MM-DD

## Channel: `namespace:action`

| Field | Value |
|-------|-------|
| Channel Name | `namespace:action` |
| Direction | renderer→main / main→renderer |
| Description | ... |
| Since Version | x.y.z |
| Status | draft / stable / deprecated |

### Request Schema
（JSON Schema）

### Response Schema
（JSON Schema - Success + Error）

### Error Handling
（错误码表）

### Security Constraints
（安全约束）

### Version History
（版本变更记录）
```

### 命名约定

| 规则 | 说明 | 示例 |
|------|------|------|
| 命名空间前缀 | 使用 `namespace:action` 格式 | `fs:read`, `app:getVersion` |
| 冒号分隔 | 命名空间与操作用冒号分隔 | `dialog:openFile` |
| 驼峰操作 | 操作名使用camelCase | `user:getPreferences` |
| 禁止通配符 | 通道名不允许使用通配符 | ~~`fs:*`~~ |

### 方向定义

| 方向 | Electron API | Tauri API | 说明 |
|------|-------------|-----------|------|
| renderer→main (invoke) | `ipcRenderer.invoke` → `ipcMain.handle` | `invoke()` → `#[command]` | 渲染进程请求，主进程响应 |
| renderer→main (send) | `ipcRenderer.send` → `ipcMain.on` | — | 渲染进程单向发送 |
| main→renderer (push) | `BrowserWindow.webContents.send` | `app_handle.emit()` | 主进程主动推送 |

---

## 通道定义Schema

### 通道信息表

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| Channel Name | string | 是 | IPC通道名，格式 `namespace:action`，需用反引号包裹 |
| Direction | enum | 是 | `renderer→main` 或 `main→renderer` |
| Description | string | 是 | 通道功能描述 |
| Since Version | string | 是 | 引入版本号（semver） |
| Status | enum | 是 | `draft` / `stable` / `deprecated` |

### Request Schema

使用JSON Schema (Draft-07) 定义请求参数：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "action": { "type": "string" },
    "payload": { "type": "object" }
  },
  "required": ["action", "payload"],
  "additionalProperties": false
}
```

**要求**：
- 必须设置 `"additionalProperties": false` 防止未知字段
- 所有参数必须标注 `type`
- 必填字段必须列入 `required` 数组

### Response Schema

必须同时定义成功和错误响应：

**成功响应**：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "success": { "type": "boolean", "const": true },
    "data": { "type": "object" },
    "timestamp": { "type": "string", "format": "date-time" }
  },
  "required": ["success", "data"]
}
```

**错误响应**：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "success": { "type": "boolean", "const": false },
    "error": {
      "type": "object",
      "properties": {
        "code": { "type": "string" },
        "message": { "type": "string" },
        "details": { "type": "object" }
      },
      "required": ["code", "message"]
    }
  },
  "required": ["success", "error"]
}
```

### Error Handling

每个通道必须定义错误码表：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| Error Code | string | 是 | 错误码，格式 `ERR_XXX` |
| Description | string | 是 | 错误描述 |
| Recovery Strategy | string | 是 | 恢复策略 |

### Security Constraints

每个通道必须声明安全约束：

| 约束项 | 说明 |
|--------|------|
| Input Validation | 输入验证方式 |
| Rate Limiting | 速率限制 |
| Permission Scope | 所需权限范围 |
| Data Sanitization | 数据消毒策略 |
| Origin Validation | 来源验证 |
| Payload Size | 最大载荷大小 |

---

## 常见桌面IPC契约示例

### 示例1：文件系统读取

## Channel: `fs:read`

| Field | Value |
|-------|-------|
| Channel Name | `fs:read` |
| Direction | renderer→main (invoke) |
| Description | 读取本地文件内容，受安全沙箱限制 |
| Since Version | 1.0.0 |
| Status | stable |

#### Request Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "action": { "type": "string", "const": "read" },
    "payload": {
      "type": "object",
      "properties": {
        "path": { "type": "string", "description": "File path to read" },
        "encoding": { "type": "string", "enum": ["utf-8", "binary"], "default": "utf-8" }
      },
      "required": ["path"]
    }
  },
  "required": ["action", "payload"],
  "additionalProperties": false
}
```

#### Response Schema

**Success**:

```json
{
  "success": true,
  "data": {
    "content": "file content string",
    "size": 1024,
    "modified": "2026-04-29T10:00:00Z"
  },
  "timestamp": "2026-04-29T10:00:00Z"
}
```

**Error**:

```json
{
  "success": false,
  "error": {
    "code": "ERR_PERMISSION_DENIED",
    "message": "File access denied by security policy",
    "details": { "path": "/restricted/file.txt" }
  }
}
```

#### Error Handling

| Error Code | Description | Recovery Strategy |
|------------|-------------|-------------------|
| `ERR_INVALID_PARAMS` | Path parameter is missing or invalid | Validate path format and retry |
| `ERR_PERMISSION_DENIED` | File access denied by security policy | Request user permission via dialog |
| `ERR_NOT_FOUND` | File does not exist | Verify file path and retry |
| `ERR_READ_FAILED` | File read operation failed | Check file permissions and disk status |

#### Security Constraints

- **Input Validation**: Path must be within allowed directories
- **Rate Limiting**: Max 50 requests/second per renderer
- **Permission Scope**: `fs:read`
- **Data Sanitization**: Path traversal prevention (no `../` sequences)
- **Payload Size**: Max 10MB per file read

---

### 示例2：对话框操作

## Channel: `dialog:openFile`

| Field | Value |
|-------|-------|
| Channel Name | `dialog:openFile` |
| Direction | renderer→main (invoke) |
| Description | 打开原生文件选择对话框 |
| Since Version | 1.0.0 |
| Status | stable |

#### Request Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "action": { "type": "string", "const": "openFile" },
    "payload": {
      "type": "object",
      "properties": {
        "title": { "type": "string", "default": "Open File" },
        "filters": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": { "type": "string" },
              "extensions": { "type": "array", "items": { "type": "string" } }
            }
          }
        },
        "multiSelect": { "type": "boolean", "default": false }
      }
    }
  },
  "required": ["action"],
  "additionalProperties": false
}
```

#### Response Schema

**Success**:

```json
{
  "success": true,
  "data": {
    "filePaths": ["/path/to/selected/file.txt"],
    "canceled": false
  },
  "timestamp": "2026-04-29T10:00:00Z"
}
```

**Error**:

```json
{
  "success": false,
  "error": {
    "code": "ERR_DIALOG_FAILED",
    "message": "Failed to open dialog",
    "details": {}
  }
}
```

#### Error Handling

| Error Code | Description | Recovery Strategy |
|------------|-------------|-------------------|
| `ERR_DIALOG_FAILED` | Native dialog failed to open | Retry or use fallback UI |
| `ERR_PERMISSION_DENIED` | User denied file access | Inform user and offer retry |

#### Security Constraints

- **Input Validation**: Filter extensions must be pre-registered
- **Rate Limiting**: Max 5 dialogs per minute per renderer
- **Permission Scope**: `dialog:open`
- **Origin Validation**: Only main window may invoke

---

### 示例3：应用状态推送

## Channel: `app:stateChanged`

| Field | Value |
|-------|-------|
| Channel Name | `app:stateChanged` |
| Direction | main→renderer (push) |
| Description | 主进程推送应用状态变更事件 |
| Since Version | 1.2.0 |
| Status | stable |

#### Event Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "event": { "type": "string", "enum": ["online", "offline", "update-available", "update-downloaded"] },
    "data": { "type": "object" },
    "timestamp": { "type": "string", "format": "date-time" }
  },
  "required": ["event", "timestamp"]
}
```

#### Security Constraints

- **Origin Validation**: Only main process may emit
- **Rate Limiting**: Max 100 events/second
- **Payload Size**: Max 1KB per event

---

### 示例4：自动更新检查

## Channel: `updater:checkForUpdate`

| Field | Value |
|-------|-------|
| Channel Name | `updater:checkForUpdate` |
| Direction | renderer→main (invoke) |
| Description | 检查应用更新 |
| Since Version | 1.3.0 |
| Status | stable |

#### Request Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "action": { "type": "string", "const": "checkForUpdate" },
    "payload": {
      "type": "object",
      "properties": {
        "channel": { "type": "string", "enum": ["stable", "beta"], "default": "stable" },
        "forceCheck": { "type": "boolean", "default": false }
      }
    }
  },
  "required": ["action"],
  "additionalProperties": false
}
```

#### Response Schema

**Success**:

```json
{
  "success": true,
  "data": {
    "updateAvailable": true,
    "latestVersion": "2.0.0",
    "currentVersion": "1.9.5",
    "releaseNotes": "Bug fixes and performance improvements",
    "downloadUrl": "https://releases.example.com/app-2.0.0.dmg"
  },
  "timestamp": "2026-04-29T10:00:00Z"
}
```

**Error**:

```json
{
  "success": false,
  "error": {
    "code": "ERR_UPDATE_CHECK_FAILED",
    "message": "Failed to check for updates",
    "details": { "reason": "network_error" }
  }
}
```

#### Error Handling

| Error Code | Description | Recovery Strategy |
|------------|-------------|-------------------|
| `ERR_UPDATE_CHECK_FAILED` | Update check request failed | Retry with exponential backoff |
| `ERR_NETWORK_ERROR` | Network connection error | Check connectivity and retry |
| `ERR_UPDATE_DISABLED` | Auto-update is disabled by policy | Inform user to check manually |

#### Security Constraints

- **Input Validation**: Channel must be valid enum value
- **Rate Limiting**: Max 1 check per 5 minutes
- **Permission Scope**: `updater:check`
- **Origin Validation**: Only main window may invoke

---

## 验证规则

以下验证规则与 `ipc-contract-validator.js` 的验证逻辑对齐：

### 通道名提取规则

验证器从契约Markdown文件中提取通道名的方式：

| 提取方式 | 正则模式 | 说明 |
|----------|---------|------|
| 表格行 | `\| Channel Name \| \`xxx\` \|` | 从通道信息表提取 |
| 标题 | `## Channel: \`xxx\`` | 从章节标题提取 |
| 代码块 - ipcMain | `ipcMain.handle('xxx'` / `ipcMain.on('xxx'` | 从Electron主进程代码提取 |
| 代码块 - ipcRenderer | `ipcRenderer.invoke('xxx'` | 从渲染进程代码提取 |
| 代码块 - Tauri | `pub async fn xxx` | 从Tauri命令提取（下划线转冒号） |

### 验证检查项

| 检查项 | 级别 | 说明 |
|--------|------|------|
| 主进程通道必须在preload中暴露 | Warning | 主进程handler存在但preload未暴露 |
| Preload暴露通道必须在主进程有handler | Error | preload暴露了通道但主进程无对应handler |
| 主进程通道必须在契约中记录 | Warning | 实现了但未文档化 |
| 契约中记录的通道必须已实现 | Warning | 文档化了但未实现 |
| Preload暴露通道必须在契约中记录 | Warning | preload暴露但未文档化 |
| 主进程handler必须包含try/catch | Warning | 缺少错误处理 |

### 验证命令

```bash
node ipc-contract-validator.js \
  --main ./src/main/index.js \
  --preload ./src/preload/index.js \
  --contract ./docs/ipc-contracts.md \
  --verbose
```

### 验证输出格式

```
=== IPC Contract Validation Report ===

📋 Info:
   Found N IPC channels in main process
   Found N exposed channels in preload script
   Found N channels in contract document

📡 Main Process Channels:
   [handle] fs:read
   [handle] dialog:openFile

🔗 Preload Exposed Channels:
   window.api.readFile → fs:read (invoke)

📄 Contract Documented Channels:
   fs:read
   dialog:openFile

⚠️  Warnings (N):
   Channel "xxx" in main process is NOT documented in contract

❌ Errors (N):
   Channel "xxx" exposed in preload but has NO handler in main process

✅ Validation PASSED
   0 errors, 2 warnings
```

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.6.0 | 2026-04-29 | 初始版本：定义IPC契约规范格式、通道Schema、示例契约和验证规则 |
