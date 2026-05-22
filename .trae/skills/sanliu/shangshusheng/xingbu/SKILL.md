---
name: xingbu
description: 刑部，负责问题修复，包括 Bug 追踪、代码重构、性能优化、持续重构等。
---
# 刑部技能指令

## 职责

| 职责领域 | 说明 |
|----------|------|
| Bug 追踪 | 跟踪和管理 Bug |
| 代码重构 | 进行代码重构 |
| 性能优化 | 优化系统性能 |
| 持续重构 | 在测试通过后优化代码结构，保持代码质量持续提升 |
| 基于规范的代码重构 | 在保持规范一致性的前提下进行重构 |
| 重构后规范一致性验证 | 验证重构后代码仍符合规范 |
| 代码质量优化 | 提升代码质量指标 |
| 覆盖率验证 | 验证测试覆盖率达标 |
| 代码审查 | 执行代码审查和质量检查 |

## 工作流程

```
1. 接收尚书省的问题修复需求
2. 记录Bug定位推理过程，形成推理链文档
3. 记录问题诊断推理过程，形成推理链文档
4. 调用 ../../subskills/wenti_xiufu.md 进行问题修复
5. 调用 ../../subskills/daima_chonggou.md 进行代码重构
6. 调用 ../../subskills/jiagou_yuanze.md 进行架构原则检查
7. 调用 ../../subskills/xingneng_youhua.md 进行性能优化
8. 调用 ../../scripts/record_skill_call.py 记录修复过程
9. 验证修复效果
10. 生成修复报告和质量评估
11. 更新技术债务记录
12. 提交代码审查请求
```

## 问题诊断决策流程（增强版）

### 问题分析阶段

```
问题分析步骤:
  1. 问题类型识别
     - Bug修复
     - 性能问题
     - 安全漏洞
     - 代码异味
     - 架构问题
  
  2. 问题严重程度评估
     - Critical: 系统崩溃、数据丢失
     - Major: 功能受损、性能严重下降
     - Minor: 功能异常、体验问题
     - Low: 边缘问题、优化建议
  
  3. 问题影响范围分析
     - 影响模块识别
     - 影响用户群体
     - 影响业务流程
  
  4. 问题根因分析
     - 直接原因
     - 根本原因
     - 关联问题
```

### 问题诊断输出

```json
{
  "diagnosis_report": {
    "diagnosis_id": "DIAG-001",
    "timestamp": "2024-01-01T00:00:00Z",
    "issue": {
      "issue_id": "ISSUE-001",
      "type": "bug",
      "severity": "major",
      "description": "用户登录后偶发Session丢失"
    },
    "analysis": {
      "symptoms": [
        "用户登录后10分钟内Session丢失",
        "错误日志显示Session ID无效"
      ],
      "root_cause": {
        "primary": "Redis连接池配置错误，连接超时未正确处理",
        "contributing": [
          "缺少Session健康检查机制",
          "重连逻辑不完善"
        ]
      },
      "impact": {
        "affected_modules": ["auth", "session"],
        "affected_users": "约5%的登录用户",
        "business_impact": "用户需要重新登录，体验下降"
      }
    },
    "solution_candidates": [
      {
        "id": "SOL-001",
        "description": "修复Redis连接池配置，添加健康检查",
        "estimated_effort": "2小时",
        "risk": "low",
        "score": 0.95
      },
      {
        "id": "SOL-002",
        "description": "切换到数据库Session存储",
        "estimated_effort": "8小时",
        "risk": "medium",
        "score": 0.75
      }
    ],
    "recommendation": {
      "selected_solution": "SOL-001",
      "rationale": "风险低、工作量小、能快速解决问题"
    }
  }
}
```

### 修复策略选择

| 策略类型 | 适用场景 | 风险等级 | 验证要求 |
|----------|----------|----------|----------|
| 快速修复 | 紧急问题、影响范围小 | 低 | 单元测试 |
| 标准修复 | 常规问题、需要测试 | 中 | 集成测试 |
| 重构修复 | 根本解决、技术债务 | 高 | 全量测试 |
| 架构调整 | 系统性问题 | 高 | E2E测试 |

### 修复执行记录

```json
{
  "fix_execution": {
    "fix_id": "FIX-001",
    "timestamp": "2024-01-01T00:00:00Z",
    "diagnosis_id": "DIAG-001",
    "solution_id": "SOL-001",
    "execution": {
      "changes": [
        {
          "file": "src/config/redis.py",
          "type": "modified",
          "lines_changed": 15,
          "description": "修复连接池配置"
        },
        {
          "file": "src/services/session.py",
          "type": "modified",
          "lines_changed": 25,
          "description": "添加健康检查和重连逻辑"
        }
      ],
      "tests_added": 3,
      "tests_modified": 2
    },
    "verification": {
      "unit_tests": {"passed": 50, "failed": 0},
      "integration_tests": {"passed": 20, "failed": 0},
      "coverage": 0.88
    },
    "status": "completed",
    "review_required": true
  }
}
```

## 重构决策流程（增强版）

### 重构触发条件分析

```
重构触发条件:
  1. 代码质量指标
     - 圈复杂度 > 15
     - 代码重复率 > 5%
     - 测试覆盖率 < 70%
  
  2. 架构问题
     - 违反SOLID原则
     - 高耦合低内聚
     - 循环依赖
  
  3. 维护性问题
     - 频繁出错的模块
     - 难以理解的代码
     - 难以扩展的设计
  
  4. 技术债务
     - 待处理的TODO
     - 临时解决方案
     - 过时的依赖
```

