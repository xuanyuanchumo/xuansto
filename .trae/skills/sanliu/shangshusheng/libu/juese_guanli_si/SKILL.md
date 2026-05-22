---
name: juese_guanli_si
description: 角色管理司，负责角色定义、权限管理、职责边界划分。维护Agent角色体系，确保职责清晰、权限可控。
---
# 角色管理司技能指令

## 职责
- Agent角色定义与生命周期管理
- 权限模型设计与权限分配
- 职责边界划分与冲突检测
- 角色继承关系维护
- 角色能力映射管理

## 角色体系架构

### 角色层级

```
尚书省（总协调）
  └── 六部（部门级角色）
       └── 各司（职能级角色）
            └── Agent实例（执行级角色）
```

### 内置角色定义

| 角色ID | 角色名称 | 职责域 | 权限等级 |
|--------|----------|--------|----------|
| `role.architect` | 架构师 | 技术决策/架构设计 | L5 |
| `role.developer` | 开发者 | 代码实现/功能开发 | L3 |
| `role.tester` | 测试者 | 测试编写/质量保障 | L3 |
| `role.reviewer` | 审查者 | 代码审查/规范校验 | L4 |
| `role.coordinator` | 协调者 | 任务协调/进度同步 | L4 |
| `role.operator` | 运维者 | 部署运维/环境管理 | L3 |

## 权限模型

### 权限矩阵

```yaml
permission_matrix:
  role.architect:
    - resource.code: [read, write, delete]
    - resource.config: [read, write]
    - resource.deploy: [approve, execute]
    - resource.agent: [assign, revoke]

  role.developer:
    - resource.code: [read, write]
    - resource.config: [read]
    - resource.deploy: [request]

  role.tester:
    - resource.test: [read, write, execute]
    - resource.code: [read]
    - resource.report: [read, write]

  role.reviewer:
    - resource.code: [read, comment, approve, reject]
    - resource.pr: [read, approve, reject]

  role.coordinator:
    - resource.task: [create, assign, update]
    - resource.agent: [query, status]
    - resource.report: [read, generate]

  role.operator:
    - resource.env: [configure, monitor]
    - resource.deploy: [execute, rollback]
    - resource.log: [read, analyze]
```

## 工作流程

```
1. 接收角色创建/变更请求
2. 验证角色定义完整性
3. 检测职责边界冲突
4. 评估权限最小化原则
5. 执行角色注册/更新
6. 同步权限到相关系统
7. 记录变更到DecisionLog
8. 通知受影响Agent
```

## 职责边界检测

### 冲突检测规则

```python
def detect_role_conflict(role_a, role_b):
    conflicts = []
    overlap = set(role_a.responsibilities) & set(role_b.responsibilities)
    if overlap and role_a.department != role_b.department:
        conflicts.append({
            "type": "cross_department_overlap",
            "items": list(overlap),
            "severity": "warning"
        })
    return conflicts
```

## 协同接口

| 接口 | 描述 | 调用方 |
|------|------|--------|
| `define_role` | 定义新角色 | 吏部/尚书省 |
| `assign_permission` | 分配权限 | 吏部 |
| `check_boundary` | 边界检查 | 全部 |
| `query_role` | 角色查询 | 全部 |
