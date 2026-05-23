# 从 v1 迁移到 v2 指南

本文档帮助你从 xuansto-skill v1（脚本驱动）迁移到 xuansto-mcp-server v2（MCP Server）。

---

## 概述

| 特性 | v1 | v2 |
|------|----|----|
| 架构 | 脚本驱动，直接调用 Python 脚本 | MCP Server，通过 MCP 协议暴露工具 |
| 交互方式 | 命令行 / Trae Skill 命令 | MCP Tool Call（JSON-RPC） |
| 工具数量 | 27+ 分散脚本 | 13 个原子工具 + 6 个资源 |
| 降级机制 | 无 | 四级降级链（MCP → 脚本 → 内嵌 → 兜底） |
| 配置管理 | `.trae/skills/xuansto-skill/` | `XUANSTO_SKILL_ROOT` + `.xuansto-config.yaml` |
| 知识库 | 文件系统直读 | ChromaDB + SQLite FTS5 + 关键词降级 |
| 安装方式 | 手动复制技能目录 | `uvx xuansto-mcp-server` |
| 会话管理 | 无持久化 | `.xuansto/sessions/` 持久化 |
| 质量门禁 | 脚本执行 | 内嵌检查 + 脚本 + 增量缓存 |

---

## 配置迁移

### v1 配置位置

```
.trae/skills/xuansto-skill/
├── SKILL.md
├── .skill-config.yaml
├── scripts/
├── agents/
├── references/
└── knowledge/
```

### v2 配置位置

v2 使用环境变量 `XUANSTO_SKILL_ROOT` 指定技能数据根目录，默认使用内置 `data/` 目录。

```
# 环境变量
XUANSTO_SKILL_ROOT=/path/to/skill-data

# 目录结构
$XUANSTO_SKILL_ROOT/
├── .xuansto-config.yaml     # 主配置文件
├── scripts/                  # 检查脚本
├── agents/                   # Agent 定义
├── references/               # 参考文档
├── knowledge/                # 知识库
│   ├── general/
│   ├── workspace/
│   └── experience/
├── workflows/                # 工作流定义
└── hooks/                    # Hook 配置
```

### 迁移步骤

1. **设置环境变量**

```bash
# 将 v1 的技能目录设为 XUANSTO_SKILL_ROOT
export XUANSTO_SKILL_ROOT=/path/to/.trae/skills/xuansto-skill
```

2. **创建 .xuansto-config.yaml**

v1 的 `.skill-config.yaml` 仍然兼容，但 v2 新增 `.xuansto-config.yaml` 用于高级配置：

```yaml
gate_scripts:
  GATE-007: "check-encoding.py"
  TEST-PASS: "coverage-check.py"
  FILE-ENCODING: "check-encoding.py"
  COMMENT-LANGUAGE: "check-comment-lang.py"
  SCRIPT-SECURITY: "script-security-scanner.py"

gates_by_phase:
  "0": ["DESIGN-SYSTEM-COMPLETE", "ANTI-PATTERN-CHECK", "DESIGN-REVIEW"]
  "1": ["BRAINSTORM-COMPLETE", "GATE-001", "GATE-002"]
  "2": ["PLAN-ATOMIC", "GATE-003", "GATE-004"]
  "3": ["TEST-FIRST"]
  "4": ["SUBAGENT-REVIEW", "REVIEW-CONFIDENCE", "GATE-007", "TEST-PASS", "GATE-009", "FILE-ENCODING"]
  "5": ["PLAYWRIGHT-E2E-PASS", "GATE-011", "GATE-012", "AI-PENTEST", "SPEC-CONSISTENCY"]
  "6": ["GATE-013", "GATE-014", "INFRA-HEALTH", "UX-ACCEPTANCE"]
  "7": ["SIMPLIFICATION-BEHAVIOR", "CHESTERTON-FENCE", "GATE-015"]
  "8": ["DESKTOP-BUILD", "DESKTOP-SIGN", "DESKTOP-UPDATE", "DESKTOP-CROSS", "IPC-CONTRACT"]

hook_scripts:
  security-block: null
  token-budget-check: "token-budget-guard.py"
  dangerous-cmd-confirm: null
  auto-format: null
  encoding-check: "check-encoding.py"
  console-log-detect: null
  type-check: null
  load-context: "session-catchup.py"
  kb-health-check: "health-checker.py"
  platform-detect: "project-initializer.py"
  session-save: "session-persist.py"
  git-status-check: null
  experience-precipitate: "pattern-learner.py"
  pattern-detect: "pattern-learner.py"
  save-state: "session-persist.py"
  decision-log-persist: null
```

