---
name: yongli_sheji_si
description: 用例设计司，负责TDD测试用例设计、边界条件推断、异常场景覆盖。集成Claw-Code契约驱动，从可执行条款自动转化测试用例。输出至docs/testing/test_cases/。
---

# 用例设计司技能指令

## 职责定义

用例设计司作为测试验证局的用例设计核心，承担以下职责：

| 职责类别 | 具体职责 | 关键产出 |
|----------|----------|----------|
| **TDD设计** | 测试驱动开发的用例设计 | TDD测试用例集 |
| **边界推断** | 边界值分析和等价类划分 | 边界测试用例 |
| **异常覆盖** | 异常场景和错误路径设计 | 异常测试用例 |
| **契约转化** | 从SDD可执行条款自动生成测试 | 契约测试用例 |

---

## Claw-Code契约驱动集成

```yaml
claw_code_integration:
  description: "从SDD规范的可执行条款自动转化为测试用例"
  
  transformation_pipeline:
    input:
      source: "SDD specification executable clauses"
      format: "structured requirement JSON"
      
    processing_steps:
      - step: "clause_parsing"
        action: "解析可执行条款的结构和约束"
        output: "parsed_clauses.json"
        
      - step: "test_scenario_generation"
        action: "基于条款生成正向和反向测试场景"
        output: "test_scenarios.json"
        
      - step: "assertion_extraction"
        action: "从条款中提取前置条件和后置条件作为断言"
        output: "assertions.json"
        
      - step: "test_case_synthesis"
        action: "合成完整的测试用例代码"
        output: "test_cases.py/.ts/.java"
        
  clause_to_test_mapping:
    types:
      validation_clause:
        transformation: "Generate boundary value tests"
        example: |
          Clause: "用户名长度应在3-50字符之间"
          → Test cases:
            - username="" (下界-1)
            - username="ab" (下界)
            - username="abc" (正常)
            - username="a"*50 (上界)
            - username="a"*51 (上界+1)
            
      business_rule_clause:
        transformation: "Generate rule compliance tests"
        example: |
          Clause: "订单金额必须>0且≤100,000"
          → Test cases:
            - amount=0 (无效边界)
            - amount=0.01 (有效最小)
            - amount=50000 (正常)
            - amount=100000 (有效最大)
            - amount=100000.01 (无效)
            
      state_transition_clause:
        transformation: "Generate state machine tests"
        example: |
          Clause: "订单状态: 待支付→已支付→已发货→已完成"
          → Test cases:
            - Valid transition sequence
            - Invalid transition attempts
            - Each state's allowed operations
            
      performance_clause:
        transformation: "Generate performance assertion tests"
        example: |
          Clause: "API响应时间<200ms (P95)"
          → Test case:
            - Measure response time under load
            - Assert P95 < 200ms
```

---

## 工作流程

### 阶段一：需求分析与条款提取

```
收到SDD规范或需求文档
    ↓
[1] 可执行条款识别
    ↓
[2] 条款分类整理
    ↓
[3] 测试点提取
    ↓
[4] 优先级排序
    ↓
进入用例设计阶段
```

#### 可执行条款识别规则

```yaml
executable_clause_identification:
  identification_patterns:
    validation_patterns:
      - regex: "(应该|必须|需要)(是|为|在|满足|符合).*(范围|之间|大于|小于|等于|不超过|至少)"
        type: "boundary_validation"
        
      - regex: "(不能|不可|禁止|不允许).*(空|null|空字符串|负数|重复)"
        type: "negative_validation"
        
      - regex: "(格式|匹配|遵循).*(正则|模式|规范|标准)"
        type: "format_validation"
        
    business_rule_patterns:
      - regex: "(当|如果).*(则|那么|应该|必须).*?(状态|变为|转为|更新)"
        type: "state_transition"
        
      - regex: "(只有|仅当|只有.*才|必须先).*?(才能|可以|允许)"
        type: "precondition"
        
      - regex: "(每次|每当|之后|完成后?).*?(应该|必须|自动|触发)"
        type: "postcondition_action"
        
    performance_patterns:
      - regex: "(响应时间|延迟|耗时).*(不超过|少于|小于|在.*以内).*?(ms|秒|毫秒)"
        type: "response_time_sla"
        
      - regex: "(支持|能够|可以).*(并发|同时|每秒).*?(用户|请求|连接)"
        type: "throughput_requirement"
        
  extraction_output_format:
    clauses_json: |
      {
        "clause_id": "REQ-AUTH-001",
        "source_document": "sdd_auth_spec.md",
        "original_text": "用户名长度必须在3-50字符之间，只能包含字母、数字和下划线",
        "type": "validation",
        "sub_type": "format_and_boundary",
        "attributes": {
          "field": "username",
          "min_length": 3,
          "max_length": 50,
          "allowed_chars": "[a-zA-Z0-9_]",
          "required": true
        },
        "test_points": [
          {"type": "boundary_min", "value": "", "expected": "invalid"},
          {"type": "boundary_min_valid", "value": "ab", "expected": "invalid"},
          {"type": "valid_min", "value": "abc", "expected": "valid"},
          {"type": "valid_typical", "value": "user123", "expected": "valid"},
          {"type": "valid_max", "value": "a"*49, "expected": "valid"},
          {"type": "boundary_max_valid", "value": "a"*50, "expected": "valid"},
          {"type": "boundary_max", "value": "a"*51, "expected": "invalid"},
          {"type": "invalid_char", "value": "user@name", "expected": "invalid"},
          {"type": "special_char", "value": "user-name", "expected": "invalid"}
        ]
      }
```

