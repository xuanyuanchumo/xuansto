# 路径配置管理使用指南

> 📁 **统一管理，灵活配置** - 通过路径配置管理器实现技能路径的集中管理和灵活配置

---

## 概述

路径配置管理器是三省六部技能的基础设施组件，提供统一的路径配置、管理和验证功能。通过路径管理器，可以实现路径的集中管理、环境变量覆盖、动态解析和健康检查。

### 核心功能

- **路径集中管理**：所有路径配置统一管理，便于维护
- **环境变量支持**：支持通过环境变量覆盖默认路径
- **动态路径解析**：支持按需解析和创建路径
- **健康检查**：自动检测路径状态，生成诊断报告
- **快照管理**：支持路径状态快照和恢复
- **路径验证功能**：从 Markdown 文档中自动提取脚本调用路径，验证路径是否存在、是否可执行，自动更正错误的路径前缀
- **输出路径管理**：支持基于时间戳、任务ID等动态生成输出路径，支持 JSON、Markdown、HTML 等多种报告格式
- **环境变量注入**：支持从 `.env` 文件读取环境变量，在路径配置中使用 `${VAR_NAME}` 格式引用环境变量

---

## 使用示例

### 路径验证功能

#### 1. 验证单个文档
```bash
python skillscripts/utils/skill_doc_path_validator.py validate --file subskills/skill_path_management.md
```

#### 2. 验证整个 subskills 目录
```bash
python skillscripts/utils/skill_doc_path_validator.py validate --dir subskills
```

#### 3. 自动修复路径前缀错误
```bash
# 预览修复（不实际修改）
python skillscripts/utils/skill_doc_path_validator.py fix --files subskills/*.md --dry-run

# 实际修复并创建备份
python skillscripts/utils/skill_doc_path_validator.py fix --files subskills/*.md
```

## 4. 提取文档中的路径
```bash
python skillscripts/utils/skill_doc_path_validator.py extract --file subskills/skill_path_management.md --format json
```

**验证结果说明**：
- `valid`：路径正确且文件存在
- `missing`：路径格式正确但文件不存在
- `wrong_prefix`：路径前缀错误（如使用了 `scripts/` 而非 `skillscripts/`）
- `invalid_format`：路径格式无法识别

### 输出路径管理

#### 1. 动态输出路径
```python
from skillscripts.utils.enhanced_path_config_manager import create_path_manager, PathKey

manager = create_path_manager()

# 获取报告输出路径（自动创建时间戳子目录）
report_path = manager.get_output_path(
    "health_report",
    format="markdown",
    create_dirs=True
)

# 自定义输出路径模板
custom_path = manager.get_output_path(
    "analysis",
    template="{category}/{date}/{name}_{timestamp}.{ext}",
    category="performance",
    name="analysis_report"
)
```

## 2. 多格式输出支持
```python
# JSON 格式报告
json_path = manager.get_output_path("report", format="json")

# Markdown 格式报告
md_path = manager.get_output_path("report", format="markdown")

# HTML 格式报告
html_path = manager.get_output_path("report", format="html")
```

## 3. 输出目录清理
```python
# 清理 7 天前的报告
cleaned = manager.cleanup_old_reports(days=7)

# 清理特定类型的报告
cleaned = manager.cleanup_old_reports(
    pattern="health_report_*.json",
    days=30
)
```

## 环境变量支持

#### 1. 配置环境变量
创建 `.env` 文件：
```env
# 数据库配置
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=skill_db

# 后端配置
BACKEND_HOST=localhost
BACKEND_PORT=8000

# 前端配置
FRONTEND_HOST=localhost
FRONTEND_PORT=3000

# 自定义路径
CUSTOM_DATA_DIR=/data/skill
CUSTOM_LOG_DIR=/var/log/skill
```

## 2. 在路径配置中使用环境变量
```python
from skillscripts.utils.enhanced_path_config_manager import create_path_manager

manager = create_path_manager()

# 使用环境变量（带默认值）
data_dir = manager.resolve_env_path(
    "${CUSTOM_DATA_DIR:-./data}"
)

# 使用环境变量（无默认值）
log_dir = manager.resolve_env_path(
    "${CUSTOM_LOG_DIR}"
)

# 组合使用
output_path = manager.resolve_env_path(
    "${CUSTOM_DATA_DIR:-./data}/reports/${TASK_ID}"
)
```

