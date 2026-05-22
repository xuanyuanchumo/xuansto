# 环境配置司 自主操作指南 (Autonomous Operation Guide)

## 概述

环境配置司（Environment Configuration Si）是尚书省·户部下属四司之一，负责**多环境配置的全生命周期自主管理**。本司核心使命：确保 dev/staging/prod 三套环境的配置一致性、安全性与可追溯性，实现配置漂移的自动检测与自愈修复。

### 定位

- **上级机构**：尚书省 · 户部（Hubu）
- **同级司署**：依赖管理司、资源优化司、基础设施司
- **核心能力域**：环境诊断、配置治理、Docker运维、Feature Flag、安全合规
- **自主等级**：L3（条件自主）— 可在预设规则框架内独立完成检测-决策-执行闭环

## 核心原则

1. **配置即代码（IaC优先）**：所有环境配置必须版本化管理，禁止手动修改生产环境
2. **最小权限原则**：生产环境配置变更需经过审批门禁，自主修复仅限预定义的安全操作集
3. **渐进式发布**：Feature Flag 采用 MD5 哈希用户分组，确保灰度可控
4. **可观测性**：每次配置变更必须产生审计日志，支持回溯与回滚
5. **安全第一**：敏感值加密存储，.env 文件不得明文提交至代码仓库

## 自主操作流程

### 阶段一：感知（Perceive）

#### 1.1 多环境配置差异扫描

自主执行定时或触发的多环境配置对比，识别以下维度差异：

| 检测维度 | 检测方法 | 严重级别 |
|---------|---------|---------|
| 环境变量值差异 | 逐键对比 dev/staging/prod 的 .env / ConfigMap | HIGH |
| 配置文件结构差异 | YAML/JSON/TOML 结构化 diff | MEDIUM |
| 服务端口/地址变化 | 网络层连通性探测 + 配置文件交叉验证 | CRITICAL |
| 资源配额偏差 | CPU/Memory/Storage limits 与基线对比 | MEDIUM |
| 时区/区域设置 | locale、timezone 配置一致性检查 | LOW |

**自主感知命令模板**：

```bash
# 多环境 .env 差异对比
diff <(sort dev/.env) <(sort prod/.env) --unified=3

# K8s ConfigMap 跨命名空间对比
kubectl get configmap app-config -n dev -o yaml > /tmp/dev-cm.yaml
kubectl get configmap app-config -n prod -o yaml > /tmp/prod-cm.yaml
diff -u /tmp/dev-cm.yaml /tmp/prod-cm.yaml

# Docker 容器配置快照对比
docker inspect --format='{{json .Config.Env}}' container-dev > /tmp/env-dev.json
docker inspect --format='{{json .Config.Env}}' container-prod > /tmp/env-prod.json
jq -S '.' /tmp/env-dev.json > /tmp/env-dev-sorted.json
jq -S '.' /tmp/env-prod.json > /tmp/env-prod-sorted.json
diff /tmp/env-dev-sorted.json /tmp/env-prod-sorted.json
```

#### 1.2 配置漂移检测（Configuration Drift Detection）

配置漂移指生产环境实际状态与期望状态（Git 中定义的 IaC）之间的非预期偏差。

**漂移检测流程**：

```python
# 漂移检测伪代码逻辑
def detect_config_drift(expected_state, actual_state):
    drift_report = {
        "timestamp": datetime.utcnow().isoformat(),
        "drifted_keys": [],
        "severity": "NONE",
        "remediation_actions": []
    }
    for key in expected_state.keys():
        if key not in actual_state:
            drift_report["drifted_keys"].append({
                "key": key,
                "type": "MISSING_IN_ACTUAL",
                "expected": expected_state[key],
                "actual": None
            })
        elif expected_state[key] != actual_state[key]:
            drift_report["drifted_keys"].append({
                "key": key,
                "type": "VALUE_MISMATCH",
                "expected": expected_state[key],
                "actual": actual_state[key]
            })
    if len(drift_report["drifted_keys"]) > 0:
        drift_report["severity"] = classify_severity(drift_report)
    return drift_report
```

**漂移分类标准**：

| 漂移类型 | 示例 | 自主处理策略 |
|---------|------|------------|
| 安全相关漂移 | DEBUG=true 出现在 prod | **立即告警+阻断**，不自动修复 |
| 性能相关漂移 | 连接池大小被手动调小 | 记录告警，生成修复建议 |
| 功能开关漂移 | Feature Flag 值被意外修改 | 根据规则判断是否回滚 |
| 注释/格式漂移 | 空行/缩进不一致 | 低优先级记录，可忽略 |
| 新增未知键 | 生产环境出现未在 Git 注册的变量 | **高危告警**，需人工审核 |

#### 1.3 Docker 环境自主诊断

对容器化环境进行全方位健康检查：

**容器健康检查矩阵**：