---

### 阶段二：测试用例设计方法论

```
条款提取完成
    ↓
[1] 等价类划分
    ↓
[2] 边界值分析
    ↓
[3] 决策表设计
    ↓
[4] 状态转换测试
    ↓
[5] 错误推测法
    ↓
[6] 用例综合与去重
    ↓
输出测试用例规格说明书
```

#### 等价类划分法

```yaml
equivalence_partitioning:
  definition: "将输入域划分为若干等价类，从每个等价类中选取代表性数据进行测试"
  
  guidelines:
    effective_equivalence_class:
      description: "对于程序规格说明来说是合理、有意义的输入数据"
      selection: "每个有效等价类至少选取一个测试用例"
      
    ineffective_equivalence_class:
      description: "对于程序规格来说是不合理、无意义的输入数据"
      selection: "每个无效等价类至少选取一个测试用例"
      
  example: "年龄字段验证 (18 ≤ age ≤ 120)"
  equivalence_classes:
    valid_classes:
      - id: "EC-V1"
        range: "[18, 120]"
        representative_value: 25
        reason: "合法成年年龄范围内"
        
      - id: "EC-V2"
        boundary_values: [18, 120]
        reason: "边界值需要单独测试"
        
    invalid_classes:
      - id: "EC-I1"
        range: "(-∞, 18)"
        representative_value: 17
        reason: "未成年"
        
      - id: "EC-I2"
        range: "(120, +∞)"
        representative_value: 121
        reason: "超过合理上限"
        
      - id: "EC-I3"
        special_values: [-1, 0, null, "", "abc", 3.14]
        reason: "非法类型和特殊值"
        
  generated_test_cases:
    - {input: 18, expected: "valid", class: "EC-V2 boundary min"}
    - {input: 25, expected: "valid", class: "EC-V1 typical"}
    - {input: 120, expected: "valid", class: "EC-V2 boundary max"}
    - {input: 17, expected: "invalid", class: "EC-I1 below min"}
    - {input: 121, expected: "invalid", class: "EC-I2 above max"}
    - {input: -1, expected: "invalid", class: "EC-I3 negative"}
    - {input: 0, expected: "invalid", class: "EC-I3 zero"}
    - {input: null, expected: "invalid", class: "EC-I3 null"}
```

#### 边界值分析法

```yaml
boundary_value_analysis:
  definition: "对输入或输出的边界值进行专门测试，因为错误常发生在边界附近"
  
  boundary_types:
    exact_boundaries:
      - "正好等于边界值"
      - "刚超出边界值 (+1/-1)"
      - "刚低于边界值 (-1/+1)"
      
    internal_boundaries:
      - "数据结构容量限制 (数组大小、字符串长度)"
      - "数值精度边界 (浮点数精度、整数溢出)"
      - "时间边界 (日期范围、超时设置)"
      
  robustness_testing:
    description: "在边界之外再取一个值进行测试"
    pattern: "[min-1, min, min+1, nominal, max-1, max, max+1]"
    
  example: "订单金额验证 (0.01 ≤ amount ≤ 999999.99)"
  boundary_test_cases:
    - {input: 0.00, expected: "invalid", type: "below min - epsilon"}
    - {input: 0.01, expected: "valid", type: "exact min"}
    - {input: 0.02, expected: "valid", type: "above min"}
    - {input: 500000.00, expected: "valid", type: "nominal"}
    - {input: 999999.98, expected: "valid", type: "below max"}
    - {input: 999999.99, expected: "valid", type: "exact max"}
    - {input: 1000000.00, expected: "invalid", type: "above max + epsilon"}
    - {input: -0.01, expected: "invalid", type: "negative"}
    - {input: 0.001, expected: "check precision", type: "sub-minimum currency"}
```

