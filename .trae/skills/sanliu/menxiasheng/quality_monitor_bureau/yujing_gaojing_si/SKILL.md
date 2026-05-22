---
name: yujing_gaojing_si
description: 预警告警司，负责质量门禁告警、SLA违规通知、告警分级（🔴严重/🟠警告/🟡提醒/🟢正常）。
---

# 预警告警司技能指令

## 职责定义

预警告警司作为质量监控局的告警核心，承担以下职责：

| 职责类别 | 具体职责 | 关键产出 |
|----------|----------|----------|
| **门禁告警** | 质量门禁触发与通知 | 门禁告警消息 |
| **SLA监控** | 服务水平协议违规检测与告警 | SLA违规报告 |
| **告警分级** | 多级告警分类与优先级管理 | 分级告警记录 |
| **通知分发** | 多渠道告警推送与升级 | 通知日志 |

---

## 告警分级体系

```yaml
alert_classification_system:
  severity_levels:
    critical:
      emoji: "🔴"
      name: "严重 (Critical)"
      score: 4
      color: "#DC2626"
      bg_color: "#FEE2E2"
      definition: "立即影响生产环境或严重违反合规要求"
      response_sla: "15分钟内响应，1小时内初步处理"
      auto_actions:
        - "阻止合并/部署"
        - "发送所有频道通知"
        - "自动创建高优Issue"
        - "通知管理层"
      escalation_policy: "15分钟无响应 → 升级至技术负责人 + 管理层"
        
    warning:
      emoji: "🟠"
      name: "警告 (Warning)"
      score: 3
      color: "#EA580C"
      bg_color: "#FFF7ED"
      definition: "质量指标显著偏离目标，可能影响近期发布"
      response_sla: "4小时内响应，24小时内制定计划"
      auto_actions:
        - "标记PR需要关注"
        - "发送Slack/Teams通知"
        - "添加到待办事项列表"
      escalation_policy: "24小时无响应 → 升级至团队负责人"
      
    notice:
      emoji: "🟡"
      name: "提醒 (Notice)"
      score: 2
      color: "#EAB308"
      bg_color": "#FEFCE8"
      definition: "指标接近阈值或轻微偏离趋势"
      response_sla: "当前Sprint内评估"
      auto_actions:
        - "记录到仪表板"
        - "发送每日摘要邮件"
        - "添加到技术债务backlog"
      escalation_policy: "连续3次出现 → 升级为Warning"
      
    normal:
      emoji: "🟢"
      name: "正常 (Normal)"
      score: 1
      color: "#22C55E"
      bg_color: "#F0FDF4"
      definition: "所有指标在健康范围内"
      response_sla: "无需响应"
      auto_actions:
        - "更新健康状态仪表板"
        - "记录到历史日志"
      notification: "仅周报汇总"
```

---

## 工作流程

### 阶段一：告警规则配置与管理

```
系统初始化或规则更新
    ↓
[1] 定义告警规则集
    ↓
[2] 配置阈值与条件
    ↓
[3] 设置静默期与抑制规则
    ↓
[4] 配置通知渠道与接收人
    ↓
[5] 测试告警链路
    ↓
进入实时监控阶段
```

#### 告警规则配置模板

