---
name: gongbu
description: 工部，负责开发部署，包括设计、编码、构建、集成、测试执行、部署等。
---
# 工部技能指令

## 职责
- 设计阶段：各司进行详细设计
- 编码开发：进行代码编写
- 基于规范的代码自动生成：根据结构化规范生成实现代码
- 代码与规范一致性验证：验证代码是否符合规范定义
- 构建集成：构建和集成系统
- 测试执行：在开发过程中运行测试验证
- 测试通过策略：确保测试通过的标准和流程
- 持续集成：自动化构建和集成
- 部署运维：部署和运维系统

## 工作流程

### 设计阶段
1. 接收中书省的设计方案
2. 识别需要外部技能支持的场景
3. 各司进行详细设计
   - 营造司：UI/UX设计，调用 `yingzaosi/SKILL.md`
   - 都水司：API设计，调用 `dushuisi/SKILL.md`
   - 屯田司：数据库设计，调用 `tuntiansi/SKILL.md`
4. 调用对应的外部技能（如需要）
   - UI/UX设计需求 → 调用外部技能 `ui-ux-pro-max`
   - MCP构建需求 → 调用外部技能 `mcp-builder`
5. 整合外部技能输出结果
6. 设计评审
7. 设计评审通过后进入开发阶段

### 开发阶段
1. 接收尚书省的开发任务和兵部的测试用例
2. **调用架构原则指导** → 调用 `../../subskills/jiagou_yuanze.md` 获取架构规范
3. **SDD规范加载** → 加载结构化规范定义（实体、接口、业务规则、约束条件）
4. 记录技术选型决策过程，形成决策记录文档
5. 记录异常处理策略决策过程，形成决策记录文档
6. 记录算法选择决策过程，形成决策记录文档
7. 分析失败测试的具体要求（红阶段）
8. **SDD代码生成** → 根据规范自动生成实现代码
9. 编写最小可行代码使测试通过（绿阶段）
10. **架构原则验证** → 检查代码是否符合架构规范
11. **规范一致性验证** → 验证代码是否符合规范定义
12. 运行单元测试验证代码正确性
13. 进行模块集成
14. 运行集成测试验证模块交互
15. 准备部署
16. 运行E2E测试验证完整业务流程
17. 测试通过后执行部署
18. 调用 `../../scripts/record_skill_call.py` 记录开发过程
19. 生成开发报告和质量评估
20. 更新项目文档

### 开发阶段架构检查点
```
检查时机:
  - 编码开始前: 确认架构设计符合原则
  - 功能开发中: 持续验证代码结构
  - 代码提交前: 全面架构合规检查

检查内容:
  - 分层架构是否正确
  - 模块依赖是否合理
  - 接口设计是否规范
  - 代码是否符合SOLID原则
```

## 设计与开发协调流程
1. 设计阶段产出物需明确交付给对应开发司
2. 营造司UI/UX设计 → 前端开发实现
3. 都水司API设计 → 后端开发实现
4. 屯田司数据库设计 → 数据库开发实现
5. 设计变更需同步通知相关开发司
6. 开发过程中发现设计问题，反馈至对应设计司进行修订

## 架构原则与开发规范

工部开发工作需遵循MVVM架构、模块化分层架构、SOLID原则、DRY/YAGNI/KISS原则等架构规范。

详细内容请参考 [架构原则](../../subskills/jiagou_yuanze.md)

## 测试执行原则
- 红灯时禁止重构
- 绿灯时方可提交代码
- 测试不通过不部署

## 开发实现流程

开发流程包括以下步骤：
1. 需求理解与任务分解
2. 开发环境准备
3. 功能开发（含架构检查）
4. 代码审查
5. 集成与测试
6. 部署发布

## TDD开发指南

TDD（测试驱动开发）是一种以测试为核心的软件开发方法，通过"红-绿-重构"循环驱动代码设计和实现。

