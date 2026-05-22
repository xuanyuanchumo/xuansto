---
id: "KP-EXP-ERR-DESK-002"
type: "error-solution"
severity: "medium"
category: "desktop"
tags: ["Tauri", "权限", "capabilities", "allowlist", "CORS", "文件系统", "Shell"]
version: "1.0.0"
confidence: 0.88
occurrences: 3
---

## Tauri 权限拒绝 (置信度: 0.88 | 技术栈: Tauri v1/v2)

### 现象
调用 Tauri API 返回 `not allowed` / `missing permission`，文件访问被 scope 拒绝，Shell 命令不在 allowlist 中。

### 根因
Tauri 2.x Capabilities 配置缺失权限、Scope 未覆盖目标路径、1.x Allowlist 未开启功能、1.x→2.x 迁移未转换权限配置。

### 解决方案

```json
{
  "identifier": "default",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "fs:allow-read-text-file",
    { "identifier": "fs:allow-read-text-file", "allow": [{ "path": "$APPDATA/**" }] },
    { "identifier": "shell:allow-execute", "allow": [{ "name": "run-python", "cmd": "python3", "args": true }] }
  ]
}
```

```bash
npx @tauri-apps/cli migrate
```

### 验证
CI 中检查 capabilities 覆盖所有前端调用的 API。
