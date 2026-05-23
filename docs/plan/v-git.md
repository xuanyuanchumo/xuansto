# Xuansto Skill Git 管理策略

> 版本: 3.0.0 | 日期: 2026-05-23 | 状态: 实施中
> 关联文档: REFACTOR_PLAN.md / .editorconfig / .gitignore(×4) / .gitattributes(缺失)

---

## 目录

1. [Git Worktree 并行开发策略](#1-git-worktree-并行开发策略)
2. [本地分支管理](#2-本地分支管理)
3. [.gitignore 合理性审查与优化](#3-gitignore-合理性审查与优化)
4. [.gitattributes 审查与优化](#4-gitattributes-审查与优化)
5. [可执行命令序列](#5-可执行命令序列)
6. [分支与重构阶段映射](#6-分支与重构阶段映射)

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
│   ├── .trae/skills/xuansto-skill/       (v5, ARCHIVED)
│   ├── .trae/skills/xuansto-skill-v2/    (v8.0.0, current)
│   ├── xuansto-mcp-server/               (MCP Server v8.0.0)
│   └── docs/plan/                        (规划文档)
│
├── skiller-dev\                      ← 开发工作树 (develop/v8 分支)
│   └── (同上结构)
│
├── skiller-hotfix\                   ← 热修复工作树 (hotfix 分支)
│   └── (同上结构)
│
├── skiller-p4\                       ← P4 收尾工作树 (feature/p4-finalization 分支)
│   └── (同上结构)
│
└── skiller-mcp-core\                 ← MCP 核心重构工作树 (feature/mcp-core 分支)
    └── (同上结构，按需创建)
```

### 1.3 Worktree 与分支对应关系

| 工作树目录 | 分支 | 用途 | 生命周期 |
|-----------|------|------|---------|
| `skiller\` | `main` | 稳定发布基线，仅接受合并 | 永久 |
| `skiller-dev\` | `develop/v8` | v8 版本开发集成分支 | 永久 |
| `skiller-hotfix\` | `hotfix` | 紧急线上修复 | 按需 |
| `skiller-p4\` | `feature/p4-finalization` | P4 v8.0.0 收尾（U-43~U-46） | 合并后删除 |

### 1.4 Worktree 管理原则

1. **一个功能一个工作树**：每个 feature 分支对应独立工作树，完成后合并并移除
2. **develop 为集成分支**：所有 feature 分支完成后合并到 `develop/v8`，经测试后合并到 `main`
3. **main 仅接受合并**：禁止在 `main` 分支上直接提交
4. **工作树及时清理**：feature 分支合并后立即执行 `git worktree remove` 和 `git branch -d`
5. **P0~P3 已完成**：对应工作树已清理，仅保留 P4 收尾工作树

---

## 2. 本地分支管理

### 2.1 分支总览

| 分支名 | 类型 | 基分支 | 创建时机 | 合并时机 | 状态 |
|--------|------|--------|---------|---------|------|
| `main` | 长期 | - | 初始化 | - | 活跃 |
| `develop/v8` | 长期 | `main` | 重构启动时 | 每阶段完成后→`main` | 活跃 |
| `feature/p4-finalization` | 短期 | `develop/v8` | P4 开始 | P4 完成后→`develop/v8` | 🔲 进行中 |
| `hotfix` | 按需 | `main` | 紧急问题时 | 修复后→`main`+`develop/v8` | 按需 |
| ~~`feature/p0-fixes`~~ | ~~短期~~ | ~~`develop/v8`~~ | ~~第1周~~ | ~~第1周末→`develop/v8`~~ | ✅ 已合并删除 |
| ~~`feature/mcp-core`~~ | ~~短期~~ | ~~`develop/v8`~~ | ~~第2周~~ | ~~第3周末→`develop/v8`~~ | ✅ 已合并删除 |
| ~~`feature/p1-api-governance`~~ | ~~短期~~ | ~~`develop/v8`~~ | ~~第2周~~ | ~~第3周末→`develop/v8`~~ | ✅ 已合并删除 |
| ~~`feature/progressive-loading`~~ | ~~短期~~ | ~~`develop/v8`~~ | ~~第4周~~ | ~~第5周末→`develop/v8`~~ | ✅ 已合并删除 |

### 2.2 分支详细说明

#### `main` — 稳定基线

- 仅接受来自 `develop/v8` 的合并和 `hotfix` 的 cherry-pick
- 每次合并打 tag：`v8.0.0-p0`、`v8.0.0-p1`、`v8.0.0-p2`、`v8.0.0` 等
- 禁止直接 push 代码到此分支

#### `develop/v8` — 开发集成

- 所有 feature 分支的汇聚点
- P2/P3 阶段小范围改动直接在此分支提交
- 合并前需通过该阶段全部验收标准

#### `feature/p4-finalization` — v8.0.0 收尾

- 对应 REFACTOR_PLAN P4 阶段
- 包含四个子任务：
  - P4-A: FALLBACK_MAP 补全 (U-43)
  - P4-B: 评估配置修正 (U-44)
  - P4-C: SKILL.md Phase 标记 (U-45)
  - P4-D: 健康检查间隔可配置 (U-46)
- 合并条件：20/20 Tool 降级路径可达、评估配置 Tool 引用全部存在、SKILL.md 行数 < 200、健康检查间隔可配置

#### `hotfix` — 紧急热修复

- 从 `main` 创建，修复后同时合并回 `main` 和 `develop/v8`
- 仅用于生产环境紧急问题，不用于常规开发

### 2.3 分支合并流程

```
feature/p4-finalization ──▶ develop/v8 ──(P4验收通过)──▶ main (tag: v8.0.0)

hotfix ──▶ main (cherry-pick to develop/v8)
```

**历史合并记录：**

```
feature/p0-fixes ──────────┐
                            ▼
feature/mcp-core ────────▶ develop/v8 ──▶ main (tag: v8.0.0-p0) ✅
                            ▲
feature/p1-api-governance ─┘
                            │
                            ──▶ main (tag: v8.0.0-p1) ✅

P2 直接提交 + feature/progressive-loading ──▶ develop/v8 ──▶ main (tag: v8.0.0-p2) ✅

P3 直接提交 ──▶ develop/v8 ──▶ main (tag: v8.0.0-p3) ✅
```

**合并规则：**

1. Feature 分支使用 `--no-ff` 合并到 `develop/v8`，保留分支历史
2. `develop/v8` 到 `main` 使用 squash merge，保持主线整洁
3. 合并前必须通过该阶段全部验收标准（见 REFACTOR_PLAN.md）
4. 合并后立即删除 feature 分支和对应 worktree

---

## 3. .gitignore 合理性审查与优化

### 3.1 审查原则

**核心规则**：只管理满足以下全部条件的文件：
1. 无法从其他源文件自动生成
2. 对项目构建/运行非必需
3. 不包含个人/机密信息

### 3.2 当前配置文件清单

| 文件路径 | 作用域 | 规则数 |
|---------|--------|--------|
| `.gitignore`（根目录） | 全仓库 | 30 条 |
| `xuansto-mcp-server/.gitignore` | MCP Server 子项目 | 50 条 |
| `.trae/skills/xuansto-skill-v2/.gitignore` | v2 Skill | 36 条 |
| `.trae/skills/xuansto-skill/.gitignore` | v1 Skill（ARCHIVED） | 37 条 |

### 3.3 根目录 `.gitignore` 分析

当前内容：

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
.trae/skills/xuansto-skill-v2/.knowledge/index/knowledge.db

.xuansto/

.venv/
.venv_test/
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
docs/_build/
docs/_static/
docs/_templates/
!docs/plan/
*.so
```

### 3.4 问题清单

| # | 问题 | 影响 | 严重度 | 建议 |
|---|------|------|--------|------|
| 1 | `.trae/skills/xuansto-skill/.knowledge/index/knowledge.db` 与 `*.db` 重复 | 冗余规则，增加理解成本 | 低 | 删除该行，`*.db` 已覆盖 |
| 2 | `.trae/skills/xuansto-skill-v2/.knowledge/index/knowledge.db` 与 `*.db` 重复 | 同上 | 低 | 删除该行，`*.db` 已覆盖 |
| 3 | v2 的 `.knowledge/temp-scripts/` 和 `.knowledge/script-errors/` 规则在根目录和 v2 自身 `.gitignore` 中重复 | 双重排除，冗余 | 低 | 根目录仅保留 `.trae/*` 的排除/保留逻辑，详细规则下沉到子目录 `.gitignore` |
| 4 | 缺少 `xuansto-mcp-server/.venv2/` 排除 | MCP Server 实际使用的 venv 目录为 `.venv2/`，但 `.gitignore` 仅排除 `.venv/` 和 `venv/` | **高** | 在 `xuansto-mcp-server/.gitignore` 添加 `.venv2/` |
| 5 | `副本/` 排除规则缺乏注释 | 不影响功能，但可读性差 | 低 | 添加注释说明用途 |
| 6 | 根目录缺少 `*.egg-info/`、`dist/`、`build/` 排除 | 子项目有独立 `.gitignore` 覆盖，但根目录未兜底 | 中 | 在根目录添加通用 Python 构建产物排除 |
| 7 | 根目录缺少 `.mypy_cache/`、`.pytest_cache/`、`.ruff_cache/` 排除 | 工具缓存目录可能被意外提交 | 中 | 在根目录添加工具缓存排除 |
| 8 | 根目录缺少 `.coverage`、`htmlcov/` 排除 | 测试覆盖率产物可能被意外提交 | 中 | 在根目录添加覆盖率产物排除 |
| 9 | v2 `.gitignore` 缺少 `.knowledge/index/chroma_db/` 排除 | ChromaDB 向量索引数据可能被意外提交（v1 有此规则） | 中 | 在 v2 `.gitignore` 添加 `.knowledge/index/chroma_db/` |

### 3.5 优化方案

#### 3.5.1 根目录 `.gitignore` 优化

```gitignore
# === Trae 平台目录 ===
.trae/*
!.trae/skills/
.trae/skills/*
!.trae/skills/xuansto-skill/
!.trae/skills/xuansto-skill-v2/

# === 运行时数据目录 ===
.xuansto/

# === Python 运行时/编译产物 ===
.venv/
.venv_test/
__pycache__/
*.py[cod]
*$py.class
*.so
*.egg-info/
*.egg
*.whl
dist/
build/
.eggs/

# === Python 工具缓存 ===
.mypy_cache/
.pytest_cache/
.ruff_cache/

# === 测试覆盖率产物 ===
.coverage
.coverage.*
htmlcov/
.tox/
.nox/
coverage.xml
*.cover
*.py,cover
.hypothesis/

# === 操作系统文件 ===
.DS_Store
Thumbs.db
._*

# === IDE/编辑器 ===
.idea/
.vscode/
*.swp
*.swo
*~

# === 环境变量/密钥 ===
.env
.env.local
.env.*.local

# === 日志 ===
*.log
logs/

# === 数据库文件 ===
*.db
*.sqlite3

# === 文档构建产物（保留 docs/plan/） ===
docs/_build/
docs/_static/
docs/_templates/
!docs/plan/

# === 临时备份目录 ===
副本/
```

**变更说明：**

| 变更项 | 原规则 | 新规则 | 理由 |
|--------|--------|--------|------|
| v1 knowledge.db 特定规则 | `.trae/skills/xuansto-skill/.knowledge/index/knowledge.db` | 删除 | `*.db` 已覆盖，消除冗余 |
| v2 knowledge.db 特定规则 | `.trae/skills/xuansto-skill-v2/.knowledge/index/knowledge.db` | 删除 | 同上 |
| v1/v2 temp-scripts、script-errors 规则 | 6 行特定路径排除 | 删除 | 子目录 `.gitignore` 已覆盖，根目录仅负责 `.trae/*` 的排除/保留 |
| Python 构建产物 | 缺失 | 新增 `*.egg-info/`、`*.egg`、`*.whl`、`dist/`、`build/`、`.eggs/` | 兜底覆盖子项目可能遗漏的构建产物 |
| 工具缓存 | 缺失 | 新增 `.mypy_cache/`、`.pytest_cache/`、`.ruff_cache/` | 防止工具缓存被意外提交 |
| 覆盖率产物 | 缺失 | 新增 `.coverage`、`htmlcov/` 等 | 防止测试覆盖率产物被意外提交 |
| 添加分类注释 | 无 | 每组规则前添加注释 | 提升可读性和可维护性 |

#### 3.5.2 `xuansto-mcp-server/.gitignore` 优化

```gitignore
# === Python 编译产物 ===
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
*.egg
*.whl
dist/
build/
.eggs/

# === 虚拟环境 ===
.venv/
.venv2/
venv/
.uv/

# === 运行时数据 ===
.xuansto/

# === Python 工具缓存 ===
.mypy_cache/
.pytest_cache/
.ruff_cache/

# === 环境变量/密钥 ===
.env
.env.local
.env.*.local

# === 数据库文件 ===
*.db
*.sqlite3

# === 日志 ===
*.log

# === 测试覆盖率 ===
.coverage
.coverage.*
htmlcov/
.tox/
.nox/
coverage.xml
*.cover
*.py,cover
.hypothesis/

# === 测试产物 ===
test_result*.txt
test_final.txt

# === 操作系统文件 ===
.DS_Store
Thumbs.db
._*

# === IDE/编辑器 ===
.idea/
.vscode/
*.swp
*.swo
*~
```

**变更说明：**

| 变更项 | 原规则 | 新规则 | 理由 |
|--------|--------|--------|------|
| `.venv2/` | 缺失 | 新增 | MCP Server 实际使用的 venv 目录为 `.venv2/` |
| 添加分类注释 | 无 | 每组规则前添加注释 | 提升可读性 |

#### 3.5.3 `.trae/skills/xuansto-skill-v2/.gitignore` 优化

```gitignore
# === Python 编译产物 ===
__pycache__/
*.py[cod]
*$py.class
*.so

# === Knowledge 运行时产物 ===
.knowledge/temp-scripts/*
!.knowledge/temp-scripts/.gitkeep
.knowledge/script-errors/*
!.knowledge/script-errors/.gitkeep
.knowledge/backup/
.knowledge/index/knowledge.db
.knowledge/index/chroma_db/

# === 数据库文件 ===
*.db
*.sqlite3

# === 日志 ===
*.log

# === 操作系统文件 ===
.DS_Store
Thumbs.db
._*

# === IDE/编辑器 ===
.idea/
.vscode/
*.swp
*.swo
*~

# === 环境变量/密钥 ===
.env
.env.local
.env.*.local

# === 临时文件 ===
*.tmp
*.temp
.cache/

# === Skill 运行时 ===
.agent_cache/
.skill-logs/

# === 前端构建产物（knowledge_server 含 JS 脚本） ===
node_modules/
dist/
build/
```

**变更说明：**

| 变更项 | 原规则 | 新规则 | 理由 |
|--------|--------|--------|------|
| `.knowledge/index/chroma_db/` | 缺失 | 新增 | ChromaDB 向量索引数据不应提交（v1 已有此规则） |
| `.knowledge/index/knowledge.db` | 缺失 | 新增 | 明确排除 knowledge.db（虽然 `*.db` 已覆盖，但显式声明更清晰） |
| 添加分类注释 | 无 | 每组规则前添加注释 | 提升可读性 |

#### 3.5.4 `.trae/skills/xuansto-skill/.gitignore`（ARCHIVED，仅记录差异）

v1 已标记 ARCHIVED，不建议修改其 `.gitignore`。仅记录与 v2 的差异供参考：

| 规则 | v1 | v2 | 说明 |
|------|----|----|------|
| `.knowledge/index/chroma_db/` | ✅ 有 | ❌ 缺（需补） | v1 已排除 ChromaDB 索引 |
| `.agent_cache/` | ❌ 无 | ✅ 有 | v2 新增 Skill 运行时缓存 |
| `.skill-logs/` | ❌ 无 | ✅ 有 | v2 新增 Skill 日志目录 |
| `node_modules/` | ❌ 无 | ✅ 有 | v2 knowledge_server 含 JS 脚本 |

### 3.6 优化后需执行的命令

> ⚠️ **注意**：当前环境 git 不可用，以下命令需在 git 可用时执行。

```powershell
# ============================================================
# 修改 .gitignore 后，清除 git 缓存中已被忽略的文件
# ============================================================
$RepoRoot = "D:\Projects\TraeProjects\skiller"
Set-Location $RepoRoot

# [1] 提交 .gitignore 变更
git add .gitignore
git add xuansto-mcp-server/.gitignore
git add .trae/skills/xuansto-skill-v2/.gitignore
git commit -m "chore: optimize .gitignore across all subprojects"

# [2] 清除已被新规则覆盖的 git 跟踪文件（不删除本地文件）
git rm -r --cached .mypy_cache/ 2>$null
git rm -r --cached .pytest_cache/ 2>$null
git rm -r --cached .ruff_cache/ 2>$null
git rm -r --cached .coverage* 2>$null
git rm -r --cached htmlcov/ 2>$null
git rm -r --cached xuansto-mcp-server/.venv2/ 2>$null
git rm -r --cached .trae/skills/xuansto-skill-v2/.knowledge/index/chroma_db/ 2>$null

# [3] 提交缓存清除
git add -A
git commit -m "chore: remove tracked files now covered by .gitignore"
```

---

## 4. .gitattributes 审查与优化

### 4.1 审查原则

**核心规则**：在仓库中显式声明所有与平台/环境/工具相关的文件行为，确保：
1. 跨平台行尾一致性（Windows CRLF vs Unix LF）
2. 二进制文件正确标记（防止 git 尝试合并二进制内容）
3. 语言/工具特定的 diff 策略
4. 与 `.editorconfig` 保持一致

### 4.2 当前状态

| 位置 | 状态 | 内容 |
|------|------|------|
| 根目录 `.gitattributes` | ❌ **缺失** | - |
| `xuansto-mcp-server/.gitattributes` | ❌ **缺失** | - |
| `.trae/skills/xuansto-skill-v2/.gitattributes` | ❌ **缺失** | - |
| `.trae/skills/xuansto-skill/.gitattributes` | ❌ **缺失** | - |
| `.trae/skills/agency-agents/.gitattributes` | ✅ 存在 | 仅 4 行（`*.md`/`*.yml`/`*.yaml`/`*.sh` text eol=lf） |

### 4.3 与 `.editorconfig` 的对齐

当前根目录 `.editorconfig` 定义：

```editorconfig
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true

[*.py]
indent_style = space
indent_size = 4

[*.{js,ts}]
indent_style = space
indent_size = 2

[*.md]
trim_trailing_whitespace = false
```

`.gitattributes` 应与 `.editorconfig` 的 `end_of_line = lf` 保持一致，在 git 层面强制执行。

### 4.4 建议的 `.gitattributes` 内容

#### 4.4.1 根目录 `.gitattributes`

```gitattributes
# === 默认行为 ===
* text=auto eol=lf

# === 文本文件（强制 LF） ===
*.py text eol=lf diff=python
*.pyx text eol=lf diff=python
*.pyi text eol=lf diff=python

*.md text eol=lf diff=markdown
*.rst text eol=lf

*.yaml text eol=lf
*.yml text eol=lf
*.json text eol=lf
*.toml text eol=lf
*.cfg text eol=lf
*.ini text eol=lf

*.js text eol=lf
*.ts text eol=lf
*.jsx text eol=lf
*.tsx text eol=lf
*.css text eol=lf
*.scss text eol=lf
*.html text eol=lf

*.sh text eol=lf
*.bash text eol=lf
*.ps1 text eol=crlf

*.xml text eol=lf
*.svg text eol=lf

*.gitignore text eol=lf
*.gitattributes text eol=lf
*.editorconfig text eol=lf

LICENSE text eol=lf

# === 二进制文件 ===
*.db binary
*.sqlite3 binary
*.so binary
*.dll binary
*.exe binary
*.pyd binary
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.ico binary
*.pdf binary
*.zip binary
*.tar binary
*.gz binary
*.whl binary
*.egg binary
*.pkl binary
*.parquet binary

# === 特殊处理 ===
*.md diff=markdown
```

#### 4.4.2 `xuansto-mcp-server/.gitattributes`

```gitattributes
# === Python 项目 ===
*.py text eol=lf diff=python
*.pyi text eol=lf diff=python
*.toml text eol=lf
*.cfg text eol=lf

# === 数据文件 ===
*.db binary
*.sqlite3 binary
*.pkl binary
*.parquet binary

# === 测试基线 ===
tests/baselines/*.json text eol=lf diff=json
```

#### 4.4.3 `.trae/skills/xuansto-skill-v2/.gitattributes`

```gitattributes
# === Skill 定义文件 ===
*.md text eol=lf diff=markdown
*.yaml text eol=lf
*.yml text eol=lf
*.json text eol=lf

# === 脚本文件 ===
*.py text eol=lf diff=python
*.js text eol=lf
*.ps1 text eol=crlf

# === Knowledge 数据 ===
*.db binary
*.sqlite3 binary

# === 模板 ===
templates/*.json text eol=lf diff=json
```

### 4.5 `.gitattributes` 设计说明

| 设计决策 | 理由 |
|---------|------|
| `* text=auto eol=lf` | 与 `.editorconfig` 的 `end_of_line = lf` 保持一致，git 层面强制 LF |
| `*.ps1 text eol=crlf` | PowerShell 脚本在 Windows 上使用 CRLF 更可靠 |
| `*.db binary` | SQLite 数据库文件必须标记为二进制，防止 git 尝试合并 |
| `*.py diff=python` | 启用 Python 语义化 diff，更易审查函数级变更 |
| `*.md diff=markdown` | 启用 Markdown 语义化 diff，忽略纯格式变更 |
| 根目录覆盖全仓库 | 子目录 `.gitattributes` 仅补充特定规则，根目录提供默认行为 |

### 4.6 创建 `.gitattributes` 的命令

> ⚠️ **注意**：当前环境 git 不可用，以下命令需在 git 可用时执行。

```powershell
$RepoRoot = "D:\Projects\TraeProjects\skiller"
Set-Location $RepoRoot

# [1] 创建根目录 .gitattributes
# （内容见 4.4.1 节，需手动创建文件）

# [2] 创建 xuansto-mcp-server/.gitattributes
# （内容见 4.4.2 节，需手动创建文件）

# [3] 创建 .trae/skills/xuansto-skill-v2/.gitattributes
# （内容见 4.4.3 节，需手动创建文件）

# [4] 提交
git add .gitattributes
git add xuansto-mcp-server/.gitattributes
git add .trae/skills/xuansto-skill-v2/.gitattributes
git commit -m "chore: add .gitattributes for cross-platform consistency"

# [5] 规范化已有文件的行尾
git add --renormalize .
git commit -m "chore: normalize line endings per .gitattributes"
```

---

## 5. 可执行命令序列

> ⚠️ **注意**：当前环境 git 不可用，以下所有命令均为文档性质，需在 git 可用时执行。

### 5.1 初始化：创建 Worktree 和分支

```powershell
$RepoRoot = "D:\Projects\TraeProjects\skiller"
Set-Location $RepoRoot

# ------------------------------------------------------------
# [1] 创建 develop/v8 分支和对应工作树（如尚未创建）
# ------------------------------------------------------------
if (-not (git branch --list "develop/v8")) {
    git checkout -b develop/v8 main
}
if (-not (Test-Path "D:\Projects\TraeProjects\skiller-dev")) {
    git worktree add D:\Projects\TraeProjects\skiller-dev develop/v8
}

# ------------------------------------------------------------
# [2] 创建 hotfix 分支和对应工作树（按需）
# ------------------------------------------------------------
# git worktree add -b hotfix D:\Projects\TraeProjects\skiller-hotfix main

# ------------------------------------------------------------
# [3] 创建 P4 收尾分支和对应工作树
# ------------------------------------------------------------
if (-not (git branch --list "feature/p4-finalization")) {
    git worktree add -b feature/p4-finalization D:\Projects\TraeProjects\skiller-p4 develop/v8
}

# ------------------------------------------------------------
# [4] 验证工作树列表
# ------------------------------------------------------------
git worktree list
```

### 5.2 应用 .gitignore 和 .gitattributes 优化

```powershell
Set-Location $RepoRoot

# ------------------------------------------------------------
# [1] 应用 .gitignore 优化（参考第 3.5 节）
# ------------------------------------------------------------
# 手动编辑以下文件：
#   - .gitignore
#   - xuansto-mcp-server/.gitignore
#   - .trae/skills/xuansto-skill-v2/.gitignore

# ------------------------------------------------------------
# [2] 创建 .gitattributes（参考第 4.4 节）
# ------------------------------------------------------------
# 手动创建以下文件：
#   - .gitattributes
#   - xuansto-mcp-server/.gitattributes
#   - .trae/skills/xuansto-skill-v2/.gitattributes

# ------------------------------------------------------------
# [3] 提交 .gitignore 变更
# ------------------------------------------------------------
git add .gitignore
git add xuansto-mcp-server/.gitignore
git add .trae/skills/xuansto-skill-v2/.gitignore
git commit -m "chore: optimize .gitignore across all subprojects"

# ------------------------------------------------------------
# [4] 提交 .gitattributes
# ------------------------------------------------------------
git add .gitattributes
git add xuansto-mcp-server/.gitattributes
git add .trae/skills/xuansto-skill-v2/.gitattributes
git commit -m "chore: add .gitattributes for cross-platform consistency"

# ------------------------------------------------------------
# [5] 清除缓存并规范化行尾
# ------------------------------------------------------------
git rm -r --cached .mypy_cache/ 2>$null
git rm -r --cached .pytest_cache/ 2>$null
git rm -r --cached .ruff_cache/ 2>$null
git rm -r --cached .coverage* 2>$null
git rm -r --cached htmlcov/ 2>$null
git rm -r --cached xuansto-mcp-server/.venv2/ 2>$null
git rm -r --cached .trae/skills/xuansto-skill-v2/.knowledge/index/chroma_db/ 2>$null
git add --renormalize .
git add -A
git commit -m "chore: remove tracked cache files and normalize line endings"
```

### 5.3 P4 阶段：v8.0.0 收尾工作流

```powershell
# ============================================================
# 在 P4 工作树中开发
# ============================================================
Set-Location D:\Projects\TraeProjects\skiller-p4

# 确认当前分支
git branch --show-current
# 预期输出: feature/p4-finalization

# ------------------------------------------------------------
# P4-A: FALLBACK_MAP 补全 (U-43)
# ------------------------------------------------------------
# 在 degradation.py 中新增 3 个降级函数
# ... 开发过程 ...

git add -A
git commit -m "feat(p4): add fallback for metrics_report, config_manage, agent_manage (U-43)"

# ------------------------------------------------------------
# P4-B: 评估配置修正 (U-44)
# ------------------------------------------------------------
# 修改 mcp_evaluation.xml，替换不存在的 Tool 引用
# ... 开发过程 ...

git add -A
git commit -m "fix(p4): correct mcp_evaluation.xml tool references (U-44)"

# ------------------------------------------------------------
# P4-C: SKILL.md Phase 标记 (U-45)
# ------------------------------------------------------------
# 在 SKILL.md 中添加 Phase 元数据标记
# ... 开发过程 ...

git add -A
git commit -m "feat(p4): add Phase metadata to SKILL.md (U-45)"

# ------------------------------------------------------------
# P4-D: 健康检查间隔可配置 (U-46)
# ------------------------------------------------------------
# 修改 DegradationManager 读取配置
# ... 开发过程 ...

git add -A
git commit -m "feat(p4): make health check interval configurable (U-46)"

# ------------------------------------------------------------
# P4 验收测试
# ------------------------------------------------------------
Set-Location D:\Projects\TraeProjects\skiller-p4\xuansto-mcp-server
uv run pytest tests/ -x --cov=xuansto_mcp --cov-fail-under=80 -v

# ------------------------------------------------------------
# 合并到 develop/v8
# ------------------------------------------------------------
Set-Location D:\Projects\TraeProjects\skiller-dev
git merge --no-ff feature/p4-finalization -m "merge: P4 v8.0.0 finalization (U-43, U-44, U-45, U-46)"

# 合并到 main 并打 tag
Set-Location $RepoRoot
git merge --squash develop/v8
git commit -m "release: v8.0.0 - complete refactoring with 46 issues resolved"
git tag -a v8.0.0 -m "v8.0.0: 全部46个问题解决，测试覆盖率≥80%"

# 清理工作树
git worktree remove D:\Projects\TraeProjects\skiller-p4
git branch -d feature/p4-finalization
```

### 5.4 紧急热修复流程

```powershell
# ============================================================
# 紧急热修复
# ============================================================
Set-Location $RepoRoot

# [1] 创建 hotfix 工作树（如尚未创建）
git worktree add -b hotfix D:\Projects\TraeProjects\skiller-hotfix main

# [2] 在 hotfix 工作树中修复
Set-Location D:\Projects\TraeProjects\skiller-hotfix
# ... 修复代码 ...
git add -A
git commit -m "hotfix: <描述>"

# [3] 合并回 main
Set-Location $RepoRoot
git cherry-pick <hotfix-commit-hash>

# [4] 同步到 develop/v8
Set-Location D:\Projects\TraeProjects\skiller-dev
git cherry-pick <hotfix-commit-hash>

# [5] 清理
git worktree remove D:\Projects\TraeProjects\skiller-hotfix
git branch -d hotfix
```

### 5.5 状态查看与日常操作

```powershell
# 查看所有工作树状态
Set-Location $RepoRoot
git worktree list

# 查看分支合并图
git log --oneline --graph --all --decorate

# 查看当前阶段待解决问题
# 参考 REFACTOR_PLAN.md 对应阶段的问题清单

# 查看 .gitattributes 是否生效
git check-attr -a -- <文件路径>

# 查看 .gitignore 规则匹配
git check-ignore -v <文件路径>

# 查看文件行尾设置
git ls-files --eol
```

---

## 6. 分支与重构阶段映射

### 6.1 映射总表

| 重构阶段 | 对应分支 | 解决问题 | 周期 | 前置依赖 | 状态 |
|---------|---------|---------|------|---------|------|
| **P0: 紧急修复** | `feature/p0-fixes` | U-01, U-02, U-03 | 第1周 | 无 | ✅ 已完成 |
| **P1-A/D/E/F: MCP 核心** | `feature/mcp-core` | U-04, U-08, U-09, U-10 | 第2-3周 | P0 | ✅ 已完成 |
| **P1-B/C/G: 接口治理** | `feature/p1-api-governance` | U-05, U-06, U-07 | 第2-3周 | P0 | ✅ 已完成 |
| **P2-A/B/C/E/G: 架构加固(上)** | `develop/v8` 直接提交 | U-11~U-18, U-20, U-24~U-26 | 第4周 | P1 | ✅ 已完成 |
| **P2-D/F: 渐进式加载** | `feature/progressive-loading` | U-19, U-22, U-23, U-27~U-29 | 第4-5周 | P1 | ✅ 已完成 |
| **P3: 优化收尾** | `develop/v8` 直接提交 | U-32~U-42 | 第6周+ | P2 | ✅ 已完成 |
| **P4: v8.0.0 收尾** | `feature/p4-finalization` | U-43, U-44, U-45, U-46 | 第7周 | P3 | 🔲 进行中 |

### 6.2 详细映射

#### P0 → `feature/p0-fixes` ✅ 已完成

| 子任务 | 统一编号 | 涉及文件 | Worktree |
|--------|---------|---------|----------|
| P0-A: 降级机制修复 | U-01 | degradation.py, subprocess_utils.py, constraints.yaml, scripts/*.py | `skiller-p0\` |
| P0-B: 参考文档补充 | U-02 | .trae/skills/xuansto-skill-v2/references/ | `skiller-p0\` |
| P0-C: 状态持久化修复 | U-03 | degradation.py (_persist_state), metrics.py, .xuansto/*.json | `skiller-p0\` |

**合并检查点**：第1周末，全部 P0 验收标准通过后合并到 `develop/v8`。

#### P1 → `feature/mcp-core` + `feature/p1-api-governance` ✅ 已完成（并行）

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

**合并检查点**：第3周末，`feature/mcp-core` 先合并，`feature/p1-api-governance` 后合并（P1-G 依赖 P1-A 的 Tool 注册表）。

#### P2 → `feature/progressive-loading` + `develop/v8` 直接提交 ✅ 已完成

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

#### P3 → `develop/v8` 直接提交 ✅ 已完成

| 子任务 | 统一编号 |
|--------|---------|
| P3-A: 文档与版本治理 | U-32, U-33, U-34, U-35, U-36 |
| P3-B: 数据模型增强 | U-37, U-38, U-39, U-40, U-41 |
| P3-C: 安全与一致性 | U-42 |

P3 为优化收尾，改动范围小且互不依赖，直接在 `develop/v8` 上提交即可。

#### P4 → `feature/p4-finalization` 🔲 进行中

| 子任务 | 统一编号 | 涉及文件 | Worktree |
|--------|---------|---------|----------|
| P4-A: FALLBACK_MAP 补全 | U-43 | degradation.py (FALLBACK_MAP), metrics_report.py, config_manage.py, agent_manage.py | `skiller-p4\` |
| P4-B: 评估配置修正 | U-44 | mcp_evaluation.xml, trigger_eval.json | `skiller-p4\` |
| P4-C: SKILL.md Phase 标记 | U-45 | SKILL.md | `skiller-p4\` |
| P4-D: 健康检查间隔可配置 | U-46 | degradation.py, config_models.py, .xuansto-config.yaml | `skiller-p4\` |

**合并检查点**：P4 全部完成后合并到 `develop/v8`，再合并到 `main` 并打 tag `v8.0.0`。

**P4 验收标准：**

| 子任务 | 验收标准 |
|--------|---------|
| P4-A | `server_health(check)` 返回 tools_count=20；MCP 不可用时 20/20 Tool 返回降级响应 |
| P4-B | 每个 qa_pair 引用的 Tool 名称在 schemas.py 中有对应 Input 定义；参数结构与 Schema 一致 |
| P4-C | SKILL.md 行数仍 < 200；Phase 标记与 resource_load_status 的 4 阶段模型一致 |
| P4-D | 修改 .xuansto-config.yaml 后 config_manage(reload) 生效；间隔范围 5s~300s；默认值 30s |

### 6.3 阶段里程碑与 Tag

| 时间点 | Tag | 包含阶段 | 验收要点 | 状态 |
|--------|-----|---------|---------|------|
| 第1周末 | `v8.0.0-p0` | P0 | 降级链可达、文档覆盖、持久化原子性 | ✅ 已完成 |
| 第3周末 | `v8.0.0-p1` | P0 + P1 | Tool 注册解耦、版本协商、knowledge 只读/只写分离 | ✅ 已完成 |
| 第5周末 | `v8.0.0-p2` | P0 + P1 + P2 | 数据层统一、渐进式加载完善、Hook 加固 | ✅ 已完成 |
| 第6周+ | `v8.0.0-p3` | P0 + P1 + P2 + P3 | 数据模型增强、安全与一致性、文档治理 | ✅ 已完成 |
| 第7周 | `v8.0.0` | 全部 | 全部 46 个问题解决、测试覆盖率 ≥80% | 🔲 进行中 |

---

## 附录 A: 分支生命周期时间线

```
第1周    feature/p0-fixes ──────────────────────┐
                                                ▼
第2周    feature/mcp-core ─────────────────┐  develop/v8
         feature/p1-api-governance ───────┤     │
                                           │     │
第3周    feature/mcp-core ──────────────┐  │     │
         feature/p1-api-governance ─────┤  │     │
                                        ▼  ▼     │
                                    merge→develop/v8 → main (tag: v8.0.0-p0) ✅
                                                        │
第4周    feature/progressive-loading ──┐  develop/v8    │
         P2-A/B/C/E/G 直接提交 ───────┤     │         │
                                       │     │         │
第5周    feature/progressive-loading ──┘     │         │
                                       ▼     ▼         │
                                    merge→develop/v8 → main (tag: v8.0.0-p1) ✅
                                                        │
                                    merge→develop/v8 → main (tag: v8.0.0-p2) ✅
                                                        │
第6周+   P3 直接在 develop/v8 提交 ──→ develop/v8 → main (tag: v8.0.0-p3) ✅
                                                        │
第7周    feature/p4-finalization ──→ develop/v8 → main (tag: v8.0.0) 🔲
```

## 附录 B: .gitignore 文件层级关系

```
根目录 .gitignore                    ← 全仓库通用规则（兜底）
├── xuansto-mcp-server/.gitignore    ← MCP Server 子项目专用规则
├── .trae/skills/xuansto-skill-v2/.gitignore  ← v2 Skill 专用规则
└── .trae/skills/xuansto-skill/.gitignore      ← v1 Skill 专用规则（ARCHIVED）
```

**层级原则：**
- 根目录 `.gitignore` 负责全仓库通用排除（Python 编译产物、IDE 文件、OS 文件等）
- 子目录 `.gitignore` 仅添加该子项目特有的排除规则
- 避免根目录和子目录 `.gitignore` 重复定义同一规则
- `.trae/*` 的排除/保留逻辑仅在根目录管理，子目录不再重复

## 附录 C: .gitattributes 文件层级关系

```
根目录 .gitattributes                    ← 全仓库默认行为（* text=auto eol=lf + 二进制声明）
├── xuansto-mcp-server/.gitattributes    ← MCP Server 特定规则（数据文件、测试基线）
└── .trae/skills/xuansto-skill-v2/.gitattributes  ← v2 Skill 特定规则（脚本行尾、Knowledge 数据）
```

**层级原则：**
- 根目录 `.gitattributes` 定义 `* text=auto eol=lf` 作为全仓库默认
- 子目录 `.gitattributes` 仅补充该子项目特有的声明
- 二进制文件声明在根目录统一管理（`*.db`、`*.so`、`*.dll` 等）
- 与 `.editorconfig` 保持一致：git 层面强制 LF，编辑器层面也强制 LF
