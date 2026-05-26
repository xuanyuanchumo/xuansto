# Xuansto - MCP Server + Skill for Autonomous Development

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-%E2%89%A53.10-blue)]()
[![MCP](https://img.shields.io/badge/MCP-v3.0.0-green)]()
[![Version](https://img.shields.io/badge/Version-8.0.0-brightgreen)]()

**Xuansto — 多Agent自主开发编排器 | MCP Server + Skill 混合架构 | SDD+TDD融合**

</div>

---

## 项目简介

Xuansto 是一个基于 MCP (Model Context Protocol) + Skill 混合架构的 AI 自主开发编排系统，为 Trae IDE、Claude Code、Cursor、Windsurf 等主流 AI 开发工具提供：

- **MCP Server**：20 个原子化 Tool + 8 个 Resource，通过标准 MCP 协议提供服务
- **Skill**：57 个专业 Agent、31 个命令、54 个质量门禁、9 阶段 SDD+TDD 工作流

## 核心特性

- **20 MCP Tools**：覆盖分析、知识、质量、安全、会话、工作流、Agent管理、基础设施等全栈能力
- **8 MCP Resources**：配置、门禁、Agent注册表、工作流阶段、模板、会话历史、加载状态、Hook注册表
- **57 专业 Agent**：13层编排体系，覆盖产品→设计→工程→测试→安全→运维全流程
- **54 质量门禁**：9阶段SDD+TDD工作流，强制"Spec → Test → Code"范式
- **4阶段渐进式加载**：Skeleton(≤2K) → Functional(≤5K) → Enhanced(≤10K) → Full(≤20K)
- **4级降级框架**：MCP → Script → Inline → Minimal，确保服务可用性
- **统一数据存储**：SQLite (xuansto.db 8表) + 可选 ChromaDB 向量搜索
- **Hook拦截系统**：8种 HookType，支持 pre/post 拦截和熔断
- **Token预算管理**：令牌桶速率限制 + 上下文压缩 + 决策日志

## 项目结构

```
xuansto/
├── xuansto-mcp-server/              # MCP Server (Python, v8.0.0)
│   ├── src/xuansto_mcp/
│   │   ├── core/                    # 核心基础设施
│   │   │   ├── config.py            # 配置管理 (DATA_DIR/SKILL_ROOT/WORK_DIR)
│   │   │   ├── database.py          # 统一SQLite存储 (8表)
│   │   │   ├── degradation.py       # 4级降级框架 (20个fallback)
│   │   │   ├── hook_engine.py       # Hook拦截引擎 (8种HookType)
│   │   │   ├── search_engine.py     # 混合搜索引擎 (语义+BM25)
│   │   │   ├── cache.py             # LRU缓存
│   │   │   ├── crypto.py            # AES-256-GCM加密
│   │   │   ├── metrics.py           # 指标收集器
│   │   │   ├── notifications.py     # MCP Notification回调
│   │   │   ├── rate_limiter.py      # 令牌桶速率限制
│   │   │   └── validator.py         # Pydantic输入校验
│   │   ├── models/
│   │   │   ├── schemas.py           # 20个Pydantic输入模型
│   │   │   └── config_models.py     # 配置Pydantic模型
│   │   ├── tools/                   # 20个MCP Tools
│   │   │   ├── skill_analyze.py
│   │   │   ├── knowledge_search.py
│   │   │   ├── knowledge_inject.py
│   │   │   ├── quality_gate_check.py
│   │   │   ├── spec_drift_detect.py
│   │   │   ├── security_scan.py
│   │   │   ├── code_simplify.py
│   │   │   ├── session_manage.py
│   │   │   ├── workflow_dispatch.py
│   │   │   ├── agent_status.py
│   │   │   ├── agent_manage.py
│   │   │   ├── hook_manage.py
│   │   │   ├── resource_load_status.py
│   │   │   ├── context_compress.py
│   │   │   ├── server_health.py
│   │   │   ├── decision_log.py
│   │   │   ├── token_budget.py
│   │   │   ├── project_init.py
│   │   │   ├── metrics_report.py
│   │   │   └── config_manage.py
│   │   ├── resources/
│   │   │   └── skill_resources.py   # 8个MCP Resources
│   │   ├── cli.py                   # CLI工具 (xuansto-cli)
│   │   └── server.py                # FastMCP入口
│   ├── tests/                       # 240+ 测试用例
│   ├── spec-locks/                  # API契约锁文件
│   └── pyproject.toml
│
└── .trae/skills/xuansto-skill-v2/   # Skill (v8.0.0)
    ├── SKILL.md                     # 主入口 (83行精简)
    ├── constraints.yaml             # 渐进式加载约束
    ├── triggers.yaml                # 触发条件
    ├── agents/                      # 57个Agent定义 (13层)
    │   └── registry.yaml            # Agent注册表
    ├── commands/                    # 31个命令
    │   └── routes.yaml              # 命令路由
    ├── workflows/                   # 15个工作流
    │   └── _yaml/                   # YAML权威源
    ├── scripts/                     # 降级脚本 + 工具脚本
    ├── references/                  # 参考文档 (100+)
    ├── templates/                   # 模板文件 (20+)
    ├── hooks/                       # Hook定义
    ├── configs/                     # 默认配置
    ├── evals/                       # 评估配置
    └── CHANGELOG.md                 # 变更日志
```

## 快速开始

### 安装 MCP Server

#### 方式一：uvx（推荐）

```json
{
  "mcpServers": {
    "xuansto-mcp-server": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/xuanyuanchumo/xuansto#subdirectory=xuansto-mcp-server",
        "xuansto-mcp"
      ]
    }
  }
}
```

将此 JSON 粘贴到 MCP 客户端（Trae、Claude Desktop 等）配置中。

> **注意**：`#subdirectory=xuansto-mcp-server` 是必需的，因为 `pyproject.toml` 位于仓库的 `xuansto-mcp-server/` 子目录中。省略此参数会导致 `uvx` 报错 `Failed to resolve --with requirement / Git operation failed`。

#### 方式二：pip

```bash
pip install "git+https://github.com/xuanyuanchumo/xuansto#subdirectory=xuansto-mcp-server"
xuansto-mcp
```

#### 方式三：从源码

```bash
git clone https://github.com/xuanyuanchumo/xuansto.git
cd xuansto/xuansto-mcp-server
uvx --from . xuansto-mcp
```

### 安装 Skill

将 `.trae/skills/xuansto-skill-v2/` 目录复制到你的项目的 `.trae/skills/` 下即可自动加载。

## MCP Tools 一览

| 工具 | 描述 |
|------|------|
| `skill_analyze` | 分析技能上下文和项目结构 |
| `knowledge_search` | 混合语义+BM25知识检索 |
| `knowledge_inject` | 知识注入与沉淀 |
| `quality_gate_check` | 54个质量门禁检查 |
| `spec_drift_detect` | 规格漂移检测 |
| `security_scan` | OWASP+Agentic安全扫描 |
| `code_simplify` | 代码简化与重构建议 |
| `session_manage` | 会话创建/恢复/归档 |
| `workflow_dispatch` | 9阶段SDD+TDD工作流调度 |
| `agent_status` | Agent状态查询与匹配 |
| `agent_manage` | Agent生命周期管理(创建/分配/释放/销毁) |
| `hook_manage` | Hook注册/查询/删除 |
| `resource_load_status` | 渐进式加载状态查询与Phase切换 |
| `context_compress` | 上下文压缩与Token优化 |
| `server_health` | 健康检查与版本协商 |
| `decision_log` | 决策记录与查询 |
| `token_budget` | Token预算分配与追踪 |
| `project_init` | 项目初始化与配置 |
| `metrics_report` | 运行指标查询与汇总 |
| `config_manage` | 配置热重载/校验/状态 |

## MCP Resources 一览

| URI | 描述 |
|-----|------|
| `xuansto://config/skill` | Skill配置信息 |
| `xuansto://gates/definitions` | 质量门禁定义 |
| `xuansto://agents/registry` | Agent注册表 |
| `xuansto://workflows/definitions` | 工作流阶段定义 |
| `xuansto://templates/{name}` | 模板文件 |
| `xuansto://session/history` | 会话历史 |
| `xuansto://loading/status` | 渐进式加载状态 |
| `xuansto://hooks/registry` | Hook注册表 |

## 配置

### 环境变量

| 变量 | 默认值 | 描述 |
|------|--------|------|
| `XUANSTO_SKILL_ROOT` | 包内 `data/` 目录 | 覆盖数据源目录 |
| `XUANSTO_WORK_DIR` | 当前目录 `.xuansto/` | 可写工作目录 |

### 自定义数据

```json
{
  "mcpServers": {
    "xuansto-mcp-server": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/xuanyuanchumo/xuansto#subdirectory=xuansto-mcp-server",
        "xuansto-mcp"
      ],
      "env": {
        "XUANSTO_SKILL_ROOT": "/path/to/your/custom-skill-data"
      }
    }
  }
}
```

## 兼容性

| 项目 | 版本 |
|------|------|
| Python | >= 3.10 |
| MCP Protocol | 2025-03-26 |
| MCP API | v3.0.0 |
| Skill | xuansto-skill-v2 >= 8.0.0 |

## 开发

```bash
cd xuansto-mcp-server
pip install -e ".[dev]"
pytest                    # 运行测试
pytest --cov=xuansto_mcp  # 覆盖率
```

## 许可证

MIT License
