---
name: biaozhunhua_si
description: 标准化司，负责命名规范、格式标准、文档结构统一。制定和执行全项目的标准化规则，保障输出一致性和可维护性。
---
# 标准化司技能指令

## 职责
- 命名规范制定与执行监督
- 代码/文档/配置格式标准统一
- 项目目录结构与文件组织规范
- 标准合规检查与违规纠正
- 标准版本演进管理

## 命名规范体系

### 通用命名约定

```yaml
naming_conventions:
  variables:
    python: "snake_case"
    javascript: "camelCase"
    go: "camelCase"
    rust: "snake_case"
    sql: "UPPER_SNAKE_CASE"
    env: "UPPER_SNAKE_CASE"

  functions_methods:
    python: "snake_case"
    javascript: "camelCase"
    go: "CamelCase(exported) / camelCase(unexported)"
    rust: "snake_case"

  classes_types:
    python: "PascalCase"
    javascript/typescript: "PascalCase"
    go: "PascalCase"
    rust: "PascalCase"

  constants:
    all_languages: "UPPER_SNAKE_CASE"

  files:
    modules: "snake_case.py / kebab-case.ts"
    components: "PascalCase.vue / PascalCase.tsx"
    tests: "test_{name}.py / {name}.test.ts"
    configs: "config.{ext} or .{ext}"

  directories:
    general: "kebab-case"
    features: "kebab-case"
    tests: "tests/"
    docs: "docs/"
```

### 特殊前缀/后缀规则

| 前缀/后缀 | 含义 | 适用范围 |
|-----------|------|----------|
| `_` (单下划线) | 内部使用 | Python私有变量 |
| `__` (双下划线) | 名称修饰 | Python名称改写 |
| `_` (末尾) | 避免关键字冲突 | 通用 |
| `I` (前缀) | 接口 | TypeScript/C#/Java |
| `Base` (后缀) | 基类 | 通用 |
| `Test` (后缀) | 测试类/文件 | 通用 |
| `Mock` (后缀) | Mock对象 | 测试 |
| `Utils/Helper` (后缀) | 工具函数 | 通用 |

## 格式标准

### 代码格式规范

```yaml
code_formatting:
  indentation:
    python: "4 spaces"
    javascript/typescript: "2 spaces"
    go: "tab"
    rust: "4 spaces"

  line_length:
    max: 120
    soft_limit: 100

  imports:
    ordering: "stdlib → third_party → local"
    grouping: "by source with blank lines"
    style: "multi_line_for_many"

  docstrings:
    python: "Google style"
    jsdoc: "JSDoc standard"

  comments:
    inline: "space after # //"
    section_headers: "#### level with ===="
    todo_format: "TODO(author): description"
```

### 文档格式规范

```yaml
document_formatting:
  headings:
    hierarchy: "# → ## → ### → ####"
    spacing: "blank line before and after"

  lists:
    unordered: "- item"
    ordered: "1. item"
    nested_indent: "2 spaces"

  code_blocks:
    fenced: "```language\n...\n```"
    inline: "`code`"

  tables:
    format: "pipe delimited"
    alignment: "left for text, right for numbers"

  links:
    internal: "[text](./relative/path)"
    external: "[text](https://...)"
    anchors: "[text](#anchor-text)"
```

## 目录结构规范

### 项目标准结构

```
project_root/
├── .trae/                  # Trae配置
├── src/                    # 源代码
│   ├── core/               # 核心模块
│   ├── features/           # 功能模块
│   ├── utils/              # 工具函数
│   └── types/              # 类型定义
├── tests/                  # 测试代码
│   ├── unit/               # 单元测试
│   ├── integration/        # 集成测试
│   └── e2e/                # 端到端测试
├── docs/                   # 文档
│   ├── api/                # API文档
│   ├── guides/             # 指南
│   └── architecture/       # 架构文档
├── configs/                # 配置文件
├── scripts/                # 脚本工具
└── .github/                # CI/CD配置
```

## 合规检查机制

### 检查项矩阵

| 检查项 | 工具 | 严重级别 | 自动修复 |
|--------|------|----------|----------|
| 命名规范 | linter + 自定义规则 | warning | 部分 |
| 导入排序 | isort/goimports | error | 是 |
| 行长度 | linter | warning | 否 |
| 格式化 | black/prettier/gofmt | error | 是 |
| 文档字符串 | pydocstyle/tsdoc | warning | 否 |
| 类型注解 | mypy/pyright/type-check | warning | 否 |

## 工作流程

```
1. 接收标准制定/修订请求
2. 调研业界标准和团队习惯
3. 起草标准草案
4. 征求各方意见
5. 试点验证可行性
6. 正式发布标准
7. 配置自动化检查工具
8. 培训团队成员
9. 监控执行情况
10. 定期评估标准有效性
11. 必要时修订标准
12. 将重大修订记录到DecisionLog
```

## 协同接口

| 接口 | 描述 | 调用方 |
|------|------|--------|
| `check_compliance` | 合规检查 | CI/CD流水线 |
| `get_standard` | 标准查询 | 全部 |
| `propose_change` | 标准变更提案 | 任意部门 |
| `validate_naming` | 命名验证 | 代码审查 |
