---
id: "KP-EXP-ERR-DESK-002"
type: "error-solution"
severity: "medium"
category: "desktop"
tags: ["Tauri", "权限", "capabilities", "allowlist", "CORS", "文件系统", "Shell"]
version: "1.0.0"
created: "2026-04-28T10:00:00Z"
resolved: "2026-04-28T14:00:00Z"
project: "xuansto-skill"
confidence: 0.88
occurrences: 3
trigger: "bug_fix_completed"
references:
  - id: "KP-EXP-ERR-003"
    relation: "related"
  - id: "KP-GEN-020"
    relation: "complies"
---

# Tauri 权限拒绝错误

## 错误现象

Tauri 应用调用系统 API 时权限被拒绝，表现为文件系统访问失败、Shell 命令无法执行、HTTP 请求被 CORS 阻止：

```
# 文件系统访问被拒绝
Unhandled Promise Rejection: path not allowed on the configured scope: /home/user/data/config.json
Error: fs.read_text_file not allowed

# Shell 执行被拒绝
Error: shell.execute not allowed. Command "python3" is not in the allowlist

# HTTP 请求被 CORS 阻止
Access to fetch at 'https://api.example.com/data' from origin 'tauri://localhost' has been blocked by CORS policy

# Tauri 2.x 权限缺失
Error: plugin:fs:read_text_file - missing required permission: fs:allow-read-text-file
Error: core:window:create - missing capability: core:window:allow-create
```

### 典型特征

- 调用 Tauri API 时返回 `not allowed` 或 `missing permission` 错误
- 文件操作仅允许访问特定目录，超出范围即报错
- Shell 命令仅在 allowlist 中的可执行，其他一律拒绝
- 从 Tauri 1.x 迁移到 2.x 后大量 API 调用失败
- 开发环境正常但构建后权限被收紧

---

## 根因分析

### 1. Capabilities 配置缺失

Tauri 2.x 引入了基于 capabilities 的权限模型，每个窗口/插件需要显式声明所需权限：

```json
// src-tauri/capabilities/default.json（缺失关键权限）
{
  "identifier": "default",
  "windows": ["main"],
  "permissions": [
    "core:default"
  ]
}
```

缺少 `fs:allow-read-text-file` 等具体权限，导致文件系统 API 调用被拒绝。

### 2. 权限范围（Scope）不足

即使声明了权限，scope 可能未覆盖目标路径：

```json
{
  "identifier": "fs:allow-read-text-file",
  "allow": [
    { "path": "$APPDATA/config/**" }
  ]
}
```

尝试读取 `$HOME/data/config.json` 时，路径不在 `$APPDATA/config/**` 范围内，权限被拒绝。

### 3. Allowlist 未包含所需 API

Tauri 1.x 的 `tauri.conf.json` 中 allowlist 未开启对应功能：

```json
{
  "tauri": {
    "allowlist": {
      "fs": {
        "readFile": false,
        "writeFile": false
      },
      "shell": {
        "execute": false
      }
    }
  }
}
```

所有 `fs` 和 `shell` 相关 API 均被禁用。

### 4. Tauri 2.x 权限模型变更

Tauri 2.x 废弃了 `allowlist` 配置，改用 `capabilities` 系统：

| Tauri 1.x | Tauri 2.x |
|-----------|-----------|
| `tauri.allowlist.fs.readFile: true` | `permissions: ["fs:allow-read-text-file"]` |
| `tauri.allowlist.shell.execute: true` | `permissions: ["shell:allow-execute"]` |
| 全局 allowlist | 按窗口/插件分配 capabilities |
| `tauri.conf.json` 单文件 | `capabilities/` 目录下多文件 |

迁移时未完整转换权限配置，导致部分 API 失去授权。

---

## 解决方案

### 1. 在 Capabilities 中添加所需权限

```json
{
  "identifier": "default",
  "description": "主窗口默认权限",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "fs:allow-read-text-file",
    "fs:allow-write-text-file",
    "fs:allow-exists",
    "shell:allow-execute",
    "shell:allow-spawn",
    "dialog:allow-open",
    "http:default",
    "http:allow-fetch",
    "http:allow-fetch-send"
  ]
}
```

### 2. 配置带 Scope 的权限

```json
{
  "identifier": "fs:allow-read-text-file",
  "allow": [
    { "path": "$APPDATA/**" },
    { "path": "$HOME/.config/app/**" },
    { "path": "$RESOURCE/**" }
  ]
}
```

Shell 命令的 scope 配置：

```json
{
  "identifier": "shell:allow-execute",
  "allow": [
    {
      "name": "run-python",
      "cmd": "python3",
      "args": true
    },
    {
      "name": "run-git",
      "cmd": "git",
      "args": true
    }
  ]
}
```

### 3. Tauri 1.x Allowlist 配置

```json
{
  "tauri": {
    "allowlist": {
      "fs": {
        "readFile": true,
        "writeFile": true,
        "readDir": true,
        "copyFile": true,
        "createDir": true,
        "removeDir": true,
        "removeFile": true,
        "renameFile": true,
        "exists": true,
        "scope": ["$APPDATA/**", "$HOME/.config/app/**"]
      },
      "shell": {
        "execute": true,
        "sidecar": true,
        "scope": [
          {
            "name": "python3",
            "cmd": "python3",
            "args": true
          }
        ]
      },
      "http": {
        "request": true,
        "scope": [
          {
            "url": "https://api.example.com/**"
          }
        ]
      }
    }
  }
}
```

### 4. Tauri 1.x 到 2.x 权限迁移

使用官方迁移工具：

```bash
npx @tauri-apps/cli migrate
```

手动迁移对照：

```json
// Tauri 1.x: tauri.conf.json
{
  "tauri": {
    "allowlist": {
      "fs": { "readFile": true, "scope": ["$APPDATA/**"] }
    }
  }
}

// Tauri 2.x: capabilities/default.json
{
  "identifier": "default",
  "windows": ["main"],
  "permissions": [
    {
      "identifier": "fs:allow-read-text-file",
      "allow": [{ "path": "$APPDATA/**" }]
    }
  ]
}
```

### 5. HTTP 请求 CORS 处理

在 `tauri.conf.json` 中配置允许的域名：

```json
{
  "app": {
    "security": {
      "csp": "default-src 'self'; connect-src 'self' https://api.example.com"
    }
  }
}
```

Tauri 2.x 中使用 HTTP 插件的 scope：

```json
{
  "identifier": "http:default",
  "allow": [
    { "url": "https://api.example.com/**" }
  ]
}
```

---

## 预防措施

| 措施 | 说明 |
|------|------|
| 开发时启用严格权限模式 | 开发阶段即使用最小权限集，避免过度授权 |
| CI 验证权限配置完整性 | 在 CI 中检查 capabilities 覆盖所有前端调用的 API |
| 权限审计脚本 | 编写脚本对比前端 API 调用与 capabilities 声明，发现遗漏 |
| 版本迁移检查清单 | Tauri 大版本升级时逐项核对权限配置迁移 |
| Scope 最小化原则 | 仅授权应用实际需要的路径和命令，避免通配符滥用 |
| 文档同步更新 | API 变更时同步更新 capabilities 配置文档 |

## 相关知识

- [KP-EXP-ERR-003] API 契约不匹配 — 权限配置与 API 调用的契约一致性
- [KP-GEN-020] 安全编码基础 — 最小权限原则与安全配置
