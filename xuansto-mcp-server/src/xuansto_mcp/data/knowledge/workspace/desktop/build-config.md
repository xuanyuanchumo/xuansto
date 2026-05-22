---
id: "KP-WS-DSK-BUILD-001"
type: "configuration"
project: "xuansto-skill"
version: "1.0.0"
tags: ["electron-builder", "tauri-bundler", "build-config", "code-signing", "auto-update"]
confidence: 0.93
---

# 桌面应用构建配置

## 1. 构建配置概述

桌面应用构建配置涵盖打包、签名、分发、更新四个核心环节。Electron使用electron-builder作为主流打包工具，Tauri使用内置的tauri-bundler。两者均支持多平台构建输出，但配置结构与签名流程存在显著差异。

构建流程关键路径：

```
源代码 → 编译/打包 → 平台产物 → 代码签名 → 安装包/便携版 → 分发渠道 → 自动更新
```

核心配置文件：
- Electron: `electron-builder.yml` 或 `package.json` 中的 `build` 字段
- Tauri: `src-tauri/tauri.conf.json`

## 2. Electron构建配置

### 2.1 electron-builder.yml 核心配置

```yaml
appId: com.xuansto.desktop
productName: Xuansto
copyright: Copyright © 2026 Xuansto Team

directories:
  output: dist
  buildResources: build
  intermediateCache: .cache/electron-builder

files:
  - dist/**/*
  - "!dist/**/*.map"
  - "!node_modules/**/{test,tests,__tests__,spec}/**"
  - "!node_modules/**/*.md"
  - "!node_modules/**/*.ts"

extraResources:
  - from: assets/bin
    to: bin
    filter:
      - "**/*.exe"
      - "**/*.dll"

asar: true
asarUnpack:
  - "**/*.node"
  - "**/*.dll"
  - "**/native/**"

win:
  target:
    - target: nsis
      arch:
        - x64
        - arm64
    - target: portable
      arch:
        - x64
  icon: build/icon.ico
  artifactName: "${productName}-${version}-${arch}.${ext}"

nsis:
  oneClick: false
  allowToChangeInstallationDirectory: true
  installerIcon: build/icon.ico
  uninstallerIcon: build/icon.ico
  installerHeaderIcon: build/headerIcon.bmp
  installerSidebar: build/sidebar.bmp
  createDesktopShortcut: true
  createStartMenuShortcut: true
  shortcutName: "${productName}"
  perMachine: false
  differentialPackage: true

mac:
  target:
    - target: dmg
      arch:
        - universal
    - target: zip
      arch:
        - universal
  icon: build/icon.icns
  category: public.app-category.developer-tools
  hardenedRuntime: true
  gatekeeperAssess: false
  entitlements: build/entitlements.mac.plist
  entitlementsInherit: build/entitlements.mac.inherit.plist
  extendInfo:
    NSDocumentsFolderUsageDescription: "Xuansto needs access to your Documents folder."
    NSDownloadsFolderUsageDescription: "Xuansto needs access to your Downloads folder."

dmg:
  title: "${productName} ${version}"
  icon: build/icon.icns
  contents:
    - x: 130
      y: 220
    - x: 410
      y: 220
      type: link
      path: /Applications

linux:
  target:
    - target: AppImage
      arch:
        - x64
    - target: deb
      arch:
        - x64
    - target: snap
      arch:
        - x64
  icon: build/icon.png
  category: Development
  maintainer: team@xuansto.dev
  vendor: Xuansto
  synopsis: Multi-agent development orchestration tool
  description: Xuansto is a desktop application for multi-agent autonomous development orchestration.

appImage:
  license: LICENSE

deb:
  depends:
    - libnotify4
    - libxtst6
    - libnss3

publish:
  provider: github
  owner: xuansto
  repo: xuansto-desktop
  releaseType: release
```

### 2.2 package.json构建脚本

```json
{
  "scripts": {
    "build": "tsc && electron-vite build",
    "pack": "electron-builder --dir",
    "dist": "electron-builder",
    "dist:win": "electron-builder --win",
    "dist:mac": "electron-builder --mac",
    "dist:linux": "electron-builder --linux",
    "release": "electron-builder --publish always"
  },
  "build": {
    "extends": null
  }
}
```