### 核心原则
- 红-绿-重构循环：先写失败测试，再写最少代码通过，最后优化重构
- 测试先行：在写实现代码前先写测试，测试是需求的可执行文档
- 小步前进：每次只添加一个测试，每次只编写最少的代码

详细内容请参考 [TDD开发指南](../../subskills/tdd_liucheng.md)

### TDD开发流程

```
1. 红阶段（编写失败测试）
   - 理解需求
   - 编写测试用例
   - 运行测试确认失败
   - 分析失败原因

2. 绿阶段（编写通过代码）
   - 编写最小代码使测试通过
   - 不考虑代码质量
   - 快速实现功能
   - 运行测试确认通过

3. 重构阶段（优化代码）
   - 改善代码结构
   - 消除代码异味
   - 保持测试通过
   - 提交代码
```

### 代码实现指南

#### 红阶段实现策略
```
目标: 理解测试要求，准备实现方案

步骤:
  1. 阅读测试用例，理解期望行为
  2. 分析输入输出
  3. 识别依赖项
  4. 设计最小实现方案

注意事项:
  - 不要提前实现
  - 专注于当前测试
  - 记录实现思路
```

#### 绿阶段实现策略
```
目标: 编写最小代码使测试通过

原则:
  - 最简单实现
  - 硬编码也可以接受
  - 重复代码也可以接受
  - 快速通过测试

示例:
  // 第一次实现 - 硬编码
  function add(a, b) {
    return 4;  // 硬编码通过第一个测试 add(2, 2)
  }

  // 第二个测试后 - 通用实现
  function add(a, b) {
    return a + b;  // 通用实现
  }
```

## 最小实现原则

### 核心原则

```
原则1: 硬编码优先
  说明: 第一个测试可以用硬编码返回值通过
  示例:
    // 测试: add(2, 2) should return 4
    function add(a, b) {
      return 4;  // 硬编码通过
    }
  后续: 随着更多测试添加，逐步通用化

原则2: 简单实现优先
  说明: 选择最简单直接的实现方式
  示例:
    // 不推荐: 引入不必要的抽象
    class Calculator {
      constructor(strategy) {
        this.strategy = strategy;
      }
      add(a, b) {
        return this.strategy.execute(a, b);
      }
    }
    
    // 推荐: 简单直接
    function add(a, b) {
      return a + b;
    }

原则3: 重复可接受
  说明: 绿阶段允许代码重复，重复在重构阶段消除
  示例:
    // 绿阶段可以接受这样的重复
    function getCircleArea(radius) {
      return 3.14159 * radius * radius;
    }
    
    function getCylinderVolume(radius, height) {
      return 3.14159 * radius * radius * height;  // 重复计算
    }
  后续: 重构阶段提取公共方法

原则4: 不预先设计
  说明: 只为当前测试编写代码，不要为未来需求提前实现
  示例:
    // 不推荐: 预先设计扩展
    function createUser(data) {
      // 验证
      // 日志
      // 通知
      // 审计
      // ...很多未来可能用到的功能
    }
    
    // 推荐: 只实现当前测试需要的功能
    function createUser(data) {
      return saveToDatabase(data);
    }
```

### 最小实现检查清单

```
□ 代码刚好让测试通过
□ 没有添加测试未要求的功能
□ 没有预先设计未来功能
□ 实现简单直接
□ 可以接受硬编码
□ 可以接受重复代码
□ 所有测试通过
```

### 最小实现反模式

```
反模式1: 过度设计
  问题: 为未来需求提前设计
  后果: 增加复杂度，维护成本高
  解决: 只实现当前测试需要的功能

反模式2: 过度抽象
  问题: 引入不必要的抽象层
  后果: 代码难以理解，调试困难
  解决: 保持简单，需要时再抽象

反模式3: 预先优化
  问题: 在测试驱动前进行性能优化
  后果: 可能优化错误的地方
  解决: 先让测试通过，有性能问题再优化

反模式4: 功能蔓延
  问题: 实现测试未要求的相关功能
  后果: 增加开发时间，可能引入bug
  解决: 严格按测试要求实现
```

