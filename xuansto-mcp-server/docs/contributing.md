# 贡献指南

感谢你对 xuansto-mcp-server 项目的关注！本文档将帮助你了解如何参与项目开发。

---

## 开发环境搭建

### 前置要求

- **Python 3.10+**（推荐 3.11 或 3.12）
- **Git** 2.30+
- **uv**（推荐）或 **pip**

### 克隆项目

```bash
git clone https://github.com/skiller-team/xuansto-mcp-server.git
cd xuansto-mcp-server
```

### 安装依赖

**使用 uv（推荐）：**

```bash
uv venv
uv pip install -e ".[dev]"
```

**使用 pip：**

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -e ".[dev]"
```

### 安装完整依赖（可选）

如需 ChromaDB 语义搜索等高级功能：

```bash
pip install -e ".[full]"
```

### 验证安装

```bash
python -c "import xuansto_mcp; print(xuansto_mcp.__version__)"
```

---

## 代码规范

### Ruff Lint

项目使用 [Ruff](https://docs.astral.sh/ruff/) 作为代码检查和格式化工具。

```bash
ruff check src/
ruff check src/ --fix
ruff format src/
```

配置位于 `pyproject.toml`：

- 行宽上限：120 字符
- 目标 Python 版本：3.10
- 启用规则：E, F, W, I, N, UP, B, A, SIM
- 忽略规则：E501（行长度由 Ruff format 处理）

### MyPy Strict

项目使用 mypy strict 模式进行类型检查。

```bash
mypy src/xuansto_mcp/
```

配置位于 `pyproject.toml`：

- `strict = true`
- `disallow_untyped_defs = true`
- `disallow_any_generics = true`
- `warn_return_any = true`
- `ignore_missing_imports = true`（data 目录下的脚本不参与检查）

### 代码风格要求

1. **所有文件必须包含** `from __future__ import annotations`，放在文件顶部
2. 使用 Python 3.10+ 语法（`X | Y` 替代 `Union[X, Y]`，`list[str]` 替代 `List[str]`）
3. 使用 Pydantic v2 风格（`BaseModel`，`ConfigDict`，`Field`）
4. 函数和类必须有类型注解
5. 不允许 `Any` 未加限制地使用，必须尽量具体化类型

---

## 提交规范

项目遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范。

### 提交格式

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Type 列表

| Type | 说明 | 示例 |
|------|------|------|
| feat | 新功能 | `feat(tools): add code_simplify tool` |
| fix | 修复 Bug | `fix(knowledge): fix chromadb connection timeout` |
| docs | 文档变更 | `docs(api): update tool parameter descriptions` |
| refactor | 重构（不改变功能） | `refactor(core): extract common validation logic` |
| test | 测试相关 | `test(tools): add tests for security_scan` |
| chore | 构建/工具变更 | `chore(deps): update pydantic to 2.7` |
| perf | 性能优化 | `perf(gates): add file hash caching for gate checks` |
| ci | CI/CD 变更 | `ci: add Python 3.13 to test matrix` |

### Scope 列表

| Scope | 说明 |
|-------|------|
| tools | MCP 工具实现 |
| core | 核心模块（config, errors, degradation, validator） |
| models | Pydantic 数据模型 |
| cli | 命令行接口 |
| server | MCP Server 入口 |

### 示例

```bash
git commit -m "feat(tools): add context_compress tool with semantic/selective/lossless strategies"
git commit -m "fix(core): handle missing config file gracefully in reload_config"
git commit -m "docs(api): add parameter tables for all 13 MCP tools"
```

---

## PR 流程

### 1. Fork 仓库

在 GitHub 上 Fork 项目到你的账号。

### 2. 创建分支

```bash
git checkout -b feat/your-feature-name
```

分支命名规范：
- `feat/` — 新功能
- `fix/` — Bug 修复
- `docs/` — 文档更新
- `refactor/` — 代码重构

### 3. 开发与提交

```bash
# 编写代码
# 运行检查
ruff check src/ --fix
mypy src/xuansto_mcp/
pytest

# 提交
git add .
git commit -m "feat(tools): add your feature"
```

### 4. 推送与创建 PR

```bash
git push origin feat/your-feature-name
```

在 GitHub 上创建 Pull Request，填写以下信息：
- 变更描述
- 关联 Issue（如有）
- 测试说明
- 截图（如涉及 UI 变更）

### 5. Review 与合并

- 至少需要 1 位 Reviewer 批准
- CI 检查必须全部通过
- 代码必须通过 Ruff 和 MyPy 检查
- 合并使用 Squash Merge

---

## 测试规范

### 测试框架

- **pytest** >= 7.0
- **pytest-asyncio** >= 0.21
- **pytest-cov** >= 4.0

### 配置

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### 运行测试

```bash
# 运行全部测试
pytest

# 运行指定模块测试
pytest tests/test_quality_gate_check.py

# 运行并显示覆盖率
pytest --cov=xuansto_mcp --cov-report=term-missing