## 3. Tauri构建配置

### 3.1 tauri.conf.json 核心配置

```json
{
  "$schema": "https://raw.githubusercontent.com/tauri-apps/tauri/dev/crates/tauri-cli/schema.json",
  "productName": "Xuansto",
  "version": "1.0.0",
  "identifier": "com.xuansto.desktop",
  "build": {
    "beforeBuildCommand": "npm run build",
    "beforeDevCommand": "npm run dev",
    "frontendDist": "../dist",
    "devUrl": "http://localhost:1420"
  },
  "app": {
    "title": "Xuansto",
    "windows": [
      {
        "title": "Xuansto",
        "width": 1200,
        "height": 800,
        "minWidth": 800,
        "minHeight": 600,
        "resizable": true,
        "fullscreen": false,
        "decorations": true,
        "transparent": false,
        "center": true
      }
    ],
    "security": {
      "csp": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
      "dangerousDisableAssetCspModification": false
    }
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ],
    "resources": [
      "assets/*"
    ],
    "copyright": "Copyright © 2026 Xuansto Team",
    "category": "DeveloperTool",
    "shortDescription": "Multi-agent development orchestration tool",
    "longDescription": "Xuansto is a desktop application for multi-agent autonomous development orchestration with SDD+TDD fusion.",
    "windows": {
      "certificateThumbprint": null,
      "digestAlgorithm": "sha256",
      "timestampUrl": "http://timestamp.digicert.com",
      "wix": null,
      "nsis": {
        "languages": [
          "SimpChinese",
          "English"
        ],
        "displayLanguageSelector": true,
        "installerIcon": "icons/icon.ico",
        "headerImage": "icons/header.bmp",
        "sidebarImage": "icons/sidebar.bmp",
        "installMode": "currentUser",
        "license": "../LICENSE"
      }
    },
    "macOS": {
      "frameworks": [],
      "minimumSystemVersion": "10.15",
      "exceptionDomain": "",
      "signingIdentity": null,
      "providerShortName": null,
      "entitlements": null
    },
    "linux": {
      "deb": {
        "depends": [
          "libwebkit2gtk-4.1-0",
          "libgtk-3-0"
        ]
      },
      "appimage": {
        "bundleMediaFramework": false
      }
    },
    "externalBin": [],
    "fileAssociations": [],
    "protocols": [
      {
        "name": "xuansto",
        "schemes": [
          "xuansto"
        ]
      }
    ]
  }
}
```

### 3.2 Tauri Cargo.toml构建优化

```toml
[profile.release]
strip = true
lto = true
codegen-units = 1
opt-level = "s"
panic = "abort"

[bundle]
name = "Xuansto"
identifier = "com.xuansto.desktop"
icon = ["icons/icon.ico"]
resources = ["assets/*"]
```

## 4. 代码签名配置

### 4.1 Windows代码签名（Authenticode）

Windows平台需要使用代码签名证书（.pfx文件）对安装包签名，确保用户安装时不出现SmartScreen警告。

环境变量配置：

```bash
CSC_LINK=C:\certs\xuansto-code-signing.pfx
CSC_KEY_PASSWORD=<secure-password>
```

electron-builder自动检测环境变量并签名：

```yaml
win:
  signAndEditExecutable: true
  signingHashAlgorithms:
    - sha256
  certificateFile: null
  certificatePassword: null
  signDlls: true
```

Tauri Windows签名配置：

```json
{
  "bundle": {
    "windows": {
      "certificateThumbprint": "AB12CD34EF56...",
      "digestAlgorithm": "sha256",
      "timestampUrl": "http://timestamp.digicert.com",
      "tsp": false
    }
  }
}
```

PowerShell签名脚本（备用方案）：

```powershell
$cert = Get-ChildItem -Path Cert:\CurrentUser\My -CodeSigningCert | Where-Object { $_.Subject -match "Xuansto" }
$files = Get-ChildItem -Path ".\dist\*.exe", ".\dist\*.msi"
foreach ($file in $files) {
    Set-AuthenticodeSignature -FilePath $file.FullName -Certificate $cert -TimestampServer "http://timestamp.digicert.com" -HashAlgorithm SHA256
}
```

### 4.2 macOS代码签名（Developer ID + 公证）