```bash
# === 容器基础状态 ===
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Size}}"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# === 容器日志异常检测（最近100行中的 ERROR/WARN）===
docker logs --tail 100 <container_name> 2>&1 | grep -iE "(ERROR|WARN|FATAL|PANIC)" | tail -20

# === 网络连通性诊断 ===
# 容器间网络测试
docker exec <container_a> ping -c 3 <container_b_hostname>
docker exec <container_a> curl -sS -o /dev/null -w "%{http_code}" http://<service_name>:<port>/health

# === 卷挂载验证 ===
docker inspect --format='{{range .Mounts}}{{.Source}} -> {{.Destination}} ({{.Type}}){{"\n"}}{{end}}' <container_name>

# === DNS 解析测试 ===
docker exec <container_name> nslookup kubernetes.default.svc.cluster.local
docker exec <container_name> getent hosts postgres.service
```

**自愈触发条件表**：

| 异常场景 | 检测指标阈值 | 自主动作 | 需要审批 |
|---------|-------------|---------|---------|
| 容器 OOMKilled | restart count > 3 in 5min | 重启容器 + 调整 memory limit | 否（若在安全范围内） |
| 端口冲突 | bind: address already in use | 停止冲突进程，重启目标容器 | 是 |
| 卷挂载失败 | Mounts 列表中 RW 变为 RO 或 missing | 重建卷并重新挂载 | 否 |
| 容器持续 CrashLoop | status=Restarting > 10次 | 导出日志 + 创建 Issue + 尝试回滚到上一版镜像 | 是 |
| 网络不通 | ping/curl 超时 > 5s | 检查 network mode 和 DNS 配置，尝试重新连接网络 | 否 |

#### 1.4 .env 文件安全管理

**敏感值处理规范**：

```bash
# === 敏感值加密存储（AES-256-GCM） ===
# 加密单个值
echo -n "my_secret_value" | openssl enc -aes-256-gcm -pbkdf2 -pass pass:<master_key> -base64

# 批量加密 .env 文件中标记为 SENSITIVE 的行
while IFS= read -r line; do
    if [[ "$line" =~ ^SENSITIVE_ ]]; then
        key=$(echo "$line" | cut -d'=' -f1)
        value=$(echo "$line" | cut -d'=' -f2-)
        encrypted=$(echo -n "$value" | openssl enc -aes-256-gcm -pbkdf2 -pass pass:${MASTER_KEY} -base64)
        echo "${key}=ENC(${encrypted})"
    else
        echo "$line"
    fi
done < .env.raw > .env.encrypted

# === 敏感值轮换策略 ===
# 轮换周期建议：
# - 数据库密码：90天
# - API Key / Token：30天（若提供商支持轮换）
# - JWT Secret：180天
# - 加密主密钥（Master Key）：每年 + 泄露时立即
```

**.env 文件安全清单**：

- [ ] `.env` 已加入 `.gitignore`
- [ ] 生产环境 `.env` 通过密钥管理系统（Vault/AWS Secrets Manager/K8s Secrets）注入
- [ ] 敏感值使用 `ENC()` 包装标识为加密态
- [ ] `.env.example` 仅包含占位值，不含真实凭据
- [ ] 定期执行 `git log -p -- .env*` 确认无历史泄露

### 阶段二：决策（Decide）

#### 2.1 决策树：是否执行自主修复

```
START
  │
  ├─ 检测到配置差异？
  │   │
  │   ├─ YES → 差异涉及安全敏感项（DB_PASSWORD, API_KEY, SECRET_*）？
  │   │   │
  │   │   ├─ YES → 【阻断】创建高优工单，通知安全团队，不自动修复
  │   │   │
  │   │   └─ NO → 差异属于预定义的自愈规则集？
  │   │       │
  │   │       ├─ YES → 【批准】按规则执行修复
  │   │       │
  │   │       └─ NO → 【人工审核】生成修复方案，等待审批
  │   │
  │   └─ NO → 环境正常，记录检测结果
  │
  └─ END
```

#### 2.2 风险评估矩阵

| 影响范围 | 修复复杂度 | 回滚难度 | 决策结果 |
|---------|-----------|---------|---------|
| 单服务/单实例 | 低（改配置即可） | 低（改回去即可） | ✅ 自主执行 |
| 单服务/多实例 | 中（需滚动更新） | 中（需逐个回滚） | ⚠️ 有条件执行（维护窗口内） |
| 多服务联动 | 高（需协调顺序） | 高（依赖关系复杂） | ❌ 必须人工审批 |
| 基础设施层 | 极高（网络/DNS/存储） | 极高 | ❌ 禁止自主操作 |

### 阶段三：执行（Execute）

#### 3.1 配置同步执行脚本

