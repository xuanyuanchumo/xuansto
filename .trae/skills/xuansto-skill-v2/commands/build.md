---
name: /build
aliases:
  - b
category: workflow
phase: "7"
description: 项目构建与编译
trigger: 需要构建或编译项目时
workflow: sdd-tdd-full
---

# /build 命令

## 命令用途

执行项目构建与编译，通过技能分析和质量门禁检查，确保项目可正确构建并满足质量标准。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | skill_analyze | scope=build | 分析构建技能需求和环境配置 |
| 2 | quality_gate_check | phase=7 | 检查构建阶段质量门禁 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| skill_analyze | 脚本调用 | python scripts/skill-test.py --analyze |
| quality_gate_check | 脚本调用 | python scripts/skill-test.py --gate [gate_id] |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| devops-engineer | 主导 | 构建执行、环境管理 |
| fullstack-engineer | 辅助 | 构建问题修复 |
| performance-optimizer | 辅助 | 构建优化 |

## 命令描述

执行项目构建与编译，通过技能分析和质量门禁检查，确保项目可正确构建并满足质量标准。该命令支持Web应用、库和工具的构建。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/build` |
| 关键词触发 | 用户提及"项目构建"、"编译"、"build" |
| 自动触发 | `/sprint` 命令执行时自动调用Build阶段 |
| 流程触发 | `/accept` 完成后自动进入Build阶段 |

## 命令名称与语法

```
/build [--env=<环境>] [--optimize] [--analyze]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--env` | enum | 否 | production | 构建环境：development/staging/production |
| `--optimize` | flag | 否 | true | 启用构建优化 |
| `--analyze` | flag | 否 | false | 分析构建产物（bundle大小等） |
| `--source-map` | flag | 否 | true | 生成Source Map |
| `--clean` | flag | 否 | false | 清理后重新构建 |

## 执行流程

> 标准五步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证 → 5. 输出交付

1. **输入验证**：校验项目配置存在、`--env`参数合法
2. **Agent调度**：devops-engineer主导构建执行
3. **任务执行**：执行依赖安装→代码编译→资源优化→产物生成的完整构建流程
4. **结果验证**：执行quality_gate_check(phase=7)
5. **输出交付**：生成构建产物、构建报告

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| BUILD-SUCCESS | BLOCK | 构建成功、无编译错误、产物完整 |
| BUILD-SIZE | WARN | Bundle大小在阈值内、无异常大文件 |

## 使用示例

### 示例1：生产构建

```
/build
```

### 示例2：开发构建

```
/build --env=development
```

### 示例3：分析构建产物

```
/build --analyze
```

### 示例4：清理重建

```
/build --clean
```

### 示例5：无优化构建

```
/build --env=staging --no-optimize
```

## 相关脚本

- `scripts/skill-test.py` - 技能测试器，执行质量门禁检查

---

## 相关命令

- `/build-desktop` - 桌面应用构建
- `/deploy` - 部署交付
- `/test` - 测试执行
- `/sprint` - 启动完整冲刺
