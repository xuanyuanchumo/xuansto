---
name: daima_chonggou
description: 进行代码重构，改善代码结构而不改变其行为，包括代码异味识别、重构手法应用、重构建议生成、测试保障和重构验证。
version: 1.1.0
---
# 代码重构流程（增强版）

## 概述
代码重构是在不改变代码外部行为的前提下，改善代码内部结构的过程。重构可以提高代码可读性、可维护性和可扩展性，降低技术债务。本文档提供完整的重构流程，包括代码异味识别、重构建议生成、重构验证等环节。

## 重构场景
1. **代码异味**：处理重复代码、过长函数等
2. **架构调整**：调整代码架构以适应新需求
3. **技术债务**：偿还技术债务，提升代码质量
4. **可维护性**：提高代码可维护性，降低修改成本
5. **性能优化**：在不改变行为的前提下优化性能

## 代码异味识别（增强版）

### 常见代码异味

| 异味类型 | 描述 | 严重程度 | 检测方法 |
|----------|------|----------|----------|
| 重复代码 | 相同或相似代码出现在多处 | 高 | AST分析、代码哈希 |
| 过长函数 | 函数超过50行，难以理解 | 高 | 行数统计 |
| 过大类 | 类承担过多职责 | 高 | 方法/属性计数 |
| 过长参数列表 | 参数超过4个 | 中 | 参数计数 |
| 发散式变化 | 一个类因多个原因被修改 | 中 | 方法分类分析 |
| 霰弹式修改 | 一个变化导致多个类修改 | 中 | 依赖分析 |
| 依恋情节 | 方法过度依赖其他类的数据 | 中 | 访问模式分析 |
| 数据泥团 | 多个数据项总是一起出现 | 低 | 参数组分析 |
| 基本类型偏执 | 过度使用基本类型而非对象 | 低 | 类型注解分析 |
| switch语句 | 大量switch/case判断 | 中 | 条件分支分析 |
| 深层嵌套 | 嵌套层级超过3层 | 高 | 嵌套深度计算 |
| 魔法数字 | 代码中出现未解释的数字 | 低 | 字面量检测 |
| 死代码 | 未被使用的代码 | 中 | 引用分析 |
| 上帝类 | 类过于庞大，承担过多职责 | 高 | 综合指标评估 |
| 懒惰类 | 类功能太少，几乎无用 | 低 | 方法计数 |
| 消息链 | 过长的调用链 | 中 | 链式调用分析 |
| 临时字段 | 只在特定场景使用的字段 | 低 | 使用频率分析 |
| 中间人 | 类只是委托给其他类 | 中 | 委托比例分析 |
| 不当亲密 | 类之间过度依赖私有成员 | 中 | 访问权限分析 |

### 代码异味检测方法

**自动化检测工具：**
- `skillscripts/utils/code_review_automation.py` - 内置代码异味检测
- ESLint（JavaScript）
- Pylint（Python）
- SonarQube（多语言）
- PMD（Java）

**使用代码审查脚本检测：**
```bash
# 检测后端代码异味
python skillscripts/utils/code_review_automation.py --target backend/app --format json

# 检测前端代码异味
python skillscripts/utils/code_review_automation.py --target frontend/src --format html

# 生成重构建议报告
python skillscripts/utils/code_review_automation.py --target backend/app --version 1.0.0
```

**手动检测清单：**
- [ ] 是否有重复代码块？
- [ ] 函数是否超过50行？
- [ ] 类是否超过500行？
- [ ] 参数列表是否过长？
- [ ] 是否有深层嵌套（超过3层）？
- [ ] 是否有魔法数字/字符串？
- [ ] 是否有未使用的代码？
- [ ] 类是否有超过10个公共方法？
- [ ] 是否有超过5层的调用链？
- [ ] 是否有只在部分方法中使用的字段？

## 重构流程

### 标准流程
1. **识别重构点**：发现代码异味或改进机会
2. **编写测试保障**：确保重构不破坏现有功能
3. **小步重构**：每次只做一个小改动
4. **运行测试验证**：确保每次改动后测试通过
5. **提交代码**：频繁提交，便于回滚

### 重构原则
- **保持行为不变**：重构不改变外部行为
- **小步前进**：每次改动要小且可控
- **持续测试**：每步重构后都要验证
- **频繁提交**：便于追踪和回滚

## 重构建议生成

### 自动化重构建议

系统可以根据代码异味自动生成重构建议：

