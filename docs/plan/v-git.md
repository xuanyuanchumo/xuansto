# Xuansto Skill v2 — Git/GitHub 管理方案

> **版本**: 1.0 | **日期**: 2026-05-26 | **基线版本**: 8.4.0
> **适用范围**: xuansto-skill-v2（Skill定义层）+ xuansto-mcp-server（MCP Server执行层）
> **Worktree 路径**: `c:\Users\86156\.trae-cn\worktrees\skiller\feat-develop-main-branch-H3MhdQ`
> **主仓库路径**: `D:\Projects\TraeProjects\skiller`

---

## 目录

1. [Git Worktree 并行开发策略](#1-git-worktree-并行开发策略)
2. [本地分支管理方案](#2-本地分支管理方案)
3. [.gitignore 审查与优化建议](#3-gitignore-审查与优化建议)
4. [.gitattributes 审查与优化建议](#4-gitattributes-审查与优化建议)
5. [.git/info/exclude 审查与优化建议](#5-gitinfoexclude-审查与优化建议)
6. [.github/ 目录审查与优化建议](#6-github-目录审查与优化建议)
7. [可直接执行的操作命令序列](#7-可直接执行的操作命令序列)
8. [分支与重构步骤映射表](#8-分支与重构步骤映射表)

---

## 1. Git Worktree 并行开发策略

### 1.1 当前 Worktree 架构

```
主仓库: D:\Projects\TraeProjects\skiller
├── .git/                                    # 主仓库 Git 数据库
│   └── worktrees/
│       └── feat-develop-main-branch-H3MhdQ/ # 当前 Worktree 元数据
│           ├── HEAD    → ref: refs/heads/feat-develop-main-branch-H3MhdQ
│           └── commondir → ../..
│
└── (主仓库工作目录 — develop 分支检出)

Worktree: c:\Users\86156\.trae-cn\worktrees\skiller\feat-develop-main-branch-H3MhdQ
├── .git → gitdir: D:/Projects/TraeProjects/skiller/.git/worktrees/feat-develop-main-branch-H3MhdQ
├── .trae/skills/xuansto-skill-v2/           # Skill 定义层
├── xuansto-mcp-server/                      # MCP Server 执行层
├── scripts/                                 # 降级脚本 & Knowledge Server
├── docs/                                    # 文档
└── .github/                                 # CI/CD & 社区模板
```

### 1.2 Worktree 目录结构设计

基于重构计划的6个阶段，设计以下 Worktree 并行开发布局：

```
D:\Projects\TraeProjects\skiller\                    # 主仓库（develop 分支）
│
├─ worktrees\
│   ├─ phase0-status-verify\                         # 阶段0: 状态验证
│   │   └─ 分支: feature/status-verify
│   │
│   ├─ phase1-data-unification\                      # 阶段1: 数据层统一
│   │   └─ 分支: feature/data-unification
│   │
│   ├─ phase2-api-unification\                       # 阶段2: 接口层统一
│   │   └─ 分支: feature/api-unification
│   │
│   ├─ phase3-mcp-enhance\                           # 阶段3: MCP层增强
│   │   └─ 分支: feature/mcp-enhance
│   │
│   ├─ phase4-skill-optimize\                        # 阶段4: Skill层优化
│   │   └─ 分支: feature/skill-optimize
│   │
│   └─ phase5-cleanup-verify\                        # 阶段5: 清理与验证
│       └─ 分支: feature/cleanup-verify
│
└─ (主仓库工作目录 — develop/v8.4 分支检出)
```

### 1.3 Worktree 操作规范

| 操作 | 命令 | 说明 |
|------|------|------|
| 创建 Worktree | `git worktree add <路径> -b <分支名> <基线分支>` | 从基线分支创建新 Worktree |
| 列出 Worktree | `git worktree list` | 查看所有 Worktree 及其分支 |
| 删除 Worktree | `git worktree remove <路径>` | 删除已合并的 Worktree |
| 清理失效 Worktree | `git worktree prune` | 清理已删除目录的 Worktree 记录 |
| 锁定 Worktree | `git worktree lock <路径>` | 防止意外删除（如包含未提交更改） |
| 解锁 Worktree | `git worktree unlock <路径>` | 解除锁定 |

### 1.4 Worktree 并行开发约束

1. **同一分支不可在多个 Worktree 中检出**：Git 禁止同一分支同时在两个 Worktree 中检出
2. **阶段间依赖关系**：阶段1依赖阶段0，阶段2依赖阶段1，不可真正并行；但阶段3/4可在阶段2完成后并行
3. **合并顺序**：必须按阶段0→1→2→3→4→5顺序合并到 develop/v8.4
4. **冲突预防**：每个阶段修改的文件尽量不重叠（参考 REFACTOR_PLAN.md 的文件影响范围统计）

### 1.5 Trae 环境 Worktree 特殊处理

当前 Worktree 位于 Trae 的 `.trae-cn\worktrees\` 目录下，需注意：

- `.git` 文件指向主仓库的 worktree 元数据目录
- `.trae/` 目录在 `.gitignore` 中有特殊白名单规则（仅跟踪 `xuansto-skill-v2/`）
- Worktree 内的 `.git/info/exclude` 路径为：`D:\Projects\TraeProjects\skiller\.git\worktrees\feat-develop-main-branch-H3MhdQ\info\exclude`
- 主仓库的 exclude 路径为：`D:\Projects\TraeProjects\skiller\.git\info\exclude`

---

## 2. 本地分支管理方案

### 2.1 分支列表与生命周期

```
main ───────────────────────────────────────────────────────────→ 稳定发布
  │
  └─ develop ───────────────────────────────────────────────────→ 开发主线
       │
       └─ develop/v8.4 ─────────────────────────────────────────→ v8.4.x 开发基线
            │
            ├─ feature/status-verify        (阶段0) ──→ 合并到 develop/v8.4
            ├─ feature/data-unification     (阶段1) ──→ 合并到 develop/v8.4
            ├─ feature/api-unification      (阶段2) ──→ 合并到 develop/v8.4
            ├─ feature/mcp-enhance          (阶段3) ──→ 合并到 develop/v8.4
            ├─ feature/skill-optimize       (阶段4) ──→ 合并到 develop/v8.4
            ├─ feature/cleanup-verify       (阶段5) ──→ 合并到 develop/v8.4
            │
            ├─ feature/mcp-core             (MCP核心修复) ──→ 合并到 develop/v8.4
            ├─ feature/progressive-loading  (渐进式加载) ──→ 合并到 develop/v8.4
            │
            ├─ hotfix/*                     (紧急修复) ──→ 合并到 main + develop/v8.4
            └─ release/v8.4.0               (发布准备) ──→ 合并到 main
```

### 2.2 分支详细说明

| 分支名 | 基线 | 创建时机 | 合并目标 | 生命周期 | 负责内容 |
|--------|------|----------|----------|----------|----------|
| `main` | — | 初始 | — | 永久 | 稳定发布版本 |
| `develop` | main | 初始 | main | 永久 | 开发主线集成 |
| `develop/v8.4` | develop | v8.4开发启动 | develop | 版本发布后归档 | v8.4.x 迭代基线 |
| `feature/status-verify` | develop/v8.4 | 阶段0启动 | develop/v8.4 | 阶段0完成后删除 | PROBLEM.md状态校验+6个待验证问题审计 |
| `feature/data-unification` | develop/v8.4 | 阶段1启动 | develop/v8.4 | 阶段1完成后删除 | 双SQLite合并+双写一致性修复 |
| `feature/api-unification` | develop/v8.4 | 阶段2启动 | develop/v8.4 | 阶段2完成后删除 | 统一响应格式+降级映射对齐 |
| `feature/mcp-enhance` | develop/v8.4 | 阶段3启动 | develop/v8.4 | 阶段3完成后删除 | Resource订阅暴露+审计查询Tool |
| `feature/skill-optimize` | develop/v8.4 | 阶段4启动 | develop/v8.4 | 阶段4完成后删除 | 内嵌门禁补全+Token预算关联 |
| `feature/cleanup-verify` | develop/v8.4 | 阶段5启动 | develop/v8.4 | 阶段5完成后删除 | v1归档+版本号统一+全量回归 |
| `feature/mcp-core` | develop/v8.4 | 随时 | develop/v8.4 | 修复完成后删除 | MCP核心Bug修复（不依赖重构阶段） |
| `feature/progressive-loading` | develop/v8.4 | 随时 | develop/v8.4 | 完成后删除 | 渐进式加载增强 |
| `hotfix/*` | main | 紧急Bug发现 | main + develop/v8.4 | 修复后删除 | 生产环境紧急修复 |
| `release/v8.4.0` | develop/v8.4 | 发布准备 | main + develop | 发布后删除 | 版本发布准备 |

### 2.3 分支创建与合并时机

#### 创建时机

```
阶段0 启动 → git checkout -b feature/status-verify develop/v8.4
阶段1 启动 → git checkout -b feature/data-unification develop/v8.4
阶段2 启动 → git checkout -b feature/api-unification develop/v8.4
阶段3 启动 → git checkout -b feature/mcp-enhance develop/v8.4
阶段4 启动 → git checkout -b feature/skill-optimize develop/v8.4
阶段5 启动 → git checkout -b feature/cleanup-verify develop/v8.4
```

#### 合并时机（必须按顺序）

```
阶段0 完成并通过CI → 合并 feature/status-verify → develop/v8.4
阶段1 完成并通过CI → 合并 feature/data-unification → develop/v8.4
阶段2 完成并通过CI → 合并 feature/api-unification → develop/v8.4
阶段3 完成并通过CI → 合并 feature/mcp-enhance → develop/v8.4
阶段4 完成并通过CI → 合并 feature/skill-optimize → develop/v8.4
阶段5 完成并通过CI → 合并 feature/cleanup-verify → develop/v8.4
全部完成 → 合并 develop/v8.4 → develop → main（打 tag v8.5.0）
```

#### 合并策略

| 场景 | 策略 | 命令 |
|------|------|------|
| Feature → develop/v8.4 | Squash Merge（保持主线整洁） | `git merge --squash feature/xxx` |
| develop/v8.4 → develop | Merge Commit（保留版本里程碑） | `git merge --no-ff develop/v8.4` |
| develop → main | Merge Commit + Tag | `git merge --no-ff develop && git tag -a v8.5.0` |
| hotfix → main | Merge Commit | `git merge --no-ff hotfix/xxx` |
| hotfix → develop/v8.4 | Cherry-pick | `git cherry-pick <commit-hash>` |

### 2.4 版本路线图与分支对应

```
v8.4.0 (基线) ─── develop/v8.4 创建
  │
  ├─ v8.4.1 ─── feature/status-verify 合并后打 tag
  │
  ├─ v8.5.0 ─── 阶段1~4全部合并后打 tag
  │             develop/v8.5 创建
  │
  ├─ v8.6.0 ─── 阶段5合并后打 tag
  │             develop/v8.6 创建
  │
  ├─ v8.7.0 ─── 后续优化
  │
  ├─ v8.8.0 ─── 后续优化
  │
  └─ v9.0.0 ─── 重大版本升级（如有破坏性变更）
```

---

## 3. .gitignore 审查与优化建议

### 3.1 现有配置审查

项目包含3个 `.gitignore` 文件，层级关系如下：

```
.gitignore                                    # 根级（128行，覆盖最全）
├── .trae/skills/xuansto-skill-v2/.gitignore  # Skill层（36行，子集）
└── xuansto-mcp-server/.gitignore             # MCP Server层（53行，子集+特有）
```

#### 3.1.1 根级 .gitignore 审查

| 分类 | 当前规则 | 评估 | 建议 |
|------|----------|------|------|
| Trae/Skill Runtime | `.trae/*` + 白名单 `!.trae/skills/xuansto-skill-v2/` | ✅ 正确 | 保持不变 |
| Knowledge 临时文件 | `.knowledge/temp-scripts/*` + `.gitkeep` 白名单 | ✅ 正确 | 保持不变 |
| Knowledge 备份 | `.knowledge/backup/` | ✅ 正确 | 保持不变 |
| Knowledge DB | `.knowledge/index/knowledge.db` | ⚠️ 与 `*.db` 重复 | 可移除此条，`*.db` 已覆盖 |
| `.xuansto/` | 运行时目录 | ✅ 正确 | 保持不变 |
| `chroma_db/` | ChromaDB 向量数据库 | ✅ 正确 | 保持不变 |
| MCP Server Runtime | `.skill-logs/` + `.agent_cache/` | ✅ 正确 | 保持不变 |
| Python 缓存 | `__pycache__/`, `*.py[cod]` 等 | ✅ 完整 | 保持不变 |
| Build Artifacts | `dist/`, `build/`, `*.egg-info/` 等 | ✅ 完整 | 保持不变 |
| Virtual Environments | `.venv*`, `venv/`, `.uv/` | ✅ 完整 | 保持不变 |
| IDE/Editor | `.idea/`, `.vscode/`, `.claude/`, `.cursor/`, `.windsurf/` | ✅ 覆盖主流IDE | 建议补充 `.zed/` |
| OS | `.DS_Store`, `Thumbs.db`, `Desktop.ini`, `._*` | ✅ 完整 | 保持不变 |
| Environment & Secrets | `.env*`, `credentials/`, `*.pem`, `*.key` 等 | ✅ 完整 | 保持不变 |
| Logs | `*.log`, `logs/`, `audit_log.jsonl` | ✅ 完整 | 保持不变 |
| Databases | `*.db`, `*.sqlite3` | ✅ 正确 | 保持不变 |
| Cache & Temporary | `*.bak`, `*.orig`, `*.tmp`, `*.temp`, `.cache/` | ✅ 完整 | 保持不变 |
| Node.js | `node_modules/` | ✅ 正确 | 保持不变 |
| Python Tool Files | `.python-version`, `pip-log.txt` | ⚠️ `.python-version` 应在 exclude | 见 §5 |

#### 3.1.2 Skill 层 .gitignore 审查

| 分类 | 当前规则 | 评估 | 建议 |
|------|----------|------|------|
| Python 缓存 | `__pycache__/`, `*.py[cod]`, `*.so` | ✅ 正确 | 保持不变 |
| Knowledge 临时 | 与根级一致 | ✅ 正确 | 保持不变 |
| DB/Log | `*.db`, `*.sqlite3`, `*.log` | ✅ 正确 | 保持不变 |
| OS | `.DS_Store`, `Thumbs.db`, `._*` | ✅ 正确 | 保持不变 |
| IDE | `.idea/`, `.vscode/`, `*.swp` | ✅ 正确 | 保持不变 |
| Env | `.env`, `.env.local`, `.env.*.local` | ✅ 正确 | 保持不变 |
| Temp/Cache | `*.tmp`, `*.temp`, `.cache/` | ✅ 正确 | 保持不变 |
| Node/Build | `node_modules/`, `dist/`, `build/` | ✅ 正确 | 保持不变 |

**问题**：Skill 层 `.gitignore` 与根级存在大量重复规则。Git 的 `.gitignore` 是层级叠加的，子目录的 `.gitignore` 只需包含该目录特有的忽略规则即可。

#### 3.1.3 MCP Server 层 .gitignore 审查

| 分类 | 当前规则 | 评估 | 建议 |
|------|----------|------|------|
| Python 缓存 | 与根级一致 | ✅ 正确 | 保持不变 |
| Build | `*.egg-info/`, `*.egg`, `*.whl`, `dist/`, `build/` | ✅ 正确 | 保持不变 |
| Virtual Environments | `.venv/`, `.venv2/`, `.testvenv/`, `venv/`, `.uv/` | ⚠️ `.venv2/`, `.testvenv/` 过于具体 | 根级 `.venv*` 通配已覆盖 |
| `.xuansto/` | 运行时目录 | ✅ 正确 | 保持不变 |
| Test 缓存 | `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/` | ✅ 正确 | 保持不变 |
| Coverage | `.coverage`, `htmlcov/`, `.tox/`, `.nox/` 等 | ✅ 正确 | 保持不变 |
| Test 输出 | `test_result*.txt`, `test_final.txt` | ✅ 特有规则 | 保持不变 |
| IDE/OS | 与根级一致 | ✅ 正确 | 保持不变 |

### 3.2 优化建议

#### 建议1：精简子目录 .gitignore（减少维护负担）

**原则**：子目录 `.gitignore` 仅包含该目录特有的忽略规则，通用规则由根级统一管理。

**Skill 层 `.gitignore` 优化后**（仅保留特有规则）：

```gitignore
# Skill层特有：Knowledge 运行时文件
.knowledge/temp-scripts/*
!.knowledge/temp-scripts/.gitkeep
.knowledge/script-errors/*
!.knowledge/script-errors/.gitkeep
.knowledge/backup/
```

**MCP Server 层 `.gitignore` 优化后**（仅保留特有规则）：

```gitignore
# MCP Server特有：运行时目录
.xuansto/
.skill-logs/
.agent_cache/

# MCP Server特有：测试输出
test_result*.txt
test_final.txt
```

#### 建议2：根级 .gitignore 补充项

```gitignore
# 补充：Zed 编辑器
.zed/

# 补充：Trae Worktree 元数据（不应被跟踪）
.trae-cn/

# 补充：uv.lock 备份
uv.lock.bak
```

#### 建议3：移除 `.python-version` 从根级 .gitignore

`.python-version` 是 pyenv 的版本锁定文件，在团队协作中应被跟踪（确保所有开发者使用相同的 Python 版本）。建议移至 `.git/info/exclude` 作为个人忽略规则。

---

## 4. .gitattributes 审查与优化建议

### 4.1 现有配置审查

项目包含3个 `.gitattributes` 文件：

```
.gitattributes                                    # 根级（170行，最完整）
├── .trae/skills/xuansto-skill-v2/.gitattributes  # Skill层（17行，子集+特有）
└── xuansto-mcp-server/.gitattributes             # MCP Server层（9行，子集+特有）
```

#### 4.1.1 根级 .gitattributes 审查

| 分类 | 当前规则 | 评估 | 建议 |
|------|----------|------|------|
| 全局默认 | `* text=auto eol=lf` | ✅ 正确 | 保持不变 |
| Python | `*.py text eol=lf diff=python` | ✅ 正确 | 保持不变 |
| 文档 | `*.md text eol=lf diff=markdown` | ✅ 正确 | 保持不变 |
| Config/Data | `*.yaml merge=union` 等 | ✅ 完整 | 保持不变 |
| Web | JS/TS/CSS/HTML | ✅ 完整 | 保持不变 |
| Shell/Scripts | `.sh=eol=lf`, `.bat/.cmd/.ps1=eol=crlf` | ✅ 正确 | 保持不变 |
| Binary | DB/Native/Image/Archive/Data/Font/Media | ✅ 完整 | 保持不变 |
| 项目特有合并策略 | `resource_state.json merge=union` | ✅ 正确 | 保持不变 |
| Linguist | `*.min.js linguist-generated` 等 | ✅ 正确 | 保持不变 |

#### 4.1.2 Skill 层 .gitattributes 审查

| 分类 | 当前规则 | 评估 | 建议 |
|------|----------|------|------|
| 文档/Config | `*.md`, `*.yaml`, `*.json`, `*.toml` | ⚠️ 与根级重复 | 可精简 |
| Python/JS | `*.py`, `*.js` | ⚠️ 与根级重复 | 可精简 |
| PowerShell | `*.ps1 text eol=crlf` | ⚠️ 与根级重复 | 可精简 |
| Lock | `*.lock text eol=lf merge=union` | ⚠️ 与根级重复 | 可精简 |
| Binary | `*.db`, `*.sqlite3` | ⚠️ 与根级重复 | 可精简 |
| 项目特有 | `resource_state.json merge=union` | ⚠️ 与根级重复 | 可精简 |
| **特有** | `constraints.yaml merge=union` | ✅ Skill层特有 | **必须保留** |

#### 4.1.3 MCP Server 层 .gitattributes 审查

| 分类 | 当前规则 | 评估 | 建议 |
|------|----------|------|------|
| Python | `*.py`, `*.pyi` | ⚠️ 与根级重复 | 可精简 |
| Config | `*.toml`, `*.cfg` | ⚠️ 与根级重复 | 可精简 |
| Binary | `*.db`, `*.sqlite3`, `*.pkl`, `*.parquet` | ⚠️ 与根级重复 | 可精简 |

### 4.2 优化建议

#### 建议1：精简子目录 .gitattributes

与 `.gitignore` 同理，子目录仅保留特有规则。

**Skill 层 `.gitattributes` 优化后**：

```gitattributes
# Skill层特有：constraints.yaml 使用 union 合并策略
# （多个开发者可能同时修改约束配置）
constraints.yaml merge=union
```

**MCP Server 层 `.gitattributes` 优化后**：

```gitattributes
# MCP Server特有：无需额外规则
# （根级 .gitattributes 已覆盖所有文件类型）
```

> 如果 MCP Server 层 `.gitattributes` 优化后为空，可直接删除该文件。

#### 建议2：根级 .gitattributes 补充项

```gitattributes
# 补充：Jupyter Notebook（diff 友好）
*.ipynb text eol=lf diff=jupyter

# 补充：TOML merge 策略（pyproject.toml 常被多人修改）
*.toml merge=union

# 补充：Skill 层关键配置文件合并策略
constraints.yaml merge=union
routes.yaml merge=union
registry.yaml merge=union

# 补充：spec-locks 目录标记为生成文件
spec-locks/ linguist-generated
```

#### 建议3：补充 `.git-blame-ignore-revs`

用于隐藏代码格式化提交的 blame 记录：

```gitignore
# 格式化提交的 hash（ruff format 后填写）
# 示例：
# a1b2c3d4e5f6 ruff format: 统一代码风格
```

---

## 5. .git/info/exclude 审查与优化建议

### 5.1 现有模板审查

项目提供了 `.git-info-exclude-template` 模板文件，包含以下分类：

| 分类 | 规则 | 评估 |
|------|------|------|
| Editor-specific | `*.sublime-project`, `*.swp` 等 | ✅ 合理 |
| OS-specific | `desktop.ini`, `ehthumbs.db` | ✅ 合理 |
| Local development | `docker-compose.override.yml`, `.local/` | ✅ 合理 |
| Debug files | `*.pyc`, `debug/`, `debug_*.py` 等 | ✅ 合理 |
| Personal notes | `NOTES.md`, `TODO_PERSONAL.md` | ✅ 合理 |
| Large file temp | `*.dump`, `*.prof`, `*.heap` | ✅ 合理 |
| Local experimental | `local_*.yaml`, `local_*.json`, `local_*.toml` | ✅ 合理 |
| Personal Python | `.python-version` | ✅ 合理（从 .gitignore 移出） |
| Personal toolchain | `.tool-versions` | ✅ 合理 |

### 5.2 优化建议

#### 建议1：补充 Trae 环境特有规则

```gitignore
# Trae Worktree 本地调试
.trae-debug/
trae_local_*.py
```

#### 建议2：补充数据库本地调试规则

```gitignore
# 本地数据库调试文件
*.db-journal
*.db-wal
*.sqlite3-journal
*.sqlite3-wal
```

#### 建议3：补充 MCP Server 本地测试规则

```gitignore
# MCP Server 本地测试输出
test_output/
benchmark_results/
```

### 5.3 优化后的完整 exclude 模板

```gitignore
# Git local exclude rules
# This file is NOT tracked by git - add your personal ignore patterns here
# These rules only apply to your local repository
#
# INSTALL: Copy this file to your git info directory:
#   For worktree: copy .git-info-exclude-template to <gitdir>/info/exclude
#     Current worktree: D:\Projects\TraeProjects\skiller\.git\worktrees\feat-develop-main-branch-H3MhdQ\info\exclude
#   For regular repo: copy .git-info-exclude-template to .git/info/exclude
#     Main repo: D:\Projects\TraeProjects\skiller\.git\info\exclude

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

# ===== Trae Worktree 本地调试 =====
.trae-debug/
trae_local_*.py

# ===== 数据库本地调试文件 =====
*.db-journal
*.db-wal
*.sqlite3-journal
*.sqlite3-wal

# ===== MCP Server 本地测试输出 =====
test_output/
benchmark_results/
```

---

## 6. .github/ 目录审查与优化建议

### 6.1 现有目录结构

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

### 6.2 Issue 模板审查

#### 6.2.1 bug_report.yml

| 字段 | 当前值 | 评估 | 建议 |
|------|--------|------|------|
| Component | MCP Server / Skill / KB / Agent / Degradation | ✅ 完整 | 保持不变 |
| Severity | P0-P3 四级 | ✅ 合理 | 保持不变 |
| Version | v8.0.0-dev / v7.x / other | ⚠️ 版本列表过时 | 更新为 v8.4.x / v8.3.x / v7.x / other |
| Bug Description | textarea | ✅ 正确 | 保持不变 |
| Steps to Reproduce | textarea | ✅ 正确 | 保持不变 |
| Expected/Actual Behavior | textarea | ✅ 正确 | 保持不变 |
| Reproduction Frequency | Always/Often/Sometimes/Rarely | ✅ 合理 | 保持不变 |
| Degradation Impact | 三选项 | ✅ 项目特色 | 保持不变 |
| Environment | textarea | ✅ 正确 | 保持不变 |
| Relevant Logs | textarea (shell render) | ✅ 正确 | 保持不变 |

**建议**：更新 Version 下拉选项，增加重构阶段关联字段：

```yaml
- type: dropdown
  id: version
  attributes:
    label: Version
    options:
      - v8.4.x (current develop)
      - v8.3.x
      - v7.x
      - other
  validations:
    required: true

- type: input
  id: unified_issue
  attributes:
    label: Related UNIFIED Issue
    description: UNIFIED issue number from REFACTOR_PLAN (e.g., NEW-07, DB-02)
```

#### 6.2.2 feature_request.yml

| 字段 | 当前值 | 评估 | 建议 |
|------|--------|------|------|
| Component | 同 Bug Report | ✅ 完整 | 保持不变 |
| Problem Statement | textarea | ✅ 正确 | 保持不变 |
| Motivation | textarea | ✅ 正确 | 保持不变 |
| Proposed Solution | textarea | ✅ 正确 | 保持不变 |
| Alternatives Considered | textarea | ✅ 正确 | 保持不变 |
| Related UNIFIED Issue | input | ✅ 项目特色 | 保持不变 |
| Target Progressive Loading Phase | Phase 0-3 | ✅ 项目特色 | 保持不变 |
| Priority Assessment | Critical-Low | ✅ 合理 | 保持不变 |

**评估**：功能请求模板设计良好，无需修改。

#### 6.2.3 config.yml

| 配置 | 当前值 | 评估 | 建议 |
|------|--------|------|------|
| blank_issues_enabled | false | ✅ 强制使用模板 | 保持不变 |
| contact_links | Documentation / Discussions / Security | ✅ 完整 | 保持不变 |

### 6.3 PR 模板审查

| 字段 | 当前值 | 评估 | 建议 |
|------|--------|------|------|
| Description | textarea | ✅ 正确 | 保持不变 |
| Type of Change | 8种类型（含 Degradation fix / Phase loading change） | ✅ 项目特色 | 保持不变 |
| Component | 5种组件 | ✅ 完整 | 保持不变 |
| Related Issues | Closes # | ✅ 正确 | 保持不变 |
| UNIFIED Issue | 复选框 | ✅ 项目特色 | 保持不变 |
| Testing | 6项检查 | ✅ 完整 | 保持不变 |
| Breaking Changes | 复选框 | ✅ 正确 | 保持不变 |
| Checklist | 7项 | ✅ 完整 | 保持不变 |

**建议**：补充重构阶段关联字段：

```markdown
## Refactoring Phase

- [ ] Phase 0: Status Verification
- [ ] Phase 1: Data Unification
- [ ] Phase 2: API Unification
- [ ] Phase 3: MCP Enhancement
- [ ] Phase 4: Skill Optimization
- [ ] Phase 5: Cleanup & Verification
- [ ] Not applicable
```

### 6.4 Workflows 审查

#### 6.4.1 ci.yml

| 配置项 | 当前值 | 评估 | 建议 |
|--------|--------|------|------|
| 触发分支 | main, develop, develop/v8, refactor/** | ⚠️ 缺少 develop/v8.4 | 补充 develop/v8.4 |
| 触发路径 | Skill + MCP Server + scripts | ✅ 合理 | 保持不变 |
| PR 触发 | 同上 + .github/** | ✅ 合理 | 保持不变 |
| 定时任务 | 每日 06:00 UTC | ✅ 合理 | 保持不变 |
| Lint | ruff check + mypy | ✅ 正确 | mypy 应改为硬失败 |
| Test | Python 3.10/3.11/3.12 矩阵 | ✅ 完整 | 保持不变 |
| Degradation Test | 仅定时触发 | ✅ 合理 | 保持不变 |
| Skill Validate | YAML/JSON 校验 | ✅ 正确 | 保持不变 |

**关键优化建议**：

1. **补充 develop/v8.4 到触发分支**：

```yaml
on:
  push:
    branches: [main, develop, develop/v8, develop/v8.4, 'refactor/**', 'feature/**']
  pull_request:
    branches: [main, develop, develop/v8, develop/v8.4]
```

2. **mypy 改为硬失败**（当前 `|| true` 会导致类型错误被忽略）：

```yaml
- name: Type check with mypy
  working-directory: xuansto-mcp-server
  run: mypy src/ --ignore-missing-imports
```

3. **补充 Schema 校验步骤**（对应 REFACTOR_PLAN §7.2.2）：

```yaml
schema-validate:
  needs: lint
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: "3.11"
    - name: Validate Tool Parameter Schemas
      run: |
        python scripts/validate_schemas.py \
          --tools xuansto-mcp-server/src/xuansto_mcp/tools/ \
          --lock xuansto-mcp-server/spec-locks/tool-parameter-schemas.json
```

4. **补充 MCP 定义验证步骤**（对应 REFACTOR_PLAN §7.2.3）：

```yaml
mcp-validate:
  needs: lint
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: "3.11"
    - name: Install dependencies
      working-directory: xuansto-mcp-server
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    - name: Verify Degradation Mapping Consistency
      run: |
        python scripts/verify_degradation_consistency.py \
          --degradation xuansto-mcp-server/src/xuansto_mcp/core/degradation.py \
          --constraints .trae/skills/xuansto-skill-v2/constraints.yaml
```

#### 6.4.2 release.yml

| 配置项 | 当前值 | 评估 | 建议 |
|--------|--------|------|------|
| 触发 | tag v* | ✅ 正确 | 保持不变 |
| Build | python -m build | ✅ 正确 | 保持不变 |
| Release | softprops/action-gh-release@v2 | ✅ 正确 | 保持不变 |
| Pre-release 检测 | rc/beta/alpha | ✅ 正确 | 保持不变 |
| PyPI 发布 | pypa/gh-action-pypi-publish | ✅ 正确 | 保持不变 |

**建议**：补充发布前测试步骤：

```yaml
release:
  needs: build
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Download artifacts
      uses: actions/download-artifact@v4
      with:
        name: dist
        path: dist/
    - name: Verify package metadata
      run: |
        pip install dist/*.whl
        xuansto-mcp --version
    - name: Create GitHub Release
      uses: softprops/action-gh-release@v2
      with:
        files: dist/*
        generate_release_notes: true
        draft: false
        prerelease: ${{ contains(github.ref_name, 'rc') || contains(github.ref_name, 'beta') || contains(github.ref_name, 'alpha') }}
```

### 6.5 dependabot.yml 审查

| 配置项 | 当前值 | 评估 | 建议 |
|--------|--------|------|------|
| pip | xuansto-mcp-server 目录, 每周一 | ✅ 正确 | 保持不变 |
| github-actions | 根目录, 每周一 | ✅ 正确 | 保持不变 |
| open-pull-requests-limit | 5 | ✅ 合理 | 保持不变 |
| reviewers | xuanyuanchumo | ✅ 正确 | 保持不变 |

**建议**：补充自动标签和提交消息前缀：

```yaml
version: 2

updates:
  - package-ecosystem: pip
    directory: /xuansto-mcp-server
    schedule:
      interval: weekly
      day: monday
      time: "06:00"
    open-pull-requests-limit: 5
    labels:
      - dependencies
      - python
    commit-message:
      prefix: "chore(deps)"
    reviewers:
      - xuanyuanchumo

  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
      day: monday
      time: "06:00"
    open-pull-requests-limit: 5
    labels:
      - dependencies
      - github-actions
    commit-message:
      prefix: "chore(ci)"
    reviewers:
      - xuanyuanchumo
```

### 6.6 缺失项建议

| 缺失项 | 说明 | 优先级 |
|--------|------|--------|
| `CODEOWNERS` | 代码所有者自动指派 Review | 中 |
| `.github/SECURITY.md` | 安全策略（config.yml 已引用链接） | 低 |
| `.github/workflows/codeql.yml` | CodeQL 安全扫描 | 低 |
| `.editorconfig` | 编辑器配置统一（与 .gitattributes 互补） | 中 |

---

## 7. 可直接执行的操作命令序列

> 以下命令在 Windows PowerShell 环境下执行，基于主仓库路径 `D:\Projects\TraeProjects\skiller`

### 7.1 初始化分支结构

```powershell
# 进入主仓库
Set-Location "D:\Projects\TraeProjects\skiller"

# 确保 develop 分支存在
git branch -a | Select-String "develop"
if (-not $?) {
    git checkout -b develop main
}

# 创建 develop/v8.4 分支
git checkout -b develop/v8.4 develop

# 推送到远程
git push origin develop/v8.4
```

### 7.2 创建阶段 Feature 分支和 Worktree

```powershell
# 阶段0: 状态验证
git worktree add "D:\Projects\TraeProjects\skiller\worktrees\phase0-status-verify" -b feature/status-verify develop/v8.4

# 阶段1: 数据层统一
git worktree add "D:\Projects\TraeProjects\skiller\worktrees\phase1-data-unification" -b feature/data-unification develop/v8.4

# 阶段2: 接口层统一
git worktree add "D:\Projects\TraeProjects\skiller\worktrees\phase2-api-unification" -b feature/api-unification develop/v8.4

# 阶段3: MCP层增强
git worktree add "D:\Projects\TraeProjects\skiller\worktrees\phase3-mcp-enhance" -b feature/mcp-enhance develop/v8.4

# 阶段4: Skill层优化
git worktree add "D:\Projects\TraeProjects\skiller\worktrees\phase4-skill-optimize" -b feature/skill-optimize develop/v8.4

# 阶段5: 清理与验证
git worktree add "D:\Projects\TraeProjects\skiller\worktrees\phase5-cleanup-verify" -b feature/cleanup-verify develop/v8.4

# 验证所有 Worktree
git worktree list
```

### 7.3 安装 .git/info/exclude

```powershell
# 主仓库
Copy-Item ".git-info-exclude-template" "D:\Projects\TraeProjects\skiller\.git\info\exclude"

# 当前 Worktree
Copy-Item ".git-info-exclude-template" "D:\Projects\TraeProjects\skiller\.git\worktrees\feat-develop-main-branch-H3MhdQ\info\exclude"
```

### 7.4 更新根级 .gitignore

```powershell
# 在项目根目录执行以下编辑操作
# 补充 .zed/ 编辑器
# 补充 .trae-cn/ 目录
# 移除 .python-version（移至 exclude）
```

具体编辑内容：在 IDE/Editor 段末尾添加 `.zed/`，在 Trae/Skill Runtime 段添加 `.trae-cn/`，移除 Python Tool Files 段的 `.python-version`。

### 7.5 更新根级 .gitattributes

```powershell
# 在项目根目录执行以下编辑操作
# 补充 constraints.yaml / routes.yaml / registry.yaml merge=union
# 补充 spec-locks/ linguist-generated
```

### 7.6 阶段完成后的合并操作

```powershell
# 以阶段0为例，其他阶段同理
Set-Location "D:\Projects\TraeProjects\skiller"

# 切换到 develop/v8.4
git checkout develop/v8.4

# Squash Merge
git merge --squash feature/status-verify

# 提交
git commit -m "feat(phase0): 状态验证完成 - PROBLEM.md更新 + 6个待验证问题审计"

# 推送
git push origin develop/v8.4

# 删除已合并的 Feature 分支
git branch -d feature/status-verify

# 删除 Worktree
git worktree remove "D:\Projects\TraeProjects\skiller\worktrees\phase0-status-verify"

# 打 tag（阶段0完成后）
git tag -a v8.4.1 -m "v8.4.1: 状态验证+PROBLEM.md更新"
git push origin v8.4.1
```

### 7.7 版本发布操作

```powershell
# 全部阶段完成后，合并到 develop
Set-Location "D:\Projects\TraeProjects\skiller"
git checkout develop
git merge --no-ff develop/v8.4 -m "release: v8.5.0 - 数据层统一+接口层统一+MCP增强+Skill优化"

# 合并到 main
git checkout main
git merge --no-ff develop -m "release: v8.5.0"

# 打 tag
git tag -a v8.5.0 -m "v8.5.0: 重构阶段0-4完成"

# 推送
git push origin main --tags
git push origin develop

# 创建 develop/v8.5 分支
git checkout -b develop/v8.5 develop
git push origin develop/v8.5
```

### 7.8 清理操作

```powershell
# 清理已删除的 Worktree 记录
git worktree prune

# 清理已合并的远程分支
git remote prune origin

# 查看可清理的本地分支
git branch --merged develop/v8.4
```

---

## 8. 分支与重构步骤映射表

### 8.1 完整映射表

| 重构阶段 | 分支 | 版本目标 | 涉及问题 | 关键文件变更 | 预计工期 |
|----------|------|----------|----------|-------------|----------|
| **阶段0: 状态验证** | `feature/status-verify` | v8.4.1 | NEW-11, ARCH-05/06/07/09/10验证, DB-03验证, MCP-03验证 | PROBLEM.md, 审计报告 | 5天 |
| **阶段1: 数据层统一** | `feature/data-unification` | v8.5.0 | NEW-07, DB-01, DB-02 | database.py, db_engine.py, migration_v13.py | 14天 |
| **阶段2: 接口层统一** | `feature/api-unification` | v8.5.0 | ARCH-11, API-01, NEW-01 | errors.py, degradation.py, constraints.yaml, api.py | 13天 |
| **阶段3: MCP层增强** | `feature/mcp-enhance` | v8.5.0 | NEW-08, MCP-03/NEW-09, NEW-05 | skill_resources.py, audit_query.py(新), progressive_loader.py | 10天 |
| **阶段4: Skill层优化** | `feature/skill-optimize` | v8.5.0 | NEW-06, SKILL-02, ARCH-08, ARCH-12 | _shared.py, constraints.yaml, token_budget.py | 8天 |
| **阶段5: 清理与验证** | `feature/cleanup-verify` | v8.6.0 | P3-01, NEW-02, NEW-04, NEW-10, NEW-03 | v1归档, __init__.py, ci.yml | 6天 |

### 8.2 阶段依赖与并行关系

```
阶段0 ─────→ 阶段1 ─────→ 阶段2 ─────┬──→ 阶段3 ──→ 阶段4 ──→ 阶段5
                                      │
                                      └──→ 阶段4（可与阶段3并行）
```

- 阶段0→1→2 必须严格顺序执行
- 阶段3和阶段4在阶段2完成后可并行开发（修改文件不重叠）
- 阶段5必须在所有阶段完成后执行

### 8.3 文件修改冲突分析

| 文件 | 阶段1 | 阶段2 | 阶段3 | 阶段4 | 冲突风险 |
|------|-------|-------|-------|-------|----------|
| `database.py` | ✏️ Schema合并 | — | — | — | 无 |
| `degradation.py` | — | ✏️ 映射对齐 | — | — | 无 |
| `constraints.yaml` | — | ✏️ 补全6映射 | — | ✏️ SKELETON命令 | ⚠️ 中 |
| `errors.py` | — | ✏️ 统一错误码 | — | — | 无 |
| `skill_resources.py` | — | — | ✏️ 暴露订阅 | — | 无 |
| `progressive_loader.py` | — | — | ✏️ 扩展MAP | — | 无 |
| `_shared.py` | — | — | — | ✏️ 补全门禁 | 无 |
| `token_budget.py` | — | — | — | ✏️ 阶段关联 | 无 |

**唯一冲突点**：`constraints.yaml` 在阶段2和阶段4都有修改。解决方案：阶段4开始前先 rebase 到阶段2合并后的 develop/v8.4。

### 8.4 版本 Tag 规划

| Tag | 基于分支 | 打 tag 时机 | 包含内容 |
|-----|----------|-------------|----------|
| `v8.4.1` | develop/v8.4 | 阶段0合并后 | 状态验证+PROBLEM.md更新 |
| `v8.5.0-rc.1` | develop/v8.4 | 阶段2合并后 | 数据层+接口层统一（Release Candidate） |
| `v8.5.0` | develop→main | 阶段4合并后 | 全部重构内容 |
| `v8.6.0` | develop→main | 阶段5合并后 | 清理归档+版本统一 |

### 8.5 CI 分支保护规则建议

| 分支 | 保护规则 |
|------|----------|
| `main` | 禁止直接推送，必须通过 PR，至少1人 Review，CI 必须通过 |
| `develop` | 禁止直接推送，必须通过 PR，CI 必须通过 |
| `develop/v8.4` | 禁止直接推送，必须通过 PR，CI 必须通过 |
| `feature/*` | 无保护，开发者可直接推送 |
| `hotfix/*` | 合并到 main 时需 Review |

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

### 提交消息规范

```
feat(phase0): 状态验证完成
fix(mcp): 修复Resource订阅未暴露问题
refactor(data): 合并双SQLite实例
chore(ci): 补充Schema校验步骤
docs(plan): 更新重构计划
test(degradation): 补充降级链路测试
```

### 关键路径速查

| 项目 | 路径 |
|------|------|
| 主仓库 | `D:\Projects\TraeProjects\skiller` |
| 当前 Worktree | `c:\Users\86156\.trae-cn\worktrees\skiller\feat-develop-main-branch-H3MhdQ` |
| Worktree 元数据 | `D:\Projects\TraeProjects\skiller\.git\worktrees\feat-develop-main-branch-H3MhdQ` |
| 主仓库 exclude | `D:\Projects\TraeProjects\skiller\.git\info\exclude` |
| Worktree exclude | `D:\Projects\TraeProjects\skiller\.git\worktrees\feat-develop-main-branch-H3MhdQ\info\exclude` |
| exclude 模板 | `.git-info-exclude-template`（项目根目录） |
