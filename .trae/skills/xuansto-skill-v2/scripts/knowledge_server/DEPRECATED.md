# DEPRECATED

This directory contains the legacy knowledge server implementation.

Knowledge storage is now unified under `xuansto-mcp-server`. The MCP server provides:

- **Knowledge search**: `knowledge_search` tool
- **Knowledge injection**: `knowledge_inject` tool
- **Knowledge stats**: `xuansto://knowledge/stats` resource
- **SQLite + ChromaDB**: Unified storage via `xuansto-mcp-server/src/xuansto_mcp/core/database.py`

The files in this directory are kept for backward compatibility only and will be removed in a future version.

## Migration Guide

1. Replace any direct calls to `knowledge_server` API endpoints with the corresponding MCP tools
2. Knowledge data is automatically accessible via the MCP server's SQLite database
3. The `hybrid_search`, `vector_engine`, and `embedding` modules are superseded by the MCP server's integrated search pipeline
