# Xuansto Skill Git 管理策略

> 版本: 1.0.0 | 日期: 2026-05-23 | 状态: 草案
> 关联文档: REFACTOR_PLAN.md / setup-worktree.ps1

---

## 目录

1. [Git Worktree 并行开发策略](#1-git-worktree-并行开发策略)
2. [本地分支管理](#2-本地分支管理)
3. [.gitignore 合理性审查与优化](#3-gitignore-合理性审查与优化)
4. [分支与重构阶段映射](#4-分支与重构阶段映射)
5. [操作命令序列](#5-操作命令序列)

---

## 1. Git Worktree 并行开发策略

### 1.1 为什么使用 Worktree

Xuansto Skill 项目包含三个紧密耦合的组件（v1 Skill / v2 Skill / MCP Server），重构期间需要同时推进多个优先级的任务。Git Worktree 允许在同一仓库下同时检出多个分支到不同目录，实现：

- **并行开发**：P0 紧急修复与 P1 接口治理可在不同工作树中同步推进
- **隔离测试**：每个工作树拥有独立的工作区，互不干扰
- **零切换成本**：无需 `git stash` 或 `git checkout`，直接在不同目录间切换

### 1.2 Worktree 目录结构

```
D:\Projects\TraeProjects\
├── skiller\                          ← 主工作树 (main 分支，稳定基线)
│   ├── .trae/skills/xuansto-skill/       (v5, deprecated)
│   ├── .trae/skills/xuansto-skill-v2/    (v7, current)
│   └── xuansto-mcp-server/               (MCP Server)
│
├── skiller-dev\                      ← 开发工作树 (develop 分支)
│   └── (同上结构)
│
├── skiller-hotfix\                   ← 热修复工作树 (hotfix 分支)
│   └── (同上结构)
│
├── skiller-p0\                       ← P0 紧急修复工作树 (feature/p0-fixes 分支)
│   └── (同上结构)
│
├── skiller-mcp-core\                 ← MCP 核心重构工作树 (feature/mcp-core 分支)
│   └── (同上结构)
│
├── skiller-progressive\              ← 渐进式加载工作树 (feature/progressive-loading 分支)
│   └── (同上结构)
│
└── skiller-api-gov\                  ← API 治理工作树 (feature/p1-api-governance 分支)
    └── (同上结构)
```

### 1.3 Worktree 与分支对应关系

| 工作树目录 | 分支 | 用途 | 生命周期 |
|-----------|------|------|---------|
| `skiller\` | `main` | 稳定发布基线，仅接受合并 | 永久 |
| `skiller-dev\` | `develop/v8` | v8 版本开发集成分支 | 永久 |
| `skiller-hotfix\` | `hotfix` | 紧急线上修复 | 按需 |
| `skiller-p0\` | `feature/p0-fixes` | P0 紧急修复（降级/持久化/文档） | 第1周后合并删除 |
| `skiller-mcp-core\` | `feature/mcp-core` | MCP 核心重构（Tool注册/Hook/降级异步化） | 第2-3周后合并删除 |
| `skiller-progressive\` | `feature/progressive-loading` | 渐进式加载完善 | 第4-5周后合并删除 |
| `skiller-api-gov\` | `feature/p1-api-governance` | P1 接口治理（版本协商/knowledge/文档） | 第2-3周后合并删除 |

### 1.4 Worktree 管理原则

1. **一个功能一个工作树**：每个 feature 分支对应独立工作树，完成后合并并移除
2. **develop 为集成分支**：所有 feature 分支完成后合并到 `develop/v8`，经测试后合并到 `main`
3. **main 仅接受合并**：禁止在 `main` 分支上直接提交
4. **工作树及时清理**：feature 分支合并后立即执行 `git worktree remove` 和 `git branch -d`

---

## 2. 本地分支管理

### 2.1 分支总览

| 分支名 | 类型 | 基分支 | 创建时机 | 合并时机 | 说明 |
|--------|------|--------|---------|---------|------|
| `main` | 长期 | - | 初始化 | - | 稳定发布基线 |
| `develop/v8` | 长期 | `main` | 重构启动时 | 每阶段完成后→`main` | v8 版本开发集成 |
| `feature/p0-fixes` | 短期 | `develop/v8` | 第1周开始 | 第1周末→`develop/v8` | P0 紧急修复 |
| `feature/mcp-core` | 短期 | `develop/v8` | 第2周开始 | 第3周末→`develop/v8` | MCP 核心重构 |
| `feature/p1-api-governance` | 短期 | `develop/v8` | 第2周开始 | 第3周末→`develop/v8` | P1 接口治理 |
| `feature/progressive-loading` | 短期 | `develop/v8` | 第4周开始 | 第5周末→`develop/v8` | 渐进式加载完善 |
| `hotfix` | 按需 | `main` | 紧急问题时 | 修复后→`main`+`develop/v8` | 紧急热修复 |

### 2.2 分支详细说明

#### `main` — 稳定基线

- 仅接受来自 `develop/v8` 的合并和 `hotfix` 的 cherry-pick
- 每次合并打 tag：`v8.0.0-p0`、`v8.0.0-p1`、`v8.0.0` 等
- 禁止直接 push 代码到此分支

#### `develop/v8` — 开发集成

- 所有 feature 分支的汇聚点
- 每个阶段完成后从此分支创建下一个 feature 分支
- 合并前需通过该阶段全部验收标准

#### `feature/p0-fixes` — 紧急修复

- 对应 REFACTOR_PLAN P0 阶段
- 包含三个子任务，可并行开发：
  - P0-A: 降级机制修复 (U-01)
  - P0-B: 参考文档补充 (U-02)
  - P0-C: 状态持久化修复 (U-03)
- 合并条件：17 个 Tool 降级链可达、v2 参考文档覆盖全部 Phase、状态持久化原子性测试通过

#### `feature/mcp-core` — MCP 核心重构

- 对应 REFACTOR_PLAN P1 中 MCP Server 侧重部分
- 包含：
  - P1-A: Tool 注册解耦 (U-04)
  - P1-D: 降级脚本异步化 (U-09)
  - P1-E: Tool 职责拆分 (U-10)
  - P1-F: ChromaDB 可选化 (U-08)
- 合并条件：`_tool_manager._tools` 零引用、降级脚本异步测试通过、agent_status/agent_manage 拆分完成

#### `feature/p1-api-governance` — 接口治理

- 对应 REFACTOR_PLAN P1 中 Skill/API 侧重部分
- 包含：
  - P1-B: 版本协商完善 (U-05)
  - P1-C: knowledge 接口治理 (U-06)
  - P1-G: 工具文档与暴露补全 (U-07)
- 合并条件：版本协商响应含功能列表、knowledge_search 只读、mcp-tools.md 覆盖全部 19 个 Tool

#### `feature/progressive-loading` — 渐进式加载

- 对应 REFACTOR_PLAN P2 中渐进式加载相关部分
- 包含：
  - P2-D: 渐进式加载完善 (U-11, U-27, U-28, U-29)
  - P2-F: Resource 增强 (U-19, U-22, U-23)
  - 部分 P2-C: Hook 系统加固 (U-13, U-20, U-25)
- 合并条件：Phase 推进/降级状态机工作正常、DisclosureTransition 通知可触发、Resource 分页可用

#### `hotfix` — 紧急热修复

- 从 `main` 创建，修复后同时合并回 `main` 和 `develop/v8`
- 仅用于生产环境紧急问题，不用于常规开发

### 2.3 分支合并流程

```
feature/p0-fixes ──────┐
                       ▼
feature/mcp-core ────▶ develop/v8 ──(阶段测试通过)──▶ main (tag)
                       ▲
feature/p1-api-gov ───┘

feature/progressive-loading ──▶ develop/v8 ──(阶段测试通过)──▶ main (tag)

hotfix ──▶ main (cherry-pick to develop/v8)
```

**合并规则：**

1. Feature 分支使用 `--no-ff` 合并到 `develop/v8`，保留分支历史
2. `develop/v8` 到 `main` 使用 squash merge，保持主线整洁
3. 合并前必须通过该阶段全部验收标准（见 REFACTOR_PLAN.md）
4. 合并后立即删除 feature 分支和对应 worktree

---

## 3. .gitignore 合理性审查与优化

### 3.1 当前配置分析

当前项目根目录 `.gitignore` 内容：

```gitignore
.trae/*
!.trae/skills/
.trae/skills/*
!.trae/skills/xuansto-skill/
!.trae/skills/xuansto-skill-v2/

.trae/skills/xuansto-skill/.knowledge/temp-scripts/*
!.trae/skills/xuansto-skill/.knowledge/temp-scripts/.gitkeep
.trae/skills/xuansto-skill/.knowledge/script-errors/*
!.trae/skills/xuansto-skill/.knowledge/script-errors/.gitkeep
.trae/skills/xuansto-skill/.knowledge/index/knowledge.db

.trae/skills/xuansto-skill-v2/.knowledge/temp-scripts/*
!.trae/skills/xuansto-skill-v2/.knowledge/temp-scripts/.gitkeep
.trae/skills/xuansto-skill-v2/.knowledge/script-errors/*
!.trae/skills/xuansto-skill-v2/.knowledge/script-errors/.gitkeep

.xuansto/

.venv/
__pycache__/
*.py[cod]
*$py.class

.DS_Store
Thumbs.db
._*

.idea/
.vscode/
*.swp
*.swo
*~

.env
.env.local
.env.*.local

*.log
logs/

*.db
*.sqlite3

副本/
docs/
```

### 3.2 问题清单

| # | 问题 | 影响 | 严重度 |
|---|------|------|--------|
| 1 | `docs/` 被整体排除，`docs/plan/` 下的规划文档无法提交 | 重构规划文档（含本文档）无法纳入版本管理 | **严重** |
| 2 | `*.db` 排除规则与 `.trae/skills/xuansto-skill/.knowledge/index/knowledge.db` 的排除重复 | 冗余规则，增加理解成本 | 低 |
| 3 | `.trae/skills/` 的排除/保留逻辑复杂，v2 缺少 `.knowledge/` 目录的排除规则 | v2 的 knowledge.db 可能被意外提交 | 中 |
| 4 | 缺少 `xuansto-mcp-server/` 相关构建产物排除（`dist/`、`*.egg-info/`） | 子项目根目录有独立 .gitignore，但根目录未覆盖 | 低 |
| 5 | `副本/` 排除规则过于特定，缺乏通用性说明 | 不影响功能，但可读性差 | 低 |

### 3.3 优化方案

核心变更：将 `docs/` 整体排除改为仅排除生成文档，保留规划文档。

```gitignore
.trae/*
!.trae/skills/
.trae/skills/*
!.trae/skills/xuansto-skill/
!.trae/skills/xuansto-skill-v2/

.trae/skills/xuansto-skill/.knowledge/temp-scripts/*
!.trae/skills/xuansto-skill/.knowledge/temp-scripts/.gitkeep
.trae/skills/xuansto-skill/.knowledge/script-errors/*
!.trae/skills/xuansto-skill/.knowledge/script-errors/.gitkeep
.trae/skills/xuansto-skill/.knowledge/index/knowledge.db

.trae/skills/xuansto-skill-v2/.knowledge/
!.trae/skills/xuansto-skill-v2/.knowledge/.gitkeep

.xuansto/

.venv/
__pycache__/
*.py[cod]
*$py.class
*.so

.DS_Store
Thumbs.db
._*

.idea/
.vscode/
*.swp
*.swo
*~

.env
.env.local
.env.*.local

*.log
logs/

*.db
*.sqlite3

docs/_build/
docs/_static/
docs/_templates/
!docs/plan/

副本/
```

### 3.4 变更说明

| 变更项 | 原规则 | 新规则 | 理由 |
|--------|--------|--------|------|
| docs 目录 | `docs/`（整体排除） | `docs/_build/` + `docs/_static/` + `docs/_templates/` + `!docs/plan/` | 保留规划文档可提交，仅排除 Sphinx 等工具生成的构建产物 |
| v2 knowledge | 无排除 | `.trae/skills/xuansto-skill-v2/.knowledge/` + `!.gitkeep` | 与 v1 保持一致，防止 knowledge.db 等运行时产物被提交 |
| *.so | 缺失 | 新增 `*.so` | Python C 扩展编译产物不应提交 |

### 3.5 优化后需执行的命令

```powershell
# 修改 .gitignore 后，强制添加已被忽略的规划文档
git add -f docs/plan/REFACTOR_PLAN.md
git add -f docs/plan/ARCHITECTURE.md
git add -f docs/plan/DATABASE_DESIGN.md
git add -f docs/plan/MCP_REVIEW.md
git add -f docs/plan/SKILL_REVIEW.md
git add -f docs/plan/API_SPECIFICATION.md
git add -f docs/plan/v-git.md
```

---

## 4. 分支与重构阶段映射

### 4.1 映射总表

| 重构阶段 | 对应分支 | 解决问题 | 周期 | 前置依赖 |
|---------|---------|---------|------|---------|
| **P0: 紧急修复** | `feature/p0-fixes` | U-01, U-02, U-03 | 第1周 | 无 |
| **P1-A/D/E/F: MCP 核心** | `feature/mcp-core` | U-04, U-08, U-09, U-10 | 第2-3周 | P0 |
| **P1-B/C/G: 接口治理** | `feature/p1-api-governance` | U-05, U-06, U-07 | 第2-3周 | P0 |
| **P2-A/B/C/E/G: 架构加固(上)** | `develop/v8` 直接提交 | U-11~U-18, U-20, U-24~U-26 | 第4周 | P1 |
| **P2-D/F: 渐进式加载** | `feature/progressive-loading` | U-19, U-22, U-23, U-27~U-29 | 第4-5周 | P1 |
| **P3: 优化收尾** | `develop/v8` 直接提交 | U-32~U-42 | 第6周+ | P2 |

### 4.2 详细映射

#### P0 → `feature/p0-fixes`

| 子任务 | 统一编号 | 涉及文件 | Worktree |
|--------|---------|---------|----------|
| P0-A: 降级机制修复 | U-01 | degradation.py, subprocess_utils.py, constraints.yaml, scripts/*.py | `skiller-p0\` |
| P0-B: 参考文档补充 | U-02 | .trae/skills/xuansto-skill-v2/references/ | `skiller-p0\` |
| P0-C: 状态持久化修复 | U-03 | degradation.py (_persist_state), metrics.py, .xuansto/*.json | `skiller-p0\` |

**合并检查点**：第1周末，全部 P0 验收标准通过后合并到 `develop/v8`。

#### P1 → `feature/mcp-core` + `feature/p1-api-governance`（并行）

**`feature/mcp-core` 分支：**

| 子任务 | 统一编号 | 涉及文件 |
|--------|---------|---------|
| P1-A: Tool 注册解耦 | U-04 | server.py, hook_engine.py |
| P1-D: 降级脚本异步化 | U-09 | subprocess_utils.py |
| P1-E: Tool 职责拆分 | U-10 | agent_status.py, schemas.py, routes.yaml |
| P1-F: ChromaDB 可选化 | U-08 | search_engine.py, config.py |

**`feature/p1-api-governance` 分支：**

| 子任务 | 统一编号 | 涉及文件 |
|--------|---------|---------|
| P1-B: 版本协商完善 | U-05 | server_health.py, SKILL.md, config.py |
| P1-C: knowledge 接口治理 | U-06 | knowledge_search.py, knowledge_inject.py, mcp-tools.md |
| P1-G: 工具文档与暴露补全 | U-07 | mcp-tools.md, metrics.py (新增 metrics_report) |

**合并检查点**：第3周末，两个分支分别通过验收后合并到 `develop/v8`。注意 `feature/mcp-core` 需先合并，因为 `feature/p1-api-governance` 的 P1-G 依赖 P1-A 的 Tool 注册表。

#### P2 → `feature/progressive-loading` + `develop/v8` 直接提交

**`feature/progressive-loading` 分支（独立大特性）：**

| 子任务 | 统一编号 | 涉及文件 |
|--------|---------|---------|
| P2-D: 渐进式加载完善 | U-11, U-27, U-28, U-29 | resource_load_status.py, SKILL.md, fallback_config.yaml |
| P2-F: Resource 增强 | U-19, U-22, U-23 | skill_resources.py, config.py |

**`develop/v8` 直接提交（小范围改动）：**

| 子任务 | 统一编号 | 涉及文件 |
|--------|---------|---------|
| P2-A: 数据层统一 | U-14, U-15, U-16, U-18 | 新建 xuansto.db, 迁移 JSON→SQLite |
| P2-B: 配置校验层 | U-17 | 新建 Pydantic 模型, config.py |
| P2-C: Hook 系统加固 | U-13, U-20, U-25 | hook_engine.py |
| P2-E: 通知与错误治理 | U-21, U-30, U-31 | errors.py, notification.py |
| P2-G: Agent 与工作流治理 | U-12, U-24, U-26 | orchestrator.py, path_resolver.py |

**合并检查点**：第5周末，`feature/progressive-loading` 合并到 `develop/v8`，P2 全部完成后 `develop/v8` 合并到 `main` 并打 tag `v8.0.0-p2`。

#### P3 → `develop/v8` 直接提交

| 子任务 | 统一编号 |
|--------|---------|
| P3-A: 文档与版本治理 | U-32, U-33, U-34, U-35, U-36 |
| P3-B: 数据模型增强 | U-37, U-38, U-39, U-40, U-41 |
| P3-C: 安全与一致性 | U-42 |

P3 为优化收尾，改动范围小且互不依赖，直接在 `develop/v8` 上提交即可。

### 4.3 阶段里程碑与 Tag

| 时间点 | Tag | 包含阶段 | 验收要点 |
|--------|-----|---------|---------|
| 第1周末 | `v8.0.0-p0` | P0 | 降级链可达、文档覆盖、持久化原子性 |
| 第3周末 | `v8.0.0-p1` | P0 + P1 | Tool 注册解耦、版本协商、knowledge 只读/只写分离 |
| 第5周末 | `v8.0.0-p2` | P0 + P1 + P2 | 数据层统一、渐进式加载完善、Hook 加固 |
| 第6周+ | `v8.0.0` | 全部 | 全部 42 个问题解决、测试覆盖率 ≥80% |

---

## 5. 操作命令序列

### 5.1 初始化：创建 Worktree 和分支

```powershell
# ============================================================
# 前置条件：确保在主仓库目录执行
# ============================================================
$RepoRoot = "D:\Projects\TraeProjects\skiller"
Set-Location $RepoRoot

# ------------------------------------------------------------
# [1] 创建 develop/v8 分支和对应工作树
# ------------------------------------------------------------
git checkout -b develop/v8 main
git worktree add D:\Projects\TraeProjects\skiller-dev develop/v8

# ------------------------------------------------------------
# [2] 创建 hotfix 分支和对应工作树
# ------------------------------------------------------------
git worktree add -b hotfix D:\Projects\TraeProjects\skiller-hotfix main

# ------------------------------------------------------------
# [3] 创建 P0 紧急修复分支和对应工作树
# ------------------------------------------------------------
git worktree add -b feature/p0-fixes D:\Projects\TraeProjects\skiller-p0 develop/v8

# ------------------------------------------------------------
# [4] 创建 MCP 核心重构分支和对应工作树
# ------------------------------------------------------------
git worktree add -b feature/mcp-core D:\Projects\TraeProjects\skiller-mcp-core develop/v8

# ------------------------------------------------------------
# [5] 创建 P1 接口治理分支和对应工作树
# ------------------------------------------------------------
git worktree add -b feature/p1-api-governance D:\Projects\TraeProjects\skiller-api-gov develop/v8

# ------------------------------------------------------------
# [6] 创建渐进式加载分支和对应工作树
# ------------------------------------------------------------
git worktree add -b feature/progressive-loading D:\Projects\TraeProjects\skiller-progressive develop/v8

# ------------------------------------------------------------
# [7] 验证工作树列表
# ------------------------------------------------------------
git worktree list
```

### 5.2 修复 .gitignore 并提交规划文档

```powershell
Set-Location $RepoRoot

# ------------------------------------------------------------
# [1] 编辑 .gitignore：将 docs/ 替换为精细排除规则
#     （参考第 3 节优化方案）
# ------------------------------------------------------------
# 手动编辑 .gitignore，将末尾的:
#   docs/
# 替换为:
#   docs/_build/
#   docs/_static/
#   docs/_templates/
#   !docs/plan/

# ------------------------------------------------------------
# [2] 强制添加规划文档（之前被 docs/ 规则排除）
# ------------------------------------------------------------
git add -f .gitignore
git add -f docs/plan/REFACTOR_PLAN.md
git add -f docs/plan/ARCHITECTURE.md
git add -f docs/plan/DATABASE_DESIGN.md
git add -f docs/plan/MCP_REVIEW.md
git add -f docs/plan/SKILL_REVIEW.md
git add -f docs/plan/API_SPECIFICATION.md
git add -f docs/plan/v-git.md

# ------------------------------------------------------------
# [3] 提交
# ------------------------------------------------------------
git commit -m "chore: fix .gitignore to allow docs/plan/ and add planning docs"
```

### 5.3 P0 阶段：紧急修复工作流

```powershell
# ============================================================
# 在 P0 工作树中开发
# ============================================================
Set-Location D:\Projects\TraeProjects\skiller-p0

# 确认当前分支
git branch --show-current
# 预期输出: feature/p0-fixes

# ------------------------------------------------------------
# P0-A: 降级机制修复 (U-01)
# ------------------------------------------------------------
# 编辑 degradation.py, subprocess_utils.py, constraints.yaml 等
# ... 开发过程 ...

git add -A
git commit -m "fix(p0): implement degradation chain with script fallback (U-01)"

# ------------------------------------------------------------
# P0-B: 参考文档补充 (U-02)
# ------------------------------------------------------------
# 迁移 v1 参考文件到 v2/references/
# ... 开发过程 ...

git add -A
git commit -m "docs(p0): supplement v2 reference documents (U-02)"

# ------------------------------------------------------------
# P0-C: 状态持久化修复 (U-03)
# ------------------------------------------------------------
# 修改 degradation.py, metrics.py 等
# ... 开发过程 ...

git add -A
git commit -m "fix(p0): add atomic persistence and jitter to state management (U-03)"

# ------------------------------------------------------------
# P0 验收测试
# ------------------------------------------------------------
# 在 xuansto-mcp-server 目录执行测试
Set-Location D:\Projects\TraeProjects\skiller-p0\xuansto-mcp-server
uv run pytest tests/ -x --cov=xuansto_mcp --cov-fail-under=80 -v

# ------------------------------------------------------------
# 合并到 develop/v8
# ------------------------------------------------------------
Set-Location D:\Projects\TraeProjects\skiller-dev
git merge --no-ff feature/p0-fixes -m "merge: P0 urgent fixes (U-01, U-02, U-03)"

# 合并到 main 并打 tag
Set-Location $RepoRoot
git merge --squash develop/v8
git commit -m "release: v8.0.0-p0 - urgent fixes for degradation, docs, persistence"
git tag -a v8.0.0-p0 -m "P0: 降级机制修复、参考文档补充、状态持久化修复"

# 清理工作树
git worktree remove D:\Projects\TraeProjects\skiller-p0
git branch -d feature/p0-fixes
```

### 5.4 P1 阶段：并行开发与合并

```powershell
# ============================================================
# P1 并行开发：MCP 核心 + 接口治理
# ============================================================

# --- MCP 核心重构 ---
Set-Location D:\Projects\TraeProjects\skiller-mcp-core

# P1-A: Tool 注册解耦 (U-04)
git commit -m "refactor(p1): decouple tool registration from FastMCP internals (U-04)"

# P1-D: 降级脚本异步化 (U-09)
git commit -m "refactor(p1): async degradation script execution (U-09)"

# P1-E: Tool 职责拆分 (U-10)
git commit -m "refactor(p1): split agent_status into query/manage tools (U-10)"

# P1-F: ChromaDB 可选化 (U-08)
git commit -m "feat(p1): make ChromaDB optional with SQLite FTS5 fallback (U-08)"

# --- 接口治理 ---
Set-Location D:\Projects\TraeProjects\skiller-api-gov

# P1-B: 版本协商完善 (U-05)
git commit -m "feat(p1): complete version negotiation with feature discovery (U-05)"

# P1-C: knowledge 接口治理 (U-06)
git commit -m "refactor(p1): separate knowledge_search (read) from knowledge_inject (write) (U-06)"

# P1-G: 工具文档与暴露补全 (U-07)
git commit -m "docs(p1): complete tool documentation and add metrics_report (U-07)"

# ------------------------------------------------------------
# 合并（注意顺序：mcp-core 先合并，api-governance 后合并）
# ------------------------------------------------------------
Set-Location D:\Projects\TraeProjects\skiller-dev

# 先合并 MCP 核心
git merge --no-ff feature/mcp-core -m "merge: P1 MCP core refactoring (U-04, U-08, U-09, U-10)"

# 再合并接口治理
git merge --no-ff feature/p1-api-governance -m "merge: P1 API governance (U-05, U-06, U-07)"

# 打 tag
Set-Location $RepoRoot
git merge --squash develop/v8
git commit -m "release: v8.0.0-p1 - tool decoupling, version negotiation, knowledge governance"
git tag -a v8.0.0-p1 -m "P1: Tool注册解耦、版本协商、knowledge接口治理、降级异步化、Tool拆分、ChromaDB可选化"

# 清理
git worktree remove D:\Projects\TraeProjects\skiller-mcp-core
git worktree remove D:\Projects\TraeProjects\skiller-api-gov
git branch -d feature/mcp-core
git branch -d feature/p1-api-governance
```

### 5.5 P2 阶段：架构加固

```powershell
# ============================================================
# P2: 渐进式加载（独立工作树）+ 架构加固（develop/v8 直接提交）
# ============================================================

# --- 渐进式加载 ---
Set-Location D:\Projects\TraeProjects\skiller-progressive

# P2-D: 渐进式加载完善
git commit -m "feat(p2): implement runtime phase negotiation and DisclosureTransition (U-11, U-27, U-28, U-29)"

# P2-F: Resource 增强
git commit -m "feat(p2): add template resources and config management tool (U-19, U-22, U-23)"

# --- 架构加固（在 develop/v8 上直接提交）---
Set-Location D:\Projects\TraeProjects\skiller-dev

# P2-A: 数据层统一
git commit -m "refactor(p2): unify data layer into xuansto.db (U-14, U-15, U-16, U-18)"

# P2-B: 配置校验层
git commit -m "feat(p2): add Pydantic config validation layer (U-17)"

# P2-C: Hook 系统加固
git commit -m "refactor(p2): harden hook system with enum types and security defaults (U-13, U-20, U-25)"

# P2-E: 通知与错误治理
git commit -m "feat(p2): implement MCP notifications and unify error codes (U-21, U-30, U-31)"

# P2-G: Agent 与工作流治理
git commit -m "feat(p2): agent merging, path warning, and token estimation (U-12, U-24, U-26)"

# ------------------------------------------------------------
# 合并渐进式加载
# ------------------------------------------------------------
git merge --no-ff feature/progressive-loading -m "merge: P2 progressive loading and resource enhancement"

# 打 tag
Set-Location $RepoRoot
git merge --squash develop/v8
git commit -m "release: v8.0.0-p2 - architecture hardening and progressive loading"
git tag -a v8.0.0-p2 -m "P2: 数据层统一、配置校验、Hook加固、渐进式加载、通知治理"

# 清理
git worktree remove D:\Projects\TraeProjects\skiller-progressive
git branch -d feature/progressive-loading
```

### 5.6 P3 阶段：优化收尾

```powershell
# ============================================================
# P3: 直接在 develop/v8 上提交
# ============================================================
Set-Location D:\Projects\TraeProjects\skiller-dev

# P3-A: 文档与版本治理
git commit -m "docs(p3): migrate evals, add CHANGELOG, archive v1 (U-32~U-36)"

# P3-B: 数据模型增强
git commit -m "feat(p3): enhance data models with soft delete, LRU cache, encryption (U-37~U-41)"

# P3-C: 安全与一致性
git commit -m "feat(p3): add rate limiting, param whitelist, required actions (U-42)"

# ------------------------------------------------------------
# 最终发布
# ------------------------------------------------------------
Set-Location $RepoRoot
git merge --squash develop/v8
git commit -m "release: v8.0.0 - complete refactoring with 42 issues resolved"
git tag -a v8.0.0 -m "v8.0.0: 全部42个问题解决，测试覆盖率≥80%"

# 清理 develop 工作树（可选，保留用于后续迭代）
# git worktree remove D:\Projects\TraeProjects\skiller-dev
```

### 5.7 状态查看与日常操作

```powershell
# 查看所有工作树状态
Set-Location $RepoRoot
git worktree list

# 查看各工作树的变更状态
.\setup-worktree.ps1 -Action status

# 查看分支合并图
git log --oneline --graph --all --decorate

# 查看当前阶段待解决问题
# 参考 REFACTOR_PLAN.md 对应阶段的问题清单

# 紧急热修复流程
Set-Location D:\Projects\TraeProjects\skiller-hotfix
# ... 修复代码 ...
git commit -m "hotfix: <描述>"
Set-Location $RepoRoot
git cherry-pick <hotfix-commit-hash>
git checkout develop/v8
git cherry-pick <hotfix-commit-hash>
```

---

## 附录: 分支生命周期时间线

```
第1周    feature/p0-fixes ──────────────────────┐
                                                ▼
第2周    feature/mcp-core ─────────────────┐  develop/v8
         feature/p1-api-governance ───────┤     │
                                           │     │
第3周    feature/mcp-core ──────────────┐  │     │
         feature/p1-api-governance ─────┤  │     │
                                        ▼  ▼     │
                                    merge→develop/v8 → main (tag: v8.0.0-p0)
                                                        │
第4周    feature/progressive-loading ──┐  develop/v8    │
         P2-A/B/C/E/G 直接提交 ───────┤     │         │
                                       │     │         │
第5周    feature/progressive-loading ──┘     │         │
                                       ▼     ▼         │
                                    merge→develop/v8 → main (tag: v8.0.0-p1)
                                                        │
                                    merge→develop/v8 → main (tag: v8.0.0-p2)
                                                        │
第6周+   P3 直接在 develop/v8 提交 ──→ develop/v8 → main (tag: v8.0.0)
```
