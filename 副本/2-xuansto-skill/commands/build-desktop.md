---
name: /build-desktop
aliases:
  - bd
category: system
description: 桌面应用构建
trigger: 需要构建桌面应用安装包时
---

# /build-desktop 命令

## 命令描述

`/build-desktop` 命令用于桌面应用的构建管理，支持 Electron、Tauri、Flutter 等主流桌面框架的多平台构建。该命令管理从预构建检查到产物验证的完整构建流程，确保生成高质量、可分发、已签名的桌面安装包。

---

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/build-desktop` |
| 关键词触发 | 用户提及"桌面构建"、"构建安装包"、"桌面打包" |
| 自动触发 | `/release-desktop` 发布流程自动触发构建 |
| 流程触发 | CI/CD流水线构建阶段自动调用 |

---

## 命令名称与语法

```
/build-desktop [platform] [options]
```

---

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| platform | string | 否 | 当前系统 | 目标平台：win、macos、linux、all |
| --framework | string | 否 | auto-detect | 桌面框架：electron、tauri、flutter |
| --sign | boolean | 否 | true | 是否进行代码签名 |
| --skip-tests | boolean | 否 | false | 跳过构建前测试 |
| --config | string | 否 | ./build.config.json | 构建配置文件路径 |

---

## 执行流程

> 标准四步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证

```
┌─────────────────────────────────────────────────────────────┐
│                /build-desktop 执行流程                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 预构建检查                                               │
│     ├── 检测桌面框架类型                                     │
│     ├── 验证构建环境依赖                                     │
│     ├── 检查平台工具链                                       │
│     │   ├── Win: NSIS/WiX, signtool                        │
│     │   ├── Mac: Xcode, codesign, notarytool               │
│     │   └── Linux: dpkg-deb, rpmbuild, AppImage            │
│     ├── 验证签名证书可用性                                   │
│     └── 生成构建计划                                         │
│                                                             │
│  2. 依赖安装                                                 │
│     ├── 安装 Node.js/Rust/Dart 依赖                         │
│     ├── 检查原生依赖兼容性                                   │
│     ├── 锁定依赖版本                                        │
│     └── 依赖完整性校验                                       │
│                                                             │
│  3. 构建主进程                                               │
│     ├── 编译主进程代码                                       │
│     ├── 原生模块编译（如需要）                                │
│     ├── 主进程代码优化                                       │
│     └── 主进程产物输出                                       │
│                                                             │
│  4. 构建渲染进程                                             │
│     ├── 编译前端资源                                         │
│     ├── 资源压缩与优化                                       │
│     ├── 静态资源打包                                         │
│     └── 渲染进程产物输出                                     │
│                                                             │
│  5. 打包安装程序                                             │
│     ├── 平台打包                                            │
│     │   ├── Win: NSIS/WiX 安装包                            │
│     │   ├── Mac: DMG/PKG 安装包                             │
│     │   └── Linux: AppImage/deb/rpm 包                     │
│     ├── 内嵌自动更新元数据                                   │
│     ├── 生成更新清单文件                                     │
│     └── 计算安装包哈希                                       │
│                                                             │
│  6. 代码签名                                                 │
│     ├── Windows: Authenticode 签名                          │
│     ├── macOS: Developer ID 签名 + 公证                     │
│     ├── Linux: GPG 签名                                     │
│     └── 签名验证                                            │
│                                                             │
│  7. 构建验证                                                 │
│     ├── 安装包完整性校验                                     │
│     ├── 签名有效性验证                                       │
│     ├── 基础功能冒烟测试                                     │
│     ├── 安装/卸载流程测试                                    │
│     └── 生成构建报告                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| build-release-engineer | 主导 | 构建流程编排与执行 |
| desktop-developer | 辅助 | 桌面框架配置与原生模块 |
| cicd-specialist | 辅助 | CI/CD流水线集成 |
| security-auditor | 辅助 | 签名验证与安全检查 |

---

## 输出格式

### 1. 构建报告 (build-report.md)

