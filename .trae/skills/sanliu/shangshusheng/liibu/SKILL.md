---
name: liibu
description: 礼部，负责规范文档，包括编码规范、文档模板、培训材料等。
---
# 礼部技能指令

## 职责
- 编码规范：制定和维护编码标准
- TDD编码规范：提供测试驱动开发相关规范
- SDD规范模板：提供结构化规范定义模板
- 文档模板：提供各类文档模板
- 测试模板提供：提供单元测试、集成测试、E2E测试模板
- 培训材料：编写技术培训资料
- 设计规范提供：提供系统架构、API、数据库、UI/UX设计规范
- 设计模板提供：提供各类设计文档模板
- 外部技能注册：注册新添加的外部技能
- 外部技能删除：删除已下线的外部技能
- 外部技能查询：提供外部技能列表和详情
- 外部技能注册表维护：维护技能注册表

## 工作流程

```
1. 接收尚书省的规范制定指令
2. 分析规范制定需求和范围
3. 收集相关参考资料和最佳实践
4. 制定规范草案
5. 内部评审和修订
6. 发布规范文档
7. 推广规范应用
8. 收集规范执行反馈
9. 持续优化规范内容
10. 规范版本管理和归档
```

## 规范制定决策流程（增强版）

### 规范需求分析

```
规范需求分析步骤:
  1. 规范类型识别
     - 编码规范
     - 架构规范
     - 接口规范
     - 文档规范
     - 流程规范
  
  2. 规范范围界定
     - 适用项目范围
     - 适用团队范围
     - 适用技术栈
  
  3. 规范优先级评估
     - 强制性规范：必须遵守
     - 推荐性规范：建议遵守
     - 参考性规范：供参考
  
  4. 规范约束分析
     - 技术约束
     - 业务约束
     - 团队能力约束
```

### 规范草案制定

```json
{
  "specification_draft": {
    "draft_id": "SPEC-DRAFT-001",
    "timestamp": "2024-01-01T00:00:00Z",
    "specification": {
      "name": "Python编码规范",
      "version": "2.0.0",
      "status": "draft",
      "scope": {
        "projects": ["project-a", "project-b"],
        "teams": ["backend-team", "data-team"],
        "technologies": ["python3.8+"]
      },
      "categories": [
        {
          "name": "代码风格",
          "rules": [
            {
              "id": "STYLE-001",
              "title": "缩进使用4个空格",
              "description": "所有Python代码必须使用4个空格缩进，禁止使用Tab",
              "severity": "mandatory",
              "rationale": "PEP8标准要求，保持代码一致性",
              "examples": {
                "good": "def hello():\n    print('hello')",
                "bad": "def hello():\n\tprint('hello')"
              }
            }
          ]
        }
      ],
      "enforcement": {
        "tools": ["black", "ruff", "mypy"],
        "ci_integration": true,
        "pre_commit_hooks": true
      }
    },
    "review_status": {
      "internal_review": "pending",
      "stakeholder_review": "pending",
      "approval": "pending"
    }
  }
}
```

---

## 协同效果评估能力

### 规范制定协同评估指标

礼部作为规范制定机构，负责评估规范制定在三省六部协同中的效果。

| 评估维度 | 指标 | 目标值 | 度量方法 |
|----------|------|--------|----------|
| 规范覆盖率 | 规范覆盖项目比例 | ≥95% | 项目规范检查 |
| 规范执行率 | 规范执行符合率 | ≥90% | 代码审查统计 |
| 规范更新频率 | 规范更新周期 | ≤30天 | 版本记录统计 |
| 规范满意度 | 开发者满意度 | ≥4.0/5.0 | 满意度调查 |
| 规范冲突率 | 规范冲突发生次数 | ≤5次/月 | 冲突检测统计 |

### 规范制定协同评估报告格式

