---
id: "KP-GEN-031"
type: "desktop"
category: "tauri"
tags: ["Tauri", "桌面开发", "Rust", "跨平台", "安全模型"]
version: "1.0.0"
confidence: 0.87
---

## Tauri 最佳实践 (版本: 1.0 | 适用: Tauri v2)

### 核心规则
- 使用 Capabilities 权限模型，每个窗口仅声明必需权限（最小权限原则）
- 文件系统访问通过 Scope 限制路径，防止路径遍历攻击
- 配置 CSP + `freezePrototype: true`，禁止远程域名 IPC 访问
- 命令参数使用 `#[serde(rename_all = "camelCase")]` 匹配前端命名
- CPU 密集任务使用 `tokio::task::spawn_blocking`，避免阻塞异步运行时
- Release 构建使用 `opt-level = "z"` + `lto = true` + `strip = true` 优化体积
- 更新包必须签名验证，使用 `tauri-plugin-updater` + 公钥校验

### 代码示例

Rust 命令：
```rust
#[tauri::command]
async fn read_config(app: tauri::AppHandle, path: String) -> Result<Config, AppError> {
    if path.contains("..") { return Err(AppError::Validation("非法路径".into())); }
    let content = std::fs::read_to_string(&path)?;
    Ok(serde_json::from_str(&content)?)
}
```

前端调用：
```typescript
const config = await invoke<Config>("read_config", { path: "/app/config.json" });
```

Capabilities 配置：
```json
{
  "identifier": "main-window",
  "windows": ["main"],
  "permissions": [
    "core:default",
    { "identifier": "fs:allow-read-text-file", "allow": [{ "path": "$APPDATA/**" }] }
  ]
}
```

### 反模式
- ❌ `dangerousRemoteDomainIpcAccess` 非空 — 允许远程域调用 IPC
- ❌ 异步命令中直接执行 CPU 密集操作 — 阻塞 Tauri 主线程
- ❌ Scope 使用 `**` 通配符 — 违反最小权限原则
