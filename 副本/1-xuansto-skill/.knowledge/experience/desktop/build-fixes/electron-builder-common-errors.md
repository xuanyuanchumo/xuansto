---
id: "KP-EXP-DSK-BUILD-001"
type: "error-solution"
severity: "high"
category: "desktop-build"
tags: ["electron", "electron-builder", "build-error", "nsis", "dmg"]
version: "1.0.0"
confidence: 0.92
occurrences: 5
---

## Electron Builder 构建错误 (置信度: 0.92 | 技术栈: electron-builder)

### 现象
NSIS 打包失败（error 7125 / could not find nsh）、DMG 创建超时（hdiutil create failed）、原生模块编译失败（node-gyp / VS not found）。

### 根因
NSIS 缓存损坏或自定义脚本路径错误；DMG 残留挂载点或磁盘 I/O 竞争；构建工具链缺失或 electron-rebuild 未执行。

### 解决方案

```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\electron-builder\Cache\nsis"
```

```json
{ "build": { "nsis": { "include": "build/nsis-installer.nsh" } } }
```

```bash
xcode-select --install
npm install --global windows-build-tools
npx electron-rebuild
```

```json
{ "scripts": { "postinstall": "electron-rebuild" } }
```

### 验证
CI 中执行 electron-rebuild 并运行集成测试，构建前检查脚本验证环境。
