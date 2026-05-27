---
name: /init
aliases:
  - ini
category: system
phase: "0"
description: 项目初始化与基础结构创建
trigger: 需要初始化新项目或创建基础结构时
execution_mode: inline
---

# /init 命令

## 命令描述

`/init` 命令用于项目初始化与基础结构创建，是项目生命周期的起始命令。该命令管理从项目类型检测到完整基础结构搭建的初始化流程，支持Web、桌面、跨平台项目类型，自动创建知识库目录、配置文件与语言特定配置，确保项目具备完整的开发基础设施与知识管理能力。

---

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/init` |
| 关键词触发 | 用户提及"初始化"、"新项目"、"setup"、"项目设置" |
| 自动触发 | 新项目目录首次进入时建议初始化 |
| 流程触发 | `/sprint` 创建新冲刺时自动建议初始化 |

---

## 命令名称与语法

```
/init [options]
```

---

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| --type | string | 否 | auto-detect | 项目类型：web、desktop、cross-platform |
| --template | string | 否 | - | 项目模板名称 |
| --skip-kb | boolean | 否 | false | 跳过知识库初始化 |
| --skip-git | boolean | 否 | false | 跳过Git初始化 |
| --skip-deps | boolean | 否 | false | 跳过依赖安装 |
| --language | string | 否 | auto-detect | 主要编程语言 |
| --framework | string | 否 | auto-detect | 前端/后端框架 |
| --config-only | boolean | 否 | false | 仅创建配置文件，不创建目录结构 |

---

## 执行流程

> 标准四步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证

```
┌─────────────────────────────────────────────────────────────┐
│                    /init 执行流程                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 输入验证                                                 │
│     ├── 检测项目类型（从目录结构推断）                        │
│     ├── 检测主要编程语言                                     │
│     ├── 检测框架依赖                                         │
│     ├── 验证目标目录是否为空或可初始化                        │
│     └── 确认初始化参数                                       │
│                                                             │
│  2. Agent调度                                                │
│     ├── Orchestrator 接收初始化任务                          │
│     ├── System Architect 规划项目结构                        │
│     └── Knowledge Manager 准备知识库                        │
│                                                             │
│  3. 结构创建                                                 │
│     ├── 创建项目目录结构                                     │
│     │   ├── src/ (源代码目录)                               │
│     │   ├── tests/ (测试目录)                               │
│     │   ├── docs/ (文档目录)                                │
│     │   └── scripts/ (脚本目录)                             │
│     ├── 创建配置文件                                         │
│     │   ├── .knowledge/ (知识库目录)                        │
│     │   ├── .skill-config.yaml (技能配置)                   │
│     │   ├── .editorconfig (编辑器配置)                      │
│     │   ├── .gitignore (Git忽略规则)                        │
│     │   └── 语言特定配置文件                                 │
│     │       ├── TypeScript: tsconfig.json                   │
│     │       ├── Python: pyproject.toml / setup.cfg          │
│     │       ├── Rust: Cargo.toml                            │
│     │       └── Go: go.mod                                  │
│     ├── 创建框架特定配置                                     │
│     │   ├── React: vite.config.ts / webpack.config.js       │
│     │   ├── Vue: vite.config.ts / vue.config.js             │
│     │   ├── Next.js: next.config.js                         │
│     │   └── Electron: electron-builder.yml                  │
│     └── 初始化Git仓库（如未跳过）                            │
│                                                             │
│  4. 知识库初始化                                             │
│     ├── 创建知识库目录结构                                   │
│     │   ├── .knowledge/decisions/ (决策记录)                │
│     │   ├── .knowledge/patterns/ (模式库)                   │
│     │   ├── .knowledge/context/ (上下文信息)                │
│     │   └── .knowledge/learnings/ (经验沉淀)                │
│     ├── 初始化SQLite数据库                                   │
│     ├── 初始化Chroma向量存储                                 │
│     ├── 加载默认知识模板                                     │
│     └── 验证知识服务可访问                                   │
│                                                             │
│  5. 验证                                                     │
│     ├── 检查所有必需目录已创建                               │
│     ├── 检查所有配置文件已生成                               │
│     ├── 验证知识库服务可访问                                 │
│     ├── 验证Git仓库已初始化                                 │
│     └── 生成初始化报告                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| orchestrator | 主导 | 初始化流程协调、任务分配 |
| system-architect | 辅助 | 项目结构规划、架构决策 |
| knowledge-manager | 辅助 | 知识库创建与管理 |