3. **配置 MCP 客户端**

在 Trae 或其他 MCP 客户端中配置：

```json
{
  "mcpServers": {
    "xuansto": {
      "command": "uvx",
      "args": ["xuansto-mcp-server"],
      "env": {
        "XUANSTO_SKILL_ROOT": "/path/to/skill-data",
        "XUANSTO_WORK_DIR": "/path/to/project/.xuansto"
      }
    }
  }
}
```

---

## 数据迁移

### 知识库路径变化

| v1 路径 | v2 路径 | 说明 |
|---------|---------|------|
| `.trae/skills/xuansto-skill/knowledge/` | `$XUANSTO_SKILL_ROOT/knowledge/` | 知识库根目录 |
| `knowledge/general/` | `knowledge/general/` | 通用知识（路径不变） |
| `knowledge/workspace/` | `knowledge/workspace/` | 工作区知识（路径不变） |
| `knowledge/experience/` | `knowledge/experience/` | 经验知识（路径不变） |
| 无 | `knowledge/index/knowledge.db` | v2 新增：SQLite FTS5 索引 |
| 无 | `knowledge/index/chroma/` | v2 新增：ChromaDB 向量索引 |

### 知识库索引构建

v2 新增了知识库索引功能。迁移后需要构建索引：

1. 首次使用 `knowledge_search` 工具时，系统会自动创建 SQLite FTS5 索引
2. 如需 ChromaDB 语义搜索，安装 `chromadb` 依赖：`pip install xuansto-mcp-server[full]`
3. 索引数据存储在 `knowledge/index/` 目录

### 会话数据迁移

v1 没有会话持久化功能。v2 新增了会话管理：

- 会话文件存储在 `$XUANSTO_WORK_DIR/sessions/`
- 模式文件存储在 `$XUANSTO_WORK_DIR/patterns/`
- 工作流状态存储在 `$XUANSTO_WORK_DIR/workflows/`
- 资源状态存储在 `$XUANSTO_WORK_DIR/resource_state.json`

---

## 命令映射

v1 的命令行调用映射到 v2 的 MCP 工具调用：

### 基础工具

| v1 命令 | v2 MCP 工具 | 说明 |
|---------|-------------|------|
| `python scripts/skill-test.py --path .` | `skill_analyze` | 技能分析 |
| `python scripts/knowledge-server.py search --query "xxx"` | `knowledge_search(action="retrieve", query="xxx")` | 知识检索 |
| `python scripts/coverage-check.py` | `quality_gate_check(gate_ids=["TEST-PASS"])` | 测试覆盖检查 |
| `python scripts/check-encoding.py` | `quality_gate_check(gate_ids=["FILE-ENCODING"])` | 编码检查 |
| `python scripts/spec-drift-detector.py` | `spec_drift_detect` | 规格偏差检测 |
| `python scripts/agentic-security-scanner.py` | `security_scan` | 安全扫描 |
| `python scripts/code-simplifier.py` | `code_simplify` | 代码简化 |
| `python scripts/session-persist.py save` | `session_manage(action="save")` | 会话保存 |
| `python scripts/health-checker.py` | `server_health` | 健康检查 |

### 门禁检查

| v1 命令 | v2 MCP 工具 |
|---------|-------------|
| `python scripts/coverage-check.py` | `quality_gate_check(gate_ids=["TEST-PASS"])` |
| `python scripts/check-encoding.py` | `quality_gate_check(gate_ids=["FILE-ENCODING"])` |
| `python scripts/check-comment-lang.py` | `quality_gate_check(gate_ids=["COMMENT-LANGUAGE"])` |
| `python scripts/script-security-scanner.py` | `quality_gate_check(gate_ids=["SCRIPT-SECURITY"])` |

### Hook 执行

| v1 命令 | v2 MCP 工具 |
|---------|-------------|
| `python scripts/token-budget-guard.py` | `hook_manage(action="execute", hook_name="token-budget-check")` |
| `python scripts/session-persist.py` | `hook_manage(action="execute", hook_name="session-save")` |
| `python scripts/health-checker.py` | `hook_manage(action="execute", hook_name="kb-health-check")` |

### 新增功能（v2 独有）

