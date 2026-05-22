# 六部工作流程

> ⚔️ **六部协同，TDD驱动** - 通过吏部、户部、礼部、兵部、工部、刑部的协同工作，实现TDD红绿蓝循环的完整执行 | **v3.3.0: 自动化测试流水线 + 质量门禁**

---

## v3.3.0 更新

### 🔄 自动化流水线集成

六部工作流程现已完全集成到CI/CD自动化流水线：

```
GitHub Actions Pipeline
├── lint (吏部+礼部: 代码规范检查)
├── type-check (礼部: 类型检查)
├── test-skillscripts (兵部: 单元测试矩阵)
│   └── Python 3.10 / 3.11 / 3.12
├── test-backend (兵部+工部: 完整测试套件)
│   ├── unit-tests (单元测试)
│   ├── integration-tests (集成测试)
│   └── e2e-tests (E2E测试)
├── security-scan (刑部: 安全扫描)
│   ├── Bandit (代码安全)
│   └── Safety (依赖安全)
└── report (尚书省: 报告生成与归档)
```

### 📊 质量门禁配置

新增统一质量门禁配置文件 `skillscripts/core/quality_gate_config.yaml`：

```yaml
quality_gate:
  coverage:
    line_coverage_min: 95      # 行覆盖率 ≥ 95%
    branch_coverage_min: 90    # 分支覆盖率 ≥ 90%
  
  defects:
    critical_max: 0            # 严重缺陷 = 0
    severe_max: 2              # 严重缺陷 ≤ 2
  
  security:
    owasp_high_risk_max: 0     # 高风险安全问题 = 0
```

**六部门在CI/CD中的角色映射**：

| 部门 | CI/CD Job | 核心职责 |
|------|-----------|----------|
| 吏部 | workflow_dispatch | 任务创建与环境配置 |
| 户部 | services (postgres/redis) | 资源管理 |
| 礼部 | lint + type-check | 规范制定与代码审查 |
| 兵部 | test-* jobs | 测试先行（红阶段） |
| 工部 | build job | 代码实现与构建（绿阶段） |
| 刑部 | security-scan | 重构优化与安全扫描（蓝阶段） |

---

## 概述

六部协调机制是尚书省下属的执行层，通过吏部、户部、礼部、兵部、工部、刑部的协同工作，实现TDD红绿蓝循环的完整执行。

---

## 六部协调机制

### 部门职责矩阵

| 部门 | 核心职责 | TDD角色 | 关键产出 | 子技能路径 |
|------|----------|---------|----------|-----------|
| **吏部**<br>👥 | 人员调度<br>Agent分配 | 分配 TDD 角色 | 角色分配表<br>任务清单 | [shangshusheng/libu/SKILL.md](../shangshusheng/libu/SKILL.md) |
| **户部**<br>💰 | 资源管理<br>环境配置 | 管理测试环境资源 | 资源配置表<br>环境清单 | [shangshusheng/hubu/SKILL.md](../shangshusheng/hubu/SKILL.md) |
| **礼部**<br>📜 | 规范制定<br>代码审查 | 制定 TDD 编码规范 | 编码规范<br>审查清单 | [shangshusheng/liibu/SKILL.md](../shangshusheng/liibu/SKILL.md) |
| **兵部** ⭐<br>🧪 | **测试先行**<br>测试策略 | **编写测试用例**<br>红阶段 | 单元测试<br>集成测试<br>E2E测试 | [shangshusheng/bingbu/SKILL.md](../shangshusheng/bingbu/SKILL.md) |
| **刑部** ⭐<br>🔧 | **持续重构**<br>质量优化 | **优化代码质量**<br>蓝阶段 | 重构方案<br>质量报告 | [shangshusheng/xingbu/SKILL.md](../shangshusheng/xingbu/SKILL.md) |
| **工部** ⭐<br>🔨 | **测试执行**<br>代码实现 | **实现代码**<br>绿阶段 | 功能代码<br>实现文档 | [shangshusheng/gongbu/SKILL.md](../shangshusheng/gongbu/SKILL.md) |

> ⭐ 标记部门为 TDD 核心执行部门

### 六部协作时序

