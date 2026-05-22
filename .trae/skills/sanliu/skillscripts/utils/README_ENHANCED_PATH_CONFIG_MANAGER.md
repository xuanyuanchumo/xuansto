# 增强版路径配置管理器

## 概述

增强版路径配置管理器（`EnhancedSkillPathManager`）是一个功能完整的路径管理工具，专为三省六部技能设计，提供了统一的路径配置、管理和验证功能。

## 主要功能

### 1. 技能根路径配置
- `SKILL_ROOT`: 技能根目录
- `SKILL_MD`: SKILL.md 文件路径
- `VERSION_FILE`: version.json 路径
- `CONFIG_DIR`: 配置目录路径

### 2. 子技能路径配置
- `SUBSKILLS_DIR`: 子技能目录
- 支持动态获取所有子技能文件路径
- 支持按名称获取特定子技能路径

### 3. 脚本路径配置
- `SCRIPTS_DIR`: 脚本根目录
- `CORE_SCRIPTS_DIR`: 核心脚本目录
- `PIPELINE_SCRIPTS_DIR`: 流水线脚本目录
- `TEST_SCRIPTS_DIR`: 测试脚本目录
- `ANALYSIS_SCRIPTS_DIR`: 分析脚本目录
- `OPTIMIZATION_SCRIPTS_DIR`: 优化脚本目录
- `REQUIREMENTS_SCRIPTS_DIR`: 需求脚本目录
- `UTILITY_SCRIPTS_DIR`: 工具脚本目录
- `MONITORING_SCRIPTS_DIR`: 监控脚本目录

### 4. 资源路径配置
- `RESOURCES_DIR`: 资源目录
- `TEMPLATES_DIR`: 模板目录
- `DATA_DIR`: 数据目录
- `REPORTS_DIR`: 报告目录

### 5. 动态路径解析
- `resolve_path(path_key)`: 根据键名解析路径
- `get_relative_path(absolute_path)`: 获取相对路径
- `validate_path(path)`: 验证路径是否存在
- `ensure_path(path_key)`: 确保路径存在，不存在则创建

### 6. 环境变量支持
- 支持通过环境变量覆盖默认路径
- 环境变量格式: `SANLIU_<PATH_KEY>`
- 例如: `SANLIU_DATA_DIR=/custom/data/path`

### 7. 单例模式
- 全局唯一实例
- 线程安全

### 8. 配置热重载
- 支持动态重新加载配置
- 可配置重载间隔

## 快速开始

### 基本使用

```python
from enhanced_path_config_manager import create_path_manager, PathKey

# 创建管理器实例
manager = create_path_manager()

# 获取技能根目录
print(f"技能根目录: {manager.skill_root}")

# 解析路径
scripts_dir = manager.resolve_path(PathKey.SCRIPTS_DIR)
print(f"脚本目录: {scripts_dir}")

# 获取子技能路径
subskill_path = manager.get_subskill_path("test_skill")
print(f"子技能路径: {subskill_path}")

# 获取所有子技能
subskills = manager.get_all_subskills()
for subskill in subskills:
    print(f"  - {subskill.name}: {subskill.path}")
```

### 环境变量使用

```python
import os
from enhanced_path_config_manager import EnvironmentVariableManager, PathKey

# 设置环境变量覆盖
os.environ["SANLIU_DATA_DIR"] = "/custom/data/path"

# 或者使用管理器
EnvironmentVariableManager.set_env_override(PathKey.DATA_DIR, "/custom/data/path")

# 获取环境变量覆盖
env_value = EnvironmentVariableManager.get_env_override(PathKey.DATA_DIR)
print(f"环境变量覆盖: {env_value}")

# 清除环境变量覆盖
EnvironmentVariableManager.clear_env_override(PathKey.DATA_DIR)
```

### 工作空间管理

```python
from enhanced_path_config_manager import create_path_manager

manager = create_path_manager()

# 初始化工作空间
result = manager.initialize_workspace(verify=True, lazy=True)
print(f"初始化结果: {result}")

# 验证工作空间
validation = manager.validate_workspace()
print(f"验证结果: {validation}")

# 获取工作空间信息
info = manager.get_workspace_info()
print(f"健康分数: {info['health_score']}")
print(f"子技能数量: {info['subskills_count']}")
```

### 健康检查

```python
from enhanced_path_config_manager import create_path_manager

manager = create_path_manager()

# 执行健康检查
report = manager.health_checker.perform_health_check()

print(f"总目录数: {report.total_directories}")
print(f"存在目录数: {report.existing_directories}")
print(f"缺失目录数: {report.missing_directories}")
print(f"健康分数: {report.health_score}")

# 查看建议
for recommendation in report.recommendations:
    print(f"  - {recommendation}")
```

### 快照管理

```python
from enhanced_path_config_manager import create_path_manager

manager = create_path_manager()

# 创建快照
snapshot = manager.create_snapshot("my_snapshot")
print(f"快照ID: {snapshot.snapshot_id}")
print(f"文件数: {snapshot.file_count}")
print(f"总大小: {snapshot.total_size} 字节")

# 列出所有快照
snapshots = manager.snapshot_manager.list_snapshots()
for snap in snapshots:
    print(f"  - {snap['snapshot_id']} ({snap['timestamp']})")

# 加载快照
loaded = manager.snapshot_manager.load_snapshot("my_snapshot")
if loaded:
    print(f"快照加载成功: {loaded.snapshot_id}")
```

### 配置导出

```python
from enhanced_path_config_manager import create_path_manager

manager = create_path_manager()

# 导出配置到文件
config = manager.export_config("path_config.json")
print(f"配置已导出")

# 从配置文件创建实例
from enhanced_path_config_manager import EnhancedSkillPathManager
manager2 = EnhancedSkillPathManager.from_config_file("path_config.json")
```