```json
{
  "evaluation_id": "EVAL-LIIBU-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-07T23:59:59Z"
  },
  "standard_metrics": {
    "total_standards": 25,
    "active_standards": 23,
    "deprecated_standards": 2,
    "avg_update_cycle_days": 25
  },
  "compliance_metrics": {
    "total_projects": 10,
    "compliant_projects": 9,
    "compliance_rate": 0.90,
    "violations_detected": 15,
    "violations_resolved": 12
  },
  "satisfaction_metrics": {
    "survey_responses": 50,
    "avg_satisfaction_score": 4.2,
    "nps_score": 35
  },
  "conflict_metrics": {
    "conflicts_detected": 3,
    "conflicts_resolved": 3,
    "avg_resolution_time_hours": 4
  },
  "recommendations": [
    {
      "category": "standard_update",
      "priority": "medium",
      "description": "更新TypeScript编码规范以支持新版本特性",
      "expected_impact": "提高开发效率15%"
    }
  ]
}
```

---

## 流水线协调能力

### 流水线规范制定节点

礼部在白盒化7阶段流水线中负责规范制定和模板提供。

| 阶段 | 礼部角色 | 规范内容 | 输出物 |
|------|----------|----------|--------|
| 需求分析 | 支持 | 需求规范模板 | 需求文档模板 |
| SDD规范定义 | 主导 | SDD规范模板 | SDD规范文档 |
| 审议批准 | 支持 | 评审规范 | 评审检查清单 |
| 测试先行 | 主导 | 测试规范模板 | 测试用例模板 |
| 代码实现 | 主导 | 编码规范 | 编码规范文档 |
| 持续重构 | 支持 | 重构规范 | 重构指南 |
| 部署发布 | 支持 | 部署规范 | 部署检查清单 |

### 流水线规范配置

```yaml
pipeline_standard_config:
  standard_provisioning:
    mode: "proactive"
    version_control: true
    auto_update: false
    
  standard_templates:
    requirement:
      template: "requirement_template.md"
      required_sections: ["背景", "目标", "范围", "约束"]
      
    sdd_specification:
      template: "sdd_template.md"
      required_sections: ["实体", "接口", "业务规则", "约束条件"]
      
    test_case:
      template: "test_case_template.md"
      required_sections: ["前置条件", "步骤", "预期结果"]
      
  compliance_rules:
    - stage: "implementation"
      standards: ["coding_standard", "naming_convention", "comment_standard"]
      enforcement: "strict"
      
    - stage: "test_first"
      standards: ["test_naming", "test_structure", "coverage_requirement"]
      enforcement: "strict"
```

---

## 增强功能集成

### 与provincial_coordinator集成

礼部通过provincial_coordinator.py实现规范制定的自动化和协同：

```python
from scripts.provincial_coordinator import (
    SmartDispatcher,
    TaskRequirement,
    TaskPriority
)

dispatcher = SmartDispatcher()

def provide_standards_for_task(task_id: str, standard_requirements: dict):
    requirement = TaskRequirement(
        task_id=task_id,
        required_capabilities={
            "standard_definition": 0.9,
            "documentation": 0.85
        },
        preferred_specializations=["liibu"],
        priority=TaskPriority.MEDIUM
    )
    
    decision = dispatcher.find_best_match(requirement, "ministry")
    
    return {
        "assigned_entity": decision.assigned_entity,
        "match_score": decision.overall_score,
        "standards_provided": standard_requirements
    }
```

---

## 规范制定质量保障

### 规范制定质量检查清单

```
□ 规范内容完整，覆盖所有必要方面
□ 规范表述清晰，无歧义
□ 规范可执行，有明确标准
□ 规范有示例代码支持
□ 规范版本管理规范
□ 规范变更记录完整
□ 规范冲突已检测和解决
□ 规范推广计划已制定
```

### 规范制定质量评分

