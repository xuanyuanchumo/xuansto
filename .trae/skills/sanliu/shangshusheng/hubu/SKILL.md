---
name: hubu
description: 户部，负责资源配置，包括预算管理、API 密钥、计算资源等。
---
# 户部技能指令

## 职责
- 资源配置：管理云服务器、数据库等计算资源
- 密钥管理：管理 API 密钥、访问凭证
- 预算管理：跟踪资源使用成本
- 测试环境管理：管理测试环境的生命周期和配置
- 资源调度策略：制定资源分配和回收策略

## 工作流程

```
1. 接收尚书省的资源配置指令
2. 分析资源需求类型和数量
3. 查询当前资源池状态
4. 制定资源配置方案
5. 记录配置决策推理过程
6. 执行资源分配
7. 监控资源使用状态
8. 处理资源异常和调整
9. 生成资源使用报告
10. 资源回收与优化
```

## 资源配置决策流程（增强版）

### 资源需求分析

```
资源需求分析步骤:
  1. 资源类型识别
     - 计算资源（CPU、内存、存储）
     - 网络资源（带宽、IP、域名）
     - API资源（密钥、配额、限流）
     - 人力资源（开发、测试、运维）
  
  2. 资源数量估算
     - 基准需求量
     - 峰值需求量
     - 冗余预留量
  
  3. 资源优先级排序
     - 关键资源：必须优先保障
     - 重要资源：需要充分保障
     - 一般资源：按需分配
  
  4. 资源约束分析
     - 预算约束
     - 时间约束
     - 技术约束
```

### 资源池状态评估

```json
{
  "resource_pool_assessment": {
    "assessment_id": "RPA-001",
    "timestamp": "2024-01-01T00:00:00Z",
    "compute_resources": {
      "cpu": {
        "total": 100,
        "used": 65,
        "available": 35,
        "utilization_rate": 0.65
      },
      "memory": {
        "total_gb": 512,
        "used_gb": 320,
        "available_gb": 192,
        "utilization_rate": 0.625
      },
      "storage": {
        "total_gb": 10000,
        "used_gb": 6000,
        "available_gb": 4000,
        "utilization_rate": 0.60
      }
    },
    "api_resources": {
      "openai": {
        "quota_limit": 1000000,
        "quota_used": 450000,
        "quota_available": 550000,
        "rate_limit": "60/minute",
        "current_rate": "25/minute"
      }
    },
    "human_resources": {
      "developers": {
        "total": 10,
        "available": 4,
        "utilization_rate": 0.60
      }
    },
    "summary": {
      "overall_utilization": 0.62,
      "bottleneck_resources": ["memory"],
      "recommendation": "内存资源紧张，建议扩容或优化"
    }
  }
}
```

---

## 协同效果评估能力

### 资源配置协同评估指标

户部作为资源配置机构，负责评估资源配置在三省六部协同中的效果。

| 评估维度 | 指标 | 目标值 | 度量方法 |
|----------|------|--------|----------|
| 资源利用率 | 资源使用效率 | 70-85% | 资源监控数据 |
| 分配效率 | 资源分配平均时间 | ≤10分钟 | 时间戳差值统计 |
| 成本效益 | 资源成本与产出比 | ≥1.5 | 成本效益分析 |
| 环境稳定性 | 测试环境可用率 | ≥99% | 可用性监控 |
| 配额准确性 | 配额预估准确率 | ≥90% | 预估与实际对比 |

### 资源配置协同评估报告格式

```json
{
  "evaluation_id": "EVAL-HUBU-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-07T23:59:59Z"
  },
  "resource_metrics": {
    "total_allocations": 50,
    "successful_allocations": 48,
    "failed_allocations": 2,
    "avg_allocation_time_minutes": 8,
    "reallocation_count": 3
  },
  "utilization_metrics": {
    "cpu_utilization": 0.78,
    "memory_utilization": 0.72,
    "storage_utilization": 0.65,
    "network_utilization": 0.55
  },
  "cost_metrics": {
    "total_cost": 8500,
    "budget": 10000,
    "cost_efficiency": 1.8,
    "savings_potential": 1200
  },
  "environment_metrics": {
    "total_environments": 15,
    "active_environments": 12,
    "availability_rate": 0.995,
    "avg_provision_time_minutes": 12
  },
  "recommendations": [
    {
      "category": "cost_optimization",
      "priority": "high",
      "description": "优化存储资源使用，清理未使用的快照",
      "expected_impact": "预计节省¥500/月"
    }
  ]
}
```