```bash
#!/bin/bash
# autonomous_config_sync.sh — 环境配置司自主同步工具
set -euo pipefail

SOURCE_ENV="${1:-staging}"
TARGET_ENV="${2:-prod}"
CONFIG_FILE="${3:-application.yml}"
BACKUP_DIR="/var/backups/config-drift/$(date +%Y%m%d_%H%M%S)"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# Step 1: 备份目标环境当前配置
log "[EXEC] 备份 ${TARGET_ENV} 当前配置..."
mkdir -p "${BACKUP_DIR}"
cp "/config/${TARGET_ENV}/${CONFIG_FILE}" "${BACKUP_DIR}/"

# Step 2: 从源环境拉取基准配置
log "[EXEC] 从 ${SOURCE_ENV} 同步配置基准..."
cp "/config/${SOURCE_ENV}/${CONFIG_FILE}" "/config/${TARGET_ENV}/${CONFIG_FILE}.pending"

# Step 3: 应用环境特定覆盖（如 DB_HOST 不同）
log "[EXEC] 应用 ${TARGET_ENV} 特定覆盖..."
apply_env_overrides "${TARGET_ENV}" "/config/${TARGET_ENV}/${CONFIG_FILE}.pending"

# Step 4: 校验配置语法
log "[EXEC] 校验配置文件语法..."
validate_config_syntax "/config/${TARGET_ENV}/${CONFIG_FILE}.pending"

# Step 5: 原子替换
log "[EXEC] 原子替换配置文件..."
mv "/config/${TARGET_ENV}/${CONFIG_FILE}.pending" "/config/${TARGET_ENV}/${CONFIG_FILE}"

# Step 6: 触发服务热重载（如果支持）
if command -v systemctl &>/dev/null; then
    log "[EXEC] 触发服务重载..."
    systemctl reload app-service || true
fi

log "[EXEC] 配置同步完成。备份位于: ${BACKUP_DIR}"
```

#### 3.2 Feature Flag 灰度发布引擎

```python
import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class RolloutPhase(Enum):
    INTERNAL = "internal_test"     # 内部测试 5%
    CANARY = "canary_release"      # 金丝雀 20%
    BETA = "beta_users"           # Beta 用户 50%
    GA = "general_availability"   # 全量 100%

@dataclass
class FeatureFlag:
    name: str
    enabled: bool
    rollout_percentage: int
    current_phase: RolloutPhase
    target_hash_prefixes: list[str]

def compute_user_flag_group(user_id: str, feature_name: str) -> bool:
    """
    基于 MD5 哈希的用户分组算法：
    对 user_id + feature_name 做 MD5，取前2位十六进制值(0x00-0xFF)，
    映射到 0-255 的空间，与 rollout_percentage * 255 / 100 比较。
    """
    raw = hashlib.md5(f"{user_id}:{feature_name}".encode()).hexdigest()
    hash_value = int(raw[:2], 16)  # 0-255
    threshold = int(rollout_percentage * 255 / 100)
    return hash_value < threshold

def progressive_rollout(flag: FeatureFlag, phase: RolloutPhase) -> dict:
    """
    渐进式 rollout 计划：
    internal_test (5%) → canary (20%) → beta (50%) → ga (100%)
    每阶段至少观察 24h 无异常方可推进。
    """
    phase_map = {
        RolloutPhase.INTERNAL: 5,
        RolloutPhase.CANARY: 20,
        RolloutPhase.BETA: 50,
        RolloutPhase.GA: 100,
    }
    flag.rollout_percentage = phase_map[phase]
    flag.current_phase = phase
    return {
        "flag": flag.name,
        "new_percentage": flag.rollout_percentage,
        "phase": phase.value,
        "action": f"rollout_to_{phase.value}",
        "observation_period_hours": 24 if phase != RolloutPhase.GA else 0
    }

# 使用示例
flag = FeatureFlag(
    name="new_checkout_flow",
    enabled=True,
    rollout_percentage=5,
    current_phase=RolloutPhase.INTERNAL,
    target_hash_prefixes=[]
)

# 推进到金丝雀阶段
result = progressive_rollout(flag, RolloutPhase.CANARY)
print(result)
# 输出: {'flag': 'new_checkout_flow', 'new_percentage': 20, ...}
```

#### 3.3 常见环境问题自愈脚本库

| 问题类型 | 自愈脚本 | 触发条件 | 操作内容 |
|---------|---------|---------|---------|
| 磁盘空间不足 | `auto_disk_cleanup.sh` | 使用率 > 85% | 清理日志/临时文件/docker unused |
| 内存泄漏趋势 | `auto_memory_restart.sh` | RSS 持续增长 > 2h | 滚动重启 Pod |
| DNS 解析失败 | `auto_dns_fix.sh` | resolve 失败率 > 30% | 刷新 CoreDNS 缓存 + 检查 Service |
| 端口耗尽 | `auto_port_recycle.sh` | TIME_WAIT > 50000 | 调整 tcp_tw_reuse 参数 |
| 配置文件损坏 | `auto_config_restore.sh` | YAML parse error | 从备份恢复最近有效版本 |

### 阶段四：验证（Verify）

#### 4.1 修复后验证 Checklist