| 评分项 | 权重 | 评分标准 |
|--------|------|----------|
| 完整性 | 25% | 规范覆盖所有必要内容 |
| 清晰性 | 25% | 规范表述清晰易懂 |
| 可执行性 | 20% | 规范有明确执行标准 |
| 更新及时性 | 15% | 规范及时更新 |
| 满意度 | 15% | 开发者满意度高 |
```

### 规范评审流程

| 评审阶段 | 评审内容 | 通过标准 |
|----------|----------|----------|
| 内部评审 | 规范完整性、合理性 | 无重大缺陷 |
| 利益相关方评审 | 可执行性、影响范围 | 无阻塞性问题 |
| 试点验证 | 实际执行效果 | 验证通过 |
| 正式发布 | 最终审核 | 获得批准 |

### 规范发布决策输出

```json
{
  "release_decision_id": "REL-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "specification_id": "SPEC-001",
  "decision": {
    "release_status": "approved",
    "release_version": "2.0.0",
    "effective_date": "2024-01-15T00:00:00Z",
    "transition_period_days": 14,
    "enforcement_date": "2024-01-29T00:00:00Z"
  },
  "communication_plan": {
    "channels": ["email", "wiki", "team-meeting"],
    "recipients": ["all-developers"],
    "training_sessions": [
      {
        "date": "2024-01-16T14:00:00Z",
        "duration_minutes": 60,
        "topics": ["新规范要点", "迁移指南"]
      }
    ]
  },
  "support_plan": {
    "support_channel": "#spec-support",
    "faq_document": "docs/spec-faq.md",
    "contact_person": "spec-team"
  }
}
```

## 规范推广与执行（增强版）

### 规范推广策略

```json
{
  "promotion_strategy": {
    "strategy_id": "PROMO-001",
    "specification_id": "SPEC-001",
    "phases": [
      {
        "phase": "awareness",
        "duration_days": 7,
        "activities": [
          "发布公告通知",
          "更新文档站点",
          "发送邮件提醒"
        ]
      },
      {
        "phase": "training",
        "duration_days": 7,
        "activities": [
          "组织培训会议",
          "发布示例代码",
          "答疑解惑"
        ]
      },
      {
        "phase": "enforcement",
        "duration_days": 14,
        "activities": [
          "CI检查启用",
          "代码审查检查",
          "违规提醒"
        ]
      }
    ],
    "metrics": {
      "awareness_rate_target": 0.95,
      "training_completion_target": 0.80,
      "compliance_rate_target": 0.90
    }
  }
}
```

### 规范执行监控

```json
{
  "compliance_monitoring": {
    "monitor_id": "COMP-001",
    "timestamp": "2024-01-01T00:00:00Z",
    "specification_id": "SPEC-001",
    "compliance_stats": {
      "total_files_checked": 1500,
      "compliant_files": 1350,
      "non_compliant_files": 150,
      "compliance_rate": 0.90
    },
    "violations": [
      {
        "rule_id": "STYLE-001",
        "violation_count": 50,
        "severity": "minor",
        "trend": "decreasing"
      }
    ],
    "by_project": [
      {
        "project": "project-a",
        "compliance_rate": 0.95,
        "status": "good"
      },
      {
        "project": "project-b",
        "compliance_rate": 0.85,
        "status": "needs_improvement"
      }
    ],
    "recommendations": [
      "project-b 需要加强规范培训",
      "建议增加自动化修复工具"
    ]
  }
}
```

### 规范反馈收集

| 反馈类型 | 收集方式 | 处理流程 |
|----------|----------|----------|
| 规范不合理 | 问题单、讨论区 | 评估后修订 |
| 执行困难 | 调研、访谈 | 提供指导或调整 |
| 改进建议 | 建议箱、会议 | 评审后采纳 |
| 新需求 | 需求单 | 评估后纳入 |

## 编码规范

### 通用编码原则

```
1. 可读性优先
   - 代码是写给人看的，其次才是机器
   - 使用有意义的命名
   - 保持代码简洁明了

