# Xuansto Skill v2 — Git/GitHub 管理方案

> **版本**: 5.0 | **日期**: 2026-05-27 | **基线版本**: 9.0.0
> **适用范围**: xuansto-skill-v2（Skill定义层）+ xuansto-mcp-server（MCP Server执行层）
> **Worktree 路径**: `c:\Users\86156\.trae-cn\worktrees\skiller\feat-develop-main-branch-60SHTK`
> **主仓库路径**: `D:\Projects\TraeProjects\skiller`

---

## 目录

1. [Git Worktree 并行开发策略](#1-git-worktree-并行开发策略)
2. [分支状态与生命周期](#2-分支状态与生命周期)
3. [.gitignore 审查与优化建议](#3-gitignore-审查与优化建议)
4. [.gitattributes 审查与优化建议](#4-gitattributes-审查与优化建议)
5. [.github/ 目录审查与优化建议](#5-github-目录审查与优化建议)
6. [v9.0.0 操作命令序列](#6-v900-操作命令序列)

---

## 1. Git Worktree 并行开发策略

### 1.1 当前 Worktree 架构（实际状态）

```
主仓库: D:\Projects\TraeProjects\skiller
├── .git/                                    # 主仓库 Git 数据库
│   └── worktrees/
│       ├── feat-develop-main-branch-60SHTK/ # 当前活跃 Worktree（本文档所在）
│       │   └── HEAD → ref: refs/heads/feat-develop-main-branch-60SHTK
│       ├── develop-main-branch-YzihpS/      # Worktree #2
│       │   └── HEAD → ref: refs/heads/develop-main-branch-YzihpS
│       ├── feat-develop-main-branch-H3MhdQ/ # Worktree #3
│       │   └── HEAD → ref: refs/heads/feat-develop-main-branch-H3MhdQ
│       ├── feat-develop-main-branch-oTKP5o/ # Worktree #4
│       │   └── HEAD → ref: refs/heads/feat-develop-main-branch-oTKP5o
│       ├── feat-develop-main-implement-g6ErtN/ # Worktree #5
│       │   └── HEAD → ref: refs/heads/feat-develop-main-implement-g6ErtN
│       └── skiller-develop/                 # Worktree #6
│           └── HEAD → ref: refs/heads/develop
│
└── (主仓库工作目录 — main 分支检出)

Worktree (当前): c:\Users\86156\.trae-cn\worktrees\skiller\feat-develop-main-branch-60SHTK
├── .git → gitdir: D:/Projects/TraeProjects/skiller/.git/worktrees/feat-develop-main-branch-60SHTK
├── .trae/skills/xuansto-skill-v2/           # Skill 定义层
├── xuansto-mcp-server/                      # MCP Server 执行层
├── scripts/                                 # 降级脚本 & Knowledge Server
├── docs/                                    # 文档
└── .github/                                 # CI/CD & 社区模板
```

### 1.2 Worktree 策略评估

| 评估维度 | 状态 | 说明 |
|----------|------|------|
| 并行开发能力 | ✅ 正常 | 6个 Worktree 可同时工作在不同分支 |
| 分支隔离性 | ✅ 正常 | 每个分支独立检出，互不干扰 |
| 命名规范 | ⚠️ 待改进 | Trae 自动生成的名称（如 `feat-develop-main-branch-60SHTK`）缺乏语义，无法从名称判断用途 |
| Worktree 清理 | ⚠️ 需关注 | 6个 Worktree 中部分可能已完成使命，需定期清理 |
| 与 develop 同步 | ✅ 正常 | 当前 Worktree 分支与 develop 指向同一 commit（064679a7） |

**关键发现**：

- 当前 Worktree 分支 `feat-develop-main-branch-60SHTK` 的 HEAD 与 `develop` 分支相同（`064679a7`），说明此分支从 develop 创建后尚未产生新提交，或已与 develop 完全同步
- `feat-develop-main-implement-g6ErtN` 同样与 develop 指向同一 commit
- `develop-main-branch-YzihpS` 和 `feat-develop-main-branch-H3MhdQ` 有独立提交，是活跃开发分支
- `feat-develop-main-branch-oTKP5o` 已推送到远程，有独立提交

### 1.3 Worktree 操作规范

| 操作 | 命令 | 说明 |
|------|------|------|
| 创建 Worktree | `git worktree add <路径> -b <分支名> <基线分支>` | 从基线分支创建新 Worktree |
| 列出 Worktree | `git worktree list` | 查看所有 Worktree 及其分支 |
| 删除 Worktree | `git worktree remove <路径>` | 删除已合并的 Worktree |
| 清理失效 Worktree | `git worktree prune` | 清理已删除目录的 Worktree 记录 |
| 锁定 Worktree | `git worktree lock <路径>` | 防止意外删除 |
| 解锁 Worktree | `git worktree unlock <路径>` | 解除锁定 |

### 1.4 Trae 环境 Worktree 特殊处理

当前 Worktree 位于 Trae 的 `.trae-cn\worktrees\` 目录下，需注意：

- `.git` 文件指向主仓库的 worktree 元数据目录
- `.trae/` 目录在 `.gitignore` 中有特殊白名单规则（仅跟踪 `xuansto-skill-v2/`）
- Worktree 内的 `.git/info/exclude` 路径为：`D:\Projects\TraeProjects\skiller\.git\worktrees\feat-develop-main-branch-60SHTK\info\exclude`
- 主仓库的 exclude 路径为：`D:\Projects\TraeProjects\skiller\.git\info\exclude`

---

## 2. 分支状态与生命周期

### 2.1 当前分支全景（实际状态）

#### 本地分支

| 分支名 | Commit SHA | 与 develop 关系 | 关联 Worktree | 状态 |
|--------|-----------|----------------|---------------|------|
| `main` | `e56e83ad` | 独立（发布线） | 主仓库工作目录 | 永久分支 |
| `develop` | `064679a7` | 基准 | skiller-develop | 永久分支 |
| `develop-main-branch-YzihpS` | `8cea8c9a` | 有独立提交 | develop-main-branch-YzihpS | 活跃开发 |
| `feat-develop-main-branch-60SHTK` | `064679a7` | 与 develop 同步 | 当前 Worktree | 活跃开发 |
| `feat-develop-main-branch-H3MhdQ` | `0537ab3c` | 有独立提交 | feat-develop-main-branch-H3MhdQ | 活跃开发 |
| `feat-develop-main-branch-oTKP5o` | `5fe7cf95` | 有独立提交 | feat-develop-main-branch-oTKP5o | 活跃开发 |
| `feat-develop-main-implement-g6ErtN` | `064679a7` | 与 develop 同步 | feat-develop-main-implement-g6ErtN | 活跃开发 |

#### 远程分支

| 分支名 | Commit SHA | 说明 |
|--------|-----------|------|
| `origin/main` | `ee882aaf` | 远程主分支（与本地 main 不同步） |
| `origin/develop` | `064679a7` | 远程开发主线（与本地 develop 同步） |
| `origin/feat-develop-main-branch-oTKP5o` | `5fe7cf95` | 已推送的 feature 分支 |
| `origin/feat-add-plan-document-xbkZQe` | — | 计划文档相关分支 |
| `origin/feat-add-plan-document-dsFOMQ` | — | 计划文档相关分支 |

#### 标签

| Tag | 说明 |
|-----|------|
| `v8.0.0` | 已发布版本 |
| `v8.1.0-dev` | 开发版本标签 |

**注意**：本地 `main`（e56e83ad）与 `origin/main`（ee882aaf）不同步，需在发布前执行 `git pull origin main` 同步。

### 2.2 分支命名规范

| 前缀 | 用途 | 示例 |
|------|------|------|
| `feature/` | 功能开发 | `feature/security-fix`, `feature/data-integration` |
| `hotfix/` | 紧急修复 | `hotfix/auth-bypass` |
| `release/` | 发布准备 | `release/v9.0.0` |
| `develop/v` | 版本开发基线 | `develop/v8.5` |

**当前问题**：Trae 自动生成的分支名（如 `feat-develop-main-branch-60SHTK`）不符合上述规范。建议在 v9.0.0 开发周期中采用语义化分支名。

### 2.3 版本路线图与分支对应

```
v8.0.0 (已发布) ─── tag: v8.0.0
  │
  ├─ v8.1.0-dev ─── tag: v8.1.0-dev
  │
  ├─ v8.5.0 ─── develop 基线（当前）
  │
  ├─ v8.5.1 ─── feature/security-fix 合并后打 tag
  │
  ├─ v8.6.0 ─── 阶段1+2合并后打 tag
  │
  ├─ v8.7.0 ─── 阶段3合并后打 tag
  │
  └─ v9.0.0 ─── 阶段4合并后打 tag（MAJOR版本）
```

### 2.4 合并策略

| 场景 | 策略 | 命令 |
|------|------|------|
| Feature → develop | Squash Merge（保持主线整洁） | `git merge --squash feature/xxx` |
| develop → main | Merge Commit + Tag | `git merge --no-ff develop && git tag -a v9.0.0` |
| hotfix → main | Merge Commit | `git merge --no-ff hotfix/xxx` |
| hotfix → develop | Cherry-pick | `git cherry-pick <commit-hash>` |
| Worktree 分支 → develop | Squash Merge 或 Merge Commit | 视变更规模而定 |

---

## 3. .gitignore 审查与优化建议

### 3.1 现有配置审查

项目包含3个 `.gitignore` 文件，层级关系如下：

```
.gitignore                                    # 根级（132行，覆盖最全）
├── .trae/skills/xuansto-skill-v2/.gitignore  # Skill层（36行，子集）
└── xuansto-mcp-server/.gitignore             # MCP Server层（53行，子集+特有）
```

### 3.2 根级 .gitignore 审查

| 分类 | 当前规则 | 评估 | 建议 |
|------|----------|------|------|
| Trae/Skill Runtime | `.trae/*` + 白名单 `!.trae/skills/xuansto-skill-v2/` | ✅ 正确 | 保持不变 |
| Knowledge 临时文件 | `.knowledge/temp-scripts/*` + `.gitkeep` 白名单 | ✅ 正确 | 保持不变 |
| Knowledge 备份 | `.knowledge/backup/` | ✅ 正确 | 保持不变 |
| Knowledge DB | `.knowledge/index/knowledge.db` | ⚠️ 与 `*.db` 重复 | 可移除此条，`*.db` 已覆盖 |
| `.xuansto/` | 运行时目录 | ✅ 正确 | 保持不变 |
| `chroma_db/` | ChromaDB 向量数据库 | ✅ 正确 | 保持不变 |
| MCP Server Runtime | `.skill-logs/` + `.agent_cache/` | ✅ 正确 | 保持不变 |
| MCP Server 知识 | `xuansto-mcp-server/data/knowledge/general/added-*` | ✅ 正确 | 保持不变 |
| Python 缓存 | `__pycache__/`, `*.py[cod]`, `*$py.class` 等 | ✅ 完整 | 保持不变 |
| Build Artifacts | `dist/`, `build/`, `*.egg-info/` 等 | ✅ 完整 | 保持不变 |
| Virtual Environments | `.venv*`, `venv/`, `.uv/` | ✅ 完整 | 保持不变 |
| IDE/Editor | `.idea/`, `.vscode/`, `.claude/`, `.cursor/`, `.windsurf/` | ✅ 覆盖主流IDE | 建议补充 `.zed/` |
| OS | `.DS_Store`, `Thumbs.db`, `Desktop.ini`, `._*` | ✅ 完整 | 保持不变 |
| Environment & Secrets | `.env*`, `credentials/`, `*.pem`, `*.key` 等 | ✅ 完整 | 保持不变 |
| Logs | `*.log`, `logs/`, `audit_log.jsonl` | ✅ 完整 | 保持不变 |
| Databases | `*.db`, `*.sqlite3` | ✅ 正确 | 保持不变 |
| Cache & Temporary | `*.bak`, `*.orig`, `*.tmp`, `*.temp`, `.cache/` | ✅ 完整 | 保持不变 |
| docs/plan 临时 | `docs/plan/*.tmp`, `docs/plan/*.bak` | ✅ 正确 | 保持不变 |
| Node.js | `node_modules/` | ✅ 正确 | 保持不变 |
| Python Tool Files | `.python-version`, `pip-log.txt` | ⚠️ `.python-version` 应在 exclude | 见 §3.5 |

### 3.3 Skill 层 .gitignore 审查

| 分类 | 当前规则 | 评估 | 建议 |
|------|----------|------|------|
| Python 缓存 | `__pycache__/`, `*.py[cod]`, `*.so` | ✅ 正确 | 与根级重复，可精简 |
| Knowledge 临时 | 与根级一致 | ✅ 正确 | 保持不变 |
| DB/Log | `*.db`, `*.sqlite3`, `*.log` | ✅ 正确 | 与根级重复，可精简 |
| OS | `.DS_Store`, `Thumbs.db`, `._*` | ✅ 正确 | 与根级重复，可精简 |
| IDE | `.idea/`, `.vscode/`, `*.swp` | ✅ 正确 | 与根级重复，可精简 |
| Env | `.env`, `.env.local`, `.env.*.local` | ✅ 正确 | 与根级重复，可精简 |
| Temp/Cache | `*.tmp`, `*.temp`, `.cache/` | ✅ 正确 | 与根级重复，可精简 |
| Node/Build | `node_modules/`, `dist/`, `build/` | ✅ 正确 | 与根级重复，可精简 |

**问题**：Skill 层 `.gitignore` 与根级存在大量重复规则。Git 的 `.gitignore` 是层级叠加的，子目录只需包含该目录特有的忽略规则。

### 3.4 MCP Server 层 .gitignore 审查

| 分类 | 当前规则 | 评估 | 建议 |
|------|----------|------|------|
| Python 缓存 | 与根级一致 | ✅ 正确 | 与根级重复，可精简 |
| Build | `*.egg-info/`, `*.egg`, `*.whl`, `dist/`, `build/` | ✅ 正确 | 与根级重复，可精简 |
| Virtual Environments | `.venv/`, `.venv2/`, `.testvenv/`, `venv/`, `.uv/` | ⚠️ `.venv2/`, `.testvenv/` 过于具体 | 根级 `.venv*` 通配已覆盖 |
| `.xuansto/` | 运行时目录 | ✅ 正确 | MCP Server 特有，保留 |
| Test 缓存 | `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/` | ✅ 正确 | 与根级重复，可精简 |
| Coverage | `.coverage`, `htmlcov/`, `.tox/`, `.nox/` 等 | ✅ 正确 | 与根级重复，可精简 |
| Test 输出 | `test_result*.txt`, `test_final.txt` | ✅ 特有规则 | 保留 |
| IDE/OS | 与根级一致 | ✅ 正确 | 与根级重复，可精简 |

### 3.5 优化建议

> **v9.0.0 更新**：以下部分建议已在 v9.0.0 中实施：
> - ✅ 子目录 .gitignore 已精简（Skill层和MCP Server层仅保留特有规则）
> - ✅ 根级 .gitignore 已补充 `.zed/`、`.trae-cn/` 等规则
> - ✅ `.knowledge/index/knowledge.db` 重复规则已移除

#### 建议1：精简子目录 .gitignore

**Skill 层 `.gitignore` 优化后**（仅保留特有规则）：

```gitignore
.knowledge/temp-scripts/*
!.knowledge/temp-scripts/.gitkeep
.knowledge/script-errors/*
!.knowledge/script-errors/.gitkeep
.knowledge/backup/
```

**MCP Server 层 `.gitignore` 优化后**（仅保留特有规则）：

```gitignore
.xuansto/
.skill-logs/
.agent_cache/
test_result*.txt
test_final.txt
```

#### 建议2：根级 .gitignore 补充项

```gitignore
.zed/
.trae-cn/
uv.lock.bak
```

#### 建议3：移除 `.python-version` 从根级 .gitignore

`.python-version` 是 pyenv 的版本锁定文件，在团队协作中应被跟踪。建议移至 `.git/info/exclude` 作为个人忽略规则。

#### 建议4：移除 `.knowledge/index/knowledge.db` 重复规则

根级已有 `*.db` 规则覆盖所有 `.db` 文件，此条属于冗余。

---

## 4. .gitattributes 审查与优化建议

### 4.1 现有配置审查

项目包含3个 `.gitattributes` 文件：

```
.gitattributes                                    # 根级（171行，最完整）
├── .trae/skills/xuansto-skill-v2/.gitattributes  # Skill层（17行，子集+特有）
└── xuansto-mcp-server/.gitattributes             # MCP Server层（9行，子集+特有）
```

### 4.2 根级 .gitattributes 审查

| 分类 | 当前规则 | 评估 | 建议 |
|------|----------|------|------|
| 全局默认 | `* text=auto eol=lf` | ✅ 正确 | 保持不变 |
| Python | `*.py text eol=lf diff=python` | ✅ 正确 | 保持不变 |
| 文档 | `*.md text eol=lf diff=markdown` | ✅ 正确 | 保持不变 |
| Config/Data | `*.yaml merge=union` 等 | ✅ 完整 | 保持不变 |
| Web | JS/TS/CSS/HTML | ✅ 完整 | 保持不变 |
| Shell/Scripts | `.sh=eol=lf`, `.bat/.cmd/.ps1=eol=crlf` | ✅ 正确 | 保持不变 |
| Binary | DB/Native/Image/Archive/Data/Font/Media | ✅ 完整 | 保持不变 |
| 项目特有合并策略 | `resource_state.json merge=union`, `spec-locks/*.json merge=union` | ✅ 正确 | 保持不变 |
| Linguist | `*.min.js linguist-generated` 等 | ✅ 正确 | 保持不变 |

### 4.3 Skill 层 .gitattributes 审查

| 分类 | 当前规则 | 评估 | 建议 |
|------|----------|------|------|
| 文档/Config | `*.md`, `*.yaml`, `*.json`, `*.toml` | ⚠️ 与根级重复 | 可精简 |
| Python/JS | `*.py`, `*.js` | ⚠️ 与根级重复 | 可精简 |
| PowerShell | `*.ps1 text eol=crlf` | ⚠️ 与根级重复 | 可精简 |
| Lock | `*.lock text eol=lf merge=union` | ⚠️ 与根级重复 | 可精简 |
| Binary | `*.db`, `*.sqlite3` | ⚠️ 与根级重复 | 可精简 |
| 项目特有 | `resource_state.json merge=union` | ⚠️ 与根级重复 | 可精简 |
| **特有** | `constraints.yaml merge=union` | ✅ Skill层特有 | **必须保留** |

### 4.4 MCP Server 层 .gitattributes 审查

| 分类 | 当前规则 | 评估 | 建议 |
|------|----------|------|------|
| Python | `*.py`, `*.pyi` | ⚠️ 与根级重复 | 可精简 |
| Config | `*.toml`, `*.cfg` | ⚠️ 与根级重复 | 可精简 |
| Binary | `*.db`, `*.sqlite3`, `*.pkl`, `*.parquet` | ⚠️ 与根级重复 | 可精简 |

### 4.5 优化建议

> **v9.0.0 更新**：以下部分建议已在 v9.0.0 中实施：
> - ✅ 子目录 .gitattributes 已精简（Skill层仅保留 `constraints.yaml merge=union`）
> - ✅ MCP Server 层 .gitattributes 已精简
> - ✅ 根级 .gitattributes 已补充 `*.toml merge=union`、`constraints.yaml merge=union`、`registry.yaml merge=union` 等规则

#### 建议1：精简子目录 .gitattributes

**Skill 层 `.gitattributes` 优化后**：

```gitattributes
constraints.yaml merge=union
```

**MCP Server 层 `.gitattributes` 优化后**：

```gitattributes
# 根级 .gitattributes 已覆盖所有文件类型，无需额外规则
```

> 如果 MCP Server 层 `.gitattributes` 优化后为空，可直接删除该文件。

#### 建议2：根级 .gitattributes 补充项

```gitattributes
*.ipynb text eol=lf diff=jupyter
*.toml merge=union
constraints.yaml merge=union
routes.yaml merge=union
registry.yaml merge=union
spec-locks/ linguist-generated
```

#### 建议3：补充 `.git-blame-ignore-revs`

用于隐藏代码格式化提交的 blame 记录：

```
# 格式化提交的 hash（ruff format 后填写）
# 示例：
# a1b2c3d4e5f6 ruff format: 统一代码风格
```

---

## 5. .github/ 目录审查与优化建议

### 5.1 现有目录结构

```
.github/
├── ISSUE_TEMPLATE/
│   ├── bug_report.yml          # Bug 报告模板
│   ├── config.yml              # Issue 模板配置
│   └── feature_request.yml     # 功能请求模板
├── workflows/
│   ├── ci.yml                  # CI 流水线
│   └── release.yml             # 发布流水线
├── FUNDING.yml                 # 资助配置
├── PULL_REQUEST_TEMPLATE.md    # PR 模板
└── dependabot.yml              # 依赖更新配置
```

### 5.2 CI Workflow（ci.yml）审查

| 配置项 | 当前值 | 评估 | 建议 |
|--------|--------|------|------|
| 触发分支(push) | main, develop, develop/v8, develop/v8.5, refactor/**, feature/** | ✅ 完整 | 保持不变 |
| 触发分支(PR) | main, develop, develop/v8, develop/v8.5 | ✅ 完整 | 保持不变 |
| 触发路径 | Skill + MCP Server + scripts | ✅ 合理 | 保持不变 |
| 定时任务 | 每日 06:00 UTC | ✅ 合理 | 保持不变 |
| Node.js 版本 | FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true | ✅ 前瞻性 | 保持不变 |
| Lint | ruff check + mypy | ⚠️ mypy 使用 `\|\| true` | mypy 应改为硬失败 |
| Test | Python 3.10/3.11/3.12 矩阵 | ✅ 完整 | 保持不变 |
| Degradation Test | 仅定时触发 | ✅ 合理 | 保持不变 |
| Skill Validate | YAML/JSON 校验 | ✅ 正确 | 保持不变 |
| Schema Validate | MCP Tool Schemas + spec-locks | ✅ 已实现 | 保持不变 |
| 版本一致性检查 | — | ✅ v9.0.0新增 | CI新增版本号一致性检查步骤 |

**关键优化**：mypy 改为硬失败（当前 `|| true` 会导致类型错误被忽略）：

```yaml
- name: Type check with mypy
  working-directory: xuansto-mcp-server
  run: mypy src/ --ignore-missing-imports
```

### 5.3 Release Workflow（release.yml）审查

| 配置项 | 当前值 | 评估 | 建议 |
|------|--------|------|------|
| 触发 | tag v* | ✅ 正确 | 保持不变 |
| Build | python -m build | ✅ 正确 | 保持不变 |
| Release | softprops/action-gh-release@v2 | ✅ 正确 | 保持不变 |
| Pre-release 检测 | rc/beta/alpha | ✅ 正确 | 保持不变 |
| PyPI 发布 | pypa/gh-action-pypi-publish | ✅ 正确 | 保持不变 |

**建议**：补充发布前验证步骤（安装 whl 并检查版本号）。

### 5.4 dependabot.yml 审查

| 配置项 | 当前值 | 评估 | 建议 |
|--------|--------|------|------|
| pip | xuansto-mcp-server 目录, 每周一 | ✅ 正确 | 保持不变 |
| github-actions | 根目录, 每周一 | ✅ 正确 | 保持不变 |
| open-pull-requests-limit | 5 | ✅ 合理 | 保持不变 |
| reviewers | xuanyuanchumo | ✅ 正确 | 保持不变 |

**建议**：补充提交消息前缀，保持 conventional commits 风格：

```yaml
commit-message:
  prefix: "chore(deps)"    # pip
  prefix: "chore(ci)"      # github-actions
```

### 5.5 Issue 模板审查

#### bug_report.yml

| 字段 | 当前值 | 评估 |
|------|--------|------|
| Component | MCP Server / Skill / KB / Agent / Degradation | ✅ 完整 |
| Severity | P0-P3 四级 | ✅ 合理 |
| Version | v8.5.x / v8.4.x / v8.3.x / v7.x / other | ✅ 已更新 |
| Degradation Impact | 三选项 | ✅ 项目特色 |

#### feature_request.yml

| 字段 | 当前值 | 评估 |
|------|--------|------|
| Component | 同 Bug Report | ✅ 完整 |
| Related UNIFIED Issue | input | ✅ 项目特色 |
| Target Progressive Loading Phase | Phase 0-3 | ✅ 项目特色 |
| Priority Assessment | Critical-Low | ✅ 合理 |

#### config.yml

| 配置 | 当前值 | 评估 |
|------|--------|------|
| blank_issues_enabled | false | ✅ 强制使用模板 |
| contact_links | Documentation / Discussions / Security | ✅ 完整 |

### 5.6 PR 模板审查

| 字段 | 当前值 | 评估 |
|------|--------|------|
| Type of Change | 8种类型（含 Degradation fix / Phase loading change） | ✅ 项目特色 |
| Component | 5种组件 | ✅ 完整 |
| UNIFIED Issue | 复选框 | ✅ 项目特色 |
| Testing | 6项检查 | ✅ 完整 |
| Checklist | 7项 | ✅ 完整 |

### 5.7 FUNDING.yml 审查

| 配置项 | 当前值 | 评估 |
|--------|--------|------|
| custom | `['https://github.com/xuanyuanchumo/xuansto']` | ✅ 正确 |

### 5.8 .editorconfig 审查

> **v9.0.0 更新**：.editorconfig 已补充 YAML 和 TOML 的缩进规则。

| 配置项 | 当前值 | 评估 | 建议 |
|--------|--------|------|------|
| root | true | ✅ 正确 | 保持不变 |
| [*] charset | utf-8 | ✅ 正确 | 保持不变 |
| [*] end_of_line | lf | ✅ 与 .gitattributes 一致 | 保持不变 |
| [*] insert_final_newline | true | ✅ 正确 | 保持不变 |
| [*.py] indent | space/4 | ✅ PEP 8 | 保持不变 |
| [*.{js,ts}] indent | space/2 | ✅ JS/TS 标准 | 保持不变 |
| [*.md] trim_trailing_whitespace | false | ✅ Markdown 需要 | 保持不变 |

**建议**：补充 YAML 和 TOML 的缩进规则：

```ini
[*.{yaml,yml}]
indent_style = space
indent_size = 2

[*.toml]
indent_style = space
indent_size = 2
```

### 5.9 缺失项建议

| 缺失项 | 说明 | 优先级 |
|--------|------|--------|
| `CODEOWNERS` | 代码所有者自动指派 Review | 中 |
| `.github/SECURITY.md` | 安全策略（config.yml 已引用链接） | 低 |
| `.github/workflows/codeql.yml` | CodeQL 安全扫描 | 低 |
| `.git-blame-ignore-revs` | 隐藏格式化提交的 blame 记录 | 低 |

---

## 6. v9.0.0 操作命令序列

> 以下命令在 Windows PowerShell 环境下执行，基于主仓库路径 `D:\Projects\TraeProjects\skiller`

### 6.1 从 Worktree 合并回 develop

```powershell
Set-Location "D:\Projects\TraeProjects\skiller"

git checkout develop

git merge --squash feat-develop-main-branch-60SHTK

git commit -m "feat: v9.0.0 开发 - 从 worktree 合并"

git push origin develop
```

### 6.2 创建 v9.0.0 Tag

```powershell
Set-Location "D:\Projects\TraeProjects\skiller"

git checkout main
git pull origin main

git merge --no-ff develop -m "release: v9.0.0"

git tag -a v9.0.0 -m "v9.0.0: 全面重构完成"

git push origin main --tags
git push origin develop
```

### 6.3 Release 自动化

Tag `v9.0.0` 推送后将自动触发 `.github/workflows/release.yml`：

1. **build** 作业：构建 Python 包（sdist + wheel）
2. **release** 作业：创建 GitHub Release（自动生成 Release Notes）
3. **publish-pypi** 作业：发布到 PyPI（仅稳定版本，不含 rc/beta/alpha）

### 6.4 清理已完成 Worktree

```powershell
Set-Location "D:\Projects\TraeProjects\skiller"

git worktree remove "c:\Users\86156\.trae-cn\worktrees\skiller\feat-develop-main-branch-60SHTK"

git branch -d feat-develop-main-branch-60SHTK

git worktree prune

git remote prune origin
```

### 6.5 完整发布流程（按顺序执行）

```powershell
# Step 1: 同步远程
Set-Location "D:\Projects\TraeProjects\skiller"
git fetch --all --tags

# Step 2: 确保 develop 是最新的
git checkout develop
git pull origin develop

# Step 3: 合并 Worktree 分支到 develop
git merge --squash feat-develop-main-branch-60SHTK
git commit -m "feat: v9.0.0 - 全面重构完成"
git push origin develop

# Step 4: 合并 develop 到 main
git checkout main
git pull origin main
git merge --no-ff develop -m "release: v9.0.0"

# Step 5: 打 tag
git tag -a v9.0.0 -m "v9.0.0: Token动态调整+架构一致性+指标合并+Git优化"

# Step 6: 推送（触发 Release workflow）
git push origin main --tags
git push origin develop

# Step 7: 清理
git worktree prune
git remote prune origin
git branch --merged develop | Where-Object { $_ -notmatch 'main|develop|\*' } | ForEach-Object { git branch -d $_.Trim() }
```

---

## 附录A：快速参考卡片

### Git Worktree 常用命令

```
创建:  git worktree add <路径> -b <分支> <基线>
列表:  git worktree list
删除:  git worktree remove <路径>
清理:  git worktree prune
锁定:  git worktree lock <路径>
解锁:  git worktree unlock <路径>
```

### 分支命名规范

```
feature/<阶段描述>    功能开发分支
hotfix/<问题描述>     紧急修复分支
release/<版本号>      发布准备分支
develop/v<版本>       版本开发基线
```

### 关键路径速查

| 项目 | 路径 |
|------|------|
| 主仓库 | `D:\Projects\TraeProjects\skiller` |
| 当前 Worktree | `c:\Users\86156\.trae-cn\worktrees\skiller\feat-develop-main-branch-60SHTK` |
| Worktree 元数据 | `D:\Projects\TraeProjects\skiller\.git\worktrees\feat-develop-main-branch-60SHTK` |
| 主仓库 exclude | `D:\Projects\TraeProjects\skiller\.git\info\exclude` |
| Worktree exclude | `D:\Projects\TraeProjects\skiller\.git\worktrees\feat-develop-main-branch-60SHTK\info\exclude` |
| exclude 模板 | `.git-info-exclude-template`（项目根目录） |

### 提交消息规范

```
feat(phase0): 安全紧急修复完成
fix(mcp): 修复Resource订阅未暴露问题
refactor(data): 合并双SQLite实例
chore(ci): 补充Schema校验步骤
docs(plan): 更新重构计划
test(degradation): 补充降级链路测试
```