### 重构方案评估

```json
{
  "refactor_proposal": {
    "proposal_id": "REF-PROP-001",
    "timestamp": "2024-01-01T00:00:00Z",
    "target": {
      "module": "src/services/payment",
      "current_metrics": {
        "cyclomatic_complexity": 18,
        "lines_of_code": 450,
        "test_coverage": 0.65,
        "duplication": 0.08
      },
      "issues": [
        "复杂度过高，难以维护",
        "测试覆盖率不足",
        "存在重复代码"
      ]
    },
    "refactor_plan": {
      "approach": "提取方法 + 策略模式",
      "steps": [
        {
          "step": 1,
          "action": "提取支付策略接口",
          "effort_hours": 2
        },
        {
          "step": 2,
          "action": "拆分支付方法",
          "effort_hours": 4
        },
        {
          "step": 3,
          "action": "补充单元测试",
          "effort_hours": 3
        }
      ],
      "estimated_total_hours": 9,
      "expected_improvement": {
        "cyclomatic_complexity": 8,
        "test_coverage": 0.90,
        "duplication": 0.02
      }
    },
    "risk_assessment": {
      "risk_level": "medium",
      "risks": [
        "可能影响现有支付流程",
        "需要回归测试"
      ],
      "mitigation": [
        "分步骤执行，每步验证",
        "保持测试通过",
        "准备回滚方案"
      ]
    },
    "approval_status": "pending"
  }
}
```

### 重构执行监控

```json
{
  "refactor_monitoring": {
    "monitor_id": "REF-MON-001",
    "timestamp": "2024-01-01T00:00:00Z",
    "refactor_id": "REF-001",
    "progress": {
      "current_step": 2,
      "total_steps": 3,
      "completion_rate": 0.67
    },
    "metrics_tracking": {
      "before": {
        "complexity": 18,
        "coverage": 0.65,
        "duplication": 0.08
      },
      "current": {
        "complexity": 12,
        "coverage": 0.78,
        "duplication": 0.04
      },
      "target": {
        "complexity": 8,
        "coverage": 0.90,
        "duplication": 0.02
      }
    },
    "test_status": {
      "unit_tests": "all_passed",
      "integration_tests": "all_passed",
      "regression_tests": "not_run"
    },
    "issues": [],
    "next_actions": [
      "完成步骤3：补充单元测试",
      "运行回归测试",
      "提交代码审查"
    ]
  }
}
```

## SDD 工作流程

```
1. 接收规范驱动重构任务
2. 获取相关规范文档（调用 ../../subskills/guifan_yanzheng.md）
3. 分析规范约束条件
4. 识别重构点并验证规范约束
5. 执行规范驱动的代码重构
6. 验证重构后规范一致性
7. 记录重构决策与规范依据
8. 输出重构报告与规范一致性报告
```

## 持续重构工作流程

```
1. 接收尚书省的重构任务（测试通过后）
2. 检查代码质量，识别优化点
3. 进行代码重构（提取方法、消除重复、优化命名等）
4. 运行单元测试确保行为不变
5. 运行集成测试确保集成正确
6. 若测试失败，回退或修复
7. 验证代码质量指标提升
8. 输出重构报告
```

## 单元测试验证重构流程

```
1. 重构前：运行现有单元测试，记录基线结果
2. 执行重构：小步修改代码结构
3. 重构后：重新运行单元测试
4. 结果比对：
   - 测试通过：重构成功，继续下一步
   - 测试失败：回退变更，分析原因后重新尝试
5. 记录测试覆盖率变化
```

## 集成测试验证重构流程

```
1. 重构前：运行现有集成测试，记录基线结果
2. 执行重构：确保接口契约不变
3. 重构后：重新运行集成测试
4. 结果比对：
   - 测试通过：重构成功，验证集成点正常
   - 测试失败：回退变更，检查接口兼容性
5. 验证系统间交互正常
```

## 重构循环验证流程

```
1. 初始评估：记录代码质量指标（复杂度、重复率、测试覆盖率）
2. 重构迭代：
   - 选择一个优化点
   - 小步重构
   - 运行单元测试
   - 运行集成测试
   - 验证质量指标提升
3. 循环条件：
   - 存在可优化点且测试通过：继续迭代
   - 测试失败：回退并修复
   - 无明显优化点：结束循环
4. 最终验证：确保所有测试通过，质量指标有提升
5. 输出重构报告
```

## 重构原则

- 保持行为不变（测试必须通过）
- 小步前进
- 持续测试验证
- 测试失败立即回退

## 重构策略与模式

### 重构策略分类

```
策略类型1: 代码整理
  - 提取方法
  - 内联方法
  - 提取变量
  - 内联变量
  - 重命名

策略类型2: 简化条件
  - 分解条件表达式
  - 合并条件表达式
  - 以卫语句取代嵌套条件
  - 以多态取代条件

策略类型3: 简化函数调用
  - 重命名函数
  - 添加参数
  - 移除参数
  - 以查询取代参数
  - 以参数取代查询

策略类型4: 处理概括关系
  - 字段上移
  - 字段下移
  - 方法上移
  - 方法下移
  - 提取接口
```

### 常用重构模式详解

#### 模式1: 提取方法