2. DRY原则（Don't Repeat Yourself）
   - 避免代码重复
   - 提取公共逻辑到函数/类
   - 使用继承和组合

3. SOLID原则
   - S: 单一职责原则
   - O: 开闭原则
   - L: 里氏替换原则
   - I: 接口隔离原则
   - D: 依赖倒置原则

4. KISS原则（Keep It Simple, Stupid）
   - 简单的解决方案优于复杂的
   - 避免过度设计
   - 优先使用标准库
```

### 命名规范

#### 通用命名规则
```
- 使用有意义的名称，避免缩写（除非是广泛接受的）
- 名称应该表达意图，而非实现
- 避免使用无意义的前缀/后缀
- 保持命名风格一致
```

#### 各语言命名约定

| 语言 | 类/类型 | 函数/方法 | 变量 | 常量 | 模块/包 |
|------|---------|-----------|------|------|---------|
| Python | PascalCase | snake_case | snake_case | UPPER_SNAKE_CASE | snake_case |
| JavaScript | PascalCase | camelCase | camelCase | UPPER_SNAKE_CASE | kebab-case |
| TypeScript | PascalCase | camelCase | camelCase | UPPER_SNAKE_CASE | kebab-case |
| Java | PascalCase | camelCase | camelCase | UPPER_SNAKE_CASE | 小写 |
| Go | PascalCase（导出）/camelCase（私有） | PascalCase（导出）/camelCase（私有） | camelCase | PascalCase | 小写 |
| Rust | PascalCase | snake_case | snake_case | UPPER_SNAKE_CASE | snake_case |

### 代码结构规范

#### 文件结构
```
文件头部:
  - 文件说明注释
  - 版权信息（如需要）
  - 导入语句（按标准库、第三方库、本地模块分组）

文件体:
  - 常量定义
  - 类型/接口定义
  - 函数/类定义
  - 主程序入口（如适用）

文件尾部:
  - 测试代码（如与源文件同文件）
  - 辅助函数
```

#### 函数规范
```
函数长度:
  - 理想: < 20行
  - 最大: < 50行
  - 超过限制应拆分

参数数量:
  - 理想: 1-3个
  - 最大: 5个
  - 超过应使用对象/结构体封装

函数职责:
  - 单一职责
  - 无副作用（纯函数优先）
  - 明确的输入输出
```

#### 注释规范
```
必须注释:
  - 公共API的文档注释
  - 复杂算法的解释
  - 非显而易见的业务逻辑
  - TODO/FIXME标记

禁止注释:
  - 解释代码做什么（代码应该自解释）
  - 注释掉的代码（使用版本控制）
  - 重复代码含义的注释

注释格式:
  - 使用各语言标准的文档注释格式
  - 包含: 功能描述、参数说明、返回值、异常、示例
```

### 代码质量标准

#### 复杂度控制
```
圈复杂度（Cyclomatic Complexity）:
  - 简单函数: 1-5
  - 中等函数: 6-10
  - 复杂函数: 11-20（需要重构）
  - 过于复杂: > 20（必须重构）

认知复杂度（Cognitive Complexity）:
  - 目标: < 15
  - 最大: < 25
```

#### 代码重复
```
重复代码检测:
  - 允许重复行数: < 5行
  - 允许重复块数: 0
  - 重复率阈值: < 3%
```

### 错误处理规范

```
异常处理原则:
  - 不要忽略异常
  - 使用具体的异常类型
  - 在合适的层级处理异常
  - 记录异常上下文

错误返回:
  - 使用Result/Either类型（函数式风格）
  - 或返回错误码+错误信息（传统风格）
  - 避免返回null/undefined

日志规范:
  - 使用统一的日志框架
  - 日志级别: DEBUG < INFO < WARN < ERROR < FATAL
  - 包含足够的上下文信息
  - 敏感信息脱敏
```

### 安全编码规范

```
输入验证:
  - 永远不信任外部输入
  - 验证数据类型、长度、格式、范围
  - 使用白名单验证