---

## 流水线协调能力

### 流水线资源配置节点

户部在白盒化7阶段流水线中负责资源配置和环境管理。

| 阶段 | 户部角色 | 配置内容 | 资源需求 |
|------|----------|----------|----------|
| 需求分析 | 支持 | 开发环境资源 | 基础开发环境 |
| SDD规范定义 | 支持 | 文档环境资源 | 协作文档平台 |
| 审议批准 | 支持 | 评审环境资源 | 评审会议室 |
| 测试先行 | 主导 | 测试环境配置 | 测试服务器、数据库 |
| 代码实现 | 主导 | 开发环境配置 | 开发服务器、依赖服务 |
| 持续重构 | 支持 | 重构环境资源 | 代码分析工具 |
| 部署发布 | 主导 | 生产环境配置 | 生产服务器、监控 |

### 流水线资源配置配置

```yaml
pipeline_resource_config:
  resource_provisioning:
    mode: "on_demand"
    preemptive: true
    auto_scaling: true
    
  environment_templates:
    development:
      cpu: 4
      memory: "8GB"
      storage: "100GB"
      
    testing:
      cpu: 8
      memory: "16GB"
      storage: "200GB"
      
    production:
      cpu: 16
      memory: "32GB"
      storage: "500GB"
      
  provisioning_rules:
    - stage: "test_first"
      environment: "testing"
      auto_provision: true
      dependencies: ["mysql", "redis", "mock_services"]
      
    - stage: "implementation"
      environment: "development"
      auto_provision: true
      dependencies: ["ide", "debugger", "local_db"]
```

---

## 增强功能集成

### 与provincial_coordinator集成

户部通过provincial_coordinator.py实现资源配置的自动化和协同：

```python
from scripts.provincial_coordinator import (
    SmartDispatcher,
    TaskRequirement,
    TaskPriority
)

dispatcher = SmartDispatcher()

def allocate_resources_for_task(task_id: str, resource_requirements: dict):
    requirement = TaskRequirement(
        task_id=task_id,
        required_capabilities={
            "environment_config": 0.9,
            "resource_allocation": 0.85
        },
        preferred_specializations=["hubu"],
        priority=TaskPriority.HIGH
    )
    
    decision = dispatcher.find_best_match(requirement, "ministry")
    
    return {
        "assigned_entity": decision.assigned_entity,
        "match_score": decision.overall_score,
        "resource_allocation": resource_requirements
    }
```

---

## 资源配置质量保障

### 资源配置质量检查清单

```
□ 资源需求评估准确
□ 资源配额在预算范围内
□ 环境配置符合规范
□ 资源分配决策有依据
□ 配置过程记录完整
□ 资源使用监控到位
□ 成本控制有效
□ 优化建议及时实施
```

### 资源配置质量评分

