# xuansto-mcp-server

Xuansto Skill MCP Server — 13 atomic tools + 7 resources for autonomous development orchestration.

## Features

- **13 MCP Tools**: skill_analyze, knowledge_search, quality_gate_check, spec_drift_detect, security_scan, code_simplify, session_manage, workflow_dispatch, agent_status, hook_manage, resource_load_status, context_compress, server_health
- **7 MCP Resources**: skill config, quality gates, agent registry, workflow phases, templates, session history, loading status
- **3-tier Knowledge Search**: ChromaDB → SQLite FTS5 → keyword fallback
- **Graceful Degradation**: MCP tool → Python script → fallback response
- **Built-in Data**: references, agents, scripts, knowledge base included in package

## Installation

### Via uvx (Recommended)

```json
{
  "mcpServers": {
    "xuansto-mcp-server": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/skiller-team/xuansto-mcp-server",
        "xuansto-mcp"
      ]
    }
  }
}
```

Paste this JSON into your MCP client (Trae, Claude Desktop, etc.) configuration.

### Via pip

```bash
pip install git+https://github.com/skiller-team/xuansto-mcp-server
xuansto-mcp
```

### From source

```bash
git clone https://github.com/skiller-team/xuansto-mcp-server.git
cd xuansto-mcp-server
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
        "git+https://github.com/skiller-team/xuansto-mcp-server",
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

- **Compatible Skill**: xuansto-skill-v2 >= 7.0.0
- **MCP Protocol**: 2025-03-26
- **Python**: >= 3.10
- **MCP API Version**: 1.0.0

## Architecture

```
src/xuansto_mcp/
├── data/                    # Built-in data (references, agents, scripts, knowledge)
├── core/
│   ├── config.py            # DATA_DIR + SKILL_ROOT + WORK_DIR
│   ├── errors.py            # Error hierarchy + response helpers
│   ├── degradation.py       # Fallback chain (MCP → script → response)
│   ├── subprocess_utils.py  # Script execution utilities
│   └── validator.py         # Pydantic input validation
├── models/
│   └── schemas.py           # 13 Pydantic input models
├── resources/
│   └── skill_resources.py   # 7 MCP Resources
├── tools/
│   ├── skill_analyze.py
│   ├── knowledge_search.py
│   ├── quality_gate_check.py
│   ├── spec_drift_detect.py
│   ├── security_scan.py
│   ├── code_simplify.py
│   ├── session_manage.py
│   ├── workflow_dispatch.py
│   ├── agent_status.py
│   ├── hook_manage.py
│   ├── resource_load_status.py
│   ├── context_compress.py
│   └── server_health.py
└── server.py                # FastMCP server entry point
```

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