```
时间轴 ──────────────────────────────────────────────────────────→

阶段1: 准备
├─ 吏部: 分配角色、创建任务
├─ 户部: 配置环境、分配资源
└─ 礼部: 制定规范、审查标准

阶段2: 红 🔴 (兵部主导)
├─ 兵部: 编写测试用例 (预期失败)
├─ 礼部: 审查测试规范
└─ 户部: 确保测试环境就绪

阶段3: 绿 🟢 (工部主导)
├─ 工部: 编写最小代码使测试通过
├─ 兵部: 验证测试通过
└─ 吏部: 记录任务进度

阶段4: 蓝 🔵 (刑部主导)
├─ 刑部: 代码重构优化
├─ 兵部: 验证测试仍通过
├─ 礼部: 代码规范审查
└─ 户部: 更新资源使用记录

阶段5: 循环
└─ 返回阶段2，直到功能完成
```

---

## TDD 红绿蓝循环详解

### 循环概述

```
        ┌─────────────────────────────────────┐
        │                                     │
        ▼                                     │
   ┌─────────┐    ┌─────────┐    ┌─────────┐ │
   │ 🔴 红   │───→│ 🟢 绿   │───→│ 🔵 蓝   │─┘
   │  编写   │    │  实现   │    │  重构   │
   │ 测试    │    │ 代码    │    │ 优化    │
   └─────────┘    └─────────┘    └─────────┘
        │              │              │
        ▼              ▼              ▼
   测试失败        测试通过        测试通过
   (预期)          (最小代码)      (优化质量)
```

### 详细步骤说明

#### 🔴 红阶段 - 兵部负责

```python
# 1. 明确需求：用户注册功能
# 2. 编写测试（在实现代码之前）

# test_user_service.py
def test_register_user_success():
    """测试用户注册成功场景"""
    # Arrange
    user_data = {"username": "testuser", "email": "test@example.com", "password": "secure123"}
    
    # Act
    result = user_service.register(user_data)
    
    # Assert
    assert result.success is True
    assert result.user_id is not None
    assert result.message == "注册成功"

def test_register_user_duplicate_email():
    """测试重复邮箱注册失败"""
    # Arrange
    existing_user = create_user(email="exists@example.com")
    user_data = {"username": "newuser", "email": "exists@example.com", "password": "secure123"}
    
    # Act
    result = user_service.register(user_data)
    
    # Assert
    assert result.success is False
    assert result.error_code == "EMAIL_EXISTS"
```

> **关键原则**：测试必须先失败，证明测试有效

## 🟢 绿阶段 - 工部负责

```python
# 3. 编写最小代码使测试通过

# user_service.py
class UserService:
    def __init__(self, user_repository):
        self.user_repository = user_repository
    
    def register(self, user_data):
        # 最小实现：仅满足测试要求
        existing = self.user_repository.find_by_email(user_data["email"])
        if existing:
            return RegisterResult(success=False, error_code="EMAIL_EXISTS")
        
        user_id = self.user_repository.create(user_data)
        return RegisterResult(success=True, user_id=user_id, message="注册成功")
```

> **关键原则**：代码刚好使测试通过，不过度设计

## 🔵 蓝阶段 - 刑部负责

```python
# 4. 重构优化，保持测试通过

# 重构前的问题：
# - 魔法字符串
# - 缺乏输入验证
# - 没有日志记录
# - 异常处理不完善

# 重构后的代码：
class UserService:
    ERROR_EMAIL_EXISTS = "EMAIL_EXISTS"
    MSG_REGISTER_SUCCESS = "注册成功"
    
    def __init__(self, user_repository, validator, logger):
        self.user_repository = user_repository
        self.validator = validator
        self.logger = logger
    
    def register(self, user_data):
        try:
            # 输入验证
            validation_result = self.validator.validate_user_data(user_data)
            if not validation_result.is_valid:
                return RegisterResult(success=False, errors=validation_result.errors)
            
            # 检查邮箱唯一性
            if self._email_exists(user_data["email"]):
                return RegisterResult(
                    success=False, 
                    error_code=self.ERROR_EMAIL_EXISTS
                )
            
            # 创建用户
            user_id = self._create_user(user_data)
            
            self.logger.info(f"User registered: {user_id}")
            
            return RegisterResult(
                success=True, 
                user_id=user_id, 
                message=self.MSG_REGISTER_SUCCESS
            )
            
        except Exception as e:
            self.logger.error(f"Registration failed: {e}")
            return RegisterResult(success=False, error_code="INTERNAL_ERROR")
    
    def _email_exists(self, email):
        return self.user_repository.find_by_email(email) is not None
    
    def _create_user(self, user_data):
        hashed_password = self._hash_password(user_data["password"])
        return self.user_repository.create({
            **user_data,
            "password_hash": hashed_password
        })
```