```python
class RefactoringSuggestionGenerator:
    """重构建议生成器"""
    
    SUGGESTION_TEMPLATES = {
        "long_method": {
            "name": "提取方法",
            "description": "将长方法拆分为多个小方法",
            "steps": [
                "识别方法中的逻辑块",
                "为每个逻辑块创建新方法",
                "用方法调用替换原代码",
                "运行测试验证"
            ]
        },
        "large_class": {
            "name": "提取类",
            "description": "将大类拆分为多个小类",
            "steps": [
                "识别类中的职责",
                "为每个职责创建新类",
                "移动相关方法和属性",
                "建立类间关系",
                "运行测试验证"
            ]
        },
        "duplicate_code": {
            "name": "提取公共方法",
            "description": "将重复代码提取为公共方法",
            "steps": [
                "识别重复代码段",
                "创建公共方法",
                "替换所有重复代码",
                "运行测试验证"
            ]
        },
        "deep_nesting": {
            "name": "减少嵌套",
            "description": "使用早返回或提取方法减少嵌套",
            "steps": [
                "识别嵌套条件",
                "反转条件使用早返回",
                "提取嵌套逻辑为方法",
                "运行测试验证"
            ]
        },
        "god_class": {
            "name": "拆分上帝类",
            "description": "将上帝类拆分为多个专注的类",
            "steps": [
                "识别类的不同职责",
                "为每个职责创建新类",
                "逐步迁移功能",
                "确保测试覆盖"
            ]
        },
        "message_chains": {
            "name": "隐藏委托",
            "description": "使用中间方法缩短消息链",
            "steps": [
                "识别消息链",
                "在中间对象添加委托方法",
                "替换链式调用"
            ]
        }
    }
    
    def generate_suggestions(self, code_smells: list) -> list:
        """根据代码异味生成重构建议"""
        suggestions = []
        for smell in code_smells:
            if smell.type in self.SUGGESTION_TEMPLATES:
                template = self.SUGGESTION_TEMPLATES[smell.type]
                suggestions.append({
                    "smell_type": smell.type,
                    "location": smell.location,
                    "suggestion": template["name"],
                    "description": template["description"],
                    "steps": template["steps"],
                    "priority": smell.severity,
                    "estimated_effort": self._estimate_effort(smell)
                })
        return sorted(suggestions, key=lambda x: x["priority"], reverse=True)
    
    def _estimate_effort(self, smell) -> str:
        """估算重构工作量"""
        effort_map = {
            "critical": "大（需要仔细规划）",
            "high": "大（需要仔细规划）",
            "medium": "中（需要一定时间）",
            "low": "小（快速完成）"
        }
        return effort_map.get(smell.severity, "未知")
```

### 重构建议输出格式

```json
{
    "refactoring_suggestions": [
        {
            "id": "REF-001",
            "smell_type": "long_method",
            "location": {
                "file": "src/services/order_processor.py",
                "line": 45,
                "method": "process_order"
            },
            "suggestion": "提取方法",
            "description": "方法 process_order 有 120 行，建议拆分为多个小方法",
            "steps": [
                "识别订单验证逻辑块（第45-60行）",
                "识别价格计算逻辑块（第62-85行）",
                "识别支付处理逻辑块（第87-110行）",
                "创建独立方法并调用"
            ],
            "priority": "high",
            "estimated_effort": "中（需要一定时间）",
            "related_patterns": ["Extract Method", "Composed Method"]
        }
    ]
}
```

### 重构优先级排序

```python
def prioritize_refactoring(suggestions: list) -> list:
    """按优先级排序重构建议"""
    priority_weights = {
        "critical": 100,
        "high": 75,
        "medium": 50,
        "low": 25
    }
    
    impact_weights = {
        "security": 1.5,
        "performance": 1.3,
        "maintainability": 1.2,
        "readability": 1.0
    }
    
    for suggestion in suggestions:
        base_weight = priority_weights.get(suggestion["priority"], 0)
        impact_weight = impact_weights.get(suggestion.get("impact_type", "readability"), 1.0)
        suggestion["score"] = base_weight * impact_weight
    
    return sorted(suggestions, key=lambda x: x["score"], reverse=True)
```

## 重构验证

### 验证流程

