# Hook生命周期系统

## 概述

Hook系统提供五类生命周期Hook，参照ECC的Hook架构设计，在Agent执行流程的关键节点注入自动化逻辑。

五类生命周期Hook：

- **PreToolUse** - 工具调用前拦截
- **PostToolUse** - 工具调用后处理
- **SessionStart** - 会话启动时初始化
- **Stop** - 会话停止时收尾
- **PreCompact** - 上下文压缩前保存状态

配置文件：`hooks/hooks.json`

运行时控制：通过环境变量 `ECC_HOOK_PROFILE` 切换配置级别

```bash
ECC_HOOK_PROFILE=minimal|standard|strict
```

---

## PreToolUse Hook

工具调用前的拦截与校验层。

### 安全拦截

检测并阻止以下高危操作：

| 危险操作 | 拦截策略 |
|---------|---------|
| `rm -rf /` | 阻止 |
| `rm -rf *` | 阻止 |
| `git push --force` | 阻止 |
| `git push -f` | 阻止 |
| 删除关键文件（package.json, tsconfig.json, Cargo.toml等） | 阻止 |
| `DROP TABLE` | 阻止 |
| `TRUNCATE` | 阻止 |
| `chmod 777` | 阻止 |
| `curl | bash` | 确认 |

### Token预算检查

根据当前Token使用率执行分级控制：

| 使用率区间 | 动作 |
|-----------|------|
| < 80% | 正常执行 |
| ≥ 80% | 警告，建议精简输出 |
| ≥ 95% | 阻止非关键操作，仅允许保存/提交类操作 |

### 危险命令确认

对以下SQL/Shell命令强制要求用户确认：

- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM`（无WHERE子句）
- `chmod 777`
- `chmod -R 777`
- `:(){:\|:&};:`（fork bomb）
- `dd if=/dev/zero`

---

## PostToolUse Hook

工具调用后的自动处理层。

### 自动格式化

编辑以下类型文件后自动运行格式化：

| 文件类型 | 命令 |
|---------|------|
| `.ts` / `.tsx` / `.js` / `.jsx` | `prettier --write <filepath>` |
| `.py` | `black <filepath>` |
| `.go` | `gofmt -w <filepath>` |
| `.rs` | `rustfmt <filepath>` |

### 类型检查

编辑 `.ts` / `.tsx` 文件后运行：

```bash
tsc --noEmit
```

仅在项目根目录存在 `tsconfig.json` 时触发。

### console.log检测

编辑前端代码文件后检查是否遗留 `console.log`：

- 扫描已编辑文件中的 `console.log` 调用
- 如发现遗留，输出警告信息及行号
- 不阻止操作，仅提醒

### 编码检查

新建或编辑文件后检查编码规范：

- 验证文件为UTF-8编码且无BOM头
- 检测是否包含替换字符 U+FFFD
- 不符合规范时输出警告

---

## SessionStart Hook

会话启动时的初始化层。

### 加载上次会话上下文

从 `.skill-logs/` 目录加载最近的会话摘要：

1. 扫描 `.skill-logs/` 目录下所有 `session-*.md` 文件
2. 按时间戳降序排列
3. 加载最近一条摘要作为上下文注入
4. 摘要包含：上次任务进度、未完成项、关键决策

### 知识库健康检查

检查本地知识库服务是否可用：

```bash
curl -s http://localhost:8765/health
```

- 返回200：知识库可用
- 无响应/错误：知识库不可用，降级为无知识库模式

### 平台检测

自动检测当前运行平台：

| 检测条件 | 平台标识 |
|---------|---------|
| 存在 `web/` 目录 | Web |
| 存在 `electron/` 或 `tauri/` 目录 | Desktop |
| 存在 `flutter/` 目录或 `pubspec.yaml` | Flutter |
| 以上均无 | 通用 |

平台标识影响后续Hook的文件类型判断和工具选择。

---

## Stop Hook

会话停止时的收尾层。

### 保存会话摘要

将会话摘要保存到 `.skill-logs/session-{timestamp}.md`：

```markdown
# 会话摘要 - {timestamp}

## 完成任务
- ...

## 未完成任务
- ...

## 关键决策
- ...

