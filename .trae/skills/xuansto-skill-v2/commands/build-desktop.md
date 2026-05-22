---
name: /build-desktop
aliases:
  - bdesk
  - desktop
category: workflow
phase: "7"
description: 桌面应用构建与打包
trigger: 需要构建桌面应用时
workflow: desktop-build-workflow
---

# /build-desktop 命令

## 命令用途

执行桌面应用构建与打包，通过DESKTOP-BUILD和DESKTOP-CROSS质量门禁检查，确保桌面应用可正确构建和跨平台兼容。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | quality_gate_check | gates=DESKTOP-BUILD,DESKTOP-CROSS | 检查桌面构建和跨平台质量门禁 |
| 2 | skill_analyze | scope=desktop-build | 分析桌面构建技能需求 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| quality_gate_check | 脚本调用 | python scripts/skill-test.py --gate [gate_id] |
| skill_analyze | 脚本调用 | python scripts/skill-test.py --analyze |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| desktop-builder | 主导 | 桌面应用构建、打包、跨平台 |
| devops-engineer | 辅助 | CI/CD配置、构建环境 |
| fullstack-engineer | 辅助 | 构建问题修复 |

## 命令描述

执行桌面应用构建与打包，通过DESKTOP-BUILD和DESKTOP-CROSS质量门禁检查，确保桌面应用可正确构建和跨平台兼容。支持Electron、Tauri等桌面框架。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/build-desktop` |
| 关键词触发 | 用户提及"桌面构建"、"打包桌面应用"、"build desktop" |
| 自动触发 | 检测到桌面项目类型时 |
| 流程触发 | `/accept` 完成后自动建议构建 |

## 命令名称与语法

```
/build-desktop [--platform=<平台>] [--framework=<框架>] [--sign]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--platform` | enum | 否 | current | 目标平台：current/win/mac/linux/all |
| `--framework` | enum | 否 | auto | 桌面框架：auto/electron/tauri/flutter |
| `--sign` | flag | 否 | false | 代码签名 |
| `--notarize` | flag | 否 | false | 公证（macOS） |
| `--portable` | flag | 否 | false | 生成便携版 |
| `--installer` | flag | 否 | true | 生成安装包 |

## 执行流程

> 标准五步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证 → 5. 输出交付

1. **输入验证**：校验桌面项目配置存在、`--platform`参数合法
2. **Agent调度**：desktop-builder主导构建，devops-engineer辅助环境配置
3. **任务执行**：执行依赖安装→代码构建→平台打包→代码签名→安装包生成
4. **结果验证**：执行quality_gate_check(gates=DESKTOP-BUILD,DESKTOP-CROSS)
5. **输出交付**：生成安装包、便携版、构建报告

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| DESKTOP-BUILD | BLOCK | 桌面应用构建成功、无编译错误 |
| DESKTOP-CROSS | BLOCK | 跨平台兼容性检查通过、所有目标平台可构建 |

## 使用示例

### 示例1：构建当前平台

```
/build-desktop
```

### 示例2：构建所有平台

```
/build-desktop --platform=all
```

### 示例3：构建并签名

```
/build-desktop --platform=win --sign
```

### 示例4：指定框架

```
/build-desktop --framework=tauri
```

### 示例5：生成便携版

```
/build-desktop --portable --no-installer
```

## 相关脚本

- `scripts/skill-test.py` - 技能测试器，执行质量门禁检查

---

## 相关命令

- `/release-desktop` - 桌面应用发布
- `/build` - Web应用构建
- `/deploy` - 部署交付
- `/sprint` - 启动完整冲刺
