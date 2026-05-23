# 故障排除指南

本文档帮助你诊断和解决 xuansto-mcp-server 使用中的常见问题。

---

## 常见问题

### 安装失败

**问题：`pip install xuansto-mcp-server` 失败**

可能原因及解决方案：

1. **Python 版本不兼容**

```bash
python --version
# 需要 Python 3.10+
```

2. **依赖冲突**

```bash
pip install --no-deps xuansto-mcp-server
pip install mcp[cli] pydantic pyyaml
```

3. **uvx 安装失败**

```bash
# 确保 uv 已安装
uv --version

# 清除缓存重试
uv cache clean
uvx xuansto-mcp-server
```

4. **从源码安装**

```bash
git clone https://github.com/skiller-team/xuansto-mcp-server.git
cd xuansto-mcp-server
pip install -e .
```

### 连接超时

**问题：MCP 客户端无法连接到 Server**

1. **检查 Server 是否启动**

```bash
# 直接运行检查
python -m xuansto_mcp.server
# 或
uvx xuansto-mcp-server
```

2. **检查 MCP 客户端配置**

确认配置中的 `command` 和 `args` 正确：

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

3. **检查环境变量**

```bash
echo $XUANSTO_SKILL_ROOT
echo $XUANSTO_WORK_DIR
```

4. **检查端口占用**

MCP 使用 stdio 通信，不涉及端口。如果使用 HTTP 模式，检查端口是否被占用。

### 工具未注册

**问题：MCP 客户端看不到 13 个工具**

1. **检查 Server 版本**

```bash
python -c "import xuansto_mcp; print(xuansto_mcp.__version__)"
# 应输出 2.5.0 或更高
```

2. **检查工具注册日志**

启动 Server 时查看日志输出，确认 13 个工具已注册。

3. **重启 MCP 客户端**

部分客户端需要重启才能发现新注册的工具。

4. **检查 MCP 协议版本**

确保客户端支持 MCP 协议 1.0+。

---

## 错误码参考

### PATH_NOT_FOUND

**含义：** 指定的文件或目录路径不存在

**触发场景：**
- `skill_analyze` 的 `skill_path` 路径不存在
- `spec_drift_detect` 的 `spec_dir` 路径不存在

**解决方案：**
1. 检查路径拼写是否正确
2. 使用绝对路径替代相对路径
3. 确认路径在当前工作目录下可访问

```json
// 错误响应示例
{
  "error": true,
  "code": "PATH_NOT_FOUND",
  "message": "路径不存在: /nonexistent/path",
  "details": {
    "path": "/nonexistent/path",
    "suggestion": "请检查路径是否正确"
  }
}
```

### SCRIPT_NOT_FOUND

**含义：** 脚本文件不存在

**触发场景：**
- 降级链尝试执行脚本，但脚本文件在 `scripts/` 目录下不存在

**解决方案：**
1. 检查 `$XUANSTO_SKILL_ROOT/scripts/` 目录是否包含所需脚本
2. 系统会自动降级到内嵌逻辑，通常不影响功能
3. 如需完整脚本功能，从源码复制 `data/scripts/` 目录

```json
// 降级响应示例
{
  "error": true,
  "code": "SCRIPT_NOT_FOUND",
  "message": "脚本不存在: spec-drift-detector.py",
  "fallback": true
}
```

### SCRIPT_EXECUTION_ERROR

**含义：** 脚本执行失败

**触发场景：**
- 脚本执行返回非零退出码
- 脚本执行超时
- 脚本存在语法错误

**解决方案：**
1. 手动执行脚本排查错误：`python scripts/xxx.py --format json`
2. 检查脚本依赖是否安装
3. 检查脚本超时设置（默认 30-120 秒）
4. 系统会自动降级到内嵌逻辑

```json
// 错误响应示例
{
  "error": true,
  "code": "SCRIPT_EXECUTION_ERROR",
  "message": "脚本执行失败: coverage-check.py",
  "details": {
    "script": "coverage-check.py",
    "reason": "ModuleNotFoundError: No module named 'pytest'"
  }
}
```

### DEGRADATION_ERROR

**含义：** 服务降级

**触发场景：**
- 主工具不可用，降级到备用方案
- 降级链中某一级失败

**解决方案：**
1. 检查 `degradation_level` 字段确认当前降级级别
2. 查看日志了解降级原因
3. 降级通常不影响基本功能，但结果精度可能降低

```json
// 降级响应示例
{
  "error": false,
  "data": { ... },
  "degradation_level": "inline"
}
```

### VALIDATION_ERROR

**含义：** 参数校验失败

**触发场景：**
- 必填参数缺失
- 参数类型不匹配
- 参数值超出范围

**解决方案：**
1. 检查 `details.errors` 字段查看具体校验错误
2. 参照 API 文档确认参数类型和范围
3. 常见错误：
   - `action` 参数值不在允许列表中
   - 数值参数超出范围（如 `top_k` 超过 50）
   - 必填参数为 null

