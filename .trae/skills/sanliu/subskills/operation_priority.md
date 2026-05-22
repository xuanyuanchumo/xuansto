# 操作优先级架构 (Operation Priority)

## 概述

操作优先级架构是 Sanliu v4.0 的核心决策系统，基于 **Agent-First** 理念，为不同类型的操作提供三级优先级选择机制。该系统通过智能决策树、任务特征提取器和预演检查机制，确保每个任务都使用最优的操作方式，充分发挥AI的文件操作能力，同时保证安全性和效率。

### 核心理念

- **Agent-First**: 优先使用AI Agent的自主手动操作能力（第一优先级）
- **智能决策**: 基于任务特征自动推荐最优操作优先级
- **安全预演**: 对命令操作进行预演分析，评估影响范围和风险
- **危险拦截**: 自动识别并拦截危险命令，防止误操作
- **灵活降级**: 在无法使用首选方式时自动降级到安全的替代方案

### 三级优先级体系

```
┌─────────────────────────────────────────────────────────────┐
│                  操作优先级三级体系                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  第一优先级: 自主手动操作 (MANUAL)                      │  │
│  │  ├─ 适用场景: 文件读写/编辑、代码重构、文档编写          │  │
│  │  ├─ 推荐场景: 单文件操作、批量文件处理、精确修改          │  │
│  │  ├─ 优势: 精确控制、可追溯、支持回滚                     │  │
│  │  └─ 示例: Read/Write/Edit 工具直接操作文件              │  │
│  └───────────────────────────────────────────────────────┘  │
│                         ↓                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  第二优先级: 规划脚本操作 (SCRIPT)                      │  │
│  │  ├─ 适用场景: 重复性任务、复杂自动化工作流               │  │
│  │  ├─ 推荐场景: 批量依赖安装、环境配置、测试执行            │  │
│  │  ├─ 优势: 可复用、可版本控制、可并行执行                 │  │
│  │  └─ 示例: python script.py / npm install              │  │
│  └───────────────────────────────────────────────────────┘  │
│                         ↓                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  第三优先级: 命令操作 (COMMAND)                         │  │
│  │  ├─ 适用场景: 需要终端交互的操作、系统命令               │  │
│  │  ├─ 推荐场景: Git操作、Docker命令、进程管理             │  │
│  │  ├─ 要求: 必须通过预演检查                              │  │
│  │  └─ 示例: git commit / docker build                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    操作优先级控制系统架构                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  输入: 任务描述 + 任务上下文                                       │
│      ↓                                                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           任务特征提取器 (TaskFeatureExtractor)            │  │
│  │  ├─ 文件操作判断 (File Operation Detection)                │  │
│  │  ├─ 批量检测 (Batch Detection)                             │  │
│  │  ├─ 脚本可用性检查 (Script Availability Check)            │  │
│  │  ├─ 危险模式识别 (Dangerous Pattern Recognition)          │  │
│  │  └─ 专家需求识别 (Expert Need Identification)            │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              智能决策引擎 (Decision Engine)                 │  │
│  │  ├─ 规则1: 精确编辑规则 (Expert Precise Edit Rule)        │  │
│  │  ├─ 规则2: 单文件操作规则 (Single File Operation Rule)    │  │
│  │  ├─ 规则3: 批量操作规则 (Batch Operation Rule)            │  │
│  │  ├─ 规则4: 脚本存在规则 (Script Exists Rule)              │  │
│  │  ├─ 规则5: 复杂度规则 (Complexity Rule)                   │  │
│  │  └─ 规则6: 环境命令规则 (Environment Command Rule)        │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │            预演检查机制 (Preflight Check)                   │  │
│  │  ├─ 影响范围分析 (Impact Scope Analysis)                   │  │
│  │  ├─ 风险评估 (Risk Assessment)                             │  │
│  │  ├─ 回滚点创建 (Rollback Point Creation)                  │  │
│  │  └─ 危险命令拦截 (Dangerous Command Interception)         │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  输出: 推荐优先级 + 理由 + 预演结果                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 任务特征提取器

### 功能概述

任务特征提取器负责从任务描述和上下文中提取关键特征，为决策引擎提供输入。

### 特征维度

#### 1. 文件操作判断 (File Operation Detection)

**功能**: 判断任务是否涉及文件操作，以及操作的类型。

**提取的特征**:
- `is_file_operation`: 是否是文件操作
- `file_count`: 涉及的文件数量
- `operation_type`: 操作类型 (read/write/edit/create/delete)
- `file_patterns`: 文件路径模式

**实现方式**:
```python
class TaskFeatureExtractor:
    def extract_file_operations(self, task_description: str, context: dict) -> FileOperationFeature:
        """
        提取文件操作特征
        """
        features = FileOperationFeature()

        # 检测文件操作关键词
        file_keywords = {
            'read': ['读取', '查看', '打开', 'Read', 'Get', 'Fetch'],
            'write': ['写入', '保存', '创建', 'Write', 'Create', 'Generate'],
            'edit': ['编辑', '修改', '更新', 'Edit', 'Update', 'Modify'],
            'delete': ['删除', '移除', 'Delete', 'Remove', 'Rm']
        }

        for op_type, keywords in file_keywords.items():
            if any(kw in task_description for kw in keywords):
                features.is_file_operation = True
                features.operation_type = op_type
                break

        # 提取文件数量
        import re
        file_paths = re.findall(r'[\w\-./]+\.(py|js|ts|md|yaml|yml|json|html|css)', task_description)
        if context.get('files'):
            file_paths.extend(context['files'])
        features.file_count = len(set(file_paths))

        # 提取文件路径模式
        features.file_patterns = list(set(file_paths))

        return features