```python
class RefactoringValidator:
    """重构验证器"""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.test_results = []
        self.behavior_checks = []
    
    def validate_refactoring(self, before_code: str, after_code: str) -> dict:
        """验证重构是否成功"""
        results = {
            "behavior_preserved": True,
            "tests_passed": True,
            "quality_improved": True,
            "issues": []
        }
        
        test_result = self._run_tests()
        if not test_result["passed"]:
            results["tests_passed"] = False
            results["issues"].extend(test_result["failures"])
        
        behavior_result = self._compare_behavior(before_code, after_code)
        if not behavior_result["identical"]:
            results["behavior_preserved"] = False
            results["issues"].extend(behavior_result["differences"])
        
        quality_result = self._compare_quality(before_code, after_code)
        if not quality_result["improved"]:
            results["quality_improved"] = False
            results["issues"].extend(quality_result["regressions"])
        
        return results
    
    def _run_tests(self) -> dict:
        """运行测试套件"""
        return {
            "passed": True,
            "failures": [],
            "coverage": 85.5,
            "execution_time": 12.3
        }
    
    def _compare_behavior(self, before: str, after: str) -> dict:
        """对比重构前后行为"""
        return {
            "identical": True,
            "differences": []
        }
    
    def _compare_quality(self, before: str, after: str) -> dict:
        """对比代码质量"""
        before_metrics = self._calculate_metrics(before)
        after_metrics = self._calculate_metrics(after)
        
        return {
            "improved": after_metrics["score"] >= before_metrics["score"],
            "before": before_metrics,
            "after": after_metrics,
            "regressions": []
        }
    
    def _calculate_metrics(self, code: str) -> dict:
        """计算代码指标"""
        return {
            "complexity": 10,
            "maintainability_index": 75,
            "lines_of_code": 100,
            "score": 80
        }
```

### 验证检查清单

```markdown
## 重构验证检查清单

### 功能验证
- [ ] 所有现有测试通过
- [ ] 测试覆盖率未下降
- [ ] 边界条件测试通过
- [ ] 异常处理正确

### 行为验证
- [ ] 输入输出行为一致
- [ ] 副作用保持不变
- [ ] 性能未显著下降
- [ ] 资源使用合理

### 代码质量验证
- [ ] 复杂度降低或保持
- [ ] 代码行数减少或合理
- [ ] 命名清晰准确
- [ ] 注释适当更新

### 文档验证
- [ ] API文档更新
- [ ] 注释与代码一致
- [ ] 变更日志记录
```

### 自动化验证脚本

```python
def run_refactoring_validation(project_path: str, refactoring_id: str) -> dict:
    """运行完整的重构验证"""
    validator = RefactoringValidator(project_path)
    
    before_code = get_code_before_refactoring(refactoring_id)
    after_code = get_code_after_refactoring(refactoring_id)
    
    results = validator.validate_refactoring(before_code, after_code)
    
    report = {
        "refactoring_id": refactoring_id,
        "timestamp": datetime.now().isoformat(),
        "validation_results": results,
        "recommendation": "可以合并" if all([
            results["behavior_preserved"],
            results["tests_passed"],
            results["quality_improved"]
        ]) else "需要修复问题后重新验证"
    }
    
    return report
```

## 重构手法详解

### 1. 提取方法（Extract Method）

**场景**：过长函数、重复代码

**重构前：**
```python
def print_invoice(order):
    print("订单号:", order.id)
    print("客户:", order.customer_name)
    print("日期:", order.date)
    total = 0
    for item in order.items:
        subtotal = item.price * item.quantity
        print(f"  {item.name}: {item.quantity} x {item.price} = {subtotal}")
        total += subtotal
    print("总计:", total)
```

**重构后：**
```python
def print_invoice(order):
    print_header(order)
    total = calculate_total(order)
    print_total(total)

def print_header(order):
    print("订单号:", order.id)
    print("客户:", order.customer_name)
    print("日期:", order.date)

def calculate_total(order):
    total = 0
    for item in order.items:
        subtotal = item.price * item.quantity
        print(f"  {item.name}: {item.quantity} x {item.price} = {subtotal}")
        total += subtotal
    return total

def print_total(total):
    print("总计:", total)
```

### 2. 提取变量（Extract Variable）

**场景**：复杂表达式难以理解

**重构前：**
```python
if platform.upper().startswith("MAC") and browser.upper().startswith("IE") and was_initialized() and resize > 0:
    pass
```

**重构后：**
```python
is_mac_os = platform.upper().startswith("MAC")
is_ie_browser = browser.upper().startswith("IE")
was_resized = resize > 0

if is_mac_os and is_ie_browser and was_initialized() and was_resized:
    pass
```

### 3. 以多态取代条件表达式（Replace Conditional with Polymorphism）

**场景**：复杂的switch/if-else逻辑

**重构前：**
```python
def calculate_salary(employee):
    if employee.type == "ENGINEER":
        return employee.base_salary
    elif employee.type == "MANAGER":
        return employee.base_salary + employee.bonus
    elif employee.type == "SALESMAN":
        return employee.base_salary + employee.commission
```

**重构后：**
```python
class Employee:
    def calculate_salary(self):
        return self.base_salary

class Manager(Employee):
    def calculate_salary(self):
        return self.base_salary + self.bonus

class Salesman(Employee):
    def calculate_salary(self):
        return self.base_salary + self.commission

def calculate_salary(employee):
    return employee.calculate_salary()
```

### 4. 移动方法（Move Method）

**场景**：方法在错误的类中

