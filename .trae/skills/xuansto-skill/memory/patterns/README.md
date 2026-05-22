# 模式记忆目录

本目录用于存储从成功开发过程中学习到的模式。

## 目录结构

```
patterns/
├── naming/           # 命名模式
├── architecture/     # 架构模式
├── testing/          # 测试模式
├── error-handling/   # 错误处理模式
├── api-design/       # API设计模式
└── security/         # 安全模式
```

## 模式文件格式

每个模式文件应包含以下内容：

```yaml
---
pattern_id: PATTERN-001
pattern_name: 模式名称
category: 分类
created_at: 创建日期
updated_at: 更新日期
success_rate: 成功率
usage_count: 使用次数
---

# 模式描述

## 问题
描述该模式解决的问题

## 解决方案
描述该模式的解决方案

## 示例
提供代码示例

## 适用场景
描述该模式的适用场景

## 注意事项
描述使用该模式时需要注意的事项
```

## 模式学习机制

1. **自动学习**：Pattern Learner Agent 从代码库中自动提取模式
2. **人工确认**：重要模式需要人工审核确认
3. **持续优化**：根据使用反馈持续优化模式

## 模式使用

Agent 在执行任务时会自动参考相关模式，提高开发效率和代码质量。