## 代码质量检查点

### 编码前检查点

```
□ 理解测试要求和预期行为
□ 确认架构分层正确
□ 确认模块依赖合理
□ 准备好开发环境
□ 了解相关规范定义
```

### 编码中检查点

```
□ 代码符合架构分层原则
□ 命名清晰有意义
□ 无编译错误和警告
□ 无明显的代码异味
□ 异常处理适当
□ 日志记录合理
```

### 编码后检查点

```
□ 所有测试通过（新测试+旧测试）
□ 代码覆盖率达标
□ 静态分析无严重问题
□ 代码规范检查通过
□ 无安全漏洞
□ 文档已更新
```

### 提交前检查点

```
□ 所有测试通过
□ 代码已审查
□ 提交信息清晰
□ 变更范围明确
□ 无调试代码残留
□ 敏感信息已移除
```

### 代码质量度量标准

| 指标 | 目标值 | 警告阈值 | 阻断阈值 |
|------|--------|----------|----------|
| 圈复杂度 | < 10 | 10-20 | > 20 |
| 方法长度 | < 20行 | 20-50行 | > 50行 |
| 类长度 | < 200行 | 200-500行 | > 500行 |
| 参数数量 | < 4个 | 4-6个 | > 6个 |
| 嵌套深度 | < 3层 | 3-5层 | > 5层 |
| 代码重复率 | < 3% | 3-5% | > 5% |
| 测试覆盖率 | > 80% | 70-80% | < 70% |

### 质量检查工具配置

```yaml
# 代码规范检查配置示例
lint:
  rules:
    max-line-length: 120
    max-function-length: 50
    max-params: 4
    max-nested-blocks: 3
    no-unused-vars: error
    no-duplicate-code: warning

# 复杂度检查配置
complexity:
  cyclomatic: 10
  cognitive: 15
  halstead: 20

# 安全检查配置
security:
  no-eval: error
  no-innerhtml: error
  no-sql-injection: error
```

#### 重构阶段策略
```
目标: 优化代码质量，保持测试通过

重构方向:
  - 消除重复
  - 改善命名
  - 简化逻辑
  - 提取方法
  - 优化结构

检查清单:
  □ 所有测试仍然通过
  □ 代码更易读
  □ 重复已消除
  □ 命名清晰
  □ 复杂度降低
```

## 测试通过策略

### 测试通过标准

```
单元测试通过标准:
  - 所有单元测试通过
  - 测试覆盖率 >= 80%
  - 无测试失败
  - 无测试跳过（除非有明确原因）

集成测试通过标准:
  - 所有集成测试通过
  - 模块间交互正常
  - 数据流正确
  - 接口契约遵守

E2E测试通过标准:
  - 所有E2E测试通过
  - 业务流程完整
  - 用户体验正常
  - 无关键路径失败
```

### 测试失败处理流程

```
1. 识别失败原因
   - 读取测试失败信息
   - 分析错误堆栈
   - 定位问题代码

2. 分类处理
   - 实现错误: 修复实现代码
   - 测试错误: 修正测试用例
   - 环境问题: 修复测试环境
   -  flaky测试: 稳定化测试

3. 修复验证
   - 修复问题
   - 重新运行测试
   - 确认测试通过
   - 检查无回归

4. 记录处理
   - 记录失败原因
   - 记录修复方案
   - 更新知识库
```

### 测试通过检查清单

```
代码提交前检查:
  □ 所有单元测试通过
  □ 代码覆盖率达标
  □ 代码规范检查通过
  □ 静态分析无严重问题

合并前检查:
  □ 集成测试通过
  □ 代码审查通过
  □ 性能测试无退化
  □ 安全扫描通过

发布前检查:
  □ E2E测试通过
  □ 回归测试通过
  □ 部署验证通过
  □ 监控告警配置完成
```

## SDD（规范驱动开发）指南

SDD（规范驱动开发）是一种以规范为核心的软件开发方法，通过"规范定义 → 规范解析 → 代码生成 → 验证"循环驱动代码设计和实现。