**重构前：**
```python
class Account:
    def __init__(self, type):
        self.type = type
        self.days_overdrawn = 0

    def overdraft_charge(self):
        if self.type.is_premium:
            result = 10
            if self.days_overdrawn > 7:
                result += (self.days_overdrawn - 7) * 0.85
            return result
        else:
            return self.days_overdrawn * 1.75
```

**重构后：**
```python
class AccountType:
    def overdraft_charge(self, days_overdrawn):
        if self.is_premium:
            result = 10
            if days_overdrawn > 7:
                result += (days_overdrawn - 7) * 0.85
            return result
        else:
            return days_overdrawn * 1.75

class Account:
    def overdraft_charge(self):
        return self.type.overdraft_charge(self.days_overdrawn)
```

### 5. 内联方法（Inline Method）

**场景**：方法体简单且名称不增加价值

**重构前：**
```python
def get_rating(self):
    return 5 if self.number_of_late_deliveries > 5 else 2

def more_than_five_late_deliveries(self):
    return self.number_of_late_deliveries > 5
```

**重构后：**
```python
def get_rating(self):
    return 5 if self.number_of_late_deliveries > 5 else 2
```

### 6. 分解条件表达式（Decompose Conditional）

**场景**：复杂的条件判断逻辑

**重构前：**
```python
if date.before(SUMMER_START) or date.after(SUMMER_END):
    charge = quantity * winter_rate + winter_service_charge
else:
    charge = quantity * summer_rate
```

**重构后：**
```python
if is_summer(date):
    charge = summer_charge(quantity)
else:
    charge = winter_charge(quantity)

def is_summer(date):
    return not (date.before(SUMMER_START) or date.after(SUMMER_END))

def summer_charge(quantity):
    return quantity * summer_rate

def winter_charge(quantity):
    return quantity * winter_rate + winter_service_charge
```

## 重构示例代码

### 综合示例：订单处理

**重构前：**
```python
class OrderProcessor:
    def process(self, order):
        if not order.customer:
            raise ValueError("客户不能为空")
        if not order.items:
            raise ValueError("订单项不能为空")
        
        if order.customer.level == "VIP":
            discount = 0.2
        elif order.customer.level == "GOLD":
            discount = 0.1
        else:
            discount = 0
        
        total = 0
        for item in order.items:
            total += item.price * item.quantity
        total = total * (1 - discount)
        
        if order.payment_method == "CREDIT_CARD":
            pass
        elif order.payment_method == "PAYPAL":
            pass
        
        return total
```

**重构后：**
```python
class OrderValidator:
    def validate(self, order):
        if not order.customer:
            raise ValueError("客户不能为空")
        if not order.items:
            raise ValueError("订单项不能为空")

class DiscountCalculator:
    DISCOUNT_RATES = {
        "VIP": 0.2,
        "GOLD": 0.1,
        "NORMAL": 0
    }
    
    def calculate(self, customer):
        return self.DISCOUNT_RATES.get(customer.level, 0)

class PriceCalculator:
    def calculate_total(self, items, discount):
        subtotal = sum(item.price * item.quantity for item in items)
        return subtotal * (1 - discount)

class PaymentProcessor:
    def process(self, order):
        processors = {
            "CREDIT_CARD": CreditCardPayment(),
            "PAYPAL": PayPalPayment()
        }
        processor = processors.get(order.payment_method)
        if processor:
            processor.process(order)

class OrderProcessor:
    def __init__(self):
        self.validator = OrderValidator()
        self.discount_calculator = DiscountCalculator()
        self.price_calculator = PriceCalculator()
        self.payment_processor = PaymentProcessor()
    
    def process(self, order):
        self.validator.validate(order)
        discount = self.discount_calculator.calculate(order.customer)
        total = self.price_calculator.calculate_total(order.items, discount)
        self.payment_processor.process(order)
        return total
```

## 重构检查清单

- [ ] 是否有足够的测试覆盖？
- [ ] 重构是否改变了外部行为？
- [ ] 是否遵循小步重构原则？
- [ ] 每步重构后测试是否通过？
- [ ] 是否有清晰的提交记录？
- [ ] 是否更新了相关文档？
- [ ] 是否进行了重构验证？
- [ ] 代码质量是否有所提升？

## 输出物
- 重构后的代码
- 重构记录文档
- 测试报告
- 重构建议报告
- 验证报告
- 代码质量对比报告
- 变更影响分析报告

## 相关脚本

- `skillscripts/utils/code_review_automation.py` - 代码审查与异味检测
- `scripts/architecture_check.py` - 架构检查
- `scripts/performance_detector.py` - 性能问题检测
- `scripts/security_scanner.py` - 安全问题扫描

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.1.0 | 2024-01 | 增强重构建议生成和验证功能 |
| 1.0.0 | 2024-01 | 初始版本 |