#### 决策表法

```yaml
decision_table_method:
  definition: "分析所有输入条件的组合及其对应的动作，系统地设计测试用例"
  
  structure:
    condition_stubs: "条件桩（列出所有条件）"
    condition_entries: "条件项（条件的取值：Y/N/-）"
    action_stubs: "动作桩（列出所有动作）"
    action_entries: "动作项（是否执行该动作：X/-）"
    
  example: "用户注册决策表"
  decision_table:
    conditions:
      C1: "用户名格式正确?"
      C2: "邮箱格式正确?"
      C3: "密码强度足够?"
      C4: "用户名未被占用?"
      C5: "邮箱未被注册?"
      
    actions:
      A1: "注册成功"
      A2: "提示用户名格式错误"
      A3: "提示邮箱格式错误"
      A4: "提示密码强度不足"
      A5: "提示用户名已存在"
      A6: "提示邮箱已注册"
      
    rules:
      - {C1: Y, C2: Y, C3: Y, C4: Y, C5: Y, actions: [A1]}
      - {C1: N, C2: -, C3: -, C4: -, C5: -, actions: [A2]}
      - {C1: Y, C2: N, C3: -, C4: -, C5: -, actions: [A3]}
      - {C1: Y, C2: Y, C3: N, C4: -, C5: -, actions: [A4]}
      - {C1: Y, C2: Y, C3: Y, C4: N, C5: -, actions: [A5]}
      - {C1: Y, C2: Y, C3: Y, C4: Y, C5: N, actions: [A6]}
      
    optimized_rules: 7 (from potential 32 combinations)
    
  test_case_generation:
    from_decision_table: "每个rule生成一个测试用例"
    output_format: |
      @pytest.mark.parametrize("username,email,password,user_exists,email_exists,expected", [
          ("validUser", "valid@email.com", "StrongPass123!", False, False, "success"),
          ("inv", "valid@email.com", "StrongPass123!", None, None, "username_format_error"),
          ("validUser", "invalid", "StrongPass123!", None, None, "email_format_error"),
          ("validUser", "valid@email.com", "weak", None, None, "password_weak"),
          ("validUser", "valid@email.com", "StrongPass123!", True, None, "username_exists"),
          ("validUser", "valid@email.com", "StrongPass123!", False, True, "email_exists"),
      ])
      def test_user_registration(username, email, password, user_exists, email_exists, expected):
          # Arrange & Act & Assert
          ...
```

---

### 阶段三：TDD测试用例生成

```
用例设计方法论应用完成
    ↓
[1] Red阶段：编写失败测试
    ↓
[2] Green阶段：编写最少代码使测试通过
    ↓
[3] Refactor阶段：重构代码
    ↓
[4] 测试代码质量保证
    ↓
[5] 文档化测试意图
    ↓
输出TDD测试用例代码
```

#### TDD工作流模板