### 核心原则
- 规范即代码：规范是实现的唯一真实来源，代码由规范自动生成
- 结构化规范定义：包含实体定义、接口契约、业务规则、约束条件
- 双向一致性：代码必须符合规范定义，规范变更触发代码更新

详细内容请参考 [SDD规范驱动开发](../../subskills/sdd_liucheng.md)

### SDD开发流程

```
1. 规范解析
   - 加载SDD规范文档
   - 解析实体定义
   - 解析接口契约
   - 解析业务规则

2. 代码生成
   - 生成实体类
   - 生成接口实现
   - 生成验证逻辑
   - 生成测试模板

3. 代码补全
   - 实现业务逻辑
   - 补充单元测试
   - 验证规范一致性

4. 持续同步
   - 监控规范变更
   - 自动更新代码
   - 验证一致性
```

## 持续集成能力

### CI/CD流程

```
1. 代码提交触发
   - 开发者提交代码
   - 触发CI流水线
   - 拉取最新代码

2. 构建阶段
   - 编译代码
   - 打包应用
   - 生成构建产物

3. 测试阶段
   - 运行单元测试
   - 运行集成测试
   - 生成测试报告
   - 检查测试覆盖率

4. 质量检查
   - 代码规范检查
   - 静态代码分析
   - 安全漏洞扫描
   - 依赖检查

5. 部署阶段
   - 部署到测试环境
   - 运行E2E测试
   - 部署到预发布环境
   - 部署到生产环境
```

### CI/CD配置示例

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run linter
      run: npm run lint
    
    - name: Run unit tests
      run: npm run test:unit -- --coverage
    
    - name: Check coverage
      run: |
        if [ $(cat coverage/lcov-report/index.html | grep -oP 'Statements.*?\K[0-9]+' | head -1) -lt 80 ]; then
          echo "Coverage is below 80%"
          exit 1
        fi
    
    - name: Run integration tests
      run: npm run test:integration
    
    - name: Build
      run: npm run build
    
    - name: Security audit
      run: npm audit --audit-level=moderate

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to production
      run: |
        echo "Deploying to production..."
        # 部署脚本
```

### 持续集成最佳实践

```
1. 快速反馈
   - 保持构建时间短（< 10分钟）
   - 并行执行独立任务
   - 优先运行快速测试

2. 自动化一切
   - 自动运行测试
   - 自动代码检查
   - 自动部署

3. 保持构建绿色
   - 立即修复失败的构建
   - 不提交破坏构建的代码
   - 快速回滚问题变更

4. 可见性
   - 构建状态可视化
   - 及时通知失败
   - 详细的构建日志