| 评分项 | 权重 | 评分标准 |
|--------|------|----------|
| 资源利用率 | 30% | 资源使用效率在目标范围内 |
| 分配效率 | 25% | 分配时间在合理范围内 |
| 成本效益 | 20% | 成本与产出比达标 |
| 环境稳定性 | 15% | 环境可用率高 |
| 持续优化 | 10% | 持续改进资源配置策略 |
```

### 资源分配策略

| 策略类型 | 适用场景 | 分配规则 |
|----------|----------|----------|
| 优先级分配 | 资源紧张时 | 关键任务优先获得资源 |
| 公平分配 | 资源充足时 | 按需求比例分配 |
| 动态分配 | 需求波动大 | 根据实时需求调整 |
| 预留分配 | 重要项目 | 预留固定资源池 |

### 资源配置决策输出

```json
{
  "allocation_decision_id": "RAD-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "request_id": "REQ-001",
  "decision": {
    "allocated_resources": {
      "compute": {
        "cpu_cores": 8,
        "memory_gb": 32,
        "storage_gb": 500
      },
      "api": {
        "openai_quota": 100000,
        "rate_limit": "30/minute"
      }
    },
    "allocation_score": 0.92,
    "decision_factors": {
      "demand_match": 0.95,
      "resource_availability": 0.90,
      "priority_weight": 0.92
    },
    "allocation_duration": "24 hours",
    "auto_renewal": true
  },
  "constraints": {
    "max_cpu": 16,
    "max_memory_gb": 64,
    "budget_limit": 1000
  },
  "risk_assessment": {
    "risk_level": "low",
    "potential_issues": [],
    "mitigation_plan": "设置资源使用告警阈值"
  }
}
```

## 资源监控与调度（增强版）

### 资源使用监控

```json
{
  "resource_monitoring": {
    "monitor_id": "RM-001",
    "timestamp": "2024-01-01T00:00:00Z",
    "monitored_resources": [
      {
        "resource_id": "RES-001",
        "type": "compute",
        "allocated": {"cpu": 8, "memory_gb": 32},
        "used": {"cpu": 5.2, "memory_gb": 18.5},
        "utilization_rate": 0.65,
        "status": "healthy",
        "alerts": []
      }
    ],
    "summary": {
      "total_allocated": 10,
      "total_used": 6.5,
      "overall_utilization": 0.65,
      "alerts_count": 0
    }
  }
}
```

### 资源告警机制

| 告警类型 | 触发条件 | 处理动作 |
|----------|----------|----------|
| 使用率过高 | 利用率>80% | 发送告警，准备扩容 |
| 配额即将耗尽 | 剩余<20% | 发送告警，申请增加配额 |
| 资源泄漏 | 使用量持续增长不释放 | 发送告警，自动回收 |
| 异常使用 | 使用模式异常 | 发送告警，人工审核 |

### 资源回收流程

```
回收触发条件:
  - 任务完成
  - 资源超时未使用
  - 用户主动释放
  - 系统强制回收

回收步骤:
  1. 识别可回收资源
  2. 验证资源状态
  3. 清理资源数据
  4. 释放资源配额
  5. 更新资源池状态
  6. 记录回收日志
  7. 通知相关方
```

## API密钥管理（增强版）

## 资源管理流程

### 1. 资源需求评估
```
输入: 任务描述、资源类型需求、预估使用时长
评估维度:
  - 计算资源: CPU核心数、内存大小、GPU需求
  - 存储资源: 磁盘空间、数据库容量、对象存储
  - 网络资源: 带宽、CDN、负载均衡
  - 外部服务: API调用额度、第三方服务订阅
  - 测试资源: 测试环境数量、测试数据规模、并发测试需求
输出: 资源需求评估报告
```

### 2. 资源可用性检查
```
检查步骤:
  1. 查询资源池当前状态
  2. 检查已分配资源与可用资源比例
  3. 验证资源配额限制
  4. 确认资源地理位置/可用区要求
  5. 检查资源预留情况
  6. 检查测试环境可用性
输出: 资源可用性报告
```

### 3. 资源分配决策
```
决策规则:
  - 紧急任务: 优先分配，可临时超配
  - 常规任务: 按配额分配
  - 资源不足: 排队等待或申请扩容
  - 测试任务: 优先使用预配置测试环境
  
分配策略:
  - 独占资源: 高性能需求任务
  - 共享资源: 低优先级任务
  - 弹性资源: 波动负载任务
  - 测试专用: 隔离的测试环境
```

### 4. 资源分配执行
```
执行步骤:
  1. 创建资源分配记录
  2. 配置资源访问权限
  3. 设置资源使用配额
  4. 配置监控告警
  5. 通知资源使用者
  6. 初始化测试环境（如需要）
```

### 5. 资源使用监控
```
监控内容:
  - 实时使用率监控
  - 成本累计追踪
  - 异常使用告警
  - 资源泄漏检测
  - 测试环境健康状态
  