macOS需要Apple Developer ID证书签名并通过Apple公证（Notarization），否则Gatekeeper会阻止用户打开应用。

环境变量配置：

```bash
APPLE_ID=developer@xuansto.dev
APPLE_APP_SPECIFIC_PASSWORD=<app-specific-password>
APPLE_TEAM_ID=ABC12DEF34
CSC_LINK=/path/to/developer-id.p12
CSC_KEY_PASSWORD=<secure-password>
```

Entitlements文件（build/entitlements.mac.plist）：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
</dict>
</plist>
```

Tauri macOS签名与公证：

```json
{
  "bundle": {
    "macOS": {
      "signingIdentity": "Developer ID Application: Xuansto Team (ABC12DEF34)",
      "providerShortName": "ABC12DEF34",
      "entitlements": "entitlements.plist",
      "minimumSystemVersion": "10.15"
    }
  }
}
```

公证命令（手动）：

```bash
xcrun notarytool submit dist/Xuansto-1.0.0.dmg \
  --apple-id "developer@xuansto.dev" \
  --password "$APPLE_APP_SPECIFIC_PASSWORD" \
  --team-id "ABC12DEF34" \
  --wait

xcrun stapler staple dist/Xuansto-1.0.0.dmg
```

## 5. 自动更新配置

### 5.1 Electron自动更新（electron-updater）

```typescript
import { autoUpdater } from "electron-updater";
import { BrowserWindow } from "electron";

autoUpdater.autoDownload = false;
autoUpdater.autoInstallOnAppQuit = true;
autoUpdater.channel = "latest";

autoUpdater.on("update-available", (info) => {
  mainWindow.webContents.send("auto:updateAvailable", {
    version: info.version,
    releaseNotes: info.releaseNotes,
  });
});

autoUpdater.on("download-progress", (progress) => {
  mainWindow.webContents.send("auto:downloadProgress", {
    percent: progress.percent,
    bytesPerSecond: progress.bytesPerSecond,
  });
});

autoUpdater.on("update-downloaded", () => {
  mainWindow.webContents.send("auto:updateDownloaded");
});

ipcMain.handle("auto:checkForUpdates", async () => {
  const result = await autoUpdater.checkForUpdates();
  return result?.updateInfo ?? null;
});

ipcMain.handle("auto:downloadUpdate", async () => {
  await autoUpdater.downloadUpdate();
});

ipcMain.handle("auto:installUpdate", () => {
  autoUpdater.quitAndInstall(false, true);
});
```

electron-builder.yml发布配置：

```yaml
publish:
  - provider: github
    owner: xuansto
    repo: xuansto-desktop
    releaseType: release
    vPrefixedTagName: true
  - provider: s3
    bucket: xuansto-releases
    region: us-east-1
    path: electron/${version}
```

### 5.2 Tauri自动更新

tauri.conf.json更新配置：

```json
{
  "plugins": {
    "updater": {
      "pubkey": "PUBLIC_KEY_CONTENT",
      "endpoints": [
        "https://releases.xuansto.dev/update/{{target}}/{{arch}}/{{current_version}}"
      ],
      "windows": {
        "installMode": "passive"
      }
    }
  }
}
```

Rust端更新逻辑：

```rust
use tauri::updater::UpdateBuilder;

#[tauri::command]
pub async fn check_for_updates(app: tauri::AppHandle) -> Result<Option<String>, String> {
    let update = UpdateBuilder::new(&app)
        .check()
        .await
        .map_err(|e| e.to_string())?;

    if update.is_update_available() {
        Ok(Some(update.latest_version().to_string()))
    } else {
        Ok(None)
    }
}

#[tauri::command]
pub async fn install_update(app: tauri::AppHandle) -> Result<(), String> {
    let update = UpdateBuilder::new(&app)
        .check()
        .await
        .map_err(|e| e.to_string())?;

    if update.is_update_available() {
        update.download_and_install(|chunk, content_len| {
            println!("Downloaded {} of {:?}", chunk, content_len);
        }, || {
            println!("Update installed, restarting...");
        }).await.map_err(|e| e.to_string())?;
    }
    Ok(())
}
```

生成更新签名密钥：

```bash
tauri signer generate -w ~/.tauri/xuansto.key
```

## 6. CI/CD集成

### 6.1 GitHub Actions多平台构建

```yaml
name: Build & Release

