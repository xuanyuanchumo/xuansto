# Agency-Agents 集成配置

## 概述

本文档定义了Agency-Agents技能与三省六部系统的集成映射关系，实现专业Agent角色与六部职能的无缝对接。

## 集成架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Agency-Agents 集成架构                        │
│                                                                  │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐                 │
│   │ 中书省   │    │ 门下省   │    │ 尚书省   │                 │
│   │ 决策层   │    │ 审议层   │    │ 执行层   │                 │
│   └────┬─────┘    └────┬─────┘    └────┬─────┘                 │
│        │               │               │                        │
│        ▼               ▼               ▼                        │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │              Agency-Agents 专业角色池                     │  │
│   │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ │  │
│   │  │ 工程 │ │ 设计 │ │ 测试 │ │ 产品 │ │ 项目 │ │ 营销 │ │  │
│   │  │ 部门 │ │ 部门 │ │ 部门 │ │ 部门 │ │ 管理 │ │ 部门 │ │  │
│   │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ │  │
│   └─────────────────────────────────────────────────────────┘  │
│        │               │               │                        │
│        ▼               ▼               ▼                        │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐                 │
│   │   吏部   │    │   兵部   │    │   工部   │                 │
│   │ 人员调度 │    │ 测试先行 │    │ 开发执行 │                 │
│   └──────────┘    └──────────┘    └──────────┘                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 一、部门映射关系

### 1. 吏部（人员调度）映射

| 三省六部角色 | Agency-Agent | 专业能力 | 调用场景 |
|-------------|--------------|----------|----------|
| 项目经理 | Senior Project Manager | 任务分解、范围管理 | 项目启动、任务分配 |
| 架构师 | Software Architect | 系统设计、DDD | 架构设计阶段 |
| 技术负责人 | Senior Developer | 技术决策、代码质量 | 复杂实现任务 |

### 2. 户部（资源管理）映射

| 三省六部角色 | Agency-Agent | 专业能力 | 调用场景 |
|-------------|--------------|----------|----------|
| DevOps工程师 | DevOps Automator | CI/CD、云基础设施 | 部署配置、环境搭建 |
| 数据库优化师 | Database Optimizer | 查询优化、索引策略 | 数据库性能调优 |
| SRE工程师 | SRE | 可靠性、监控 | 生产环境保障 |

### 3. 礼部（规范制定）映射

| 三省六部角色 | Agency-Agent | 专业能力 | 调用场景 |
|-------------|--------------|----------|----------|
| 技术文档师 | Technical Writer | API文档、教程编写 | 文档生成、知识库建设 |
| UI设计师 | UI Designer | 设计系统、组件库 | UI规范制定 |
| UX架构师 | UX Architect | 技术架构、CSS系统 | 前端架构设计 |

### 4. 兵部（测试先行）映射

| 三省六部角色 | Agency-Agent | 专业能力 | 调用场景 |
|-------------|--------------|----------|----------|
| 测试工程师 | Evidence Collector | 视觉验证、截图QA | UI测试、视觉验证 |
| 质量保证师 | Reality Checker | 质量门禁、生产就绪 | 发布前验证 |
| 性能测试师 | Performance Benchmarker | 性能测试、负载测试 | 性能优化阶段 |
| API测试师 | API Tester | API验证、集成测试 | API测试 |
| 可访问性审计师 | Accessibility Auditor | WCAG审计、无障碍测试 | 可访问性合规 |

### 5. 刑部（持续重构）映射

| 三省六部角色 | Agency-Agent | 专业能力 | 调用场景 |
|-------------|--------------|----------|----------|
| 代码审查师 | Code Reviewer | 代码质量、安全审查 | PR审查、代码质量门禁 |
| 安全工程师 | Security Engineer | 威胁建模、安全架构 | 安全审计、漏洞评估 |
| Git工作流专家 | Git Workflow Master | 分支策略、提交规范 | 版本控制优化 |

### 6. 工部（开发执行）映射

| 三省六部角色 | Agency-Agent | 专业能力 | 调用场景 |
|-------------|--------------|----------|----------|
| 前端开发师 | Frontend Developer | React/Vue/Angular、UI实现 | 前端开发任务 |
| 后端架构师 | Backend Architect | API设计、数据库架构 | 后端开发任务 |
| 移动开发师 | Mobile App Builder | iOS/Android、React Native | 移动应用开发 |
| AI工程师 | AI Engineer | ML模型、AI集成 | AI功能开发 |
| 快速原型师 | Rapid Prototyper | MVP、POC开发 | 快速验证想法 |

## 二、TDD循环集成

### 红-绿-重构循环中的Agent调用