```

## 代码提交规范

采用约定式提交（Conventional Commits）规范，格式为 `<type>(<scope>): <subject>`。

### 提交类型
| 类型 | 描述 |
|------|------|
| feat | 新功能 |
| fix | Bug修复 |
| docs | 文档更新 |
| style | 代码格式 |
| refactor | 重构 |
| perf | 性能优化 |
| test | 测试相关 |
| build | 构建系统 |
| ci | CI配置 |
| chore | 其他杂项 |

### 分支命名规范
格式: `<type>/<issue-id>-<description>`
- feature: 新功能开发
- bugfix: Bug修复
- hotfix: 紧急修复
- release: 发布分支

## 外部技能调用

### UI/UX设计技能
- 技能名称：`ui-ux-pro-max`
- 调用场景：
  - 需要专业UI界面设计时
  - 需要UX用户体验优化时
  - 需要设计系统规范制定时
  - 需要交互原型设计时
- 调用方式：根据具体设计需求，传递设计上下文和约束条件

### MCP构建技能
- 技能名称：`mcp-builder`
- 调用场景：
  - 需要构建MCP（Model Context Protocol）服务时
  - 需要集成外部工具和服务时
  - 需要扩展AI能力边界时
- 调用方式：根据MCP构建需求，传递功能规格和技术要求

## 决策记录要求

开发过程中需记录技术选型、异常处理策略、算法选择等关键决策，确保决策过程透明可追溯。

### 记录内容
- 技术选型决策：候选方案对比、最终选择及理由、风险评估
- 异常处理决策：异常场景识别、处理策略选择、恢复机制设计
- 算法选择决策：复杂度分析、适用场景对比、性能基准测试
- 代码变更记录：变更详情、方案选择依据、测试验证结果

### 记录格式
每个决策记录需包含：决策编号、决策类型、决策背景、候选方案、评估过程、最终决策、时间戳、参与者。

## 协同调用接口

### 接口定义

工部作为开发部署机构，提供以下协同调用接口供其他技能调用：

| 接口名称 | 接口描述 | 调用方 |
|----------|----------|--------|
| `develop_feature` | 功能开发接口 | 尚书省 |
| `generate_code` | 代码生成接口 | 中书省、尚书省 |
| `build_and_deploy` | 构建部署接口 | 尚书省、门下省 |
| `run_integration_test` | 集成测试执行接口 | 兵部 |

### 输入参数规范

#### 功能开发接口参数

```json
{
  "interface": "develop_feature",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "feature": {
      "feature_id": "功能ID",
      "name": "功能名称",
      "description": "功能描述",
      "test_cases": ["测试用例列表"]
    },
    "tdd_phase": "red|green|refactor",
    "spec": {
      "spec_path": "规范文档路径",
      "entities": ["实体列表"],
      "interfaces": ["接口列表"]
    },
    "development_options": {
      "auto_generate": true,
      "follow_architecture": true,
      "code_review_required": true
    }
  }
}
```

#### 代码生成接口参数

```json
{
  "interface": "generate_code",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "spec": {
      "entities": [
        {
          "name": "实体名称",
          "attributes": ["属性列表"],
          "behaviors": ["行为列表"]
        }
      ],
      "interfaces": [
        {
          "name": "接口名称",
          "methods": ["方法列表"]
        }
      ]
    },
    "generation_options": {
      "language": "python|javascript|typescript|java",
      "framework": "框架名称",
      "output_path": "输出路径",
      "generate_tests": true,
      "generate_docs": true
    }
  }
}
```

#### 构建部署接口参数

```json
{
  "interface": "build_and_deploy",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "build_config": {
      "type": "docker|npm|maven|gradle",
      "environment": "development|staging|production",
      "version": "1.0.0"
    },
    "deploy_config": {
      "target": "kubernetes|ecs|lambda|vm",
      "replicas": 3,
      "health_check": true,
      "rollback_enabled": true
    },
    "approval": {
      "approved": true,
      "approver": "审批人",
      "approval_id": "审批ID"
    }
  }
}
```

### 输出格式规范

```json
{
  "interface": "develop_feature",
  "call_id": "DEV-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "status": "success|failure|partial",
  "result": {
    "feature_id": "F-001",
    "code_artifacts": [
      {
        "type": "source",
        "path": "文件路径",
        "lines": 100
      }
    ],
    "test_result": {
      "passed": true,
      "coverage": 0.85
    },
    "compliance": {
      "spec_compliant": true,
      "architecture_compliant": true
    }
  }
}
```

### 调用示例

```bash
# 调用功能开发接口
调用 ./SKILL.md --interface=develop_feature \
  --feature='{"feature_id":"F-001","name":"用户登录"}' \
  --tdd-phase="green" \
  --development-options='{"auto_generate":true}'

# 调用代码生成接口
调用 ./SKILL.md --interface=generate_code \
  --spec='{"entities":[{"name":"User"}]}' \
  --generation-options='{"language":"python"}'

# 调用构建部署接口
调用 ./SKILL.md --interface=build_and_deploy \
  --build-config='{"type":"docker","environment":"staging"}' \
  --deploy-config='{"target":"kubernetes"}'