```python
"""
TDD测试用例模板 - 用户服务模块
生成自: SDD规范 AUTH-USER-001
生成时间: 2024-01-01
生成者: 用例设计司
"""

import pytest
from unittest.mock import Mock, patch
from src.services.user_service import UserService
from src.exceptions import ValidationError, DuplicateError


class TestUserServiceCreation:
    """TDD Red-Green-Refactor Cycle for User Creation"""
    
    def setup_method(self):
        """每个测试前的初始化"""
        self.mock_repository = Mock()
        self.service = UserService(self.mock_repository)
    
    # ========== RED Phase: 先写失败的测试 ==========
    
    @pytest.mark.red_phase
    def test_create_user_with_valid_data_should_return_user_object(self):
        """
        Given: 有效的用户数据（用户名、邮箱、密码）
        When: 调用create_user方法
        Then: 应返回User对象，包含正确的属性值
        
        来源条款: REQ-AUTH-002 - "使用有效数据创建用户应返回用户对象"
        """
        # Given
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
        self.mock_repository.find_by_username.return_value = None
        self.mock_repository.save.return_value = Mock(
            id=1,
            username="testuser",
            email="test@example.com",
            is_active=True
        )
        
        # When
        result = self.service.create_user(user_data)
        
        # Then - 这会失败因为还没实现
        assert result is not None
        assert result.username == "testuser"
        assert result.email == "test@example.com"
        assert result.is_active is True
        self.mock_repository.save.assert_called_once()
    
    @pytest.mark.red_phase
    def test_create_user_with_duplicate_username_should_raise_error(self):
        """
        Given: 已存在的用户名
        When: 尝试创建相同用户名的用户
        Then: 应抛出DuplicateError异常
        
        来源条款: REQ-AUTH-003 - "用户名必须唯一"
        """
        # Given
        user_data = {
            "username": "existinguser",
            "email": "new@example.com",
            "password": "SecurePass123!"
        }
        self.mock_repository.find_by_username.return_value = Mock(id=1)
        
        # When & Then
        with pytest.raises(DuplicateError) as exc_info:
            self.service.create_user(user_data)
        
        assert "用户名已存在" in str(exc_info.value)
    
    # ========== Boundary Value Tests ==========
    
    @pytest.mark.boundary
    @pytest.mark.parametrize("username,length,should_be_valid", [
        ("ab", 2, False),           # 下界-1
        ("abc", 3, True),           # 下界
        ("testuser", 8, True),      # 正常值
        ("a" * 49, 49, True),       # 上界-1
        ("a" * 50, 50, True),       # 上界
        ("a" * 51, 51, False),      # 上界+1
    ])
    def test_username_length_boundary(self, username, length, should_be_valid):
        """
        测试用户名长度边界值
        条款: 用户名长度必须在3-50字符之间
        """
        user_data = {
            "username": username,
            "email": f"test{length}@example.com",
            "password": "SecurePass123!"
        }
        self.mock_repository.find_by_username.return_value = None
        
        if should_be_valid:
            result = self.service.create_user(user_data)
            assert result is not None
        else:
            with pytest.raises(ValidationError):
                self.service.create_user(user_data)
    
    @pytest.mark.boundary
    @pytest.mark.parametrize("username,contains_special,should_be_valid", [
        ("user_name", "_", True),           # 允许下划线
        ("user123", "digits", True),         # 允许数字
        ("userName", "uppercase", True),     # 允许大写字母
        ("user-name", "-", False),           # 不允许连字符
        ("user.name", ".", False),           # 不允许点号
        ("user name", "space", False),       # 不允许空格
        ("user@name", "@", False),           # 不允许@符号
    ])
    def test_username_character_set(self, username, contains_special, should_be_valid):
        """
        测试用户名字符集限制
        条件: 只能包含字母、数字和下划线
        """
        user_data = {
            "username": username,
            "email": f"{username}@example.com",
            "password": "SecurePass123!"
        }
        self.mock_repository.find_by_username.return_value = None
        
        if should_be_valid:
            result = self.service.create_user(user_data)
            assert result.username == username
        else:
            with pytest.raises(ValidationError) as exc_info:
                self.service.create_user(user_data)
            assert "字符" in str(exc_info.value)
    
    # ========== Exception/Error Scenario Tests ==========
    
    @pytest.mark.exception
    def test_create_user_with_empty_username_should_validate(self):
        """空用户名验证"""
        user_data = {"username": "", "email": "test@example.com", "password": "pass"}
        
        with pytest.raises(ValidationError) as exc_info:
            self.service.create_user(user_data)
        
        assert exc_info.value.field == "username"
        assert "不能为空" in str(exc_info.value.message)
    
    @pytest.mark.exception
    def test_create_user_with_invalid_email_format_should_reject(self):
        """无效邮箱格式验证"""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user@.com",
            "user..name@example.com"
        ]
        
        for email in invalid_emails:
            user_data = {
                "username": f"user_{hash(email)}",
                "email": email,
                "password": "SecurePass123!"
            }
            
            with pytest.raises(ValidationError) as exc_info:
                self.service.create_user(user_data)
            
            assert exc_info.value.field == "email"
    
    @pytest.mark.exception
    def test_create_user_with_weak_password_should_enforce_policy(self):
        """密码强度策略强制执行"""
        weak_passwords = [
            ("short", "太短"),
            ("nocaps123!", "缺少大写字母"),
            ("NOLOWERS123", "缺少小写字母"),
            ("Nodigits!!", "缺少数字"),
            ("NoSymbols123", "缺少特殊字符")
        ]
        
        for password, reason in weak_passwords:
            user_data = {
                "username": f"test_{hash(password)}",
                "email": f"test_{hash(password)}@example.com",
                "password": password
            }
            
            with pytest.raises(ValidationError) as exc_info:
                self.service.create_user(user_data)
            
            assert "密码" in str(exc_info.value.message)
    
    @pytest.mark.exception
    def test_create_user_when_database_fails_should_handle_gracefully(self):
        """数据库故障时的优雅处理"""
        user_data = {
            "username": "dbfail_user",
            "email": "dbfail@example.com",
            "password": "SecurePass123!"
        }
        self.mock_repository.find_by_username.return_value = None
        self.mock_repository.save.side_effect = Exception("Database connection lost")
        
        with pytest.raises(Exception) as exc_info:
            self.service.create_user(user_data)
        
        # 确保错误被适当包装或记录
        assert "数据库" in str(exc_info.value) or "Database" in str(exc_info.value)
    
    # ========== State Transition Tests ==========
    
    @pytest.mark.state_transition
    def test_user_status_transitions_correctly_after_creation(self):
        """
        用户状态转换测试
        初始状态: None → 创建后: pending_verification → 验证后: active
        """
        user_data = {
            "username": "statetest",
            "email": "state@example.com",
            "password": "SecurePass123!"
        }
        self.mock_repository.find_by_username.return_value = None
        self.mock_repository.save.return_value = Mock(
            status="pending_verification"
        )
        
        result = self.service.create_user(user_data)
        
        assert result.status == "pending_verification"
        
        # 模拟验证过程
        verified_user = self.service.verify_email(result.id, "valid_token")
        assert verified_user.status == "active"
    
    @pytest.mark.state_transition
    def test_cannot_activate_already_deleted_user(self):
        """已删除的用户无法激活"""
        deleted_user = Mock(
            id=99,
            status="deleted",
            deleted_at="2024-01-01"
        )
        self.mock_repository.get_by_id.return_value = deleted_user
        
        with pytest.raises(ValidationError) as exc_info:
            self.service.activate_user(99)
        
        assert "已删除" in str(exc_info.value)


class TestUserServiceEdgeCases:
    """边缘情况和特殊场景测试"""
    
    def setup_method(self):
        self.mock_repository = Mock()
        self.service = UserService(self.mock_repository)
    
    @pytest.mark.edge_case
    def test_concurrent_user_creation_race_condition(self):
        """
        并发创建用户的竞态条件处理
        使用mock模拟时序问题
        """
        call_count = 0
        
        def side_effect_find(username):
            nonlocal call_count
            call_count += 1
            # 第一次调用返回None（不存在），第二次调用返回已存在（竞态）
            if call_count == 1:
                return None
            return Mock(id=1)
        
        self.mock_repository.find_by_username.side_effect = side_effect_find
        
        user_data = {
            "username": "race_user",
            "email": "race@example.com",
            "password": "SecurePass123!"
        }
        
        # 第一次调用应该成功（或根据业务逻辑处理竞态）
        # 这里假设我们会检测到竞态并抛出特定异常
        with pytest.raises((DuplicateError, Exception)):
            self.service.create_user(user_data)
    
    @pytest.mark.edge_case
    def test_unicode_and_special_characters_in_username(self):
        """Unicode和特殊字符处理"""
        unicode_usernames = [
            ("用户名123", "中文用户名"),
            ("юзернейм", "西里尔字母"),
            ("🎉user", "emoji字符"),
            ("user\tname", "制表符"),
            ("user\nname", "换行符"),
        ]
        
        for username, description in unicode_usernames:
            user_data = {
                "username": username,
                "email": f"unicode{hash(username)}@example.com",
                "password": "SecurePass123!"
            }
            
            try:
                result = self.service.create_user(user_data)
                # 如果通过了，确保存储的是安全的
                assert result.username == username
            except ValidationError:
                # 拒绝也是可接受的行为
                pass


# ========== Performance Assertion Tests ==========
@pytest.mark.performance
class TestUserServicePerformance:
    """性能断言测试"""
    
    def test_create_user_should_complete_within_time_limit(self):
        """
        性能要求: 用户创建应在100ms内完成
        来源条款: PERF-AUTH-001
        """
        import time
        
        mock_repo = Mock()
        mock_repo.find_by_username.return_value = None
        mock_repo.save.return_value = Mock(id=1)
        service = UserService(mock_repo)
        
        start_time = time.perf_counter()
        
        for _ in range(100):  # 执行100次以获得稳定测量
            service.create_user({
                "username": "perf_user",
                "email": "perf@example.com",
                "password": "SecurePass123!"
            })
        
        elapsed_ms = (time.perf_counter() - start_time) / 100 * 1000
        
        assert elapsed_ms < 100, f"创建用户耗时 {elapsed_ms:.2f}ms，超过100ms限制"


# ========== Fixture Definitions ==========
@pytest.fixture
def sample_user_data():
    """标准用户数据fixture"""
    return {
        "username": "fixture_user",
        "email": "fixture@example.com",
        "password": "SecurePass123!"
    }


@pytest.fixture
def authenticated_service():
    """已认证的服务实例fixture"""
    repo = Mock()
    service = UserService(repo)
    service.current_user = Mock(id=1, role="admin")
    return service
```