## 错误记录
- ...
```

### 未提交变更提醒

执行 `git status` 检查是否存在未提交变更：

- 存在未暂存变更：提醒用户是否需要提交
- 存在未推送提交：提醒用户是否需要推送
- 不自动执行任何git操作

### 经验沉淀触发

调用知识库的Precipitate流程：

1. 收集本次会话中的关键操作和决策
2. 提取可复用的模式和方法
3. 调用知识库API进行沉淀

```bash
curl -X POST http://localhost:8765/precipitate -d '{...}'
```

知识库不可用时跳过此步骤。

### 重复模式检测

检测本次会话中是否出现重复错误模式：

- 相同错误出现 ≥ 2次：标记为重复模式
- 触发技能草稿生成流程
- 草稿保存到 `.skill-drafts/` 目录
- 草稿内容包含：错误描述、触发条件、解决方案

---

## PreCompact Hook

上下文压缩前的状态保存层。

### 保存关键状态

将关键状态保存到 `.agent_cache/` 目录：

```
.agent_cache/
├── phase-state.json
├── decision-log.json
├── workflow-state.json
└── active-tasks.json
```

### Decision Log持久化

将内存中的Decision Log写入持久化存储：

```json
{
  "decisions": [
    {
      "id": "D001",
      "timestamp": "2026-05-12T10:30:00Z",
      "context": "...",
      "decision": "...",
      "rationale": "...",
      "alternatives": ["..."]
    }
  ]
}
```

### 当前Phase和工作流状态保存

保存当前执行状态：

```json
{
  "current_phase": "implementation",
  "workflow_id": "WF-001",
  "step_index": 5,
  "total_steps": 12,
  "pending_gates": ["GATE-006", "GATE-007"],
  "active_agents": ["agent-alpha", "agent-beta"]
}
```

---

## Hook配置级别

通过 `ECC_HOOK_PROFILE` 环境变量控制Hook启用范围。

### minimal

仅启用核心安全与数据保存Hook：

| Hook | 启用项 |
|------|-------|
| PreToolUse | 安全拦截 |
| Stop | 会话摘要保存 |

### standard

在minimal基础上增加开发辅助Hook：

| Hook | 启用项 |
|------|-------|
| PreToolUse | 安全拦截 |
| PostToolUse | 自动格式化 |
| SessionStart | 上下文加载 |
| Stop | 会话摘要保存 |

### strict

全部Hook启用：

| Hook | 启用项 |
|------|-------|
| PreToolUse | 安全拦截 + Token预算检查 + 危险命令确认 |
| PostToolUse | 自动格式化 + 类型检查 + console.log检测 + 编码检查 |
| SessionStart | 上下文加载 + 知识库健康检查 + 平台检测 |
| Stop | 会话摘要保存 + 未提交变更提醒 + 经验沉淀 + 重复模式检测 |
| PreCompact | 关键状态保存 + Decision Log持久化 + Phase状态保存 |

默认配置级别为 `standard`。

---

## hooks.json配置格式

```json
{
  "PreToolUse": [
    {
      "name": "security-intercept",
      "enabled": true,
      "profile": ["minimal", "standard", "strict"],
      "patterns": [
        "rm -rf /",
        "rm -rf *",
        "git push --force",
        "git push -f"
      ],
      "action": "block",
      "message": "检测到高危操作，已拦截"
    },
    {
      "name": "token-budget-check",
      "enabled": true,
      "profile": ["strict"],
      "thresholds": {
        "warn": 80,
        "block": 95
      },
      "action": "conditional-block",
      "message": "Token使用率已达{usage}%，建议精简输出"
    },
    {
      "name": "dangerous-command-confirm",
      "enabled": true,
      "profile": ["strict"],
      "patterns": [
        "DROP TABLE",
        "TRUNCATE",
        "chmod 777"
      ],
      "action": "confirm",
      "message": "检测到危险命令，请确认是否执行"
    }
  ],
  "PostToolUse": [
    {
      "name": "auto-format",
      "enabled": true,
      "profile": ["standard", "strict"],
      "extensions": [".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs"],
      "commands": {
        ".ts": "prettier --write {filepath}",
        ".tsx": "prettier --write {filepath}",
        ".js": "prettier --write {filepath}",
        ".jsx": "prettier --write {filepath}",
        ".py": "black {filepath}",
        ".go": "gofmt -w {filepath}",
        ".rs": "rustfmt {filepath}"
      }
    },
    {
      "name": "type-check",
      "enabled": true,
      "profile": ["strict"],
      "extensions": [".ts", ".tsx"],
      "command": "tsc --noEmit",
      "requireConfig": "tsconfig.json"
    },
    {
      "name": "console-log-detect",
      "enabled": true,
      "profile": ["strict"],
      "pattern": "console\\.log",
      "action": "warn"
    },
    {
      "name": "encoding-check",
      "enabled": true,
      "profile": ["strict"],
      "rules": {
        "encoding": "utf-8",
        "noBOM": true,
        "noReplacementChar": true
      },
      "action": "warn"
    }
  ],
  "SessionStart": [
    {
      "name": "load-previous-context",
      "enabled": true,
      "profile": ["standard", "strict"],
      "source": ".skill-logs/",
      "pattern": "session-*.md",
      "maxEntries": 1
    },
    {
      "name": "knowledge-base-health",
      "enabled": true,
      "profile": ["strict"],
      "endpoint": "http://localhost:8765/health",
      "timeout": 3000,
      "fallback": "degrade"
    },
    {
      "name": "platform-detect",
      "enabled": true,
      "profile": ["strict"],
      "indicators": {
        "Web": ["web/"],
        "Desktop": ["electron/", "tauri/"],
        "Flutter": ["flutter/", "pubspec.yaml"]
      }
    }
  ],
  "Stop": [
    {
      "name": "save-session-summary",
      "enabled": true,
      "profile": ["minimal", "standard", "strict"],
      "target": ".skill-logs/session-{timestamp}.md",
      "sections": ["completed", "pending", "decisions", "errors"]
    },
    {
      "name": "uncommitted-changes-reminder",
      "enabled": true,
      "profile": ["strict"],
      "command": "git status",
      "action": "remind"
    },
    {
      "name": "experience-precipitate",
      "enabled": true,
      "profile": ["strict"],
      "endpoint": "http://localhost:8765/precipitate",
      "method": "POST",
      "fallback": "skip"
    },
    {
      "name": "repeat-pattern-detect",
      "enabled": true,
      "profile": ["strict"],
      "threshold": 2,
      "output": ".skill-drafts/",
      "action": "generate-draft"
    }
  ],
  "PreCompact": [
    {
      "name": "save-critical-state",
      "enabled": true,
      "profile": ["strict"],
      "target": ".agent_cache/",
      "files": ["phase-state.json", "decision-log.json", "workflow-state.json", "active-tasks.json"]
    },
    {
      "name": "persist-decision-log",
      "enabled": true,
      "profile": ["strict"],
      "target": ".agent_cache/decision-log.json",
      "format": "json"
    },
    {
      "name": "save-phase-workflow-state",
      "enabled": true,
      "profile": ["strict"],
      "target": ".agent_cache/workflow-state.json",
      "fields": ["current_phase", "workflow_id", "step_index", "total_steps", "pending_gates", "active_agents"]
    }
  ]
}
```
