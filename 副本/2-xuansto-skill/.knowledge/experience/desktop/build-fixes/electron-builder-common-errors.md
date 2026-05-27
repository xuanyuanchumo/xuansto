---
id: "KP-EXP-DSK-BUILD-001"
type: "error-solution"
severity: "high"
category: "desktop-build"
tags:
  - "electron"
  - "electron-builder"
  - "build-error"
  - "nsis"
  - "dmg"
version: "1.0.0"
created: "2026-04-28"
confidence: 0.92
occurrences: 5
---

# Electron Builder 常见构建错误与修复

## 错误现象

### 错误 1: NSIS 打包失败

在 Windows 平台构建时，NSIS 安装程序打包阶段报错，典型错误信息：

```
Error: NSIS Error: error 7125 executing makensis.exe
  at NsisTarget.executeMakensis [as _executeMakensis]
  ...

NSIS output:
Processing config: C:\Users\builder\AppData\Local\electron-builder\Cache\nsis\nsis-3.0.4.1\nsisconf.nsh
!include: could not find: "C:\Users\builder\AppData\Local\Temp\bt-xxxxx\nsis\messages.nsh"
Error in script "<stdin>" on line 42 -- aborting creation process
```

或出现自定义 NSIS 脚本引用路径不存在的问题。

### 错误 2: DMG 创建超时

在 macOS 平台构建 DMG 安装镜像时，进程长时间挂起后超时：

```
Error: DMG creation failed: Timeout after 300000ms
  at DmgTarget.build [as _build]
  ...

hdiutil: create failed - Resource busy
```

常见于 CI 环境或磁盘 I/O 负载较高的场景。

### 错误 3: 原生模块编译失败

构建过程中原生 Node 模块（如 better-sqlite3、keytar、node-gyp 相关模块）编译失败：

```
Error: node-gyp failed to rebuild 'better-sqlite3@11.0.0'
  gyp ERR! find VS
  gyp ERR! find VS msvs_version not set from command line or npm config
  gyp ERR! find VS VCINSTALLDIR not set, not running in VS Command Prompt
  gyp ERR! find VS could not find a Visual Studio installation
```

或在 macOS 上：

```
Error: node-gyp failed to rebuild 'keytar@7.9.0'
  gyp ERR! find Xcode
  gyp ERR! find Xcode no Xcode or CLT version detected
```

## 根因分析

### NSIS 打包失败根因

1. **缓存损坏**：electron-builder 的 NSIS 缓存（`%LOCALAPPDATA%\electron-builder\Cache\nsis`）中的文件不完整或版本不匹配
2. **自定义脚本路径错误**：`include` 配置项引用的 NSIS 脚本使用了相对路径，而 electron-builder 在临时目录中执行 makensis，导致相对路径解析失败
3. **路径含特殊字符**：项目路径或用户目录包含中文、空格等特殊字符，NSIS 的 makensis.exe 对 Unicode 路径支持不完整

### DMG 创建超时根因

1. **磁盘 I/O 竞争**：CI 环境中多个构建任务并发，磁盘写入带宽不足
2. **hdiutil 挂载冲突**：残留的 DMG 挂载点未正确卸载，导致新 DMG 创建时资源占用
3. **文件系统延迟**：APFS 卷在大量小文件操作时性能下降，DMG 创建过程涉及大量文件拷贝

### 原生模块编译失败根因

1. **构建工具链缺失**：Windows 上缺少 Visual Studio Build Tools 或 macOS 上缺少 Xcode Command Line Tools
2. **Node 版本不匹配**：electron 使用的 Node 版本与系统安装的 Node 版本不同，原生模块需要针对 electron 的 Node headers 编译
3. **electron-rebuild 未执行**：npm install 后未运行 electron-rebuild，导致原生模块使用系统 Node ABI 编译而非 Electron ABI

## 解决方案

### NSIS 打包失败修复

**方案 1: 清除 NSIS 缓存**

```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\electron-builder\Cache\nsis"
```

```bash
rm -rf ~/Library/Caches/electron-builder/nsis
```

**方案 2: 修正自定义 NSIS 脚本路径**

```json
{
  "build": {
    "nsis": {
      "include": "build/nsis-installer.nsh",
      "script": "build/nsis-installer.nsi"
    }
  }
}
```

确保 `build/nsis-installer.nsh` 文件存在且使用项目相对路径。electron-builder 会自动将 `build` 目录下的文件复制到临时构建目录。

**方案 3: 使用绝对路径或环境变量**

```json
{
  "build": {
    "nsis": {
      "include": "${projectDir}/build/nsis-installer.nsh"
    },
    "extraResources": [
      {
        "from": "build/assets",
        "to": "assets",
        "filter": ["**/*"]
      }
    ]
  }
}
```

**方案 4: 避免特殊字符路径**