```yaml
alert_rules_configuration:
  rule_groups:
    
    quality_gate_rules:
      group_name: "质量门禁规则"
      enabled: true
      evaluation_trigger: "on_each_build_completion"
      
      rules:
        - id: "QG-001"
          name: "测试覆盖率低于门槛"
          metric: "test_coverage.line_coverage_percent"
          condition: "value < 80"  # 绝对阈值
          severity: "critical"
          message: "行覆盖率 {value}% 低于最低门槛80%，已阻止合并"
          runbook_link: "docs/runbooks/low_coverage.md"
          channels: ["slack_critical", "email_dev_team", "pr_comment"]
          
        - id: "QG-002"
          name: "安全扫描发现Critical漏洞"
          metric: "security.critical_vulnerability_count"
          condition: "value > 0"
          severity: "critical"
          message: "发现 {value} 个Critical级别安全漏洞！部署已阻断。"
          channels: ["slack_security", "pagerduty", "email_security_team"]
          requires_immediate_action: true
          
        - id: "QG-003"
          name: "代码重复率超标"
          metric: "code_quality.code_duplication_percent"
          condition: "value > 8"
          severity: "warning"
          message: "代码重复率达到 {value}%，超过警戒线8%"
          channels: ["slack_tech_debt", "pr_comment"]
          
        - id: "QG-004"
          name: "新引入技术债务过多"
          metric: "technical_debt.new_debt_this_sprint_hours"
          condition: "value > 40"  # Sprint新增>40小时债务
          severity: "notice"
          message: "本期新增技术债务 {value}h，建议关注"
          channels: ["daily_digest"]
          
    trend_anomaly_rules:
      group_name: "趋势异常规则"
      enabled: true
      evaluation_trigger: "daily_at_09:00"
      
      rules:
        - id: "TA-001"
          name: "覆盖率突然下降"
          metric: "test_coverage.line_coverage_percent"
          condition: "pct_change_7d < -5"  # 一周下降超过5%
          severity: "warning"
          message: "覆盖率一周内下降 {abs_change}%，请调查原因"
          lookback_period: "7 days"
          min_data_points: 5
          
        - id: "TA-002"
          name: "性能退化加速"
          metric: "performance.api_p95_response_time_ms"
          condition: "acceleration > 20 AND value > baseline * 1.3"
          severity: "warning"
          message: "API P95延迟恶化加速：当前 {value}ms，较基线恶化 {pct_increase}%"
          
        - id: "TA-003"
          name: "Bug产生率异常升高"
          metric: "quality.new_bugs_per_week"
          condition: "z_score > 2.5"
          severity: "notice"
          message: "本周新Bug数量 ({value}) 显著高于历史均值"
          
    sla_violation_rules:
      group_name: "SLA违规规则"
      enabled: true
      evaluation_trigger: "continuous_monitoring"
      
      rules:
        - id: "SLA-001"
          name: "API可用性低于SLA"
          metric: "availability.uptime_percent_30d"
          condition: "value < 99.9"  # SLA承诺99.9%
          severity: "critical"
          sla_reference: "SLA-2024-API-001"
          message: "30天可用性 {value}% 低于SLA承诺的99.9%！违约风险！"
          financial_impact: "可能触发服务等级赔偿条款"
          
        - id: "SLA-002"
          name: "P99响应时间超SLA"
          metric: "performance.api_p99_response_time_ms"
          condition: "value > 1000"  # SLA: P99 < 1秒
          severity: "warning"
          sla_reference: "SLA-2024-PERF-002"
          message: "P99响应时间 {value}ms 超过SLA上限(1000ms)"
          
        - id: "SLA-003"
          name: "安全漏洞修复超时"
          metric: "security.mean_time_to_fix_critical_days"
          condition: "value > 7"  # SLA: Critical漏洞7天内修复
          severity: "warning"
          message: "Critical漏洞平均修复时间 {value}天，超过7天SLA"
          
  global_settings:
    silence_rules:
      maintenance_window:
        enabled: true
        schedule: "Sunday 02:00-06:00 UTC"
        silenced_severities: ["notice"]
        auto_resume: true
        
      deployment_silence:
        trigger: "on_deployment_start"
        duration_minutes: 30
        silenced_rules: ["*availability*", "*error_rate_spike*"]
        reason: "部署期间预期短暂波动"
        
    deduplication:
      grouping_window_minutes: 30  # 相似告警30分钟内合并
      grouping_keys: ["rule_id", "affected_component"]
      max_group_size: 10
      
    rate_limiting:
      max_alerts_per_hour_per_rule: 10
      max_alerts_per_hour_total: 100
      burst_allowance: 5
```

---

### 阶段二：实时监控与告警触发

```
收到新的指标数据或事件
    ↓
[1] 规则引擎评估
    ↓
[2] 条件匹配检查
    ↓
[3] 严重级别判定
    ↓
[4] 静默/抑制检查
    ↓
[5] 去重与分组
    ↓
[6] 告警生成
    ↓
进入通知分发阶段
```

#### 告警生成格式