```
┌─────────────────────────────────────────────────────────────────┐
│                    TDD循环中的Agent调用                          │
│                                                                  │
│   ┌──────────┐                                                  │
│   │  红 🔴   │  兵部调用测试Agent                               │
│   │ 编写测试 │  ├─ Evidence Collector: 视觉测试用例             │
│   │          │  ├─ API Tester: API测试用例                      │
│   │          │  └─ Performance Benchmarker: 性能基准测试        │
│   └────┬─────┘                                                  │
│        │                                                        │
│        ▼                                                        │
│   ┌──────────┐                                                  │
│   │  绿 🟢   │  工部调用开发Agent                               │
│   │ 实现代码 │  ├─ Frontend Developer: 前端实现                 │
│   │          │  ├─ Backend Architect: 后端实现                  │
│   │          │  └─ Senior Developer: 复杂业务逻辑               │
│   └────┬─────┘                                                  │
│        │                                                        │
│        ▼                                                        │
│   ┌──────────┐                                                  │
│   │ 重构 🔵  │  刑部调用优化Agent                               │
│   │ 优化代码 │  ├─ Code Reviewer: 代码审查                      │
│   │          │  ├─ Security Engineer: 安全优化                  │
│   │          │  └─ Database Optimizer: 数据库优化               │
│   └────┬─────┘                                                  │
│        │                                                        │
│        └──────────────────────────────────┐                     │
│                                           │                     │
│                                           ▼                     │
│                                    下一轮循环                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 三、项目类型与Agent选择

### Web应用项目

| 项目阶段 | 推荐Agent组合 | 职责分工 |
|----------|---------------|----------|
| 需求分析 | Product Manager + UX Researcher | 需求收集、用户研究 |
| 架构设计 | Software Architect + Backend Architect | 系统设计、API设计 |
| 前端开发 | Frontend Developer + UI Designer | UI实现、设计系统 |
| 后端开发 | Backend Architect + Senior Developer | API实现、业务逻辑 |
| 测试验证 | Evidence Collector + API Tester | UI测试、API测试 |
| 部署上线 | DevOps Automator + SRE | CI/CD、监控告警 |

### 移动应用项目

| 项目阶段 | 推荐Agent组合 | 职责分工 |
|----------|---------------|----------|
| 需求分析 | Product Manager + UX Researcher | 需求分析、用户研究 |
| 设计阶段 | UI Designer + UX Architect | UI设计、交互设计 |
| 开发阶段 | Mobile App Builder + Senior Developer | 应用开发、业务逻辑 |
| 测试阶段 | Evidence Collector + Performance Benchmarker | 功能测试、性能测试 |
| 上线发布 | DevOps Automator | 应用商店发布 |

### AI/ML项目

| 项目阶段 | 推荐Agent组合 | 职责分工 |
|----------|---------------|----------|
| 需求分析 | Product Manager + AI Engineer | 需求定义、技术可行性 |
| 数据准备 | Data Engineer + AI Data Remediation Engineer | 数据管道、数据清洗 |
| 模型开发 | AI Engineer + Senior Developer | 模型训练、工程实现 |
| 测试验证 | Model QA Specialist + API Tester | 模型评估、API测试 |
| 部署监控 | DevOps Automator + SRE | 模型部署、性能监控 |

## 四、调用流程规范

### 1. Agent选择流程

```python
def select_agent(task_type, project_context):
    """
    根据任务类型和项目上下文选择合适的Agent
    
    Args:
        task_type: 任务类型（frontend/backend/testing等）
        project_context: 项目上下文信息
    
    Returns:
        推荐的Agent列表
    """
    # 1. 查询部门映射
    department = get_department_by_task(task_type)
    
    # 2. 获取可用Agent
    available_agents = get_available_agents(department)
    
    # 3. 根据项目上下文筛选
    matched_agents = filter_by_context(available_agents, project_context)
    
    # 4. 返回推荐Agent
    return matched_agents
```

## 2. Agent调用记录

```json
{
  "call_id": "CALL-001",
  "timestamp": "2026-03-27T10:30:00Z",
  "caller": "吏部",
  "agent": "Frontend Developer",
  "task": "实现用户登录界面",
  "context": {
    "project_type": "Web应用",
    "tech_stack": "Vue 3 + Element Plus",
    "tdd_phase": "绿"
  },
  "result": {
    "status": "success",
    "deliverables": [
      "LoginComponent.vue",
      "login.spec.ts"
    ],
    "quality_metrics": {
      "test_coverage": "85%",
      "performance_score": "95/100"
    }
  }
}
```

## 五、质量保障机制

### 1. Agent能力验证

| 验证项 | 验证方法 | 通过标准 |
|--------|----------|----------|
| 技术能力 | 代码质量检查 | 符合项目规范 |
| 沟通能力 | 文档完整性 | 清晰可理解 |
| 协作能力 | 集成测试 | 无冲突集成 |
| 学习能力 | 模式识别 | 持续改进 |

### 2. 集成监控指标

| 指标 | 目标值 | 监控方式 |
|------|--------|----------|
| Agent调用成功率 | ≥ 95% | 自动化监控 |
| 任务完成质量 | ≥ 90分 | 代码审查 |
| 响应时间 | ≤ 30秒 | 性能监控 |
| 集成错误率 | ≤ 5% | 错误日志 |

## 六、最佳实践

### 1. Agent组合原则

- **互补性**：选择能力互补的Agent组合
- **专业性**：优先选择专业领域匹配的Agent
- **协作性**：确保Agent之间可以顺畅协作
- **可追溯性**：记录所有Agent调用和决策过程

### 2. 冲突解决机制

当多个Agent给出不同建议时：
1. **技术决策**：由架构师Agent最终决策
2. **设计决策**：由UI/UX Designer最终决策
3. **质量决策**：由Reality Checker最终决策
4. **项目决策**：由Project Manager最终决策

### 3. 持续优化

- 定期评估Agent表现
- 收集使用反馈
- 更新映射关系
- 优化调用流程

## 七、扩展指南

### 添加新的Agent映射

1. 在对应部门配置中添加Agent定义
2. 定义Agent的专业能力和适用场景
3. 配置与其他Agent的协作关系
4. 添加到自动化调用流程
5. 更新文档和测试用例

### 自定义Agent行为

可以通过以下方式自定义Agent行为：
- 覆盖默认工作流程
- 添加项目特定的成功指标
- 配置特定的交付物模板
- 设置项目特定的约束条件

---

**维护者**: 三省六部技能团队  
**更新日期**: 2026-03-27  
**版本**: 1.0.0
