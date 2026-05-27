# xuansto-mcp-server

Xuansto Skill MCP Server v8.0.0 — 20 atomic tools + 8 resources for autonomous development orchestration.

## Features

### 20 MCP Tools

**Analysis & Knowledge**
- `skill_analyze` — Analyze skill structure, scripts, and agents
- `knowledge_search` — 3-tier knowledge retrieval (ChromaDB → FTS5 → keyword)
- `knowledge_inject` — Inject knowledge into context or precipitate experience

**Quality & Security**
- `quality_gate_check` — Execute quality gates by phase or ID
- `spec_drift_detect` — Detect drift between specs and implementation
- `security_scan` — Security vulnerability scanning with OWASP Agentic Top 10
- `code_simplify` — Code simplification and deduplication analysis

**Session & Workflow**
- `session_manage` — Session save/load/list/detect/verify/track/restore
- `workflow_dispatch` — Start/monitor/abort SDD-TDD workflows

**Agent Management**
- `agent_status` — Query agent registry by phase or capability
- `agent_manage` — Create/assign/release/destroy agent instances

**Infrastructure**
- `hook_manage` — List and execute hook profiles (minimal/standard/strict)
- `resource_load_status` — Progressive resource loading with phase management
- `context_compress` — Semantic/selective/lossless context compression
- `server_health` — Health check, version negotiation, capabilities
- `decision_log` — Architecture decision record management
- `token_budget` — Token budget allocation, recommendation, and reporting
- `project_init` — Project creation, validation, and stack detection
- `metrics_report` — Tool usage metrics query and summary
- `config_manage` — Configuration reload, status, and validation

### 8 MCP Resources

- `xuansto://config/skill` — Skill configuration
- `xuansto://gates/definitions` — Quality gates reference
- `xuansto://agents/registry` — Agent registry
- `xuansto://workflows/definitions` — Workflow phases definition
- `xuansto://templates/{name}` — Template documents
- `xuansto://session/history` — Session history
- `xuansto://loading/status` — Resource loading status
- `xuansto://hooks/registry` — Hooks registry

### Key Capabilities

- **3-tier Knowledge Search**: ChromaDB → SQLite FTS5 → keyword fallback
- **Graceful Degradation**: MCP tool → Python script → fallback response
- **Hook Engine**: Pluggable pre/post hook system with security enforcement
- **Progressive Loading**: Phase-based resource preloading (skeleton → functional → enhanced → full)
- **Token Budget Management**: Allocation, recommendation, and real-time tracking
- **Decision Logging**: Architecture decision records with full lifecycle management
- **Built-in Data**: References, agents, scripts, knowledge base included in package

## Installation

### Via uvx (Recommended)

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

Paste this JSON into your MCP client (Trae, Claude Desktop, etc.) configuration.

> **Note**: The `#subdirectory=xuansto-mcp-server` fragment is required because `pyproject.toml` lives inside the `xuansto-mcp-server/` subdirectory of the monorepo. Without it, `uvx` will fail with `Failed to resolve --with requirement / Git operation failed`.

### Via pip

```bash
pip install "git+https://github.com/xuanyuanchumo/xuansto#subdirectory=xuansto-mcp-server"
xuansto-mcp
```

### From source