```json
{
  "alert_id": "ALERT-20240108-001",
  "timestamp": "2024-01-08T14:32:45Z",
  "generated_by": "yujing_gaojing_si",
  "rule_id": "QG-001",
  "rule_name": "测试覆盖率低于门槛",
  
  "severity": {
    "level": "critical",
    "emoji": "🔴",
    "score": 4,
    "color": "#DC2626"
  },
  
  "metric_context": {
    "metric_name": "test_coverage.line_coverage_percent",
    "current_value": 76.8,
    "unit": "%",
    "threshold": 80.0,
    "deviation": -3.2,
    "deviation_percent": -4.0,
    "previous_value": 82.5,
    "trend": "declining (-5.7 in 24h)",
    "evaluation_timestamp": "2024-01-08T14:30:00Z"
  },
  
  "build_context": {
    "trigger": "pull_request",
    "pr_number": 145,
    "branch": "feature/payment-gateway",
    "commit_hash": "xyz789abc012",
    "author": "developer@company.com",
    "ci_build_url": "https://ci.example.com/build/12345"
  },
  
  "message": {
    "title": "🔴 CRITICAL: 测试覆盖率低于门槛 - PR #145 已被阻止合并",
    "summary": "行覆盖率为 76.8%，低于质量门禁要求的 80%。本次变更导致覆盖率下降 5.7 个百分点。",
    "details": [
      "当前覆盖率: 76.8% (门槛: 80%)",
      "上次构建覆盖率: 82.5%",
      "变化量: -5.7% (显著下降)",
      "影响文件: src/payment/gateway.py (+350 lines, 未测试)",
      "未覆盖的新代码: 约280行"
    ],
    "impact_assessment": {
      "immediate": "PR无法合并至main分支",
      "quality_risk": "支付模块缺乏测试保护，存在回归风险",
      "compliance_risk": "不符合内部质量标准 (QP-001)"
    },
    "recommended_actions": [
      {
        "step": 1,
        "action": "审查 src/payment/gateway.py 的测试覆盖情况",
        "assignee": "PR作者",
        "deadline": "今日下班前"
      },
      {
        "step": 2,
        "action": "为核心支付逻辑添加单元测试（目标覆盖率恢复至80%+）",
        "assignee": "PR作者 + 测试团队支持",
        "deadline": "明日中午前"
      },
      {
        "step": 3,
        "action": "重新运行CI并验证覆盖率达标",
        "assignee": "PR作者",
        "deadline": "完成测试后"
      }
    ]
  },
  
  "runbook": {
    "link": "docs/runbooks/low_coverage.md",
    "quick_steps": [
      "1. 查看覆盖率报告: https://coverage.example.com/build/12345",
      "2. 定位未覆盖的函数和分支",
      "3. 编写针对性测试用例",
      "4. 运行 pytest --cov=src/payment --cov-report=term-missing",
      "5. 确保增量覆盖率 ≥ 80%"
    ]
  },
  
  "notification_plan": {
    "channels": [
      {
        "channel": "slack_critical",
        "status": "pending_send",
        "template": "slack_critical_template",
        "recipients": ["#engineering-alerts", "@backend-team-lead"]
      },
      {
        "channel": "pr_comment",
        "status": "pending_send",
        "target": "PR #145 comment",
        "auto_post": true
      },
      {
        "channel": "email",
        "status: "pending_send",
        "recipients": ["pr-author@company.com", "tech-lead@company.com"],
        "template": "email_critical_alert"
      }
    ],
    "escalation_schedule": [
      {
        "at": "2024-01-08T14:47:45Z",  // 15分钟后
        "if_no_response": "upgrade_to_pagerduty",
        "additional_recipients": ["cto@company.com"]
      },
      {
        "at": "2024-01-08T15:32:45Z",  // 1小时后
        "if_still_open": "escalate_to_management",
        "action": "Create incident and notify VP Engineering"
      }
    ]
  },
  
  "metadata": {
    "source_system": "quality_gate_engine",
    "correlation_id: "CORR-20240108-ABC123",
    "labels": ["quality_gate", "test_coverage", "blocking"],
    "silenced_until": null,
    "acknowledged_by": null,
    "acknowledged_at": null,
    "resolved": false,
    "resolved_at": null,
    "resolution_note": null
  }
}
```

---

### 阶段三：多渠道通知分发

```
告警生成完成
    ↓
[1] 渲染各渠道消息模板
    ↓
[2] 发送至配置的通知渠道
    ↓
[3] 确认送达
    ↓
[4] 记录通知日志
    ↓
[5] 监控响应状态
    ↓
[6] 必要时执行升级策略
    ↓
完成通知周期
```

