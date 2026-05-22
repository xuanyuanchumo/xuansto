# create-sddwcc SDD+TDD 多Agent架构参考文档

> 版本: 3.2.0 | 更新日期: 2026-05-06 | 编码: UTF-8 without BOM | 行尾: LF

---

## 概述

create-sddwcc 是一套基于SDD（Specification-Driven Development）与TDD（Test-Driven Development）融合的多Agent协作架构，通过18个专业化Agent和MCP（Model Context Protocol）集成，实现从需求到交付的全生命周期自动化。其核心框架definition-done确保每个阶段都有明确的完成定义。

---

## 18个专业化Agent

### 规划层Agent（Planning Layer）

| Agent | 职责 | 输入 | 输出 |
|-------|------|------|------|
| Requirements Analyst | 需求分析与澄清 | 用户需求描述 | 结构化需求文档 |
| Architecture Planner | 架构设计与技术选型 | 需求文档 | 架构设计文档 |
| Sprint Planner | 迭代规划与任务分解 | 架构文档 | Sprint计划 |
| Specification Writer | 规格文档编写 | 需求+架构 | SDD规格文档 |

### 开发层Agent（Development Layer）

| Agent | 职责 | 输入 | 输出 |
|-------|------|------|------|
| TDD Writer | 测试用例先行编写 | SDD规格 | 测试代码（RED阶段） |
| Feature Developer | 功能实现 | 测试用例 | 实现代码（GREEN阶段） |
| Refactoring Specialist | 代码重构优化 | 实现代码 | 重构代码（REFACTOR阶段） |
| API Developer | API接口开发 | API规格 | API端点代码 |
| UI Developer | 界面组件开发 | UI设计稿 | 前端组件代码 |

### 质量层Agent（Quality Layer）

| Agent | 职责 | 输入 | 输出 |
|-------|------|------|------|
| Code Reviewer | 代码审查 | 代码变更 | 审查报告 |
| Security Auditor | 安全审计 | 代码+配置 | 安全报告 |
| Performance Tester | 性能测试 | 构建产物 | 性能报告 |
| Integration Tester | 集成测试 | 模块集合 | 集成测试报告 |

### 运维层Agent（Operations Layer）

| Agent | 职责 | 输入 | 输出 |
|-------|------|------|------|
| DevOps Engineer | CI/CD与部署 | 构建产物 | 部署配置 |
| Documentation Writer | 文档生成 | 代码+规格 | 技术文档 |
| Release Manager | 版本发布管理 | 发布清单 | 发布包 |
| Monitoring Specialist | 运行监控 | 运行指标 | 监控告警 |

### 协调层Agent（Coordination Layer）

| Agent | 职责 | 输入 | 输出 |
|-------|------|------|------|
| Project Coordinator | 项目协调与冲突解决 | Agent间消息 | 协调决策 |
| Knowledge Manager | 知识库维护与检索 | 所有Agent输出 | 知识库更新 |

---

## MCP集成架构

### MCP工具注册

```yaml
mcp_integration:
  protocol_version: "2025-03-26"
  tools:
    - name: "sddwcc:query_spec"
      description: "查询SDD规格文档"
      input_schema:
        spec_id: string
        section: string

    - name: "sddwcc:run_tdd_cycle"
      description: "执行TDD RED-GREEN-REFACTOR循环"
      input_schema:
        test_file: string
        implementation_file: string

    - name: "sddwcc:check_definition_done"
      description: "检查阶段完成定义"
      input_schema:
        phase: string
        deliverables: list

    - name: "sddwcc:dispatch_agent"
      description: "调度专业化Agent"
      input_schema:
        agent_type: string
        task: string
        context: object

    - name: "sddwcc:sync_knowledge"
      description: "同步知识库"
      input_schema:
        category: string
        content: object
```

### Agent间通信

```
Agent A ──→ MCP Tool Call ──→ Agent B
   │                              │
   ├── sddwcc:dispatch_agent ─────┤
   ├── sddwcc:query_spec ─────────┤
   └── sddwcc:sync_knowledge ────┘
```

---

## Definition-Done框架

### 核心原则

每个开发阶段都有明确的"完成定义"（Definition of Done），只有满足所有条件才能进入下一阶段。

### 阶段完成定义