| v2 MCP 工具 | 说明 |
|-------------|------|
| `workflow_dispatch` | 工作流调度（启动/查询/中止/阶段推进） |
| `agent_status` | Agent 状态查询（57 个 Agent） |
| `hook_manage` | Hook 管理（16 个 Hook，3 种 Profile） |
| `resource_load_status` | 渐进式资源加载状态管理 |
| `context_compress` | 上下文压缩（3 种策略） |

---

## 环境变量

| 环境变量 | 必填 | 默认值 | 说明 |
|----------|------|--------|------|
| `XUANSTO_SKILL_ROOT` | 否 | 内置 `data/` 目录 | 技能数据根目录 |
| `XUANSTO_WORK_DIR` | 否 | 项目根目录下 `.xuansto/` | 工作目录（会话、模式、工作流状态） |

### XUANSTO_SKILL_ROOT

指定技能数据的根目录，包含 scripts、agents、references、knowledge 等子目录。

- 不设置时，使用内置的 `src/xuansto_mcp/data/` 目录
- 设置后，从指定目录加载配置和脚本
- 支持 `.xuansto-config.yaml` 配置热重载

### XUANSTO_WORK_DIR

指定工作目录，用于存储运行时状态。

- 不设置时，自动查找项目根目录（包含 `.trae/` 或 `.git/` 的目录）下的 `.xuansto/`
- 设置后，使用指定路径
- 子目录结构：
  - `sessions/` — 会话记录
  - `patterns/` — 错误模式
  - `workflows/` — 工作流实例状态
  - `gate_cache.json` — 门禁检查缓存
  - `resource_state.json` — 资源加载状态

---

## 安装方式

### v2 安装

```bash
# 使用 uvx（推荐）
uvx xuansto-mcp-server

# 使用 pip
pip install xuansto-mcp-server

# 从源码安装
git clone https://github.com/skiller-team/xuansto-mcp-server.git
cd xuansto-mcp-server
pip install -e .
```

### 验证安装

```bash
# 检查版本
python -c "import xuansto_mcp; print(xuansto_mcp.__version__)"

# 启动 MCP Server
xuansto-mcp

# 使用 CLI
xuansto-cli --help
```

### MCP 客户端配置

**Trae IDE：**

```json
{
  "mcpServers": {
    "xuansto": {
      "command": "uvx",
      "args": ["xuansto-mcp-server"]
    }
  }
}
```

**Claude Desktop：**

```json
{
  "mcpServers": {
    "xuansto": {
      "command": "uvx",
      "args": ["xuansto-mcp-server"],
      "env": {
        "XUANSTO_SKILL_ROOT": "/path/to/skill-data"
      }
    }
  }
}
```

**Cursor：**

```json
{
  "mcp.servers": {
    "xuansto": {
      "command": "uvx",
      "args": ["xuansto-mcp-server"]
    }
  }
}
```

---

## 常见问题

### Q: v1 的脚本还能用吗？

可以。v2 的降级链会尝试执行 `scripts/` 目录下的脚本。如果脚本存在且执行成功，优先使用脚本结果；脚本不可用时降级到内嵌逻辑。

### Q: 迁移后知识库搜索结果不同？

v2 使用 ChromaDB + SQLite FTS5 混合搜索，比 v1 的纯文件扫描更精确。如果 ChromaDB 未安装，会自动降级到 SQLite FTS5 或关键词搜索。

### Q: 如何保留 v1 的自定义脚本？

将自定义脚本放在 `$XUANSTO_SKILL_ROOT/scripts/` 目录下，v2 的降级链会自动发现并执行。

### Q: v1 的 .trae/skills/ 目录还需要吗？

不需要。v2 通过 `XUANSTO_SKILL_ROOT` 环境变量指定数据目录，不再依赖 `.trae/skills/` 路径。

### Q: 配置热重载如何工作？

v2 支持配置热重载：
- Linux/macOS：发送 `SIGHUP` 信号（`kill -HUP <pid>`）
- Windows：后台线程每 5 秒检查 `.xuansto-config.yaml` 文件修改时间

### Q: 工作目录 .xuansto/ 可以删除吗？

可以。删除后下次使用会自动重建。但会丢失会话记录、模式数据和工作流状态。

### Q: v2 的门禁检查比 v1 慢？

首次检查可能较慢，但 v2 支持增量缓存。文件未变更时，门禁结果从缓存读取，速度显著提升。使用 `force_refresh: true` 强制刷新缓存。

### Q: 如何确认当前降级级别？

调用 `server_health` 工具，查看 `degradation_stats` 字段。每个工具的降级次数会被记录。
