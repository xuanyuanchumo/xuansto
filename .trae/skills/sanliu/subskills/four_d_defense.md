# 四维度输出防线系统 (Four-Dimensional Output Defense)

## 概述

四维度输出防线是 Sanliu v4.0 的核心质量保障体系，通过四层纵深防御确保所有输出内容的质量、安全性和可靠性。该系统贯穿整个开发流程，从需求分析到代码生成，从文档编写到测试执行，每个环节都必须通过四层防线才能最终交付。

### 核心理念

- **纵深防御**：四层防线依次执行，每层都有独立的检查点和质量门禁
- **快速失败**：任何一层检测到问题立即中止，避免低质量输出进入下一层
- **自动降级**：当某层不可用时，系统自动降级到安全模式，保证核心功能可用
- **质量评分**：每层输出质量评分，低于阈值自动触发回滚或重新生成
- **可追溯性**：所有检查结果和决策过程完整记录，支持审计和回溯

### 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    四维度输出防线系统架构                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  输入: 用户请求 / Agent任务 / 系统触发                              │
│      ↓                                                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  第1层: Prompt工程层 (PromptLayer)                         │  │
│  │  ├─ 意图识别 (Intent Recognition)                          │  │
│  │  ├─ 上下文注入 (Context Injection)                        │  │
│  │  ├─ 歧义消解 (Ambiguity Resolution)                        │  │
│  │  └─ 输入验证 (Input Validation)                            │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓ PASS                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  第2层: 能力约束层 (CapabilityLayer)                      │  │
│  │  ├─ 技能匹配度评估 (Skill Matching)                       │  │
│  │  ├─ 知识覆盖检查 (Knowledge Coverage)                      │  │
│  │  ├─ 工具可用性验证 (Tool Availability)                     │  │
│  │  └─ 能力缺口识别 (Capability Gap Detection)                │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓ PASS                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  第3层: 规则校验层 (RuleValidationLayer)                   │  │
│  │  ├─ Lint检查集成 (Lint Integration)                        │  │
│  │  ├─ 安全扫描接口 (Security Scanning)                       │  │
│  │  ├─ 硬编码检测调用 (Hardcoded Detection)                   │  │
│  │  └─ 性能基线对比 (Performance Baseline)                    │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓ PASS                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  第4层: 兜底恢复层 (FallbackRecoveryLayer)                │  │
│  │  ├─ 质量评分 (Quality Scoring)                            │  │
│  │  ├─ 自动回滚 (Automatic Rollback)                         │  │
│  │  ├─ 降级策略 (Degradation Strategy)                       │  │
│  │  └─ 错误日志记录 (Error Logging)                          │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓ QUALITY ≥ 3.5/5.0                     │
│  输出: 高质量内容 / 代码 / 文档 / 测试用例                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 第1层: Prompt工程层 (PromptLayer)

### 功能概述

Prompt工程层是四维防线的第一道关卡，负责对输入进行预处理和增强，确保后续处理层接收到清晰、准确、完整的输入信息。

### 核心组件

#### 1.1 意图识别 (Intent Recognition)

**功能**: 自动识别用户请求的真实意图，将模糊的自然语言转换为明确的任务类型。

**支持的意图类型**:
- `CODE_GENERATION`: 代码生成
- `CODE_REFACTORING`: 代码重构
- `DOCUMENTATION`: 文档编写
- `TESTING`: 测试用例生成
- `DEBUGGING`: 调试和问题诊断
- `ARCHITECTURE`: 架构设计
- `CONFIGURATION`: 配置管理

**实现方式**:
```python
class PromptLayer:
    def recognize_intent(self, input_data: InputData) -> IntentType:
        """
        基于关键词、上下文、历史行为识别意图
        """
        keywords = input_data.content.lower()
        context = input_data.context

        # 关键词匹配
        if any(kw in keywords for kw in ['生成', '创建', '开发', '实现']):
            return IntentType.CODE_GENERATION
        elif any(kw in keywords for kw in ['重构', '优化', '改进']):
            return IntentType.CODE_REFACTORING
        # ... 其他意图识别逻辑
```

#### 1.2 上下文注入 (Context Injection)

**功能**: 自动注入项目上下文信息，包括技术栈、编码规范、项目结构等。

**注入的上下文信息**:
- 项目技术栈 (Python 3.9+, React 18, PostgreSQL 14)
- 编码规范 (PEP8, ESLint规则)
- 项目结构 (src/, tests/, docs/ 目录组织)
- 依赖关系 (requirements.txt, package.json)
- 环境配置 (.env 变量)

**实现方式**:
```python
class PromptLayer:
    def inject_context(self, input_data: InputData) -> InputData:
        """
        注入项目上下文信息
        """
        context = {
            'tech_stack': self._load_tech_stack(),
            'coding_standards': self._load_coding_standards(),
            'project_structure': self._load_project_structure(),
            'dependencies': self._load_dependencies(),
            'environment': self._load_environment_vars()
        }
        input_data.context.update(context)
        return input_data
```

#### 1.3 歧义消解 (Ambiguity Resolution)

**功能**: 识别输入中的歧义点，主动向用户确认或基于上下文进行智能推断。

**常见歧义类型**:
- 技术选型歧义: "使用数据库" → MySQL? PostgreSQL? MongoDB?
- 功能范围歧义: "实现用户认证" → 仅登录? 包含注册? OAuth2.0?
- 性能要求歧义: "高性能" → QPS 1000? 10000? 延迟 < 100ms?

**实现方式**:
```python
class PromptLayer:
    def resolve_ambiguity(self, input_data: InputData) -> InputData:
        """
        识别并消解歧义
        """
        ambiguities = self._detect_ambiguities(input_data)
        if ambiguities:
            # 优先从上下文推断
            resolved = self._infer_from_context(ambiguities, input_data.context)
            # 无法推断的向用户确认
            unresolved = [a for a in ambiguities if a not in resolved]
            if unresolved:
                resolved.update(self._ask_user_confirmation(unresolved))
            input_data.resolved_ambiguities = resolved
        return input_data
```

#### 1.4 输入验证 (Input Validation)

**功能**: 验证输入的完整性和有效性，拒绝无效或危险的请求。

**验证规则**:
- 必填字段检查
- 格式验证 (文件路径、URL、版本号)
- 安全性检查 (SQL注入、命令注入、XSS)
- 资源可用性检查 (文件是否存在、目录是否可写)