```yaml
definition_done:
  requirements:
    - all_user_stories_documented: true
    - acceptance_criteria_defined: true
    - stakeholder_review_passed: true

  architecture:
    - tech_stack_decided: true
    - module_boundaries_defined: true
    - api_contracts_specified: true
    - security_model_documented: true

  tdd_red:
    - test_cases_cover_all_requirements: true
    - all_tests_fail_as_expected: true
    - test_coverage_targets_set: true

  tdd_green:
    - all_tests_pass: true
    - no_test_modifications: true
    - minimum_implementation: true

  tdd_refactor:
    - all_tests_still_pass: true
    - code_quality_gates_passed: true
    - no_behavior_change: true

  review:
    - code_review_approved: true
    - security_audit_passed: true
    - performance_benchmarks_met: true

  deployment:
    - ci_cd_pipeline_green: true
    - smoke_tests_passed: true
    - rollback_plan_documented: true
```

### 门禁检查机制

```python
def check_definition_done(phase: str, deliverables: dict) -> bool:
    criteria = DEFINITION_DONE[phase]
    for criterion, expected in criteria.items():
        actual = deliverables.get(criterion)
        if actual != expected:
            log_failure(phase, criterion, expected, actual)
            return False
    return True
```

---

## SDD+TDD融合流程

```
需求分析 → SDD规格编写 → TDD RED → TDD GREEN → TDD REFACTOR → 代码审查 → 部署
    │            │             │          │            │             │         │
    └─ DoD检查 ──┘── DoD检查 ──┘── DoD ──┘── DoD ────┘── DoD ─────┘── DoD ──┘
```

---

## Definition of Done框架

### 核心原则

Definition of Done（DoD）框架确保每个交付物在进入下一阶段前满足明确的质量标准。DoD不仅适用于阶段门禁，也适用于单个功能、用户故事和代码提交。

### DoD检查清单

```yaml
definition_of_done_checklist:
  code_review:
    - code_review_passed: true
      description: "代码审查通过，无未解决的审查意见"
      verification: "PR已获至少1位审查者批准，无未解决评论"

  test_coverage:
    - test_coverage_met: true
      description: "测试覆盖率达标（≥80%默认，≥90%严格模式）"
      verification: "覆盖率报告确认达标，无关键路径遗漏"

  security_scan:
    - security_scan_clean: true
      description: "安全扫描无高危及以上漏洞"
      verification: "SAST/DAST扫描通过，无Critical/High级别发现"

  documentation:
    - docs_complete: true
      description: "文档完整（API文档、变更日志、用户文档）"
      verification: "文档审查通过，覆盖所有公开接口和行为变更"

  performance:
    - performance_not_degraded: true
      description: "性能未退化，关键指标在基线范围内"
      verification: "性能基准测试通过，响应时间/吞吐量/内存使用无显著退化"

  design_consistency:
    - design_consistency_gte_95: true
      description: "设计一致性≥95%"
      verification: "UI/UX设计审查通过，设计系统组件使用率≥95%"
```

### DoD执行机制

```python
class DoDEnforcer:
    CHECKLIST = {
        "code_review_passed": {"blocking": True, "severity": "BLOCK"},
        "test_coverage_met": {"blocking": True, "severity": "BLOCK"},
        "security_scan_clean": {"blocking": True, "severity": "BLOCK"},
        "docs_complete": {"blocking": True, "severity": "WARN"},
        "performance_not_degraded": {"blocking": True, "severity": "WARN"},
        "design_consistency_gte_95": {"blocking": False, "severity": "WARN"},
    }

    def evaluate(self, deliverables: dict) -> dict:
        results = {}
        for check, config in self.CHECKLIST.items():
            actual = deliverables.get(check, False)
            results[check] = {
                "passed": actual,
                "blocking": config["blocking"],
                "severity": config["severity"],
            }
        all_blocking_passed = all(
            r["passed"] for r in results.values() if r["blocking"]
        )
        return {
            "dod_passed": all_blocking_passed,
            "checks": results,
        }
```

### DoD门禁集成

DoD框架与xuansto-skill质量门禁体系深度集成：

| 阶段 | DoD检查项 | 对应质量门禁 |
|------|----------|-------------|
| 实现完成 | code_review_passed, test_coverage_met | GATE-007, TEST-PASS, GATE-009 |
| 安全验证 | security_scan_clean | GATE-012, AGENTIC-SECURITY |
| 交付就绪 | docs_complete, performance_not_degraded, design_consistency_gte_95 | DOC-COMPLETENESS, UX-ACCEPTANCE |

---

## 与xuansto-skill的集成

| xuansto模块 | sddwcc对应 | 集成方式 |
|------------|-----------|---------|
| 57 Agents | 18 Agents | 角色映射与能力对齐 |
| Quality Gates | Definition-Done | 门禁条件同步 |
| MCP Protocol | MCP Tools | 工具注册与调用 |
| Knowledge Base | Knowledge Manager | 知识库共享 |

---

> 本文档由 Multi-Agent SDD/TDD Orchestrator 维护 | 最后更新: 2026-05-06