```markdown
# 桌面应用构建报告

## 构建概要
- 构建时间: 2026-04-28 10:00:00
- 目标平台: win, macos, linux
- 桌面框架: electron
- 构建版本: v2.1.0
- 构建状态: ✅ 成功

## 构建产物
| 平台 | 文件名 | 大小 | 哈希(SHA256) | 签名状态 |
|------|--------|------|-------------|----------|
| Windows | app-setup-2.1.0.exe | 85.3 MB | a1b2c3... | ✅ 已签名 |
| macOS | app-2.1.0.dmg | 92.1 MB | d4e5f6... | ✅ 已签名+公证 |
| Linux | app-2.1.0.AppImage | 78.6 MB | g7h8i9... | ✅ GPG签名 |

## 构建时间线
- 10:00:00 - 开始预构建检查
- 10:01:30 - 依赖安装完成
- 10:05:00 - 主进程构建完成
- 10:08:00 - 渲染进程构建完成
- 10:12:00 - 安装包打包完成
- 10:15:00 - 代码签名完成
- 10:18:00 - 构建验证通过

## 验证结果
- 安装包完整性: ✅ 通过
- 签名有效性: ✅ 通过
- 冒烟测试: ✅ 通过 (8/8)
- 安装/卸载: ✅ 通过
```

### 2. 构建清单 (build-manifest.json)

```json
{
  "build_id": "BUILD-20260428-001",
  "version": "v2.1.0",
  "framework": "electron",
  "platforms": [
    {
      "name": "win",
      "arch": "x64",
      "installer": "app-setup-2.1.0.exe",
      "size_bytes": 89436569,
      "sha256": "a1b2c3d4e5f6...",
      "signed": true,
      "format": "nsis"
    },
    {
      "name": "macos",
      "arch": "universal",
      "installer": "app-2.1.0.dmg",
      "size_bytes": 96542763,
      "sha256": "d4e5f6g7h8i9...",
      "signed": true,
      "notarized": true,
      "format": "dmg"
    },
    {
      "name": "linux",
      "arch": "x64",
      "installer": "app-2.1.0.AppImage",
      "size_bytes": 82345984,
      "sha256": "g7h8i9j0k1l2...",
      "signed": true,
      "format": "appimage"
    }
  ],
  "build_config": "./build.config.json"
}
```

### 3. 更新清单 (update-manifest.json)

```json
{
  "version": "2.1.0",
  "releaseDate": "2026-04-28",
  "platforms": {
    "win": {
      "url": "https://releases.example.com/win/app-setup-2.1.0.exe",
      "sha256": "a1b2c3d4e5f6...",
      "size": 89436569
    },
    "macos": {
      "url": "https://releases.example.com/macos/app-2.1.0.dmg",
      "sha256": "d4e5f6g7h8i9...",
      "size": 96542763
    },
    "linux": {
      "url": "https://releases.example.com/linux/app-2.1.0.AppImage",
      "sha256": "g7h8i9j0k1l2...",
      "size": 82345984
    }
  }
}
```

---

## 示例用法

### 示例1: 构建当前平台

```bash
/build-desktop
```

自动检测当前系统平台和框架，构建当前平台的安装包。

### 示例2: 构建 Windows 安装包

```bash
/build-desktop win
```

构建 Windows 平台的安装包，使用默认 NSIS 格式。

### 示例3: 构建全平台安装包

```bash
/build-desktop all --framework=tauri
```

使用 Tauri 框架构建全平台（Win/Mac/Linux）安装包。

### 示例4: 跳过测试构建

```bash
/build-desktop win --skip-tests
```

构建 Windows 安装包，跳过构建前测试（紧急构建场景）。

### 示例5: 使用自定义构建配置

```bash
/build-desktop all --config=./ci/build.config.json
```

使用指定的构建配置文件构建全平台安装包。

### 示例6: 无签名构建（开发调试）

```bash
/build-desktop linux --sign=false
```

构建 Linux 安装包，跳过代码签名（仅用于开发调试）。

---

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| DESKTOP-BUILD | BLOCK | 安装包完整性校验通过、冒烟测试通过、安装/卸载流程正常 |
| DESKTOP-SIGN | BLOCK | 代码签名有效、签名验证通过 |
| IPC-CONTRACT | BLOCK | IPC接口契约定义完整、主进程与渲染进程通信验证通过 |
---

## 注意事项

1. **平台工具链**: Windows 构建需要 Visual Studio Build Tools；macOS 构建需要 Xcode Command Line Tools；Linux 构建需要对应的打包工具
2. **签名证书**: 生产构建必须启用代码签名，确保签名证书和密钥安全存储
3. **macOS 公证**: macOS 应用分发需通过 Apple 公证，确保使用有效的 Developer ID 证书
4. **跨平台构建**: 部分平台不支持交叉编译，建议使用对应平台的 CI Runner
5. **原生依赖**: 涉及原生模块时需确保各平台编译工具链完整
6. **构建缓存**: 合理利用构建缓存加速重复构建，但需注意缓存失效策略

---

## 相关命令

- `/release-desktop` - 桌面应用发布
- `/build` - Web 应用构建
- `/deploy` - 部署管理
- `/agent-status` - 查看构建Agent状态
