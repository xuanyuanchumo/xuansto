---
id: "KP-EXP-DSK-PLAT-001"
type: "experience"
severity: "medium"
category: "cross-platform"
tags: ["windows", "macos", "compatibility", "electron", "tauri", "path-separator", "case-sensitive"]
version: "1.0.0"
confidence: 0.90
occurrences: 8
---

## Windows/macOS 平台差异 (置信度: 0.90 | 技术栈: Electron/Tauri)

### 现象
同一代码库在不同平台行为不一致：路径解析失败、文件名大小写错误导致模块找不到、文件监听器超限、自启动/托盘/窗口管理行为不同。

### 根因
路径分隔符差异（\ vs /）、文件系统大小写敏感性差异、fs.watch 底层 API 不同（FSEvents vs ReadDirectoryChangesW）、自启动机制不同（注册表 vs LaunchAgent）。

### 解决方案

```typescript
const assetPath = path.join('assets', 'images', 'logo.png');
```

```typescript
export class AutoLauncher {
  async enable() {
    if (process.platform === 'win32') execSync(`reg add "HKCU\\...\\Run" /v "${this.appName}" /d "${this.appPath}" /f`);
    else fs.writeFileSync(this.getPlistPath(), plistContent);
  }
}
```

```typescript
const win = new BrowserWindow({
  titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
  frame: process.platform !== 'darwin',
});
```

### 验证
GitHub Actions 配置 Windows + macOS 双平台构建矩阵，Linux CI 发现大小写错误。