告警阈值:
  - CPU使用率 > 80%: 警告
  - 内存使用率 > 85%: 警告
  - 磁盘使用率 > 90%: 严重
  - 成本超预算 > 10%: 警告
  - 测试环境故障: 立即告警
```

### 6. 资源回收
```
回收条件:
  - 任务完成且无后续需求
  - 资源闲置超过规定时间
  - 用户主动释放
  - 测试环境过期
  
回收流程:
  1. 确认资源可回收状态
  2. 备份必要数据
  3. 清理资源内容
  4. 释放资源到资源池
  5. 更新资源分配记录
  6. 重置测试环境状态
```

## 测试环境资源管理

### 测试环境分类

| 环境类型 | 用途 | 资源配额 | 保留时间 | 数据保留策略 |
|----------|------|----------|----------|--------------|
| unit-test | 单元测试 | 基础配置 | 临时 | 不保留 |
| integration-test | 集成测试 | 中等配置 | 按需 | 测试数据保留 |
| e2e-test | 端到端测试 | 完整配置 | 按需 | 测试数据保留 |
| performance-test | 性能测试 | 高配置 | 临时 | 不保留 |
| security-test | 安全测试 | 隔离配置 | 临时 | 不保留 |
| staging | 预发布验证 | 生产同配 | 短期 | 保留关键数据 |

### 测试环境生命周期管理

```yaml
test_environment_lifecycle:
  states:
    - name: "pending"
      description: "等待资源分配"
      actions: ["allocate_resources"]
    - name: "provisioning"
      description: "环境创建中"
      actions: ["setup_services", "configure_network"]
    - name: "ready"
      description: "环境就绪可用"
      actions: ["assign_to_task", "run_tests"]
    - name: "in_use"
      description: "正在使用中"
      actions: ["monitor_usage", "extend_if_needed"]
    - name: "cleanup"
      description: "清理中"
      actions: ["backup_data", "reset_state"]
    - name: "available"
      description: "可重新分配"
      actions: ["return_to_pool"]
  
  transitions:
    - from: "pending"
      to: "provisioning"
      trigger: "resource_allocated"
    - from: "provisioning"
      to: "ready"
      trigger: "setup_complete"
    - from: "ready"
      to: "in_use"
      trigger: "task_assigned"
    - from: "in_use"
      to: "cleanup"
      trigger: "task_completed"
    - from: "cleanup"
      to: "available"
      trigger: "cleanup_complete"
```

### 测试环境配置模板

#### 单元测试环境配置
```yaml
test_environment:
  name: "unit-test-env"
  type: "unit-test"
  
  compute:
    cpu_cores: 2
    memory: "4GB"
    gpu: false
    
  storage:
    disk_size: "20GB"
    temp_storage: "5GB"
    
  network:
    bandwidth: "10Mbps"
    public_ip: false
    isolated: true
    
  services:
    - name: "测试框架"
      type: "test_runner"
      options: ["jest", "pytest", "junit"]
      
  lifecycle:
    max_duration: "30分钟"
    auto_cleanup: true
    data_persistence: false
    
  cost_limit:
    per_run: "¥5"
```

#### 集成测试环境配置
```yaml
test_environment:
  name: "integration-test-env"
  type: "integration-test"
  
  compute:
    cpu_cores: 4
    memory: "8GB"
    gpu: false
    
  storage:
    disk_size: "50GB"
    database_size: "10GB"
    
  network:
    bandwidth: "50Mbps"
    public_ip: true
    internal_network: true
    
  services:
    - name: "主数据库"
      type: "mysql"
      version: "8.0"
      size: "small"
    - name: "缓存"
      type: "redis"
      version: "7.0"
      size: "small"
    - name: "消息队列"
      type: "rabbitmq"
      version: "3.12"
      size: "small"
    - name: "测试服务"
      type: "test_runner"
      options: ["integration_test_framework"]
      
  lifecycle:
    max_duration: "2小时"
    auto_cleanup: false
    data_persistence: true
    backup_on_cleanup: true
    
  cost_limit:
    per_run: "¥50"
    daily: "¥200"