```
适用场景:
  - 方法过长
  - 代码重复
  - 逻辑复杂需要注释才能理解

操作步骤:
  1. 创建新方法，用意图命名
  2. 将代码复制到新方法
  3. 调整参数传递
  4. 替换原位置为方法调用
  5. 运行测试验证

示例:
  // 重构前
  function printOwing(invoice) {
    let outstanding = 0;
    console.log("***********************");
    console.log("*** Customer Owes ***");
    console.log("***********************");
    
    for (const o of invoice.orders) {
      outstanding += o.amount;
    }
    
    console.log(`name: ${invoice.customer}`);
    console.log(`amount: ${outstanding}`);
  }
  
  // 重构后
  function printOwing(invoice) {
    printBanner();
    const outstanding = calculateOutstanding(invoice);
    printDetails(invoice, outstanding);
  }
```

#### 模式2: 以多态取代条件

```
适用场景:
  - 复杂的switch/if-else逻辑
  - 条件分支经常变化
  - 需要添加新的条件分支

操作步骤:
  1. 创建策略接口
  2. 为每个分支创建策略类
  3. 使用工厂创建策略实例
  4. 替换条件逻辑为策略调用
  5. 运行测试验证

示例:
  // 重构前
  function calculatePrice(type, amount) {
    if (type === 'VIP') {
      return amount * 0.8;
    } else if (type === 'MEMBER') {
      return amount * 0.9;
    } else {
      return amount;
    }
  }
  
  // 重构后
  class PricingStrategy {
    calculate(amount) {
      return amount;
    }
  }
  
  class VIPStrategy extends PricingStrategy {
    calculate(amount) {
      return amount * 0.8;
    }
  }
  
  class MemberStrategy extends PricingStrategy {
    calculate(amount) {
      return amount * 0.9;
    }
  }
```

#### 模式3: 提取接口

```
适用场景:
  - 依赖具体实现
  - 耦合过紧
  - 需要支持多种实现

操作步骤:
  1. 识别依赖的方法
  2. 定义接口
  3. 让实现类实现接口
  4. 修改依赖为接口类型
  5. 运行测试验证

示例:
  // 重构前
  class UserService {
    constructor() {
      this.repository = new UserRepository();  // 直接依赖具体类
    }
  }
  
  // 重构后
  interface IUserRepository {
    findById(id);
    save(user);
  }
  
  class UserService {
    constructor(repository: IUserRepository) {
      this.repository = repository;  // 依赖接口
    }
  }
```

#### 模式4: 以卫语句取代嵌套条件

```
适用场景:
  - 嵌套过深的条件判断
  - 难以理解的条件逻辑

操作步骤:
  1. 识别嵌套条件
  2. 将每个条件转为卫语句
  3. 提前返回
  4. 运行测试验证

示例:
  // 重构前
  function getPaymentAmount() {
    let result;
    if (isDead) {
      result = deadAmount();
    } else {
      if (isSeparated) {
        result = separatedAmount();
      } else {
        if (isRetired) {
          result = retiredAmount();
        } else {
          result = normalPayAmount();
        }
      }
    }
    return result;
  }
  
  // 重构后
  function getPaymentAmount() {
    if (isDead) return deadAmount();
    if (isSeparated) return separatedAmount();
    if (isRetired) return retiredAmount();
    return normalPayAmount();
  }
```

#### 模式5: 移动方法

```
适用场景:
  - 方法在错误的类中
  - 方法过多使用其他类的数据
  - 方法与当前类职责不符

操作步骤:
  1. 识别目标类
  2. 复制方法到目标类
  3. 调整访问权限和参数
  4. 删除原方法
  5. 运行测试验证

示例:
  // 重构前
  class Account {
    overdraftCharge() {  // 这个方法更适合在AccountType中
      if (this.type.isPremium()) {
        return Math.max(10, this.daysOverdrawn * 0.85);
      }
      return this.daysOverdrawn * 1.75;
    }
  }
  
  // 重构后
  class AccountType {
    overdraftCharge(daysOverdrawn) {
      if (this.isPremium()) {
        return Math.max(10, daysOverdrawn * 0.85);
      }
      return daysOverdrawn * 1.75;
    }
  }
```

### 重构时机判断

```
重构信号1: 代码异味
  - 重复代码
  - 过长方法
  - 过大类
  - 过长参数列表
  - 发散式变化
  - 霰弹式修改

重构信号2: 设计问题
  - 违反SOLID原则
  - 高耦合低内聚
  - 循环依赖
  - 不恰当的暴露

重构信号3: 可维护性问题
  - 难以理解
  - 难以修改
  - 难以测试
  - 频繁出错
```

### 重构风险评估

| 重构类型 | 风险等级 | 影响范围 | 测试要求 |
|----------|----------|----------|----------|
| 重命名 | 低 | 小 | 单元测试 |
| 提取方法 | 低 | 小 | 单元测试 |
| 移动方法 | 中 | 中 | 集成测试 |
| 提取接口 | 中 | 中 | 集成测试 |
| 重构继承体系 | 高 | 大 | 全量测试 |
| 更改架构 | 高 | 大 | E2E测试 |

## 质量度量标准

### 代码质量指标体系

| 指标 | 说明 | 目标值 | 警告阈值 | 严重阈值 | 度量方法 |
|------|------|--------|----------|----------|----------|
| 圈复杂度 | 函数复杂度 | < 10 | 10-20 | > 20 | McCabe |
| 认知复杂度 | 代码理解难度 | < 15 | 15-25 | > 25 | SonarQube |
| 代码重复率 | 重复代码比例 | < 3% | 3-5% | > 5% | CPD |
| 方法长度 | 函数行数 | < 20 | 20-50 | > 50 | 行数统计 |
| 类长度 | 类行数 | < 200 | 200-500 | > 500 | 行数统计 |
| 参数数量 | 函数参数个数 | < 4 | 4-6 | > 6 | 参数计数 |
| 嵌套深度 | 代码嵌套层级 | < 3 | 3-5 | > 5 | 层级统计 |
| 测试覆盖率 | 测试覆盖比例 | > 80% | 70-80% | < 70% | 覆盖率工具 |
| 技术债务 | 债务时间 | < 1h | 1-4h | > 4h | SQALE |
| 代码异味数 | 异味数量 | < 10 | 10-30 | > 30 | SonarQube |