**实现方式**:
```python
class PromptLayer:
    def validate_input(self, input_data: InputData) -> ValidationResult:
        """
        验证输入的有效性
        """
        errors = []

        # 必填字段检查
        if not input_data.content:
            errors.append("输入内容不能为空")

        # 格式验证
        if input_data.file_path:
            if not self._is_valid_path(input_data.file_path):
                errors.append(f"无效的文件路径: {input_data.file_path}")

        # 安全性检查
        if self._contains_malicious_pattern(input_data.content):
            errors.append("检测到潜在的安全风险")

        # 资源可用性
        if input_data.target_file:
            if not self._file_exists(input_data.target_file):
                errors.append(f"目标文件不存在: {input_data.target_file}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
```

### API接口

```python
class PromptLayer:
    def process(self, input_data: InputData) -> LayerResult:
        """
        完整的Prompt层处理流程

        Args:
            input_data: 输入数据，包含content、context、metadata等

        Returns:
            LayerResult: 处理结果，包含status、output、metadata
        """
        # 1. 意图识别
        intent = self.recognize_intent(input_data)
        input_data.intent = intent

        # 2. 上下文注入
        input_data = self.inject_context(input_data)

        # 3. 歧义消解
        input_data = self.resolve_ambiguity(input_data)

        # 4. 输入验证
        validation = self.validate_input(input_data)
        if not validation.is_valid:
            return LayerResult(
                status=LayerStatus.REJECTED,
                output=None,
                metadata={'errors': validation.errors}
            )

        return LayerResult(
            status=LayerStatus.PASSED,
            output=input_data,
            metadata={'intent': intent, 'ambiguities_resolved': len(input_data.resolved_ambiguities)}
        )
```

### 配置参数

```yaml
prompt_layer:
  # 意图识别配置
  intent_recognition:
    confidence_threshold: 0.7
    enable_fallback: true
    fallback_intent: "GENERAL"

  # 上下文注入配置
  context_injection:
    max_context_size: 4096
    include_tech_stack: true
    include_coding_standards: true
    include_project_structure: true
    include_dependencies: true
    include_environment: true

  # 歧义消解配置
  ambiguity_resolution:
    auto_resolve: true
    max_inference_attempts: 3
    require_confirmation_for:
      - "技术选型"
      - "功能范围"
      - "性能要求"

  # 输入验证配置
  input_validation:
    check_required_fields: true
    validate_format: true
    security_check: true
    resource_check: true
```

### 使用示例

```python
from four_d_defense import FourDimensionalDefense, InputData

# 初始化四维防线系统
defense = FourDimensionalDefense()

# 准备输入数据
input_data = InputData(
    content="生成一个用户认证模块，支持OAuth2.0登录",
    context={
        'project_name': 'my-app',
        'tech_stack': ['Python', 'FastAPI', 'PostgreSQL']
    },
    metadata={
        'user_id': 'user-123',
        'timestamp': '2024-01-01T00:00:00Z'
    }
)

# 执行完整检查
result = defense.run_full_check(input_data)

if result.overall_status == DefenseStatus.PASSED:
    print("✅ 通过四维防线检查")
    print(f"质量评分: {result.quality_score}/5.0")
    print(f"各层状态: {result.layer_statuses}")
else:
    print("❌ 未通过四维防线检查")
    print(f"失败层级: {result.failed_layer}")
    print(f"错误信息: {result.errors}")
```

## 第2层: 能力约束层 (CapabilityLayer)

### 功能概述

能力约束层评估系统是否具备完成当前任务的能力，包括技能匹配度、知识覆盖范围、工具可用性等。只有当系统确认有能力完成任务时，才允许进入下一层。

### 核心组件

#### 2.1 技能匹配度评估 (Skill Matching)

**功能**: 评估当前任务与系统技能的匹配程度，确保任务在系统能力范围内。

**评估维度**:
- 技术栈匹配度 (0-100%)
- 任务类型匹配度 (0-100%)
- 复杂度匹配度 (0-100%)
- 综合匹配度 (加权平均)

**实现方式**:
```python
class CapabilityLayer:
    def evaluate_skill_matching(self, input_data: InputData) -> float:
        """
        评估技能匹配度
        """
        # 技术栈匹配
        tech_stack_score = self._evaluate_tech_stack_match(
            input_data.context.get('tech_stack', []),
            input_data.intent
        )

        # 任务类型匹配
        task_type_score = self._evaluate_task_type_match(
            input_data.intent,
            input_data.content
        )

        # 复杂度匹配
        complexity_score = self._evaluate_complexity_match(
            input_data.content,
            input_data.metadata
        )

        # 加权平均
        overall_score = (
            tech_stack_score * 0.4 +
            task_type_score * 0.4 +
            complexity_score * 0.2
        )

        return overall_score
```

#### 2.2 知识覆盖检查 (Knowledge Coverage)

**功能**: 检查系统知识库是否包含完成任务所需的知识。

**知识库覆盖范围**:
- 编程语言语法和最佳实践
- 框架和库的使用方法
- 设计模式和架构原则
- 安全编码规范
- 性能优化技巧

**实现方式**:
```python
class CapabilityLayer:
    def check_knowledge_coverage(self, input_data: InputData) -> CoverageResult:
        """
        检查知识覆盖范围
        """
        required_knowledge = self._extract_required_knowledge(input_data)
        coverage = {}

        for knowledge_item in required_knowledge:
            coverage[knowledge_item] = self._knowledge_base.has(knowledge_item)

        coverage_rate = sum(coverage.values()) / len(coverage)

        return CoverageResult(
            coverage_rate=coverage_rate,
            covered_items=[k for k, v in coverage.items() if v],
            missing_items=[k for k, v in coverage.items() if not v]
        )
```

#### 2.3 工具可用性验证 (Tool Availability)

**功能**: 验证完成任务所需的工具是否可用。

**工具类型**:
- 文件操作工具 (Read, Write, Edit)
- 命令执行工具 (RunCommand)
- 搜索工具 (SearchCodebase, Grep)
- 依赖管理工具 (npm, pip, cargo)
- 测试工具 (pytest, jest, cargo test)

**实现方式**:
```python
class CapabilityLayer:
    def verify_tool_availability(self, input_data: InputData) -> ToolAvailabilityResult:
        """
        验证工具可用性
        """
        required_tools = self._identify_required_tools(input_data)
        availability = {}

        for tool in required_tools:
            availability[tool] = self._tool_registry.is_available(tool)

        available_tools = [t for t, v in availability.items() if v]
        unavailable_tools = [t for t, v in availability.items() if not v]

        return ToolAvailabilityResult(
            all_available=len(unavailable_tools) == 0,
            available_tools=available_tools,
            unavailable_tools=unavailable_tools
        )
```