```

#### 性能测试环境配置
```yaml
test_environment:
  name: "performance-test-env"
  type: "performance-test"
  
  compute:
    cpu_cores: 8
    memory: "32GB"
    gpu: false
    high_performance: true
    
  storage:
    disk_size: "200GB"
    database_size: "50GB"
    ssd_only: true
    
  network:
    bandwidth: "1Gbps"
    public_ip: true
    load_balancer: true
    
  services:
    - name: "主数据库"
      type: "mysql"
      version: "8.0"
      size: "large"
      performance_tuned: true
    - name: "缓存集群"
      type: "redis"
      version: "7.0"
      size: "medium"
      cluster_mode: true
    - name: "负载生成器"
      type: "load_generator"
      options: ["k6", "jmeter", "locust"]
    - name: "监控服务"
      type: "monitoring"
      options: ["prometheus", "grafana"]
      
  lifecycle:
    max_duration: "4小时"
    auto_cleanup: true
    data_persistence: false
    
  cost_limit:
    per_run: "¥200"
```

## 资源调度策略

### 调度算法

#### 优先级调度
```
优先级规则:
  - P0（紧急）: 立即分配，可抢占低优先级资源
  - P1（高）: 优先分配，等待时间不超过5分钟
  - P2（中）: 正常排队，按FIFO顺序
  - P3（低）: 填充式分配，利用空闲资源

抢占策略:
  - 允许高优先级抢占低优先级
  - 被抢占任务进入等待队列
  - 记录抢占事件用于分析
```

#### 负载均衡调度
```
均衡策略:
  - 轮询: 均匀分配任务到各资源节点
  - 最少连接: 分配到当前负载最低的节点
  - 加权分配: 根据节点能力加权分配
  - 亲和性: 考虑任务与资源的亲和性

测试环境负载均衡:
  - 按测试类型分配到专用环境池
  - 相同测试类型按轮询分配
  - 考虑环境预热状态
```

#### 成本优化调度
```
优化策略:
  - 预留实例: 长期任务使用预留实例降低成本
  - 竞价实例: 可中断任务使用竞价实例
  - 自动伸缩: 根据负载自动调整资源
  - 定时调度: 非紧急任务安排在低峰时段

测试成本优化:
  - 复用测试环境
  - 并行执行测试
  - 自动清理闲置环境
  - 测试数据压缩存储
```

### 资源预留策略

```yaml
resource_reservation:
  strategies:
    - name: "critical_task_reserve"
      description: "关键任务资源预留"
      reserve_percentage: 20
      apply_to: ["P0", "P1"]
      
    - name: "test_environment_pool"
      description: "测试环境资源池"
      reserve_count:
        unit_test: 5
        integration_test: 3
        performance_test: 2
      
    - name: "burst_capacity"
      description: "突发容量预留"
      reserve_percentage: 10
      trigger_condition: "负载超过80%"
      
  expiration:
    default_ttl: "24小时"
    extendable: true
    max_extension: "72小时"
```

### 资源回收策略

```
回收触发条件:
  - 任务完成且空闲超过30分钟
  - 资源使用率达到配额上限
  - 预算超支警告
  - 环境配置过期

回收优先级:
  1. 已完成的临时测试环境
  2. 长时间空闲的开发环境
  3. 低优先级任务占用的资源
  4. 可迁移的弹性资源

数据保留策略:
  - 测试日志: 保留7天
  - 测试报告: 保留30天
  - 性能数据: 保留90天
  - 环境配置: 永久保留
