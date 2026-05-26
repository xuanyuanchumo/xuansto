# Git/GitHub 管理文档

> 版本：2.1.0 | 项目：xuansto-skill-v2 | 更新日期：2026-05-26
> 基线版本：Skill v8.0.0 / MCP Server v8.0.0
> 数据来源：.gitignore、.gitattributes、.github/、.editorconfig、REFACTOR_PLAN.md

---

## 目录

1. [Git Worktree 并行开发策略](#1-git-worktree-并行开发策略)
2. [本地分支管理](#2-本地分支管理)
3. [.gitignore 审查与优化](#3-gitignore-审查与优化)
4. [.gitattributes 审查与优化](#4-gitattributes-审查与优化)
5. [.git/info/exclude 本地忽略规则](#5-gitinfoexclude-本地忽略规则)
6. [.github/ 目录审查与补充](#6-github-目录审查与补充)
7. [可执行操作命令序列](#7-可执行操作命令序列)
8. [分支与 REFACTOR_PLAN.md 重构步骤映射](#8-分支与-refactor_planmd-重构步骤映射)

---

## 1. Git Worktree 并行开发策略

### 1.1 目录结构

所有 worktree 统一放置在 `c:\Users\86156\.trae-cn\worktrees\skiller\` 目录下，由 Trae 自动管理。

```
D:\Projects\TraeProjects\skiller\                    ← 主仓库（主工作树）
c:\Users\86156\.trae-cn\worktrees\skiller\            ← Trae 管理的 worktree 根目录
    ├── develop-main-branch-YzihpS\                   ← 当前活跃 worktree（develop）
    ├── feat-develop-main-branch-Akindx\              ← develop 并行开发 worktree
    └── feat-develop-main-branch-oTKP5o\              ← develop 并行开发 worktree
```

> **注**：当前所有 worktree 均基于 develop 分支，尚未创建 feature 分支的 worktree。feature 分支的 worktree 需在 Phase A 启动时按需创建。

### 1.2 Worktree 核心概念

Git Worktree 允许在同一仓库下同时检出多个分支到不同目录，实现：

- **并行开发**：同时在不同目录中开发不同功能，无需频繁切换分支
- **隔离环境**：每个 worktree 拥有独立的工作区和索引，互不干扰
- **共享 .git**：所有 worktree 共享同一个 `.git` 仓库，节省磁盘空间
- **快速验证**：在一个 worktree 中开发，在另一个 worktree 中测试集成

### 1.3 创建 Worktree 用于并行功能开发

```powershell
# 基于 develop 创建 feature/mcp-resources 的 worktree
git worktree add -b feature/mcp-resources `
    "c:\Users\86156\.trae-cn\worktrees\skiller\feat-mcp-resources-a3f1b2" `
    develop

# 基于 develop 创建 feature/audit-logger 的 worktree
git worktree add -b feature/audit-logger `
    "c:\Users\86156\.trae-cn\worktrees\skiller\feat-audit-logger-c7d4e9" `
    develop

# 基于 develop 创建 feature/persistence 的 worktree
git worktree add -b feature/persistence `
    "c:\Users\86156\.trae-cn\worktrees\skiller\feat-persistence-f2a8c5" `
    develop
```

### 1.4 Worktree 管理命令

```powershell
# 列出所有 worktree
git worktree list

# 查看指定 worktree 详情（porcelain 格式，适合脚本解析）
git worktree list --porcelain

# 移除已完成的 worktree
git worktree remove "c:\Users\86156\.trae-cn\worktrees\skiller\feat-mcp-resources-a3f1b2"

# 强制移除（有未提交更改时）
git worktree remove --force "c:\Users\86156\.trae-cn\worktrees\skiller\feat-mcp-resources-a3f1b2"

# 清理失效的 worktree 记录（目录已被手动删除时）
git worktree prune --verbose
```

### 1.5 Worktree 使用规范

1. **命名约定**：Trae 自动生成的 worktree 目录名格式为 `{type}-{branch}-{hash}/`
2. **及时清理**：分支合并后立即移除对应 worktree，避免 stale 记录
3. **避免冲突**：不同 worktree 不要修改同一文件；若必须修改，需在合并时手动解决
4. **提交前检查**：在 worktree 中提交前，确认当前分支正确 `git branch --show-current`
5. **独立环境**：每个 worktree 可独立运行 `pip install -e ".[dev]"`，互不影响

---

## 2. 本地分支管理

### 2.1 分支总览

#### 当前已存在的分支

| 分支 | 类型 | 位置 | 说明 |
|------|------|------|------|
| `main` | 长期 | 本地 + 远程 | 生产就绪代码，仅通过 release 或 hotfix 合入 |
| `develop` | 长期 | 本地 + 远程 | 开发主分支，当前工作基线 |
| `feat-add-plan-document-dsFOMQ` | 临时 | 仅远程 | Trae 自动创建的计划文档分支 |
| `feat-add-plan-document-xbkZQe` | 临时 | 仅远程 | Trae 自动创建的计划文档分支 |
| `feat-develop-main-branch-oTKP5o` | 临时 | 本地 + 远程 | Trae worktree 分支 |

#### 待创建的 feature 分支

```
main ──────────────────────────────────────────────────────────────────────►
  └─ develop ──────────────────────────────────────────────────────────────►
       │
       ├─ develop/v8 ──────────────────────────────────────────────────────► (v8.x 开发线，待创建)
       │
       ├─ feature/mcp-resources ────────┐ (Phase A, ARCH-05/MCP-02，待创建)
       │                                 └─► develop
       ├─ feature/unified-errors ───────┐ (Phase A, ARCH-11，待创建)
       │                                 └─► develop
       ├─ feature/audit-logger ─────────┐ (Phase A, MCP-03，待创建)
       │                                 └─► develop
       ├─ feature/skeleton-commands ────┐ (Phase A, SKILL-02，待创建)
       │                                 └─► develop
       │
       ├─ feature/persistence ──────────┐ (Phase B, ARCH-06/07，待创建)
       │                                 └─► develop
       ├─ feature/dual-write ───────────┐ (Phase B, DB-01/02，待创建)
       │                                 └─► develop
       ├─ feature/hook-timeout ─────────┐ (Phase B, ARCH-09，待创建)
       │                                 └─► develop
       │
       ├─ feature/config-hot-reload ────┐ (Phase C, ARCH-10，待创建)
       │                                 └─► develop
       ├─ feature/api-versioning ───────┐ (Phase C, ARCH-12，待创建)
       │                                 └─► develop
       │
       ├─ feature/progressive-loading ──┐ (Phase D, ARCH-08，待创建)
       │                                 └─► develop
       │
       └─ release/v8.1.0 ──────────────┐
                                         └─► main + develop
```

### 2.2 分支详细说明

| 分支 | 类型 | 创建时机 | 合并目标 | 对应问题 | 说明 |
|------|------|----------|----------|----------|------|
| `main` | 长期 | 初始化 | — | — | 生产就绪代码，仅通过 release 或 hotfix 合入 |
| `develop` | 长期 | 从 main 创建 | — | — | 开发主分支，当前工作基线，所有 feature 的最终归宿 |
| `develop/v8` | 长期 | 从 develop 创建（待创建） | — | — | v8.x 开发线，用于 v8 系列的长期维护和特性集成 |
| `feature/mcp-resources` | 功能 | Phase A 启动时从 develop 创建（待创建） | develop | ARCH-05, MCP-02 | Resource 推送通知实现，完善 22 个 Resource 的订阅/推送机制 |
| `feature/unified-errors` | 功能 | Phase A 启动时从 develop 创建（待创建） | develop | ARCH-11 | 统一错误处理，所有工具返回 JSON 格式 `{error, data, degradation_level, hook_errors}` |
| `feature/audit-logger` | 功能 | Phase A 启动时从 develop 创建（待创建，依赖 unified-errors） | develop | MCP-03 | 审计日志，`audit_log` 表 + 工具调用自动记录 + 90 天归档 |
| `feature/skeleton-commands` | 功能 | Phase A 启动时从 develop 创建（待创建） | develop | SKILL-02 | SKELETON 阶段可用命令 `/status`、`/help`、`/budget` |
| `feature/persistence` | 功能 | Phase B 启动时从 develop 创建（待创建） | develop | ARCH-06, ARCH-07 | Agent 持久化 + 工作流持久化，SQLite 双写过渡 + 启动恢复 |
| `feature/dual-write` | 功能 | Phase B 启动时从 develop 创建（待创建） | develop | DB-01, DB-02 | 决策双写事务保证 + ChromaDB 双写增强（重试 + 死信队列） |
| `feature/hook-timeout` | 功能 | Phase B 启动时从 develop 创建（待创建） | develop | ARCH-09 | Hook 执行超时保护（默认 30s）+ 超时后降级策略 |
| `feature/config-hot-reload` | 功能 | Phase C 启动时从 develop 创建（待创建） | develop | ARCH-10 | 配置热更新，constraints.yaml / hooks.json 变更无需重启 |
| `feature/api-versioning` | 功能 | Phase C 启动时从 develop 创建（待创建） | develop | ARCH-12 | API 版本协商，客户端声明版本→服务端返回兼容性+特性列表 |
| `feature/progressive-loading` | 功能 | Phase D 启动时从 develop 创建（待创建） | develop | ARCH-08 | Token-Phase 关联，每阶段独立预算 + 自动调整 + 降级触发 |

### 2.3 分支创建与合并时机

#### Phase A（v8.1.0）— 修复关键问题

| 分支 | 创建时机 | 合并时机 | 前置依赖 | 合并顺序 |
|------|----------|----------|----------|----------|
| `feature/unified-errors` | Phase A 启动 | ARCH-11 验收通过 | 无 | 第 1 个合并（其他分支依赖统一错误格式） |
| `feature/mcp-resources` | Phase A 启动 | ARCH-05/MCP-02 验收通过 | 无 | 第 2 个合并 |
| `feature/audit-logger` | unified-errors 合并后 | MCP-03 验收通过 | feature/unified-errors | 第 3 个合并（依赖统一错误格式） |
| `feature/skeleton-commands` | Phase A 启动 | SKILL-02 验收通过 | 无 | 可与上述并行合并 |

#### Phase B（v8.2.0）— 持久化与一致性

| 分支 | 创建时机 | 合并时机 | 前置依赖 | 合并顺序 |
|------|----------|----------|----------|----------|
| `feature/persistence` | Phase B 启动 | ARCH-06/07 验收通过 | Phase A 全部合并 | Agent→工作流顺序合并 |
| `feature/dual-write` | Phase B 启动 | DB-01/02 验收通过 | Phase A 全部合并 | 决策→ChromaDB 顺序合并 |
| `feature/hook-timeout` | Phase B 启动 | ARCH-09 验收通过 | Phase A 全部合并 | 可与上述并行合并 |

#### Phase C（v8.3.0）— 增强功能

| 分支 | 创建时机 | 合并时机 | 前置依赖 | 合并顺序 |
|------|----------|----------|----------|----------|
| `feature/config-hot-reload` | Phase C 启动 | ARCH-10 验收通过 | Phase B 全部合并 | 可与 api-versioning 并行 |
| `feature/api-versioning` | Phase C 启动 | ARCH-12 验收通过 | Phase B 全部合并 | 依赖 C2 完成后再合并 HTTP/MCP Schema 统一 |

#### Phase D（v8.4.0）— 优化

| 分支 | 创建时机 | 合并时机 | 前置依赖 | 合并顺序 |
|------|----------|----------|----------|----------|
| `feature/progressive-loading` | Phase D 启动 | ARCH-08 验收通过 | Phase C 全部合并 | 最后合并 |

### 2.4 分支保护规则

- `main`：禁止直接推送，必须通过 PR 合入；仅接受 release/* 和 hotfix/* 的合并
- `develop`：禁止强制推送，禁止 rebase 已推送的提交；所有 feature 分支必须通过 `--no-ff` 合并
- `develop/v8`：v8.x 维护线，仅接受从 develop cherry-pick 的修复
- `feature/*`：开发者可自由推送，但合并前需通过 CI 检查（lint + test + skill-validate）

---

## 3. .gitignore 审查与优化

### 3.1 当前项目根目录 .gitignore 分析

当前 `.gitignore` 共 109 行规则，逐项审查如下：

#### ✅ 良好的规则

| 规则 | 说明 |
|------|------|
| `.trae/*` / `!.trae/skills/` / `.trae/skills/*` / `!.trae/skills/xuansto-skill-v2/` | 精确控制 Trae 目录，仅跟踪 skill 目录 |
| `.xuansto/` | 排除运行时数据目录 |
| `chroma_db/` | 排除 ChromaDB 向量数据库数据 |
| `__pycache__/` / `*.py[cod]` / `*$py.class` / `*.pyo` / `*.pyc` | Python 字节码缓存排除（`*.pyc` 和 `*.pyo` 已显式声明） |
| `*.egg-info/` / `*.egg` / `*.whl` | Python 包构建产物排除（`*.egg` 已显式声明） |
| `.DS_Store` / `Thumbs.db` / `Desktop.ini` / `._*` | macOS/Windows 系统文件排除（`Desktop.ini` 已显式声明） |
| `.idea/` / `.vscode/` / `.claude/` / `.cursor/` / `.windsurf/` | 多种 IDE 配置排除 |
| `*.swp` / `*.swo` / `*~` | Vim 临时文件排除 |
| `.env` / `.env.local` / `.env.*.local` / `.env.production` | 环境变量文件保护 |
| `credentials/` / `*.pem` / `*.key` / `*.p12` / `*.pfx` / `*.jks` | 证书密钥文件保护 |
| `*.log` / `logs/` / `audit_log.jsonl` | 日志文件排除（含审计日志 JSONL） |
| `*.db` / `*.sqlite3` | 数据库文件排除 |
| `.mypy_cache/` / `.pytest_cache/` / `.ruff_cache/` | Python 工具缓存排除 |
| `htmlcov/` / `.coverage` | 覆盖率报告排除 |
| `*.bak` / `*.orig` / `*.tmp` / `*.temp` / `.cache/` | 临时/备份文件排除 |
| `node_modules/` | 前端依赖排除 |

#### ⚠️ 可优化的规则

| 规则 | 问题 | 建议 |
|------|------|------|
| `.venv/` / `.venv2/` / `.venv_test/` / `.testvenv/` | 4 条规则可合并 | 合并为 `.venv*` 一条规则 |
| `.trae/skills/xuansto-skill-v2/.knowledge/temp-scripts/*` | 路径过长，与子目录 .gitignore 重复 | 保留，根目录 .gitignore 作为全局兜底 |
| `.trae/skills/xuansto-skill-v2/.knowledge/script-errors/*` | 同上 | 保留，理由同上 |
| `.trae/skills/xuansto-skill-v2/.knowledge/index/knowledge.db` | 同上 | 保留，理由同上 |
| `.trae/skills/xuansto-skill-v2/.knowledge/backup/` | 同上 | 保留，理由同上 |

#### ❌ 缺失的规则

| 规则 | 说明 |
|------|------|
| `coverage.xml` | pytest-cov 生成的 XML 覆盖率报告 |
| `.python-version` | pyenv 版本文件（个人环境配置） |
| `pip-log.txt` | pip 安装日志 |
| `*.manifest` / `*.spec` | PyInstaller 打包产物 |
| `.eggs/` | setuptools 缓存目录 |
| `.tox/` | tox 测试环境 |
| `dist/` / `build/` | 构建产物（当前仅排除 `dist/`，`build/` 已存在但建议确认） |

> **注**：v2.0.0 版本文档中标记为缺失的 `*.egg`、`*.pyc`、`Desktop.ini` 规则，当前已在 .gitignore 中显式声明，状态已更新为 ✅。新增 `audit_log.jsonl` 规则也已包含。

### 3.2 建议的 .gitignore 优化方案

```gitignore
# ===== Trae 工作区 =====
.trae/*
!.trae/skills/
.trae/skills/*
!.trae/skills/xuansto-skill-v2/

# Skill 内部运行时数据（根级兜底）
.trae/skills/xuansto-skill-v2/.knowledge/temp-scripts/*
!.trae/skills/xuansto-skill-v2/.knowledge/temp-scripts/.gitkeep
.trae/skills/xuansto-skill-v2/.knowledge/script-errors/*
!.trae/skills/xuansto-skill-v2/.knowledge/script-errors/.gitkeep
.trae/skills/xuansto-skill-v2/.knowledge/index/knowledge.db
.trae/skills/xuansto-skill-v2/.knowledge/backup/

# ===== 运行时数据 =====
.xuansto/
chroma_db/

# ===== Python 虚拟环境（合并优化） =====
.venv*

# ===== Python 缓存与产物 =====
__pycache__/
*.py[cod]
*$py.class
*.pyo
*.pyc
*.egg-info/
*.egg
*.whl
.eggs/

# ===== 系统文件 =====
.DS_Store
Thumbs.db
Desktop.ini
._*

# ===== IDE / 编辑器 =====
.idea/
.vscode/
.claude/
.cursor/
.windsurf/
*.swp
*.swo
*~

# ===== 环境变量与密钥 =====
.env
.env.local
.env.*.local
.env.production
credentials/
*.pem
*.key
*.p12
*.pfx
*.jks

# ===== 日志 =====
*.log
logs/
audit_log.jsonl

# ===== 数据库 =====
*.db
*.sqlite3

# ===== 测试与覆盖率 =====
.mypy_cache/
.pytest_cache/
.ruff_cache/
.tox/
htmlcov/
.coverage
coverage.xml

# ===== 临时 / 备份文件 =====
*.bak
*.orig
*.tmp
*.temp
.cache/

# ===== 前端构建 =====
node_modules/
dist/
build/

# ===== 新增：Python 工具 =====
.python-version
pip-log.txt
```

### 3.3 Skill 子目录 .gitignore 审查

当前 `.trae/skills/xuansto-skill-v2/.gitignore` 共 35 行规则，与根目录 .gitignore 存在大量重复。子目录 .gitignore 的价值在于：当 skill 目录被单独分发时仍能正确忽略文件。

| 规则 | 状态 | 说明 |
|------|------|------|
| `__pycache__/` / `*.py[cod]` / `*$py.class` / `*.so` | ✅ | Python 缓存，独立分发时必需 |
| `.knowledge/temp-scripts/*` / `!.knowledge/temp-scripts/.gitkeep` | ✅ | Skill 专属临时脚本 |
| `.knowledge/script-errors/*` / `!.knowledge/script-errors/.gitkeep` | ✅ | Skill 专属错误日志 |
| `.knowledge/backup/` | ✅ | Skill 专属备份 |
| `*.db` / `*.sqlite3` / `*.log` | ✅ | 数据库和日志 |
| `.DS_Store` / `Thumbs.db` / `._*` | ✅ | 系统文件 |
| `.idea/` / `.vscode/` / `*.swp` / `*.swo` / `*~` | ✅ | IDE 文件 |
| `.env` / `.env.local` / `.env.*.local` | ✅ | 环境变量 |
| `*.tmp` / `*.temp` / `.cache/` | ✅ | 临时文件 |
| `node_modules/` / `dist/` / `build/` | ✅ | 构建产物 |

**建议**：子目录 .gitignore 保持现状，重复是合理的（独立分发保障）。

### 3.4 .gitignore 管理原则

只让 Git 管理满足以下**全部条件**的文件：

1. **不可再生**：无法从其他源文件直接生成
2. **项目必需**：对项目构建和运行必不可少
3. **无安全风险**：不包含个人或机密信息

| 类别 | 排除规则 | 原因 |
|------|----------|------|
| Python 缓存 | `__pycache__/`、`*.pyc`、`*.pyo` | 可自动生成 |
| 环境变量 | `.env`、`.env.local` | 包含密钥 |
| 依赖目录 | `node_modules/` | 可通过包管理器恢复 |
| 构建产物 | `dist/`、`build/`、`*.egg-info/` | 可自动构建 |
| 运行时数据 | `.xuansto/` | 运行时产生，非源码 |
| 向量数据库 | `chroma_db/` | 可重建的索引数据 |
| IDE 配置 | `.idea/`、`.vscode/` | 个人环境配置 |
| 测试缓存 | `.pytest_cache/`、`.mypy_cache/` | 可自动生成 |
| 证书密钥 | `*.pem`、`*.key`、`credentials/` | 安全风险 |
| 审计日志 | `audit_log.jsonl` | 运行时产生，可重建 |

---

## 4. .gitattributes 审查与优化

### 4.1 当前 .gitattributes 分析

当前根目录 `.gitattributes` 共 144 行规则，覆盖面非常全面：

#### ✅ 良好的规则

| 类别 | 规则 | 说明 |
|------|------|------|
| 默认行为 | `* text=auto eol=lf` | 自动检测文本文件，统一 LF 行尾 |
| Python | `*.py` / `*.pyx` / `*.pyi` text eol=lf diff=python | 完整覆盖 Python 文件类型 |
| 文档 | `*.md` diff=markdown / `*.rst` | Markdown 有 diff 驱动 |
| 配置文件 | `*.yaml` / `*.yml` / `*.json` text eol=lf diff=yaml/json **merge=union** | 7 种配置格式全覆盖，YAML/JSON 已添加 union 合并策略 |
| 前端 | `*.js` / `*.ts` / `*.jsx` / `*.tsx` / `*.css` / `*.scss` / `*.html` | 完整前端文件类型 |
| Shell/脚本 | `*.sh` / `*.bash` eol=lf / `*.bat` / `*.cmd` / `*.ps1` eol=crlf | 正确区分 Unix/Windows 脚本行尾 |
| 标记语言 | `*.xml` / `*.svg` | XML 系列文件 |
| Git 元文件 | `*.gitignore` / `*.gitattributes` / `*.editorconfig` / `.git-blame-ignore-revs` | Git 自身配置文件 |
| 锁文件 | `*.lock merge=union` | 锁文件使用 union 合并策略 |
| 补丁 | `*.patch text eol=lf` | 补丁文件 |
| 许可证 | `LICENSE text eol=lf` | 许可证文件 |
| 二进制文件 | 20+ 种二进制格式（含 `.woff` / `.eot`） | 覆盖数据库、图片、压缩包、字体、音视频等 |
| 特殊合并 | `resource_state.json merge=union` | 资源状态文件使用 union 合并 |
| Linguist | `*.min.js` / `*.min.css` / `package-lock.json` / `yarn.lock` / `pnpm-lock.yaml` linguist-generated | 标记生成文件，排除语言统计 |

> **注**：v2.0.0 版本文档中标记为缺失的 `constraints.yaml merge=union` 和 `hooks.json merge=union`，当前已通过 `*.yaml merge=union` 和 `*.json merge=union` 全局规则覆盖，无需单独添加。

#### ⚠️ 可优化的规则

| 规则 | 问题 | 建议 |
|------|------|------|
| 无 Dockerfile 规则 | 项目可能引入 Docker | 添加 `Dockerfile text eol=lf` |
| 无 docker-compose 规则 | 同上 | 添加 `docker-compose*.yml text eol=lf diff=yaml` |
| 无 `requirements*.txt` 规则 | pip 依赖文件 | 添加 `requirements*.txt text eol=lf` |
| 无 `.env.example` diff 规则 | 当前仅 `text eol=lf` | 可添加 `diff=yaml` 或保持现状 |

#### ❌ 缺失的规则

| 规则 | 说明 |
|------|------|
| `Dockerfile text eol=lf` | Docker 构建文件 |
| `docker-compose*.yml text eol=lf diff=yaml` | Docker Compose 配置 |
| `requirements*.txt text eol=lf` | pip 依赖锁定文件 |
| `*.sql text eol=lf` | SQL 脚本 |
| `*.csv text eol=lf` | CSV 数据文件 |
| `*.tsv text eol=lf` | TSV 数据文件 |
| `*.7z binary` / `*.rar binary` | 额外压缩格式 |
| `*.npy binary` / `*.npz binary` | NumPy 数据文件 |
| `*.h5 binary` / `*.safetensors binary` | ML 模型文件 |

### 4.2 建议的 .gitattributes 优化方案

```gitattributes
# ===== 默认行为 =====
* text=auto eol=lf

# ===== Python =====
*.py text eol=lf diff=python
*.pyx text eol=lf diff=python
*.pyi text eol=lf diff=python

# ===== 文档 =====
*.md text eol=lf diff=markdown
*.rst text eol=lf

# ===== 配置文件 =====
*.yaml text eol=lf diff=yaml merge=union
*.yml text eol=lf diff=yaml merge=union
*.json text eol=lf diff=json merge=union
*.toml text eol=lf diff=toml
*.cfg text eol=lf
*.ini text eol=lf
*.conf text eol=lf

# ===== 前端 =====
*.js text eol=lf diff=javascript
*.ts text eol=lf diff=typescript
*.jsx text eol=lf diff=javascript
*.tsx text eol=lf diff=typescript
*.css text eol=lf diff=css
*.scss text eol=lf
*.html text eol=lf

# ===== Shell / 脚本 =====
*.sh text eol=lf
*.bash text eol=lf
*.bat text eol=crlf
*.cmd text eol=crlf
*.ps1 text eol=crlf

# ===== 标记语言 =====
*.xml text eol=lf
*.svg text eol=lf

# ===== 数据文件 =====
*.sql text eol=lf
*.csv text eol=lf
*.tsv text eol=lf

# ===== Docker =====
Dockerfile text eol=lf
docker-compose*.yml text eol=lf diff=yaml

# ===== Python 依赖 =====
requirements*.txt text eol=lf

# ===== Git 元文件 =====
*.gitignore text eol=lf
*.gitattributes text eol=lf
*.editorconfig text eol=lf
.git-blame-ignore-revs text eol=lf

# ===== 锁文件与补丁 =====
*.lock text eol=lf merge=union
*.patch text eol=lf
*.env.example text eol=lf

# ===== 许可证 =====
LICENSE text eol=lf

# ===== 二进制文件 =====
*.db binary
*.sqlite3 binary
*.so binary
*.dll binary
*.exe binary
*.pyd binary
*.wasm binary
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.ico binary
*.webp binary
*.pdf binary
*.zip binary
*.tar binary
*.gz binary
*.whl binary
*.egg binary
*.pkl binary
*.parquet binary
*.woff2 binary
*.woff binary
*.ttf binary
*.otf binary
*.eot binary
*.mp4 binary
*.mp3 binary
*.7z binary
*.rar binary
*.bz2 binary
*.xz binary
*.npy binary
*.npz binary
*.h5 binary
*.safetensors binary

# ===== 特殊合并策略 =====
resource_state.json merge=union

# ===== Linguist: generated files =====
*.min.js linguist-generated
*.min.css linguist-generated
package-lock.json linguist-generated
yarn.lock linguist-generated
pnpm-lock.yaml linguist-generated
```

### 4.3 Skill 子目录 .gitattributes 审查

当前 `.trae/skills/xuansto-skill-v2/.gitattributes` 共 11 行，是根目录的子集：

```
*.md text eol=lf diff=markdown
*.yaml text eol=lf
*.yml text eol=lf
*.json text eol=lf
*.py text eol=lf diff=python
*.js text eol=lf
*.ps1 text eol=crlf
*.db binary
*.sqlite3 binary
```

**评估**：作为独立分发的 skill 目录，覆盖了核心文件类型，但缺少 `*.toml`、`*.lock merge=union`、`resource_state.json merge=union` 等规则。

**建议**：补充以下规则到 skill 子目录：

```gitattributes
*.toml text eol=lf diff=toml
*.lock text eol=lf merge=union
resource_state.json merge=union
constraints.yaml merge=union
```

---

## 5. .git/info/exclude 本地忽略规则

`.git/info/exclude` 是仅对本地生效的忽略文件，不会被提交到仓库，适合存放个人偏好规则。

### 5.1 当前 .git-info-exclude-template 模板文件

项目根目录已提供 `.git-info-exclude-template` 模板文件，当前内容如下：

```gitignore
# Git local exclude rules
# This file is NOT tracked by git - add your personal ignore patterns here
# These rules only apply to your local repository
#
# INSTALL: Copy this file to your git info directory:
#   For worktree: copy .git-info-exclude-template to <gitdir>/info/exclude
#   For regular repo: copy .git-info-exclude-template to .git/info/exclude

# Editor-specific
*.sublime-project
*.sublime-workspace

# OS-specific
desktop.ini

# Local development overrides
docker-compose.override.yml
.local/

# Debug files
*.pyc
debug/
```

### 5.2 建议的增强配置

当前模板较为简洁，建议补充以下规则：

```gitignore
# Git local exclude rules
# This file is NOT tracked by git - add your personal ignore patterns here
# These rules only apply to your local repository
#
# INSTALL: Copy this file to your git info directory:
#   For worktree: copy .git-info-exclude-template to <gitdir>/info/exclude
#   For regular repo: copy .git-info-exclude-template to .git/info/exclude

# ===== Editor-specific =====
*.sublime-project
*.sublime-workspace
*.swp
*.swo
*~

# ===== OS-specific =====
desktop.ini
Desktop.ini
ehthumbs.db

# ===== Local development overrides =====
docker-compose.override.yml
.local/

# ===== Debug files =====
*.pyc
debug/
debug_*.py
test_local_*.py
scratch_*.py

# ===== Personal notes =====
NOTES.md
TODO_PERSONAL.md

# ===== Large file temporary storage =====
*.dump
*.prof
*.heap

# ===== Local experimental configs =====
local_*.yaml
local_*.json
local_*.toml

# ===== Personal Python version =====
.python-version

# ===== Personal toolchain =====
.tool-versions
```

### 5.3 设置命令（PowerShell）

```powershell
# 方法 1：从模板复制
Copy-Item ".git-info-exclude-template" ".git/info/exclude"

# 方法 2：直接写入
@"
# Editor-specific
*.sublime-project
*.sublime-workspace
*.swp
*.swo
*~

# OS-specific
desktop.ini
Desktop.ini
ehthumbs.db

# Local development overrides
docker-compose.override.yml
.local/

# Debug files
*.pyc
debug/
debug_*.py
test_local_*.py
scratch_*.py

# Personal notes
NOTES.md
TODO_PERSONAL.md

# Large file temporary storage
*.dump
*.prof
*.heap

# Local experimental configs
local_*.yaml
local_*.json
local_*.toml

# Personal Python version
.python-version

# Personal toolchain
.tool-versions
"@ | Set-Content -Path ".git\info\exclude" -Encoding UTF8
```

---

## 6. .github/ 目录审查与补充

### 6.1 当前目录结构

```
.github/
├── ISSUE_TEMPLATE/
│   ├── bug_report.yml          # Bug 报告模板
│   ├── config.yml              # Issue 模板配置
│   └── feature_request.yml     # 功能请求模板
├── workflows/
│   ├── ci.yml                  # CI 流水线
│   └── release.yml             # 发布流水线 ✅ (v2.1.0 已确认存在)
├── dependabot.yml              # 依赖自动更新 ✅ (v2.1.0 已确认存在)
├── FUNDING.yml                 # 赞助配置
└── PULL_REQUEST_TEMPLATE.md    # PR 模板

项目根目录（GitHub 同样支持）：
├── CODEOWNERS                  # 代码所有者 ✅ (v2.1.0 已确认存在)
└── SECURITY.md                 # 安全策略 ✅ (v2.1.0 已确认存在)
```

> **注**：`CODEOWNERS` 和 `SECURITY.md` 放置在项目根目录而非 `.github/` 目录下，GitHub 两种位置均支持。

### 6.2 现有文件审查

#### ci.yml

当前 CI 流水线包含 4 个 Job：

| Job | 触发条件 | 运行环境 | 评估 |
|-----|----------|----------|------|
| `lint` | push/PR 到 main/develop/develop/v8/refactor/** | ubuntu-latest, Python 3.11 | ✅ ruff check + mypy |
| `test` | lint 通过后 | ubuntu-latest, Python 3.10/3.11/3.12 矩阵 | ✅ pytest + coverage |
| `degradation-test` | 定时调度（每日 06:00 UTC） | ubuntu-latest, Python 3.11 | ✅ 降级链专项测试 |
| `skill-validate` | push/PR | ubuntu-latest, Python 3.11 | ✅ YAML/JSON 格式校验 |

**改进建议**：

1. **添加 Schema 验证步骤**：当前 skill-validate 仅做 YAML/JSON 格式校验，应增加结构化验证（constraints.yaml Token 预算范围、routes.yaml 命令完整性等）
2. **添加 MCP 定义验证步骤**：验证工具数量（20 个）、Resource 数量（≥22 个）、inputSchema 完整性
3. **添加缓存优化**：当前已有 pip 缓存，可增加 venv 缓存加速安装
4. **添加路径过滤**：push 触发已有 paths 过滤，但 PR 触发缺少
5. **mypy 应非容忍失败**：当前 `mypy ... || true` 允许类型检查失败通过，建议逐步收紧

#### release.yml

当前发布流水线包含 3 个 Job：

| Job | 触发条件 | 运行环境 | 评估 |
|-----|----------|----------|------|
| `build` | push tag `v*` | ubuntu-latest, Python 3.11 | ✅ pip 缓存 + build 包 + 上传 artifact |
| `release` | build 通过后 | ubuntu-latest | ✅ 下载 artifact + 创建 GitHub Release（含 prerelease 检测） |
| `publish-pypi` | build 通过后 + 非 rc/beta/alpha tag | ubuntu-latest | ✅ PyPI 发布（trusted publisher） |

**评估**：比 v2.0.0 文档建议的方案更完善，增加了 PyPI 发布和 prerelease 自动检测。

#### dependabot.yml

当前依赖更新配置：

| 生态系统 | 目录 | 更新频率 | PR 限制 | 评估 |
|----------|------|----------|---------|------|
| pip | `/xuansto-mcp-server` | 每周一 06:00 | 5 | ✅ |
| github-actions | `/` | 每周一 06:00 | 5 | ✅ |

**评估**：比 v2.0.0 文档建议的方案更细致，增加了 `time: "06:00"` 和 `python` 标签，github-actions PR 限制从 3 提升到 5。

#### bug_report.yml

当前模板字段评估：

| 字段 | 类型 | 评估 | 改进建议 |
|------|------|------|----------|
| Component | checkboxes | ✅ 覆盖 5 个组件 | — |
| Severity | dropdown | ✅ P0-P3 | — |
| Version | dropdown | ⚠️ 仅 v8.0.0-dev / v7.x / other | 需随发布添加 v8.1.0、v8.2.0 等 |
| Bug Description | textarea | ✅ 必填 | — |
| Steps to Reproduce | textarea | ✅ 必填 | — |
| Expected Behavior | textarea | ✅ 必填 | — |
| Actual Behavior | textarea | ✅ 必填 | — |
| Reproduction Frequency | dropdown | ✅ | — |
| Degradation Impact | checkboxes | ✅ 降级链影响评估 | — |
| Environment | textarea | ✅ | — |
| Relevant Logs | textarea | ✅ shell 渲染 | — |

#### feature_request.yml

当前模板字段评估均为 ✅，特别是 `Related UNIFIED Issue` 和 `Target Progressive Loading Phase` 字段与 REFACTOR_PLAN.md 对齐。

#### config.yml

- `blank_issues_enabled: false` ✅
- 3 个联系链接（Documentation / Discussions / Security Policy）✅

#### PULL_REQUEST_TEMPLATE.md

| 区块 | 评估 | 改进建议 |
|------|------|----------|
| Description | ✅ | — |
| Type of Change | ✅ 含 8 种变更类型 | — |
| Component | ✅ 含 5 个组件 | — |
| Related Issues | ✅ | — |
| UNIFIED Issue | ✅ | — |
| Testing | ✅ 含 5 种测试类型 | — |
| Breaking Changes | ✅ | — |
| Checklist | ✅ 含 4 项检查 | 可添加"性能影响评估"和"文档已更新" |

#### FUNDING.yml

当前配置 `custom: ['https://github.com/xuanyuanchumo/xuansto']` ✅，指向项目仓库。

#### CODEOWNERS（根目录）

当前配置覆盖以下目录：

| 路径 | 所有者 |
|------|--------|
| `*`（默认） | `@xuanyuanchumo` |
| `/xuansto-mcp-server/` | `@xuanyuanchumo` |
| `/.trae/skills/xuansto-skill-v2/agents/` | `@xuanyuanchumo` |
| `/.trae/skills/xuansto-skill-v2/commands/` | `@xuanyuanchumo` |
| `/.trae/skills/xuansto-skill-v2/configs/` | `@xuanyuanchumo` |
| `/.trae/skills/xuansto-skill-v2/scripts/` | `@xuanyuanchumo` |
| `/.trae/skills/xuansto-skill-v2/references/` | `@xuanyuanchumo` |
| `/.github/` | `@xuanyuanchumo` |
| `/docs/` | `@xuanyuanchumo` |
| `/xuansto-mcp-server/pyproject.toml` | `@xuanyuanchumo` |

**评估**：比 v2.0.0 文档建议的方案更细化，按 skill 子目录分别指定了所有者。

#### SECURITY.md（根目录）

当前安全策略内容：

| 区块 | 评估 | 说明 |
|------|------|------|
| Supported Versions | ✅ | 8.x 支持，< 8.0 不支持 |
| How to Report | ✅ | GitHub Security Advisory + 邮件 |
| What to Include | ✅ | 漏洞描述、复现步骤、影响、建议修复 |
| Response Timeline | ✅ | 48h 确认，5 工作日评估 |
| Disclosure Policy | ✅ | 负责任披露 |
| Security Best Practices | ✅ | 5 条安全建议 |

**评估**：比 v2.0.0 文档建议的方案更完善，增加了 Disclosure Policy 和更详细的 Best Practices。

### 6.3 当前 .github/ 目录完整性评估

| 文件 | 状态 | 位置 | 说明 |
|------|------|------|------|
| `ISSUE_TEMPLATE/bug_report.yml` | ✅ 已存在 | `.github/` | Bug 报告模板 |
| `ISSUE_TEMPLATE/config.yml` | ✅ 已存在 | `.github/` | Issue 模板配置 |
| `ISSUE_TEMPLATE/feature_request.yml` | ✅ 已存在 | `.github/` | 功能请求模板 |
| `workflows/ci.yml` | ✅ 已存在 | `.github/` | CI 流水线 |
| `workflows/release.yml` | ✅ 已存在 | `.github/` | 发布流水线（含 PyPI 发布） |
| `dependabot.yml` | ✅ 已存在 | `.github/` | 依赖自动更新 |
| `FUNDING.yml` | ✅ 已存在 | `.github/` | 赞助配置 |
| `PULL_REQUEST_TEMPLATE.md` | ✅ 已存在 | `.github/` | PR 模板 |
| `CODEOWNERS` | ✅ 已存在 | 根目录 | 代码所有者 |
| `SECURITY.md` | ✅ 已存在 | 根目录 | 安全策略 |

**结论**：v2.0.0 文档建议补充的所有文件均已存在，.github/ 目录结构完整。

### 6.4 仍需改进的项目

| 项目 | 当前状态 | 改进建议 |
|------|----------|----------|
| bug_report.yml 版本选项 | 仅 v8.0.0-dev / v7.x | 随版本发布更新选项列表 |
| ci.yml mypy 容忍失败 | `mypy ... \|\| true` | 逐步收紧为严格检查 |
| ci.yml PR 路径过滤 | PR 触发缺少 paths 过滤 | 添加 paths 过滤减少不必要的 CI 运行 |
| ci.yml Schema 验证 | 仅 YAML/JSON 格式校验 | 添加结构化验证步骤 |
| PULL_REQUEST_TEMPLATE.md | Checklist 4 项 | 可添加"性能影响评估"和"文档已更新" |

---

## 7. 可执行操作命令序列

以下所有命令均为 Windows PowerShell 兼容格式。

### 7.1 创建 Worktree

```powershell
# 进入主仓库
Set-Location "D:\Projects\TraeProjects\skiller"

# 确保 develop 分支最新
git checkout develop
git pull origin develop

# ===== Phase A: 创建 4 个 feature 分支的 worktree =====

# feature/mcp-resources (ARCH-05/MCP-02)
git worktree add -b feature/mcp-resources `
    "c:\Users\86156\.trae-cn\worktrees\skiller\feat-mcp-resources-a3f1b2" `
    develop

# feature/unified-errors (ARCH-11)
git worktree add -b feature/unified-errors `
    "c:\Users\86156\.trae-cn\worktrees\skiller\feat-unified-errors-b5e7c3" `
    develop

# feature/audit-logger (MCP-03) — 依赖 unified-errors，先创建但后开发
git worktree add -b feature/audit-logger `
    "c:\Users\86156\.trae-cn\worktrees\skiller\feat-audit-logger-c7d4e9" `
    develop

# feature/skeleton-commands (SKILL-02)
git worktree add -b feature/skeleton-commands `
    "c:\Users\86156\.trae-cn\worktrees\skiller\feat-skeleton-commands-d1f6a4" `
    develop

# ===== Phase B: 创建 3 个 feature 分支的 worktree =====

# feature/persistence (ARCH-06/07)
git worktree add -b feature/persistence `
    "c:\Users\86156\.trae-cn\worktrees\skiller\feat-persistence-f2a8c5" `
    develop

# feature/dual-write (DB-01/02)
git worktree add -b feature/dual-write `
    "c:\Users\86156\.trae-cn\worktrees\skiller\feat-dual-write-g9b3d7" `
    develop

# feature/hook-timeout (ARCH-09)
git worktree add -b feature/hook-timeout `
    "c:\Users\86156\.trae-cn\worktrees\skiller\feat-hook-timeout-h4c2e8" `
    develop

# ===== Phase C: 创建 2 个 feature 分支的 worktree =====

# feature/config-hot-reload (ARCH-10)
git worktree add -b feature/config-hot-reload `
    "c:\Users\86156\.trae-cn\worktrees\skiller\feat-config-hot-reload-j6d5f1" `
    develop

# feature/api-versioning (ARCH-12)
git worktree add -b feature/api-versioning `
    "c:\Users\86156\.trae-cn\worktrees\skiller\feat-api-versioning-k8e7a3" `
    develop

# ===== Phase D: 创建 1 个 feature 分支的 worktree =====

# feature/progressive-loading (ARCH-08)
git worktree add -b feature/progressive-loading `
    "c:\Users\86156\.trae-cn\worktrees\skiller\feat-progressive-loading-l2f9b5" `
    develop

# 验证所有 worktree
git worktree list
```

### 7.2 创建 Feature 分支（不使用 Worktree）

```powershell
# 从 develop 创建 feature 分支
git checkout develop
git pull origin develop

git branch feature/mcp-resources develop
git branch feature/unified-errors develop
git branch feature/audit-logger develop
git branch feature/skeleton-commands develop
git branch feature/persistence develop
git branch feature/dual-write develop
git branch feature/hook-timeout develop
git branch feature/config-hot-reload develop
git branch feature/api-versioning develop
git branch feature/progressive-loading develop

# 创建 develop/v8 长期分支
git branch develop/v8 develop

# 推送所有分支到远程
git push origin --all
```

### 7.3 合并 Feature 分支

```powershell
# ===== Phase A 合并顺序 =====

# 1. 合并 feature/unified-errors（其他分支依赖统一错误格式）
git checkout develop
git pull origin develop
git merge --no-ff feature/unified-errors -m "merge: Phase A - ARCH-11 统一错误处理"

# 2. 合并 feature/mcp-resources
git merge --no-ff feature/mcp-resources -m "merge: Phase A - ARCH-05/MCP-02 Resource 推送通知"

# 3. 合并 feature/audit-logger（依赖 unified-errors）
git merge --no-ff feature/audit-logger -m "merge: Phase A - MCP-03 审计日志"

# 4. 合并 feature/skeleton-commands
git merge --no-ff feature/skeleton-commands -m "merge: Phase A - SKILL-02 SKELETON 命令"

# ===== Phase B 合并顺序 =====

# 5. 合并 feature/persistence
git merge --no-ff feature/persistence -m "merge: Phase B - ARCH-06/07 Agent/工作流持久化"

# 6. 合并 feature/dual-write
git merge --no-ff feature/dual-write -m "merge: Phase B - DB-01/02 双写一致性"

# 7. 合并 feature/hook-timeout
git merge --no-ff feature/hook-timeout -m "merge: Phase B - ARCH-09 Hook 超时保护"

# ===== Phase C 合并顺序 =====

# 8. 合并 feature/config-hot-reload
git merge --no-ff feature/config-hot-reload -m "merge: Phase C - ARCH-10 配置热更新"

# 9. 合并 feature/api-versioning
git merge --no-ff feature/api-versioning -m "merge: Phase C - ARCH-12 API 版本协商"

# ===== Phase D 合并顺序 =====

# 10. 合并 feature/progressive-loading
git merge --no-ff feature/progressive-loading -m "merge: Phase D - ARCH-08 Token-Phase 关联"

# 推送 develop
git push origin develop
```

### 7.4 标记发布版本

```powershell
# ===== v8.1.0 发布（Phase A 完成） =====

# 创建 release 分支
git checkout -b release/v8.1.0 develop

# 在 release 分支上修复版本号
# ... 修改 pyproject.toml 版本号等 ...

git add .
git commit -m "chore: bump version to v8.1.0"

# 合并到 main
git checkout main
git merge --no-ff release/v8.1.0 -m "release: v8.1.0 - 修复关键问题"
git tag -a v8.1.0 -m "Release v8.1.0: ARCH-05 Resource推送 + ARCH-11 统一错误 + MCP-03 审计日志 + SKILL-02 SKELETON命令"

# 合并回 develop
git checkout develop
git merge --no-ff release/v8.1.0

# 推送
git push origin main develop --tags

# 清理
git branch -d release/v8.1.0

# ===== v8.2.0 发布（Phase B 完成） =====
git checkout -b release/v8.2.0 develop
git add .
git commit -m "chore: bump version to v8.2.0"
git checkout main
git merge --no-ff release/v8.2.0 -m "release: v8.2.0 - 持久化与一致性"
git tag -a v8.2.0 -m "Release v8.2.0: ARCH-06/07 持久化 + DB-01/02 双写 + ARCH-09 Hook超时"
git checkout develop
git merge --no-ff release/v8.2.0
git push origin main develop --tags
git branch -d release/v8.2.0

# ===== v8.3.0 发布（Phase C 完成） =====
git checkout -b release/v8.3.0 develop
git add .
git commit -m "chore: bump version to v8.3.0"
git checkout main
git merge --no-ff release/v8.3.0 -m "release: v8.3.0 - 增强功能"
git tag -a v8.3.0 -m "Release v8.3.0: ARCH-10 配置热更新 + ARCH-12 API版本协商"
git checkout develop
git merge --no-ff release/v8.3.0
git push origin main develop --tags
git branch -d release/v8.3.0

# ===== v8.4.0 发布（Phase D 完成） =====
git checkout -b release/v8.4.0 develop
git add .
git commit -m "chore: bump version to v8.4.0"
git checkout main
git merge --no-ff release/v8.4.0 -m "release: v8.4.0 - 优化"
git tag -a v8.4.0 -m "Release v8.4.0: ARCH-08 Token-Phase关联 + 渐进式加载增强 + 性能指标"
git checkout develop
git merge --no-ff release/v8.4.0
git push origin main develop --tags
git branch -d release/v8.4.0
```

### 7.5 清理 Worktree 和已合并分支

```powershell
# 移除已合并的 worktree
git worktree remove "c:\Users\86156\.trae-cn\worktrees\skiller\feat-unified-errors-b5e7c3"
git worktree remove "c:\Users\86156\.trae-cn\worktrees\skiller\feat-mcp-resources-a3f1b2"
git worktree remove "c:\Users\86156\.trae-cn\worktrees\skiller\feat-audit-logger-c7d4e9"
git worktree remove "c:\Users\86156\.trae-cn\worktrees\skiller\feat-skeleton-commands-d1f6a4"

# 删除已合并的本地 feature 分支
git branch -d feature/unified-errors
git branch -d feature/mcp-resources
git branch -d feature/audit-logger
git branch -d feature/skeleton-commands

# 删除远程 feature 分支
git push origin --delete feature/unified-errors
git push origin --delete feature/mcp-resources
git push origin --delete feature/audit-logger
git push origin --delete feature/skeleton-commands

# 清理失效的 worktree 记录
git worktree prune --verbose
```

### 7.6 更新 .gitignore 和 .gitattributes 后刷新索引

```powershell
# 更新 .gitignore 后刷新 Git 索引
git rm -r --cached .
git add .
git commit -m "chore: update .gitignore rules"

# 更新 .gitattributes 后规范化已有文件的行尾
git rm --cached -r .
git reset --hard
```

---

## 8. 分支与 REFACTOR_PLAN.md 重构步骤映射

> **重要更新**：REFACTOR_PLAN.md 中所有 32 项问题（除 P3-01 Open 和 P3-02 Deferred 外）均已标记为 ✅ Fixed。以下分支映射仍作为开发策略参考，但实际实现可能已在 develop 分支上直接完成，无需创建独立 feature 分支。

### 8.1 Phase A（v8.1.0）— 修复关键问题

| 重构步骤 | 问题 ID | 状态 | 分支名称 | Worktree 目录 | 核心目标 |
|----------|---------|------|----------|---------------|----------|
| A1 | ARCH-05, MCP-02 | ✅ Fixed | `feature/mcp-resources` | `feat-mcp-resources-a3f1b2` | Resource 推送通知实现：22 个 Resource 变更时通过 MCP `notifications/resources/updated` 通知订阅客户端 |
| A2 | ARCH-11 | ✅ Fixed | `feature/unified-errors` | `feat-unified-errors-b5e7c3` | 统一错误处理：所有工具统一返回 JSON 格式 `{error, data, degradation_level, hook_errors}` |
| A3 | MCP-03 | ✅ Fixed | `feature/audit-logger` | `feat-audit-logger-c7d4e9` | 审计日志：`audit_log` 表 + `record_audit_log()` + 工具调用自动记录 + 90 天归档 |
| A4 | SKILL-02 | ✅ Fixed | `feature/skeleton-commands` | `feat-skeleton-commands-d1f6a4` | SKELETON 阶段可用命令：`/status`、`/help`、`/budget` |

**依赖关系**：

```
A2 (统一错误处理) ──► A3 (审计日志)     ← A3 依赖 A2 的统一错误格式
A1 (Resource推送) ──► A3 (审计日志)     ← A3 需要记录 Resource 变更
A4 (SKELETON命令)                       ← 独立，无依赖
```

**受影响文件**：

| 文件 | 变更类型 | 涉及步骤 |
|------|----------|----------|
| `xuansto-mcp-server/src/xuansto_mcp/resources/skill_resources.py` | 修改 | A1 |
| `xuansto-mcp-server/src/xuansto_mcp/core/errors.py` | 修改 | A2 |
| `xuansto-mcp-server/src/xuansto_mcp/tools/*.py` | 修改（20 个工具） | A2 |
| `xuansto-mcp-server/src/xuansto_mcp/core/database.py` | 修改 | A3 |
| `xuansto-mcp-server/src/xuansto_mcp/server.py` | 修改 | A3 |
| `.trae/skills/xuansto-skill-v2/SKILL.md` | 修改 | A4 |
| `.trae/skills/xuansto-skill-v2/constraints.yaml` | 修改 | A4 |

### 8.2 Phase B（v8.2.0）— 持久化与一致性

| 重构步骤 | 问题 ID | 状态 | 分支名称 | Worktree 目录 | 核心目标 |
|----------|---------|------|----------|---------------|----------|
| B1 | ARCH-06 | ✅ Fixed | `feature/persistence` | `feat-persistence-f2a8c5` | Agent 持久化：`agent_states` SQLite 表 + 双写过渡 + 启动恢复 |
| B2 | ARCH-07 | ✅ Fixed | `feature/persistence` | `feat-persistence-f2a8c5` | 工作流持久化：`workflow_states` SQLite 表 + 双写过渡 + 启动恢复 |
| B3 | DB-01 | ✅ Fixed | `feature/dual-write` | `feat-dual-write-g9b3d7` | 决策双写事务保证：SQLite 为主存储 + 文件系统备份 + 对账 |
| B4 | DB-02 | ✅ Fixed | `feature/dual-write` | `feat-dual-write-g9b3d7` | ChromaDB 双写增强：重试 3 次 + 死信队列 + 对账修复率 ≥ 99% |
| B5 | ARCH-09 | ✅ Fixed | `feature/hook-timeout` | `feat-hook-timeout-h4c2e8` | Hook 超时保护：默认 30s + 安全 Hook 超时阻断 + 非 Hook 超时跳过 |

**依赖关系**：

```
B1 (Agent持久化) ──► B2 (工作流持久化)   ← B2 依赖 B1 的持久化框架
B3 (决策双写) ──► B4 (ChromaDB双写)     ← B4 依赖 B3 的对账框架
B5 (Hook超时)                           ← 独立，无依赖
```

**受影响文件**：

| 文件 | 变更类型 | 涉及步骤 |
|------|----------|----------|
| `xuansto-mcp-server/src/xuansto_mcp/tools/agent_manage.py` | 修改 | B1 |
| `xuansto-mcp-server/src/xuansto_mcp/tools/workflow_dispatch.py` | 修改 | B2 |
| `xuansto-mcp-server/src/xuansto_mcp/tools/decision_log.py` | 修改 | B3 |
| `xuansto-mcp-server/src/xuansto_mcp/tools/knowledge_inject.py` | 修改 | B4 |
| `xuansto-mcp-server/src/xuansto_mcp/core/database.py` | 修改 | B1-B4 |
| `xuansto-mcp-server/src/xuansto_mcp/core/hook_engine.py` | 修改 | B5 |

### 8.3 Phase C（v8.3.0）— 增强功能

| 重构步骤 | 问题 ID | 状态 | 分支名称 | Worktree 目录 | 核心目标 |
|----------|---------|------|----------|---------------|----------|
| C1 | ARCH-10 | ✅ Fixed | `feature/config-hot-reload` | `feat-config-hot-reload-j6d5f1` | 配置热更新：constraints.yaml 变更 5s 内生效 + hooks.json 下次 Hook 生效 + 失败回滚 |
| C2 | ARCH-12 | ✅ Fixed | `feature/api-versioning` | `feat-api-versioning-k8e7a3` | API 版本协商：版本不匹配返回降级建议 + 弃用特性列表 + 向后兼容 |
| C3 | API-01 | ✅ Fixed | `feature/api-versioning` | `feat-api-versioning-k8e7a3` | HTTP/MCP Schema 统一：相同工具的 HTTP 和 MCP 调用返回相同 JSON 结构 |
| C4 | DB-03 | ✅ Fixed | `feature/dual-write` | `feat-dual-write-g9b3d7` | 知识版本历史清理：保留最近 10 版本 + 90 天归档 |
| C5 | MCP-04 | ✅ Fixed | `feature/mcp-resources` | `feat-mcp-resources-a3f1b2` | 便捷 Resource：新增 4 个 Resource |

**依赖关系**：

```
C1 (配置热更新)                        ← 独立
C2 (API版本协商) ──► C3 (HTTP/MCP统一) ← C2 是 Schema 统一的前置
C4 (版本清理)                           ← 独立
C5 (便捷Resource)                       ← 独立
```

> 注：C3 在 `feature/api-versioning` 中完成，C4 在 `feature/dual-write` 中完成，C5 在 `feature/mcp-resources` 中完成。

**受影响文件**：

| 文件 | 变更类型 | 涉及步骤 |
|------|----------|----------|
| `xuansto-mcp-server/src/xuansto_mcp/core/config.py` | 修改 | C1 |
| `xuansto-mcp-server/src/xuansto_mcp/tools/server_health.py` | 修改 | C2 |
| `xuansto-mcp-server/src/xuansto_mcp/server.py` | 修改 | C3 |
| `scripts/knowledge_server/api.py` | 修改 | C3 |
| `scripts/knowledge_server/api_routes.py` | 修改 | C3 |
| `xuansto-mcp-server/src/xuansto_mcp/core/database.py` | 修改 | C4 |
| `xuansto-mcp-server/src/xuansto_mcp/resources/skill_resources.py` | 修改 | C5 |

### 8.4 Phase D（v8.4.0）— 优化

| 重构步骤 | 问题 ID | 状态 | 分支名称 | Worktree 目录 | 核心目标 |
|----------|---------|------|----------|---------------|----------|
| D1 | ARCH-08 | ✅ Fixed | `feature/progressive-loading` | `feat-progressive-loading-l2f9b5` | Token-Phase 关联：每阶段独立预算 + 阶段推进自动分配 + 预算超限触发降级 |
| D2 | ARCH-13 | ✅ Fixed | `feature/progressive-loading` | `feat-progressive-loading-l2f9b5` | Resource 推送通知增强：批量通知合并 + 推送失败自动重试 |
| D3 | — | ✅ Fixed | `feature/progressive-loading` | `feat-progressive-loading-l2f9b5` | 渐进式加载增强：4 阶段状态机 + 转换条件 + 降级集成 |
| D4 | — | ✅ Fixed | `feature/progressive-loading` | `feat-progressive-loading-l2f9b5` | 性能指标体系：P50/P95/P99 延迟 + 错误率 + 降级率 + Token 消耗 |

**依赖关系**：

```
D1 (Token-Phase关联) ──► D3 (渐进式加载增强) ──► D4 (性能指标体系)
D2 (推送通知增强)                                        ← 独立
```

**受影响文件**：

| 文件 | 变更类型 | 涉及步骤 |
|------|----------|----------|
| `xuansto-mcp-server/src/xuansto_mcp/tools/token_budget.py` | 修改 | D1 |
| `xuansto-mcp-server/src/xuansto_mcp/tools/resource_load_status.py` | 修改 | D1, D3 |
| `xuansto-mcp-server/src/xuansto_mcp/resources/skill_resources.py` | 修改 | D2 |
| `xuansto-mcp-server/src/xuansto_mcp/tools/server_health.py` | 修改 | D4 |
| `xuansto-mcp-server/src/xuansto_mcp/tools/metrics_report.py` | 修改 | D4 |
| `xuansto-mcp-server/src/xuansto_mcp/core/database.py` | 修改 | D4 |

### 8.5 版本发布计划总览

| 版本 | 包含 Phase | 包含分支 | 预期内容 | 关键问题 | 问题状态 |
|------|-----------|----------|----------|----------|----------|
| v8.0.0 | 基线 | — | 现有功能稳定版 | P0-01/02 已修复 | ✅ |
| v8.1.0 | Phase A | feature/mcp-resources, feature/unified-errors, feature/audit-logger, feature/skeleton-commands | Resource 推送 + 统一错误 + 审计日志 + SKELETON 命令 | ARCH-05, ARCH-11, MCP-03, SKILL-02 | ✅ Fixed |
| v8.2.0 | Phase B | feature/persistence, feature/dual-write, feature/hook-timeout | Agent/工作流持久化 + 双写一致性 + Hook 超时 | ARCH-06/07, DB-01/02, ARCH-09 | ✅ Fixed |
| v8.3.0 | Phase C | feature/config-hot-reload, feature/api-versioning | 配置热更新 + API 版本协商 | ARCH-10, ARCH-12, API-01, DB-03, MCP-04 | ✅ Fixed |
| v8.4.0 | Phase D | feature/progressive-loading | Token-Phase 关联 + 渐进式加载增强 + 性能指标 | ARCH-08, ARCH-13 | ✅ Fixed |

### 8.6 各阶段分支生命周期

```
develop ──────────────────────────────────────────────────────────────────────►
         │                    │                    │                    │
         │ Phase A            │ Phase B            │ Phase C            │ Phase D
         │                    │                    │                    │
         ├─ feat/unified-errors ─┤                  │                    │
         ├─ feat/mcp-resources ──┤                  │                    │
         ├─ feat/audit-logger ───┤                  │                    │
         ├─ feat/skeleton-cmds ──┤                  │                    │
         │                    │                    │                    │
         │     release/v8.1.0 ─┤                    │                    │
         │                    │                    │                    │
         │                    ├─ feat/persistence ──┤                    │
         │                    ├─ feat/dual-write ───┤                    │
         │                    ├─ feat/hook-timeout ──┤                   │
         │                    │                    │                    │
         │                    │     release/v8.2.0 ─┤                    │
         │                    │                    │                    │
         │                    │                    ├─ feat/config-hot ──┤
         │                    │                    ├─ feat/api-ver ─────┤
         │                    │                    │                    │
         │                    │                    │     release/v8.3.0 ─┤
         │                    │                    │                    │
         │                    │                    │                    ├─ feat/progressive ─┤
         │                    │                    │                    │
         │                    │                    │                    │     release/v8.4.0 ─┤
         │                    │                    │                    │
main ──────────────────────────────────────────────────────────────────────────►
              ↑ v8.1.0         ↑ v8.2.0         ↑ v8.3.0         ↑ v8.4.0
```

---

> **文档维护说明**：本文档应随项目版本迭代同步更新，特别是分支列表、版本号和阶段映射关系。每次 release 发布后需更新版本发布计划表。分支与 REFACTOR_PLAN.md 的问题 ID 保持一致，新增问题按原有编号规则续编。REFACTOR_PLAN.md 中 30/32 项问题已标记为 ✅ Fixed，仅 P3-01 (Open) 和 P3-02 (Deferred) 未修复。