```json
// 错误响应示例
{
  "error": true,
  "code": "VALIDATION_ERROR",
  "message": "参数校验失败: 2个错误",
  "details": {
    "errors": [
      { "field": "action", "message": "Input should be 'save', 'load', ..." },
      { "field": "top_k", "message": "Input should be less than or equal to 50" }
    ]
  }
}
```

---

## 降级诊断

### 降级链说明

xuansto-mcp-server 采用四级降级链确保服务可用性：

```
MCP 工具调用 → 脚本执行 → 内嵌逻辑 → 兜底响应
   (Level 1)   (Level 2)   (Level 3)  (Level 4)
```

### 各工具降级链

| 工具 | Level 1 | Level 2 | Level 3 | Level 4 |
|------|---------|---------|---------|---------|
| skill_analyze | MCP | — | 内嵌分析 | 错误响应 |
| knowledge_search | MCP | ChromaDB | SQLite FTS5 | 关键词扫描 |
| quality_gate_check | MCP | 脚本 | 内嵌检查 | SKIP |
| spec_drift_detect | MCP | 脚本 | 内嵌检测 | 错误响应 |
| security_scan | MCP | 脚本 | 内嵌扫描 | 错误响应 |
| code_simplify | MCP | 脚本 | 内嵌检测 | 错误响应 |
| session_manage | MCP | — | 文件操作 | 错误响应 |
| workflow_dispatch | MCP | — | 内存/文件 | 错误响应 |
| agent_status | MCP | — | 文件解析 | 错误响应 |
| hook_manage | MCP | 脚本 | 内嵌逻辑 | 跳过 |
| resource_load_status | MCP | — | 文件读取 | 错误响应 |
| context_compress | MCP | — | 内嵌压缩 | 错误响应 |
| server_health | MCP | — | 内存读取 | 错误响应 |

### 如何判断当前降级级别

1. **查看响应中的 `degradation_level` 字段**

| degradation_level | 含义 |
|-------------------|------|
| 无此字段 | 全功能正常（MCP + 脚本） |
| `"script"` | 脚本执行成功 |
| `"inline"` | 降级到内嵌逻辑 |
| `"partial"` | 部分功能降级 |
| `"chromadb"` | ChromaDB 语义搜索 |
| `"sqlite_fts5"` | SQLite FTS5 全文搜索 |
| `"keyword_fallback"` | 关键词文件扫描 |

2. **调用 server_health 查看降级统计**

```json
{
  "action": "server_health"
}
```

返回的 `degradation_stats` 字段记录了每个工具的降级次数：

```json
{
  "degradation_stats": {
    "security_scan": 3,
    "spec_drift_detect": 1
  }
}
```

3. **查看日志**

降级时会输出 WARNING 级别日志：

```
WARNING [security_scan] security_scan degraded: agentic_scan -> inline
WARNING [spec_drift_detect] spec_drift_detect degraded: script -> inline
```

---

## 日志分析

### 结构化日志格式

xuansto-mcp-server 使用结构化日志，格式如下：

```
<LEVEL> [<tool_name>] <message>
```

示例：

```
INFO [skill_analyze] skill_analyze called: skill_path=/path/to/project
WARNING [security_scan] security_scan degraded: agentic_scan -> inline
ERROR [knowledge_search] knowledge_search error: ChromaDB connection failed
```

### 关键日志级别

| 级别 | 说明 | 常见场景 |
|------|------|----------|
| DEBUG | 详细调试信息 | 参数解析、中间结果 |
| INFO | 正常操作信息 | 工具调用、操作完成 |
| WARNING | 降级/异常信息 | 脚本执行失败降级、配置缺失 |
| ERROR | 操作失败 | 脚本执行错误、数据损坏 |

### 常见日志模式

#### 1. 正常调用

```
INFO [quality_gate_check] quality_gate_check called: gate_ids=['TEST-PASS'] phase=None
```

**含义：** 工具正常调用，无需关注。

#### 2. 降级警告

```
WARNING [spec_drift_detect] spec_drift_detect degraded: no script -> inline
WARNING [security_scan] security_scan degraded: agentic_scan -> inline
WARNING [code_simplify] code_simplify degraded: simplification -> inline
```

**含义：** 脚本不可用，降级到内嵌逻辑。功能基本可用，但精度可能降低。

**处理方式：**
- 检查 `$XUANSTO_SKILL_ROOT/scripts/` 目录是否包含对应脚本
- 如果不需要完整脚本功能，可以忽略此警告

#### 3. 缓存命中

```
INFO [quality_gate_check] Cache hit: returning cached gate results
```

**含义：** 门禁检查命中缓存，直接返回缓存结果。

#### 4. 错误日志

```
ERROR [knowledge_search] knowledge_search error: database disk image is malformed
```

**含义：** 操作失败，需要排查。

**处理方式：**
- 删除损坏的数据库文件：`rm $XUANSTO_SKILL_ROOT/knowledge/index/knowledge.db`
- 重启 Server，系统会自动重建索引

---

## 性能问题

### 门禁检查慢

**症状：** `quality_gate_check` 执行时间超过 10 秒

**原因：** 门禁检查需要遍历项目文件，大型项目可能较慢

**解决方案：**

1. **使用增量缓存**