```

## 资源分配模板

### 计算资源分配模板
```yaml
compute_resource_allocation:
  allocation_id: "alloc-xxx"
  
  task_info:
    task_id: "任务ID"
    task_name: "任务名称"
    requester: "请求者"
    priority: "P0|P1|P2|P3"
    
  compute_resources:
    cpu:
      cores: 数字
      type: "shared|dedicated"
    memory:
      size: "GB"
      type: "standard|high_perf"
    gpu:
      enabled: true|false
      type: "型号"
      count: 数字
      
  storage_resources:
    disk:
      type: "ssd|hdd"
      size: "GB"
      iops: 数字
    database:
      type: "mysql|postgresql|mongodb|redis"
      size: "GB"
      connections: 数字
      
  network_resources:
    bandwidth: "Mbps|Gbps"
    cdn_enabled: true|false
    load_balancer: true|false
    
  allocation_config:
    start_time: "开始时间"
    end_time: "结束时间"
    auto_extend: true|false
    max_extend_hours: 数字
    
  access_control:
    allowed_users: ["用户列表"]
    allowed_ips: ["IP列表"]
    ssh_keys: ["SSH密钥ID"]
    
  monitoring:
    alert_contacts: ["联系人"]
    alert_thresholds:
      cpu: 百分比
      memory: 百分比
      disk: 百分比
```

### API密钥分配模板
```yaml
api_key_allocation:
  allocation_id: "key-alloc-xxx"
  
  api_info:
    provider: "服务提供商"
    service_name: "服务名称"
    api_type: "REST|GraphQL|gRPC"
    
  key_config:
    key_name: "密钥名称"
    permissions: ["权限列表"]
    rate_limit: "请求/分钟"
    quota_limit: "请求/月"
    
  security:
    encryption: "AES-256"
    rotation_period: "天"
    ip_whitelist: ["IP列表"]
    
  allocation:
    allocated_to: "分配对象"
    purpose: "用途说明"
    valid_from: "生效时间"
    valid_until: "失效时间"
    
  monitoring:
    usage_alert_threshold: 百分比
    cost_alert_threshold: "金额"
```

### 存储资源分配模板
```yaml
storage_allocation:
  allocation_id: "storage-xxx"
  
  storage_type: "object|block|file|database"
  
  capacity:
    total_size: "GB|TB"
    used_size: "GB|TB"
    growth_rate: "GB/天"
    
  performance:
    iops: 数字
    throughput: "MB/s"
    latency: "ms"
    
  redundancy:
    replication: "单副本|双副本|三副本"
    backup_enabled: true|false
    backup_frequency: "daily|weekly|monthly"
    
  access:
    access_mode: "private|public|mixed"
    access_protocol: "NFS|SMB|S3|iSCSI"
    
  lifecycle:
    retention_policy: "保留策略"
    auto_archive: true|false
    archive_after_days: 数字
```

## 环境配置指南

### 环境分类

| 环境类型 | 用途 | 资源配额 | 保留时间 |
|----------|------|----------|----------|
| development | 开发调试 | 基础配置 | 长期 |
| testing | 测试验证 | 中等配置 | 按需 |
| staging | 预发布验证 | 生产同配 | 短期 |
| production | 正式运行 | 高可用配置 | 永久 |

### 环境配置模板

#### 开发环境配置
```yaml
environment:
  name: "development"
  type: "dev"
  
  compute:
    cpu_cores: 2
    memory: "4GB"
    gpu: false
    
  storage:
    disk_size: "50GB"
    database_size: "10GB"
    
  network:
    bandwidth: "10Mbps"
    public_ip: false
    
  services:
    - name: "数据库"
      type: "mysql"
      version: "8.0"
      size: "small"
    - name: "缓存"
      type: "redis"
      version: "7.0"
      size: "small"
      
  cost_limit:
    daily: "¥50"
    monthly: "¥1000"
```

#### 测试环境配置
```yaml
environment:
  name: "testing"
  type: "test"
  
  compute:
    cpu_cores: 4
    memory: "8GB"
    gpu: false
    
  storage:
    disk_size: "100GB"
    database_size: "20GB"
    
  network:
    bandwidth: "50Mbps"
    public_ip: true
    
  services:
    - name: "数据库"
      type: "mysql"
      version: "8.0"
      size: "medium"
    - name: "缓存"
      type: "redis"
      version: "7.0"
      size: "medium"
    - name: "消息队列"
      type: "rabbitmq"
      version: "3.12"
      size: "small"
      
  cost_limit:
    daily: "¥200"
    monthly: "¥4000"