### 质量门禁标准

```yaml
质量门禁配置:
  阻断级别:
    - 圈复杂度 > 20
    - 测试覆盖率 < 70%
    - 阻断级安全漏洞 > 0
    - 代码重复率 > 5%
  
  警告级别:
    - 圈复杂度 10-20
    - 测试覆盖率 70-80%
    - 代码异味数 10-30
    - 技术债务 1-4小时
  
  豁免条件:
    - 自动生成的代码
    - 配置文件
    - 第三方库代码
    - 遗留代码（需记录技术债务）
```

### 质量趋势分析

```
质量趋势指标:
  1. 质量评分趋势
     - 每周质量评分变化
     - 目标: 持续上升或保持稳定
  
  2. 技术债务趋势
     - 新增债务 vs 偿还债务
     - 目标: 债务净增长为负或零
  
  3. 测试覆盖率趋势
     - 覆盖率变化曲线
     - 目标: 持续上升
  
  4. 代码异味趋势
     - 异味数量变化
     - 目标: 持续下降
  
  5. 重构效率
     - 重构时间 vs 质量提升
     - 目标: 投入产出比合理
```

### 质量报告模板

```
质量报告内容:
  1. 总体评分
     - 当前评分: X/100
     - 上期评分: Y/100
     - 变化趋势: ↑/↓/→
  
  2. 关键指标
     - 圈复杂度: 当前值/目标值
     - 测试覆盖率: 当前值/目标值
     - 代码重复率: 当前值/目标值
     - 技术债务: 当前值/目标值
  
  3. 问题清单
     - 阻断级问题: 数量/列表
     - 警告级问题: 数量/Top10
     - 改进建议: 列表
  
  4. 改进计划
     - 本期完成的重构
     - 下期计划的重构
     - 预期效果
```

## 规范驱动重构流程（SDD）

### 1. 识别重构点

```
识别方法:
  - 规范偏离检测：对比代码与规范的差异
  - 规范演进触发：规范更新导致的代码调整需求
  - 规范冲突检测：发现代码与规范不一致的地方
  - 规范覆盖分析：识别规范未覆盖或覆盖不足的代码区域

识别输出:
  - 重构点清单
  - 规范关联映射
  - 优先级排序
  - 风险评估
```

### 2. 验证规范约束

```
验证内容:
  - 规范适用性确认：确认规范是否适用于目标代码
  - 约束条件提取：从规范中提取具体约束条件
  - 约束冲突检测：检查多个规范约束之间是否存在冲突
  - 约束优先级排序：确定约束的应用顺序

验证方法:
  - 规范文档解析
  - 约束条件形式化
  - 规则引擎验证
  - 人工审查确认
```

### 3. 执行重构

```
执行原则:
  - 规范优先：重构决策以规范为准绳
  - 最小变更：在满足规范前提下最小化改动范围
  - 可追溯性：记录每个重构决策的规范依据
  - 渐进式重构：分步骤执行，每步验证

执行步骤:
  1. 确认当前代码状态与规范差距
  2. 制定规范驱动的重构方案
  3. 小步执行重构操作
  4. 每步验证规范一致性
  5. 记录重构决策与规范依据
```

### 4. 验证规范一致性

```
验证维度:
  - 代码规范一致性：代码风格、命名、格式等
  - 架构规范一致性：分层、模块划分、依赖关系等
  - 业务规范一致性：业务逻辑、流程、规则等
  - 接口规范一致性：API设计、数据格式、契约等

验证方法:
  - 自动化规范检查工具
  - 规范符合性测试
  - 代码审查对照规范
  - 规范审计报告生成
```

## 重构后规范一致性验证方法

详细的验证流程、检查清单和工具配置请参考 [规范一致性验证资源](../../resources/guifan_yizhixing_yanzheng.md)。

## 代码重构流程

### 1. 重构触发条件

```
主动触发:
  - 测试通过后的持续重构
  - 代码审查发现的问题
  - 技术债务清理计划

被动触发:
  - Bug修复时顺便重构
  - 新功能开发时重构相关代码
  - 性能问题修复
```

### 2. 重构评估

```
评估内容:
  - 代码异味检测
  - 复杂度分析
  - 重复代码检测
  - 测试覆盖率检查
  - 依赖关系分析
  - SOLID原则检查（调用 ../../subskills/jiagou_yuanze.md）
  - 高内聚低耦合评估

评估输出:
  - 重构优先级列表
  - 预估工作量
  - 风险评估
  - 架构问题清单
```

### 3. 重构计划制定

```
计划内容:
  - 重构目标
  - 重构范围
  - 重构步骤
  - 验证方法
  - 回滚方案
  - 时间安排
```

### 4. 重构执行

```
执行原则:
  - 小步重构，频繁提交
  - 每步重构后运行测试
  - 保持代码可编译/可运行
  - 及时提交，便于回滚

执行步骤:
  1. 确保测试全部通过
  2. 执行单个重构操作
  3. 运行测试验证
  4. 提交变更
  5. 重复以上步骤
```

### 5. 重构验证

