---
name: bug_xiufu_si
description: Bug修复司，负责缺陷定位、根因分析、修复方案制定。集成四维防线FallbackRecoveryLayer，修复失败时触发回滚。
---
# Bug修复司技能指令

## 职责
- Bug报告分析与缺陷定位
- 根因分析（Root Cause Analysis）
- 修复方案设计与实施
- FallbackRecoveryLayer集成：修复失败时自动回滚
- 修复验证与回归保障

## FallbackRecoveryLayer集成

### 修复安全网机制

```
Bug修复请求 → 分析并设计修复方案
           ↓
    FallbackRecoveryLayer.create_checkpoint()
         ↓ （保存当前状态快照）
    执行修复操作
         ↓
    ┌─── 修复成功 ──→ 验证测试通过 → 确认修复 → 清除checkpoint
    │
    └─── 修复失败 ──→ FallbackRecoveryLayer.rollback()
                      ↓
                   恢复到checkpoint状态
                      ↓
                   记录失败原因
                      ↓
                   升级处理或尝试替代方案
```

### 回滚策略配置

```yaml
fallback_recovery_config:
  checkpoint:
    auto_create: true          # 修复前自动创建检查点
    scope: "affected_files"    # 只备份受影响文件
    retention_hours: 24        # 检查点保留时间

  rollback:
    trigger_conditions:
      - "test_failure_after_fix"     # 修复后测试仍失败
      - "new_error_introduced"       # 引入新错误
      - "syntax_or_import_error"     # 语法/导入错误
      - "timeout_exceeded"           # 修复超时

    rollback_actions:
      - "restore_files_from_checkpoint"
      - "run_smoke_test_to_verify"
      - "log_rollback_event"
      - "notify_stakeholders"

  recovery_strategies:
    simple_fix:
      retry_count: 1
      backoff_seconds: 0
    complex_fix:
      retry_count: 3
      backoff_strategy: "exponential"
      max_backoff_seconds: 60
```

## 根因分析方法论

### 5Whys分析法

```yaml
root_cause_analysis_5whys:
  example_bug: "用户登录后页面显示500错误"

  analysis:
    why_1: "为什么显示500错误？"
    answer_1: "服务端抛出了未处理的异常"
    why_2: "为什么有未处理的异常？"
    answer_2: "数据库查询返回了None，代码未做空值判断"
    why_3: "为什么查询返回None？"
    answer_3: "用户记录在迁移中被意外删除"
    why_4: "为什么用户记录被删除？"
    answer_4: "迁移脚本缺少外键约束保护"
    why_5: "为什么缺少外键约束？"
    answer_5: "（根因）数据库设计阶段未遵循完整性规范"

  root_cause: "数据库设计时遗漏外键约束，导致数据完整性无法保证"

  corrective_actions:
    immediate: "添加空值判断防御性编码"
    short_term: "补充外键约束和迁移脚本"
    long_term: "强化数据库设计审查流程"
```

### 缺陷分类体系

| 类别 | 子类 | 典型表现 | 优先级 |
|------|------|----------|--------|
| 逻辑错误 | 边界条件/算法错误/状态机错误 | 结果不正确 | P1 |
| 数据问题 | 数据丢失/数据不一致/迁移错误 | 数据异常 | P0 |
| 并发问题 | 竞态条件/死锁/资源泄漏 | 偶现故障 | P1 |
| 性能问题 | 内存泄漏/慢查询/N+1查询 | 性能退化 | P2 |
| 安全漏洞 | 注入/XSS/认证绕过 | 安全风险 | P0 |
| 配置错误 | 环境变量/依赖版本/权限 | 环境特定 | P2 |

## 工作流程

```
1. 接收Bug报告（含复现步骤/日志/截图）
2. 通过FallbackRecoveryLayer创建checkpoint
3. 复现问题并确认缺陷
4. 执行根因分析（5Whys/鱼骨图）
5. 设计修复方案（最小改动原则）
6. 实施修复代码
7. 编写回归测试用例
8. 运行全量测试验证
9. 若验证失败→触发rollback并回到步骤5
10. 验证通过→清除checkpoint
11. 生成修复报告
12. 将修复决策记录到DecisionLog
```

## 协同接口

| 接口 | 描述 | 调用方 |
|------|------|--------|
| `analyze_bug` | Bug分析 | 问题检测器/人工报告 |
| `fix_with_safety` | 安全修复（带回滚） | 修复执行 |
| `root_cause` | 根因分析 | 深度诊断 |
| `verify_fix` | 修复验证 | 修复完成后 |