on:
  push:
    tags:
      - "v*"
  workflow_dispatch:

jobs:
  build:
    strategy:
      matrix:
        include:
          - os: windows-latest
            platform: win
            ext: exe
          - os: macos-latest
            platform: mac
            ext: dmg
          - os: ubuntu-latest
            platform: linux
            ext: AppImage

    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm

      - name: Setup Rust
        if: matrix.platform == 'linux'
        uses: dtolnay/rust-toolchain@stable

      - name: Install Linux dependencies
        if: matrix.platform == 'linux'
        run: |
          sudo apt-get update
          sudo apt-get install -y libwebkit2gtk-4.1-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev

      - name: Install dependencies
        run: npm ci

      - name: Build application
        run: npm run build

      - name: Package (Electron)
        if: env.FRAMEWORK == 'electron'
        run: npm run dist:${{ matrix.platform }}
        env:
          CSC_LINK: ${{ secrets.CSC_LINK }}
          CSC_KEY_PASSWORD: ${{ secrets.CSC_KEY_PASSWORD }}
          APPLE_ID: ${{ secrets.APPLE_ID }}
          APPLE_APP_SPECIFIC_PASSWORD: ${{ secrets.APPLE_APP_SPECIFIC_PASSWORD }}
          APPLE_TEAM_ID: ${{ secrets.APPLE_TEAM_ID }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Package (Tauri)
        if: env.FRAMEWORK == 'tauri'
        run: npm run tauri build
        env:
          TAURI_SIGNING_PRIVATE_KEY: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY }}
          APPLE_SIGNING_IDENTITY: ${{ secrets.APPLE_SIGNING_IDENTITY }}
          APPLE_ID: ${{ secrets.APPLE_ID }}
          APPLE_PASSWORD: ${{ secrets.APPLE_APP_SPECIFIC_PASSWORD }}
          APPLE_TEAM_ID: ${{ secrets.APPLE_TEAM_ID }}

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: xuansto-${{ matrix.platform }}
          path: |
            dist/*.exe
            dist/*.dmg
            dist/*.AppImage
            dist/*.deb
          retention-days: 30

  release:
    needs: build
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')

    steps:
      - name: Download all artifacts
        uses: actions/download-artifact@v4
        with:
          path: artifacts

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          files: artifacts/**/*
          generate_release_notes: true
          draft: false
          prerelease: ${{ contains(github.ref, '-rc') || contains(github.ref, '-beta') }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 6.2 构建环境变量清单

| 变量名                       | 用途                     | 平台     | 必要性 |
|-----------------------------|--------------------------|----------|--------|
| `CSC_LINK`                  | 代码签名证书路径          | Win/Mac  | 发布必须 |
| `CSC_KEY_PASSWORD`          | 证书密码                  | Win/Mac  | 发布必须 |
| `APPLE_ID`                  | Apple开发者账号           | Mac      | 公证必须 |
| `APPLE_APP_SPECIFIC_PASSWORD`| Apple应用专用密码         | Mac      | 公证必须 |
| `APPLE_TEAM_ID`             | Apple团队ID              | Mac      | 公证必须 |
| `GH_TOKEN`                  | GitHub Token             | 全平台   | 发布必须 |
| `TAURI_SIGNING_PRIVATE_KEY` | Tauri更新签名私钥         | 全平台   | 更新必须 |
| `NODE_OPTIONS`              | Node.js内存限制           | 全平台   | 可选    |

### 6.3 构建产物结构

```
dist/
├── Xuansto-1.0.0-x64.exe          # Windows NSIS安装包
├── Xuansto-1.0.0-x64.msi          # Windows MSI安装包
├── Xuansto-1.0.0-arm64.exe        # Windows ARM64
├── Xuansto-1.0.0-universal.dmg    # macOS通用二进制
├── Xuansto-1.0.0-universal-mac.zip # macOS ZIP
├── Xuansto-1.0.0-amd64.AppImage   # Linux AppImage
├── Xuansto-1.0.0-amd64.deb        # Linux DEB包
├── latest.yml                      # electron-updater元数据(Win)
├── latest-mac.yml                  # electron-updater元数据(Mac)
└── builder-effective-config.yaml   # 构建生效配置快照
```