```bash
#!/bin/bash
# post_remediation_verify.sh — 自主修复后验证脚本

verify_config_applied() {
    local env=$1 key=$2 expected=$3
    local actual=$(grep "^${key}=" /config/${env}/application.yml | cut -d'=' -f2-)
    if [[ "$actual" == "$expected" ]]; then
        echo "✅ PASS: ${key} = ${actual}"
        return 0
    else
        echo "❌ FAIL: ${key} expected='${expected}' actual='${actual}'"
        return 1
    fi
}

verify_service_health() {
    local endpoint=$1
    local code=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 10 "$endpoint")
    if [[ "$code" =~ ^2[0-9][0-9]$ ]]; then
        echo "✅ PASS: ${endpoint} → HTTP ${code}"
        return 0
    else
        echo "❌ FAIL: ${endpoint} → HTTP ${code}"
        return 1
    fi
}

verify_docker_container() {
    local container=$1
    local status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null)
    if [[ "$status" == "running" ]]; then
        echo "✅ PASS: Container '${container}' is running"
        return 0
    else
        echo "❌ FAIL: Container '${container}' status=${status}"
        return 1
    fi
}

# 主验证流程
PASS_COUNT=0; FAIL_COUNT=0
for check in \
    "verify_config_applied prod DATABASE_URL jdbc:postgresql://prod-db:5432/app" \
    "verify_service_health http://localhost:8080/api/health" \
    "verify_docker_container app-backend"; do
    if eval "$check"; then ((PASS_COUNT++)); else ((FAIL_COUNT++)); fi
done

echo ""
echo "========================================="
echo "验证结果: ${PASS_COUNT} PASS / ${FAIL_COUNT} FAIL"
if [[ $FAIL_COUNT -gt 0 ]]; then
    echo "⚠️ 存在验证失败项，已触发回滚准备"
    exit 1
else
    echo "🎉 所有验证通过，修复生效确认"
    exit 0
fi
```

#### 4.2 回滚机制

当验证失败时，自动执行回滚：

```bash
#!/bin/bash
# auto_rollback.sh — 验证失败时的自动回滚
BACKUP_DIR="$1"
TARGET_ENV="$2"
CONFIG_FILE="$3"

if [[ -f "${BACKUP_DIR}/${CONFIG_FILE}" ]]; then
    cp "${BACKUP_DIR}/${CONFIG_FILE}" "/config/${TARGET_ENV}/${CONFIG_FILE}"
    systemctl reload app-service || true
    echo "[ROLLBACK] 已从备份回滚配置: ${BACKUP_DIR}"
else
    echo "[ROLLBACK] ⚠️ 备份文件不存在，无法自动回滚！需人工介入"
    exit 1
fi
```

### 阶段五：记录（Record）

#### 5.1 审计日志格式

每次自主操作必须输出结构化审计记录：

```json
{
  "event_id": "evt_20260406_001",
  "timestamp": "2026-04-06T10:30:00Z",
  "si_department": "environment_config_si",
  "operation_type": "config_drift_remediation",
  "trigger_mode": "autonomous_scheduled",
  "source_environment": "staging",
  "target_environment": "prod",
  "drift_detected": [
    {"key": "APP_LOG_LEVEL", "expected": "INFO", "actual": "DEBUG", "severity": "MEDIUM"}
  ],
  "action_taken": "sync_config_value",
  "decision_rationale": "non_security_key_within_auto_fix_ruleset",
  "verification_result": "PASS",
  "rollback_status": "not_needed",
  "operator": "AUTONOMOUS_AGENT",
  "approval_required": false,
  "approval_id": null
}
```

#### 5.2 运营仪表盘指标

| 指标名称 | 计算方式 | 告警阈值 |
|---------|---------|---------|
| 配置漂移检出率 | 漂移事件数 / 总扫描次数 | < 95% 时告警 |
| 自愈成功率 | 成功修复数 / 总修复尝试数 | < 90% 时告警 |
| 平均修复时间(MTTR) | 从检测到验证通过的平均时长 | > 15min 告警 |
| 误报率 | 误判为漂移的事件 / 总漂移告警 | > 5% 告警 |
| 回滚次数 | 验证失败触发回滚的次数 | > 3次/天 告警 |

## 典型自主场景

### 场景1：生产环境配置漂移检测与自愈

**背景**：某次运维人员紧急调整了生产环境的日志级别（DEBUG），但忘记同步回 Git 仓库。

**自主处理流程**：

1. **感知**：定时任务每 15 分钟执行一次配置漂移扫描
2. **发现**：`APP_LOG_LEVEL` 在 prod 为 `DEBUG`，Git 基准值为 `INFO`
3. **决策**：该键不在安全敏感列表中，且属于预定义自愈规则集 → **批准修复**
4. **执行**：从 staging 基准同步值，备份当前值，原子替换
5. **验证**：调用 `/api/health` 确认服务正常，检查日志输出确认为 INFO 级别
6. **记录**：写入审计日志，发送摘要通知给运维团队

**关键产出**：
- 漂移报告 JSON
- 修复前后 diff
- 服务健康验证结果
- 审计追踪 ID

