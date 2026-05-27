---
id: desktop-security-guidelines
type: knowledge
category: desktop
tags: [桌面安全, contextIsolation, IPC安全, 代码签名, 自动更新, 本地加密]
version: 1.0.0
confidence: high
---

## 桌面应用安全指南 (版本: 1.0 | 适用: Electron/Tauri)

### 核心规则
- 必须启用 `contextIsolation: true` + `nodeIntegration: false` + `sandbox: true`
- IPC 消息校验来源和参数类型，不信任渲染进程输入
- 敏感操作（文件系统/网络/系统调用）仅在主进程执行
- 禁止明文存储密码/Token/密钥，使用 OS 原生 Keychain（macOS Keychain / Windows DPAPI / Linux libsecret）
- 代码签名：macOS Apple Developer + 公证，Windows Authenticode（EV 证书优先）
- 自动更新必须 HTTPS + 签名验证，支持回滚机制

### 代码示例

```javascript
new BrowserWindow({
  webPreferences: {
    contextIsolation: true,
    nodeIntegration: false,
    sandbox: true,
    preload: path.join(__dirname, 'preload.js')
  }
});
```

本地加密存储：
```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
cipher = Fernet(key)
encrypted = cipher.encrypt(plaintext.encode())
```

### 反模式
- ❌ `enableRemoteModule: true` — remote 模块已废弃且不安全
- ❌ 明文存储 Token 到 localStorage — 应使用系统 Keychain
- ❌ 自动更新未验证签名 — 中间人可注入恶意更新包