#### 2.4 能力缺口识别 (Capability Gap Detection)

**功能**: 识别系统当前能力与任务需求之间的差距，提供改进建议。

**缺口类型**:
- 知识缺口: 缺少特定领域的知识
- 工具缺口: 缺少必要的工具或插件
- 技能缺口: 技能匹配度低于阈值
- 资源缺口: 缺少必要的计算资源或权限

**实现方式**:
```python
class CapabilityLayer:
    def identify_capability_gaps(self, input_data: InputData) -> List[CapabilityGap]:
        """
        识别能力缺口
        """
        gaps = []

        # 技能匹配度检查
        skill_score = self.evaluate_skill_matching(input_data)
        if skill_score < 0.8:
            gaps.append(CapabilityGap(
                type=GapType.SKILL,
                severity=GapSeverity.HIGH if skill_score < 0.6 else GapSeverity.MEDIUM,
                description=f"技能匹配度 {skill_score:.2%} 低于阈值 80%",
                suggestion="考虑提供更多上下文信息或分解任务"
            ))

        # 知识覆盖检查
        coverage = self.check_knowledge_coverage(input_data)
        if coverage.coverage_rate < 0.9:
            gaps.append(CapabilityGap(
                type=GapType.KNOWLEDGE,
                severity=GapSeverity.MEDIUM,
                description=f"知识覆盖 {coverage.coverage_rate:.2%} 低于阈值 90%",
                suggestion=f"缺少知识: {', '.join(coverage.missing_items[:5])}"
            ))

        # 工具可用性检查
        tools = self.verify_tool_availability(input_data)
        if not tools.all_available:
            gaps.append(CapabilityGap(
                type=GapType.TOOL,
                severity=GapSeverity.HIGH,
                description=f"缺少必要工具: {', '.join(tools.unavailable_tools)}",
                suggestion="安装缺失的工具或使用替代方案"
            ))

        return gaps
```

### API接口

```python
class CapabilityLayer:
    def process(self, input_data: InputData) -> LayerResult:
        """
        完整的能力约束层处理流程

        Args:
            input_data: 输入数据（已通过Prompt层处理）

        Returns:
            LayerResult: 处理结果
        """
        # 1. 技能匹配度评估
        skill_score = self.evaluate_skill_matching(input_data)
        if skill_score < self.config.min_skill_score:
            return LayerResult(
                status=LayerStatus.REJECTED,
                output=None,
                metadata={
                    'reason': '技能匹配度不足',
                    'skill_score': skill_score,
                    'threshold': self.config.min_skill_score
                }
            )

        # 2. 知识覆盖检查
        coverage = self.check_knowledge_coverage(input_data)
        if coverage.coverage_rate < self.config.min_coverage_rate:
            return LayerResult(
                status=LayerStatus.REJECTED,
                output=None,
                metadata={
                    'reason': '知识覆盖不足',
                    'coverage_rate': coverage.coverage_rate,
                    'missing_items': coverage.missing_items
                }
            )

        # 3. 工具可用性验证
        tools = self.verify_tool_availability(input_data)
        if not tools.all_available:
            return LayerResult(
                status=LayerStatus.REJECTED,
                output=None,
                metadata={
                    'reason': '工具不可用',
                    'unavailable_tools': tools.unavailable_tools
                }
            )

        # 4. 能力缺口识别（仅警告，不拒绝）
        gaps = self.identify_capability_gaps(input_data)

        return LayerResult(
            status=LayerStatus.PASSED,
            output=input_data,
            metadata={
                'skill_score': skill_score,
                'coverage_rate': coverage.coverage_rate,
                'capability_gaps': gaps
            }
        )
```

### 配置参数

```yaml
capability_layer:
  # 技能匹配度配置
  skill_matching:
    min_score: 0.8
    tech_stack_weight: 0.4
    task_type_weight: 0.4
    complexity_weight: 0.2

  # 知识覆盖配置
  knowledge_coverage:
    min_coverage_rate: 0.9
    max_missing_items: 5

  # 工具可用性配置
  tool_availability:
    check_required: true
    fallback_tools:
      "grep": ["Select-String"]
      "npm": ["yarn", "pnpm"]

  # 能力缺口配置
  capability_gaps:
    identify_gaps: true
    warn_on_gaps: true
    block_on_critical_gaps: true
```

## 第3层: 规则校验层 (RuleValidationLayer)

### 功能概述

规则校验层对输出内容进行自动化检查，确保符合编码规范、安全要求、性能标准等规则。该层集成了多种静态分析工具和自定义规则引擎。

### 核心组件

#### 3.1 Lint检查集成 (Lint Integration)

**功能**: 集成多种Lint工具进行代码质量检查。

**支持的Lint工具**:
- Python: pylint, flake8, black, mypy
- JavaScript/TypeScript: ESLint, Prettier
- Go: gofmt, golint, golangci-lint
- Rust: clippy, rustfmt

**检查规则**:
- 代码风格一致性
- 命名规范
- 复杂度控制
- 类型安全
- 最佳实践

**实现方式**:
```python
class RuleValidationLayer:
    def run_lint_checks(self, output: str, language: str) -> LintResult:
        """
        运行Lint检查
        """
        linter = self._get_linter(language)
        issues = linter.check(output)

        # 分类问题
        errors = [i for i in issues if i.severity == 'error']
        warnings = [i for i in issues if i.severity == 'warning']
        suggestions = [i for i in issues if i.severity == 'suggestion']

        return LintResult(
            total_issues=len(issues),
            errors=len(errors),
            warnings=len(warnings),
            suggestions=len(suggestions),
            issues=issues
        )
```

#### 3.2 安全扫描接口 (Security Scanning)

**功能**: 扫描代码中的安全漏洞和风险。

**安全检查项**:
- SQL注入漏洞
- XSS漏洞
- 命令注入
- 不安全的随机数生成
- 硬编码密钥
- 不安全的反序列化
- 依赖漏洞