### 场景2：Feature Flag 渐进式灰度发布

**背景**：新支付网关接口需要逐步开放给用户群体，要求零宕机、可即时回退。

**自主处理流程**：

1. **初始化**：创建 Flag `payment_gateway_v2`，初始 rollout=5%（内部测试组）
2. **监控期**（24h）：收集错误率、延迟 P99、转化率指标
3. **推进判定**：错误率 < 0.1%，延迟无明显退化 → 推进到 Canary（20%）
4. **Canary 监控**（24h）：继续采集指标
5. **推进到 Beta**（50%）：扩大用户群
6. **全量发布**（GA 100%）：移除 Flag 分支逻辑，清理代码

**回退条件**（任一触发即暂停推进并回退到上一阶段）：
- 错误率 > 0.5%
- P99 延迟增加 > 200ms
- 用户投诉量突增 > 300%
- 支付成功率下降 > 2%

### 场景3：Docker 容器 OOM 自动恢复

**背景**：后端服务因内存泄漏导致容器频繁 OOMKilled。

**自主处理流程**：

1. **感知**：Kubernetes Event Watcher 检测到 OOMKilled 事件
2. **分析**：检查容器内存使用趋势图，确认 RSS 持续增长模式
3. **决策**：属于预定义自愈场景（内存泄漏类）→ **批准执行**
4. **执行**：
   - 导出容器 dmesg 和 jstack（如有 JVM）
   - 执行滚动重启（rolling restart），逐个 Pod 替换
   - 临时将 memory limit 上调 20% 作为缓冲
5. **验证**：所有 Pod Running 且 Ready，内存使用稳定
6. **记录**：生成内存泄漏分析报告，创建技术债务工单

### 场景4：.env 敏感值泄露应急响应

**背景**：Git 历史中发现某次提交意外包含了真实的数据库密码。

**自主处理流程**：

1. **感知**：定期 git log 扫描检测到 `.env` 文件曾出现在 commit 中
2. **决策**：**安全敏感事件 → 阻断自动修复，立即告警**
3. **执行**：
   - 立即轮换受影响的数据库密码
   - 使用 `git filter-repo` 或 BFG 清除历史中的敏感数据
   - 强制推送 clean 历史（需审批）
   - 通知所有相关服务使用新密码
4. **验证**：确认旧密码失效，新密码生效
5. **记录**：安全事件完整报告，包含时间线、影响范围、处置措施

## 决策框架

### 权限矩阵

| 操作类别 | 自主执行 | 需审批 | 禁止 |
|---------|---------|--------|------|
| 读取配置 | ✅ | - | - |
| 配置值同步（非敏感） | ✅ | - | - |
| 配置值同步（敏感） | - | ✅ | - |
| Feature Flag 推进 | ✅（≤50%） | ✅（>50%） | - |
| 容器重启 | ✅ | - | - |
| 容器删除/重建 | - | ✅ | - |
| 密钥轮换 | - | ✅ | - |
| 网络策略变更 | - | - | ❌ |
| 存储卷操作 | - | ✅ | - |
| 生产环境新建资源 | - | ✅ | - |

### 风险评分模型

```
Risk Score = Impact × Probability × Velocity

Impact (影响):
  1 = 仅开发环境影响
  2 = 影响非关键功能
  3 = 影响核心业务功能
  4 = 影响全部用户
  5 = 数据丢失/安全漏洞

Probability (概率):
  1 = < 1%（极低）
  2 = 1-10%（低）
  3 = 10-50%（中）
  4 = 50-80%（高）
  5 = > 80%（极高）

Velocity (速度):
  1 = 可立即回滚
  2 = 回滚需 < 5min
  3 = 回滚需 < 30min
  4 = 回滚需 < 2h
  5 = 无法回滚或回滚代价极大

判定：
  Score ≤ 8   → 自主执行
  Score 9-20  → 有条件执行（低风险时段）
  Score 21-35 → 必须人工审批
  Score > 35  → 禁止操作，升级处理
```

## 安全与治理

### 敏感配置分类

| 分类 | 示例 | 存储方式 | 访问控制 |
|------|------|---------|---------|
| 🔴 绝密 | DB_PASSWORD, PRIVATE_KEY, JWT_SECRET | HashiCorp Vault / AWS SM | 仅授权服务账户 |
| 🟠 机密 | API_KEY_THIRD_PARTY, STRIPE_SECRET | K8s Secrets (加密) | 团队级 RBAC |
| 🟡 内部 | INTERNAL_SERVICE_TOKEN, CACHE_KEY | .env (ENC包装) | 项目成员可读 |
| 🟢 公开 | LOG_LEVEL, FEATURE_FLAGS, PORT | ConfigMap / 明文 .env | 所有人可读 |

### 合规要求

