# API文档目录

此目录用于存储API接口文档。

## 目录用途

- 存储REST API接口文档
- 存储API使用说明和示例
- 存储接口变更日志

## 文档规范

建议使用以下格式：
- OpenAPI/Swagger 规范
- Markdown 格式的接口说明
- 包含请求/响应示例

---

## 📚 v3.1.0 API端点总览（31个）

### 核心管理API（10个）
| 端点文件 | 功能说明 | 路径前缀 |
|---------|---------|---------|
| [projects.py](../../../backend/app/api/projects.py) | 项目管理 | `/api/projects` |
| [tasks.py](../../../backend/app/api/tasks.py) | 任务管理 | `/api/tasks` |
| [agents.py](../../../backend/app/api/agents.py) | Agent管理 | `/api/agents` |
| [departments.py](../../../backend/app/api/departments.py) | 部门管理 | `/api/departments` |
| [assignments.py](../../../backend/app/api/assignments.py) | 任务分配 | `/api/assignments` |
| [milestones.py](../../../backend/app/api/milestones.py) | 里程碑管理 | `/api/milestones` |
| [skill_calls.py](../../../backend/app/api/skill_calls.py) | 技能调用记录 | `/api/skill-calls` |
| [workflow.py](../../../backend/app/api/workflow.py) | 工作流管理 | `/api/workflow` |
| [dashboard.py](../../../backend/app/api/dashboard.py) | 仪表盘数据 | `/api/dashboard` |
| [statistics.py](../../../backend/app/api/statistics.py) | 统计数据 | `/api/statistics` |

### 质量与监控API（6个）
| 端点文件 | 功能说明 | 路径前缀 |
|---------|---------|---------|
| [quality_monitor.py](../../../backend/app/api/quality_monitor.py) | 质量监控 | `/api/quality` |
| [reports.py](../../../backend/app/api/reports.py) | 报告生成 | `/api/reports` |
| [pipeline.py](../../../backend/app/api/pipeline.py) | 流水线管理 | `/api/pipeline` |
| [evolution_monitor.py](../../../backend/app/api/evolution_monitor.py) | 演化监控 | `/api/evolution/monitor` |
| [skill_health.py](../../../backend/app/api/skill_health.py) | 技能健康检查 | `/api/skill-health` |
| [path_validation.py](../../../backend/app/api/path_validation.py) | 路径验证 | `/api/path-validation` |

### 透明度与追溯API（6个）
| 端点文件 | 功能说明 | 路径前缀 |
|---------|---------|---------|
| [transparency.py](../../../backend/app/api/transparency.py) | 透明度数据 | `/api/transparency` |
| [decision_logs.py](../../../backend/app/api/decision_logs.py) | 决策日志 | `/api/decision-logs` |
| [input_output_traces.py](../../../backend/app/api/input_output_traces.py) | 输入输出追溯 | `/api/traces` |
| [code_changes.py](../../../backend/app/api/code_changes.py) | 代码变更记录 | `/api/code-changes` |
| [artifacts.py](../../../backend/app/api/artifacts.py) | 产物管理 | `/api/artifacts` |
| [requirement_traces.py](../../../backend/app/api/requirement_traces.py) | 需求追溯 | `/api/requirement-traces` |

### 测试与安全API（5个）
| 端点文件 | 功能说明 | 路径前缀 |
|---------|---------|---------|
| [acceptance_tests.py](../../../backend/app/api/acceptance_tests.py) | 验收测试 | `/api/acceptance-tests` |
| [mutation_tests.py](../../../backend/app/api/mutation_tests.py) | 变异测试 | `/api/mutation-tests` |
| [non_functional_checks.py](../../../backend/app/api/non_functional_checks.py) | 非功能检查 | `/api/non-functional` |
| [clarification_questions.py](../../../backend/app/api/clarification_questions.py) | 澄清问题 | `/api/clarifications` |
| [human_approvals.py](../../../backend/app/api/human_approvals.py) | 人工审批 | `/api/approvals` |

### 演化与知识API（3个）
| 端点文件 | 功能说明 | 路径前缀 |
|---------|---------|---------|
| [skill_evolution_api.py](../../../backend/app/api/skill_evolution_api.py) | 技能演化 | `/api/evolution` |
| [evolution_knowledge.py](../../../backend/app/api/evolution_knowledge.py) | 演化知识库 | `/api/evolution/knowledge` |
| [exceptions.py](../../../backend/app/api/exceptions.py) | 异常处理 | - |

### 实时通信API（1个）
| 端点文件 | 功能说明 | 路径前缀 |
|---------|---------|---------|
| [ws.py](../../../backend/app/api/ws.py) | WebSocket实时通信 | `/ws` |

---

## 🔗 快速访问

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 📖 使用示例

```bash
# 获取所有项目
curl http://localhost:8000/api/projects

# 创建新任务
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "新任务", "project_id": 1}'

# 查看质量报告
curl http://localhost:8000/api/reports/quality

# WebSocket连接
ws://localhost:8000/ws
```

---

**最后更新**: 2026-04-01
**版本**: v3.1.0
**API总数**: 31个端点