**实现方式**:
```python
class RuleValidationLayer:
    def run_security_scan(self, output: str, language: str) -> SecurityResult:
        """
        运行安全扫描
        """
        scanner = self._get_security_scanner(language)
        vulnerabilities = scanner.scan(output)

        # 按严重程度分类
        critical = [v for v in vulnerabilities if v.severity == 'critical']
        high = [v for v in vulnerabilities if v.severity == 'high']
        medium = [v for v in vulnerabilities if v.severity == 'medium']
        low = [v for v in vulnerabilities if v.severity == 'low']

        return SecurityResult(
            total_vulnerabilities=len(vulnerabilities),
            critical=len(critical),
            high=len(high),
            medium=len(medium),
            low=len(low),
            vulnerabilities=vulnerabilities
        )
```

#### 3.3 硬编码检测调用 (Hardcoded Detection)

**功能**: 调用硬编码检测器，扫描代码中的硬编码敏感信息。

**检测模式** (25种正则模式):
- 密码模式: `password\s*=\s*['"]\w+['"]`
- API密钥: `api[_-]?key\s*=\s*['"][A-Za-z0-9]{20,}['"]`
- Token: `token\s*=\s*['"][A-Za-z0-9._-]{20,}['"]`
- 数据库连接字符串: `mongodb://\w+:\w+@`
- AWS密钥: `AKIA[0-9A-Z]{16}`
- 私钥: `-----BEGIN (RSA )?PRIVATE KEY-----`
- Base64编码: `[A-Za-z0-9+/]{100,}={0,2}`
- JWT: `eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+`
- IP地址: `\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b`
- 数据库端口: `:(3306|5432|27017|6379|11211)\b`

**实现方式**:
```python
class RuleValidationLayer:
    def run_hardcoded_detection(self, output: str) -> HardcodedResult:
        """
        运行硬编码检测
        """
        detector = HardcodedDetector()
        detections = detector.scan_content(output)

        # 按严重程度分类
        critical = [d for d in detections if d.severity == 'critical']
        high = [d for d in detections if d.severity == 'high']
        medium = [d for d in detections if d.severity == 'medium']
        low = [d for d in detections if d.severity == 'low']

        return HardcodedResult(
            total_detections=len(detections),
            critical=len(critical),
            high=len(high),
            medium=len(medium),
            low=len(low),
            detections=detections
        )
```

#### 3.4 性能基线对比 (Performance Baseline)

**功能**: 对比输出与性能基线，确保性能指标符合要求。

**性能指标**:
- 时间复杂度
- 空间复杂度
- 响应时间
- 吞吐量
- 资源消耗

**实现方式**:
```python
class RuleValidationLayer:
    def compare_performance_baseline(self, output: str, baseline: PerformanceBaseline) -> PerformanceResult:
        """
        对比性能基线
        """
        analysis = self._analyze_performance(output)

        # 对比基线
        comparisons = {}
        for metric, baseline_value in baseline.metrics.items():
            actual_value = analysis.get(metric)
            if actual_value:
                comparison = self._compare_values(actual_value, baseline_value)
                comparisons[metric] = comparison

        # 检查是否超标
        exceeded = [m for m, c in comparisons.items() if c.exceeded]

        return PerformanceResult(
            all_passed=len(exceeded) == 0,
            comparisons=comparisons,
            exceeded_metrics=exceeded
        )
```

### API接口

```python
class RuleValidationLayer:
    def process(self, output: str, metadata: dict) -> LayerResult:
        """
        完整的规则校验层处理流程

        Args:
            output: 输出内容（代码、文档等）
            metadata: 元数据（语言、类型等）

        Returns:
            LayerResult: 处理结果
        """
        issues = []

        # 1. Lint检查
        if metadata.get('type') == 'code':
            lint_result = self.run_lint_checks(output, metadata.get('language'))
            if lint_result.errors > 0:
                issues.append(f"Lint错误: {lint_result.errors}个")
            if lint_result.warnings > self.config.max_warnings:
                issues.append(f"Lint警告过多: {lint_result.warnings}个")

        # 2. 安全扫描
        security_result = self.run_security_scan(output, metadata.get('language'))
        if security_result.critical > 0:
            issues.append(f"严重安全漏洞: {security_result.critical}个")
        if security_result.high > self.config.max_high_vulnerabilities:
            issues.append(f"高危安全漏洞: {security_result.high}个")

        # 3. 硬编码检测
        hardcoded_result = self.run_hardcoded_detection(output)
        if hardcoded_result.critical > 0:
            issues.append(f"严重硬编码: {hardcoded_result.critical}个")
        if hardcoded_result.high > 0:
            issues.append(f"高危硬编码: {hardcoded_result.high}个")

        # 4. 性能基线对比
        if metadata.get('baseline'):
            performance_result = self.compare_performance_baseline(
                output,
                metadata['baseline']
            )
            if not performance_result.all_passed:
                issues.append(f"性能超标: {', '.join(performance_result.exceeded_metrics)}")

        # 判断是否通过
        if issues:
            return LayerResult(
                status=LayerStatus.REJECTED,
                output=None,
                metadata={'issues': issues}
            )

        return LayerResult(
            status=LayerStatus.PASSED,
            output=output,
            metadata={
                'lint_result': lint_result if metadata.get('type') == 'code' else None,
                'security_result': security_result,
                'hardcoded_result': hardcoded_result,
                'performance_result': performance_result if metadata.get('baseline') else None
            }
        )
```

### 配置参数

```yaml
rule_validation_layer:
  # Lint检查配置
  lint:
    enabled: true
    max_warnings: 10
    languages:
      python:
        tools: ["pylint", "flake8", "mypy"]
        config: ".pylintrc"
      javascript:
        tools: ["eslint"]
        config: ".eslintrc.json"

  # 安全扫描配置
  security:
    enabled: true
    max_high_vulnerabilities: 0
    max_medium_vulnerabilities: 5
    tools:
      python: ["bandit"]
      javascript: ["eslint-plugin-security"]

  # 硬编码检测配置
  hardcoded:
    enabled: true
    patterns_file: "config/hardcoded_patterns.yaml"
    severity_threshold: "high"

  # 性能基线配置
  performance:
    enabled: true
    baseline_file: "config/performance_baseline.yaml"
    metrics:
      - "time_complexity"
      - "space_complexity"
      - "response_time"
```

## 第4层: 兜底恢复层 (FallbackRecoveryLayer)

### 功能概述

兜底恢复层是四维防线的最后一道关卡，负责对输出进行质量评分，并在质量不达标时触发回滚或降级策略。

### 核心组件

#### 4.1 质量评分 (Quality Scoring)

**功能**: 对输出内容进行多维度质量评分。

