# v1 → v2 迁移指南

> xuansto-skill (v5.0.0) → xuansto-skill-v2 (v8.0.0) + xuansto-mcp-server (v4.0.0)

## 迁移步骤

1. **安装 xuansto-mcp-server v4.0.0**
   ```bash
   pip install xuansto-mcp-server>=4.0.0
   ```

2. **配置 MCP 服务器连接**
   在 Trae 的 MCP 配置中添加 xuansto-mcp-server：
   ```json
   {
     "mcpServers": {
       "xuansto": {
         "command": "python",
         "args": ["-m", "xuansto_mcp"]
       }
     }
   }
   ```

3. **切换技能引用**
   将 `.trae/skills/xuansto-skill/` 替换为 `.trae/skills/xuansto-skill-v2/`

4. **迁移会话状态**
   - 删除旧的 `.xuansto/resource_state.json`
   - 新版本会自动创建 v3 格式的状态文件

5. **验证迁移**
   - 运行 `resource_load_status(action="status")` 确认 MCP 连接正常
   - 运行 `server_health(action="check")` 确认版本兼容

## 关键差异

| 特性 | v1 (xuansto-skill) | v2 (xuansto-skill-v2) |
|------|-------------------|----------------------|
| 架构 | 纯Skill内嵌 | MCP Server + Skill 双层架构 |
| 工具调用 | 内嵌脚本/内联逻辑 | 13个MCP原子工具 + 降级脚本 |
| 加载策略 | 9阶段(0-8)工作流Phase | 4阶段(0-3)渐进式加载 |
| Token预算 | 无明确预算 | 每阶段Token预算(2K/5K/10K/20K) |
| Agent加载 | 全量加载 | 按Phase渐进加载 |
| 披露机制 | 无 | disclosure_note + upgrade_hint + available_commands |
| 自动升级 | 无 | auto_upgrade参数，Token超限自动推进 |
| 知识检索 | ChromaDB/SQLite/关键词 | 可插拔搜索引擎架构 |
| Hook系统 | 静态配置 | HookEngine插件系统 |
| 配置热重载 | 需重启 | watchfiles事件驱动热重载 |
| API版本 | 无 | MCP API v2.0.0 |
| 降级策略 | 无统一降级 | YAML配置降级 + 三级降级链 |

## 破坏性变更

### 1. Phase 编号变更
- **v1**: `phase` 参数范围 0-8（工作流阶段）
- **v2**: `phase` 参数范围 0-3（加载阶段）
  - 0 = 骨架(Skeleton)
  - 1 = 功能(Functional)
  - 2 = 增强(Enhanced)
  - 3 = 完整(Full)

### 2. resource_load_status 工具变更
- 新增 `auto_upgrade` 参数
- `status` 响应新增字段：`disclosure_note`、`upgrade_hint`、`available_commands`、`token_budget`、`token_usage`、`phase_token_usage`
- `preload` 响应新增字段：`phase_name`、`estimated_tokens`、`token_budget`、`disclosure_note`、`upgrade_hint`、`available_commands`
- `token_report` 响应新增字段：`phase_token_usage`、`phase_token_budgets`
- 状态文件版本从 v2 升级到 v3

### 3. MCP 依赖要求
- **v1**: 无MCP依赖，纯Skill内嵌
- **v2**: 需要 xuansto-mcp-server >= 4.0.0，API版本 2.0.0

### 4. 配置文件变更
- 新增 `.xuansto-config.yaml` 支持热重载
- `resource_state.json` 格式升级到 v3（新增 `phase` 字段）

### 5. Agent 加载策略变更
- **v1**: 所有Agent全量加载
- **v2**: 按Phase渐进加载
  - Phase 0: 无Agent
  - Phase 1: 核心Agent (Product Manager, Orchestrator, System Architect)
  - Phase 2: Agent注册表(名称+层级)
  - Phase 3: 全部Agent完整定义

## 命令映射

v1 和 v2 的27个命令完全一致，无需映射变更：

| v1 命令 | v2 命令 | 变更说明 |
|---------|---------|---------|
| /sprint | /sprint | 无变更 |
| /clarify | /clarify | 无变更 |
| /plan | /plan | 无变更 |
| /spec | /spec | 无变更 |
| /design | /design | 无变更 |
| /implement | /implement | 无变更 |
| /test | /test | 无变更 |
| /review | /review | 无变更 |
| /fix | /fix | 无变更 |
| /accept | /accept | 无变更 |
| /deploy | /deploy | 无变更 |
| /build-desktop | /build-desktop | 无变更 |
| /release-desktop | /release-desktop | 无变更 |
| /refactor | /refactor | 无变更 |
| /audit | /audit | 无变更 |
| /agent-status | /agent-status | 无变更 |
| /learn | /learn | 无变更 |
| /brainstorm | /brainstorm | 无变更 |
| /execute-plan | /execute-plan | 无变更 |
| /design-system | /design-system | 无变更 |
| /simplify | /simplify | 无变更 |
| /loop | /loop | 无变更 |
| /cancel-loop | /cancel-loop | 无变更 |
| /build | /build | 无变更 |
| /init | /init | 无变更 |
| /status | /status | 无变更 |
| /rollback | /rollback | 无变更 |

命令本身未变更，但底层执行方式从内嵌脚本迁移到MCP工具调用链。

## 配置变更

### 新增配置项
- `.xuansto-config.yaml`: 门禁脚本映射、Hook脚本映射、阶段门禁映射
- `constraints.yaml`: 新增 `budget` 字段、`token_budget` 字段

### 删除配置项
- 无删除，v1配置在v2中均向后兼容

### 变更配置项
- `constraints.yaml` 的 `version` 从 `"7.0.0"` 变更为 `"8.0.0"`
- `constraints.yaml` 的 `token_budgets` 各阶段 `estimate` 从近似值变更为上限值
- `resource_state.json` 的 `version` 从 `2` 变更为 `3`