> **关键原则**：不改变外部行为，提升内部质量

## 循环节奏指南

| 循环粒度 | 时间盒 | 适用场景 | 产出 |
|----------|--------|----------|------|
| **微循环** | 5-10 分钟 | 单个函数/方法 | 1个功能 + 测试 |
| **小循环** | 30-60 分钟 | 单个功能点 | 1个用户故事 |
| **中循环** | 2-4 小时 | 功能模块 | 1个功能模块 |
| **大循环** | 1-2 天 | 完整特性 | 1个完整特性 |

> 📖 **详细内容**请参考 [TDD循环流程](tdd_liucheng.md)

---

## SDD 规范驱动开发

### 核心理念

```
规范先行 → 规范即契约 → 规范驱动生成 → 规范持续验证
```

### 规范文件结构

```markdown
# SDD 规范文件模板 (sdd_<模块名>.md)

## 1. 接口规范
- API 端点定义
- 请求/响应格式
- 错误码定义

## 2. 数据模型规范
- 实体定义
- 字段类型与约束
- 关系定义

## 3. 行为规则规范
- 业务规则
- 状态流转
- 验证规则

## 4. 测试规范
- 测试场景
- 边界条件
- 验收标准
```

### 规范驱动生成流程

```
SDD 规范文件
    │
    ├──→ 解析器 → 生成测试用例 → 兵部使用
    │
    ├──→ 解析器 → 生成代码骨架 → 工部使用
    │
    └──→ 解析器 → 生成 API 文档 → 礼部使用
```

### 规范示例

```markdown
## 用户注册接口规范

### 接口定义
POST /api/v1/users/register

### 请求参数
| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| username | string | 是 | 3-20字符，字母开头 |
| email | string | 是 | 有效邮箱格式 |
| password | string | 是 | 8-32字符，含大小写+数字 |

### 响应格式
```json
{
  "success": boolean,
  "user_id": string | null,
  "message": string,
  "error_code": string | null
}
```

### 业务规则
1. 邮箱必须全局唯一
2. 密码必须加密存储
3. 注册成功后发送验证邮件

### 错误码
| 错误码 | 说明 |
|--------|------|
| EMAIL_EXISTS | 邮箱已存在 |
| INVALID_EMAIL | 邮箱格式无效 |
| WEAK_PASSWORD | 密码强度不足 |
```

> 📖 **详细内容**请参考 [SDD规范驱动开发](sdd_liucheng.md)

---

## 自动化流水线

### 流水线架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        自动化流水线                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌────────┐│
│  │ 代码提交 │──→│ 静态检查 │──→│ 单元测试 │──→│ 集成测试 │──→│ 构建   ││
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘   └───┬────┘│
│       │                                                      │     │
│       ↓                                                      ↓     │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌────────┐│
│  │ 文档生成 │   │ 代码审查 │   │ 覆盖率  │   │ E2E测试  │──→│ 部署   ││
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘   └────────┘│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 流水线阶段详解

#### 1. 静态代码检查

```bash
# 代码风格检查
python scripts/lint_check.py --style

# 类型检查
python scripts/type_check.py --strict

# 安全扫描
python scripts/security_scan.py --full

# 代码异味检测
python scripts/code_smell_check.py
```

**检查项清单**：
- [ ] 代码风格合规（PEP8/ESLint/Prettier）
- [ ] 类型注解完整
- [ ] 无安全漏洞
- [ ] 无代码异味
- [ ] 复杂度达标（圈复杂度 < 10）

## 2. 自动化测试

```bash
# 单元测试
pytest tests/unit --cov=src --cov-report=html

# 集成测试
pytest tests/integration -v

# E2E测试
pytest tests/e2e --browser=chrome

# 覆盖率检查
python scripts/coverage_check.py --threshold=80
```

**测试门禁**：

| 测试类型 | 覆盖率要求 | 通过标准 |
|----------|------------|----------|
| 单元测试 | ≥ 80% | 100% 通过 |
| 集成测试 | ≥ 60% | 100% 通过 |
| E2E测试 | 核心流程 | 100% 通过 |

## 3. 文档自动生成