**评分维度** (5分制):
- 完整性 (Completeness): 输出是否完整，是否满足所有需求
- 准确性 (Accuracy): 输出是否正确，是否符合技术规范
- 清晰度 (Clarity): 输出是否清晰易懂，代码是否有注释
- 可操作性 (Actionability): 输出是否可以直接使用，是否需要额外修改
- 安全性 (Safety): 输出是否安全，是否存在安全风险

**实现方式**:
```python
class FallbackRecoveryLayer:
    def score_quality(self, output: str, requirements: dict) -> QualityScore:
        """
        评估输出质量
        """
        scores = {}

        # 完整性评分
        scores['completeness'] = self._evaluate_completeness(output, requirements)

        # 准确性评分
        scores['accuracy'] = self._evaluate_accuracy(output, requirements)

        # 清晰度评分
        scores['clarity'] = self._evaluate_clarity(output)

        # 可操作性评分
        scores['actionability'] = self._evaluate_actionability(output)

        # 安全性评分
        scores['safety'] = self._evaluate_safety(output)

        # 计算平均分
        overall_score = sum(scores.values()) / len(scores)

        return QualityScore(
            overall_score=overall_score,
            dimension_scores=scores,
            passed=overall_score >= self.config.min_quality_score
        )
```

#### 4.2 自动回滚 (Automatic Rollback)

**功能**: 当质量评分不达标时，自动回滚到之前的状态。

**回滚策略**:
- 文件回滚: 恢复文件到修改前的版本
- 代码回滚: 撤销代码更改
- 配置回滚: 恢复配置文件到之前的状态
- 依赖回滚: 恢复依赖到之前的版本

**实现方式**:
```python
class FallbackRecoveryLayer:
    def rollback(self, rollback_point: RollbackPoint) -> RollbackResult:
        """
        执行自动回滚
        """
        results = []

        # 文件回滚
        for file_change in rollback_point.file_changes:
            result = self._rollback_file(file_change)
            results.append(result)

        # 配置回滚
        for config_change in rollback_point.config_changes:
            result = self._rollback_config(config_change)
            results.append(result)

        # 依赖回滚
        for dependency_change in rollback_point.dependency_changes:
            result = self._rollback_dependency(dependency_change)
            results.append(result)

        return RollbackResult(
            success=all(r.success for r in results),
            results=results
        )
```

#### 4.3 降级策略 (Degradation Strategy)

**功能**: 当某层防线不可用时，自动降级到安全模式。

**降级场景**:
- Prompt层不可用: 跳过意图识别，直接使用原始输入
- 能力层不可用: 跳过能力检查，直接执行任务
- 规则层不可用: 跳过规则校验，仅进行基本验证
- 恢复层不可用: 跳过质量评分，直接输出

**实现方式**:
```python
class FallbackRecoveryLayer:
    def apply_degradation(self, failed_layer: str) -> DegradationResult:
        """
        应用降级策略
        """
        degradation_plan = self._get_degradation_plan(failed_layer)

        results = []
        for action in degradation_plan.actions:
            result = self._execute_degradation_action(action)
            results.append(result)

        return DegradationResult(
            success=all(r.success for r in results),
            degraded_mode=True,
            results=results
        )
```

#### 4.4 错误日志记录 (Error Logging)

**功能**: 记录所有错误和决策过程，支持审计和回溯。

**日志内容**:
- 输入信息
- 各层处理结果
- 质量评分
- 回滚/降级决策
- 错误堆栈

**实现方式**:
```python
class FallbackRecoveryLayer:
    def log_error(self, error: ErrorInfo) -> None:
        """
        记录错误日志
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'error_id': error.error_id,
            'error_type': error.error_type,
            'error_message': error.error_message,
            'failed_layer': error.failed_layer,
            'input_data': error.input_data,
            'layer_results': error.layer_results,
            'quality_score': error.quality_score,
            'action_taken': error.action_taken,
            'stack_trace': error.stack_trace
        }

        self._write_to_log_file(log_entry)
        self._write_to_database(log_entry)
```

### API接口

```python
class FallbackRecoveryLayer:
    def process(self, output: str, metadata: dict) -> LayerResult:
        """
        完整的兜底恢复层处理流程

        Args:
            output: 输出内容
            metadata: 元数据（需求、回滚点等）

        Returns:
            LayerResult: 处理结果
        """
        # 1. 质量评分
        quality_score = self.score_quality(output, metadata.get('requirements', {}))

        if not quality_score.passed:
            # 2. 自动回滚
            rollback_point = metadata.get('rollback_point')
            if rollback_point:
                rollback_result = self.rollback(rollback_point)
                if rollback_result.success:
                    return LayerResult(
                        status=LayerStatus.ROLLED_BACK,
                        output=None,
                        metadata={
                            'reason': '质量评分不达标',
                            'quality_score': quality_score.overall_score,
                            'threshold': self.config.min_quality_score,
                            'action': 'rollback'
                        }
                    )

            # 3. 降级策略
            degradation_result = self.apply_degradation(metadata.get('failed_layer'))
            if degradation_result.success:
                return LayerResult(
                    status=LayerStatus.DEGRADED,
                    output=output,
                    metadata={
                        'reason': '质量评分不达标，已降级',
                        'quality_score': quality_score.overall_score,
                        'degraded_mode': True
                    }
                )

            # 4. 记录错误
            error_info = ErrorInfo(
                error_id=self._generate_error_id(),
                error_type='quality_check_failed',
                error_message=f'质量评分 {quality_score.overall_score:.2f} 低于阈值 {self.config.min_quality_score}',
                failed_layer='FallbackRecoveryLayer',
                input_data=metadata,
                quality_score=quality_score,
                action_taken='reject'
            )
            self.log_error(error_info)

            return LayerResult(
                status=LayerStatus.REJECTED,
                output=None,
                metadata={
                    'reason': '质量评分不达标且无法回滚或降级',
                    'quality_score': quality_score.overall_score,
                    'error_id': error_info.error_id
                }
            )

        return LayerResult(
            status=LayerStatus.PASSED,
            output=output,
            metadata={
                'quality_score': quality_score.overall_score,
                'dimension_scores': quality_score.dimension_scores
            }
        )
```

### 配置参数