```

#### 2. 批量检测 (Batch Detection)

**功能**: 判断任务是否涉及批量操作。

**提取的特征**:
- `is_batch`: 是否是批量操作
- `batch_size`: 批量大小估计
- `batch_pattern`: 批量模式 (all_files/specific_pattern/range)

**实现方式**:
```python
class TaskFeatureExtractor:
    def extract_batch_features(self, task_description: str, context: dict) -> BatchFeature:
        """
        提取批量操作特征
        """
        features = BatchFeature()

        # 检测批量关键词
        batch_keywords = ['全部', '所有', '批量', '多个', 'all', 'every', 'batch', 'multiple']
        features.is_batch = any(kw in task_description.lower() for kw in batch_keywords)

        # 估算批量大小
        if features.is_batch:
            if context.get('files'):
                features.batch_size = len(context['files'])
            elif '所有' in task_description or 'all' in task_description.lower():
                features.batch_size = -1  # 表示所有文件
            else:
                # 尝试从描述中提取数字
                import re
                numbers = re.findall(r'\d+', task_description)
                features.batch_size = int(numbers[0]) if numbers else 10

        return features
```

#### 3. 脚本可用性检查 (Script Availability Check)

**功能**: 检查是否存在可用于完成任务的现有脚本。

**提取的特征**:
- `script_available`: 是否有可用脚本
- `script_path`: 脚本路径
- `script_match_score`: 脚本匹配度

**实现方式**:
```python
class TaskFeatureExtractor:
    def check_script_availability(self, task_description: str, context: dict) -> ScriptFeature:
        """
        检查脚本可用性
        """
        features = ScriptFeature()

        # 搜索相关脚本
        scripts_dir = context.get('scripts_dir', 'skillscripts')
        available_scripts = self._scan_scripts(scripts_dir)

        # 匹配脚本
        matched_scripts = []
        for script in available_scripts:
            match_score = self._calculate_script_match(task_description, script)
            if match_score > 0.5:
                matched_scripts.append((script, match_score))

        if matched_scripts:
            features.script_available = True
            best_script = max(matched_scripts, key=lambda x: x[1])
            features.script_path = best_script[0]
            features.script_match_score = best_script[1]

        return features
```

#### 4. 危险模式识别 (Dangerous Pattern Recognition)

**功能**: 识别任务中是否包含危险操作模式。

**提取的特征**:
- `is_dangerous`: 是否危险
- `danger_level`: 危险等级 (LOW/MEDIUM/HIGH/CRITICAL)
- `danger_reasons`: 危险原因列表

**实现方式**:
```python
class TaskFeatureExtractor:
    def recognize_dangerous_patterns(self, task_description: str, command: Optional[str] = None) -> DangerFeature:
        """
        识别危险模式
        """
        features = DangerFeature()

        # 检查21种危险命令模式
        dangerous_patterns = [
            (r'rm\s+-rf\s+/', 'CRITICAL', '删除根目录'),
            (r'rm\s+-rf\s+\*', 'CRITICAL', '删除所有文件'),
            (r'drop\s+table', 'CRITICAL', '删除数据库表'),
            (r'format\s+[a-z]:', 'CRITICAL', '格式化磁盘'),
            (r'shutdown', 'HIGH', '关机命令'),
            (r'reboot', 'MEDIUM', '重启命令'),
            (r'chmod\s+777', 'MEDIUM', '权限过宽'),
            (r'>\s+/dev/sda', 'CRITICAL', '覆盖磁盘'),
            (r'mkfs\.', 'CRITICAL', '格式化文件系统'),
            (r':(){\|:&\};:', 'HIGH', 'Fork炸弹'),
            (r'dd\s+if=.*of=/dev/', 'CRITICAL', '磁盘覆写'),
            (r'git\s+reset\s+--hard', 'HIGH', '强制重置Git'),
            (r'git\s+clean\s+-fd', 'HIGH', '强制清理未跟踪文件'),
            (r'npm\s+uninstall\s+-g', 'MEDIUM', '全局卸载包'),
            (r'pip\s+uninstall\s+-y', 'MEDIUM', '强制卸载Python包'),
            (r'apt-get\s+remove\s+--purge', 'MEDIUM', '彻底删除软件包'),
            (r'yum\s+remove', 'MEDIUM', '删除软件包'),
            (r'kubectl\s+delete\s+--all', 'HIGH', '删除所有Kubernetes资源'),
            (r'docker\s+rm\s+-f\s+\$\(docker', 'HIGH', '强制删除所有容器'),
            (r'truncate\s+-s\s+0', 'MEDIUM', '清空文件'),
            (r'curl.*\|\s*bash', 'HIGH', '远程代码执行')
        ]

        check_text = f"{task_description} {command or ''}"

        for pattern, level, reason in dangerous_patterns:
            if re.search(pattern, check_text, re.IGNORECASE):
                features.is_dangerous = True
                danger_level = DangerLevel[level]
                if not features.danger_level or danger_level.value > features.danger_level.value:
                    features.danger_level = danger_level
                features.danger_reasons.append(reason)

        return features
