---
name: /release-desktop
aliases:
  - rd
category: system
description: 桌面应用发布与签名
trigger: 需要发布桌面应用或进行代码签名时
---

# /release-desktop 命令

## 命令描述

`/release-desktop` 命令用于桌面应用的发布管理，覆盖从构建产物验证到分发上线的完整发布流程。该命令支持多渠道发布（stable/beta/alpha）、自动更新配置、代码公证与商店提交，确保桌面应用安全、可控地触达终端用户。

---

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/release-desktop` |
| 关键词触发 | 用户提及"桌面发布"、"发布桌面应用"、"桌面应用上线" |
| 自动触发 | `/build-desktop` 构建成功后自动建议发布 |
| 流程触发 | 版本发布计划触发 |

---

## 命令名称与语法

```
/release-desktop [platform] [options]
```

---

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| platform | string | 否 | all | 目标平台：win、macos、linux、all |
| --version | string | 否 | package.json | 发布版本号（遵循 SemVer） |
| --channel | string | 否 | stable | 发布渠道：stable、beta、alpha |
| --auto-update | boolean | 否 | true | 配置自动更新 |
| --notarize | boolean | 否 | true | macOS 公证（仅 macOS 有效） |
| --store-submit | boolean | 否 | false | 提交到应用商店（Mac App Store / Microsoft Store） |

---

## 执行流程

> 标准四步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证

```
┌─────────────────────────────────────────────────────────────┐
│               /release-desktop 执行流程                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 发布检查                                                 │
│     ├── 验证版本号合规性                                     │
│     ├── 检查 CHANGELOG 更新                                  │
│     ├── 验证构建产物存在且完整                               │
│     ├── 确认发布渠道配置                                     │
│     ├── 检查签名证书有效期                                   │
│     └── 生成发布计划                                         │
│                                                             │
│  2. 构建产物                                                 │
│     ├── 触发 /build-desktop 构建流程                         │
│     ├── 收集各平台构建产物                                   │
│     ├── 产物完整性校验                                       │
│     └── 产物哈希记录                                         │
│                                                             │
│  3. 代码签名与公证                                           │
│     ├── Windows: Authenticode 签名                           │
│     ├── macOS: Developer ID 签名                             │
│     ├── macOS: Apple 公证（notarization）                    │
│     ├── Linux: GPG 签名                                     │
│     └── 签名与公证结果验证                                   │
│                                                             │
│  4. 自动更新配置                                             │
│     ├── 生成更新清单（latest.yml / .json）                   │
│     ├── 填充版本号与下载地址                                 │
│     ├── 计算 delta 更新差异（如支持）                        │
│     ├── 配置回滚版本信息                                     │
│     └── 更新清单签名                                         │
│                                                             │
│  5. 上传分发                                                 │
│     ├── 上传到 CDN/OSS 分发节点                              │
│     ├── 上传到 GitHub Releases（如适用）                     │
│     ├── 提交到应用商店（--store-submit）                     │
│     │   ├── Microsoft Store 提交                            │
│     │   └── Mac App Store 提交                              │
│     ├── 更新分发清单                                         │
│     └── 验证下载可用性                                       │
│                                                             │
│  6. 验证更新流程                                             │
│     ├── 模拟旧版本检测更新                                   │
│     ├── 验证增量/全量更新                                    │
│     ├── 验证回滚机制                                         │
│     ├── 检查更新通知推送                                     │
│     └── 更新流程端到端验证                                   │
│                                                             │
│  7. 生成发布文档                                             │
│     ├── 生成 Release Notes                                  │
│     ├── 更新 CHANGELOG                                      │
│     ├── 生成升级指南                                         │
│     ├── 生成已知问题清单                                     │
│     └── 发布通知与公告                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| build-release-engineer | 主导 | 发布流程编排与执行 |
| cicd-specialist | 辅助 | CI/CD流水线与分发 |
| security-auditor | 辅助 | 签名公证与安全验证 |
| documentation-engineer | 辅助 | 发布文档生成 |

---

## 输出格式

### 1. 发布报告 (release-report.md)

```markdown
# 桌面应用发布报告

## 发布概要
- 发布时间: 2026-04-28 14:00:00
- 发布版本: v2.1.0
- 发布渠道: stable
- 目标平台: win, macos, linux
- 发布状态: ✅ 成功

## 签名与公证
| 平台 | 签名类型 | 签名状态 | 公证状态 |
|------|----------|----------|----------|
| Windows | Authenticode | ✅ 已签名 | - |
| macOS | Developer ID | ✅ 已签名 | ✅ 已公证 |
| Linux | GPG | ✅ 已签名 | - |

## 分发状态
| 目标 | 状态 | URL |
|------|------|-----|
| CDN | ✅ 已上传 | https://releases.example.com/v2.1.0/ |
| GitHub Releases | ✅ 已发布 | https://github.com/org/app/releases/tag/v2.1.0 |
| Microsoft Store | ⏳ 审核中 | - |
| Mac App Store | ⏳ 审核中 | - |

## 自动更新验证
- 更新检测: ✅ 正常
- 全量更新: ✅ 验证通过
- 增量更新: ✅ 验证通过
- 回滚机制: ✅ 验证通过

## 发布时间线
- 14:00:00 - 开始发布检查
- 14:02:00 - 构建产物验证完成
- 14:05:00 - 代码签名与公证完成
- 14:08:00 - 自动更新配置完成
- 14:12:00 - 分发上传完成
- 14:15:00 - 更新流程验证通过
- 14:18:00 - 发布文档生成完成
```