```yaml
fallback_recovery_layer:
  # 质量评分配置
  quality_scoring:
    min_score: 3.5
    dimensions:
      completeness:
        weight: 0.2
        threshold: 3.0
      accuracy:
        weight: 0.3
        threshold: 3.5
      clarity:
        weight: 0.2
        threshold: 3.0
      actionability:
        weight: 0.2
        threshold: 3.0
      safety:
        weight: 0.1
        threshold: 4.0

  # 自动回滚配置
  rollback:
    enabled: true
    max_rollback_attempts: 3
    rollback_timeout: 30
    backup_before_changes: true

  # 降级策略配置
  degradation:
    enabled: true
    fallback_modes:
      prompt_layer: "skip_intent_recognition"
      capability_layer: "skip_capability_check"
      rule_validation_layer: "basic_validation_only"
      fallback_recovery_layer: "skip_quality_scoring"

  # 错误日志配置
  error_logging:
    enabled: true
    log_file: "logs/four_d_defense_errors.log"
    log_database: true
    log_level: "DEBUG"
```

## 完整API接口

### FourDimensionalDefense 主类

```python
class FourDimensionalDefense:
    """
    四维度输出防线系统主类
    """

    def __init__(self, config: Optional[DefenseConfig] = None):
        """
        初始化四维防线系统

        Args:
            config: 配置对象，如果为None则使用默认配置
        """
        self.config = config or DefenseConfig()
        self.prompt_layer = PromptLayer(self.config.prompt_layer)
        self.capability_layer = CapabilityLayer(self.config.capability_layer)
        self.rule_validation_layer = RuleValidationLayer(self.config.rule_validation_layer)
        self.fallback_recovery_layer = FallbackRecoveryLayer(self.config.fallback_recovery_layer)

    def run_full_check(self, input_data: InputData) -> DefenseResult:
        """
        执行完整的四维防线检查

        Args:
            input_data: 输入数据

        Returns:
            DefenseResult: 检查结果
        """
        layer_results = {}

        # 第1层: Prompt工程层
        try:
            result = self.prompt_layer.process(input_data)
            layer_results['prompt_layer'] = result
            if result.status != LayerStatus.PASSED:
                return DefenseResult(
                    overall_status=DefenseStatus.FAILED,
                    failed_layer='prompt_layer',
                    layer_results=layer_results,
                    errors=result.metadata.get('errors', [])
                )
        except Exception as e:
            return self._handle_layer_failure('prompt_layer', e, layer_results)

        # 第2层: 能力约束层
        try:
            result = self.capability_layer.process(result.output)
            layer_results['capability_layer'] = result
            if result.status != LayerStatus.PASSED:
                return DefenseResult(
                    overall_status=DefenseStatus.FAILED,
                    failed_layer='capability_layer',
                    layer_results=layer_results,
                    errors=[result.metadata.get('reason')]
                )
        except Exception as e:
            return self._handle_layer_failure('capability_layer', e, layer_results)

        # 第3层: 规则校验层
        try:
            result = self.rule_validation_layer.process(result.output, input_data.metadata)
            layer_results['rule_validation_layer'] = result
            if result.status != LayerStatus.PASSED:
                return DefenseResult(
                    overall_status=DefenseStatus.FAILED,
                    failed_layer='rule_validation_layer',
                    layer_results=layer_results,
                    errors=result.metadata.get('issues', [])
                )
        except Exception as e:
            return self._handle_layer_failure('rule_validation_layer', e, layer_results)

        # 第4层: 兜底恢复层
        try:
            result = self.fallback_recovery_layer.process(result.output, input_data.metadata)
            layer_results['fallback_recovery_layer'] = result

            if result.status == LayerStatus.PASSED:
                return DefenseResult(
                    overall_status=DefenseStatus.PASSED,
                    layer_results=layer_results,
                    quality_score=result.metadata.get('quality_score'),
                    output=result.output
                )
            elif result.status == LayerStatus.DEGRADED:
                return DefenseResult(
                    overall_status=DefenseStatus.DEGRADED,
                    layer_results=layer_results,
                    quality_score=result.metadata.get('quality_score'),
                    output=result.output,
                    warnings=['已降级模式运行']
                )
            elif result.status == LayerStatus.ROLLED_BACK:
                return DefenseResult(
                    overall_status=DefenseStatus.ROLLED_BACK,
                    failed_layer='fallback_recovery_layer',
                    layer_results=layer_results,
                    errors=['质量评分不达标，已回滚']
                )
            else:
                return DefenseResult(
                    overall_status=DefenseStatus.FAILED,
                    failed_layer='fallback_recovery_layer',
                    layer_results=layer_results,
                    errors=result.metadata.get('reason', ['质量评分不达标'])
                )
        except Exception as e:
            return self._handle_layer_failure('fallback_recovery_layer', e, layer_results)

    def _handle_layer_failure(self, layer_name: str, error: Exception, layer_results: dict) -> DefenseResult:
        """
        处理层失败情况
        """
        error_info = ErrorInfo(
            error_id=self._generate_error_id(),
            error_type='layer_exception',
            error_message=str(error),
            failed_layer=layer_name,
            stack_trace=traceback.format_exc()
        )

        # 记录错误
        self.fallback_recovery_layer.log_error(error_info)

        # 尝试降级
        degradation_result = self.fallback_recovery_layer.apply_degradation(layer_name)
        if degradation_result.success:
            return DefenseResult(
                overall_status=DefenseStatus.DEGRADED,
                failed_layer=layer_name,
                layer_results=layer_results,
                errors=[f'{layer_name} 异常: {str(error)}'],
                warnings=['已降级模式运行']
            )

        return DefenseResult(
            overall_status=DefenseStatus.FAILED,
            failed_layer=layer_name,
            layer_results=layer_results,
            errors=[f'{layer_name} 异常且无法降级: {str(error)}']
        )
```

## 数据类定义

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime

class IntentType(Enum):
    """意图类型"""
    CODE_GENERATION = "code_generation"
    CODE_REFACTORING = "code_refactoring"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEBUGGING = "debugging"
    ARCHITECTURE = "architecture"
    CONFIGURATION = "configuration"
    GENERAL = "general"

class LayerStatus(Enum):
    """层状态"""
    PASSED = "passed"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"
    DEGRADED = "degraded"

class DefenseStatus(Enum):
    """防线状态"""
    PASSED = "passed"
    FAILED = "failed"
    DEGRADED = "degraded"
    ROLLED_BACK = "rolled_back"

class FallbackStrategy(Enum):
    """降级策略"""
    SKIP_LAYER = "skip_layer"
    USE_CACHE = "use_cache"
    SIMPLIFIED_CHECK = "simplified_check"
    MANUAL_INTERVENTION = "manual_intervention"