```

#### 5. 专家需求识别 (Expert Need Identification)

**功能**: 识别任务是否需要专家级别的精确操作。

**提取的特征**:
- `need_expert`: 是否需要专家操作
- `expert_reasons`: 需要专家的原因

**实现方式**:
```python
class TaskFeatureExtractor:
    def identify_expert_need(self, task_description: str, context: dict) -> ExpertFeature:
        """
        识别专家需求
        """
        features = ExpertFeature()

        expert_keywords = [
            ('精确', '需要精确的定位和修改'),
            ('特定位置', '需要在特定位置进行操作'),
            ('保持格式', '需要保持原有格式'),
            ('部分替换', '只替换部分内容'),
            ('条件修改', '根据条件选择性修改'),
            ('precise', '需要精确操作'),
            ('specific location', '需要在特定位置操作'),
            ('preserve format', '需要保持格式'),
            ('partial replacement', '只替换部分内容'),
            ('conditional modification', '根据条件修改')
        ]

        for keyword, reason in expert_keywords:
            if keyword in task_description.lower():
                features.need_expert = True
                features.expert_reasons.append(reason)

        return features
```

## 智能决策引擎

### 决策树规则

决策引擎基于以下6条规则进行优先级决策：

#### 规则1: 精确编辑规则 (_rule_expert_precise_edit)

**触发条件**: 任务需要专家级别的精确编辑

**决策逻辑**:
```python
def _rule_expert_precise_edit(self, features: TaskFeatures) -> Optional[DecisionResult]:
    """
    规则1: 如果任务需要精确编辑，推荐手动操作
    """
    if features.expert.need_expert:
        return DecisionResult(
            priority=Priority.MANUAL,
            confidence=0.95,
            reasons=[f"任务需要精确编辑: {', '.join(features.expert.expert_reasons)}"],
            suggestion="使用文件编辑工具进行精确修改"
        )
    return None
```

#### 规则2: 单文件操作规则 (_rule_single_file_operation)

**触发条件**: 任务涉及单个文件的读写或编辑操作

**决策逻辑**:
```python
def _rule_single_file_operation(self, features: TaskFeatures) -> Optional[DecisionResult]:
    """
    规则2: 如果是单文件操作，推荐手动操作
    """
    if (features.file.is_file_operation and
        features.file.operation_type in ['read', 'write', 'edit'] and
        features.file.file_count == 1):

        return DecisionResult(
            priority=Priority.MANUAL,
            confidence=0.9,
            reasons=["单文件操作"],
            suggestion=f"使用{'读取' if features.file.operation_type == 'read' else '编辑'}工具操作 {features.file.file_patterns[0]}"
        )
    return None
```

#### 规则3: 批量操作规则 (_rule_batch_operation)

**触发条件**: 任务涉及批量文件操作

**决策逻辑**:
```python
def _rule_batch_operation(self, features: TaskFeatures) -> Optional[DecisionResult]:
    """
    规则3: 如果是批量操作，根据情况决定优先级
    """
    if features.batch.is_batch:
        if features.batch.batch_size <= 5:
            # 小批量：仍可手动操作
            return DecisionResult(
                priority=Priority.MANUAL,
                confidence=0.85,
                reasons=[f"小批量操作 ({features.batch.batch_size}个文件)"],
                suggestion="逐个使用文件工具操作"
            )
        elif features.script.script_available and features.script.script_match_score > 0.8:
            # 大批量且有合适脚本：使用脚本
            return DecisionResult(
                priority=Priority.SCRIPT,
                confidence=0.9,
                reasons=[f"大批量操作 ({features.batch.batch_size}个文件)，有现成脚本"],
                suggestion=f"运行脚本: {features.script.script_path}"
            )
        else:
            # 大批量且无脚本：降级到命令
            return DecisionResult(
                priority=Priority.COMMAND,
                confidence=0.75,
                reasons=[f"大批量操作 ({features.batch.batch_size}个文件)，无合适脚本"],
                suggestion="使用命令行批量操作，需通过预演检查"
            )
    return None
```

#### 规则4: 脚本存在规则 (_rule_script_exists)

**触发条件**: 存在高度匹配的现有脚本

**决策逻辑**:
```python
def _rule_script_exists(self, features: TaskFeatures) -> Optional[DecisionResult]:
    """
    规则4: 如果有高度匹配的脚本，推荐使用脚本
    """
    if (features.script.script_available and
        features.script.script_match_score > 0.8 and
        not features.file.is_file_operation):

        return DecisionResult(
            priority=Priority.SCRIPT,
            confidence=0.92,
            reasons=[f"找到匹配脚本 ({features.script.script_match_score:.2%}匹配度)"],
            suggestion=f"运行脚本: {features.script.script_path}"
        )
    return None