```bash
# API 文档生成
python scripts/generate_api_docs.py --format=openapi

# 代码文档生成
python scripts/generate_code_docs.py --style=google

# 架构图生成
python scripts/generate_arch_diagrams.py

# 变更日志生成
python scripts/generate_changelog.py --since=last-release
```

**生成文档清单**：
- [ ] API 文档（OpenAPI/Swagger）
- [ ] 代码文档（Docstring 提取）
- [ ] 架构图（模块依赖图）
- [ ] 变更日志（Commit 历史）
- [ ] 测试报告（覆盖率、通过率）

## 4. 自动化代码审查

```bash
# 启动审查流程
python scripts/code_review.py --auto

# 生成审查报告
python scripts/generate_review_report.py
```

**审查维度**：

| 维度 | 检查内容 | 工具 |
|------|----------|------|
| 架构合规 | MVVM/SOLID/DRY | architecture_check.py |
| 测试覆盖 | 测试完整性 | coverage_check.py |
| 安全合规 | OWASP Top 10 | security_scan.py |
| 性能指标 | 响应时间/内存 | performance_check.py |

## 5. 持续部署

```bash
# 构建镜像
docker build -t app:${VERSION} .

# 部署到测试环境
python scripts/deploy.py --env=staging

# 运行冒烟测试
python scripts/smoke_test.py --env=staging

# 部署到生产环境
python scripts/deploy.py --env=production
```

> 📖 **详细内容**请参考 [白盒化流水线](baihehua_liushuixian.md)

---

## 测试体系

### 测试金字塔

```
        /\
       /  \     E2E测试 (少量)
      /____\    ─────────────────
     /      \   集成测试 (中等)
    /________\  ─────────────────
   /          \ 单元测试 (大量)
  /____________\
```

### 核心功能

- 🧪 单元测试（pytest/jest）
- 🔗 集成测试（API/DB）
- 🎭 E2E测试（Playwright/Cypress）
- 📊 测试覆盖率管理

### 测试命令

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit -v

# 运行集成测试
pytest tests/integration -v

# 运行E2E测试
pytest tests/e2e --headed

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

> 📖 **详细内容**请参考 [测试体系](ceshi.md)

---

## 设计与 TDD 协同

| 设计产出物 | 对应测试类型 | 负责部门 | 产出时机 |
|------------|--------------|----------|----------|
| 接口定义 | 单元测试 | 兵部 | 设计阶段 |
| 模块交互图 | 集成测试 | 兵部 | 设计阶段 |
| 用户流程图 | E2E测试 | 兵部 | 设计阶段 |
| 数据模型 | 数据测试 | 兵部 | 设计阶段 |
| 状态机图 | 状态测试 | 兵部 | 设计阶段 |
| 异常场景 | 异常测试 | 兵部 | 设计阶段 |

---

## v4.0 更新

### 🏛️ 二十四司精细化工作流体系

v4.0 将原有的 **六部** 架构扩展为 **六部 × 4司 = 24司** 精细化执行体系，每个部下设4个专业司，实现更细粒度的职责划分和专业化执行。

#### 二十四司组织架构总览

