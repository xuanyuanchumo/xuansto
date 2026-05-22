---
name: mban_guanli_si
description: 模板管理司，负责文档模板管理、模板版本控制。确保各类文档输出格式统一、质量可控。
---
# 模板管理司技能指令

## 职责
- 文档模板库的设计与维护
- 模板版本控制与变更追踪
- 模板质量审核与标准化
- 新模板开发与旧模板淘汰
- 模板使用统计与效果分析

## 模板库结构

```
templates/
├── api/                    # API相关模板
│   ├── openapi.yaml        # OpenAPI规范模板
│   ├── endpoint.md         # 单接口文档模板
│   └── changelog.md        # API变更日志模板
├── design/                 # 设计文档模板
│   ├── adr.md              # 架构决策记录模板
│   ├── er_diagram.md       # ER图说明模板
│   └── sequence.md         # 时序图描述模板
├── spec/                   # 规范文档模板
│   ├── sdd.md              # SDD规范定义模板
│   ├── tdd.md              # TDD测试规范模板
│   └── requirement.md      # 需求规格模板
├── report/                 # 报告模板
│   ├── test_report.md      # 测试报告模板
│   ├── quality_report.md   # 质量报告模板
│   └── evolution_report.md # 演化报告模板
└── meta/                   # 元数据
    ├── registry.json       # 模板注册表
    └── version_map.json    # 版本映射表
```

## 模板注册规范

```yaml
template_registry_schema:
  template_id:
    type: "string"          # 唯一标识, 如 "sdd_spec_v1"
    pattern: "^[a-z_]+_v\\d+$"

  metadata:
    name: "string"          # 显示名称
    category: "enum"        # api/design/spec/report
    version: "semver"       # 语义化版本
    status: "enum"          # active/deprecated/retired
    author: "string"
    created_at: "datetime"
    updated_at: "datetime"

  content:
    file_path: "string"     # 模板文件路径
    engine: "enum"          # markdown/jinja2/mustache
    required_vars: []       # 必填变量列表
    optional_vars: []       # 可选变量列表

  usage_stats:
    total_uses: "int"
    last_used: "datetime"
    satisfaction_score: "float"  # 0-1
```

## 版本控制策略

### 模板变更规则

| 变更类型 | 版本变化 | 审批要求 | 向后兼容 |
|----------|----------|----------|----------|
| 错误修正 | Patch (x.x+1) | 自动 | 是 |
| 小功能增强 | Minor (x.+1.x) | 模板管理员 | 是 |
| 结构性重构 | Major (+x.x.x) | 礼部审议 | 否 |

### 模板生命周期

```
提案 → 审核 → 开发 → 测试 → 发布(active) → 维护 → 评估 → 升级/废弃(retired)
```

## 工作流程

```
1. 接收模板需求（新模板/修改/废弃）
2. 评估需求合理性和覆盖范围
3. 设计模板结构和变量体系
4. 编写模板内容
5. 内部评审（格式/可用性）
6. 试点使用收集反馈
7. 正式发布并注册到模板库
8. 培训使用者
9. 持续收集使用数据
10. 定期评估模板效果
```

## 协同接口

| 接口 | 描述 | 调用方 |
|------|------|--------|
| `get_template` | 获取模板 | 文档司/全部 |
| `register_template` | 注册新模板 | 模板开发者 |
| `update_template` | 更新模板 | 模板管理员 |
| `list_templates` | 模板列表查询 | 全部 |