```
验证内容:
  - 所有测试通过
  - 功能行为不变
  - 代码质量提升
  - 性能无明显下降

验证方法:
  - 单元测试
  - 集成测试
  - E2E测试
  - 代码审查
  - 性能测试
```

### 6. 重构完成

```
完成标准:
  - 所有测试通过
  - 代码质量指标达标
  - 代码审查通过
  - 文档更新完成

输出物:
  - 重构报告
  - 更新的测试用例
  - 更新的文档
```

## 代码质量优化指南

### 代码质量指标

| 指标 | 说明 | 目标值 | 警告阈值 | 严重阈值 |
|------|------|--------|----------|----------|
| 圈复杂度 | 函数复杂度 | < 10 | 10-20 | > 20 |
| 认知复杂度 | 代码理解难度 | < 15 | 15-25 | > 25 |
| 代码重复率 | 重复代码比例 | < 3% | 3-5% | > 5% |
| 方法长度 | 函数行数 | < 20 | 20-50 | > 50 |
| 类长度 | 类行数 | < 200 | 200-500 | > 500 |
| 参数数量 | 函数参数个数 | < 4 | 4-6 | > 6 |
| 嵌套深度 | 代码嵌套层级 | < 3 | 3-5 | > 5 |

### 代码质量优化策略

#### 降低复杂度
```
策略:
  - 提取方法：将复杂逻辑拆分为小函数
  - 使用卫语句：减少嵌套层级
  - 多态替代条件：用策略模式替代复杂switch/if
  - 引入解释变量：简化复杂表达式

示例:
  // 重构前
  function calculatePrice(order) {
    let price = order.basePrice;
    if (order.customer.type === 'VIP') {
      if (order.amount > 1000) {
        price *= 0.8;
      } else {
        price *= 0.9;
      }
    } else if (order.customer.type === 'MEMBER') {
      price *= 0.95;
    }
    return price;
  }

  // 重构后
  function calculatePrice(order) {
    const discount = getDiscount(order.customer.type, order.amount);
    return order.basePrice * discount;
  }

  function getDiscount(customerType, amount) {
    const discounts = {
      'VIP': amount > 1000 ? 0.8 : 0.9,
      'MEMBER': 0.95,
      'DEFAULT': 1.0
    };
    return discounts[customerType] || discounts['DEFAULT'];
  }
```

#### 消除重复代码
```
策略:
  - 提取共性到父类/基类
  - 使用模板方法模式
  - 提取工具函数
  - 使用组合替代继承

示例:
  // 重构前
  class PDFReport {
    generateHeader() { /* ... */ }
    generateBody() { /* ... */ }
    generateFooter() { /* ... */ }
  }

  class ExcelReport {
    generateHeader() { /* 相同逻辑 */ }
    generateBody() { /* ... */ }
    generateFooter() { /* 相同逻辑 */ }
  }

  // 重构后
  abstract class Report {
    generateHeader() { /* 通用实现 */ }
    generateFooter() { /* 通用实现 */ }
    abstract generateBody(): void;
  }

  class PDFReport extends Report {
    generateBody() { /* PDF特定实现 */ }
  }

  class ExcelReport extends Report {
    generateBody() { /* Excel特定实现 */ }
  }
```

#### 优化命名
```
策略:
  - 使用意图导向的命名
  - 避免缩写（除非是通用缩写）
  - 使用领域术语
  - 保持命名一致性

示例:
  // 重构前
  function calc(d) {
    return d * 0.05;
  }

  // 重构后
  function calculateDiscountPrice(originalPrice) {
    const DISCOUNT_RATE = 0.05;
    return originalPrice * DISCOUNT_RATE;
  }
```

### 代码质量检查工具

| 工具 | 语言 | 功能 | 集成方式 |
|------|------|------|----------|
| SonarQube | 多语言 | 全面质量分析 | CI/CD集成 |
| ESLint | JavaScript | 代码规范检查 | 编辑器/CI |
| Pylint | Python | 代码规范检查 | 编辑器/CI |
| Checkstyle | Java | 代码规范检查 | 编辑器/CI |
| RuboCop | Ruby | 代码规范检查 | 编辑器/CI |
| CodeClimate | 多语言 | 质量分析平台 | Git集成 |

## 覆盖率验证

### 覆盖率验证流程

```
1. 覆盖率基线建立
   - 确定当前覆盖率水平
   - 设定目标覆盖率
   - 识别覆盖率盲区

2. 覆盖率监控
   - 每次提交检查覆盖率
   - 趋势分析
   - 告警设置

3. 覆盖率提升
   - 优先补充关键路径测试
   - 识别难以测试的代码
   - 重构以提高可测试性

4. 覆盖率报告
   - 生成详细报告
   - 识别未覆盖代码
   - 提供改进建议
```

### 覆盖率验证策略

```
增量覆盖率:
  - 新代码覆盖率必须 >= 80%
  - 修改代码不能降低整体覆盖率
  - 关键路径必须100%覆盖

整体覆盖率:
  - 行覆盖率 >= 80%
  - 分支覆盖率 >= 75%
  - 函数覆盖率 >= 90%

覆盖率豁免:
  - 配置代码
  - 自动生成的代码
  - 简单的getter/setter
  - 需要明确记录豁免原因
```

### 覆盖率提升技巧

```
1. 识别盲区
   - 使用覆盖率报告
   - 分析未覆盖代码
   - 确定优先级

2. 补充测试
   - 边界条件测试
   - 异常路径测试
   - 组合场景测试

3. 重构代码
   - 提取可测试的逻辑
   - 减少依赖
   - 使用依赖注入

4. 使用测试替身
   - Mock外部依赖
   - Stub复杂逻辑
   - Fake简化实现
```