```

#### 规则5: 复杂度规则 (_rule_complexity)

**触发条件**: 任务复杂度高

**决策逻辑**:
```python
def _rule_complexity(self, features: TaskFeatures) -> Optional[DecisionResult]:
    """
    规则5: 根据任务复杂度决定优先级
    """
    complexity = self._calculate_complexity(features)

    if complexity > 0.8:
        # 高复杂度：推荐脚本
        return DecisionResult(
            priority=Priority.SCRIPT,
            confidence=0.88,
            reasons=[f"高复杂度任务 ({complexity:.2%})"],
            suggestion="建议将任务拆分为子任务或编写脚本"
        )
    elif complexity > 0.5:
        # 中等复杂度：根据其他因素决定
        return None  # 让后续规则决定
    else:
        # 低复杂度：推荐手动操作
        return DecisionResult(
            priority=Priority.MANUAL,
            confidence=0.82,
            reasons=[f"低复杂度任务 ({complexity:.2%})"],
            suggestion="可直接使用文件工具操作"
        )
```

#### 规则6: 环境命令规则 (_rule_environment_command)

**触发条件**: 任务明确要求执行环境命令

**决策逻辑**:
```python
def _rule_environment_command(self, features: TaskFeatures) -> Optional[DecisionResult]:
    """
    规则6: 如果是环境命令，推荐命令操作（需预演）
    """
    env_commands = ['git', 'docker', 'npm', 'pip', 'cargo', 'make', 'cmake']

    for cmd in env_commands:
        if cmd in features.task_description.lower():
            if features.danger.is_dangerous and features.danger.danger_level >= DangerLevel.HIGH:
                return DecisionResult(
                    priority=Priority.COMMAND,
                    confidence=0.95,
                    reasons=[f"环境命令 ({cmd})，但具有危险性"],
                    suggestion="必须通过预演检查后才能执行"
                )
            else:
                return DecisionResult(
                    priority=Priority.COMMAND,
                    confidence=0.87,
                    reasons=[f"环境命令 ({cmd})"],
                    suggestion="通过预演检查后执行"
                )

    return None
```

### 核心API接口

#### decide() 方法

```python
class OperationPriorityController:
    @staticmethod
    def decide(task_context: dict) -> tuple[str, str]:
        """
        根据任务上下文决定操作优先级

        Args:
            task_context: 任务上下文，包含：
                - description: 任务描述
                - files: 涉及的文件列表（可选）
                - command: 要执行的命令（可选）
                - scripts_dir: 脚本目录（可选）

        Returns:
            tuple[str, str]: (优先级, 理由)
        """
        controller = OperationPriorityController()

        # 提取任务特征
        features = controller.extractor.extract_all(task_context)

        # 运行决策树
        result = controller._run_decision_tree(features)

        return (result.priority.value, '; '.join(result.reasons))
```

#### decide_full() 方法

```python
class OperationPriorityController:
    @staticmethod
    def decide_full(task_context: dict) -> FullDecisionResult:
        """
        完整的决策流程，返回详细信息

        Args:
            task_context: 任务上下文

        Returns:
            FullDecisionResult: 完整的决策结果
        """
        controller = OperationPriorityController()

        # 提取任务特征
        features = controller.extractor.extract_all(task_context)

        # 运行决策树
        decision = controller._run_decision_tree(features)

        # 如果是命令操作，执行预演检查
        preflight_result = None
        if decision.priority == Priority.COMMAND:
            preflight_result = controller.preflight_check(
                task_context.get('command', ''),
                task_context
            )

        return FullDecisionResult(
            decision=decision,
            features=features,
            preflight_result=preflight_result
        )
```

## 预演检查机制

### 功能概述

预演检查机制对命令操作进行事前分析，评估影响范围、风险等级，并创建回滚点。对于危险命令，直接拦截并拒绝执行。

### 检查项

#### 1. 影响范围分析 (Impact Scope Analysis)

**功能**: 分析命令可能影响的范围。

**分析维度**:
- 影响的文件数量
- 影响的目录层级
- 是否影响系统文件
- 是否影响网络资源

**实现方式**:
```python
class PreflightChecker:
    def analyze_impact_scope(self, command: str, context: dict) -> ImpactScope:
        """
        分析影响范围
        """
        impact = ImpactScope()

        # 分析文件影响
        file_patterns = [
            r'[\w\-./]+\.\w+',  # 文件路径
            r'\*\.?\w+',  # 通配符
            r'-r\s+(recursive)?',  # 递归标志
        ]

        for pattern in file_patterns:
            matches = re.findall(pattern, command)
            impact.affected_files.extend(matches)

        impact.affected_file_count = len(impact.affected_files)

        # 分析目录影响
        if '-r' in command or '--recursive' in command:
            impact.affects_subdirectories = True

        # 分析系统文件影响
        system_paths = ['/etc', '/usr', '/bin', '/sbin', 'C:\\Windows', 'C:\\System32']
        for path in system_paths:
            if path in command:
                impact.affects_system_files = True
                break

        return impact
