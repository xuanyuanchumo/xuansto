---
name: /learn
aliases:
  - l
category: system
phase: "any"
description: 知识学习与经验积累
trigger: 需要学习新知识或积累经验时
workflow: none
---

# /learn 命令

## 命令用途

执行知识学习与经验积累，搜索知识库中的相关模式和最佳实践，将学习成果存储到项目知识库中。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | knowledge_search | query=<学习主题> | 搜索知识库中相关模式和最佳实践 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| knowledge_search | 脚本调用 | python scripts/knowledge-server.py --search [query] |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| knowledge-manager | 主导 | 知识搜索、经验整理、知识存储 |
| system-architect | 辅助 | 技术知识评估 |
| technical-writer | 辅助 | 知识文档整理 |

## 命令描述

执行知识学习与经验积累，搜索知识库中的相关模式和最佳实践，将学习成果存储到项目知识库中。该命令支持从代码库、文档和外部资源中学习。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/learn` |
| 关键词触发 | 用户提及"学习"、"知识积累"、"learn" |
| 自动触发 | 检测到新技术栈或未知模式时 |
| 条件触发 | 项目知识库缺少相关领域知识时 |

## 命令名称与语法

```
/learn <主题> [--source=<来源>] [--depth=<深度>]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `<主题>` | string | 是 | - | 学习主题或关键词 |
| `--source` | enum | 否 | all | 知识来源：all/codebase/docs/external |
| `--depth` | enum | 否 | standard | 学习深度：quick/standard/thorough |
| `--save` | flag | 否 | true | 保存学习成果到知识库 |
| `--category` | string | 否 | auto | 知识分类 |

## 执行流程

> 标准四步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证

1. **输入验证**：校验学习主题非空、`--source`参数合法
2. **Agent调度**：knowledge-manager主导知识搜索和整理
3. **任务执行**：执行知识搜索→知识提取→知识整理→知识存储的完整学习流程
4. **结果验证**：验证知识已正确存储、可被后续命令检索

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| LEARN-STORED | BLOCK | 学习成果已存储到知识库、可被检索 |

## 使用示例

### 示例1：学习新框架

```
/learn React Server Components
```

### 示例2：从代码库学习

```
/learn 认证模式 --source=codebase
```

### 示例3：深度学习

```
/learn 微服务架构 --depth=thorough
```

### 示例4：指定分类

```
/learn 设计模式 --category=architecture
```

## 相关脚本

- `scripts/knowledge-server.py` - 知识服务器，知识库搜索和存储

---

## 相关命令

- `/clarify` - 需求澄清
- `/brainstorm` - 需求探索
- `/agent-status` - Agent状态查询