```

#### 生产环境配置
```yaml
environment:
  name: "production"
  type: "prod"
  
  compute:
    cpu_cores: 8
    memory: "32GB"
    gpu: false
    high_availability: true
    
  storage:
    disk_size: "500GB"
    database_size: "200GB"
    backup_enabled: true
    
  network:
    bandwidth: "1Gbps"
    public_ip: true
    cdn_enabled: true
    load_balancer: true
    ssl_certificate: true
    
  services:
    - name: "主数据库"
      type: "mysql"
      version: "8.0"
      size: "large"
      replication: true
    - name: "从数据库"
      type: "mysql"
      version: "8.0"
      size: "large"
      role: "replica"
    - name: "缓存集群"
      type: "redis"
      version: "7.0"
      size: "large"
      cluster_mode: true
    - name: "消息队列"
      type: "rabbitmq"
      version: "3.12"
      size: "medium"
      cluster_mode: true
      
  monitoring:
    enabled: true
    log_retention: "30天"
    metrics_retention: "90天"
    alerting: true
    
  cost_limit:
    daily: "¥1000"
    monthly: "¥20000"
```

### 环境配置流程

```
1. 环境申请
   - 提交环境申请表
   - 说明环境用途和需求
   - 指定环境类型和保留时间

2. 资源评估
   - 评估资源需求合理性
   - 检查资源可用性
   - 计算成本预估

3. 环境创建
   - 按模板创建环境
   - 配置网络和安全组
   - 部署基础服务

4. 访问配置
   - 创建访问账号
   - 配置访问权限
   - 分发访问凭证

5. 环境验证
   - 验证环境可用性
   - 验证网络连通性
   - 验证服务正常

6. 移交使用
   - 提供环境文档
   - 提供访问指南
   - 设置监控告警
```

### 环境安全配置

```yaml
security_config:
  network_security:
    firewall_enabled: true
    allowed_ports: [80, 443, 22]
    vpn_required: true|false
    
  access_control:
    authentication: "password|ssh_key|sso"
    mfa_enabled: true|false
    session_timeout: "分钟"
    
  data_security:
    encryption_at_rest: true
    encryption_in_transit: true
    backup_encryption: true
    
  audit:
    access_logging: true
    operation_logging: true
    log_retention: "天"
```

## 资源调度最佳实践

### 测试环境快速启动
```
预热策略:
  - 保持最小数量的预热环境
  - 使用容器镜像加速启动
  - 预配置常用服务
  - 使用快照快速恢复

启动优化:
  - 并行初始化服务
  - 延迟加载非关键组件
  - 使用配置模板
  - 自动化健康检查
```

### 资源利用率优化
```
监控指标:
  - CPU平均利用率: 目标60-80%
  - 内存平均利用率: 目标70-85%
  - 环境周转率: 每小时环境复用次数
  - 成本效率: 每元成本完成的任务数

优化措施:
  - 自动伸缩资源
  - 合并相似测试
  - 优化环境配置
  - 清理闲置资源