```

#### 2. 风险评估 (Risk Assessment)

**功能**: 评估命令的风险等级。

**风险等级**:
- 🟢 LOW: 安全操作，无特殊风险
- 🟡 MEDIUM: 中等风险，需要注意
- 🔴 HIGH: 高风险，需要确认
- ⛔ CRITICAL: 极高风险，禁止执行

**实现方式**:
```python
class PreflightChecker:
    def assess_risk(self, command: str, impact: ImpactScope) -> RiskAssessment:
        """
        评估风险等级
        """
        risk = RiskAssessment()

        # 基于影响范围评分
        risk_score = 0

        if impact.affected_file_count > 100:
            risk_score += 3
        elif impact.affected_file_count > 10:
            risk_score += 2
        elif impact.affected_file_count > 1:
            risk_score += 1

        if impact.affects_subdirectories:
            risk_score += 2

        if impact.affects_system_files:
            risk_score += 4

        # 基于命令类型调整
        destructive_commands = ['rm', 'delete', 'drop', 'truncate', 'format']
        for cmd in destructive_commands:
            if cmd in command.lower():
                risk_score += 3
                break

        # 确定风险等级
        if risk_score >= 7:
            risk.level = RiskLevel.CRITICAL
            risk.blocked = True
            risk.block_reason = "风险过高，禁止执行"
        elif risk_score >= 5:
            risk.level = RiskLevel.HIGH
            risk.requires_confirmation = True
        elif risk_score >= 3:
            risk.level = RiskLevel.MEDIUM
            risk.requires_warning = True
        else:
            risk.level = RiskLevel.LOW

        risk.score = risk_score

        return risk
```

#### 3. 回滚点创建 (Rollback Point Creation)

**功能**: 为命令操作创建回滚点，以便在出现问题时恢复。

**回滚策略**:
- 文件操作: 创建备份副本
- Git操作: 记录当前commit hash
- 包操作: 记录当前版本号
- 配置操作: 导出当前配置

**实现方式**:
```python
class PreflightChecker:
    def create_rollback_point(self, command: str, context: dict) -> RollbackPoint:
        """
        创建回滚点
        """
        rollback = RollbackPoint()
        rollback.created_at = datetime.now()
        rollback.command = command

        # 文件备份
        if re.search(r'[\w\-./]+\.\w+', command):
            affected_files = re.findall(r'[\w\-./]+\.\w+', command)
            rollback.file_backups = {}
            for file_path in affected_files:
                if os.path.exists(file_path):
                    backup_path = f"{file_path}.backup.{int(time.time())}"
                    shutil.copy2(file_path, backup_path)
                    rollback.file_backups[file_path] = backup_path

        # Git状态记录
        if 'git' in command:
            try:
                result = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True)
                rollback.git_commit_hash = result.stdout.strip()
            except Exception as e:
                logger.warning(f"无法获取Git commit hash: {e}")

        # 包版本记录
        if 'npm' in command or 'pip' in command:
            try:
                if 'npm' in command:
                    result = subprocess.run(['npm', 'list', '--json'], capture_output=True, text=True)
                    rollback.package_versions = json.loads(result.stdout)
                elif 'pip' in command:
                    result = subprocess.run(['pip', 'freeze'], capture_output=True, text=True)
                    rollback.package_versions = result.stdout.split('\n')
            except Exception as e:
                logger.warning(f"无法获取包版本信息: {e}")

        return rollback
