---
name: huanjing_peizhi_si
description: 环境配置司，负责dev/staging/prod环境配置、环境一致性保障。集成SecretsManager进行.env文件规范和密钥加载流程管理。
---
# 环境配置司技能指令

## 职责
- 多环境（dev/staging/prod）配置管理
- 环境一致性保障与漂移检测
- .env文件规范与模板管理
- SecretsManager集成：密钥安全加载
- 环境变量校验与注入

## SecretsManager集成

### 密钥加载流程

```
应用启动 → SecretsManager.load_secrets(env)
         → 密钥解密与验证
         → 环境变量注入（非日志输出）
         → 配置完整性校验
         → 应用就绪信号
```

### .env文件规范

```bash
# === 环境配置模板 ===
# 命名规则: 大写下划线_分组_名称

# --- 数据库配置 ---
DB_HOST=localhost
DB_PORT=5432
DB_NAME=skiller_dev
DB_USER=${DB_USER}          # 引用SecretsManager
DB_PASS=${DB_PASS}          # 敏感值禁止硬编码

# --- API服务 ---
API_BASE_URL=http://localhost:8000
API_TIMEOUT_SECONDS=30
API_RETRY_COUNT=3

# --- 日志配置 ---
LOG_LEVEL=DEBUG             # dev环境
LOG_FORMAT=json

# --- 功能开关 ---
FEATURE_TDD_ENABLED=true
FEATURE_AUTO_REPAIR=true
```

## 环境矩阵

| 环境 | 用途 | 数据隔离 | 访问控制 | 备份策略 |
|------|------|----------|----------|----------|
| dev | 开发调试 | 独立实例 | 团队内 | 每日快照 |
| staging | 预发布验证 | 独立实例 | 受限访问 | 每小时 |
| prod | 生产运行 | 高可用集群 | 最小权限 | 实时同步 |

## 环境一致性检查

### 检查项清单

```yaml
consistency_checks:
  config_files:
    - check: "version_match"
      description: "各环境配置版本一致"
    - check: "schema_valid"
      description: "配置文件结构符合Schema"

  dependencies:
    - check: "version_pinned"
      description: "依赖版本锁定一致"
    - check: "hash_verified"
      description: "包哈希值校验通过"

  secrets:
    - check: "no_hardcoded"
      description: "无硬编码敏感信息"
    - check: "rotation_policy"
      description: "密钥轮换策略有效"

  runtime:
    - check: "env_vars_complete"
      description: "必需环境变量齐全"
    - check: "type_correct"
      description: "变量类型转换正确"
```

## 工作流程

```
1. 接收环境配置请求（创建/更新/切换）
2. 选择目标环境模板
3. 通过SecretsManager加载敏感配置
4. 执行配置变量校验
5. 生成环境特定配置文件
6. 一致性检查（对比基准环境）
7. 部署配置到目标环境
8. 验证配置生效
9. 记录变更到DecisionLog
```

## 配置漂移检测

```python
def detect_config_drift(base_env, target_env):
    drift_report = {
        "drift_detected": False,
        "drift_items": [],
        "severity": "none"
    }

    for key in base_env.keys() | target_env.keys():
        base_val = base_env.get(key)
        target_val = target_env.get(key)

        if base_val != target_val:
            drift_report["drift_detected"] = True
            drift_report["drift_items"].append({
                "key": key,
                "base_value": mask_sensitive(base_val),
                "target_value": mask_sensitive(target_val),
                "is_sensitive": is_sensitive_key(key)
            })

    drift_report["severity"] = classify_drift_severity(drift_report)
    return drift_report
```

## 协同接口

| 接口 | 描述 | 调用方 |
|------|------|--------|
| `setup_env` | 环境初始化 | 项目启动/基础设施司 |
| `switch_env` | 环境切换 | 部署流程 |
| `check_consistency` | 一致性检查 | CI/CD流水线 |
| `rotate_secret` | 密钥轮换 | 安全审计 |