## 3. 环境变量验证
```python
# 检查必需的环境变量
required_vars = ["DATABASE_HOST", "DATABASE_PORT", "DATABASE_NAME"]
validation = manager.validate_env_vars(required_vars)

if not validation["valid"]:
    print(f"缺失环境变量: {validation['missing']}")
```

---

## 路径配置管理器使用指南

### 快速开始

#### 基本使用

```python
from skillscripts.utils.enhanced_path_config_manager import create_path_manager, PathKey

manager = create_path_manager()

print(f"技能根目录: {manager.skill_root}")
print(f"脚本目录: {manager.resolve_path(PathKey.SCRIPTS_DIR)}")
print(f"数据目录: {manager.resolve_path(PathKey.DATA_DIR)}")
print(f"日志目录: {manager.resolve_path(PathKey.LOGS_DIR)}")
```

#### 获取子技能路径

```python
from skillscripts.utils.enhanced_path_config_manager import create_path_manager

manager = create_path_manager()

subskill_path = manager.get_subskill_path("test")
print(f"子技能路径: {subskill_path}")

all_subskills = manager.get_all_subskills()
for subskill in all_subskills:
    print(f"  - {subskill.name}: {subskill.path}")
```

#### 获取脚本路径

```python
from skillscripts.utils.enhanced_path_config_manager import create_path_manager, ScriptType

manager = create_path_manager()

script_path = manager.get_script_path("auto_fixer", ScriptType.OPTIMIZATION)
print(f"脚本路径: {script_path}")

template_path = manager.get_template_path("sdd_guifan_muban.md")
print(f"模板路径: {template_path}")

report_path = manager.get_report_path("analysis_report.md")
print(f"报告路径: {report_path}")
```

### 路径键列表

| 路径键 | 说明 | 默认路径 |
|--------|------|----------|
| `SKILL_ROOT` | 技能根目录 | `.trae/skills/sanliu/` |
| `SKILL_MD` | SKILL.md 文件 | `SKILL.md` |
| `VERSION_FILE` | version.json 文件 | `version.json` |
| `CONFIG_DIR` | 配置目录 | `config/` |
| `SUBSKILLS_DIR` | 子技能目录 | `subskills/` |
| `SCRIPTS_DIR` | 脚本根目录 | `skillscripts/` |
| `CORE_SCRIPTS_DIR` | 核心脚本目录 | `skillscripts/core/` |
| `PIPELINE_SCRIPTS_DIR` | 流水线脚本目录 | `skillscripts/pipeline/` |
| `TEST_SCRIPTS_DIR` | 测试脚本目录 | `skillscripts/test/` |
| `ANALYSIS_SCRIPTS_DIR` | 分析脚本目录 | `skillscripts/analysis/` |
| `OPTIMIZATION_SCRIPTS_DIR` | 优化脚本目录 | `skillscripts/optimization/` |
| `UTILITY_SCRIPTS_DIR` | 工具脚本目录 | `skillscripts/utils/` |
| `RESOURCES_DIR` | 资源目录 | `resources/` |
| `TEMPLATES_DIR` | 模板目录 | `resources/templates/` |
| `DATA_DIR` | 数据目录 | `data/` |
| `REPORTS_DIR` | 报告目录 | `reports/` |
| `DOCS_DIR` | 文档目录 | `docs/` |
| `TESTS_DIR` | 测试目录 | `tests/` |
| `BACKEND_DIR` | 后端目录 | `backend/` |
| `FRONTEND_DIR` | 前端目录 | `frontend/` |
| `LOGS_DIR` | 日志目录 | `logs/` |
| `CACHE_DIR` | 缓存目录 | `.cache/` |
| `TEMP_DIR` | 临时目录 | `.temp/` |

### 命令行使用

```bash
python skillscripts/utils/enhanced_path_config_manager.py --info

python skillscripts/utils/enhanced_path_config_manager.py --init

python skillscripts/utils/enhanced_path_config_manager.py --validate

python skillscripts/utils/enhanced_path_config_manager.py --health-check

python skillscripts/utils/enhanced_path_config_manager.py --list-subskills

python skillscripts/utils/enhanced_path_config_manager.py --snapshot

python skillscripts/utils/enhanced_path_config_manager.py --export-config path_config.json
```

---

## 环境变量配置说明

### 环境变量格式