```

#### 4. 危险命令拦截 (Dangerous Command Interception)

**功能**: 拦截已知的危险命令，防止误操作。

**拦截规则**:

| 模式 | 风险等级 | 说明 |
|------|---------|------|
| `rm -rf /` | CRITICAL | 删除根目录 |
| `rm -rf *` | CRITICAL | 删除所有文件 |
| `DROP TABLE` | CRITICAL | 删除数据库表 |
| `FORMAT C:` | CRITICAL | 格式化磁盘 |
| `> /dev/sda` | CRITICAL | 覆盖磁盘 |
| `dd if= of=/dev/` | CRITICAL | 磁盘覆写 |
| `mkfs.` | CRITICAL | 格式化文件系统 |
| `:()\{: & \};:` | HIGH | Fork炸弹 |
| `shutdown` | HIGH | 关机命令 |
| `reboot` | MEDIUM | 重启命令 |
| `chmod 777` | MEDIUM | 权限过宽 |
| `git reset --hard` | HIGH | 强制重置Git |
| `git clean -fd` | HIGH | 强制清理 |
| `curl \| bash` | HIGH | 远程代码执行 |

**实现方式**:
```python
class PreflightChecker:
    DANGEROUS_COMMAND_PATTERNS = [
        (r'rm\s+-rf\s+/\s*', RiskLevel.CRITICAL, '禁止删除根目录'),
        (r'rm\s+-rf\s+\*\s*', RiskLevel.CRITICAL, '禁止删除所有文件'),
        (r'DROP\s+TABLE\s+\w+', RiskLevel.CRITICAL, '禁止删除数据库表'),
        (r'FORMAT\s+\w:', RiskLevel.CRITICAL, '禁止格式化磁盘'),
        (r'>\s*/dev/sda', RiskLevel.CRITICAL, '禁止覆盖磁盘'),
        (r'dd\s+if=\S+\s+of=/dev/', RiskLevel.CRITICAL, '禁止磁盘覆写'),
        (r'mkfs\.', RiskLevel.CRITICAL, '禁止格式化文件系统'),
        (r':\(\)\{\|:\s*&\s*\}\s*;', RiskLevel.HIGH, '检测到Fork炸弹'),
        (r'\bshutdown\b', RiskLevel.HIGH, '关机命令需要确认'),
        (r'\breboot\b', RiskLevel.MEDIUM, '重启命令需要确认'),
        (r'chmod\s+777\b', RiskLevel.MEDIUM, '权限设置过宽'),
        (r'git\s+reset\s+--hard', RiskLevel.HIGH, '强制重置Git历史'),
        (r'git\s+clean\s+-fd', RiskLevel.HIGH, '强制清理未跟踪文件'),
        (r'curl.*\|\s*(bash|sh)\b', RiskLevel.HIGH, '远程代码执行风险'),
        (r'truncate\s+-s\s+0', RiskLevel.MEDIUM, '清空文件操作'),
        (r'kubectl\s+delete\s+--all', RiskLevel.HIGH, '删除所有K8s资源'),
        (r'docker\s+rm\s+-f\s+\$\(', RiskLevel.HIGH, '强制删除所有容器'),
        (r'npm\s+uninstall\s+-g', RiskLevel.MEDIUM, '全局卸载操作'),
        (r'pip\s+uninstall\s+-y', RiskLevel.MEDIUM, '强制卸载操作'),
        (r'apt-get\s+remove\s+--purge', RiskLevel.MEDIUM, '彻底删除软件包'),
        (r'yum\s+remove\s+-y', RiskLevel.MEDIUM, '强制删除软件包'),
        (r'Set-Content.*-Path.*\$env:', RiskLevel.HIGH, 'PS环境变量覆写')
    ]

    def intercept_dangerous_command(self, command: str) -> InterceptionResult:
        """
        拦截危险命令
        """
        result = InterceptionResult(command=command)

        for pattern, level, reason in self.DANGEROUS_COMMAND_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                result.intercepted = True
                result.risk_level = level
                result.reason = reason

                if level == RiskLevel.CRITICAL:
                    result.blocked = True
                    result.action = 'BLOCK'
                elif level == RiskLevel.HIGH:
                    result.requires_confirmation = True
                    result.action = 'CONFIRM'
                else:
                    result.requires_warning = True
                    result.action = 'WARN'

                break

        return result
```

## 使用示例

### 示例1: 单文件编辑

```python
from operation_priority import OperationPriorityController

# 准备任务上下文
task_context = {
    'description': '修改config.yaml中的端口号从8080改为3000',
    'files': ['config.yaml']
}

# 决策优先级
priority, reason = OperationPriorityController.decide(task_context)

print(f"推荐优先级: {priority}")
print(f"理由: {reason}")
# 输出:
# 推荐优先级: manual
# 理由: 单文件操作
```

### 示例2: 批量文件处理

```python
# 准备任务上下文
task_context = {
    'description': '将所有.py文件中的print语句替换为logger',
    'files': ['src/main.py', 'src/utils.py', 'src/models.py', 'src/views.py',
              'src/controllers.py', 'src/services.py', 'src/middleware.py']
}

# 完整决策
result = OperationPriorityController.decide_full(task_context)

print(f"推荐优先级: {result.decision.priority.value}")
print(f"置信度: {result.decision.confidence:.2%}")
print(f"理由: {'; '.join(result.decision.reasons)}")
print(f"建议: {result.decision.suggestion}")

# 输出:
# 推荐优先级: manual
# 置信度: 85.00%
# 理由: 小批量操作 (7个文件)
# 建议: 逐个使用文件工具操作
```

### 示例3: 环境命令执行

```python
# 准备任务上下文
task_context = {
    'description': '提交代码到Git仓库',
    'command': 'git add . && git commit -m "feat: add user authentication"'
}

# 完整决策（包含预演检查）
result = OperationPriorityController.decide_full(task_context)

print(f"推荐优先级: {result.decision.priority.value}")
print(f"预演结果:")
if result.preflight_result:
    print(f"  风险等级: {result.preflight_result.risk.level.value}")
    print(f"  是否被拦截: {result.preflight_result.interception.blocked}")
    print(f"  回滚点: {result.preflight_result.rollback.git_commit_hash}")
```

### 示例4: 危险命令拦截

```python
# 准备任务上下文
task_context = {
    'description': '清理项目文件',
    'command': 'rm -rf ./node_modules'
}

# 完整决策
result = OperationPriorityController.decide_full(task_context)

print(f"推荐优先级: {result.decision.priority.value}")
print(f"预演结果:")
if result.preflight_result:
    interception = result.preflight_result.interception
    print(f"  是否被拦截: {interception.intercepted}")
    print(f"  风险等级: {interception.risk_level.value if interception.risk_level else 'None'}")
    print(f"  拦截原因: {interception.reason}")
    print(f"  处理动作: {interception.action}")
    print(f"  是否阻止: {interception.blocked}")
```

### 示例5: 安装依赖

```python
# 准备任务上下文
task_context = {
    'description': '安装lodash依赖',
    'command': 'npm install lodash@4.17.21'
}

# 完整决策
result = OperationPriorityController.decide_full(task_context)