#### 通知渠道配置

```yaml
notification_channels:
  slack:
    workspace: "company.slack.com"
    bot_token: "${SLACK_BOT_TOKEN}"
    
    channels:
      - name: "#engineering-alerts"
        purpose: "所有Critical和Warning级别告警"
        severity_filter: ["critical", "warning"]
        format: "rich_message_with_blocks"
        
      - name: "#quality-dashboard"
        purpose: "质量指标日常更新"
        severity_filter: ["normal", "notice"]
        format: "compact_summary"
        schedule: "daily at 09:00"
        
      - name: "#security-incidents"
        purpose: "安全相关告警"
        purpose_filter: ["category=security"]
        severity_filter: ["critical", "warning"]
        mention:["@security-team"]
        
    message_templates:
      critical: |
        🚨 *{alert_title}*
        
        *Severity:* 🔴 Critical
        *Metric:* {metric_name}: {current_value}{unit} (threshold: {threshold}{unit})
        *Triggered by:* {build_info}
        
        *Impact:* 
        {impact_summary}
        
        *Immediate Actions Required:*
        {recommended_actions}
        
        👉 <{ci_build_url}|View Build> | <{runbook_link}|Runbook> | <{alert_url}|Acknowledge>
        
      warning: |
        ⚠️ *{alert_title}*
        
        Metric `{metric_name}` is at {current_value}{unit}
        Threshold: {threshold}{unit}
        
        _{brief_description}_
        
        Suggested action: {primary_action}
        
  email:
    smtp_server: "smtp.company.com"
    from_address: "quality-alerts@company.com"
    
    templates:
      critical_subject: "🔴 [CRITICAL] {alert_title} - Immediate Action Required"
      warning_subject: "⚠️ [WARNING] {alert_title} - Attention Needed"
      daily_digest_subject: "📊 Daily Quality Digest - {date}"
      
    recipients_by_role:
      critical: ["on-call-engineer@company.com", "tech-lead@company.com", "engineering-manager@company.com"]
      warning: ["team-lead@company.com", "relevant-developers@company.com"]
      notice: ["tech-debt-tracker@company.com"]
      
  pagerduty:
    integration_key: "${PAGERDUTY_INTEGRATION_KEY}"
    
    routing_rules:
      - match: "severity=critical AND category=production_incident"
        service: "production-backend"
        urgency: "high"
        
      - match: "severity=critical AND category=security"
        service: "security-response"
        urgency: "high"
        
  github:
    token: "${GITHUB_TOKEN}"
    
    pr_comment_auto_post: true
    pr_comment_templates:
      blocking: |
        ## 🔴 Quality Gate Blocked
        
        This PR cannot be merged due to quality gate failure.
        
        ### Issue: {rule_name}
        - **Metric**: {metric_name}
        - **Current**: {current_value}{unit}
        - **Required**: {threshold}{unit}
        
        ### What to do:
        {action_steps}
        
        ### Resources:
        - [Coverage Report]({coverage_url})
        - [Run Book]({runbook_url})
        
        ---
        *Automated by 门下省·预警告警司*
        *Alert ID: {alert_id}* 
        
  webhook:
    endpoints:
      - url: "https://internal-tools.company.com/api/alerts/webhook"
        method: "POST"
        headers: {"Authorization": "Bearer ${WEBHOOK_TOKEN}"}
        payload_format: "standard_alert_json"
```

---

### 阶段四：告警生命周期管理

```
告警已发送
    ↓
[1] 等待确认(Acknowledge)
    ↓
[2] 跟踪处理进度
    ↓
[3] 监控升级条件
    ↓
[4] 记录解决结果
    ↓
[5] 生成事后报告
    ↓
[6] 更新规则（如需）
    ↓
告警生命周期结束
```

#### 告警状态机