---

## 输出格式

### 1. 初始化报告 (init-report.md)

```markdown
# 初始化报告

## 初始化概要
- 初始化时间: 2026-05-06 09:00:00
- 项目类型: web
- 主要语言: TypeScript
- 框架: React
- 模板: default
- 初始化状态: ✅ 成功

## 创建的目录
| 目录 | 状态 | 说明 |
|------|------|------|
| src/ | ✅ 已创建 | 源代码目录 |
| src/components/ | ✅ 已创建 | 组件目录 |
| src/hooks/ | ✅ 已创建 | Hooks目录 |
| src/utils/ | ✅ 已创建 | 工具函数目录 |
| tests/ | ✅ 已创建 | 测试目录 |
| tests/unit/ | ✅ 已创建 | 单元测试目录 |
| tests/integration/ | ✅ 已创建 | 集成测试目录 |
| docs/ | ✅ 已创建 | 文档目录 |
| scripts/ | ✅ 已创建 | 脚本目录 |
| .knowledge/ | ✅ 已创建 | 知识库目录 |

## 创建的配置文件
| 文件 | 状态 | 说明 |
|------|------|------|
| .skill-config.yaml | ✅ 已创建 | 技能配置 |
| .editorconfig | ✅ 已创建 | 编辑器配置 |
| .gitignore | ✅ 已创建 | Git忽略规则 |
| tsconfig.json | ✅ 已创建 | TypeScript配置 |
| vite.config.ts | ✅ 已创建 | Vite构建配置 |
| package.json | ✅ 已创建 | 项目依赖配置 |

## 知识库状态
- SQLite: ✅ 已初始化
- Chroma: ✅ 已初始化
- 知识模板: ✅ 已加载
- 服务可访问: ✅ 正常

## Git状态
- 仓库: ✅ 已初始化
- 初始提交: ✅ 已完成
```

### 2. 项目配置 (.skill-config.yaml)

```yaml
project:
  name: auto-detected
  type: web
  language: typescript
  framework: react

knowledge:
  enabled: true
  backend: sqlite+chroma
  path: .knowledge/

quality:
  gates_enabled: true
  block_on_failure: true

agents:
  default_team: full
  max_parallel: 5
```

---

## 示例用法

### 示例1: 标准初始化

```bash
/init
```

自动检测项目类型并执行完整初始化。

### 示例2: 桌面项目初始化

```bash
/init --type desktop
```

初始化桌面应用项目结构。

### 示例3: 跨平台项目初始化

```bash
/init --type cross-platform --template electron
```

使用Electron模板初始化跨平台项目。

### 示例4: 跳过知识库初始化

```bash
/init --skip-kb
```

初始化项目但跳过知识库创建。

### 示例5: 仅创建配置文件

```bash
/init --config-only
```

仅创建配置文件，不创建完整目录结构。

---

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| INIT-COMPLETE | BLOCK | 所有必需目录和配置文件均已创建 |

---

## 注意事项

1. **目录检查**: 初始化前确认目标目录状态，避免覆盖已有文件
2. **知识库依赖**: 知识库初始化需要SQLite和Chroma服务可用
3. **模板选择**: 选择合适的项目模板可大幅减少后续配置工作
4. **Git初始化**: 建议始终初始化Git仓库以支持版本管理
5. **配置定制**: 初始化后应根据项目需求定制配置文件

---

## 相关脚本

- `scripts/project-initializer.py` - 项目初始化器，创建目录结构、配置文件与知识库

---

## 相关工作流

- `workflows/sdd-tdd-full.md` (Phase 1) - SDD+TDD全生命周期工作流的需求分析阶段

---

## 相关命令

- `/sprint` - 初始化后创建冲刺规划
- `/plan` - 初始化后进行项目规划
- `/status` - 查看项目初始化状态