- **SOC2**：所有配置变更必须有审计轨迹，保留期 ≥ 12 个月
- **GDPR**：含 PII 的配置字段需特殊标注，访问需记录目的
- **等保三级**：生产环境配置变更需双人复核（4-eyes principle）
- **CIS Benchmark**：定期执行 Docker/K8s 安全基线扫描

### 变更冻结期规则

以下时间段禁止自主配置变更（除非 P0 紧急修复）：
- 每周五 18:00 - 周一 09:00
- 大促/活动前 72 小时
- 财务月结期间（每月最后 3 个工作日）

## 协作关系

### 向上汇报（户部）

| 报送内容 | 频率 | 格式 |
|---------|------|------|
| 环境健康日报 | 每日 | Markdown 摘要 |
| 配置漂移周报 | 每周 | JSON + 分析图表 |
| 月度 MTTR 趋势 | 每月 | Dashboard 截图 + 文字说明 |
| 安全事件报告 | 即时 | 完整事件报告 |

### 平级协作

| 协作对象 | 协作内容 | 接口协议 |
|---------|---------|---------|
| **依赖管理司** | 配置中的依赖版本号一致性校验 | 共享 dependency-lock 文件 |
| **资源优化司** | 配置变更后的资源使用影响评估 | 提供 before/after metrics |
| **基础设施司** | CI/CD 流水线中的环境配置注入环节 | Pipeline 变量 + ConfigMap 模板 |

### 下游消费者

- 开发团队：通过 AOG 获取环境最佳实践
- 运维团队：接收自主操作的审计通知
- 安全团队：接收敏感配置相关的告警和报告

---

## 🤝 v5.1 增强：Agency Agent 协作指南

### 可调用的 Agency Agents

| Agent 名称 | 所属部门 | 协作模式 | 适用场景 |
|-----------|---------|---------|---------|
| **DevOps Automator** | Agency Engineering | IaC 自动化执行 | 承接度支司的配置同步和漂移修复决策，在多环境中执行实际的 IaC 应用、容器编排和配置注入操作 |
| **Embedded Firmware Engineer** | Agency Hardware | 嵌入式/边缘环境管理 | 为度支司提供边缘计算节点和嵌入式设备的环境配置能力扩展，将环境管理范围从云原生延伸至边缘侧 |

### Agent 协作工作流

1. **配置基线生成**: 度支司完成多环境差异扫描和漂移检测 → 输出标准化配置基线（YAML/Terraform）→ DevOps Automator 在各目标环境执行 apply
2. **CI 环境一致性保障**: 度支司定义 dev/staging/prod 三套环境的 ConfigMap 模板 → DevOps Automator 在 CI Pipeline 中自动注入正确环境的配置 → Embedded Firmware Engineer 确保边缘节点的配置与云端一致
3. **漂移自愈闭环**: 度支司检测到配置漂移 → 判定是否在自愈规则集内 → 若是，DevOps Automator 执行自动修复（备份→同步→验证→回滚）→ 若涉及安全项则阻断并告警
4. **Feature Flag 联动**: 度支司推进 Feature Flag 灰度阶段 → DevOps Automator 更新各环境的 Flag 配置 → Embedded Firmware Engineer 同步更新边缘设备的本地 Flag 缓存
5. **跨环境审计**: 定期由 DevOps Automator 执行全量环境快照对比 → 度支司分析差异报告 → 生成合规审计材料
6. **边缘-云端协同**: Embedded Firmware Engineer 上报边缘设备配置状态 → 度支司纳入全局配置拓扑视图 → 发现边缘特有配置问题时远程下发修复指令

### 典型协作场景

- **场景一 - 三环境配置一键同步**: 度支司检测到 staging 与 prod 之间存在 3 处非预期配置偏差 → 生成标准化的 sync 方案 → DevOps Automator 在 3 个环境依次执行：备份当前配置 → 从 Git 基线拉取正确值 → 原子替换 → 触发服务热重载 → 运行健康检查 → 全部 PASS
- **场景二 - CI 环境零漂移**: 每次 CI 构建时，度支司的漂移检测作为 Gate 步骤嵌入 Pipeline → DevOps Automator 确保 CI 容器内的环境变量与 ConfigMap 完全匹配 → 防止"本地能跑但CI挂"的环境不一致问题
- **场景三 - 边缘设备批量配置更新**: 500 台边缘设备需要统一更新 API Endpoint 配置 → 度支司生成增量配置 Patch → Embedded Firmware Engineer 通过 OTA 通道批量下发 → 逐设备上报确认 → 度支司汇总成功率并标记异常设备重试

---

## 🏗️ v5.1 增强：Harness 工程实践

### 相关 Harness 模块

- **Harness Infrastructure as Code (IaCM)**: 将度支司的多环境配置管理直接对接 Harness 的 IaC 管理模块，实现 Terraform/OpenTofu 配置的 Plan→Apply→Drift Detection 全流程自动化
- **Harness Environment (Service/Override)**: 利用 Harness 的 Environment + Service Override 机制，实现度支司的 dev/staging/prod 环境配置模板化管理和差异化覆盖

### 实践指南