## 命令行使用

```bash
# 显示基本信息
python enhanced_path_config_manager.py

# 初始化工作空间
python enhanced_path_config_manager.py --init

# 验证工作空间
python enhanced_path_config_manager.py --validate

# 执行健康检查
python enhanced_path_config_manager.py --health-check

# 创建快照
python enhanced_path_config_manager.py --snapshot

# 列出所有快照
python enhanced_path_config_manager.py --list-snapshots

# 显示工作空间信息
python enhanced_path_config_manager.py --info

# 列出所有子技能
python enhanced_path_config_manager.py --list-subskills

# 导出配置
python enhanced_path_config_manager.py --export-config config.json

# 指定技能根目录
python enhanced_path_config_manager.py --skill-root /path/to/skill/root --info
```

## API 参考

### EnhancedSkillPathManager

#### 属性

- `skill_root`: 技能根目录
- `path_config`: 路径配置对象
- `structure_manager`: 目录结构管理器
- `health_checker`: 目录健康检查器
- `snapshot_manager`: 目录快照管理器

#### 方法

- `resolve_path(path_key)`: 根据键名解析路径
- `get_relative_path(absolute_path)`: 获取相对路径
- `to_absolute_path(relative_path)`: 将相对路径转换为绝对路径
- `validate_path(path)`: 验证路径是否存在
- `ensure_path(path_key)`: 确保路径存在
- `get_subskill_path(subskill_name)`: 获取特定子技能路径
- `get_all_subskills()`: 获取所有子技能信息
- `get_script_path(script_name, script_type)`: 获取脚本路径
- `get_template_path(template_name)`: 获取模板路径
- `get_report_path(report_name)`: 获取报告路径
- `initialize_workspace(...)`: 初始化工作空间
- `validate_workspace(...)`: 验证工作空间
- `get_workspace_info()`: 获取工作空间信息
- `create_snapshot(snapshot_id)`: 创建工作空间快照
- `restore_from_snapshot(snapshot_id)`: 从快照恢复
- `reload_config(force)`: 重新加载配置
- `export_config(output_file)`: 导出配置
- `from_config_file(config_file)`: 从配置文件创建实例（类方法）
- `get_instance()`: 获取单例实例（类方法）
- `reset_instance()`: 重置单例实例（类方法）

### PathKey 枚举

所有可用的路径键：

- `SKILL_ROOT`: 技能根目录
- `SKILL_MD`: SKILL.md 文件
- `VERSION_FILE`: version.json 文件
- `CONFIG_DIR`: 配置目录
- `SUBSKILLS_DIR`: 子技能目录
- `SCRIPTS_DIR`: 脚本根目录
- `CORE_SCRIPTS_DIR`: 核心脚本目录
- `PIPELINE_SCRIPTS_DIR`: 流水线脚本目录
- `TEST_SCRIPTS_DIR`: 测试脚本目录
- `ANALYSIS_SCRIPTS_DIR`: 分析脚本目录
- `OPTIMIZATION_SCRIPTS_DIR`: 优化脚本目录
- `REQUIREMENTS_SCRIPTS_DIR`: 需求脚本目录
- `UTILITY_SCRIPTS_DIR`: 工具脚本目录
- `MONITORING_SCRIPTS_DIR`: 监控脚本目录
- `RESOURCES_DIR`: 资源目录
- `TEMPLATES_DIR`: 模板目录
- `DATA_DIR`: 数据目录
- `REPORTS_DIR`: 报告目录
- `DOCS_DIR`: 文档目录
- `TESTS_DIR`: 测试目录
- `BACKEND_DIR`: 后端目录
- `FRONTEND_DIR`: 前端目录
- `LOGS_DIR`: 日志目录
- `CACHE_DIR`: 缓存目录
- `TEMP_DIR`: 临时目录

## 测试

运行单元测试：

```bash
python test_enhanced_path_config_manager.py
```

运行示例代码：

```bash
python example_enhanced_path_config_manager.py
```

## 设计模式

### 单例模式

`EnhancedSkillPathManager` 使用单例模式，确保全局只有一个实例：

```python
# 两种方式获取实例
manager1 = EnhancedSkillPathManager()
manager2 = EnhancedSkillPathManager.get_instance()

# manager1 和 manager2 是同一个实例
assert manager1 is manager2
```

### 懒加载模式

默认使用懒加载模式，不预创建目录结构，按需创建：

```python
# 懒加载模式（默认）
manager = create_path_manager(lazy_init=True)

# 立即初始化
manager = create_path_manager(lazy_init=False)
```

## 最佳实践

1. **使用单例**: 通过 `create_path_manager()` 或 `EnhancedSkillPathManager.get_instance()` 获取实例
2. **环境变量**: 使用环境变量覆盖默认路径，便于不同环境配置
3. **懒加载**: 默认使用懒加载模式，减少不必要的目录创建
4. **健康检查**: 定期执行健康检查，确保目录结构完整
5. **快照**: 重要操作前创建快照，便于回滚
6. **配置导出**: 导出配置便于备份和迁移

## 注意事项

1. 路径分隔符在不同操作系统上可能不同（Windows: `\`, Linux/Mac: `/`）
2. 环境变量优先级高于默认配置
3. 快照仅保存目录结构，不保存文件内容
4. 单例实例在测试时需要手动重置

## 版本历史

- v1.0.0 (2026-03-31): 初始版本
  - 实现所有核心功能
  - 支持环境变量覆盖
  - 单例模式
  - 配置热重载
  - 完整的测试覆盖

## 许可证

MIT License
