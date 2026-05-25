# Git/GitHub 管理文档

> 版本：8.0.0 | 项目：xuansto-skill-v2 | 更新日期：2026-05-25

---

## 目录

1. [Git Worktree 并行开发策略](#1-git-worktree-并行开发策略)
2. [本地分支管理](#2-本地分支管理)
3. [.gitignore 优化](#3-gitignore-优化)
4. [.gitattributes 完善](#4-gitattributes-完善)
5. [.git/info/exclude 本地忽略规则](#5-gitinfoexclude-本地忽略规则)
6. [.github/ 目录检查与优化](#6-github-目录检查与优化)
7. [操作命令序列](#7-操作命令序列)
8. [分支与重构步骤映射](#8-分支与重构步骤映射)

---

## 1. Git Worktree 并行开发策略

### 1.1 目录结构

| 路径 | 用途 | 分支 |
|------|------|------|
| `D:\Projects\TraeProjects\skiller\` | 主仓库（主工作树） | main / develop |
| `c:\Users\86156\.trae-cn\worktrees\skiller\` | Worktree 工作树根目录 | 各 feature 分支 |
| `c:\Users\86156\.trae-cn\worktrees\skiller\feat-develop-main-branch-Akindx\` | 当前活跃 worktree | develop |

### 1.2 Worktree 核心概念

Git Worktree 允许在同一仓库下同时检出多个分支到不同目录，实现：

- **并行开发**：同时在不同目录中开发不同功能，无需频繁切换分支
- **隔离环境**：每个 worktree 拥有独立的工作区和索引，互不干扰
- **共享 .git**：所有 worktree 共享同一个 `.git` 仓库，节省磁盘空间
- **快速验证**：在一个 worktree 中开发，在另一个 worktree 中测试

### 1.3 Worktree 管理命令

```bash
# 创建 worktree（基于已有分支）
git worktree add c:\Users\86156\.trae-cn\worktrees\skiller\feat-mcp-tool-modular feature/mcp-tool-modular

# 创建 worktree（同时创建新分支）
git worktree add -b feature/progressive-sync c:\Users\86156\.trae-cn\worktrees\skiller\feat-progressive-sync develop

# 列出所有 worktree
git worktree list

# 查看指定 worktree 详情
git worktree list --porcelain

# 移除已完成的 worktree
git worktree remove c:\Users\86156\.trae-cn\worktrees\skiller\feat-mcp-tool-modular

# 强制移除（有未提交更改时）
git worktree remove --force c:\Users\86156\.trae-cn\worktrees\skiller\feat-mcp-tool-modular

# 清理失效的 worktree 记录（目录已被手动删除时）
git worktree prune

# 修剪并显示详情
git worktree prune --verbose
```

### 1.4 Worktree 使用规范

1. **命名约定**：worktree 目录名格式为 `feat-<分支简称>` 或 `fix-<分支简称>`
2. **及时清理**：分支合并后立即移除对应 worktree
3. **避免冲突**：不同 worktree 不要修改同一文件
4. **提交前检查**：在 worktree 中提交前，确认当前分支正确 `git branch --show-current`

---

## 2. 本地分支管理

### 2.1 分支总览

```
main ─────────────────────────────────────────────────────────────►
  └─ develop ─────────────────────────────────────────────────────►
       ├─ feature/mcp-tool-modular ──────┐ (阶段A)
       │                                  └─► develop
       ├─ feature/progressive-sync ──────┐ (阶段B)
       │                                  └─► develop
       ├─ feature/data-consistency ──────┐ (阶段C)
       │                                  └─► develop
       ├─ feature/config-hot-reload ─────┐ (阶段D)
       │                                  └─► develop
       └─ release/v8.1.0 ───────────────┐
                                          └─► main + develop
```

### 2.2 分支详细说明

| 分支 | 类型 | 创建时机 | 合并目标 | 说明 |
|------|------|----------|----------|------|
| `main` | 长期 | 初始化 | — | 生产就绪代码，仅通过 release 或 hotfix 合入 |
| `develop` | 长期 | 从 main 创建 | — | 开发主分支，当前工作分支，所有 feature 的最终归宿 |
| `feature/mcp-tool-modular` | 功能 | 阶段A启动时从 develop 创建 | develop | 重构阶段A：MCP工具模块化拆分 |
| `feature/progressive-sync` | 功能 | 阶段B启动时从 develop 创建 | develop | 重构阶段B：渐进式加载与同步机制 |
| `feature/data-consistency` | 功能 | 阶段C启动时从 develop 创建 | develop | 重构阶段C：数据一致性保障 |
| `feature/config-hot-reload` | 功能 | 阶段D启动时从 develop 创建 | develop | 重构阶段D：配置热更新机制 |
| `release/v8.1.0` | 发布 | 阶段A+B完成后从 develop 创建 | main + develop | 包含阶段A、B的发布版本 |
| `release/v8.2.0` | 发布 | 阶段C+D完成后从 develop 创建 | main + develop | 包含阶段C、D的发布版本 |

### 2.3 分支操作规范

```bash
# 创建 feature 分支（始终从最新的 develop 创建）
git checkout develop
git pull origin develop
git checkout -b feature/mcp-tool-modular

# feature 分支开发完成后合并回 develop（使用 --no-ff 保留合并记录）
git checkout develop
git merge --no-ff feature/mcp-tool-modular

# 创建 release 分支
git checkout -b release/v8.1.0 develop

# release 完成后合并到 main 和 develop
git checkout main
git merge --no-ff release/v8.1.0
git tag -a v8.1.0 -m "Release v8.1.0: 阶段A工具模块化 + 阶段B加载同步"

git checkout develop
git merge --no-ff release/v8.1.0

# 删除已合并的 feature/release 分支
git branch -d feature/mcp-tool-modular
git branch -d release/v8.1.0
```

### 2.4 分支保护规则

- `main`：禁止直接推送，必须通过 PR 合入
- `develop`：禁止强制推送，禁止 rebase 已推送的提交
- `feature/*`：开发者可自由推送，但合并前需通过 CI 检查

---

## 3. .gitignore 优化

### 3.1 当前项目根目录 .gitignore 审查

当前 `.gitignore` 已包含以下规则（状态评估）：

| 规则 | 状态 | 说明 |
|------|------|------|
| `.trae/*` / `!.trae/skills/xuansto-skill-v2/` | ✅ 良好 | 仅跟踪 skill 目录 |
| `.xuansto/` | ✅ 良好 | 排除运行时数据 |
| `.venv/` / `.venv2/` / `.venv_test/` / `.testvenv/` | ⚠️ 可优化 | 可合并为 `.venv*` |
| `__pycache__/` / `*.py[cod]` | ✅ 良好 | Python 缓存排除 |
| `.env` / `.env.local` / `.env.*.local` | ✅ 良好 | 环境变量保护 |
| `node_modules/` / `dist/` / `build/` | ✅ 良好 | 构建产物排除 |
| `*.db` / `*.sqlite3` | ✅ 良好 | 数据库文件排除 |
| `*.egg-info/` | ✅ 良好 | Python 包信息排除 |

### 3.2 建议优化项

```gitignore
# 优化：合并虚拟目录匹配
.venv*

# 新增：ChromaDB 向量数据库数据
chroma_data/
chroma_db/

# 新增：Python 类型存根缓存
.mypy_cache/

# 新增：测试与覆盖率
.pytest_cache/
.ruff_cache/
htmlcov/
.coverage
coverage.xml

# 新增：打包产物
*.whl
```

### 3.3 Skill 目录 .gitignore 审查

当前 `.trae/skills/xuansto-skill-v2/.gitignore` 规则评估：

| 规则 | 状态 | 说明 |
|------|------|------|
| `__pycache__/` / `*.py[cod]` | ✅ 良好 | Python 缓存 |
| `.knowledge/temp-scripts/*` / `!.knowledge/temp-scripts/.gitkeep` | ✅ 良好 | 临时脚本排除但保留目录 |
| `.knowledge/script-errors/*` / `!.knowledge/script-errors/.gitkeep` | ✅ 良好 | 错误日志排除但保留目录 |
| `.knowledge/backup/` | ✅ 良好 | 备份数据排除 |
| `*.db` / `*.sqlite3` | ✅ 良好 | 数据库文件排除 |
| `.env` / `.env.local` | ✅ 良好 | 环境变量保护 |
| `node_modules/` / `dist/` / `build/` | ✅ 良好 | 构建产物排除 |

### 3.4 .gitignore 管理原则

只让 Git 管理满足以下**全部条件**的文件：

1. **不可再生**：无法从其他源文件直接生成
2. **项目必需**：对项目构建和运行必不可少
3. **无安全风险**：不包含个人或机密信息

必须排除的文件类型：

| 类别 | 排除规则 | 原因 |
|------|----------|------|
| Python 缓存 | `__pycache__/`、`*.pyc`、`*.pyo` | 可自动生成 |
| 环境变量 | `.env`、`.env.local` | 包含密钥 |
| 依赖目录 | `node_modules/` | 可通过包管理器恢复 |
| 构建产物 | `dist/`、`build/`、`*.egg-info/` | 可自动构建 |
| 运行时数据 | `.xuansto/` | 运行时产生，非源码 |
| 向量数据库 | `chroma_data/`、`chroma_db/` | 可重建的索引数据 |
| IDE 配置 | `.idea/`、`.vscode/` | 个人环境配置 |
| 测试缓存 | `.pytest_cache/`、`.mypy_cache/` | 可自动生成 |

---

## 4. .gitattributes 完善

### 4.1 当前 .gitattributes 审查

当前配置已覆盖以下文件类型（状态评估）：

| 类别 | 规则 | 状态 |
|------|------|------|
| 默认行为 | `* text=auto eol=lf` | ✅ 良好 |
| Python | `*.py text eol=lf diff=python` | ✅ 良好 |
| Markdown | `*.md text eol=lf diff=markdown` | ✅ 良好 |
| YAML/JSON/TOML | `*.yaml text eol=lf diff=yaml` 等 | ✅ 良好 |
| JS/TS | `*.js text eol=lf diff=javascript` 等 | ✅ 良好 |
| Shell | `*.sh text eol=lf` | ✅ 良好 |
| PowerShell | `*.ps1 text eol=crlf` | ✅ 良好 |
| 二进制文件 | `*.png binary`、`*.dll binary` 等 | ✅ 良好 |
| 合并策略 | `*.lock text eol=lf merge=union` | ✅ 良好 |

### 4.2 建议补充项

```gitattributes
# Windows 批处理文件必须使用 CRLF
*.bat text eol=crlf
*.cmd text eol=crlf

# Docker 文件
Dockerfile text eol=lf
docker-compose*.yml text eol=lf diff=yaml

# Git 相关
*.patch text eol=lf

# 二进制文件补充
*.7z binary
*.rar binary
*.bz2 binary
*.xz binary
*.npy binary
*.npz binary
*.h5 binary
*.safetensors binary
```

### 4.3 完整 .gitattributes 规范

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
*.yaml text eol=lf diff=yaml
*.yml text eol=lf diff=yaml
*.json text eol=lf diff=json
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
*.ttf binary
*.otf binary
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
```

---

## 5. .git/info/exclude 本地忽略规则

`.git/info/exclude` 是仅对本地生效的忽略文件，不会被提交到仓库，适合存放个人偏好规则。

### 5.1 推荐配置

```gitignore
# 个人编辑器临时文件
*.swp
*.swo
*~

# 个人调试脚本
debug_*.py
test_local_*.py

# 个人笔记
NOTES.md
TODO_PERSONAL.md

# 大文件临时存储
*.dump
*.prof

# 本地实验性配置
local_*.yaml
local_*.json
```

### 5.2 设置命令

```bash
cat > .git/info/exclude << 'EOF'
# 个人编辑器临时文件
*.swp
*.swo
*~

# 个人调试脚本
debug_*.py
test_local_*.py

# 个人笔记
NOTES.md
TODO_PERSONAL.md

# 大文件临时存储
*.dump
*.prof

# 本地实验性配置
local_*.yaml
local_*.json
EOF
```

---

## 6. .github/ 目录检查与优化

### 6.1 当前目录结构

```
.github/
├── ISSUE_TEMPLATE/
│   ├── bug_report.yml        # Bug 报告模板
│   ├── config.yml            # Issue 模板配置
│   └── feature_request.yml   # 功能请求模板
├── workflows/
│   └── ci.yml                # CI 流水线
├── FUNDING.yml               # 赞助配置
└── PULL_REQUEST_TEMPLATE.md  # PR 模板
```

### 6.2 Issue 模板审查

#### bug_report.yml

当前模板包含以下字段，评估均为 ✅：

| 字段 | 类型 | 评估 |
|------|------|------|
| Component | checkboxes | ✅ 覆盖 MCP Server / Skill / Knowledge Base / Agent / Degradation |
| Severity | dropdown | ✅ P0-P3 四级分类 |
| Version | dropdown | ✅ 包含 v8.0.0-dev / v7.x |
| Bug Description | textarea | ✅ 必填 |
| Steps to Reproduce | textarea | ✅ 必填 |
| Expected Behavior | textarea | ✅ 必填 |
| Actual Behavior | textarea | ✅ 必填 |
| Reproduction Frequency | dropdown | ✅ Always/Rarely |
| Degradation Impact | checkboxes | ✅ 降级链影响评估 |
| Environment | textarea | ✅ |
| Relevant Logs | textarea | ✅ shell 渲染 |

**建议优化**：版本选项需随发布更新，添加 `v8.1.0`、`v8.2.0` 等。

#### feature_request.yml

当前模板包含以下字段，评估均为 ✅：

| 字段 | 类型 | 评估 |
|------|------|------|
| Component | checkboxes | ✅ |
| Problem Statement | textarea | ✅ 必填 |
| Motivation | textarea | ✅ |
| Proposed Solution | textarea | ✅ 必填 |
| Alternatives Considered | textarea | ✅ |
| Related UNIFIED Issue | input | ✅ 关联重构计划 |
| Target Progressive Loading Phase | dropdown | ✅ Phase 0-3 |
| Priority Assessment | dropdown | ✅ Critical-Low |

#### config.yml

当前配置 ✅：

- `blank_issues_enabled: false`：禁止空白 Issue
- 提供了 Documentation / Discussions / Security Policy 三个联系链接

### 6.3 PR 模板审查

当前 `PULL_REQUEST_TEMPLATE.md` 包含：

| 区块 | 评估 |
|------|------|
| Description | ✅ |
| Type of Change | ✅ 含 Bug fix / New feature / Breaking change / Refactoring / Degradation fix / Phase loading change / MCP tool addition/fix |
| Component | ✅ 含 MCP Server / Skill / Knowledge Base / Agent / Degradation Chain |
| Related Issues | ✅ |
| UNIFIED Issue | ✅ |
| Testing | ✅ 含 Unit / Integration / Degradation / Progressive loading / Manual |
| Breaking Changes | ✅ |
| Checklist | ✅ 含代码规范 / 自审 / 无密钥暴露 / UNIFIED 状态更新 |

### 6.4 CI/CD 流水线审查

当前 `ci.yml` 包含以下 Job：

| Job | 触发条件 | 评估 |
|-----|----------|------|
| lint | push/PR | ✅ ruff check + mypy |
| test | lint 通过后 | ✅ Python 3.10/3.11/3.12 矩阵测试 |
| degradation-test | 定时调度 | ✅ 降级链专项测试 |
| skill-validate | push/PR | ✅ YAML/JSON 格式校验 |

**建议新增的 Workflow**：

#### release.yml（发布流水线）

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Build package
        working-directory: xuansto-mcp-server
        run: |
          python -m pip install --upgrade pip build
          python -m build
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          generate_release_notes: true
```

### 6.5 建议补充的 GitHub 配置

#### 依赖审查（dependabot.yml）

```yaml
version: 2
updates:
  - package-ecosystem: pip
    directory: /xuansto-mcp-server
    schedule:
      interval: weekly
    open-pull-requests-limit: 5
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: monthly
```

---

## 7. 操作命令序列

### 7.1 初始化 Worktree 与分支

```bash
# 在主仓库中操作
cd D:\Projects\TraeProjects\skiller

# 确保 develop 分支最新
git checkout develop
git pull origin develop

# 创建阶段A的 feature 分支和 worktree
git branch feature/mcp-tool-modular develop
git worktree add c:\Users\86156\.trae-cn\worktrees\skiller\feat-mcp-tool-modular feature/mcp-tool-modular

# 创建阶段B的 feature 分支和 worktree
git branch feature/progressive-sync develop
git worktree add c:\Users\86156\.trae-cn\worktrees\skiller\feat-progressive-sync feature/progressive-sync

# 创建阶段C的 feature 分支和 worktree
git branch feature/data-consistency develop
git worktree add c:\Users\86156\.trae-cn\worktrees\skiller\feat-data-consistency feature/data-consistency

# 创建阶段D的 feature 分支和 worktree
git branch feature/config-hot-reload develop
git worktree add c:\Users\86156\.trae-cn\worktrees\skiller\feat-config-hot-reload feature/config-hot-reload

# 验证所有 worktree
git worktree list
```

### 7.2 阶段A开发流程示例

```bash
# 进入阶段A worktree
cd c:\Users\86156\.trae-cn\worktrees\skiller\feat-mcp-tool-modular

# 确认当前分支
git branch --show-current
# 预期输出: feature/mcp-tool-modular

# 开发过程中定期提交
git add .
git commit -m "feat(mcp): modularize tool registry"

# 推送到远程
git push origin feature/mcp-tool-modular

# 开发完成后，回到主仓库合并
cd D:\Projects\TraeProjects\skiller
git checkout develop
git merge --no-ff feature/mcp-tool-modular -m "merge: 阶段A - MCP工具模块化"

# 清理 worktree 和分支
git worktree remove c:\Users\86156\.trae-cn\worktrees\skiller\feat-mcp-tool-modular
git branch -d feature/mcp-tool-modular
```

### 7.3 发布流程

```bash
# 阶段A+B完成后创建 release
cd D:\Projects\TraeProjects\skiller
git checkout develop
git checkout -b release/v8.1.0

# 在 release 分支上修复版本号等
# ...

# 合并到 main
git checkout main
git merge --no-ff release/v8.1.0 -m "release: v8.1.0"
git tag -a v8.1.0 -m "Release v8.1.0: 阶段A工具模块化 + 阶段B加载同步"

# 合并回 develop
git checkout develop
git merge --no-ff release/v8.1.0

# 推送所有
git push origin main develop --tags

# 清理
git branch -d release/v8.1.0
```

### 7.4 .gitignore 和 .gitattributes 更新

```bash
# 更新 .gitignore 后刷新 Git 索引
git rm -r --cached .
git add .
git commit -m "chore: update .gitignore rules"

# 规范化已有文件的行尾（更新 .gitattributes 后）
git rm --cached -r .
git reset --hard
```

### 7.5 设置本地排除规则

```bash
# 编辑本地排除文件
# Windows 下使用 PowerShell
@"
# 个人编辑器临时文件
*.swp
*.swo
*~

# 个人调试脚本
debug_*.py
test_local_*.py

# 个人笔记
NOTES.md
TODO_PERSONAL.md

# 大文件临时存储
*.dump
*.prof

# 本地实验性配置
local_*.yaml
local_*.json
"@ | Set-Content -Path ".git/info/exclude" -Encoding UTF8
```

---

## 8. 分支与重构步骤映射

### 8.1 映射关系

| 重构阶段 | 分支名称 | Worktree 目录 | 核心目标 | 对应版本 |
|----------|----------|---------------|----------|----------|
| **阶段A**：工具模块化 | `feature/mcp-tool-modular` | `feat-mcp-tool-modular` | 将 MCP 工具从单体拆分为独立模块，支持按需加载 | v8.1.0 |
| **阶段B**：加载同步 | `feature/progressive-sync` | `feat-progressive-sync` | 实现渐进式加载与状态同步机制，Phase 0-3 分层 | v8.1.0 |
| **阶段C**：数据一致性 | `feature/data-consistency` | `feat-data-consistency` | 保障跨模块数据一致性，实现 resource_state.json 统一管理 | v8.2.0 |
| **阶段D**：配置热更新 | `feature/config-hot-reload` | `feat-config-hot-reload` | 支持运行时配置热更新，无需重启 MCP Server | v8.2.0 |

### 8.2 阶段依赖关系

```
阶段A (工具模块化)
  │
  ├──► 阶段B (加载同步)     ← 依赖A的模块化拆分结果
  │
  └──► 阶段C (数据一致性)   ← 依赖A的模块边界定义
        │
        └──► 阶段D (配置热更新) ← 依赖C的数据一致性机制
```

### 8.3 版本发布计划

| 版本 | 包含阶段 | 预期内容 |
|------|----------|----------|
| v8.0.0 | 当前基线 | 现有功能稳定版 |
| v8.1.0 | 阶段A + 阶段B | 工具模块化 + 渐进式加载同步 |
| v8.2.0 | 阶段C + 阶段D | 数据一致性 + 配置热更新 |

### 8.4 各阶段分支生命周期

```
develop ─────────────────────────────────────────────────────────────►
         │                                    │
         ├─ feature/mcp-tool-modular ─────────┤ 合并后删除
         │   (创建 → 开发 → 测试 → 合并)      │
         │                                    │
         ├─ feature/progressive-sync ─────────┤ 合并后删除
         │   (创建 → 开发 → 测试 → 合并)      │
         │                                    │
         │          release/v8.1.0 ───────────┤ 发布后删除
         │          (创建 → 稳定 → 发布)       │
         │                                    │
         ├─ feature/data-consistency ─────────┤ 合并后删除
         │   (创建 → 开发 → 测试 → 合并)      │
         │                                    │
         ├─ feature/config-hot-reload ────────┤ 合并后删除
         │   (创建 → 开发 → 测试 → 合并)      │
         │                                    │
         │          release/v8.2.0 ───────────┤ 发布后删除
         │          (创建 → 稳定 → 发布)       │
         │                                    │
main ────────────────────────────────────────────────────────────────►
              ↑ v8.1.0 tag        ↑ v8.2.0 tag
```

---

> **文档维护说明**：本文档应随项目版本迭代同步更新，特别是分支列表、版本号和阶段映射关系。每次 release 发布后需更新版本发布计划表。