# 运行指定标记
pytest -m "not slow"
```

### 测试编写要求

1. **异步测试**：使用 `asyncio_mode = "auto"`，直接编写 `async def test_xxx()` 即可
2. **测试命名**：`test_<tool>_<action>_<scenario>`，如 `test_knowledge_search_retrieve_hybrid`
3. **Mock 外部依赖**：使用 `unittest.mock` 或 `pytest.monkeypatch` 模拟文件系统、子进程等
4. **覆盖降级路径**：每个工具的测试必须覆盖降级场景
5. **测试数据**：使用 `tests/fixtures/` 目录存放测试数据

### 测试文件组织

```
tests/
├── conftest.py              # 公共 fixture
├── fixtures/                # 测试数据
│   ├── sample_project/
│   └── sample_knowledge/
├── test_skill_analyze.py
├── test_knowledge_search.py
├── test_quality_gate_check.py
├── test_spec_drift_detect.py
├── test_security_scan.py
├── test_code_simplify.py
├── test_session_manage.py
├── test_workflow_dispatch.py
├── test_agent_status.py
├── test_hook_manage.py
├── test_resource_load_status.py
├── test_context_compress.py
└── test_server_health.py
```

---

## 项目结构说明

```
xuansto-mcp-server/
├── .github/
│   └── workflows/
│       └── ci.yml                    # GitHub Actions CI 配置
├── docs/                             # 文档目录
│   ├── api.md                        # API 文档
│   ├── contributing.md               # 贡献指南
│   ├── migration-v1-to-v2.md         # 迁移指南
│   └── troubleshooting.md            # 故障排除
├── scripts/
│   └── start_server.py               # 启动脚本
├── src/
│   └── xuansto_mcp/
│       ├── __init__.py               # 包初始化，定义 __version__
│       ├── server.py                 # MCP Server 入口
│       ├── cli.py                    # CLI 入口
│       ├── core/                     # 核心模块
│       │   ├── config.py             # 配置管理（路径、环境变量、热重载）
│       │   ├── errors.py             # 错误类型与响应构造
│       │   ├── degradation.py        # 降级链与 fallback 映射
│       │   ├── logging_config.py     # 结构化日志配置
│       │   ├── subprocess_utils.py   # 子进程执行工具
│       │   └── validator.py          # Pydantic 输入校验
│       ├── models/
│       │   └── schemas.py            # 13 个工具的 Pydantic 输入模型
│       ├── tools/                    # 13 个 MCP 工具实现
│       │   ├── __init__.py
│       │   ├── skill_analyze.py
│       │   ├── knowledge_search.py
│       │   ├── quality_gate_check.py
│       │   ├── spec_drift_detect.py
│       │   ├── security_scan.py
│       │   ├── code_simplify.py
│       │   ├── session_manage.py
│       │   ├── workflow_dispatch.py
│       │   ├── agent_status.py
│       │   ├── hook_manage.py
│       │   ├── resource_load_status.py
│       │   ├── context_compress.py
│       │   └── server_health.py
│       └── data/                     # 内置数据
│           ├── agents/               # 57 个 Agent 定义
│           ├── hooks/                # Hook 配置
│           ├── knowledge/            # 知识库
│           ├── references/           # 参考文档
│           └── scripts/              # 检查脚本
├── tests/                            # 测试目录
├── pyproject.toml                    # 项目配置
├── mcp-config.json                   # MCP 客户端配置示例
└── LICENSE                           # MIT 许可证
```

### 核心模块说明

| 模块 | 职责 |
|------|------|
| `core/config.py` | 路径解析、环境变量读取、YAML 配置加载、配置热重载（SIGHUP/文件监听） |
| `core/errors.py` | 统一错误类型（PathNotFoundError, ScriptExecutionError 等）、响应构造 |
| `core/degradation.py` | 降级链定义、脚本 fallback、13 个工具的 fallback 函数映射 |
| `core/logging_config.py` | 结构化日志（JSON 格式）、日志级别管理 |
| `core/subprocess_utils.py` | 子进程执行封装、超时控制、输出解析 |
| `core/validator.py` | Pydantic 模型校验、参数验证 |
| `models/schemas.py` | 13 个工具的 Pydantic v2 输入模型定义 |

### 工具实现模式

每个工具文件遵循统一模式：

1. 导入依赖
2. 定义内嵌逻辑函数（以 `_` 前缀标识）
3. 定义 `register(mcp: FastMCP)` 函数
4. 在 `register` 内部使用 `@mcp.tool()` 装饰器注册工具
5. 工具函数内部：校验输入 → 执行脚本 → 降级到内嵌逻辑 → 返回结果

---

## 新增工具指南

如需添加新工具，请按以下步骤操作：

1. 在 `models/schemas.py` 中定义 Pydantic 输入模型
2. 在 `tools/` 目录下创建新工具文件
3. 实现 `register(mcp: FastMCP)` 函数
4. 在 `core/degradation.py` 中添加 fallback 函数
5. 在 `server.py` 中注册新工具
6. 编写测试
7. 更新 `docs/api.md`

### 工具模板

```python
from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core.errors import make_error_response, make_success_response
from ..core.logging_config import get_logger
from ..core.validator import validate_input
from ..models.schemas import YourToolInput

logger = get_logger("your_tool")


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        )
    )
    async def your_tool(
        param1: str,
        param2: int = 10,
    ) -> dict[str, Any]:
        """工具描述。"""
        validated, err = validate_input(YourToolInput, param1=param1, param2=param2)
        if err:
            return err
        logger.info("your_tool called: param1=%s", param1)
        # 实现逻辑
        return make_success_response({"result": "..."})
```

---

## 常见问题

### Q: Ruff 检查不通过怎么办？

运行 `ruff check src/ --fix` 自动修复可修复的问题，手动修复剩余问题。

### Q: MyPy 报错 `Any` 类型怎么办？

尽量使用具体类型替代 `Any`。如果确实需要，添加 `# type: ignore[xxx]` 注释并说明原因。

### Q: 测试中如何 Mock 文件系统？

使用 `pytest.monkeypatch` 或 `tmp_path` fixture：

```python
def test_something(monkeypatch, tmp_path):
    monkeypatch.setattr("xuansto_mcp.core.config.SKILL_ROOT", tmp_path)
```

### Q: 如何运行单个工具的 MCP Server？

```bash
python -m xuansto_mcp.server
# 或
uvx xuansto-mcp-server
```