路径管理器支持通过环境变量覆盖默认路径配置。环境变量格式为 `SANLIU_<PATH_KEY>`。

### 支持的环境变量

```bash
export SANLIU_SKILL_ROOT=/custom/skill/root
export SANLIU_DATA_DIR=/custom/data
export SANLIU_LOGS_DIR=/custom/logs
export SANLIU_REPORTS_DIR=/custom/reports
export SANLIU_DOCS_DIR=/custom/docs
export SANLIU_TESTS_DIR=/custom/tests
export SANLIU_BACKEND_DIR=/custom/backend
export SANLIU_FRONTEND_DIR=/custom/frontend
export SANLIU_CACHE_DIR=/custom/cache
export SANLIU_TEMP_DIR=/custom/temp
```

### 使用示例

#### 通过环境变量覆盖路径

```python
import os
from skillscripts.utils.enhanced_path_config_manager import create_path_manager, PathKey

os.environ["SANLIU_DATA_DIR"] = "/custom/data/path"
os.environ["SANLIU_LOGS_DIR"] = "/custom/logs/path"

manager = create_path_manager()

print(f"数据目录: {manager.resolve_path(PathKey.DATA_DIR)}")
print(f"日志目录: {manager.resolve_path(PathKey.LOGS_DIR)}")
```

#### 使用环境变量管理器

```python
from skillscripts.utils.enhanced_path_config_manager import (
    create_path_manager, 
    EnvironmentVariableManager, 
    PathKey
)

EnvironmentVariableManager.set_env_override(PathKey.DATA_DIR, "/custom/data")
EnvironmentVariableManager.set_env_override(PathKey.LOGS_DIR, "/custom/logs")

manager = create_path_manager()
print(f"数据目录: {manager.resolve_path(PathKey.DATA_DIR)}")

EnvironmentVariableManager.clear_env_override(PathKey.DATA_DIR)
```

### 配置文件方式

除了环境变量，还可以通过配置文件设置路径：

#### YAML 配置

```yaml
paths:
  data_dir: /custom/data
  logs_dir: /custom/logs
  reports_dir: /custom/reports
  docs_dir: /custom/docs
  cache_dir: /custom/cache
```

#### JSON 配置

```json
{
  "paths": {
    "data_dir": "/custom/data",
    "logs_dir": "/custom/logs",
    "reports_dir": "/custom/reports",
    "docs_dir": "/custom/docs",
    "cache_dir": "/custom/cache"
  }
}
```

### 环境变量优先级

路径解析优先级从高到低：

1. **代码中直接指定的路径**
2. **环境变量覆盖**
3. **配置文件中的路径**
4. **默认路径**

---

## 路径迁移指南

### 迁移概述

路径迁移是将硬编码路径转换为动态路径管理的过程，提高代码的可维护性和可移植性。

### 迁移模式

#### 模式1：数据存储路径迁移

```python
# 迁移前
def __init__(self, storage_path: Optional[Path] = None):
    self.storage_path = storage_path or Path("data/issues/issues.json")

# 迁移后
def __init__(self, storage_path: Optional[Path] = None):
    if storage_path is None:
        try:
            from skillscripts.utils.enhanced_path_config_manager import create_path_manager, PathKey
            manager = create_path_manager()
            self.storage_path = manager.resolve_path(PathKey.DATA_DIR) / "issues" / "issues.json"
        except Exception:
            self.storage_path = Path("data/issues/issues.json")
    else:
        self.storage_path = storage_path
```

## 模式2：日志路径迁移

```python
# 迁移前
logging.FileHandler('logs/ui_ux_integration.log', encoding='utf-8', mode='a')

# 迁移后
try:
    from skillscripts.utils.enhanced_path_config_manager import create_path_manager, PathKey
    _path_manager = create_path_manager()
    _log_path = _path_manager.resolve_path(PathKey.LOGS_DIR) / "ui_ux_integration.log"
    logging.FileHandler(str(_log_path), encoding='utf-8', mode='a')
except Exception:
    logging.FileHandler('logs/ui_ux_integration.log', encoding='utf-8', mode='a')
```

## 模式3：报告输出路径迁移

```python
# 迁移前
parser.add_argument("--output", type=Path, default=Path("docs/reports"))

# 迁移后
parser.add_argument("--output", type=Path, default=None)

if args.output is None:
    try:
        from skillscripts.utils.enhanced_path_config_manager import create_path_manager, PathKey
        _manager = create_path_manager()
        args.output = _manager.resolve_path(PathKey.DOCS_DIR) / "reports"
    except Exception:
        args.output = Path("docs/reports")
```