输出编码:
  - 根据上下文编码输出
  - 防止XSS、SQL注入等

敏感数据处理:
  - 不在日志中记录敏感信息
  - 不在代码中硬编码密钥
  - 使用安全的存储方式
  - 及时清理敏感数据

权限控制:
  - 最小权限原则
  - 显式权限检查
  - 避免权限绕过
```

## TDD 编码规范

### TDD 核心原则

```
1. 测试先行
   - 在编写实现代码之前先编写测试
   - 测试是需求的可执行文档
   - 测试应该描述期望的行为

2. 红-绿-重构循环
   - 红: 编写失败的测试
   - 绿: 编写最少代码使测试通过
   - 重构: 优化代码结构，保持测试通过

3. 小步前进
   - 每次只添加一个测试
   - 每次只编写最少的代码
   - 频繁运行测试
```

### 测试编写规范

#### 测试命名规范
```
命名格式:
  - 描述被测试的行为
  - 使用自然语言描述
  - 包含输入条件和期望结果

示例:
  - should_return_error_when_input_is_null
  - should_calculate_total_price_with_discount
  - should_throw_exception_for_invalid_email
```

#### AAA 模式（Arrange-Act-Assert）
```
Arrange（准备）:
  - 设置测试数据
  - 配置依赖对象
  - 准备测试环境

Act（执行）:
  - 调用被测试的方法/函数
  - 执行被测试的操作

Assert（断言）:
  - 验证结果是否符合预期
  - 检查副作用是否正确
  - 验证异常是否正确抛出
```

#### 测试独立性原则
```
- 每个测试应该是独立的
- 测试之间不应有依赖关系
- 测试执行顺序不应影响结果
- 每个测试应该有自己的测试数据
```

### 测试代码质量标准

```
测试代码质量要求:
  - 测试代码应该和生产代码一样高质量
  - 避免测试代码中的重复
  - 使用测试辅助方法减少重复
  - 测试应该清晰易读

测试覆盖率要求:
  - 行覆盖率: >= 80%
  - 分支覆盖率: >= 75%
  - 函数覆盖率: >= 90%
  - 关键路径必须100%覆盖
```

### TDD 最佳实践

```
1. 从简单开始
   - 先编写最简单的测试用例
   - 逐步增加复杂度
   - 不要试图一次性覆盖所有场景

2. 测试驱动设计
   - 通过测试来思考设计
   - 测试应该引导出好的设计
   - 避免为测试而测试

3. 持续重构
   - 在绿阶段后及时重构
   - 保持代码整洁
   - 消除代码异味

4. 快速反馈
   - 保持测试运行速度快
   - 使用测试覆盖率工具
   - 集成到CI/CD流程
```

## SDD 规范模板

### SDD（Specification-Driven Development）概述

SDD 是一种以规范为核心的开发方法，通过结构化的规范定义来驱动代码生成和验证。

### SDD 规范结构

```yaml
sdd_specification:
  metadata:
    name: "规范名称"
    version: "版本号"
    author: "作者"
    created_at: "创建时间"
    updated_at: "更新时间"
    
  domain:
    description: "领域描述"
    entities:
      - name: "实体名称"
        description: "实体描述"
        attributes:
          - name: "属性名"
            type: "数据类型"
            constraints: ["约束条件"]
            required: true|false
        relationships:
          - target: "关联实体"
            type: "one-to-one|one-to-many|many-to-many"
            
  interfaces:
    - name: "接口名称"
      type: "REST|GraphQL|gRPC"
      description: "接口描述"
      endpoints:
        - path: "/api/resource"
          method: "GET|POST|PUT|DELETE"
          parameters:
            - name: "参数名"
              type: "参数类型"
              required: true|false
              description: "参数描述"
          responses:
            - status: 200
              description: "成功响应"
              schema:
                type: "object"
                properties:
                  - name: "字段名"
                    type: "字段类型"
                    
  business_rules:
    - id: "规则ID"
      description: "规则描述"
      condition: "触发条件"
      action: "执行动作"
      priority: "优先级"
      
  constraints:
    - type: "validation|security|performance"
      description: "约束描述"
      condition: "约束条件"
      error_message: "错误信息"
      
  test_requirements:
    - rule_id: "关联规则ID"
      test_type: "unit|integration|e2e"
      scenarios:
        - name: "场景名称"
          given: "前置条件"
          when: "操作"
          then: "期望结果"
