---
id: "KP-EXP-DSK-SIGN-001"
type: "error-solution"
severity: "high"
category: "code-signing"
tags:
  - "code-signing"
  - "windows-authenticode"
  - "macos-notarization"
  - "ev-certificate"
  - "smart-screen"
version: "1.0.0"
created: "2026-04-28"
confidence: 0.88
occurrences: 4
---

# 代码签名故障排除指南

## 错误现象

### 错误 1: Windows SmartScreen 警告

用户下载安装应用后，Windows SmartScreen 显示蓝色警告：

```
Windows 已保护你的电脑
Microsoft Defender SmartScreen 阻止了一个无法识别的应用启动
```

即使应用已使用代码签名证书签名，仍然出现此警告。用户必须点击"更多信息"→"仍要运行"才能安装。

### 错误 2: macOS Gatekeeper 阻止

用户在 macOS 上打开应用时，系统弹出警告：

```
"MyApp" 已损坏，无法打开。你应该将它移到废纸篓。
```

或：

```
无法打开"MyApp"，因为无法验证开发者。
```

在系统偏好设置 → 安全性与隐私中也无法找到"仍要打开"选项。

### 错误 3: 证书过期或签名失败

构建过程中签名步骤失败：

```
Error: Sign failed:
  The specified PFX file is not valid.
  SignTool Error: No certificates were found that met all the given criteria.
```

或 macOS 上：

```
Error: Notarization failed:
  The software is not notarized.
  The signature of the binary is invalid.
```

证书过期后，所有构建流水线中断，无法发布新版本。

## 根因分析

### SmartScreen 警告根因

1. **证书信誉不足**：SmartScreen 不仅验证签名有效性，还基于证书的"信誉"进行判断。新证书或新应用首次发布时，SmartScreen 数据库中没有该应用的信誉记录，即使签名有效也会触发警告
2. **OV 证书限制**：组织验证（OV）代码签名证书需要积累下载量才能建立信誉。EV（扩展验证）代码签名证书可立即获得 SmartScreen 信誉
3. **签名时间戳问题**：如果签名未包含时间戳，证书过期后签名即失效，SmartScreen 会将其视为未签名应用
4. **SHA-1 弃用**：Windows 10+ 不再信任 SHA-1 签名，仅接受 SHA-256 签名

### Gatekeeper 阻止根因

1. **未公证（Notarization）**：macOS 10.15+ 要求所有分发的应用必须经过 Apple 公证。未公证的应用会被 Gatekeeper 阻止
2. **Hardened Runtime 缺失**：公证要求应用启用 Hardened Runtime，未启用则公证失败
3. **签名不完整**：应用包内的动态库（.dylib）、框架（.framework）未单独签名
4. ** entitlements 配置错误**：应用使用的权限（如网络访问、文件读取）未在 entitlements 中声明

### 证书过期根因

1. **证书有效期**：代码签名证书通常有效期为 1-3 年，到期后无法用于新签名
2. **自动续签失败**：CI/CD 中存储的证书未及时更新，导致构建使用过期证书
3. **中间证书缺失**：签名时未包含完整的证书链，导致验证时无法建立信任链
4. **密钥访问权限**：macOS Keychain 中签名密钥的访问控制设置阻止了 CI 环境的无交互签名

## 解决方案

### SmartScreen 警告修复

**方案 1: 使用 EV 代码签名证书**

EV 证书通过硬件令牌（USB Key）存储私钥，SmartScreen 立即信任 EV 签名的应用。

```json
{
  "build": {
    "win": {
      "sign": true,
      "signingHashAlgorithms": ["sha256"],
      "certificateFile": "path/to/certificate.pfx",
      "certificatePassword": "${WINDOWS_CERT_PASSWORD}",
      "signingHashAlgorithms": ["sha256"],
      "rfc3161TimeStampServer": "http://timestamp.digicert.com",
      "timeStampServer": "http://timestamp.digicert.com"
    }
  }
}
```