print(f"推荐优先级: {result.decision.priority.value}")
print(f"预演结果:")
if result.preflight_result:
    print(f"  风险等级: {result.preflight_result.risk.level.value}")
    print(f"  影响文件数: {result.preflight_result.impact.affected_file_count}")
    print(f"  回滚点:")
    if result.preflight_result.rollback.package_versions:
        print(f"    包版本已记录")
```

## 配置参数

```yaml
operation_priority:
  # 决策引擎配置
  decision_engine:
    rules_enabled:
      - expert_precise_edit
      - single_file_operation
      - batch_operation
      - script_exists
      - complexity
      - environment_command

    confidence_threshold: 0.8  # 最低置信度阈值

  # 预演检查配置
  preflight_check:
    enabled: true
    auto_create_rollback: true
    require_confirmation_for:
      - HIGH
      - CRITICAL

  # 危险命令拦截配置
  dangerous_command_interception:
    enabled: true
    block_critical: true  # 阻止CRITICAL级别命令
    confirm_high: true   # HIGH级别需要确认
    warn_medium: true    # MEDIUM级别警告

  # 特征提取配置
  feature_extraction:
    batch_threshold: 5  # 超过此数量的文件视为批量操作
    script_match_threshold: 0.8  # 脚本匹配度阈值
```

## 最佳实践

### 1. 始终调用decide_full()获取完整信息

在生产环境中，始终使用 `decide_full()` 而不是简单的 `decide()`，以获取完整的决策信息和预演结果。

```python
# 推荐
result = OperationPriorityController.decide_full(task_context)
if result.preflight_result and result.preflight_result.interception.blocked:
    print("命令已被阻止")
else:
    # 执行操作
    pass

# 不推荐
priority, reason = OperationPriorityController.decide(task_context)
# 缺少预演信息
```

### 2. 处理预演结果

始终检查预演结果，特别是对于命令操作。

```python
result = OperationPriorityController.decide_full(task_context)

if result.decision.priority == Priority.COMMAND:
    if result.preflight_result:
        # 检查是否被拦截
        if result.preflight_result.interception.blocked:
            print(f"❌ 命令被阻止: {result.preflight_result.interception.reason}")
            return

        # 检查是否需要确认
        if result.preflight_result.interception.requires_confirmation:
            print(f"⚠️  需要确认: {result.preflight_result.interception.reason}")
            if not get_user_confirmation():
                return

        # 检查警告
        if result.preflight_result.interception.requires_warning:
            print(f"⚠️  警告: {result.preflight_result.interception.reason}")

        # 执行命令
        execute_command(task_context['command'], result.preflight_result.rollback)
```

### 3. 利用回滚点

在执行命令前确保创建了回滚点，并在出错时使用回滚点恢复。

```python
result = OperationPriorityController.decide_full(task_context)

if result.preflight_result and result.preflight_result.rollback:
    rollback = result.preflight_result.rollback

    try:
        # 执行命令
        output = execute_command(task_context['command'])

        # 检查执行结果
        if output.return_code != 0:
            raise ExecutionError(output.stderr)

    except Exception as e:
        print(f"❌ 执行失败: {e}")
        print("正在回滚...")

        # 使用回滚点恢复
        restore_from_rollback(rollback)
        print("✅ 已恢复到执行前的状态")
```

### 4. 自定义决策规则

可以根据项目需求添加自定义决策规则。

```python
class CustomOperationPriorityController(OperationPriorityController):
    def _custom_rule(self, features: TaskFeatures) -> Optional[DecisionResult]:
        """自定义规则: 对于测试相关任务，优先使用脚本"""
        test_keywords = ['test', '测试', 'pytest', 'jest', 'unittest']

        if any(kw in features.task_description.lower() for kw in test_keywords):
            if features.script.script_available:
                return DecisionResult(
                    priority=Priority.SCRIPT,
                    confidence=0.93,
                    reasons=["测试任务，有现成脚本"],
                    suggestion=f"运行测试脚本: {features.script.script_path}"
                )

        return None

    def _run_decision_tree(self, features: TaskFeatures) -> DecisionResult:
        """运行决策树（含自定义规则）"""
        # 先尝试自定义规则
        result = self._custom_rule(features)
        if result:
            return result

        # 再使用默认规则
        return super()._run_decision_tree(features)
```

### 5. 日志记录

记录所有决策过程，便于审计和调试。

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

result = OperationPriorityController.decide_full(task_context)

logger.info(f"任务: {task_context['description']}")
logger.info(f"推荐优先级: {result.decision.priority.value}")
logger.info(f"置信度: {result.decision.confidence:.2%}")
logger.info(f"理由: {'; '.join(result.decision.reasons)}")

if result.preflight_result:
    logger.info(f"风险等级: {result.preflight_result.risk.level.value}")
    if result.preflight_result.interception.intercepted:
        logger.warning(f"命令被{result.preflight_result.interception.action}: "
                       f"{result.preflight_result.interception.reason}")
```

## 与其他模块的集成

### 与四维防线的集成

四维防线可以使用操作优先级控制器来决定如何处理输出。

