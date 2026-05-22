---
id: "KP-EXP-DSK-SIGN-001"
type: "error-solution"
severity: "high"
category: "code-signing"
tags: ["code-signing", "windows-authenticode", "macos-notarization", "ev-certificate", "smart-screen"]
version: "1.0.0"
confidence: 0.88
occurrences: 4
---

## 代码签名故障 (置信度: 0.88 | 技术栈: Electron/Tauri)

### 现象
Windows SmartScreen 蓝色警告、macOS Gatekeeper 阻止（"已损坏"）、构建签名失败（证书过期/PFX 无效）。

### 根因
OV 证书无 SmartScreen 信誉需积累下载量；macOS 未公证或未启用 Hardened Runtime；证书过期未续签、签名未含时间戳。

### 解决方案

```json
{ "build": { "win": {
  "sign": true, "signingHashAlgorithms": ["sha256"],
  "rfc3161TimeStampServer": "http://timestamp.digicert.com"
}}}
```

```json
{ "build": { "mac": {
  "hardenedRuntime": true, "gatekeeperAssess": false,
  "entitlements": "build/entitlements.mac.plist", "sign": true
}, "afterSign": "scripts/notarize.js" }}
```

```bash
xattr -cr /Applications/MyApp.app
```

### 验证
构建后自动验证签名（codesign --verify / signtool verify），证书到期前 30 天告警。
