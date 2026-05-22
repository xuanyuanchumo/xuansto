---
name: /release-desktop
aliases:
  - rdesk
  - rdesk
category: workflow
phase: "8"
description: 桌面应用发布与更新管理
trigger: 需要发布桌面应用时
workflow: desktop-release-workflow
---

# /release-desktop 命令

## 命令用途

执行桌面应用发布与更新管理，通过DESKTOP-SIGN和DESKTOP-UPDATE质量门禁检查后启动发布工作流。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | quality_gate_check | gates=DESKTOP-SIGN,DESKTOP-UPDATE | 检查签名和更新质量门禁 |
| 2 | workflow_dispatch | action=start, workflow=desktop-release | 启动桌面发布工作流 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| quality_gate_check | 脚本调用 | python scripts/skill-test.py --gate [gate_id] |
| workflow_dispatch | 内联执行 | 内联阶段推进（发布流程） |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| desktop-builder | 主导 | 发布构建、签名、打包 |
| devops-engineer | 辅助 | 发布流程、更新服务 |
| security-auditor | 辅助 | 签名验证、安全检查 |

## 命令描述

执行桌面应用发布与更新管理，通过DESKTOP-SIGN和DESKTOP-UPDATE质量门禁检查后启动发布工作流。该命令管理从签名到发布的完整桌面应用发布流程。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/release-desktop` |
| 关键词触发 | 用户提及"桌面发布"、"发布桌面应用"、"release desktop" |
| 流程触发 | `/build-desktop` 完成后自动建议发布 |

## 命令名称与语法

```
/release-desktop [--channel=<通道>] [--auto-update] [--notes=<发布说明>]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--channel` | enum | 否 | stable | 发布通道：stable/beta/alpha/nightly |
| `--auto-update` | flag | 否 | true | 启用自动更新 |
| `--notes` | string | 否 | auto | 发布说明 |
| `--sign` | flag | 否 | true | 代码签名 |
| `--notarize` | flag | 否 | true | macOS公证 |
| `--delta` | flag | 否 | true | 生成增量更新包 |

## 执行流程

> 标准五步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证 → 5. 输出交付

1. **输入验证**：校验构建产物存在、签名配置完整
2. **Agent调度**：desktop-builder主导发布，security-auditor辅助签名验证
3. **任务执行**：执行代码签名→公证→发布包生成→更新清单→发布上传
4. **结果验证**：执行quality_gate_check(gates=DESKTOP-SIGN,DESKTOP-UPDATE)
5. **输出交付**：生成发布包、更新清单、发布说明

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| DESKTOP-SIGN | BLOCK | 代码签名有效、签名验证通过 |
| DESKTOP-UPDATE | BLOCK | 更新清单正确、增量更新可用、自动更新可工作 |

## 使用示例

### 示例1：稳定版发布

```
/release-desktop
```

### 示例2：Beta版发布

```
/release-desktop --channel=beta
```

### 示例3：带发布说明

```
/release-desktop --notes="修复了登录问题和性能优化"
```

### 示例4：仅签名

```
/release-desktop --sign --no-auto-update
```

## 相关脚本

- `scripts/skill-test.py` - 技能测试器，执行质量门禁检查

---

## 相关命令

- `/build-desktop` - 桌面应用构建
- `/deploy` - 部署交付
- `/rollback` - 发布回滚
- `/sprint` - 启动完整冲刺