1. **IaC Drift Detection 集成**: 将度支司的自定义漂移检测脚本注册为 Harness IaCM 的自定义 Drift Detector，每次 PR 或定时任务触发时自动运行，漂移结果直接关联到对应的 Harness Pipeline Run
2. **Environment Override 模式化**: 将度支司的三套环境配置抽象为 Harness Environment 的 `config.yaml` Override 文件，基础配置在 Service 层定义，环境差异在 Environment 层覆盖，实现"一次定义，多环境生效"

---

## 🆕 v6.0 增强能力集成

### MARC资源协调器集成指南

本司在多Agent并发场景下的资源协调要求：

#### 资源锁机制
- **文件写锁**：当本司需要修改环境配置文件、ConfigMap、Secret、Feature Flag配置时，必须通过MARC申请互斥锁
  ```python
  # 示例：申请文件写锁
  from skillscripts.resource_coordinator import LockManager, LockType
  lock_mgr = LockManager()
  lock_id = lock_mgr.acquire_lock(
      resource_id="path/to/config.yaml",
      agent_id="环境配置司",
      lock_type=LockType.EXCLUSIVE,
      priority=8,
      timeout=120.0
  )
  ```
- **读锁**：读取环境变量、配置基线、Feature Flag状态时申请读锁
- **释放锁**：配置同步和修复操作完成后立即释放锁，避免阻塞其他司的环境查询

#### 终端会话池使用
- 从MARC终端会话池获取会话执行配置同步脚本和环境诊断命令
- 会话使用完毕后及时归还池中
- 单个命令超时设置为300秒（配置漂移检测可能涉及多环境对比）

#### 并发安全注意事项
- 多环境配置同步时需锁定目标环境的全部配置文件，保证一致性
- Feature Flag变更需原子性操作，避免用户看到中间状态
- 死锁预防：按固定顺序申请锁（先锁dev环境→再锁staging环境→最后锁prod环境）

### 四维度输出防线集成

| 防线层级 | 本司检查重点 | 自动化程度 |
|---------|-------------|----------|
| **提示词工程层** | 配置差异分析提示词、漂移检测提示词、Feature Flag策略提示词 | 半自动（AI辅助） |
| **能力约束层** | 仅允许环境配置操作（配置同步/漂移修复/Flag管理），禁止修改业务代码 | 全自动 |
| **规则校验层** | 输出格式：YAML环境配置、JSON漂移报告、Markdown Feature Flag状态表 | 全自动 |
| **兜底恢复层** | 配置同步失败时自动从备份回滚并触发告警 | 半自动 |

### 操作优先级指引（v6.0核心）

本司推荐的操作方式：

1. 🥇 **Agent自主手动操作**（强烈推荐用于配置同步、漂移修复、Feature Flag管理）
   - 示例：直接编辑环境配置YAML、手动调整Feature Flag百分比、编写自愈脚本
   - 优势：精确控制配置粒度、可逐步验证配置效果、可随时回滚配置变更

2. 🥈 **规划脚本操作**（适用于批量环境初始化、定期漂移扫描）
   - 推荐脚本：
     - `skillscripts/resource_coordinator/quota_manager.py` — 检查环境资源配置配额
     - `skillscripts/open_source_philosophy/clawcode_sdd_tdd_engine.py` — SDD/TDD驱动的环境治理
     - `skillscripts/platform/powershell_adapter.py` — PS7环境适配

3. 🥉 **命令操作**（仅限紧急配置回滚、容器重启等极少数场景）
   - ⚠️ 必须预演影响范围（生产环境配置变更影响全局服务）
   - ⚠️ 生产环境配置操作需逐条确认并留痕
   - 推荐使用PS7适配器转换docker/kubectl命令

### PowerShell 7 执行指南

本司相关操作的PS7适配要点：
- 文件操作：使用原生PowerShell Cmdlet处理.env/YAML/JSON配置文件
- Docker操作：docker命令用于容器诊断、日志查看和网络检查
- K8s操作：kubectl命令用于ConfigMap/Secret管理和Pod诊断
- 编码：确保所有输出 UTF-8 无 BOM（配置文件和审计日志）

### 与其他司的协作接口

- 上游依赖：基础设施司（接收CI/CD环境注入需求）、依赖管理司（获取依赖版本约束）
- 下游输出：资源优化司（推送配置变更后的资源影响）、协同调度司（报告环境状态）
- 数据交换格式：YAML / JSON / Markdown（统一UTF-8无BOM）

---

## 🔑 环境变量标准化管理（v6.1 新增）

### 核心工具：SecretsManager + EnvTemplateGenerator

**模块路径**:
- `skillscripts/secrets_manager/secrets_manager.py`
- `skillscripts/secrets_manager/env_template_generator.py`

### .env 文件规范

#### 文件命名约定

