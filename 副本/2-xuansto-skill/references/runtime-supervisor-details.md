# Runtime Supervisor 详细参考

## 记忆系统

- **短期记忆**: 当前运行状态、活跃告警、临时恢复操作
- **中期记忆**: 故障历史记录、恢复策略库、伸缩事件日志
- **长期记忆**: 故障模式库、恢复最佳实践、容量规划数据

## 协作关系

- **上游**: 接收 DevOps Engineer 的运维策略、Monitor Specialist 的监控数据
- **下游**: 为开发团队提供运行时洞察、为产品团队提供可用性报告
- **同级**: 与 CI/CD Specialist 协作部署验证、与 Security Auditor 协作安全响应

## Karpathy Guidelines 详细说明

### 1. Think Before Coding（编码前思考）
- 理解服务依赖和运行时状态再操作；若恢复策略有歧义，先提问
- 分析服务健康指标，确定最佳恢复路径
- 不假设服务状态，必须基于监控数据判断

### 2. Simplicity First（简洁优先）
- 不强加未要求的保护措施；按需配置恢复触发条件
- 不添加未要求的自动恢复、熔断或限流机制
- 用最简单的恢复策略实现高可用目标

### 3. Surgical Changes（外科手术式修改）
- 只修改目标服务的运行时配置；不顺手调整其他服务的恢复策略
- 运行时变更只影响目标服务，不扩散到无关服务
- 不顺手优化其他服务的扩缩容配置

### 4. Goal-Driven Execution（目标驱动执行）
- 定义恢复验证标准；服务恢复后必须通过健康检查和就绪检查
- 循环检查直到验证通过或触发升级流程
- 运行时管理目标必须有可用性、MTTR和恢复成功率指标

## Critical Rules 详细示例

### 禁止无限重试

```yaml
# ❌ 错误：无限制重试
recovery:
  action: restart
  retry: unlimited

# ✅ 正确：限制重试次数
recovery:
  action: restart
  max_retries: 3
  retry_interval: 30s
  backoff_multiplier: 2
  escalation:
    after: 3_retries
    action: notify_oncall
```

### 禁止忽略级联故障

```yaml
# ❌ 错误：独立恢复
recovery:
  services:
    - name: service-a
      independent: true
    - name: service-b
      independent: true

# ✅ 正确：考虑依赖关系
recovery:
  services:
    - name: database
      priority: 1
    - name: cache
      priority: 2
      depends_on: [database]
    - name: api
      priority: 3
      depends_on: [database, cache]
```

### 禁止无回滚的自动修复

```yaml
auto_fix:
  action: scale_out
  parameters:
    min_replicas: 2
    max_replicas: 10
  rollback:
    trigger:
      - error_rate > 10%
      - latency_p95 > 2000ms
    action: scale_in
    target: previous_replicas
```

### 禁止跳过健康检查直接恢复

```bash
# ❌ 错误：直接重启
kubectl rollout restart deployment/app

# ✅ 正确：先检查后恢复
if ! health_check; then
    diagnose_issue
    if can_auto_recover; then
        execute_recovery
        verify_recovery
    else
        notify_oncall
    fi
fi
```

## 健康检查配置示例

```yaml
# health-checks.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: health-check-config
data:
  checks:
    - name: api-health
      type: http
      endpoint: /health
      interval: 10s
      timeout: 5s
      retries: 3
      expected_status: 200
      expected_body:
        status: healthy
    - name: database-health
      type: tcp
      host: postgres-service
      port: 5432
      interval: 30s
      timeout: 5s
    - name: cache-health
      type: redis
      host: redis-service
      port: 6379
      command: PING
      expected_response: PONG
  dependencies:
    - service: api
      depends_on:
        - database
        - cache
      health_threshold: 2/3
```

## 自动恢复配置示例

```yaml
# auto-recovery.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: auto-recovery-config
data:
  recovery_policies:
    - name: service-restart
      triggers:
        - health_check_failed: true
          consecutive_failures: 3
        - error_rate: "> 10%"
          duration: 5m
      actions:
        - type: restart
          service: ${service_name}
          grace_period: 30s
        - type: notify
          channels: [slack, pagerduty]
          message: "服务 ${service_name} 自动重启"
      verification:
        health_check: true
        smoke_test: true
        timeout: 120s
      rollback:
        trigger:
          - recovery_failed: true
          - error_rate_after_recovery: "> 20%"
        action: notify_oncall
    - name: cascade-recovery
      triggers:
        - dependency_failed: true
      actions:
        - type: recover_dependency
          order: [database, cache, api]
        - type: verify_chain
          services: [database, cache, api]
```

## 弹性伸缩配置示例

```yaml
# scaling.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-scaler
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: app
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: 1000
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100
          periodSeconds: 15
        - type: Pods
          value: 4
          periodSeconds: 15
      selectPolicy: Max
```

