# Xuansto Git 管理策略

> 版本: 4.0.0 | 日期: 2026-05-24 | 状态: 实施中
> 仓库: https://github.com/xuanyuanchumo/xuansto
> 关联文档: .editorconfig / .gitignore(×3) / .gitattributes(✅) / .git/info/exclude(✅) / .github/(✅)

---

## 目录

1. [Git Worktree 并行开发策略](#1-git-worktree-并行开发策略)
2. [本地分支管理](#2-本地分支管理)
3. [.gitignore 合理性审查与优化](#3-gitignore-合理性审查与优化)
4. [.gitattributes 审查与优化](#4-gitattributes-审查与优化)
5. [.git/info/exclude 本地忽略规则](#5-gitinfoexclude-本地忽略规则)
6. [.github/ 目录方案](#6-github-目录方案)
7. [可执行命令序列](#7-可执行命令序列)
8. [分支与重构阶段映射](#8-分支与重构阶段映射)

---

## 1. Git Worktree 并行开发策略

### 1.1 为什么使用 Worktree

Xuansto 项目包含两个紧密耦合的组件（v2 Skill / MCP Server），重构期间需要同时推进多个优先级的任务。Git Worktree 允许在同一仓库下同时检出多个分支到不同目录，实现：

- **并行开发**：feature 开发与 main 稳定基线可在不同工作树中同步推进
- **隔离测试**：每个工作树拥有独立的工作区，互不干扰
- **零切换成本**：无需 `git stash` 或 `git checkout`，直接在不同目录间切换

### 1.2 Worktree 目录结构

```
D:\Projects\TraeProjects\
├── skiller\                          ← 主工作树 (main 分支，稳定基线)
│   ├── .trae/skills/xuansto-skill-v2/    (v8.0.0, current)
│   ├── xuansto-mcp-server/               (MCP Server v8.0.0)
│   └── docs/plan/                        (规划文档)
│
├── skiller-feature\                  ← 功能开发工作树 (feature/* 分支，按需创建)
│   └── (同上结构)
│
└── skiller-hotfix\                   ← 热修复工作树 (hotfix/* 分支，按需创建)
    └── (同上结构)
```

### 1.3 Worktree 与分支对应关系

| 工作树目录 | 分支 | 用途 | 生命周期 |
|-----------|------|------|---------|
| `skiller\` | `main` | 稳定发布基线，仅接受合并 | 永久 |
| `skiller-feature\` | `feature/<name>` | 功能开发 | 合并后删除 |
| `skiller-hotfix\` | `hotfix/<name>` | 紧急线上修复 | 合并后删除 |

### 1.4 Worktree 管理原则

1. **一个功能一个工作树**：每个 feature 分支对应独立工作树，完成后合并并移除
2. **main 为唯一长期分支**：所有 feature/hotfix 分支完成后合并到 `main`
3. **main 仅接受合并**：禁止在 `main` 分支上直接提交（hotfix cherry-pick 除外）
4. **工作树及时清理**：分支合并后立即执行 `git worktree remove` 和 `git branch -d`
5. **历史分支已清理**：develop/v8、feature/p0-fixes、feature/mcp-core、feature/p1-api-governance、feature/progressive-loading、feature/p4-finalization 均已从远程删除

### 1.5 简化说明

> **从 v3.0.0 到 v4.0.0 的关键变更**：原方案使用 `develop/v8` 作为开发集成分支，实际操作中发现对于单人维护项目，中间集成分支增加了不必要的合并复杂度。现简化为 **main+feature** 模式：
> - `main` 即为稳定基线，也是开发主线
> - 大特性使用 feature 分支隔离开发，完成后直接合并回 main
> - 小范围改动直接在 main 上提交
> - develop/v8 已从远程删除，不再使用

---

## 2. 本地分支管理

### 2.1 当前分支状态

| 分支名 | 类型 | 状态 | 说明 |
|--------|------|------|------|
| `main` | 长期 | ✅ 活跃 | 唯一远程分支，稳定基线 |
| ~~`develop/v8`~~ | ~~长期~~ | ❌ 已删除 | 原开发集成分支，已从远程删除 |
| ~~`feature/p0-fixes`~~ | ~~短期~~ | ❌ 已删除 | P0 紧急修复，已合并后删除 |
| ~~`feature/mcp-core`~~ | ~~短期~~ | ❌ 已删除 | P1 MCP 核心重构，已合并后删除 |
| ~~`feature/p1-api-governance`~~ | ~~短期~~ | ❌ 已删除 | P1 接口治理，已合并后删除 |
| ~~`feature/progressive-loading`~~ | ~~短期~~ | ❌ 已删除 | P2 渐进式加载，已合并后删除 |
| ~~`feature/p4-finalization`~~ | ~~短期~~ | ❌ 已删除 | P4 收尾，已合并后删除 |

### 2.2 当前标签状态

| 标签 | 状态 | 说明 |
|------|------|------|
| `v8.0.0` | ✅ 存在 | 当前唯一标签，标记 v8.0.0 完整发布 |
| ~~`v5.0.0`~~ | ❌ 已删除 | 旧版本标签，已清理 |
| ~~`v8.0.0-p0`~~ | ❌ 未创建 | 原计划阶段标签，简化后不再使用 |
| ~~`v8.0.0-p1`~~ | ❌ 未创建 | 同上 |
| ~~`v8.0.0-p2`~~ | ❌ 未创建 | 同上 |
| ~~`v8.0.0-p3`~~ | ❌ 未创建 | 同上 |

### 2.3 未来分支策略

#### 分支命名规范

| 分支类型 | 命名格式 | 示例 | 生命周期 |
|---------|---------|------|---------|
| 功能开发 | `feature/<简短描述>` | `feature/mcp-eval-v2` | 合并后删除 |
| 热修复 | `hotfix/<简短描述>` | `hotfix/degradation-loop` | 合并后删除 |
| 实验性 | `experiment/<简短描述>` | `experiment/chroma-migration` | 评估后删除 |

#### 分支创建与合并流程

```
feature/<name> ──(开发完成+测试通过)──▶ main (tag: v<version>)
hotfix/<name> ──(修复完成)──▶ main (cherry-pick)
```

**合并规则：**

1. Feature 分支使用 `--no-ff` 合并到 `main`，保留分支历史
2. 合并前必须通过全部验收标准
3. 合并后立即删除 feature 分支和对应 worktree
4. 重大版本合并后打 tag：`v<major>.<minor>.<patch>`

#### 本地残留分支清理

如本地仍有已删除远程分支的跟踪引用，执行以下命令清理：

```powershell
git remote prune origin
git branch -vv | Where-Object { $_ -match '\[gone\]' } | ForEach-Object {
    $_ -match '^\s+(\S+)' | Out-Null
    git branch -D $Matches[1]
}
```

---

## 3. .gitignore 合理性审查与优化

### 3.1 审查原则

**核心规则**：只管理满足以下全部条件的文件：
1. 无法从其他源文件自动生成
2. 对项目构建/运行非必需
3. 不包含个人/机密信息

### 3.2 当前配置文件清单

| 文件路径 | 作用域 | 状态 |
|---------|--------|------|
| `.gitignore`（根目录） | 全仓库 | ✅ 已优化 |
| `xuansto-mcp-server/.gitignore` | MCP Server 子项目 | ✅ 存在 |
| `.trae/skills/xuansto-skill-v2/.gitignore` | v2 Skill | ✅ 存在 |

> **变更说明**：v1 Skill（`.trae/skills/xuansto-skill/`）已从仓库彻底移除，其 `.gitignore` 不再存在。

### 3.3 根目录 `.gitignore` 当前内容（已优化）

```gitignore
.trae/*
!.trae/skills/
.trae/skills/*
!.trae/skills/xuansto-skill-v2/

.trae/skills/xuansto-skill-v2/.knowledge/temp-scripts/*
!.trae/skills/xuansto-skill-v2/.knowledge/temp-scripts/.gitkeep
.trae/skills/xuansto-skill-v2/.knowledge/script-errors/*
!.trae/skills/xuansto-skill-v2/.knowledge/script-errors/.gitkeep
.trae/skills/xuansto-skill-v2/.knowledge/index/knowledge.db

.xuansto/

.venv/
.venv2/
.venv_test/
.testvenv/
__pycache__/
*.py[cod]
*$py.class

.DS_Store
Thumbs.db
._*

.idea/
.vscode/
.claude/
.cursor/
.windsurf/
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

xuansto-clean/
副本/

CHANGELOG.md
CODE_WIKI.md
xuansto-skill-WIKI.md
_copy_helper.ps1
_copy_helper.py
setup-worktree.ps1
test-path-resolve.ps1
test-syntax.ps1
docs/*
!docs/plan/
```

### 3.4 合理性分析

#### ✅ 合理的设计

| 规则 | 分析 |
|------|------|
| `.trae/*` → `!.trae/skills/` → `.trae/skills/*` → `!.trae/skills/xuansto-skill-v2/` | 精确控制 Trae 目录的纳入范围，仅保留 v2 Skill，v1 已移除后不再保留其例外 |
| `.xuansto/` | 运行时数据目录，不应提交 |
| `.venv/ .venv2/ .venv_test/ .testvenv/` | 覆盖所有实际使用的虚拟环境目录，`.venv2/` 已补入 |
| `.idea/ .vscode/ .claude/ .cursor/ .windsurf/` | 覆盖主流 AI IDE 配置目录 |
| `*.db *.sqlite3` | 数据库文件全局排除 |
| `docs/` | 文档目录整体排除（规划文档仅在本地保留） |
| `CHANGELOG.md CODE_WIKI.md xuansto-skill-WIKI.md` | 排除自动生成/历史文档文件 |
| `_copy_helper.ps1 _copy_helper.py setup-worktree.ps1 test-path-resolve.ps1 test-syntax.ps1` | 排除本地辅助脚本 |

#### ⚠️ 可优化项

| # | 问题 | 影响 | 严重度 | 建议 |
|---|------|------|--------|------|
| 1 | `.trae/skills/xuansto-skill-v2/.knowledge/index/knowledge.db` 与 `*.db *.sqlite3` 重复 | 冗余规则，`*.db` 已覆盖 | 低 | 可删除该行，但保留可提高可读性，建议保留 |
| 2 | `.trae/skills/xuansto-skill-v2/.knowledge/temp-scripts/*` 和 `script-errors/*` 规则在根目录和 v2 自身 `.gitignore` 中可能重复 | 双重排除，冗余但不影响功能 | 低 | 根目录保留（确保即使子目录 `.gitignore` 缺失也能正确排除） |
| 3 | 缺少 `*.egg-info/`、`dist/`、`build/` 排除 | Python 构建产物可能被意外提交 | 中 | 添加通用 Python 构建产物排除 |
| 4 | 缺少 `.mypy_cache/`、`.pytest_cache/`、`.ruff_cache/` 排除 | 工具缓存目录可能被意外提交 | 中 | 添加工具缓存排除 |
| 5 | 缺少 `.coverage`、`htmlcov/` 排除 | 测试覆盖率产物可能被意外提交 | 中 | 添加覆盖率产物排除 |
| 6 | `*.so` 缺失 | Python C 扩展编译产物可能被意外提交 | 低 | 添加 `*.so` |
| 7 | 多条规则写在同一行（如 `.venv/ .venv2/ .venv_test/ .testvenv/`） | 降低可读性 | 低 | 建议每条规则独立一行，并添加分类注释 |
| 8 | 缺少 `*.pkl`、`*.parquet` 排除 | 数据序列化文件可能被意外提交 | 低 | 按需添加 |

### 3.5 优化方案

#### 3.5.1 根目录 `.gitignore` 优化

```gitignore
# === Trae 平台目录 ===
.trae/*
!.trae/skills/
.trae/skills/*
!.trae/skills/xuansto-skill-v2/

.trae/skills/xuansto-skill-v2/.knowledge/temp-scripts/*
!.trae/skills/xuansto-skill-v2/.knowledge/temp-scripts/.gitkeep
.trae/skills/xuansto-skill-v2/.knowledge/script-errors/*
!.trae/skills/xuansto-skill-v2/.knowledge/script-errors/.gitkeep
.trae/skills/xuansto-skill-v2/.knowledge/index/knowledge.db

# === 运行时数据目录 ===
.xuansto/

# === Python 虚拟环境 ===
.venv/
.venv2/
.venv_test/
.testvenv/

# === Python 编译产物 ===
__pycache__/
*.py[cod]
*.so

# === Python 构建产物 ===
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
.claude/
.cursor/
.windsurf/

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

# === 数据序列化文件 ===
*.pkl
*.parquet

# === 临时备份/清理目录 ===
xuansto-clean/
副本/

# === 排除的文档/脚本文件 ===
CHANGELOG.md
CODE_WIKI.md
xuansto-skill-WIKI.md
_copy_helper.ps1
_copy_helper.py
setup-worktree.ps1
test-path-resolve.ps1
test-syntax.ps1

# === 文档目录（规划文档仅本地保留） ===
docs/
```

**变更说明：**

| 变更项 | 原规则 | 新规则 | 理由 |
|--------|--------|--------|------|
| 多规则同行 | `.venv/ .venv2/ .venv_test/ .testvenv/` | 每条规则独立一行 | 提升可读性 |
| 多规则同行 | `.DS_Store Thumbs.db ._*` | 每条规则独立一行 | 同上 |
| 多规则同行 | `.idea/ .vscode/ .claude/ .cursor/ .windsurf/` | 每条规则独立一行 | 同上 |
| 多规则同行 | `*.log logs/` | 每条规则独立一行 | 同上 |
| 多规则同行 | `*.db *.sqlite3` | 每条规则独立一行 | 同上 |
| Python 构建产物 | 缺失 | 新增 `*.egg-info/`、`*.egg`、`*.whl`、`dist/`、`build/`、`.eggs/` | 兜底覆盖构建产物 |
| 工具缓存 | 缺失 | 新增 `.mypy_cache/`、`.pytest_cache/`、`.ruff_cache/` | 防止工具缓存被意外提交 |
| 覆盖率产物 | 缺失 | 新增 `.coverage`、`htmlcov/` 等 | 防止测试覆盖率产物被意外提交 |
| `*.so` | 缺失 | 新增 | Python C 扩展编译产物 |
| `*.pkl`、`*.parquet` | 缺失 | 新增 | 数据序列化文件 |
| 添加分类注释 | 无 | 每组规则前添加注释 | 提升可读性和可维护性 |

#### 3.5.2 `xuansto-mcp-server/.gitignore` 优化建议

> 当前文件已存在，以下为建议补充的规则（需确认当前内容后合并）：

```gitignore
# === 建议补充 ===
.venv2/
.mypy_cache/
.pytest_cache/
.ruff_cache/
.coverage
.coverage.*
htmlcov/
*.egg-info/
dist/
build/
```

#### 3.5.3 `.trae/skills/xuansto-skill-v2/.gitignore` 优化建议

> 当前文件已存在，以下为建议补充的规则（需确认当前内容后合并）：

```gitignore
# === 建议补充 ===
.knowledge/index/chroma_db/
.mypy_cache/
.pytest_cache/
```

### 3.6 优化后需执行的命令

```powershell
$RepoRoot = "D:\Projects\TraeProjects\skiller"
Set-Location $RepoRoot

# [1] 提交 .gitignore 变更
git add .gitignore
git add xuansto-mcp-server/.gitignore
git add .trae/skills/xuansto-skill-v2/.gitignore
git commit -m "chore: optimize .gitignore with categories, build artifacts, and tool caches"

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

| 位置 | 状态 | 说明 |
|------|------|------|
| 根目录 `.gitattributes` | ❌ **缺失** | 需创建 |
| `xuansto-mcp-server/.gitattributes` | ❌ **缺失** | 需创建 |
| `.trae/skills/xuansto-skill-v2/.gitattributes` | ❌ **缺失** | 需创建 |

### 4.3 与 `.editorconfig` 的对齐

当前根目录 `.editorconfig` 定义：

```editorconfig
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
```

`.gitattributes` 应与 `.editorconfig` 的 `end_of_line = lf` 保持一致，在 git 层面强制执行。

**对齐关系：**

| 行为 | `.editorconfig` | `.gitattributes` | 职责 |
|------|----------------|-----------------|------|
| 字符编码 | `charset = utf-8` | 不涉及 | 编辑器负责 |
| 行尾符 | `end_of_line = lf` | `eol=lf` | 双重保障：编辑器写入时 + git checkout 时 |
| 末尾换行 | `insert_final_newline = true` | 不涉及 | 编辑器负责 |
| 二进制标记 | 不涉及 | `binary` | git 负责 |
| diff 策略 | 不涉及 | `diff=python` 等 | git 负责 |

### 4.4 建议的 `.gitattributes` 内容

#### 4.4.1 根目录 `.gitattributes`

```gitattributes
# === 默认行为：自动检测文本文件，强制 LF ===
* text=auto eol=lf

# === Python ===
*.py text eol=lf diff=python
*.pyx text eol=lf diff=python
*.pyi text eol=lf diff=python

# === Markdown / 文档 ===
*.md text eol=lf diff=markdown
*.rst text eol=lf

# === 配置文件 ===
*.yaml text eol=lf
*.yml text eol=lf
*.json text eol=lf
*.toml text eol=lf
*.cfg text eol=lf
*.ini text eol=lf
*.xml text eol=lf

# === Web 前端 ===
*.js text eol=lf
*.ts text eol=lf
*.jsx text eol=lf
*.tsx text eol=lf
*.css text eol=lf
*.html text eol=lf

# === Shell 脚本（强制 LF） ===
*.sh text eol=lf
*.bash text eol=lf

# === PowerShell 脚本（Windows 使用 CRLF） ===
*.ps1 text eol=crlf

# === Git 自身配置 ===
*.gitignore text eol=lf
*.gitattributes text eol=lf
*.editorconfig text eol=lf

# === 许可证 ===
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

```powershell
$RepoRoot = "D:\Projects\TraeProjects\skiller"
Set-Location $RepoRoot

# [1] 创建根目录 .gitattributes（内容见 4.4.1 节）
# [2] 创建 xuansto-mcp-server/.gitattributes（内容见 4.4.2 节）
# [3] 创建 .trae/skills/xuansto-skill-v2/.gitattributes（内容见 4.4.3 节）

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

## 5. .git/info/exclude 本地忽略规则

### 5.1 三层忽略机制对比

| 特性 | `.gitignore` | `.gitattributes` | `.git/info/exclude` |
|------|-------------|-----------------|---------------------|
| **纳入版本控制** | ✅ 是 | ✅ 是 | ❌ 否 |
| **影响范围** | 所有克隆者 | 所有克隆者 | 仅当前克隆 |
| **适用内容** | 团队共享忽略规则 | 文件属性/行尾/差异算法 | 个人偏好/本地临时文件 |
| **优先级** | 中 | 高（属性声明） | 高（本地覆盖） |
| **修改可见性** | 提交可见 | 提交可见 | 不进提交历史 |

### 5.2 当前状态

`.git/info/exclude` 原为 Git 默认模板（仅含注释），已补充项目适用的本地忽略规则。

### 5.3 规则内容

```gitignore
# === 个人IDE/编辑器临时文件 ===
*.sublime-project
*.sublime-workspace
.project
.classpath
.settings/

# === 本地调试/临时文件 ===
*.tmp
*.bak
*.swp
*.swo
local_*.py
scratch_*.py

# === 本地环境特定路径 ===
.local/
local_config/

# === 性能分析/覆盖率输出 ===
.coverage
htmlcov/
.mypy_cache/
.pytest_cache/
.ruff_cache/

# === 操作系统缩略图 ===
ehthumbs.db
Desktop.ini
```

### 5.4 设计原则

| 原则 | 说明 |
|------|------|
| **不与 .gitignore 重复** | 团队共享规则（如 `__pycache__/`、`.venv/`）已在 `.gitignore` 中，exclude 仅放个人/本地规则 |
| **不进版本控制** | exclude 文件位于 `.git/info/` 下，不会被 `git add` 追踪，各开发者可独立维护 |
| **IDE 中立** | 常见 IDE 临时文件（Sublime/Eclipse/MyEclipse）均覆盖，但不强制特定 IDE |
| **调试友好** | `local_*.py`、`scratch_*.py` 允许开发者在项目内创建临时调试脚本而不被误提交 |

### 5.5 与 .gitignore 的职责划分

| 规则类型 | 放置位置 | 示例 |
|----------|---------|------|
| 项目构建产物 | `.gitignore` | `__pycache__/`, `*.pyc`, `*.egg-info/` |
| 敏感信息 | `.gitignore` | `.env`, `.env.local` |
| 团队IDE配置 | `.gitignore` | `.vscode/`, `.idea/` |
| 个人IDE偏好 | `.git/info/exclude` | `*.sublime-project`, `.settings/` |
| 本地调试脚本 | `.git/info/exclude` | `local_*.py`, `scratch_*.py` |
| 性能分析输出 | `.git/info/exclude` | `.coverage`, `.mypy_cache/` |
| 本地环境路径 | `.git/info/exclude` | `.local/`, `local_config/` |

---

## 6. .github/ 目录方案

### 6.1 当前状态

| 位置 | 状态 | 说明 |
|------|------|------|
| `.github/` | ❌ **缺失** | 需创建 Issue 模板、PR 模板、CI workflow |

### 6.2 目录结构

```
.github/
├── ISSUE_TEMPLATE/
│   ├── bug_report.yml          ← Bug 报告模板
│   ├── feature_request.yml     ← 功能请求模板
│   └── config.yml              ← 模板配置（issue chooser）
├── PULL_REQUEST_TEMPLATE.md    ← PR 模板
└── workflows/
    └── ci.yml                  ← CI 工作流
```

### 6.3 Issue 模板

#### 6.3.1 `bug_report.yml`

```yaml
name: Bug 报告
description: 报告 xuansto 项目的问题
labels: ["bug"]
body:
  - type: checkboxes
    id: component
    attributes:
      label: 组件
      options:
        - label: xuansto-mcp-server
        - label: xuansto-skill-v2
        - label: 其他
  - type: textarea
    id: description
    attributes:
      label: 问题描述
      description: 清晰描述遇到的问题
    validations:
      required: true
  - type: textarea
    id: steps
    attributes:
      label: 复现步骤
      description: 提供复现问题的具体步骤
      placeholder: |
        1. ...
        2. ...
        3. ...
    validations:
      required: true
  - type: textarea
    id: expected
    attributes:
      label: 期望行为
    validations:
      required: true
  - type: textarea
    id: actual
    attributes:
      label: 实际行为
    validations:
      required: true
  - type: textarea
    id: environment
    attributes:
      label: 环境信息
      description: 操作系统、Python 版本、xuansto 版本等
      placeholder: |
        - OS:
        - Python:
        - xuansto version:
  - type: textarea
    id: logs
    attributes:
      label: 相关日志
      description: 粘贴相关错误日志或截图
      render: shell
```

#### 6.3.2 `feature_request.yml`

```yaml
name: 功能请求
description: 建议新功能或改进
labels: ["enhancement"]
body:
  - type: checkboxes
    id: component
    attributes:
      label: 组件
      options:
        - label: xuansto-mcp-server
        - label: xuansto-skill-v2
  - type: textarea
    id: problem
    attributes:
      label: 问题/需求背景
      description: 描述促使此功能请求的问题或需求
    validations:
      required: true
  - type: textarea
    id: solution
    attributes:
      label: 期望的解决方案
    validations:
      required: true
  - type: textarea
    id: alternatives
    attributes:
      label: 备选方案
      description: 考虑过的其他解决方案
  - type: textarea
    id: additional
    attributes:
      label: 补充信息
```

#### 6.3.3 `config.yml`

```yaml
blank_issues_enabled: false
contact_links: []
```

### 6.4 PR 模板

#### `PULL_REQUEST_TEMPLATE.md`

```markdown
## 变更描述

<!-- 简要描述此 PR 的目的 -->

## 变更类型

- [ ] Bug 修复
- [ ] 新功能
- [ ] 重构
- [ ] 文档更新
- [ ] CI/构建变更
- [ ] 其他：

## 影响范围

- [ ] xuansto-mcp-server
- [ ] xuansto-skill-v2
- [ ] 项目配置（.gitignore / .gitattributes / .editorconfig）

## 测试

- [ ] 已通过现有测试
- [ ] 已添加新测试
- [ ] 已手动验证

## 关联 Issue

<!-- 关联的 Issue 编号，如 Closes #123 -->

## 检查清单

- [ ] 代码遵循项目现有风格
- [ ] 无硬编码密钥或敏感信息
- [ ] 已更新相关文档（如需要）
```

### 6.5 CI Workflow

#### `workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: |
          cd xuansto-mcp-server
          pip install -e ".[dev]"
      - name: Ruff check
        run: |
          cd xuansto-mcp-server
          ruff check .
      - name: Ruff format check
        run: |
          cd xuansto-mcp-server
          ruff format --check .

  test:
    runs-on: ubuntu-latest
    needs: lint
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          cd xuansto-mcp-server
          pip install -e ".[dev,test]"
      - name: Run tests
        run: |
          cd xuansto-mcp-server
          pytest tests/ -x --cov=xuansto_mcp --cov-fail-under=80 -v

  typecheck:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: |
          cd xuansto-mcp-server
          pip install -e ".[dev]"
      - name: Mypy
        run: |
          cd xuansto-mcp-server
          mypy src/ --ignore-missing-imports
```

### 6.6 创建 `.github/` 目录的命令

```powershell
$RepoRoot = "D:\Projects\TraeProjects\skiller"
Set-Location $RepoRoot

# [1] 创建目录结构
New-Item -ItemType Directory -Force -Path ".github/ISSUE_TEMPLATE"
New-Item -ItemType Directory -Force -Path ".github/workflows"

# [2] 创建各模板文件（内容见 6.3~6.5 节）
# 手动创建以下文件：
#   - .github/ISSUE_TEMPLATE/bug_report.yml
#   - .github/ISSUE_TEMPLATE/feature_request.yml
#   - .github/ISSUE_TEMPLATE/config.yml
#   - .github/PULL_REQUEST_TEMPLATE.md
#   - .github/workflows/ci.yml

# [3] 提交
git add .github/
git commit -m "chore: add GitHub issue/PR templates and CI workflow"
```

---

## 7. 可执行命令序列

> 以下命令基于当前实际 git 状态：仅 main 分支、仅 v8.0.0 标签、710 个文件。

### 7.1 环境验证

```powershell
$RepoRoot = "D:\Projects\TraeProjects\skiller"
Set-Location $RepoRoot

# [1] 验证当前分支
git branch --show-current
# 预期输出: main

# [2] 验证远程分支
git branch -r
# 预期输出: origin/main

# [3] 验证标签
git tag -l
# 预期输出: v8.0.0

# [4] 验证文件数量
git ls-files | Measure-Object | Select-Object -ExpandProperty Count
# 预期输出: 710

# [5] 验证仓库结构
git ls-tree --name-only HEAD
# 预期输出: .editorconfig  .gitignore  .trae/  README.md  xuansto-mcp-server/

# [6] 清理本地残留的远程跟踪引用
git remote prune origin
```

### 7.2 应用 .gitignore 优化

```powershell
Set-Location $RepoRoot

# [1] 编辑 .gitignore（内容见 3.5.1 节）
# [2] 编辑 xuansto-mcp-server/.gitignore（补充 3.5.2 节建议）
# [3] 编辑 .trae/skills/xuansto-skill-v2/.gitignore（补充 3.5.3 节建议）

# [4] 提交 .gitignore 变更
git add .gitignore
git add xuansto-mcp-server/.gitignore
git add .trae/skills/xuansto-skill-v2/.gitignore
git commit -m "chore: optimize .gitignore with categories, build artifacts, and tool caches"

# [5] 清除已被新规则覆盖的 git 跟踪文件
git rm -r --cached .mypy_cache/ 2>$null
git rm -r --cached .pytest_cache/ 2>$null
git rm -r --cached .ruff_cache/ 2>$null
git rm -r --cached .coverage* 2>$null
git rm -r --cached htmlcov/ 2>$null
git rm -r --cached xuansto-mcp-server/.venv2/ 2>$null
git rm -r --cached .trae/skills/xuansto-skill-v2/.knowledge/index/chroma_db/ 2>$null
git add -A
git commit -m "chore: remove tracked cache files now covered by .gitignore"
```

### 7.3 创建 .gitattributes

```powershell
Set-Location $RepoRoot

# [1] 创建 .gitattributes 文件（内容见 4.4 节）
# [2] 提交
git add .gitattributes
git add xuansto-mcp-server/.gitattributes
git add .trae/skills/xuansto-skill-v2/.gitattributes
git commit -m "chore: add .gitattributes for cross-platform consistency"

# [3] 规范化行尾
git add --renormalize .
git commit -m "chore: normalize line endings per .gitattributes"
```

### 7.4 创建 .github/ 目录

```powershell
Set-Location $RepoRoot

# [1] 创建目录和文件（内容见第 6 节）
# [2] 提交
git add .github/
git commit -m "chore: add GitHub issue/PR templates and CI workflow"
```

### 7.5 推送到远程

```powershell
Set-Location $RepoRoot

# [1] 查看待推送的提交
git log --oneline origin/main..HEAD

# [2] 推送
git push origin main

# [3] 验证远程状态
git remote show origin
```

### 7.6 功能开发工作流（日常使用）

```powershell
# ============================================================
# 创建 feature 分支和 worktree
# ============================================================
Set-Location $RepoRoot

git worktree add -b feature/<name> D:\Projects\TraeProjects\skiller-feature main

# ============================================================
# 在 feature 工作树中开发
# ============================================================
Set-Location D:\Projects\TraeProjects\skiller-feature

# 开发...
git add -A
git commit -m "feat(<scope>): <description>"

# ============================================================
# 测试
# ============================================================
cd xuansto-mcp-server
uv run pytest tests/ -x --cov=xuansto_mcp -v

# ============================================================
# 合并到 main
# ============================================================
Set-Location $RepoRoot
git merge --no-ff feature/<name> -m "merge: feature/<name>"
git tag -a v<version> -m "v<version>: <description>"

# ============================================================
# 清理
# ============================================================
git worktree remove D:\Projects\TraeProjects\skiller-feature
git branch -d feature/<name>
git push origin main --tags
git push origin --delete feature/<name> 2>$null
```

### 7.7 紧急热修复流程

```powershell
Set-Location $RepoRoot

# [1] 创建 hotfix 工作树
git worktree add -b hotfix/<name> D:\Projects\TraeProjects\skiller-hotfix main

# [2] 修复
Set-Location D:\Projects\TraeProjects\skiller-hotfix
# ... 修复代码 ...
git add -A
git commit -m "hotfix(<scope>): <description>"

# [3] 合并回 main
Set-Location $RepoRoot
git cherry-pick <hotfix-commit-hash>

# [4] 清理
git worktree remove D:\Projects\TraeProjects\skiller-hotfix
git branch -d hotfix/<name>
git push origin main
```

### 7.8 日常状态查看

```powershell
Set-Location $RepoRoot

# 查看所有工作树
git worktree list

# 查看分支合并图
git log --oneline --graph --all --decorate

# 查看 .gitattributes 是否生效
git check-attr -a -- <文件路径>

# 查看 .gitignore 规则匹配
git check-ignore -v <文件路径>

# 查看文件行尾设置
git ls-files --eol
```

---

## 8. 分支与重构阶段映射

### 8.1 映射总表

| 重构阶段 | 原对应分支 | 解决问题 | 状态 |
|---------|-----------|---------|------|
| **P0: 紧急修复** | `feature/p0-fixes` | U-01, U-02, U-03 | ✅ 已完成，分支已删除 |
| **P1-A/D/E/F: MCP 核心** | `feature/mcp-core` | U-04, U-08, U-09, U-10 | ✅ 已完成，分支已删除 |
| **P1-B/C/G: 接口治理** | `feature/p1-api-governance` | U-05, U-06, U-07 | ✅ 已完成，分支已删除 |
| **P2-A/B/C/E/G: 架构加固(上)** | `develop/v8` 直接提交 | U-11~U-18, U-20, U-24~U-26 | ✅ 已完成，分支已删除 |
| **P2-D/F: 渐进式加载** | `feature/progressive-loading` | U-19, U-22, U-23, U-27~U-29 | ✅ 已完成，分支已删除 |
| **P3: 优化收尾** | `develop/v8` 直接提交 | U-32~U-42 | ✅ 已完成，分支已删除 |
| **P4: v8.0.0 收尾** | `feature/p4-finalization` | U-43, U-44, U-45, U-46 | 🟡 部分完成，分支已删除 |

### 8.2 P4 详细状态

| 子任务 | 统一编号 | 状态 | 说明 |
|--------|---------|------|------|
| P4-A: FALLBACK_MAP 补全 | U-43 | ✅ 已解决 | 降级函数已补全 |
| P4-B: 评估配置修正 | U-44 | ✅ 已解决 | Tool 引用已修正 |
| P4-C: SKILL.md Phase 标记 | U-45 | ⚠️ 已知限制 | SKILL.md 行数控制存在已知限制，Phase 标记与 resource_load_status 的 4 阶段模型一致性待验证 |
| P4-D: 健康检查间隔可配置 | U-46 | ✅ 已解决 | 间隔已可配置 |

### 8.3 仓库清理记录

| 清理项 | 原状态 | 清理后 | 说明 |
|--------|--------|--------|------|
| 文件数量 | 3306 | 710 | 清理冗余文件，移除 v1 Skill |
| 远程分支 | main + develop/v8 + feature/* | 仅 main | 所有 feature 和 develop 分支已删除 |
| 标签 | v5.0.0 + v8.0.0 | 仅 v8.0.0 | v5.0.0 旧标签已删除 |
| v1 Skill | 存在 | 已移除 | `.trae/skills/xuansto-skill/` 已从仓库彻底移除 |
| 仓库内容 | 多个组件 | 3 个核心 | 仅保留 xuansto-mcp-server/ + .trae/skills/xuansto-skill-v2/ + README.md + .gitignore + .editorconfig |

### 8.4 阶段里程碑

| 阶段 | Tag | 包含问题 | 状态 |
|------|-----|---------|------|
| P0~P3 | `v8.0.0` | U-01~U-42 | ✅ 已完成 |
| P4 | `v8.0.0` | U-43 ✅, U-44 ✅, U-45 ⚠️, U-46 ✅ | 🟡 部分完成 |

> **说明**：原计划的阶段标签（v8.0.0-p0/p1/p2/p3）在简化分支策略后不再使用，所有已完成阶段统一归入 `v8.0.0` 标签。

---

## 附录 A: 分支生命周期时间线

```
第1周    feature/p0-fixes ──────────────────────┐
                                                ▼
第2周    feature/mcp-core ─────────────────┐  develop/v8
         feature/p1-api-governance ───────┤     │
                                           │     │
第3周    合并 → develop/v8 → main              │
                                                │
第4周    feature/progressive-loading ──┐  develop/v8
         P2-A/B/C/E/G 直接提交 ───────┤     │
                                       │     │
第5周    合并 → develop/v8 → main              │
                                                │
第6周+   P3 直接在 develop/v8 提交 → main       │
                                                │
第7周    feature/p4-finalization → main         │
                                                │
         ─── 清理阶段 ───                       │
         删除 develop/v8、所有 feature 分支      │
         删除 v5.0.0 标签                       │
         移除 v1 Skill                          │
         文件从 3306 清理至 710                  │
         仅保留 main 分支 + v8.0.0 标签  ← 当前状态
```

## 附录 B: .gitignore 文件层级关系

```
根目录 .gitignore                              ← 全仓库通用规则（兜底）
├── xuansto-mcp-server/.gitignore              ← MCP Server 子项目专用规则
└── .trae/skills/xuansto-skill-v2/.gitignore   ← v2 Skill 专用规则
```

**层级原则：**
- 根目录 `.gitignore` 负责全仓库通用排除（Python 编译产物、IDE 文件、OS 文件等）
- 子目录 `.gitignore` 仅添加该子项目特有的排除规则
- 避免根目录和子目录 `.gitignore` 重复定义同一规则
- `.trae/*` 的排除/保留逻辑仅在根目录管理，子目录不再重复

## 附录 C: .gitattributes 文件层级关系

```
根目录 .gitattributes                           ← 全仓库默认行为（* text=auto eol=lf + 二进制声明）
├── xuansto-mcp-server/.gitattributes           ← MCP Server 特定规则（数据文件）
└── .trae/skills/xuansto-skill-v2/.gitattributes ← v2 Skill 特定规则（脚本行尾、Knowledge 数据）
```

**层级原则：**
- 根目录 `.gitattributes` 定义 `* text=auto eol=lf` 作为全仓库默认
- 子目录 `.gitattributes` 仅补充该子项目特有的声明
- 二进制文件声明在根目录统一管理（`*.db`、`*.so`、`*.dll` 等）
- 与 `.editorconfig` 保持一致：git 层面强制 LF，编辑器层面也强制 LF

## 附录 D: .github/ 目录层级关系

```
.github/
├── ISSUE_TEMPLATE/
│   ├── bug_report.yml          ← Bug 报告模板
│   ├── feature_request.yml     ← 功能请求模板
│   └── config.yml              ← 模板配置
├── PULL_REQUEST_TEMPLATE.md    ← PR 模板
└── workflows/
    └── ci.yml                  ← CI 工作流（lint + test + typecheck）
```

**设计原则：**
- Issue 模板使用 YAML 格式，支持结构化输入和验证
- PR 模板使用 Markdown 格式，提供检查清单
- CI 工作流分三个 job：lint → test + typecheck（并行），确保代码质量
- CI 仅在 push 到 main 或 PR 到 main 时触发