### 2. 发布清单 (release-manifest.json)

```json
{
  "release_id": "RELEASE-20260428-001",
  "version": "2.1.0",
  "channel": "stable",
  "release_date": "2026-04-28T14:00:00Z",
  "previous_version": "2.0.0",
  "platforms": {
    "win": {
      "artifact": "app-setup-2.1.0.exe",
      "sha256": "a1b2c3d4e5f6...",
      "signed": true,
      "distribution": {
        "cdn": "https://releases.example.com/v2.1.0/win/app-setup-2.1.0.exe",
        "github": "https://github.com/org/app/releases/download/v2.1.0/app-setup-2.1.0.exe"
      }
    },
    "macos": {
      "artifact": "app-2.1.0.dmg",
      "sha256": "d4e5f6g7h8i9...",
      "signed": true,
      "notarized": true,
      "distribution": {
        "cdn": "https://releases.example.com/v2.1.0/macos/app-2.1.0.dmg",
        "github": "https://github.com/org/app/releases/download/v2.1.0/app-2.1.0.dmg"
      }
    },
    "linux": {
      "artifact": "app-2.1.0.AppImage",
      "sha256": "g7h8i9j0k1l2...",
      "signed": true,
      "distribution": {
        "cdn": "https://releases.example.com/v2.1.0/linux/app-2.1.0.AppImage",
        "github": "https://github.com/org/app/releases/download/v2.1.0/app-2.1.0.AppImage"
      }
    }
  },
  "auto_update": {
    "enabled": true,
    "rollback_version": "2.0.0"
  }
}
```

### 3. Release Notes (release-notes-v2.1.0.md)

```markdown
# Release v2.1.0

## 新功能
- 原生文件系统访问增强
- 系统托盘交互优化
- 离线模式支持

## 改进
- 启动速度提升 40%
- 内存占用降低 25%
- 自动更新稳定性提升

## 修复
- 修复 Windows 下任务栏图标闪烁问题
- 修复 macOS 下菜单栏渲染异常
- 修复 Linux 下系统通知不显示问题

## 升级说明
- 支持从 v2.0.x 自动更新
- 首次安装请下载对应平台安装包
- macOS 用户需重新授权辅助功能权限

## 已知问题
- Windows 7 不支持硬件加速渲染
- Linux Wayland 下部分快捷键不可用
```

---

## 示例用法

### 示例1: 标准稳定版发布

```bash
/release-desktop all
```

发布全平台稳定版，包含签名、公证、自动更新配置和 CDN 分发。

### 示例2: 指定版本与渠道

```bash
/release-desktop all --version=2.1.0 --channel=beta
```

发布 v2.1.0 beta 版本到全平台。

### 示例3: 单平台发布

```bash
/release-desktop macos --notarize
```

仅发布 macOS 版本，执行 Apple 公证流程。

### 示例4: 应用商店提交

```bash
/release-desktop all --store-submit
```

发布并提交到 Microsoft Store 和 Mac App Store。

### 示例5: Alpha 内测发布

```bash
/release-desktop win --channel=alpha --auto-update=false
```

发布 Windows alpha 内测版，不配置自动更新。

---

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| DESKTOP-BUILD | BLOCK | 构建产物完整、哈希校验通过 |
| DESKTOP-SIGN | BLOCK | 签名有效、macOS公证通过 |
| DESKTOP-UPDATE | BLOCK | 自动更新检测正常、增量/全量更新验证通过、回滚机制正常 |
| DESKTOP-CROSS | WARN | 全平台构建产物可用、分发下载验证通过 |
---

## 注意事项

1. **版本号规范**: 严格遵循 SemVer 语义化版本，避免覆盖已发布版本
2. **渠道隔离**: stable/beta/alpha 渠道的更新清单必须独立维护，避免渠道混淆
3. **公证时效**: macOS 公证结果有有效期，发布后应尽快完成分发
4. **回滚预案**: 发布前确认回滚版本可用，自动更新回滚机制正常
5. **商店审核**: 应用商店提审需预留审核时间，Microsoft Store 通常 1-3 天，Mac App Store 1-2 天
6. **CDN 缓存**: 更新清单更新后需刷新 CDN 缓存，确保用户及时获取更新

---

## 相关命令

- `/build-desktop` - 桌面应用构建
- `/deploy` - Web 应用部署
- `/accept` - 发布前验收确认
- `/learn` - 发布经验沉淀