## 故障恢复脚本

```bash
#!/bin/bash
# auto-recovery.sh

SERVICE_NAME=$1
MAX_RETRIES=3
RETRY_COUNT=0

diagnose() {
    local service=$1
    echo "=== 诊断服务: $service ==="
    echo "Pod状态:"
    kubectl get pods -l app=$service -o wide
    echo "最近事件:"
    kubectl get events --field-selector involvedObject.name=$service --sort-by='.lastTimestamp'
    echo "最近日志:"
    kubectl logs -l app=$service --tail=50
    echo "资源使用:"
    kubectl top pods -l app=$service
}

attempt_recovery() {
    local service=$1
    local attempt=$2
    echo "=== 恢复尝试 $attempt/$MAX_RETRIES: $service ==="
    case $attempt in
        1)
            echo "策略1: 重启Pod"
            kubectl rollout restart deployment/$service
            kubectl rollout status deployment/$service --timeout=120s
            ;;
        2)
            echo "策略2: 扩容"
            kubectl scale deployment/$service --replicas=$(kubectl get deployment $service -o jsonpath='{.spec.replicas}' | xargs -I {} echo $(({} + 2)))
            ;;
        3)
            echo "策略3: 回滚到上一版本"
            kubectl rollout undo deployment/$service
            kubectl rollout status deployment/$service --timeout=120s
            ;;
    esac
}

verify_recovery() {
    local service=$1
    echo "=== 验证恢复: $service ==="
    local health=$(kubectl exec -it deployment/$service -- curl -sf localhost:8080/health 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "✓ 健康检查通过"
    else
        echo "✗ 健康检查失败"
        return 1
    fi
    local ready=$(kubectl exec -it deployment/$service -- curl -sf localhost:8080/ready 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "✓ 就绪检查通过"
    else
        echo "✗ 就绪检查失败"
        return 1
    fi
    if ./scripts/smoke-test.sh $service; then
        echo "✓ 烟雾测试通过"
    else
        echo "✗ 烟雾测试失败"
        return 1
    fi
    return 0
}

notify_oncall() {
    local service=$1
    local message=$2
    curl -X POST $SLACK_WEBHOOK_URL \
        -H 'Content-Type: application/json' \
        -d "{\"text\": \"🚨 运行时告警: $service - $message\"}"
}

main() {
    diagnose $SERVICE_NAME
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        RETRY_COUNT=$((RETRY_COUNT + 1))
        attempt_recovery $SERVICE_NAME $RETRY_COUNT
        if verify_recovery $SERVICE_NAME; then
            echo "✓ 恢复成功"
            notify_oncall $SERVICE_NAME "自动恢复成功 (尝试 $RETRY_COUNT/$MAX_RETRIES)"
            exit 0
        fi
    done
    echo "✗ 自动恢复失败，需要人工介入"
    notify_oncall $SERVICE_NAME "自动恢复失败，需要人工介入"
    exit 1
}

main
```

## 工作流程图

### 运行时监控流程

```
1. 健康检查 → 定期执行健康探测 → 收集服务状态数据 → 更新服务状态表
2. 异常检测 → 分析健康检查结果 → 识别异常模式 → 触发告警通知
3. 自动恢复 → 诊断故障原因 → 执行恢复策略 → 验证恢复结果
4. 弹性伸缩 → 监控资源使用 → 评估伸缩需求 → 执行伸缩操作
5. 持续优化 → 分析恢复效率 → 优化恢复策略 → 更新配置参数
```

### 事故响应流程

```
1. 故障检测 → 健康检查失败 → 告警触发 → 创建事故工单
2. 初步评估 → 确认影响范围 → 判断严重级别 → 决定恢复策略
3. 自动恢复 → 执行预设恢复策略 → 监控恢复进度 → 验证服务状态
4. 人工介入（如需要）→ 通知值班人员 → 提供诊断信息 → 协助人工恢复
5. 事后复盘 → 编写事故报告 → 分析根因 → 优化恢复策略
```

## 任务执行模板

```markdown
## 任务: [服务名称]运行时管理配置

### 输入
- 服务名称: [服务名]
- 可用性目标: [SLA要求]
- 恢复策略: [策略描述]

### 执行步骤
1. [ ] 分析服务依赖
2. [ ] 配置健康检查
3. [ ] 配置自动恢复
4. [ ] 配置弹性伸缩
5. [ ] 编写恢复脚本
6. [ ] 测试验证
7. [ ] 文档输出

### 输出
- 健康检查: `health/[service].yaml`
- 恢复配置: `recovery/[service].yaml`
- 伸缩配置: `scaling/[service].yaml`
- 恢复脚本: `scripts/recovery-[service].sh`
```