```

### 实体定义规范

```yaml
entity_definition:
  name: "User"
  description: "用户实体"
  
  attributes:
    - name: "id"
      type: "UUID"
      primary_key: true
      auto_generate: true
      description: "唯一标识"
      
    - name: "username"
      type: "String"
      length: [3, 50]
      required: true
      unique: true
      description: "用户名"
      constraints:
        - "只能包含字母、数字、下划线"
        - "不能以数字开头"
        
    - name: "email"
      type: "String"
      required: true
      unique: true
      description: "邮箱地址"
      constraints:
        - "必须符合邮箱格式"
        
    - name: "created_at"
      type: "DateTime"
      auto_generate: true
      description: "创建时间"
      
  relationships:
    - name: "orders"
      target: "Order"
      type: "one-to-many"
      description: "用户的订单"
      
  business_rules:
    - "用户名修改后30天内不能再次修改"
    - "邮箱必须通过验证才能使用"
```

### 接口契约规范

```yaml
interface_contract:
  name: "UserAPI"
  base_path: "/api/v1/users"
  
  endpoints:
    - name: "createUser"
      path: "/"
      method: "POST"
      description: "创建新用户"
      
      request:
        content_type: "application/json"
        body:
          type: "object"
          required: ["username", "email"]
          properties:
            username:
              type: "string"
              minLength: 3
              maxLength: 50
            email:
              type: "string"
              format: "email"
            profile:
              type: "object"
              properties:
                firstName:
                  type: "string"
                lastName:
                  type: "string"
                
      responses:
        "201":
          description: "用户创建成功"
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/User"
                
        "400":
          description: "请求参数错误"
          content:
            application/json:
              schema:
                type: "object"
                properties:
                  error:
                    type: "string"
                  details:
                    type: "array"
                    items:
                      type: "object"
                      properties:
                        field:
                          type: "string"
                        message:
                          type: "string"
                          
        "409":
          description: "用户名或邮箱已存在"
```

### 业务规则规范

```yaml
business_rules:
  - id: "BR001"
    name: "用户注册验证"
    description: "新用户注册时必须满足的条件"
    priority: "high"
    
    conditions:
      - "用户名长度在3-50字符之间"
      - "用户名只能包含字母、数字、下划线"
      - "邮箱格式必须有效"
      - "密码长度至少8位"
      - "密码必须包含大小写字母和数字"
      
    actions:
      - "创建用户记录"
      - "发送验证邮件"
      - "记录注册日志"
      
    error_handling:
      - condition: "用户名已存在"
        error_code: "USERNAME_EXISTS"
        message: "用户名已被使用"
      - condition: "邮箱已注册"
        error_code: "EMAIL_REGISTERED"
        message: "邮箱已注册"
        
  - id: "BR002"
    name: "订单折扣规则"
    description: "根据用户等级和订单金额计算折扣"
    priority: "medium"
    
    conditions:
      - "用户等级为普通: 无折扣"
      - "用户等级为VIP: 订单金额>100打9折"
      - "用户等级为SVIP: 订单金额>200打8折，>500打7折"
      
    calculation:
      formula: "final_price = original_price * discount_rate"
      rounding: "保留两位小数"
