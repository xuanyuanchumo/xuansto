---
name: /spec
aliases:
  - sp
category: workflow
phase: "2"
description: 规格文档编写
trigger: 需要编写功能规格或设计文档时
workflow: sdd-tdd-full
---

# /spec 命令

## 命令用途

编写技术规格文档，定义API契约、数据模型、接口规范和技术标准，确保开发团队有清晰的技术指导。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | spec_drift_detect | - | 检测代码实现与规格文档之间的偏差 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| spec_drift_detect | 脚本调用 | python scripts/spec-drift-detector.py |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| system-architect | 主导 | 架构规格、技术选型 |
| specification-keeper | 辅助 | 规格一致性维护、版本管理、变更控制 |
| backend-developer | 辅助 | API规格、数据规格 |
| database-engineer | 辅助 | 数据模型、Schema |
| security-auditor | 辅助 | 安全规格 |
| technical-writer | 辅助 | 文档整理 |

## 命令描述

编写技术规格文档，定义API契约、数据模型、接口规范和技术标准。该命令确保开发团队有清晰的技术指导，是SDD流程中文档驱动的核心环节。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/spec` |
| 关键词触发 | 用户提及"规格编写"、"API规格"、"技术规格" |
| 自动触发 | `/sprint` 命令执行时自动调用Spec阶段 |
| 流程触发 | `/plan` 完成后自动进入Spec阶段 |

## 命令名称与语法

```
/spec [--type=<类型>] [--format=<格式>] [--template=<模板>]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--type` | enum | 否 | all | 规格类型：all/api/data/architecture/security |
| `--format` | enum | 否 | openapi | 输出格式：openapi/asyncapi/graphql/protobuf |
| `--template` | path | 否 | default | 自定义模板路径 |
| `--validate` | flag | 否 | true | 验证规格完整性 |
| `--generate-code` | flag | 否 | false | 生成骨架代码 |
| `--language` | list | 否 | auto | 目标语言：typescript/python/go/java |

## 执行流程

> 标准五步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证 → 5. 输出交付

1. **输入验证**：校验`--type`参数合法、`--template`路径存在；加载计划文件
2. **Agent调度**：system-architect主导架构规格，specification-keeper维护一致性
3. **任务执行**：根据`--type`参数并行或串行编写API/数据/架构/安全规格
4. **结果验证**：执行GATE-002和GATE-004门禁检查，执行spec_drift_detect
5. **输出交付**：生成api-spec.yaml、data-model.md、architecture.md等规格文档

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| GATE-002 | BLOCK | 所有API有完整定义、数据模型关系完整、版本信息完整 |
| GATE-004 | BLOCK | 技术选型合理、架构图清晰、安全要求明确 |
| SPEC-CONSISTENCY | BLOCK | 规格文档与代码实现100%一致、Spec-Drift标记项已确认 |

## 使用示例

### 示例1：生成所有规格

```
/spec
```

### 示例2：仅生成API规格

```
/spec --type=api
```

### 示例3：生成GraphQL规格

```
/spec --type=api --format=graphql
```

### 示例4：生成并验证

```
/spec --validate --generate-code --language=typescript
```

### 示例5：使用自定义模板

```
/spec --template=./templates/api-spec-template.yaml
```

## 相关脚本

- `scripts/spec-drift-detector.py` - 规格偏移检测器，检测代码实现与规格文档之间的偏差
- `scripts/api-contract-validator.py` - API契约验证器，验证接口契约完整性

---

## 相关命令

- `/plan` - 计划制定
- `/design` - 设计流程
- `/implement` - 开始实施
- `/sprint` - 启动完整冲刺