@dataclass
class InputData:
    """输入数据"""
    content: str
    context: Dict[str, Any]
    metadata: Dict[str, Any]
    intent: Optional[IntentType] = None
    resolved_ambiguities: Dict[str, Any] = None

@dataclass
class LayerResult:
    """层处理结果"""
    status: LayerStatus
    output: Optional[Any]
    metadata: Dict[str, Any]

@dataclass
class DefenseResult:
    """防线检查结果"""
    overall_status: DefenseStatus
    layer_results: Dict[str, LayerResult]
    failed_layer: Optional[str] = None
    quality_score: Optional[float] = None
    output: Optional[Any] = None
    errors: List[str] = None
    warnings: List[str] = None

@dataclass
class QualityScore:
    """质量评分"""
    overall_score: float
    dimension_scores: Dict[str, float]
    passed: bool

@dataclass
class ErrorInfo:
    """错误信息"""
    error_id: str
    error_type: str
    error_message: str
    failed_layer: str
    input_data: Optional[Dict[str, Any]] = None
    layer_results: Optional[Dict[str, Any]] = None
    quality_score: Optional[QualityScore] = None
    action_taken: Optional[str] = None
    stack_trace: Optional[str] = None
```

## 使用示例

### 示例1: 代码生成场景

```python
from four_d_defense import FourDimensionalDefense, InputData, IntentType

# 初始化
defense = FourDimensionalDefense()

# 准备输入
input_data = InputData(
    content="生成一个用户认证模块，支持OAuth2.0登录，包含注册、登录、登出功能",
    context={
        'project_name': 'my-app',
        'tech_stack': ['Python', 'FastAPI', 'PostgreSQL'],
        'coding_standards': 'PEP8'
    },
    metadata={
        'user_id': 'user-123',
        'timestamp': '2024-01-01T00:00:00Z',
        'type': 'code',
        'language': 'python',
        'requirements': {
            'features': ['registration', 'login', 'logout'],
            'auth_method': 'OAuth2.0'
        }
    }
)

# 执行检查
result = defense.run_full_check(input_data)

# 处理结果
if result.overall_status == DefenseStatus.PASSED:
    print("✅ 通过四维防线检查")
    print(f"质量评分: {result.quality_score}/5.0")
    print(f"输出内容:\n{result.output}")
elif result.overall_status == DefenseStatus.DEGRADED:
    print("⚠️ 降级模式运行")
    print(f"质量评分: {result.quality_score}/5.0")
    print(f"警告: {result.warnings}")
    print(f"输出内容:\n{result.output}")
else:
    print("❌ 未通过四维防线检查")
    print(f"失败层级: {result.failed_layer}")
    print(f"错误信息: {result.errors}")
```

### 示例2: 文档编写场景

```python
# 准备输入
input_data = InputData(
    content="编写API文档，描述用户认证相关的所有端点",
    context={
        'project_name': 'my-app',
        'api_version': 'v1'
    },
    metadata={
        'type': 'documentation',
        'format': 'markdown',
        'requirements': {
            'include_endpoints': [
                '/api/v1/auth/register',
                '/api/v1/auth/login',
                '/api/v1/auth/logout'
            ],
            'include_examples': True
        }
    }
)

# 执行检查
result = defense.run_full_check(input_data)

# 处理结果
if result.overall_status == DefenseStatus.PASSED:
    # 保存文档
    with open('docs/api_auth.md', 'w', encoding='utf-8') as f:
        f.write(result.output)
    print("✅ 文档生成成功")
```

### 示例3: 测试用例生成场景

```python
# 准备输入
input_data = InputData(
    content="为用户认证模块生成完整的测试用例，覆盖所有边界情况",
    context={
        'project_name': 'my-app',
        'test_framework': 'pytest'
    },
    metadata={
        'type': 'testing',
        'language': 'python',
        'requirements': {
            'test_framework': 'pytest',
            'coverage_target': 0.95,
            'include_edge_cases': True
        }
    }
)

# 执行检查
result = defense.run_full_check(input_data)

# 处理结果
if result.overall_status == DefenseStatus.PASSED:
    # 保存测试用例
    with open('tests/test_auth.py', 'w', encoding='utf-8') as f:
        f.write(result.output)
    print("✅ 测试用例生成成功")
```

## 最佳实践

### 1. 合理配置阈值

根据项目需求调整各层的阈值，避免过于严格导致频繁拒绝，或过于宽松导致质量下降。

```yaml
# 推荐配置
prompt_layer:
  intent_recognition:
    confidence_threshold: 0.7  # 适中，避免误判

capability_layer:
  skill_matching:
    min_score: 0.8  # 较高，确保能力匹配

rule_validation_layer:
  security:
    max_high_vulnerabilities: 0  # 严格，零容忍

fallback_recovery_layer:
  quality_scoring:
    min_score: 3.5  # 较高，确保质量
```

### 2. 启用降级策略

在开发阶段可以启用降级策略，提高系统可用性；在生产环境建议关闭降级，确保质量。

```yaml
fallback_recovery_layer:
  degradation:
    enabled: true  # 开发环境
    # enabled: false  # 生产环境
```

### 3. 定期审查日志

定期审查错误日志，识别常见问题和改进点。

```python
# 查看最近7天的错误日志
import json
from datetime import datetime, timedelta

log_file = "logs/four_d_defense_errors.log"
with open(log_file, 'r', encoding='utf-8') as f:
    logs = [json.loads(line) for line in f]

# 过滤最近7天的日志
week_ago = datetime.now() - timedelta(days=7)
recent_logs = [
    log for log in logs
    if datetime.fromisoformat(log['timestamp']) > week_ago
]

# 统计失败层级
failed_layers = {}
for log in recent_logs:
    layer = log['failed_layer']
    failed_layers[layer] = failed_layers.get(layer, 0) + 1

print("最近7天失败层级统计:")
for layer, count in sorted(failed_layers.items(), key=lambda x: x[1], reverse=True):
    print(f"  {layer}: {count}次")
```

### 4. 集成到CI/CD

将四维防线集成到CI/CD流程中，确保所有输出都经过质量检查。

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Four-Dimensional Defense
        run: |
          python -m four_d_defense.check \
            --input docs/requirements.md \
            --output docs/api_spec.md \
            --config .trae/skills/sanliu/configs/four_d_defense.yaml

      - name: Upload Results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: defense-results
          path: logs/four_d_defense_*.log
```

## 与其他模块的集成

### 与操作优先级控制器的集成

四维防线与操作优先级控制器协同工作，根据操作优先级调整防线严格程度。

