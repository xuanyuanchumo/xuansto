---
name: /implement
aliases:
  - i
  - impl
category: workflow
phase: "4"
description: 代码实现与功能开发
trigger: 需要编写代码实现功能时
workflow: sdd-tdd-full
---

# /implement 命令

## 命令用途

基于规格文档和设计文档执行代码实现，编写功能代码并确保通过质量门禁检查。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | quality_gate_check | phase=4 | 检查实现阶段质量门禁 |
| 2 | agent_status | - | 查询可用Agent状态和负载 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| quality_gate_check | 脚本调用 | python scripts/skill-test.py --gate [gate_id] |
| agent_status | 静态查询 | 静态注册表查找 |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| fullstack-engineer | 主导 | 功能实现、代码编写 |
| backend-developer | 辅助 | 后端API实现 |
| frontend-developer | 辅助 | 前端组件实现 |
| database-engineer | 辅助 | 数据库操作实现 |
| devops-engineer | 辅助 | 部署配置实现 |

## 命令描述

基于规格文档和设计文档执行代码实现，编写功能代码并确保通过质量门禁检查。该命令是SDD流程的核心实现环节，协调多个开发Agent并行工作。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/implement` |
| 关键词触发 | 用户提及"代码实现"、"功能开发"、"编写代码" |
| 自动触发 | `/sprint` 命令执行时自动调用Implement阶段 |
| 流程触发 | `/design` 完成后自动进入Implement阶段 |

## 命令名称与语法

```
/implement [--task=<任务ID>] [--agent=<Agent>] [--parallel=<并行数>]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--task` | string | 否 | all | 指定任务ID或all |
| `--agent` | string | 否 | auto | 指定实现Agent |
| `--parallel` | int | 否 | 3 | 最大并行任务数 |
| `--skip-tests` | flag | 否 | false | 跳过单元测试编写（不推荐） |
| `--skip-lint` | flag | 否 | false | 跳过代码检查（不推荐） |
| `--dry-run` | flag | 否 | false | 仅生成代码不写入文件 |

## 执行流程

> 标准五步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证 → 5. 输出交付

1. **输入验证**：校验规格文件和设计文件存在、任务ID有效
2. **Agent调度**：根据任务类型分配fullstack-engineer/backend-developer/frontend-developer
3. **任务执行**：执行代码实现→单元测试→代码检查→文档更新的完整实现流程
4. **结果验证**：执行GATE-005和IMPL-COMPLETE门禁检查
5. **输出交付**：生成实现代码、测试代码、实现报告

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| GATE-005 | BLOCK | 代码编译通过、单元测试通过、代码检查通过 |
| IMPL-COMPLETE | BLOCK | 所有计划任务已实现、代码已提交、测试覆盖率≥80% |
| IMPL-NO-TODO | BLOCK | 实现代码中无TODO/FIXME/HACK标记 |

## 使用示例

### 示例1：实现所有任务

```
/implement
```

### 示例2：实现指定任务

```
/implement --task=TASK-001
```

### 示例3：指定Agent实现

```
/implement --agent=backend-developer
```

### 示例4：高并行度实现

```
/implement --parallel=5
```

### 示例5：试运行

```
/implement --dry-run
```

## 相关脚本

- `scripts/init-session.py` - 会话初始化器，创建实现会话和工作目录结构

---

## 相关命令

- `/design` - 设计流程
- `/test` - 测试执行
- `/review` - 代码审查
- `/sprint` - 启动完整冲刺