```bash
git clone https://github.com/xuanyuanchumo/xuansto.git
cd xuansto/xuansto-mcp-server
uvx --from . xuansto-mcp
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `XUANSTO_SKILL_ROOT` | Package `data/` directory | Override data source directory |
| `XUANSTO_WORK_DIR` | `.xuansto/` in current directory | Writable working directory (sessions, patterns) |

### Custom Data

To use your own skill data (e.g., from a customized xuansto-skill):

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

## Compatibility

- **Python**: >= 3.10
- **MCP Protocol**: 2025-03-26
- **MCP API Version**: 3.0.0
- **Compatible Skill**: xuansto-skill-v2 >= 8.0.0

## Architecture

```
src/xuansto_mcp/
├── data/                        # Built-in data (references, agents, scripts, knowledge)
├── core/
│   ├── cache.py                 # LRU cache utilities
│   ├── config.py                # DATA_DIR + SKILL_ROOT + WORK_DIR + hot-reload
│   ├── crypto.py                # Cryptographic utilities
│   ├── database.py              # SQLite database initialization
│   ├── degradation.py           # Fallback chain (MCP → script → response)
│   ├── errors.py                # Error hierarchy + response helpers
│   ├── hook_engine.py           # Pluggable hook engine for pre/post interception
│   ├── logging_config.py        # Structured logging setup
│   ├── metrics.py               # Internal metrics collection
│   ├── notifications.py         # Notification dispatch
│   ├── rate_limiter.py          # Per-tool rate limiting
│   ├── search_engine.py         # Pluggable search engine protocol
│   ├── subprocess_utils.py      # Script execution utilities
│   └── validator.py             # Pydantic input validation
├── models/
│   ├── config_models.py         # Pydantic config validation models
│   └── schemas.py               # 20 Pydantic input models
├── resources/
│   └── skill_resources.py       # 8 MCP Resources
├── tools/
│   ├── skill_analyze.py
│   ├── knowledge_search.py
│   ├── knowledge_inject.py
│   ├── quality_gate_check.py
│   ├── spec_drift_detect.py
│   ├── security_scan.py
│   ├── code_simplify.py
│   ├── session_manage.py
│   ├── workflow_dispatch.py
│   ├── agent_status.py
│   ├── agent_manage.py
│   ├── hook_manage.py
│   ├── resource_load_status.py
│   ├── context_compress.py
│   ├── server_health.py
│   ├── decision_log.py
│   ├── token_budget.py
│   ├── project_init.py
│   ├── metrics_report.py
│   └── config_manage.py
├── cli.py                       # CLI entry point
└── server.py                    # FastMCP server entry point
```

## Tool Reference

| Tool | Description |
|------|-------------|
| `skill_analyze` | Analyze skill structure, scripts, and agents |
| `knowledge_search` | 3-tier knowledge retrieval (ChromaDB → FTS5 → keyword) |
| `knowledge_inject` | Inject knowledge into context or precipitate experience |
| `quality_gate_check` | Execute quality gates by phase or ID |
| `spec_drift_detect` | Detect drift between specs and implementation |
| `security_scan` | Security vulnerability scanning with OWASP Agentic Top 10 |
| `code_simplify` | Code simplification and deduplication analysis |
| `session_manage` | Session save/load/list/detect/verify/track/restore |
| `workflow_dispatch` | Start/monitor/abort SDD-TDD workflows |
| `agent_status` | Query agent registry by phase or capability |
| `agent_manage` | Create/assign/release/destroy agent instances |
| `hook_manage` | List and execute hook profiles (minimal/standard/strict) |
| `resource_load_status` | Progressive resource loading with phase management |
| `context_compress` | Semantic/selective/lossless context compression |
| `server_health` | Health check, version negotiation, capabilities |
| `decision_log` | Architecture decision record management |
| `token_budget` | Token budget allocation, recommendation, and reporting |
| `project_init` | Project creation, validation, and stack detection |
| `metrics_report` | Tool usage metrics query and summary |
| `config_manage` | Configuration reload, status, and validation |

## Resource Reference

| URI | Description |
|-----|-------------|
| `xuansto://config/skill` | Skill configuration |
| `xuansto://gates/definitions` | Quality gates reference |
| `xuansto://agents/registry` | Agent registry |
| `xuansto://workflows/definitions` | Workflow phases definition |
| `xuansto://templates/{name}` | Template documents |
| `xuansto://session/history` | Session history |
| `xuansto://loading/status` | Resource loading status |
| `xuansto://hooks/registry` | Hooks registry |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=xuansto_mcp
```

## License

MIT