```python
from four_d_defense import FourDimensionalDefense
from operation_priority import OperationPriorityController

defense = FourDimensionalDefense()

# 获取操作优先级
priority, reason = OperationPriorityController.decide({
    'description': '生成用户认证模块代码',
    'files': ['src/auth/__init__.py', 'src/auth/models.py', 'src/auth/routes.py']
})

# 根据优先级调整防线严格程度
if priority == 'manual':
    config = DefenseConfig(strict_mode=True)  # 手动操作使用严格模式
elif priority == 'script':
    config = DefenseConfig(strict_mode=False)  # 脚本操作使用标准模式
else:
    config = DefenseConfig(strict_mode=False, allow_degradation=True)  # 命令操作允许降级

defense = FourDimensionalDefense(config)
result = defense.run_full_check(input_data)
```

### 与资源协调器的集成

资源协调器可以根据操作优先级分配不同的资源配额。

```python
from resource_coordinator import ResourceCoordinator, ResourceType, Priority

coordinator = ResourceCoordinator()

# 获取操作优先级
op_priority, _ = OperationPriorityController.decide(task_context)

# 根据优先级设置配额
if op_priority == 'manual':
    resource_priority = Priority.HIGH
elif op_priority == 'script':
    resource_priority = Priority.MEDIUM
else:
    resource_priority = Priority.LOW

# 注册任务时指定优先级
task_id = coordinator.schedule_task(
    task=Task(...),
    priority=resource_priority
)
```

### 与密钥管理系统的集成

对于涉及密钥的操作，操作优先级控制器可以与密钥管理系统协同工作。

```python
from secrets_manager import SecretsManager

# 检测是否涉及密钥操作
task_context = {
    'description': '更新API密钥配置',
    'command': 'echo $GITHUB_API_KEY >> .env'
}

result = OperationPriorityController.decide_full(task_context)

# 如果检测到密钥操作，使用密钥管理器
if any('key' in kw or 'secret' in kw or 'password' in kw
       for kw in result.features.task_description.lower().split()):
    secrets_manager = SecretsManager()
    secrets_manager.load()

    # 使用安全的密钥操作方式
    api_key = secrets_manager.get_required('GITHUB_API_KEY')

    # 更新.env文件（使用手动操作而非命令）
    update_env_file('GITHUB_API_KEY', api_key)
```

## 故障排查

### 问题1: 决策结果不符合预期

**症状**: 系统推荐的优先级与预期不符。

**排查步骤**:
1. 检查任务描述是否清晰准确
2. 查看 `decide_full()` 返回的特征提取结果
3. 检查是否有自定义规则干扰
4. 查看决策日志了解具体决策过程

**解决方案**:
```python
# 查看完整决策信息
result = OperationPriorityController.decide_full(task_context)

print("=== 任务特征 ===")
print(f"文件操作: {result.features.file.is_file_operation}")
print(f"文件数量: {result.features.file.file_count}")
print(f"批量操作: {result.features.batch.is_batch}")
print(f"脚本可用: {result.features.script.script_available}")
print(f"危险操作: {result.features.danger.is_dangerous}")

print("\n=== 决策过程 ===")
print(f"优先级: {result.decision.priority.value}")
print(f"置信度: {result.decision.confidence:.2%}")
print(f"理由: {'; '.join(result.decision.reasons)}")
print(f"建议: {result.decision.suggestion}")
```

### 问题2: 预演检查频繁失败

**症状**: 命令操作频繁被预演检查阻止。

**排查步骤**:
1. 检查命令是否符合危险模式
2. 检查影响范围分析是否过于保守
3. 检查风险评估阈值是否过低

**解决方案**:
```python
# 调整预演检查配置
config = PreflightConfig(
    enabled=True,
    auto_create_rollback=True,
    risk_assessment=RiskAssessmentConfig(
        critical_threshold=9,  # 从7提高到9
        high_threshold=7,      # 从5提高到7
        medium_threshold=4     # 从3提高到4
    )
)

controller = OperationPriorityController(config=config)
```

### 问题3: 性能问题

**症状**: 决策过程耗时过长。

**排查步骤**:
1. 检查脚本扫描范围是否过大
2. 检查特征提取是否有冗余计算
3. 检查是否有不必要的预演检查

**解决方案**:
```python
# 优化配置
config = OperationPriorityConfig(
    feature_extraction=FeatureExtractionConfig(
        scan_scripts=False,  # 禁用脚本扫描
        calculate_complexity=False  # 禁用复杂度计算
    ),
    preflight_check=PreflightConfig(
        enabled=False  # 对于非命令操作禁用预演
    )
)

controller = OperationPriorityController(config=config)
```

## 总结

操作优先级架构是Sanliu v4.0的核心决策系统，通过Agent-First理念、智能决策树、任务特征提取器和预演检查机制，确保每个任务都使用最优的操作方式。该系统具有以下特点:

- **智能化**: 基于多维度特征自动推荐最优优先级
- **安全性**: 内置危险命令拦截和预演检查机制
- **灵活性**: 支持自定义决策规则和配置参数
- **可追溯性**: 完整记录决策过程和预演结果
- **可扩展性**: 易于添加新的特征维度和决策规则

通过合理配置和使用操作优先级架构，可以显著提高开发效率、降低操作风险、增强系统安全性。