```

---

## 下属四司
- yingzaosi（营造司）：前端开发、UI/UX设计，详细内容请参考 [UI/UX设计](../../subskills/ui_ux_sheji.md)
- dushuisi（都水司）：后端开发、API设计，详细内容请参考 [API设计](../../subskills/api_sheji.md)
- tuntiansi（屯田司）：数据库管理、数据库设计，详细内容请参考 [数据库设计](../../subskills/shujuku_sheji.md)
- yuhengsi（虞衡司）：部署运维

## 代码生成

详细代码生成流程（根据结构化规范自动生成实现代码）请参考 [代码生成](../../subskills/daima_shengcheng.md)。

## SDD与TDD融合

详细SDD与TDD融合工作流指导请参考 [SDD+TDD融合](../../subskills/sdd_tdd_ronghe.md)。

---

## 开发自动化增强

### 代码生成模板管理

```yaml
code_generation_templates:
  entity:
    source: "templates/entity.{lang}.jinja2"
    output: "src/models/{name}.{ext}"
    variables:
      - name
      - attributes
      - relationships
      
  service:
    source: "templates/service.{lang}.jinja2"
    output: "src/services/{name}_service.{ext}"
    variables:
      - name
      - methods
      - dependencies
      
  test:
    source: "templates/test.{lang}.jinja2"
    output: "tests/test_{name}.{ext}"
    variables:
      - name
      - test_cases
      - fixtures
```

### 开发环境自动配置

```json
{
  "dev_environment": {
    "setup_script": "scripts/setup_dev.sh",
    "dependencies": {
      "runtime": "python3.11",
      "packages": [
        "fastapi>=0.100.0",
        "pydantic>=2.0.0",
        "pytest>=7.0.0"
      ],
      "dev_packages": [
        "black",
        "ruff",
        "mypy"
      ]
    },
    "ide_config": {
      "vscode": {
        "extensions": [
          "ms-python.python",
          "ms-python.vscode-pylance"
        ],
        "settings": {
          "python.linting.enabled": true,
          "python.formatting.provider": "black"
        }
      }
    },
    "pre_commit_hooks": {
      "enabled": true,
      "hooks": [
        "black",
        "ruff",
        "mypy"
      ]
    }
  }
}
```

### 部署流水线配置

```yaml
deployment_pipeline:
  environments:
    - name: "development"
      auto_deploy: true
      branch: "develop"
      approval_required: false
      
    - name: "staging"
      auto_deploy: true
      branch: "main"
      approval_required: true
      approvers: ["tech_lead"]
      
    - name: "production"
      auto_deploy: false
      branch: "main"
      approval_required: true
      approvers: ["tech_lead", "product_owner"]
      
  rollback:
    enabled: true
    strategy: "blue_green"
    health_check_timeout_seconds: 300
    
  monitoring:
    enabled: true
    alerts:
      - type: "error_rate"
        threshold: "1%"
        action: "notify"
      - type: "response_time"
        threshold: "500ms"
        action: "notify"