| 文件名 | 用途 | 是否提交 Git |
|--------|------|-------------|
| `.env.example` | 模板文件（含占位符） | ✅ 提交 |
| `.env.development` | 开发环境变量 | ❌ 不提交 |
| `.env.staging` | 预发布环境变量 | ❌ 不提交 |
| `.env.production` | 生产环境变量 | ❌ 不提交 |
| `.env.local` | 本地个人覆盖 | ❌ 不提交 |

#### .env 文件格式规范

```bash
# ===========================================
# Universal DevOps 环境变量配置
# Environment: development
# Generated: 2026-04-06 by EnvTemplateGenerator
# ===========================================

# --- 数据库配置 ---
DATABASE_URL=postgresql://localhost:5432/myapp_dev
DATABASE_POOL_SIZE=10

# --- API 密钥 ---
# ⚠️ Critical: 请从安全渠道获取真实密钥
API_SECRET_KEY=********
JWT_SECRET_KEY=********

# --- 应用设置 ---
DEBUG=true
LOG_LEVEL=debug
```

#### 环境变量命名规范

| 类型 | 命名模式 | 示例 |
|------|---------|------|
| 数据库 | `{DB_TYPE}_{PARAM}` | DATABASE_URL, REDIS_HOST |
| API 密钥 | `{SERVICE}_SECRET_KEY` | GITHUB_SECRET_KEY, STRIPE_API_KEY |
| 特性开关 | `FEATURE_{NAME}_ENABLED` | FEATURE_DARK_MODE_ENABLED |
| 外部服务 | `{SERVICE}_{PARAM}` | AWS_REGION, SENTRY_DSN |
| 路径配置 | `{COMPONENT}_{TYPE}_PATH` | LOG_FILE_PATH, CACHE_DIR_PATH |

### SecretsManager 集成指南

#### 初始化（应用启动时）

```python
from pathlib import Path
from skillscripts.secrets_manager import SecretsManager

def init_secrets():
    """应用启动时初始化密钥管理器"""
    sm = SecretsManager(env_file=Path(".env"))
    sm.load()
    
    # 验证必需密钥
    result = sm.validate_all()
    if not result.is_valid:
        for issue in result.issues:
            print(f"⚠️ 密钥问题: {issue}")
        if any(i.get("severity") == "critical" for i in result.issues):
            raise RuntimeError("存在关键密钥缺失，无法启动")
    
    return sm

sm = init_secrets()
```

#### 在项目中使用

```python
# 获取数据库连接串（必需，缺失则报错）
db_url = sm.get_required("DATABASE_URL", purpose="数据库主连接")

# 获取调试标志（可选，有默认值）
debug = sm.get("DEBUG", "false").lower() == "true"

# 获取 API 密钥（自动分类为 API_KEY 类型）
api_key = sm.get_required("GITHUB_API_KEY")
key_type = sm.classify(api_key)
print(f"密钥类型: {key_type}")  # -> SecretType.API_KEY

# 日志输出时自动脱敏
import logging
logger.info(f"连接数据库: {sm.mask_for_log(db_url)}")
# 输出: 连接数据库: postgresql://user:****@host:5432/db
```

### 自动化工作流

#### 生成/更新 .env.example

```bash
# 方式1: Python API
python -c "
from pathlib import Path
from skillscripts.secrets_manager.env_template_generator import EnvTemplateGenerator
gen = EnvTemplateGenerator()
vars = gen.scan_project(Path('.'))
content = gen.generate_example(vars)
Path('.env.example').write_text(content, encoding='utf-8')
print('✅ .env.example 已生成')
"

# 方式2: 命令行（如果有 CLI 入口）
python -m skillscripts.secrets_manager.env_template_generator --scan . --output .env.example
```

#### 检测缺失环境变量

```bash
python -c "
from pathlib import Path
from skillscripts.secrets_manager.env_template_generator import EnvTemplateGenerator
gen = EnvTemplateGenerator()
vars = gen.scan_project(Path('.'))
loaded = {'DATABASE_URL', 'DEBUG', 'LOG_LEVEL'}  # 当前已加载的变量集合
report = gen.detect_missing_vars(loaded, vars.required_set)
if not report.all_present:
    print('❌ 缺失必需变量:')
    for v in report.missing_vars:
        print(f'  - {v.name} ({v.source_file}:{v.source_line}')
else:
    print('✅ 所有必要量均已设置')
"
```

### 多环境配置管理

| 环境 | 配置文件 | 必填变量 | 特殊处理 |
|------|---------|---------|---------|
| development | .env.development | 基础变量 | 允许宽松默认值 |
| staging | .env.staging | 全部变量 | 模拟生产配置 |
| production | .env.production | 全部变量 | 禁止默认值，强制外部注入 |

### 环境变量变更流程

1. 开发者在代码中使用 `os.environ.get()` 或 `SecretsManager.get()` 引入新变量
2. 运行 EnvTemplateGenerator 更新 `.env.example`
3. 各环境负责人更新对应 `.env.*` 文件
4. 提交 `.env.example` 变更到版本控制
5. CI/CD 验证所有必需变量可加载