## 代码审查能力

### 代码审查流程

```
1. 审查前准备
   - 了解需求背景
   - 阅读相关文档
   - 设置审查环境

2. 代码审查执行
   - 按检查清单逐项检查
   - 记录发现的问题
   - 评估问题严重程度

3. 审查反馈
   - 撰写审查意见
   - 与开发者沟通
   - 确认修改方案

4. 审查后验证
   - 验证问题修复
   - 确认无新问题引入
   - 批准合并
```

### 代码审查检查清单

#### 功能性检查
```
□ 代码是否实现了需求
□ 边界条件是否处理
□ 错误处理是否完善
□ 并发安全性
□ 资源泄漏检查
```

#### 代码质量检查
```
□ 代码可读性
□ 命名是否清晰
□ 注释是否恰当
□ 复杂度是否合理
□ 重复代码检查
```

#### 架构设计检查
```
□ SOLID原则遵守
□ 设计模式使用
□ 模块划分合理
□ 依赖关系清晰
□ 扩展性考虑
```

#### 测试检查
```
□ 测试覆盖充分
□ 测试用例质量
□ 测试独立性
□ 边界条件测试
□ 异常路径测试
```

#### 安全与性能检查
```
□ 输入验证
□ 敏感数据处理
□ SQL注入防护
□ XSS防护
□ 性能影响评估
```

### 代码审查最佳实践

```
1. 审查粒度
   - 每次审查200-400行代码
   - 审查时间控制在1小时内
   - 复杂逻辑需要更多时间

2. 审查态度
   - 对事不对人
   - 提供建设性意见
   - 解释"为什么"而非仅说"怎么做"

3. 审查工具
   - 使用代码审查工具
   - 集成到工作流
   - 保留审查历史

4. 审查文化
   - 鼓励团队参与
   - 知识共享
   - 持续改进
```

## 代码异味检测清单

详细的代码异味检测清单（包括代码结构异味、重复异味、面向对象异味、设计异味、命名异味、复杂度异味、架构异味）请参考 [代码异味清单](../../resources/daima_yiwei_qingdan.md)。

## 架构原则审查

### SOLID原则检查流程

```
1. 单一职责原则 (SRP) 检查
   - 分析类的职责数量
   - 检查变更原因是否唯一
   - 识别需要拆分的类

2. 开放封闭原则 (OCP) 检查
   - 评估扩展机制
   - 检查修改现有代码的频率
   - 识别策略模式应用机会

3. 里氏替换原则 (LSP) 检查
   - 验证子类行为一致性
   - 检查继承关系合理性
   - 识别违反契约的行为

4. 接口隔离原则 (ISP) 检查
   - 分析接口方法使用率
   - 检查接口职责单一性
   - 识别需要拆分的接口

5. 依赖倒置原则 (DIP) 检查
   - 分析依赖方向
   - 检查抽象层使用
   - 识别依赖注入机会
```

### 架构质量评估流程

```
1. 架构扫描
   - 调用 ../../subskills/jiagou_yuanze.md 获取架构原则
   - 扫描项目结构和模块划分
   - 分析依赖关系图

2. 原则验证
   - 逐项检查SOLID原则遵守情况
   - 评估内聚度和耦合度
   - 检查分层架构合规性

3. 问题识别
   - 标记违反原则的代码位置
   - 评估问题严重程度
   - 生成问题清单

4. 改进建议
   - 提供重构建议
   - 评估改进优先级
   - 制定改进计划
```

### 架构检查命令示例

详细的架构检查命令示例和配置请参考 [架构检查命令资源](../../resources/jiagou_jiancha_mingling.md)。

## 问题跟踪机制

详细的问题跟踪模板和流程（包括问题生命周期、状态定义、优先级定义、分类、跟踪流程、统计报告）请参考 [问题跟踪模板](../../resources/wenti_genzong_muban.md)。

## 白盒化推理链要求

### Bug定位推理过程记录

- 记录Bug发现到定位的完整推理链
- 推理链内容包括：
  - 问题现象描述
  - 问题复现步骤
  - 初步假设列表
  - 假设验证过程（每个假设的验证方法、结果、结论）
  - 根因定位过程
  - 定位依据与证据链

### 问题诊断推理过程记录

- 记录问题诊断的完整推理过程
- 诊断推理内容包括：
  - 问题分类推理（Bug类型、严重程度、影响范围）
  - 代码分析推理（代码路径追踪、依赖关系分析）
  - 修复方案推理（候选方案、方案评估、最终选择）
  - 风险评估推理（修复风险、回归风险、兼容性风险）

### 推理链文档格式

- 采用结构化格式记录推理过程
- 每个推理步骤需包含：
  - 步骤编号
  - 推理类型（假设/验证/结论）
  - 推理内容
  - 依据来源（日志/代码/测试/文档）
  - 时间戳
- 推理链应可追溯、可审查

## 输出物清单

| 输出物 | 说明 |
|--------|------|
| 推理链文档 | Bug定位和问题诊断推理过程 |
| 重构报告 | 重构内容和效果记录 |
| 性能优化报告 | 性能优化结果报告 |
| 修复验证报告 | 修复效果验证报告 |
| 规范一致性报告 | 规范一致性验证结果 |
| 规范驱动重构决策记录 | 规范驱动的重构决策依据 |
| 代码质量报告 | 代码质量指标和分析 |
| 覆盖率报告 | 测试覆盖率统计 |
| 代码审查报告 | 审查发现和建议 |

## 透明度记录要求