将项目克隆到不含空格和中文的路径下：

```powershell
git clone https://github.com/org/repo.git C:\build\repo
```

### DMG 创建超时修复

**方案 1: 清理残留挂载点**

```bash
mount | grep '/Volumes/.*' | awk '{print $3}' | xargs -I {} umount -f {}
```

**方案 2: 增加超时时间**

```json
{
  "build": {
    "mac": {
      "target": [
        {
          "target": "dmg",
          "arch": ["universal"]
        }
      ]
    },
    "dmg": {
      "writeUpdateInfo": false,
      "background": null
    }
  }
}
```

**方案 3: 使用 zip 替代 DMG 在 CI 中**

```json
{
  "build": {
    "mac": {
      "target": [
        {
          "target": "zip",
          "arch": ["x64"]
        },
        {
          "target": "dmg",
          "arch": ["x64"]
        }
      ]
    }
  }
}
```

CI 中仅构建 zip 用于测试，DMG 在发布构建中生成。

**方案 4: 禁用 DMG 背景图和窗口定制**

```json
{
  "build": {
    "dmg": {
      "background": null,
      "backgroundColor": "#ffffff",
      "window": {
        "width": 540,
        "height": 380
      },
      "contents": [
        { "x": 144, "y": 150 },
        { "x": 396, "y": 150, "type": "link", "path": "/Applications" }
      ]
    }
  }
}
```

### 原生模块编译失败修复

**方案 1: 安装构建工具链**

Windows:

```powershell
npm install --global windows-build-tools
npm install --global node-gyp
```

或手动安装 Visual Studio Build Tools 2022，勾选 "C++ build tools" 工作负载。

macOS:

```bash
xcode-select --install
```

**方案 2: 配置 electron-rebuild**

```json
{
  "scripts": {
    "postinstall": "electron-rebuild"
  },
  "devDependencies": {
    "electron-rebuild": "^3.2.9"
  }
}
```

**方案 3: 使用 electron-builder 的原生模块重建**

```json
{
  "build": {
    "npmRebuild": true,
    "buildDependenciesFromSource": true
  }
}
```

**方案 4: 针对特定模块指定重建**

```javascript
const { rebuild } = require('electron-rebuild');

async function main() {
  await rebuild({
    buildPath: process.cwd(),
    electronVersion: '28.0.0',
    modules: ['better-sqlite3', 'keytar'],
    debug: true
  });
}

main().catch(console.error);
```

**方案 5: 使用 electron-forge 集成方案**

```javascript
module.exports = {
  packagerConfig: {
    asar: true,
    ignore: [
      /^\/\.github/,
      /^\/\.vscode/,
      /^\/test/
    ]
  },
  makers: [
    {
      name: '@electron-forge/maker-squirrel',
      config: {
        name: 'MyApp'
      }
    },
    {
      name: '@electron-forge/maker-dmg',
      config: {
        background: './assets/dmg-background.png',
        format: 'ULFO'
      }
    }
  ],
  plugins: [
    {
      name: '@electron-forge/plugin-auto-unpack-natives',
      config: {}
    }
  ]
};
```

## 预防措施

1. **CI 缓存策略**：对 electron-builder 缓存目录配置 CI 缓存，避免每次构建重新下载 NSIS 和框架
2. **锁定 electron-builder 版本**：在 `devDependencies` 中锁定 electron-builder 精确版本，避免版本升级引入不兼容
3. **构建前检查脚本**：添加 prebuild 脚本验证构建环境

```json
{
  "scripts": {
    "prebuild": "node scripts/check-build-env.js",
    "build": "electron-builder --publish never"
  }
}
```

```javascript
const { execSync } = require('child_process');
const platform = process.platform;

if (platform === 'win32') {
  try {
    execSync('where makensis', { stdio: 'ignore' });
  } catch {
    console.warn('NSIS not found, electron-builder will download it');
  }
} else if (platform === 'darwin') {
  try {
    execSync('xcode-select -p', { stdio: 'ignore' });
  } catch {
    console.error('Xcode CLT not installed. Run: xcode-select --install');
    process.exit(1);
  }
}
```

4. **原生模块白名单**：尽量减少原生模块使用，优先选择纯 JavaScript 替代方案
5. **多平台构建矩阵**：在对应平台上构建对应产物，避免交叉编译

## 相关知识

- [electron-builder 官方文档 - NSIS 配置](https://www.electron.build/configuration/nsis)
- [electron-builder 官方文档 - DMG 配置](https://www.electron.build/configuration/dmg)
- [electron-rebuild 工作原理](https://github.com/electron/electron-rebuild)
- [node-gyp 与 Electron 原生模块](https://www.electronjs.org/docs/latest/tutorial/using-native-node-modules)
- [NSIS 脚本参考手册](https://nsis.sourceforge.io/Docs/)