```
v4.0 三省六部二十四司 架构
═══════════════════════════

  ┌─────────────────────────────────────────────────────────────┐
  │                     中书省 (决策层)                           │
  │                   4局 × 4司 = 16司                            │
  ├──────────────┬──────────────┬──────────────┬─────────────────┤
  │ 需求分析局    │ 架构设计局    │ 规范制定局    │ 方案审议局       │
  │              │              │              │                 │
  │ 用户研究司   │ 系统架构司   │ 编码规范司   │ 方案评审司      │
  │ 需求拆解司   │ 技术选型司   │ 文档标准司   │ 风险评估司      │
  │ 验收标准司   │ 接口定义司   │ 命名约定司   │ 决策记录司 ←DecisionLog│
  │ 优先级排序司  │ ADR记录司    │ Lint规则司   │ 影响分析司      │
  └──────────────┴──────────────┴──────────────┴─────────────────┘
                          ↓ 审议通过
  ┌─────────────────────────────────────────────────────────────┐
  │                     门下省 (审核层)                           │
  │                   4局 × 4司 = 16司                            │
  ├──────────────┬──────────────┬──────────────┬─────────────────┤
  │ 代码审查局    │ 测试验证局    │ 质量监控局    │ 合规审计局       │
  │              │              │              │                 │
  │ 静态分析司   │ 策略制定司   │ 指标采集司   │ 许可证审计司    │
  │ 安全扫描司   │ 用例设计司   │ 趋势分析司   │ 安全合规司      │
  │ 性能审计司   │ 执行管理司   │ 预警告警司   │ 数据隐私司      │
  │ 审查报告司   │ 覆盖分析司   │ 门禁把控司   │ 整改跟踪司      │
  └──────────────┴──────────────┴──────────────┴─────────────────┘
                          ↓ 全部通过
  ┌─────────────────────────────────────────────────────────────┐
  │                  尚书省 (执行层)                              │
  │                6部 × 4司 = 24司                               │
  ├──────────────┬──────────────┬──────────────┬─────────────────┤
  │     吏部      │     户部      │     礼部      │     兵部        │
  │  [MARC-Lite]  │[SecretsMgr]  │[Decision Log]│ [TDD/Clause]   │
  ├──────────────┤ ├──────────────┤ ├──────────────┤ ├──────────────┤
  │ Agent调度司   │ 环境配置司   │ 文档司       │ TDD执行司      │
  │ 角色管理司    │ 依赖管理司   │ 模板管理司   │ 测试框架司      │
  │ 技能匹配司    │ 资源优化司   │ 知识库司     │ 覆盖分析司      │
  │ 协调司       │ 基础设施司   │ 标准化司     │ 回归测试司      │
  ├──────────────┼──────────────┼──────────────┼─────────────────┤
  │     工部      │     刑部      │               │                │
  │ [UX Integration]│[四维防线L4]  │               │                │
  ├──────────────┤ ├──────────────┤               │                │
  │ 代码生成司    │ Bug修复司    │               │                │
  │ UI/UX设计司   │ 重构司       │               │                │
  │ 数据库设计司   │ 自演化司←四维 │               │                │
  │ API设计司     │ 版本控制司   │               │                │
  └──────────────┴──────────────┴──────────────┴─────────────────┘
```

#### 各部门与v4.0模块的集成关系

| 部门 | 核心集成模块 | 主要职责 | 关键司 |
|------|-------------|----------|--------|
| **吏部** | MARC-Lite | Agent调度、资源分配、角色管理 | Agent调度司(MARC)、技能匹配司、协调司 |
| **户部** | SecretsManager + HardcodedDetector | 环境、依赖、基础设施安全 | 环境配置司(Secrets)、基础设施司 |
| **礼部** | Decision Log | 文档、模板、知识库、标准化 | 文档司、标准化司(DecisionLog) |
| **兵部** | Claw-Code契约驱动TDD | 测试先行、测试框架、覆盖率 | TDD执行司(Clause Extraction) |
| **工部** | UX Integration + AgencyBridge | 代码生成、UI/UX设计、API设计 | UI/UX设计司(UX Integration) |
| **刑部** | 四维防线L4兜底恢复 | Bug修复、重构、自演化、版本控制 | 自演化司(四维防线) |

#### 中书省 (决策层) — 4局16司

**需求分析局**
| 司名 | 核心职责 | 输出物 |
|------|----------|--------|
| 用户研究司 | 用户画像、使用场景分析、需求优先级排序 | 用户研究报告 |
| 需求拆解司 | EPIC→Story→Task拆解、需求结构化 | 需求拆解文档 |
| 验收标准司 | 定义DoD/Done、验收条件编写 | AC清单 |
| 优先级排序司 | MoSCoW分类、WSJF评分、依赖关系图 | 优先级矩阵 |

**架构设计局**
| 司名 | 核心职责 | 输出物 |
|------|----------|--------|
| 系统架构司 | 整体架构设计、模块边界定义、技术选型建议 | ADR文档、架构图 |
| 技术选型司 | 技术栈评估、POC验证、选型对比分析 | 技术选型报告 → DecisionLog |
| 接口定义司 | API接口规范、数据模型设计、协议选择 | API Spec |
| ADR记录司 | 架构决策记录、决策依据归档、影响范围分析 | ADR日志 |

**规范制定局**
| 司名 | 核心职责 | 输出物 |
|------|----------|--------|
| 编码规范司 | 代码风格、命名规范、目录结构约定 | .editorconfig, lint规则 |
| 文档标准司 | 文档格式、注释规范、README模板 | 文档模板集 |
| 命名约定司 | 变量/函数/类/文件命名规则 | 命名词典 |
| Lint规则司 | Linter配置、静态检查规则、CI检查项 | lint配置文件 |