### 重构决策记录

- 记录重构决策依据：包括代码质量指标、技术债务评估、业务影响分析
- 记录问题诊断推理过程：包括问题定位方法、根因分析、修复方案评估

### 记录内容规范

```
- 决策时间戳
- 问题/优化点描述
- 诊断过程记录
- 重构方案选择理由
- 风险评估与缓解措施
- 重构前后对比指标
```

## 协同调用接口

### 接口定义

刑部作为问题修复机构，提供以下协同调用接口供其他技能调用：

| 接口名称 | 接口描述 | 调用方 |
|----------|----------|--------|
| `refactor_code` | 代码重构接口 | 工部、尚书省 |
| `fix_bug` | Bug修复接口 | 兵部、尚书省 |

---

## 协同效果评估能力

### 持续重构协同评估指标

刑部作为代码重构机构，负责评估持续重构在三省六部协同中的效果。

| 评估维度 | 指标 | 目标值 | 度量方法 |
|----------|------|--------|----------|
| 代码质量提升 | 复杂度降低率 | ≥15% | 代码质量工具统计 |
| 重构覆盖率 | 重构代码比例 | ≥60% | 代码变更统计 |
| 测试保持率 | 重构后测试通过率 | 100% | 测试结果统计 |
| 技术债务减少 | 债务减少率 | ≥20% | 技术债务统计 |
| 性能提升 | 性能优化效果 | ≥10% | 性能测试对比 |

### 持续重构协同评估报告格式

```json
{
  "evaluation_id": "EVAL-XINGBU-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-07T23:59:59Z"
  },
  "refactoring_metrics": {
    "total_refactorings": 35,
    "successful_refactorings": 33,
    "failed_refactorings": 2,
    "avg_refactoring_time_minutes": 25
  },
  "quality_metrics": {
    "complexity_before": 12.5,
    "complexity_after": 10.2,
    "complexity_reduction_rate": 0.184,
    "duplication_before": 8.5,
    "duplication_after": 5.2,
    "duplication_reduction_rate": 0.388
  },
  "test_metrics": {
    "tests_before": 150,
    "tests_after": 150,
    "pass_rate_before": 1.0,
    "pass_rate_after": 1.0,
    "test_preservation_rate": 1.0
  },
  "debt_metrics": {
    "technical_debt_hours_before": 45,
    "technical_debt_hours_after": 32,
    "debt_reduction_rate": 0.289,
    "code_smells_fixed": 28
  },
  "performance_metrics": {
    "response_time_before_ms": 250,
    "response_time_after_ms": 180,
    "performance_improvement_rate": 0.28
  },
  "recommendations": [
    {
      "category": "refactoring_focus",
      "priority": "medium",
      "description": "增加对核心模块的重构投入",
      "expected_impact": "预计技术债务再减少15%"
    }
  ]
}
```

---

## 流水线协调能力

### 流水线持续重构节点

刑部在白盒化7阶段流水线中负责持续重构阶段的执行。

| 阶段 | 刑部角色 | 重构内容 | 输出物 |
|------|----------|----------|--------|
| 需求分析 | 支持 | 代码质量评估 | 质量评估报告 |
| SDD规范定义 | 支持 | 规范一致性检查 | 规范检查报告 |
| 审议批准 | 支持 | 代码审查 | 审查报告 |
| 测试先行 | 支持 | 测试代码质量检查 | 测试质量报告 |
| 代码实现 | 支持 | 代码质量监控 | 质量监控报告 |
| 持续重构 | 主导 | 代码重构优化 | 重构报告 |
| 部署发布 | 支持 | 部署前质量检查 | 质量检查报告 |

### 流水线重构配置

```yaml
pipeline_refactoring_config:
  refactoring_execution:
    mode: "continuous"
    automated: true
    test_preservation: true
    
  refactoring_rules:
    - trigger: "complexity_threshold"
      threshold: 15
      action: "suggest_refactoring"
      
    - trigger: "duplication_threshold"
      threshold: 5
      action: "auto_extract"
      
    - trigger: "test_pass_rate"
      threshold: 1.0
      action: "allow_refactoring"
      
  quality_gates:
    - name: "test_preservation"
      check: "all_tests_pass"
      blocking: true
      
    - name: "complexity_improvement"
      check: "complexity_reduced"
      blocking: false
```

---

## 增强功能集成

### 与provincial_coordinator集成

刑部通过provincial_coordinator.py实现重构流程的自动化和协同：

```python
from scripts.provincial_coordinator import (
    SmartDispatcher,
    TaskRequirement,
    TaskPriority
)

dispatcher = SmartDispatcher()

def execute_refactoring_for_task(task_id: str, refactoring_requirements: dict):
    requirement = TaskRequirement(
        task_id=task_id,
        required_capabilities={
            "code_refactoring": 0.9,
            "quality_optimization": 0.85
        },
        preferred_specializations=["xingbu"],
        priority=TaskPriority.MEDIUM
    )
    
    decision = dispatcher.find_best_match(requirement, "ministry")
    
    return {
        "assigned_entity": decision.assigned_entity,
        "match_score": decision.overall_score,
        "refactoring_execution": refactoring_requirements
    }
```

---

## 重构质量保障

### 重构质量检查清单

```
□ 重构前测试全部通过
□ 重构有明确目标
□ 重构步骤小而安全
□ 重构后测试全部通过
□ 代码质量指标有提升
□ 重构过程记录完整
□ 无功能回归
□ 性能无明显下降
```

### 重构质量评分