```yaml
alert_lifecycle_state_machine:
  states:
    firing:
      description: "告警已触发，等待首次通知"
      transitions_to: ["pending_acknowledgment", "silenced", "resolved_auto"]
      
    pending_acknowledgment:
      description: "已通知，等待人工确认"
      timeout: "defined by severity SLA"
      transitions_to: ["acknowledged", "escalated", "resolved_auto"]
      
    acknowledged:
      description: "负责人已确认，正在处理中"
      transitions_to: ["in_progress", "escalated", "resolved_manual"]
      
    in_progress:
      description: "修复工作正在进行"
      transitions_to: ["resolved_manual", "reopened", "escalated"]
      
    escalated:
      description: "已升级至更高层级"
      level: 1, 2, 3...
      transitions_to: ["acknowledged_escalated", "resolved_manual"]
      
    resolved:
      description: "问题已解决"
      resolution_types: ["manual", "auto", "superseded"]
      transitions_to: ["closed", "reopened"]
      
    silenced:
      description: "已被静默（维护窗口等）"
      silence_expires_at: "timestamp"
      transitions_to: ["firing", "closed"]
      
    closed:
      description: "告警生命周期结束"
      final_state: true
      
  state_transition_audit_log:
    record_every_transition: true
    fields:
      - from_state
      - to_state
      - timestamp
      - actor (user or system)
      - note
      - duration_in_previous_state
```

---

## 告警仪表板展示

### 实时告警状态视图

```markdown
# 🚨 质量告警中心

**最后更新**: 2024-01-08 14:35:00 UTC  
**活跃告警**: 3 (🔴1 | 🟠1 | 🟡1)  
**今日已处理**: 12  

---

## 🔴 活跃的Critical告警 (1)

### ALERT-20240108-001: 测试覆盖率低于门槛
- **状态**: 🔥 Firing (等待确认, 已过 3 分钟)
- **指标**: 行覆盖率 = 76.8% (门槛: 80%)
- **来源**: PR #145 feature/payment-gateway
- **责任人**: @developer (未确认)
- **升级倒计时**: ⏱️ 12 分钟后升级至 PagerDuty
- **操作**: [确认] [查看详情] [静默1小时]

---

## 🟠 活跃的Warning告警 (1)

### ALERT-20240107-015: 技术债务持续增长
- **状态**: ⏳ Acknowledged (处理中, 已过 18 小时)
- **指标**: 技术债务比率 = 7.2% (上周: 6.5%)
- **趋势**: ↗ 持续上升
- **责任人**: @tech-lead (已确认)
- **计划**: Sprint 14 安排偿债专项
- **操作**: [更新进度] [升级]

---

## 🟡 活跃的Notice告警 (1)

### ALERT-20240108-003: 文档覆盖率略降
- **状态**: 📝 Pending
- **指标**: API文档覆盖率 = 87% (目标: 90%)
- **变化**: -2% vs 上周
- **建议**: 本Sprint补充新端点文档

---

## 📊 今日统计

| 级别 | 新增 | 已确认 | 处理中 | 已关闭 | 平均响应时间 |
|------|------|--------|--------|--------|--------------|
| 🔴 Critical | 2 | 1 | 1 | 0 | 8 分钟 |
| 🟠 Warning | 5 | 4 | 3 | 2 | 1.5 小时 |
| 🟡 Notice | 8 | 3 | 2 | 6 | 4 小时 |

## 📈 趋势 (近7天)

```
告警数量走势
15 ┤     ████
10 ┤   ██    ██    ██
 5 ┤ ██          ██       ██
 0 ┤└──────────────────────────→
    Mon  Tue  Wed  Thu  Fri  Sat  Sun
```
```

---

## 与MARC资源协调器的资源需求

```yaml
marc_resource_requirements:
  compute_resources:
    cpu_cores: 2
    memory_gb: 4
    
  execution_time:
    rule_evaluation: "< 500ms per metric batch"
    alert_generation: "< 200ms"
    notification_dispatch: "< 5 seconds (all channels)"
    
  reliability_requirements:
    availability: "99.9%"  # 告警系统本身必须高度可靠
    data_loss_tolerance: "zero (no alerts may be lost)"
    failover: "Active-passive with < 30s switchover"
    
  integration_points:
    upstream:
      - "zhibiao_caicji_si (metrics input)"
      - "qushi_fenxi_si (trend anomaly input)"
      - "menjin_baba_si (gate status input)"
      
    downstream:
      - "Slack API"
      - "Email SMTP"
      - "PagerDuty API"
      - "GitHub API"
      - "Internal webhook endpoints"
```

---

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-04-06 | 初始版本，包含完整的四级告警体系、多渠道通知、生命周期管理能力 |