---

### 阶段四：测试用例规格说明书生成

```
TDD测试用例生成完成
    ↓
[1] 用例编号分配
    ↓
[2] 前置条件整理
    ↓
[3] 测试步骤细化
    ↓
[4] 预期结果明确
    ↓
[5] 优先级标注
    ↓
[6] 追溯矩阵建立
    ↓
输出测试用例规格说明书
```

#### 测试用例规格说明书格式

```markdown
# 测试用例规格说明书

**项目**: {{project_name}}  
**模块**: User Service  
**版本**: 1.0.0  
**日期**: 2024-01-01  
**编制**: 用例设计司  

---

## 📋 用例概览

| 用例ID | 名称 | 类型 | 优先级 | 预估时间 | 状态 |
|--------|------|------|--------|----------|------|
| TC-USR-001 | 有效用户创建成功 | 正向 | P0 | 30s | 待执行 |
| TC-USR-002 | 重复用户名拒绝 | 异常 | P0 | 20s | 待执行 |
| TC-USR-003 | 用户名长度边界-下界 | 边界 | P1 | 15s | 待执行 |
| ... | ... | ... | ... | ... | ... |

**总计**: 45 个测试用例  
**预估总时间**: 25 分钟  

---

## 📝 详细用例

### TC-USR-001: 有效用户创建成功

**基本信息**
- **用例类型**: 正向测试
- **优先级**: P0 (Critical)
- **来源条款**: REQ-AUTH-002
- **TDD阶段**: Red ✓ Green ✓ Refactor ✓

**前置条件**
- [x] 数据库服务可用
- [x] 用户名 "testuser" 未被占用
- [x] 邮箱 "test@example.com" 未被注册
- [x] 密码符合强度要求

**测试数据**
| 字段 | 值 | 说明 |
|------|-----|------|
| username | testuser | 符合格式的有效用户名 |
| email | test@example.com | 有效邮箱格式 |
| password | SecurePass123! | 强密码（大写+小写+数字+特殊字符） |

**测试步骤**
1. 创建 UserService 实例，注入 Mock Repository
2. 配置 Mock Repository：
   - find_by_username("testuser") 返回 None
   - save() 返回 User 对象
3. 调用 service.create_user(user_data)
4. 验证返回结果

**预期结果**
✅ 返回非空的 User 对象  
✅ user.username == "testuser"  
✅ user.email == "test@example.com"  
✅ user.is_active == True  
✅ repository.save() 被调用一次  
✅ 无异常抛出  

**实际结果**
_(待填写)_  

**执行状态**
- [ ] 通过
- [ ] 失败
- [ ] 阻塞
- [ ] 跳过

**缺陷记录** (如有)
- 缺陷ID: ___
- 严重级别: ___
- 描述: ___

---

### TC-USR-010: 用户名为空字符串

**基本信息**
- **用例类型**: 异常/边界测试
- **优先级**: P1 (High)
- **来源条款**: REQ-AUTH-001
- **等价类**: 无效等价类 (空值)

**测试数据**
| 字段 | 值 | 说明 |
|------|-----|------|
| username | "" (空字符串) | 违反必填约束 |
| email | empty@test.com | 有效邮箱 |
| password | SecurePass123! | 有效密码 |

**预期结果**
❌ 抛出 ValidationError 异常  
❌ exception.field == "username"  
❌ exception.message 包含 "不能为空" 或 "为必填项"  

---

## 🔗 需求追溯矩阵

| 需求ID | 需求描述 | 覆盖用例 | 覆盖状态 |
|--------|----------|----------|----------|
| REQ-AUTH-001 | 用户名长度3-50字符 | TC-USR-003~TC-USR-008 | ✅ 100% |
| REQ-AUTH-002 | 有效数据创建返回用户对象 | TC-USR-001 | ✅ 100% |
| REQ-AUTH-003 | 用户名唯一性 | TC-USR-002, TC-USR-020 | ✅ 100% |
| REQ-AUTH-004 | 邮箱格式验证 | TC-USR-011~TC-USR-015 | ✅ 100% |
| REQ-AUTH-005 | 密码强度策略 | TC-USR-016~TC-USR-019 | ✅ 100% |
| REQ-AUTH-006 | 用户状态转换 | TC-USR-021~TC-USR-023 | ✅ 100% |
| PERF-AUTH-001 | 创建性能<100ms | TC-PERF-001 | ✅ 100% |

**总体覆盖率**: 100% (7/7 需求)

---

## 📊 用例统计

### 按类型统计
| 类型 | 数量 | 占比 |
|------|------|------|
| 正向测试 | 15 | 33.3% |
| 边界测试 | 12 | 26.7% |
| 异常测试 | 13 | 28.9% |
| 性能测试 | 2 | 4.4% |
| 状态转换 | 3 | 6.7% |

### 按优先级统计
| 优先级 | 数量 | 占比 | 预估时间 |
|--------|------|------|----------|
| P0-Critical | 10 | 22.2% | 5 min |
| P1-High | 15 | 33.3% | 10 min |
| P2-Medium | 12 | 26.7% | 6 min |
| P3-Low | 8 | 17.8% | 4 min |

---

**文档审批**:  
- 编制: 用例设计司  
- 审核: 测试验证局技术负责人  
- 批准: 门下省质量官
```

