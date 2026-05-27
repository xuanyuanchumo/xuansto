---
id: ws-desktop-signing-setup
type: desktop
project: [待填写]
version: 0.1.0
---

# 签名配置指南

## 概述

[待填写：项目代码签名与公证的配置说明]

## 证书类型

| 平台 | 证书类型 | 颁发机构 | 有效期 | 用途 |
|------|---------|---------|--------|------|
| Windows | 代码签名证书 (EV/OV) | [待填写] | [待填写] | [待填写] |
| macOS | Developer ID Certificate | Apple | [待填写] | [待填写] |
| macOS | Apple Distribution Certificate | Apple | [待填写] | [待填写] |

## 配置步骤

### Windows 签名

| 步骤 | 操作 | 命令/说明 |
|------|------|----------|
| 1 | 安装证书 | [待填写] |
| 2 | 配置签名工具 | [待填写] |
| 3 | 执行签名 | [待填写] |

### macOS 签名与公证

| 步骤 | 操作 | 命令/说明 |
|------|------|----------|
| 1 | 导入证书到钥匙串 | [待填写] |
| 2 | 应用签名 | `codesign --sign "Developer ID Application: [待填写]" [待填写]` |
| 3 | 提交公证 | `xcrun notarytool submit [待填写]` |
| 4 | 装订公证票据 | `xcrun stapler staple [待填写]` |

## 环境变量配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| [待填写]_CERT_PASSWORD | 证书密码 | [待填写] |
| [待填写]_APPLE_ID | Apple 开发者账号 | [待填写] |
| [待填写]_APPLE_PASSWORD | App-specific password | [待填写] |

## 验证方法

| 平台 | 验证命令 | 预期输出 |
|------|---------|---------|
| Windows | `signtool verify /pa [待填写]` | [待填写] |
| macOS | `codesign --verify --deep --strict [待填写]` | [待填写] |
| macOS | `spctl --assess --type execute [待填写]` | [待填写] |

## 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| [待填写] | [待填写] | [待填写] |

## 变更记录

| 日期 | 变更内容 | 变更人 |
|------|---------|--------|
| [待填写] | [待填写] | [待填写] |