**方案 2: 为 OV 证书积累信誉**

```json
{
  "build": {
    "win": {
      "sign": true,
      "signingHashAlgorithms": ["sha256"],
      "certificateFile": "certs/code-signing.pfx",
      "certificatePassword": "${CERT_PASSWORD}",
      "rfc3161TimeStampServer": "http://timestamp.digicert.com"
    },
    "publish": {
      "provider": "github",
      "releaseType": "release"
    }
  }
}
```

通过 GitHub Releases 等正规渠道分发，让用户逐步下载建立信誉。通常需要数千次下载后 SmartScreen 警告才会消失。

**方案 3: 使用 signtool 手动签名（EV 硬件令牌）**

```powershell
$signtool = "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"
$cert = "E:\ev-cert-token"
$timestamp = "http://timestamp.digicert.com"
$file = "dist/MyApp-Setup-1.0.0.exe"

& $signtool sign /fd SHA256 /td SHA256 /tr $timestamp /a /debug $file
```

**方案 4: 提交 Microsoft SmartScreen 信誉申请**

通过 Microsoft 开发者支持提交信誉申请，加速 SmartScreen 白名单过程。

### Gatekeeper 阻止修复

**方案 1: 完整公证流程（electron-builder）**

```json
{
  "build": {
    "mac": {
      "hardenedRuntime": true,
      "gatekeeperAssess": false,
      "entitlements": "build/entitlements.mac.plist",
      "entitlementsInherit": "build/entitlements.mac.plist",
      "sign": true
    },
    "afterSign": "scripts/notarize.js",
    "dmg": {
      "sign": true
    }
  }
}
```

entitlements.mac.plist:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>com.apple.security.cs.allow-jit</key>
  <true/>
  <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
  <true/>
  <key>com.apple.security.cs.allow-dyld-environment-variables</key>
  <true/>
  <key>com.apple.security.cs.disable-library-validation</key>
  <true/>
  <key>com.apple.security.network.client</key>
  <true/>
  <key>com.apple.security.network.server</key>
  <true/>
  <key>com.apple.security.files.user-selected.read-write</key>
  <true/>
</dict>
</plist>
```

**方案 2: 公证脚本**

```javascript
const { notarize } = require('@electron/notarize');
const path = require('path');

async function notarizeApp(context) {
  const { electronPlatformName, appOutDir } = context;

  if (electronPlatformName !== 'darwin') {
    return;
  }

  const appName = context.packager.appInfo.productFilename;
  const appPath = path.join(appOutDir, `${appName}.app`);

  const appleId = process.env.APPLE_ID;
  const appleIdPassword = process.env.APPLE_ID_PASSWORD;
  const teamId = process.env.APPLE_TEAM_ID;

  if (!appleId || !appleIdPassword || !teamId) {
    console.warn('Skipping notarization: missing Apple credentials');
    return;
  }

  await notarize({
    appPath,
    appleId,
    appleIdPassword,
    teamId
  });

  console.log('Notarization completed successfully');
}

exports.default = notarizeApp;
```

**方案 3: Tauri 应用签名与公证**

```json
{
  "bundle": {
    "macOS": {
      "signingIdentity": "Developer ID Application: Your Name (TEAMID)",
      "entitlements": "entitlements.plist",
      "providerShortName": "TEAMID"
    }
  }
}
```

Tauri 公证命令：

```bash
export APPLE_ID="your@email.com"
export APPLE_PASSWORD="app-specific-password"
export APPLE_TEAM_ID="TEAMID"

cargo tauri build --target universal-apple-darwin
xcrun notarytool submit "target/universal-apple-darwin/release/bundle/macos/MyApp.app.tar.gz" \
  --apple-id "$APPLE_ID" \
  --password "$APPLE_PASSWORD" \
  --team-id "$APPLE_TEAM_ID" \
  --wait