---

## 输出物管理

### 输出目录结构

```
docs/testing/test_cases/
├── user_service/
│   ├── test_user_service.py              # TDD测试代码
│   ├── tc_spec_user_service.md           # 用例规格说明书
│   └── trace_matrix_user_service.xlsx    # 追溯矩阵
├── auth_module/
│   ├── test_authentication.py
│   ├── tc_spec_authentication.md
│   └── trace_matrix_authentication.xlsx
├── order_management/
│   ├── test_order_service.py
│   ├── tc_spec_order_service.md
│   └── trace_matrix_order_service.xlsx
└── index.md                              # 用例索引
```

---

## 与MARC资源协调器的资源需求

```yaml
marc_resource_requirements:
  compute_resources:
    cpu_cores: 2
    memory_gb: 4
    disk_space_gb: 10
    
  execution_time:
    clause_analysis: "< 3 minutes"
    test_case_generation: "< 5 minutes"
    documentation_generation: "< 5 minutes"
    
  ai_assistance:
    nlp_capabilities:
      - "requirement parsing"
      - "test scenario inference"
      - "natural language to code generation"
    ml_models:
      - "clause classifier"
      - "boundary value predictor"
      - "test name generator"
      
  output_storage:
    location: "docs/testing/test_cases/"
    formats: [".py", ".ts", ".java", ".md", ".xlsx"]
    estimated_size_per_module_mb: 5
    
  integration_points:
    claw_code:
      endpoint: "/api/sdd/clauses"
      authentication: "API key required"
      rate_limit: "100 requests/minute"
```

---

## 协同调用接口

### 接口定义

| 接口名称 | 接口描述 | 调用方 |
|----------|----------|--------|
| `generate_tdd_tests` | 从SDD条款生成TDD测试用例 | 执行管理司、开发人员 |
| `design_boundary_tests` | 设计边界值测试用例 | 执行管理司 |
| `design_exception_tests` | 设计异常场景测试用例 | 执行管理司 |
| `generate_test_spec` | 生成测试用例规格说明书 | 策略制定司、项目经理 |

### 调用示例

```bash
# 从SDD规范生成测试用例
python skillscripts/testing/test_case_generator.py \
  --sdd-spec docs/sdd/auth_spec.json \
  --module user_service \
  --include-boundary \
  --include-exception \
  --include-performance \
  --output docs/testing/test_cases/user_service/
```

---

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-04-06 | 初始版本，包含TDD设计、边界分析、异常覆盖、契约转化完整能力 |