门禁检查默认启用文件哈希缓存。文件未变更时，直接返回缓存结果。

```json
{
  "gate_ids": ["TEST-PASS"],
  "project_path": ".",
  "force_refresh": false
}
```

2. **按阶段过滤**

只检查当前阶段的门禁，而非全部：

```json
{
  "phase": "4",
  "project_path": "."
}
```

3. **指定门禁 ID**

只检查需要的门禁：

```json
{
  "gate_ids": ["TEST-PASS", "FILE-ENCODING"],
  "project_path": "."
}
```

4. **清理缓存**

如果缓存数据异常，删除缓存文件：

```bash
rm .xuansto/gate_cache.json
```

### 知识检索慢

**症状：** `knowledge_search` 执行时间超过 5 秒

**原因：** ChromaDB 向量搜索或 SQLite FTS5 索引未建立

**解决方案：**

1. **检查降级级别**

如果 `degradation_level` 为 `keyword_fallback`，说明数据库不可用。

2. **构建索引**

首次使用 `knowledge_search` 时，系统会自动创建 SQLite FTS5 索引。确保 `knowledge/index/` 目录可写。

3. **安装 ChromaDB**

```bash
pip install chromadb
# 或
pip install xuansto-mcp-server[full]
```

4. **使用 keyword_only 模式**

如果不需要语义搜索，使用关键词模式更快：

```json
{
  "action": "retrieve",
  "query": "数据库连接超时",
  "search_type": "keyword_only"
}
```

5. **限制搜索范围**

```json
{
  "action": "retrieve",
  "query": "数据库连接超时",
  "scope": "experience",
  "top_k": 3
}
```

### Hook 拦截慢

**症状：** 工具调用前 Hook 执行时间过长

**原因：** Hook 脚本执行耗时或扫描文件过多

**解决方案：**

1. **使用 minimal profile**

只启用安全拦截和会话保存：

```json
{
  "action": "list",
  "profile": "minimal"
}
```

2. **禁用特定 Hook**

修改 `.xuansto-config.yaml`，将不需要的 Hook 脚本设为 `null`：

```yaml
hook_scripts:
  auto-format: null
  console-log-detect: null
  type-check: null
```

3. **使用内嵌逻辑**

内嵌 Hook 逻辑比脚本执行更快。确保 Hook 有内嵌逻辑（`has_inline_logic: true`）。

---

## 配置热重载问题

### 热重载不生效

**症状：** 修改 `.xuansto-config.yaml` 后，配置未更新

**解决方案：**

1. **Linux/macOS：发送 SIGHUP 信号**

```bash
# 查找进程 ID
ps aux | grep xuansto-mcp-server

# 发送 SIGHUP
kill -HUP <pid>
```

2. **Windows：等待自动重载**

Windows 使用后台线程每 5 秒检查配置文件修改时间。等待最多 5 秒后配置自动生效。

3. **重启 Server**

最可靠的方式是重启 MCP Server。

### 配置文件格式错误

**症状：** 修改配置后 Server 行为异常

**解决方案：**

1. **验证 YAML 语法**

```bash
python -c "import yaml; yaml.safe_load(open('.xuansto-config.yaml'))"
```

2. **使用默认配置**

删除 `.xuansto-config.yaml`，系统会使用内置默认配置。

3. **检查配置字段**

确保 `gate_scripts`、`gates_by_phase`、`hook_scripts` 字段格式正确：

```yaml
gate_scripts:
  GATE-007: "check-encoding.py"    # 字符串值

gates_by_phase:
  "0":                              # 阶段编号必须是字符串
    - "DESIGN-SYSTEM-COMPLETE"      # 列表值

hook_scripts:
  security-block: null              # null 表示无脚本，使用内嵌逻辑
```

### 工作目录权限问题

**症状：** 无法创建 `.xuansto/` 目录或写入文件

**解决方案：**

1. **检查目录权限**

```bash
ls -la .xuansto/
```

2. **手动创建目录**

```bash
mkdir -p .xuansto/sessions .xuansto/patterns .xuansto/workflows
```

3. **设置 XUANSTO_WORK_DIR**

将工作目录设为有写权限的路径：

```bash
export XUANSTO_WORK_DIR=/tmp/xuansto-work
```

---

## 常见错误排查流程

### 工具调用返回错误

```
1. 检查错误码（PATH_NOT_FOUND / VALIDATION_ERROR / SCRIPT_EXECUTION_ERROR）
2. 查看错误详情（details 字段）
3. 根据错误码参考上方解决方案
4. 如为降级错误，检查 degradation_level 字段
5. 调用 server_health 查看全局状态
```

### 工具调用无响应

```
1. 检查 Server 是否运行（server_health）
2. 检查日志是否有 ERROR 级别输出
3. 检查是否超时（脚本默认 30-120 秒）
4. 重启 Server
```

### 结果不符合预期

```
1. 检查 degradation_level — 可能降级到内嵌逻辑
2. 检查参数是否正确（如 scope、search_type）
3. 对比脚本执行和内嵌逻辑的结果差异
4. 使用 force_refresh: true 刷新缓存
5. 查看日志了解降级原因
```