xcrun stapler staple "target/universal-apple-darwin/release/bundle/macos/MyApp.app"
```

**方案 4: 修复"已损坏"错误**

如果用户已下载未公证的应用，可通过终端命令移除隔离属性：

```bash
xattr -cr /Applications/MyApp.app
```

但这不是正式解决方案，仅作为临时应急手段。

### 证书过期修复

**方案 1: 证书到期监控与自动续签**

```javascript
const { execSync } = require('child_process');
const fs = require('fs');

function checkCertificateExpiry(certPath, warnDays = 30) {
  const platform = process.platform;

  if (platform === 'win32') {
    const output = execSync(
      `certutil -verify "${certPath}" 2>&1 | findstr /i "NotAfter"`,
      { encoding: 'utf-8' }
    );
    const match = output.match(/NotAfter\s*:\s*(.+)/);
    if (match) {
      const expiryDate = new Date(match[1]);
      const daysLeft = Math.ceil((expiryDate - Date.now()) / (1000 * 60 * 60 * 24));
      if (daysLeft <= warnDays) {
        console.error(`Certificate expires in ${daysLeft} days!`);
        process.exit(1);
      }
      console.log(`Certificate valid for ${daysLeft} more days`);
    }
  } else if (platform === 'darwin') {
    const output = execSync(
      `security find-certificate -c "Developer ID" -p /Library/Keychains/System.keychain | openssl x509 -noout -enddate`,
      { encoding: 'utf-8' }
    );
    const match = output.match(/notAfter=(.+)/);
    if (match) {
      const expiryDate = new Date(match[1]);
      const daysLeft = Math.ceil((expiryDate - Date.now()) / (1000 * 60 * 60 * 24));
      if (daysLeft <= warnDays) {
        console.error(`Certificate expires in ${daysLeft} days!`);
        process.exit(1);
      }
      console.log(`Certificate valid for ${daysLeft} more days`);
    }
  }
}

checkCertificateExpiry(process.argv[2]);
```

**方案 2: CI/CD 中安全存储和轮换证书**

GitHub Actions 示例：

```yaml
jobs:
  build:
    strategy:
      matrix:
        include:
          - os: windows-latest
            platform: win
          - os: macos-latest
            platform: mac
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4

      - name: Install Apple certificates
        if: matrix.platform == 'mac'
        run: |
          security create-keychain -p actions temp.keychain
          security unlock-keychain -p actions temp.keychain
          echo "${{ secrets.MAC_CERT_BASE64 }}" | base64 -d | security import /dev/stdin \
            -k temp.keychain \
            -P "${{ secrets.MAC_CERT_PASSWORD }}" \
            -T /usr/bin/codesign
          security set-key-partition-list -S apple-tool:,apple: -s -k actions temp.keychain
          security list-keychains -d user -s temp.keychain

      - name: Install Windows certificate
        if: matrix.platform == 'win'
        run: |
          $certBytes = [Convert]::FromBase64String("${{ secrets.WIN_CERT_BASE64 }}")
          $certPath = Join-Path $env:TEMP "code-signing.pfx"
          [IO.File]::WriteAllBytes($certPath, $certBytes)
          echo "WIN_CERT_PATH=$certPath" >> $env:GITHUB_ENV

      - name: Build and sign
        run: npm run build
        env:
          CSC_LINK: ${{ secrets.WIN_CERT_BASE64 }}
          CSC_KEY_PASSWORD: ${{ secrets.WIN_CERT_PASSWORD }}
          APPLE_ID: ${{ secrets.APPLE_ID }}
          APPLE_ID_PASSWORD: ${{ secrets.APPLE_ID_PASSWORD }}
          APPLE_TEAM_ID: ${{ secrets.APPLE_TEAM_ID }}

      - name: Cleanup certificates
        if: always()
        run: |
          if ($env:RUNNER_OS -eq "Windows") {
            Remove-Item -Force $env:WIN_CERT_PATH -ErrorAction SilentlyContinue
          } elseif ($env:RUNNER_OS -eq "macOS") {
            security delete-keychain temp.keychain 2>$null
          }