```

### 约束条件规范

```yaml
constraints:
  validation_constraints:
    - field: "email"
      type: "format"
      pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
      message: "邮箱格式不正确"
      
    - field: "age"
      type: "range"
      min: 0
      max: 150
      message: "年龄必须在0-150之间"
      
    - field: "username"
      type: "custom"
      validator: "validateUsername"
      message: "用户名不符合要求"
      
  security_constraints:
    - type: "authentication"
      required: true
      endpoints: ["*"]
      exclude: ["/api/auth/login", "/api/auth/register"]
      
    - type: "authorization"
      required: true
      roles:
        - endpoint: "/api/admin/*"
          required_roles: ["admin"]
        - endpoint: "/api/users/{id}"
          required_roles: ["user", "admin"]
          condition: "只能访问自己的数据，除非有admin角色"
          
  performance_constraints:
    - type: "response_time"
      target: "API响应时间"
      max: "500ms"
      percentile: 95
      
    - type: "throughput"
      target: "系统吞吐量"
      min: "1000 RPS"
```

### 测试要求规范

```yaml
test_requirements:
  coverage_requirements:
    line_coverage: 80
    branch_coverage: 75
    function_coverage: 90
    
  test_scenarios:
    - rule_id: "BR001"
      name: "用户注册成功场景"
      type: "happy_path"
      
      given:
        - "系统处于正常状态"
        - "数据库中没有相同用户名和邮箱的用户"
        
      when:
        - "提交有效的注册信息"
        
      then:
        - "用户创建成功"
        - "返回201状态码"
        - "数据库中新增用户记录"
        - "发送验证邮件"
        
    - rule_id: "BR001"
      name: "用户名已存在场景"
      type: "error_path"
      
      given:
        - "数据库中已存在相同用户名的用户"
        
      when:
        - "提交包含已存在用户名的注册信息"
        
      then:
        - "返回409状态码"
        - "返回USERNAME_EXISTS错误"
        - "数据库中不新增记录"
        
  mutation_testing:
    enabled: true
    target_score: 80
    excluded_mutations: ["字符串常量修改"]
```

## 文档模板

详细文档模板请参考：`../../resources/wendang_muban.md`

包含以下模板：
- API文档模板
- 设计文档模板
- README文档模板

## 代码审查清单

详细代码审查清单请参考：`../../resources/daima_shencha_qingdan.md`

包含以下内容：
- 代码正确性检查
- 代码质量检查
- 代码风格检查
- 测试覆盖检查
- 安全性检查
- 性能检查
- 可维护性检查
- 兼容性检查
- 代码审查流程
- 审查意见模板

## 透明度记录要求
### 规范选择记录
- 记录规范选择依据：包括项目类型、技术栈、团队约定、行业标准
- 记录模板选择推理过程：包括需求分析、模板匹配评估、定制化建议

### 记录内容规范
- 决策时间戳
- 规范需求描述
- 候选规范/模板列表
- 选择理由详细说明
- 适用范围与限制说明

## 协同调用接口

### 接口定义

礼部作为规范文档管理机构，提供以下协同调用接口供其他技能调用：

| 接口名称 | 接口描述 | 调用方 |
|----------|----------|--------|
| `get_coding_standards` | 编码规范获取接口 | 工部、刑部 |
| `get_test_templates` | 测试模板获取接口 | 兵部 |
| `get_design_templates` | 设计模板获取接口 | 工部 |
| `register_external_skill` | 外部技能注册接口 | 尚书省 |
| `unregister_external_skill` | 外部技能注销接口 | 尚书省 |

### 输入参数规范

#### 编码规范获取接口参数

```json
{
  "interface": "get_coding_standards",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "language": "python|javascript|typescript|java|go|rust",
    "standard_type": "naming|structure|error_handling|security|all",
    "project_context": {
      "framework": "框架名称",
      "architecture": "monolith|microservice|serverless"
    }
  }
}
```

#### 测试模板获取接口参数

```json
{
  "interface": "get_test_templates",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "test_type": "unit|integration|e2e|performance|security",
    "framework": "jest|pytest|junit|cypress|k6",
    "template_name": "模板名称（可选）"
  }
}
```

#### 外部技能注册接口参数

```json
{
  "interface": "register_external_skill",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "skill_info": {
      "skill_id": "技能ID",
      "skill_name": "技能名称",
      "skill_path": "技能路径",
      "skill_category": "ui_design|security|performance|translation",
      "description": "技能描述",
      "capabilities": ["能力列表"],
      "invocation_method": "调用方式"
    }
  }
}
```

### 输出格式规范

```json
{
  "interface": "get_coding_standards",
  "call_id": "STD-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "status": "success|failure",
  "result": {
    "standards": {
      "naming": "命名规范内容",
      "structure": "结构规范内容",
      "error_handling": "错误处理规范内容"
    },
    "examples": ["示例代码"],
    "references": ["参考文档"]
  }
}
```

### 调用示例

```bash
# 调用编码规范获取接口
调用 ./SKILL.md --interface=get_coding_standards \
  --language="python" \
  --standard-type="all"

