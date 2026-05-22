---
name: /clarify
aliases:
  - c
category: workflow
phase: "1"
description: 需求澄清与歧义检测
trigger: 需求不明确或存在歧义时
workflow: brainstorming-workflow
---

# /clarify 命令

## 命令用途

执行需求澄清与歧义检测，确保需求描述清晰、完整、可实施。是SDD流程的第一步。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | knowledge_search | query=<需求描述> | 搜索知识库中相关需求模式和澄清策略 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| knowledge_search | 脚本调用 | python scripts/knowledge-server.py --search [query] |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| product-manager | 主导 | 需求管理、优先级排序 |
| system-architect | 辅助 | 技术可行性评估 |
| technical-writer | 辅助 | 需求文档整理 |
| security-auditor | 辅助 | 安全需求识别 |

## 命令描述

执行需求澄清与歧义检测，确保需求描述清晰、完整、可实施。该命令是SDD流程的第一步，为后续计划制定和规格编写奠定基础。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/clarify` |
| 关键词触发 | 用户提及"需求澄清"、"需求不明确"、"需求分析" |
| 自动触发 | `/sprint` 命令执行时自动调用Clarify阶段 |
| 条件触发 | 检测到需求描述存在歧义或缺失时自动建议 |

## 命令名称与语法

```
/clarify <需求描述> [--depth=<深度>] [--output=<输出格式>]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `<需求描述>` | string | 是 | - | 待澄清的需求文本或文件路径 |
| `--depth` | enum | 否 | standard | 澄清深度：quick/standard/thorough |
| `--output` | enum | 否 | markdown | 输出格式：markdown/json/yaml |
| `--questions` | int | 否 | 5 | 最大问题数量 |
| `--context` | path | 否 | - | 上下文文件路径（如现有代码） |

## 执行流程

> 标准五步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证 → 5. 输出交付

1. **输入验证**：校验需求描述非空、`--depth`参数合法、`--context`路径存在
2. **Agent调度**：product-manager主导需求分析，system-architect评估技术可行性，security-auditor识别安全需求
3. **任务执行**：执行语义分析→歧义检测→缺失识别→问题生成→用户确认→需求完善的完整澄清流程
4. **结果验证**：执行GATE-001门禁检查，验证所有高优先级问题已回答、验收标准可测试、无遗留歧义
5. **输出交付**：生成clarified-requirements.md和acceptance-criteria.json

## 歧义检测规则

### 高优先级检测

| 检测类型 | 示例 | 建议澄清 |
|----------|------|----------|
| 模糊量词 | "大量数据" | 具体数量级 |
| 条件缺失 | "用户登录后" | 未登录时行为 |
| 边界模糊 | "快速响应" | 具体响应时间 |
| 权限未定 | "用户可以查看" | 哪类用户 |

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| GATE-001 | BLOCK | 所有高优先级问题已回答、验收标准可测试、无遗留歧义、需求完整度评分≥90 |
| GATE-002 | BLOCK | 术语使用一致、内部逻辑无矛盾 |

## 使用示例

### 示例1：标准澄清

```
/clarify 实现一个用户可以搜索商品并添加到购物车的功能
```

### 示例2：深度澄清

```
/clarify 实现支付系统 --depth=thorough --questions=10
```

### 示例3：带上下文澄清

```
/clarify 添加用户权限管理 --context=./src/auth/
```

### 示例4：JSON输出

```
/clarify 实现数据导出 --output=json
```

## 相关脚本

- `scripts/init-session.py` - 会话初始化器，创建澄清会话和工作目录结构

---

## 相关命令

- `/plan` - 基于澄清结果制定计划
- `/spec` - 基于澄清结果编写规格
- `/sprint` - 启动完整冲刺周期