## 迁移检查清单

```markdown
- [ ] 识别所有硬编码路径
- [ ] 确定路径类型（数据、日志、报告等）
- [ ] 选择合适的迁移模式
- [ ] 添加异常处理和降级机制
- [ ] 测试迁移后的功能
- [ ] 更新相关文档
```

### 迁移工具

```bash
python skillscripts/utils/path_migration_tool.py scan \
  --directory ./skillscripts \
  --output migration_report.json

python skillscripts/utils/path_migration_tool.py migrate \
  --file skillscripts/analysis/issue_tracker.py \
  --backup

python skillscripts/utils/path_migration_tool.py validate \
  --directory ./skillscripts
```

---

## 最佳实践

### 1. 使用单例模式获取管理器

```python
from skillscripts.utils.enhanced_path_config_manager import create_path_manager

def my_function():
    manager = create_path_manager()
    data_dir = manager.resolve_path(PathKey.DATA_DIR)
```

### 2. 始终添加异常处理

```python
from skillscripts.utils.enhanced_path_config_manager import create_path_manager, PathKey

try:
    manager = create_path_manager()
    path = manager.resolve_path(PathKey.DATA_DIR) / "my_data.json"
except Exception as e:
    path = Path("data/my_data.json")
    logging.warning(f"路径管理器不可用，使用默认路径: {e}")
```

### 3. 使用路径键而非字符串

```python
from skillscripts.utils.enhanced_path_config_manager import create_path_manager, PathKey

manager = create_path_manager()

data_dir = manager.resolve_path(PathKey.DATA_DIR)
```

### 4. 重要操作前创建快照

```python
from skillscripts.utils.enhanced_path_config_manager import create_path_manager

manager = create_path_manager()

snapshot = manager.create_snapshot("before_update")
print(f"快照ID: {snapshot.snapshot_id}")

try:
    pass
finally:
    pass
```

### 5. 定期执行健康检查

```python
from skillscripts.utils.enhanced_path_config_manager import create_path_manager

manager = create_path_manager()

report = manager.health_checker.perform_health_check()

if report.health_score < 0.8:
    print("路径健康分数较低，建议检查:")
    for rec in report.recommendations:
        print(f"  - {rec}")
```

### 6. 配置导出与备份

```python
from skillscripts.utils.enhanced_path_config_manager import create_path_manager

manager = create_path_manager()

config = manager.export_config("path_config_backup.json")
print("配置已备份")
```

### 7. 懒加载模式

```python
from skillscripts.utils.enhanced_path_config_manager import create_path_manager

manager = create_path_manager(lazy_init=True)

manager.ensure_path(PathKey.DATA_DIR)
```

---

## 常见问题

### Q: 路径管理器初始化失败？

```python
try:
    from skillscripts.utils.enhanced_path_config_manager import create_path_manager
    manager = create_path_manager()
except ImportError:
    print("路径管理器模块未找到，使用默认路径")
except Exception as e:
    print(f"路径管理器初始化失败: {e}")
```

### Q: 如何处理跨平台路径问题？

```python
from pathlib import Path
from skillscripts.utils.enhanced_path_config_manager import create_path_manager, PathKey

manager = create_path_manager()

path = manager.resolve_path(PathKey.DATA_DIR) / "subdir" / "file.json"
```

### Q: 如何验证路径是否存在？

```python
from skillscripts.utils.enhanced_path_config_manager import create_path_manager, PathKey

manager = create_path_manager()

if manager.validate_path(PathKey.DATA_DIR):
    print("数据目录存在")
else:
    manager.ensure_path(PathKey.DATA_DIR)
    print("数据目录已创建")
```

### Q: 如何获取相对路径？

```python
from skillscripts.utils.enhanced_path_config_manager import create_path_manager

manager = create_path_manager()

absolute_path = "/full/path/to/file.txt"
relative_path = manager.get_relative_path(absolute_path)
print(f"相对路径: {relative_path}")
```

---

## 相关文档

- [持续演化系统](continuous_evolution.md)
- [自迭代机制](self_iteration.md)
- [脚本协同调用](skill_script_coordination.md)
- [知识库管理](knowledge_base.md)