| 评分项 | 权重 | 评分标准 |
|--------|------|----------|
| 测试保持率 | 30% | 重构后测试全部通过 |
| 质量提升 | 25% | 代码质量指标提升 |
| 安全性 | 20% | 无功能回归 |
| 效率 | 15% | 重构时间合理 |
| 可维护性 | 10% | 重构后代码更易维护 |
| `analyze_code_quality` | 代码质量分析接口 | 门下省、工部 |
| `verify_compliance` | 规范一致性验证接口 | 门下省 |

### 输入参数规范

#### 代码重构接口参数

```json
{
  "interface": "refactor_code",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "target": {
      "path": "代码路径",
      "scope": "file|module|project"
    },
    "refactor_type": "extract_method|rename|simplify|remove_duplication",
    "constraints": {
      "preserve_behavior": true,
      "run_tests": true,
      "max_changes": 50
    },
    "spec_reference": {
      "spec_path": "规范文档路径",
      "spec_version": "1.0.0"
    }
  }
}
```

#### Bug修复接口参数

```json
{
  "interface": "fix_bug",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "bug_info": {
      "bug_id": "Bug ID",
      "description": "Bug描述",
      "severity": "critical|major|minor",
      "location": {
        "file": "文件路径",
        "line": 42
      }
    },
    "diagnosis": {
      "root_cause": "根因分析",
      "affected_components": ["受影响组件"]
    },
    "fix_options": {
      "auto_fix": true,
      "create_test": true,
      "review_required": false
    }
  }
}
```

#### 代码质量分析接口参数

```json
{
  "interface": "analyze_code_quality",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "target_path": "代码路径",
    "analysis_types": [
      "complexity",
      "duplication",
      "code_smell",
      "architecture_compliance"
    ],
    "thresholds": {
      "max_complexity": 10,
      "max_duplication": 3,
      "max_method_length": 50
    }
  }
}
```

### 输出格式规范

```json
{
  "interface": "refactor_code",
  "call_id": "REFACTOR-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "status": "success|failure|partial",
  "result": {
    "changes": [
      {
        "file": "文件路径",
        "type": "extract_method|rename|simplify",
        "description": "变更描述",
        "lines_changed": 10
      }
    ],
    "metrics": {
      "complexity_before": 15,
      "complexity_after": 8,
      "duplication_before": 5,
      "duplication_after": 0
    },
    "test_result": {
      "passed": true,
      "coverage": 0.85
    }
  }
}
```

### 调用示例

```bash
# 调用代码重构接口
调用 ./SKILL.md --interface=refactor_code \
  --target='{"path":"./src/utils.py","scope":"file"}' \
  --refactor-type="extract_method" \
  --constraints='{"preserve_behavior":true}'

# 调用Bug修复接口
调用 ./SKILL.md --interface=fix_bug \
  --bug-info='{"bug_id":"BUG-001","severity":"major"}' \
  --fix-options='{"auto_fix":true}'

# 调用代码质量分析接口
调用 ./SKILL.md --interface=analyze_code_quality \
  --target-path="./src/" \
  --analysis-types='["complexity","duplication"]'
```

---

## 下属四司

| 司名 | 职责 |
|------|------|
| xingbucangsi（刑部仓司） | 问题追踪 |
| dubucangsi（都部仓司） | 代码重构 |
| bibucangsi（比部仓司） | 性能优化 |
| sibucangsi（司部仓司） | 质量保证 |

---

## 重构自动化增强

### 自动重构检测

```yaml
auto_refactor_detection:
  triggers:
    - type: "complexity_threshold"
      condition: "cyclomatic_complexity > 15"
      action: "suggest_extract_method"
      
    - type: "duplication"
      condition: "duplicate_lines > 10"
      action: "suggest_extract_common"
      
    - type: "code_smell"
      patterns:
        - "long_parameter_list"
        - "large_class"
        - "feature_envy"
      action: "generate_refactor_suggestions"
      
  auto_apply:
    enabled: false
    require_approval: true
    safe_refactors:
      - "rename_variable"
      - "extract_constant"
      - "simplify_boolean"
```

### 重构影响分析

```json
{
  "impact_analysis": {
    "refactor_id": "REF-001",
    "target": "src/services/user_service.py",
    "refactor_type": "extract_method",
    "affected_components": [
      {
        "type": "file",
        "path": "src/services/user_service.py",
        "change_type": "modified",
        "risk_level": "low"
      },
      {
        "type": "test",
        "path": "tests/test_user_service.py",
        "change_type": "none",
        "risk_level": "none"
      }
    ],
    "dependency_impact": {
      "incoming": 5,
      "outgoing": 3,
      "circular": 0
    },
    "test_coverage": {
      "before": 0.85,
      "after_estimate": 0.85
    },
    "risk_assessment": {
      "overall_risk": "low",
      "rollback_complexity": "simple",
      "estimated_time_minutes": 15
    }
  }
}
```

### 重构执行记录

```json
{
  "refactor_log": {
    "log_id": "LOG-001",
    "timestamp": "2024-01-01T00:00:00Z",
    "refactor_type": "extract_method",
    "before": {
      "file": "src/services/user_service.py",
      "method": "process_user",
      "lines": 85,
      "complexity": 18
    },
    "after": {
      "file": "src/services/user_service.py",
      "methods": ["process_user", "validate_user_data", "save_user"],
      "lines": [25, 20, 25],
      "complexity": [5, 4, 6]
    },
    "test_result": {
      "before": "all_passed",
      "after": "all_passed",
      "coverage_maintained": true
    },
    "approved_by": "code_review",
    "execution_time_seconds": 45
  }
}