**方案审议局** (DecisionLog核心集成)
| 司名 | 核心职责 | v4.0集成 |
|------|----------|----------|
| 方案评审司 | 方案完整性评审、可行性验证 | → DecisionLog |
| 风险评估司 | 技术风险识别、风险矩阵、缓解策略 | → DecisionLog |
| 决策记录司 | 决策过程记录、决策链路追溯 | **DecisionLog.generate()** |
| 影响分析司 | 变更影响范围、兼容性分析、迁移路径 | → DecisionLog |

#### 门下省 (审核层) — 4局16司

**代码审查局** (集成四维防线Layer3)
| 司名 | 核心职责 | 四维防线集成 |
|------|----------|-------------|
| 静态分析司 | 类型检查、语法分析、复杂度度量 | RuleValidationLayer |
| 安全扫描司 | OWASP Top10检测、漏洞扫描 | RuleValidationLayer: 安全扫描 |
| 性能审计司 | 性能基线对比、瓶颈分析 | RuleValidationLayer: 性能基准 |
| 审查报告司 | 审查结果汇总、问题分级、修复建议 | Layer4质量输入 |

**测试验证局 / 质量监控局(六维) / 合规审计局**

各司职责详见[架构总览](architecture_overview.md#v4-0-核心架构组件详解)

#### 尚书省 (执行层) — 6部24司

**吏部** (MARC-Lite集成)
| 司名 | 核心职责 | MARC集成 |
|------|----------|----------|
| Agent调度司 | Agent角色分配、任务分派、负载均衡 | ResourceCoordinator |
| 角色管理司 | Agent角色定义、权限矩阵、能力模型 | AgentQuota |
| 技能匹配司 | 任务→最优Agent匹配、能力评估 | SchedulerQueue |
| 协调司 | 跨部协调、冲突解决、进度同步 | acquire_context |

**户部** (SecretsManager集成)
| 司名 | 核心职责 | Secrets集成 |
|------|----------|------------|
| 环境配置司 | 环境变量管理、.env维护、配置校验 | SecretsManager.load() |
| 依赖管理司 | 依赖版本锁定、安全审计、升级策略 | HardcodedDetector |
| 资源优化司 | 资源占用优化、缓存策略、CDN配置 | 配额管理 |
| 基础设施司 | Docker/K8s配置、CI/CD流水线 | PlatformAdapter |

**礼部** (Decision Log集成)
| 司名 | 核心职责 | DecisionLog集成 |
|------|----------|-----------------|
| 文档司 | API文档、架构文档、变更日志 | generate() |
| 模板管理司 | 文档模板、代码模板、PR模板 | evaluate_outcome() |
| 知识库司 | 最佳实践库、模式库、反模式库 | list_decisions() |
| 标准化司 | 编码标准、Git工作流、PR规范 | get_statistics() |

**兵部** (Claw-Code契约驱动TDD)
| 司名 | 核心职责 | Clause Extraction集成 |
|------|----------|---------------------|
| TDD执行司 | TDD红-绿-蓝循环编排 | **ClauseExtractor** |
| 测试框架司 | pytest/unittest配置、fixture管理 | ClauseToTestMapper |
| 覆盖分析司 | 覆盖率统计、分支覆盖、条款覆盖 | ClauseCoverageReport |
| 回归测试司 | 回归套件管理、冒烟测试、全量回归 | 条款→回归映射 |

**工部** (UX Integration + AgencyBridge)
| 司名 | 核心职责 | 外部生态集成 |
|------|------|-------------|
| 代码生成司 | 代码骨架生成、脚手架搭建 | AgencyBridge.invoke_agent() |
| UI/UX设计司 | UI组件开发、交互逻辑实现 | **UXIntegration** |
| 数据库设计司 | Schema设计、Migration编写、索引优化 | AgencyBridge |
| API设计司 | RESTful/GraphQL API实现、文档生成 | UX Integration validate |

**刑部** (四维防线Layer4兜底恢复)
| 司名 | 核心职责 | 四维防线集成 |
|------|----------|-------------|
| Bug修复司 | Bug定位、根因分析、热修复 | FallbackRecoveryLayer |
| 重构司 | 代码重构、技术债务清理 | RuleValidationLayer |
| 自演化司 | 自动优化建议、模式应用 | **FallbackRecoveryLayer** |
| 版本控制司 | Git策略、Release管理、回滚操作 | rollback_state |

#### 二十四司协同TDD工作流时序

```
时间轴 ──────────────────────────────────────────────────────→

【中书省 - 决策阶段】
│  需求分析局4司(并行) → 架构设计局4司(并行) → 规范制定局4司 → 方案审议局4司
│                       │                        │              │
│                       ▼ DecisionLog            ▼             ▼ DecisionLog
│                    技术选型决策               规范完成        综合评审+决策记录
│                                             
│                    ↓ 审议通过
│
【门下省 - 审核阶段】
│  代码审查局4司(MARC共享读锁+四维防线L3) → 测试验证局4司 → 质量监控局4司(六维) → 合规审计局4司
│                                                    │
│                                                    ↓ 全部通过
│
【尚书省 - TDD红-绿-蓝循环】
│
│  🔴 RED (兵部 + MARC):
│  ClauseExtractor提取条款 → ClauseToTestMapper生成测试骨架 → 四维防线L1确认 → pytest失败🔴
│
│  🟢 GREEN (工部 + SecretsManager):
│  sm.load() → 最小实现 → UX Integration验证 → AgencyBridge专家咨询 → 四维防线L3 → pytest通过🟢
│
│  🔵 BLUE (刑部 + 四维防线L4):
│  Bug修复 → 重构(L3校验) → 自演化(L4质量评分+兜底恢复) → Git release ✅
│
│                    ↓ 循环或交付
```

#### 使用示例：完整二十四司协作流程

```python
from skillscripts.core.resource_coordinator import ResourceCoordinator, ResourceType, LockType
from skillscripts.core.decision_log import DecisionLog
from skillscripts.security.secrets_manager import SecretsManager
from skillscripts.core.four_d_defense import FourDimensionalDefense
from skillscripts.integration.agency_bridge import AgencyBridge

# 初始化v4.0模块
marc = ResourceCoordinator()
decisions = DecisionLog(output_dir="docs/logs/decision_logs/")
sm = SecretsManager()
defense = FourDimensionalDefense()
bridge = AgencyBridge()

# === 中书省: 决策 ===
tech_decision = decisions.generate(
    title="认证服务框架选型: FastAPI vs Flask",
    rationale=["异步原生", "自动OpenAPI", "团队熟悉"],
    alternatives=[
        {"option": "FastAPI", "pros": ["异步", "自动文档"], "cons": ["较新"]},
        {"option": "Flask", "pros": ["成熟"], "cons": ["需手动配置"]},
    ],
    selected_option=0,
    maker="中书省-架构设计局-技术选型司"
)

# === 门下省: 审核 (MARC共享读锁) ===
with marc.acquire_context("./src/auth", "menxiasheng-daima-shenchajujing-anquansaomiaosi", LockType.SHARED):
    # 安全扫描...
    pass

# === 尚书省: TDD执行 ===
# RED: 条款提取
with marc.acquire_context("test_files", "bingbu-tdd-zhixingsi", LockType.EXCLUSIVE):
    clauses = extract_clauses_from_sdd("specs/AUTH-SDD.yaml")
    
# GREEN: 实现 + SecretsManager
with marc.acquire_context("src_files", "gongbu-daima-shengchengsi", LockType.EXCLUSIVE):
    sm.load()  # .env → .env.local → os.environ → defaults
    
# BLUE: 重构 + 四维防线兜底
with marc.acquire_context("src_files", "xingbu-ziyanhuasi", LockType.EXCLUSIVE):
    result = defense.run_full_check({"phase": "blue", "module": "auth"})
    if not result.passed:
        apply_fallback(result.fallback_strategy)

# 后评估
decisions.evaluate_outcome(decision_id=tech_decision.id, effectiveness_score=0.92, would_repeat=True)
print(decisions.get_statistics())
```

## 相关文档

- [架构概览](architecture_overview.md) - 整体架构说明
- [省部协调机制](provincial_coordination.md) - 三省协调详细说明
- [技能脚本协同](skill_script_coordination.md) - 子技能与脚本协同调用
- [TDD循环流程](tdd_liucheng.md) - TDD详细说明
- [SDD规范驱动开发](sdd_liucheng.md) - SDD详细说明
- [测试体系](ceshi.md) - 测试详细说明