```

**方案 3: 时间戳服务器确保签名持久有效**

```json
{
  "build": {
    "win": {
      "rfc3161TimeStampServer": "http://timestamp.digicert.com",
      "timeStampServer": "http://timestamp.digicert.com"
    }
  }
}
```

多个时间戳服务器备选：

```json
{
  "build": {
    "win": {
      "rfc3161TimeStampServer": "http://timestamp.digicert.com",
      "timeStampServer": "http://timestamp.digicert.com"
    }
  }
}
```

常用时间戳服务器：
- DigiCert: `http://timestamp.digicert.com`
- Sectigo: `http://timestamp.sectigo.com`
- GlobalSign: `http://timestamp.globalsign.com`

**方案 4: macOS Keychain 无交互签名配置**

```bash
security unlock-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
```

在 CI 中创建专用 Keychain 避免弹窗：

```bash
KEYCHAIN_PATH="$RUNNER_TEMP/signing.keychain-db"
security create-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
security set-keychain-settings -lut 21600 "$KEYCHAIN_PATH"
security unlock-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"

echo "$MAC_CERT_BASE64" | base64 -d | security import /dev/stdin \
  -k "$KEYCHAIN_PATH" \
  -P "$MAC_CERT_PASSWORD" \
  -T /usr/bin/codesign \
  -T /usr/bin/productsign

security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
security list-keychains -d user -s "$KEYCHAIN_PATH"
```

## 预防措施

1. **EV 证书优先**：新项目优先采购 EV 代码签名证书，避免 SmartScreen 信誉积累期
2. **双平台签名自动化**：CI/CD 中集成完整签名和公证流程，确保每次构建产物均有效签名
3. **证书到期告警**：在 CI 流水线中添加证书有效期检查步骤，到期前 30 天发送告警

```yaml
- name: Check certificate expiry
  run: node scripts/check-cert-expiry.js
```

4. **时间戳必选**：所有签名操作必须包含 RFC 3161 时间戳，确保证书过期后签名仍有效
5. **公证验证脚本**：构建后自动验证签名和公证状态

```javascript
const { execSync } = require('child_process');
const platform = process.platform;

if (platform === 'darwin') {
  const appPath = process.argv[2];
  const signResult = execSync(`codesign --verify --deep --strict "${appPath}" 2>&1`, { encoding: 'utf-8' });
  console.log('Signature valid:', signResult || 'OK');

  const stapleResult = execSync(`xcrun stapler validate "${appPath}" 2>&1`, { encoding: 'utf-8' });
  console.log('Staple valid:', stapleResult);
} else if (platform === 'win32') {
  const exePath = process.argv[2];
  const result = execSync(`signtool verify /pa /all "${exePath}" 2>&1`, { encoding: 'utf-8' });
  console.log('Signature valid:', result);
}
```

6. **密钥安全存储**：证书私钥存储在 HSM 或云密钥管理服务中，禁止存储在代码仓库或 CI 明文变量中
7. **Apple App-Specific Password**：公证使用的 Apple ID 密码使用 App-Specific Password，而非主账户密码，并定期轮换

## 相关知识

- [Apple 公证要求文档](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [Windows Authenticode 签名](https://learn.microsoft.com/en-us/windows-hardware/drivers/install/authenticode)
- [Microsoft SmartScreen 信誉](https://learn.microsoft.com/en-us/windows/security/threat-protection/microsoft-defender-smartscreen/microsoft-defender-smartscreen-overview)
- [electron-builder 代码签名配置](https://www.electron.build/code-signing)
- [Tauri 签名与公证](https://tauri.app/v1/guides/distribution/sign-macos/)
- [DigiCert 代码签名证书](https://www.digicert.com/signing/code-signing-certificates)
- [Sectigo 代码签名证书](https://sectigo.com/ssl-certificates-tls/code-signing)