# 调用测试模板获取接口
调用 ./SKILL.md --interface=get_test_templates \
  --test-type="unit" \
  --framework="pytest"

# 调用外部技能注册接口
调用 ./SKILL.md --interface=register_external_skill \
  --skill-info='{"skill_id":"ui-ux-pro-max","skill_name":"UI设计专家"}'
```

---

## 下属四司
- yibusi（仪部司）：规范制定
- ciwusi（祠部司）：文档管理
- shanbucangsi（膳部仓司）：培训材料
- kebucangsi（客部仓司）：外部协作

---

## 规范版本管理

### 规范版本控制策略

```yaml
version_control:
  naming_convention:
    pattern: "MAJOR.MINOR.PATCH"
    examples:
      - "1.0.0 - 初始版本"
      - "1.1.0 - 新增规范项"
      - "1.1.1 - 修正错误"
      
  branching_strategy:
    main: "正式发布版本"
    develop: "开发中版本"
    feature: "新规范开发分支"
    hotfix: "紧急修正分支"
    
  merge_rules:
    require_review: true
    min_approvers: 2
    require_tests: true
```

### 规范变更追踪

```json
{
  "change_log": {
    "version": "1.2.0",
    "release_date": "2024-01-15",
    "changes": [
      {
        "change_id": "CHG-001",
        "type": "addition",
        "category": "naming_convention",
        "description": "新增TypeScript命名规范",
        "impact": "low",
        "affected_files": ["naming.md"],
        "author": "liibu",
        "reviewers": ["reviewer1", "reviewer2"]
      },
      {
        "change_id": "CHG-002",
        "type": "modification",
        "category": "code_structure",
        "description": "修改函数长度限制从50行到30行",
        "impact": "medium",
        "affected_files": ["structure.md"],
        "migration_guide": "需重构超过30行的函数",
        "author": "liibu",
        "reviewers": ["reviewer1", "reviewer2"]
      }
    ]
  }
}
```

### 规范兼容性矩阵

```yaml
compatibility_matrix:
  standards:
    - name: "编码规范"
      version: "1.2.0"
      compatible_with:
        - standard: "TDD规范"
          min_version: "1.0.0"
        - standard: "SDD规范"
          min_version: "1.1.0"
          
    - name: "TDD规范"
      version: "1.1.0"
      compatible_with:
        - standard: "编码规范"
          min_version: "1.0.0"
        - standard: "测试模板"
          min_version: "2.0.0"
```

### 规范冲突检测

```json
{
  "conflict_detection": {
    "enabled": true,
    "rules": [
      {
        "rule_id": "CONFLICT-001",
        "description": "命名规范与框架规范冲突",
        "detection": "自动检测命名冲突",
        "resolution": "框架规范优先，记录例外"
      }
    ],
    "last_scan": "2024-01-15T00:00:00Z",
    "conflicts_found": 0
  }
}