```

## 透明度记录要求
### 资源分配决策记录
- 记录资源分配依据：包括资源类型、数量、优先级、成本效益分析
- 记录资源调度推理过程：包括需求评估、资源可用性检查、分配策略选择

### 记录内容规范
- 决策时间戳
- 资源需求详情
- 可用资源清单
- 分配方案及理由
- 成本预估与实际对比

## 协同调用接口

### 接口定义

户部作为资源配置机构，提供以下协同调用接口供其他技能调用：

| 接口名称 | 接口描述 | 调用方 |
|----------|----------|--------|
| `allocate_resources` | 资源分配接口 | 尚书省、六部 |
| `provision_test_env` | 测试环境配置接口 | 兵部 |
| `manage_api_keys` | API密钥管理接口 | 工部、外部技能 |
| `check_resource_quota` | 资源配额检查接口 | 尚书省 |

### 输入参数规范

#### 资源分配接口参数

```json
{
  "interface": "allocate_resources",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "resource_request": {
      "compute": {
        "cpu_cores": 4,
        "memory": "8GB",
        "gpu": false
      },
      "storage": {
        "disk_size": "100GB",
        "type": "ssd|hdd"
      },
      "network": {
        "bandwidth": "100Mbps",
        "public_ip": true
      }
    },
    "purpose": "用途说明",
    "duration": "使用时长",
    "priority": "P0|P1|P2|P3"
  }
}
```

#### 测试环境配置接口参数

```json
{
  "interface": "provision_test_env",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "env_type": "unit-test|integration-test|e2e-test|performance-test",
    "services": [
      {
        "name": "mysql",
        "version": "8.0",
        "size": "small|medium|large"
      }
    ],
    "config": {
      "auto_cleanup": true,
      "data_persistence": false,
      "isolated_network": true
    }
  }
}
```

### 输出格式规范

```json
{
  "interface": "allocate_resources",
  "call_id": "ALLOC-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "status": "success|failure|partial",
  "result": {
    "allocation_id": "ALLOC-001",
    "resources": {
      "compute": {"allocated": true, "details": "配置详情"},
      "storage": {"allocated": true, "details": "配置详情"}
    },
    "access_info": {
      "endpoint": "访问地址",
      "credentials": "凭证信息"
    },
    "expires_at": "过期时间"
  }
}
```

### 调用示例

```bash
# 调用资源分配接口
调用 ./SKILL.md --interface=allocate_resources \
  --resource-request='{"compute":{"cpu_cores":4,"memory":"8GB"}}' \
  --purpose="开发测试环境" \
  --priority="P1"

# 调用测试环境配置接口
调用 ./SKILL.md --interface=provision_test_env \
  --env-type="integration-test" \
  --services='[{"name":"mysql","version":"8.0"}]'
```

---

## 下属四司
- duzhisi（度支司）：预算管理
- jinbucangsi（金部仓司）：资金管理
- cangbucangsi（仓部仓司）：存储资源
- libucangsi（吏部仓司）：人力资源库

---

## 资源监控增强

### 实时资源监控仪表板

```json
{
  "dashboard_config": {
    "refresh_interval_seconds": 30,
    "widgets": [
      {
        "type": "gauge",
        "title": "CPU使用率",
        "metrics": ["cpu.usage_percent"],
        "thresholds": {
          "warning": 70,
          "critical": 90
        }
      },
      {
        "type": "gauge",
        "title": "内存使用率",
        "metrics": ["memory.usage_percent"],
        "thresholds": {
          "warning": 80,
          "critical": 95
        }
      },
      {
        "type": "chart",
        "title": "资源使用趋势",
        "metrics": ["cpu.usage", "memory.usage", "disk.usage"],
        "time_range": "24h"
      }
    ]
  }
}
```

### 资源自动伸缩策略

```yaml
auto_scaling:
  compute:
    enabled: true
    min_instances: 2
    max_instances: 10
    scale_up:
      trigger: "cpu > 70% for 5 minutes"
      action: "add 1 instance"
      cooldown: 300
    scale_down:
      trigger: "cpu < 30% for 15 minutes"
      action: "remove 1 instance"
      cooldown: 600
      
  database:
    enabled: true
    read_replicas:
      min: 1
      max: 5
      scale_trigger: "read_qps > 10000"
      
  cache:
    enabled: true
    memory_scaling:
      trigger: "hit_rate < 80%"
      action: "increase memory by 20%"
```

### 成本优化分析

```json
{
  "cost_analysis": {
    "period": "monthly",
    "breakdown": {
      "compute": {
        "budget": 5000,
        "actual": 4500,
        "variance": -10,
        "optimization_suggestions": [
          "考虑使用预留实例节省20%成本",
          "非生产环境可使用竞价实例"
        ]
      },
      "storage": {
        "budget": 2000,
        "actual": 2200,
        "variance": 10,
        "optimization_suggestions": [
          "清理未使用的快照",
          "启用生命周期策略归档旧数据"
        ]
      },
      "network": {
        "budget": 1000,
        "actual": 800,
        "variance": -20
      }
    },
    "total_savings_potential": "¥1200/月"
  }
}
