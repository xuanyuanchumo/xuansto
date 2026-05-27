---
id: desktop-security-guidelines
type: knowledge
category: desktop
tags: [桌面安全, contextIsolation, IPC安全, 代码签名, 自动更新, 本地加密]
version: 1.0.0
created: 2026-04-28
updated: 2026-04-28
confidence: high
---

# 桌面应用安全指南

## Electron 安全

### contextIsolation

必须启用 `contextIsolation: true`（Electron 12+ 默认开启）：

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

- 禁止 `nodeIntegration: true`，防止渲染进程直接访问 Node API
- 禁止 `enableRemoteModule`，remote 模块已废弃且不安全
- sandbox 模式限制 preload 脚本能力

### IPC 安全

- 使用 `contextBridge.exposeInMainWorld` 暴露最小 API 面积
- IPC 消息必须校验来源和参数类型，不信任渲染进程输入
- 敏感操作（文件系统/网络/系统调用）仅在主进程执行
- 使用 IPC 通道命名规范区分权限级别

## 本地存储加密

| 数据类型 | 存储方式 | 加密策略 |
|----------|----------|----------|
| 用户凭证 | keytar / OS Keychain | 系统级加密存储 |
| 配置数据 | 加密文件 | AES-256-GCM，密钥派生自机器指纹 |
| 临时数据 | 内存 / 加密临时文件 | 进程退出即清除 |
| 日志文件 | 本地文件 | 脱敏后存储，不含敏感信息 |

- 禁止明文存储密码、Token、密钥
- 使用 OS 原生 Keychain（macOS Keychain / Windows DPAPI / Linux libsecret）
- 加密密钥不硬编码，从系统特征派生或用户输入派生

## 代码签名

- **macOS**：Apple Developer 证书签名 + 公证 (Notarization)，否则 Gatekeeper 拦截
- **Windows**：Authenticode 代码签名证书，EV 证书可立即获得 SmartScreen 信誉
- **Linux**：AppImage 无签名要求，Snap/Flatpak 使用商店签名
- 签名失败 = 用户无法安装，CI/CD 中必须验证签名步骤

## 自动更新安全

- 更新源必须使用 HTTPS，校验服务器证书
- 更新包必须验证签名（macOS 公证 + Windows Authenticode）
- 使用 Squirrel / electron-updater 时配置 `verifySignature`
- 更新检查频率合理，避免泄露用户使用模式
- 支持回滚机制，更新失败自动恢复上一版本

## 通用安全检查清单

- 依赖审计：定期 `npm audit` / `cargo audit`
- CSP 策略：Content-Security-Policy 限制资源加载
- 最小权限：仅申请必要的系统权限
- 输入校验：所有外部输入（文件/URL/IPC）均需验证
- 安全头部：Web 内容启用严格 CSP 和 X-Frame-Options