```python
from operation_priority import OperationPriorityController

# 获取操作优先级
priority, reason = OperationPriorityController.decide(task_context)

# 根据优先级调整防线配置
if priority == OperationPriority.MANUAL:
    # 手动操作，使用严格配置
    config = DefenseConfig(strict_mode=True)
elif priority == OperationPriority.SCRIPT:
    # 脚本操作，使用标准配置
    config = DefenseConfig(strict_mode=False)
else:
    # 命令操作，使用宽松配置
    config = DefenseConfig(strict_mode=False, allow_degradation=True)

defense = FourDimensionalDefense(config)
```

### 与资源协调器的集成

四维防线使用资源协调器管理资源，避免资源竞争。

```python
from resource_coordinator import ResourceCoordinator, ResourceType

# 注册资源
coordinator = ResourceCoordinator()
coordinator.register_resource('four_d_defense', ResourceType.COMPUTE)

# 获取资源锁
lock_token = coordinator.acquire_lock('four_d_defense', 'defense_agent', 'exclusive')

try:
    # 执行四维防线检查
    result = defense.run_full_check(input_data)
finally:
    # 释放资源锁
    coordinator.release_lock(lock_token)
```

### 与密钥管理系统的集成

四维防线第3层调用密钥管理系统进行硬编码检测。

```python
from secrets_manager import SecretsManager, HardcodedDetector

# 初始化密钥管理器
secrets_manager = SecretsManager()
secrets_manager.load()

# 初始化硬编码检测器
detector = HardcodedDetector()

# 在规则校验层中使用
class RuleValidationLayer:
    def run_hardcoded_detection(self, output: str) -> HardcodedResult:
        # 使用硬编码检测器
        detections = detector.scan_content(output)

        # 检查是否与已注册的密钥冲突
        for detection in detections:
            if secrets_manager.is_registered(detection.value):
                detection.severity = 'critical'

        return HardcodedResult(...)
```

### 与Agency Bridge的集成

四维防线可以调用Agency Bridge获取专业Agent的审查意见。

```python
from agency_bridge import AgencyBridge

# 初始化Agency Bridge
bridge = AgencyBridge()

# 在规则校验层中使用
class RuleValidationLayer:
    def run_agent_review(self, output: str, task_type: str) -> AgentReviewResult:
        # 调用专业Agent进行审查
        agents = bridge.recommend_agents(f"审查{task_type}代码")
        results = []

        for agent in agents:
            result = bridge.invoke_agent(
                agent.id,
                f"审查以下代码:\n{output}",
                {'task_type': task_type}
            )
            results.append(result)

        # 整合审查意见
        return AgentReviewResult(results=results)
```

## 故障排查

### 问题1: 某层频繁失败

**症状**: 某层（如规则校验层）频繁拒绝输出。

**排查步骤**:
1. 检查该层的配置阈值是否过于严格
2. 查看错误日志，分析失败原因
3. 检查输入数据是否完整和准确
4. 考虑启用降级策略

**解决方案**:
```yaml
# 调整阈值
rule_validation_layer:
  lint:
    max_warnings: 20  # 从10提高到20
  security:
    max_medium_vulnerabilities: 10  # 从5提高到10
```

### 问题2: 质量评分偏低

**症状**: 输出通过前三层，但在第4层质量评分不达标。

**排查步骤**:
1. 查看各维度评分，找出短板
2. 检查需求是否明确和完整
3. 检查输出是否符合编码规范
4. 考虑提供更多上下文信息

**解决方案**:
```python
# 提供更完整的需求
input_data.metadata['requirements'] = {
    'features': ['feature1', 'feature2', 'feature3'],
    'performance': {'response_time': '< 100ms'},
    'security': {'authentication': 'OAuth2.0'},
    'documentation': True
}
```

### 问题3: 降级模式频繁触发

**症状**: 系统频繁进入降级模式。

**排查步骤**:
1. 检查各层是否正常工作
2. 检查依赖工具是否可用
3. 检查配置文件是否正确
4. 查看错误日志，分析失败原因

**解决方案**:
```python
# 检查工具可用性
from four_d_defense import FourDimensionalDefense

defense = FourDimensionalDefense()
print("Prompt层可用:", defense.prompt_layer.is_available())
print("能力层可用:", defense.capability_layer.is_available())
print("规则层可用:", defense.rule_validation_layer.is_available())
print("恢复层可用:", defense.fallback_recovery_layer.is_available())
```

## 性能优化

### 1. 缓存机制

缓存常见输入的处理结果，避免重复计算。

```python
from functools import lru_cache

class PromptLayer:
    @lru_cache(maxsize=1000)
    def recognize_intent(self, content: str) -> IntentType:
        """缓存意图识别结果"""
        # ... 实现逻辑
```

### 2. 并行处理

并行执行独立的检查任务，提高处理速度。

```python
from concurrent.futures import ThreadPoolExecutor

class RuleValidationLayer:
    def process(self, output: str, metadata: dict) -> LayerResult:
        """并行执行检查任务"""
        with ThreadPoolExecutor(max_workers=4) as executor:
            # 并行执行Lint、安全扫描、硬编码检测
            future_lint = executor.submit(self.run_lint_checks, output, metadata.get('language'))
            future_security = executor.submit(self.run_security_scan, output, metadata.get('language'))
            future_hardcoded = executor.submit(self.run_hardcoded_detection, output)

            lint_result = future_lint.result()
            security_result = future_security.result()
            hardcoded_result = future_hardcoded.result()

        # ... 整合结果
```

### 3. 增量检查

对于增量更新，只检查变更部分。

```python
class RuleValidationLayer:
    def process_incremental(self, output: str, changes: List[Change]) -> LayerResult:
        """增量检查"""
        # 只检查变更的部分
        for change in changes:
            if change.type == 'addition':
                self._check_addition(change.content)
            elif change.type == 'modification':
                self._check_modification(change.old_content, change.new_content)
```

## 总结

四维度输出防线系统是 Sanliu v4.0 的核心质量保障体系，通过四层纵深防御确保所有输出的质量、安全性和可靠性。该系统具有以下特点:

- **全面性**: 覆盖从输入到输出的全流程
- **灵活性**: 支持自定义配置和降级策略
- **可追溯性**: 完整记录所有检查结果和决策过程
- **可扩展性**: 易于添加新的检查规则和工具
- **高性能**: 支持缓存、并行处理和增量检查

通过合理配置和使用四维防线系统，可以显著提高代码质量、减少安全漏洞、提升开发效率。