```

---

## 协同效果评估能力

### 代码实现协同评估指标

工部作为代码实现机构，负责评估代码实现在三省六部协同中的效果。

| 评估维度 | 指标 | 目标值 | 度量方法 |
|----------|------|--------|----------|
| 实现效率 | 功能实现平均时间 | ≤4小时 | 时间戳统计 |
| 代码质量 | 代码质量评分 | ≥0.85 | 质量工具统计 |
| 测试通过率 | 一次测试通过率 | ≥85% | 测试结果统计 |
| 规范符合率 | 代码规范符合率 | ≥95% | 规范检查统计 |
| 部署成功率 | 部署一次成功率 | ≥95% | 部署记录统计 |

### 代码实现协同评估报告格式

```json
{
  "evaluation_id": "EVAL-GONGBU-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-07T23:59:59Z"
  },
  "implementation_metrics": {
    "total_features": 15,
    "completed_features": 14,
    "avg_implementation_time_hours": 3.5,
    "code_lines_added": 2500,
    "code_lines_deleted": 500
  },
  "quality_metrics": {
    "code_quality_score": 0.88,
    "complexity_score": 8.5,
    "duplication_score": 0.03,
    "maintainability_index": 72
  },
  "test_metrics": {
    "test_first_compliance": 1.0,
    "first_pass_rate": 0.87,
    "avg_red_green_cycle_minutes": 18,
    "test_coverage": 0.86
  },
  "compliance_metrics": {
    "coding_standard_compliance": 0.96,
    "architecture_compliance": 0.94,
    "security_compliance": 0.98
  },
  "deployment_metrics": {
    "total_deployments": 8,
    "successful_deployments": 8,
    "rollback_count": 0,
    "avg_deployment_time_minutes": 12
  },
  "recommendations": [
    {
      "category": "quality_improvement",
      "priority": "medium",
      "description": "提高代码可维护性指数至75以上",
      "expected_impact": "降低后续维护成本"
    }
  ]
}
```

---

## 流水线协调能力

### 流水线代码实现节点

工部在白盒化7阶段流水线中负责代码实现和部署发布阶段的执行。

| 阶段 | 工部角色 | 实现内容 | 输出物 |
|------|----------|----------|--------|
| 需求分析 | 支持 | 技术可行性分析 | 可行性报告 |
| SDD规范定义 | 支持 | 技术规范定义 | 技术规范 |
| 审议批准 | 支持 | 技术方案评审 | 评审意见 |
| 测试先行 | 支持 | 测试环境准备 | 测试环境 |
| 代码实现 | 主导 | 功能代码开发 | 功能代码 |
| 持续重构 | 支持 | 重构后验证 | 验证报告 |
| 部署发布 | 主导 | 部署发布执行 | 部署产物 |

### 流水线实现配置

```yaml
pipeline_implementation_config:
  development_process:
    mode: "tdd"
    test_first: true
    minimal_implementation: true
    
  implementation_stages:
    - stage: "red"
      action: "write_failing_test"
      timeout_minutes: 10
      
    - stage: "green"
      action: "minimal_implementation"
      timeout_minutes: 15
      
    - stage: "refactor"
      action: "optimize_code"
      timeout_minutes: 10
      
  quality_gates:
    - name: "test_pass"
      check: "all_tests_pass"
      blocking: true
      
    - name: "code_quality"
      check: "quality_score >= 0.80"
      blocking: false
      
    - name: "coverage"
      check: "coverage >= 0.80"
      blocking: true
```

---

## 增强功能集成

### 与provincial_coordinator集成

工部通过provincial_coordinator.py实现代码实现的自动化和协同：

```python
from scripts.provincial_coordinator import (
    SmartDispatcher,
    TaskRequirement,
    TaskPriority
)

dispatcher = SmartDispatcher()

def implement_feature_for_task(task_id: str, feature_requirements: dict):
    requirement = TaskRequirement(
        task_id=task_id,
        required_capabilities={
            "code_implementation": 0.9,
            "feature_development": 0.85
        },
        preferred_specializations=["gongbu"],
        priority=TaskPriority.HIGH
    )
    
    decision = dispatcher.find_best_match(requirement, "ministry")
    
    return {
        "assigned_entity": decision.assigned_entity,
        "match_score": decision.overall_score,
        "implementation_details": feature_requirements
    }
```

---

## 实现质量保障

### 实现质量检查清单

```
□ 测试先行，先写测试
□ 最小实现，刚好通过测试
□ 代码符合编码规范
□ 代码符合架构设计
□ 无安全漏洞
□ 性能满足要求
□ 代码可读性好
□ 提交信息清晰
```

### 实现质量评分

| 评分项 | 权重 | 评分标准 |
|--------|------|----------|
| 测试先行率 | 25% | 测试先于实现编写 |
| 代码质量 | 25% | 代码质量评分高 |
| 规范符合率 | 20% | 代码符合规范 |
| 实现效率 | 15% | 实现时间合理 |
| 可维护性 | 15% | 代码易于维护 |
