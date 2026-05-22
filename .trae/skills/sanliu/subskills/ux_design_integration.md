# UI/UX 设计协同集成 (UX Design Integration)

## 概述

UI/UX设计协同集成层是 Sanliu v4.0 与 `ui-ux-pro-max` 技能的深度连接桥梁，使 Sanliu 能够在设计驱动的开发流程中获取专业的设计系统、UX规则和代码验证能力。该系统通过设计系统生成、规则查询、UI代码验证和交付前检查清单等子系统，确保前端开发符合最佳用户体验实践。

### 核心理念

- **设计驱动**: 以设计系统为指导进行前端开发
- **规则约束**: 遵循99+条UX设计规则
- **代码验证**: 自动对照UX指南检查代码质量
- **交付保障**: 通过21项检查清单确保交付质量
- **专业协同**: 与ui-ux-pro-max技能深度集成

### 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                  UI/UX 设计协同集成架构                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │        设计系统生成 (Design System Generation)             │  │
│  │  ├─ 调用 ui-ux-pro-max --design-system                  │  │
│  │  ├─ 产品类型识别 (SaaS/Mobile/E-commerce/Admin)           │  │
│  │  ├─ 设计模式推荐                                         │  │
│  │  ├─ 色彩系统生成                                         │  │
│  │  ├─ 字体排版系统                                         │  │
│  │  └─ 视觉效果规范                                         │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │          UX规则查询 (UX Rule Query)                        │  │
│  │  ├─ 10个领域分类                                          │  │
│  │  ├─ 关键词搜索                                            │  │
│  │  ├─ 规则详情获取                                          │  │
│  │  └─ 最佳实践推荐                                          │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │         UI代码验证 (UI Code Validation)                    │  │
│  │  ├─ 7个验证维度                                           │  │
│  │  ├─ 对比度检查                                             │  │
│  │  ├─ 间距一致性检查                                         │  │
│  │  ├─ 交互状态检查                                           │  │
│  │  ├─ 可访问性检查                                           │  │
│  │  └─ 响应式设计检查                                         │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │      交付前检查清单 (Pre-Delivery Checklist)               │  │
│  │  ├─ 视觉质量 (6项)                                        │  │
│  │  ├─ 交互体验 (5项)                                        │  │
│  │  ├─ 暗色模式 (4项)                                        │  │
│  │  ├─ 布局结构 (3项)                                        │  │
│  │  └─ 无障碍访问 (3项)                                      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │          ui-ux-pro-max 子进程调用                          │  │
│  │  ├─ --design-system: 设计系统生成                         │  │
│  │  ├--domain <domain> <query>: 规则查询                     │  │
│  │  ├--validate <file>: 代码验证                             │  │
│  │  └--checklist: 检查清单生成                                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 设计系统生成

### 功能概述

设计系统生成功能通过调用 `ui-ux-pro-max` 技能，根据产品类型和关键词生成完整的设计系统规范。

### 支持的产品类型

| 类型 | 说明 | 典型特征 |
|------|------|---------|
| SaaS | 软件即服务 | 仪表板、数据表格、图表 |
| Mobile | 移动应用 | 手势导航、触摸目标、底部导航 |
| E-commerce | 电商平台 | 商品展示、购物车、支付流程 |
| Admin | 管理后台 | 表单密集、CRUD操作、权限控制 |
| Marketing | 营销网站 | 视觉冲击、转化优化、A/B测试 |
| Dashboard | 数据仪表板 | 实时数据、可视化、KPI卡片 |
| Social | 社交网络 | 信息流、用户互动、实时通知 |
| Enterprise | 企业应用 | 复杂工作流、多角色、合规性 |

### 核心方法

#### generate_design_system() 方法

```python
class UXIntegration:
    def generate_design_system(
        self,
        product_type: str,
        keywords: str = '',
        context: dict = None
    ) -> DesignSystem:
        """
        生成设计系统

        Args:
            product_type: 产品类型 (saas/mobile/ecommerce/admin/marketing/dashboard/social/enterprise)
            keywords: 额外关键词（逗号分隔）
            context: 上下文信息

        Returns:
            DesignSystem: 设计系统对象
        """
        context = context or {}

        # 构建命令参数
        cmd_args = [
            '--design-system',
            '--type', product_type
        ]

        if keywords:
            cmd_args.extend(['--keywords', keywords])

        # 调用ui-ux-pro-max
        result = self._call_ui_ux_pro_max(cmd_args)

        # 解析结果
        design_system = self._parse_design_system(result)

        return design_system

    def _call_ui_ux_pro_max(self, args: list) -> subprocess.CompletedProcess:
        """
        调用ui-ux-pro-max子进程
        """
        cmd = ['python', '-m', 'ui-ux-pro-max'] + args

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.ui_ux_pro_max_path
            )

            if result.returncode != 0:
                raise UXIntegrationError(f"ui-ux-pro-max执行失败: {result.stderr}")

            return result

        except subprocess.TimeoutExpired:
            raise UXIntegrationError("ui-ux-pro-max执行超时")
        except FileNotFoundError:
            raise UXIntegrationError("ui-ux-pro-max未找到")

    def _parse_design_system(self, output: str) -> DesignSystem:
        """解析设计系统输出"""
        import json

        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            data = self._parse_markdown_design_system(output)

        return DesignSystem(
            pattern=data.get('pattern', {}),
            style=data.get('style', {}),
            colors=ColorPalette(**data.get('colors', {})),
            typography=TypographySystem(**data.get('typography', {})),
            effects=data.get('effects', {}),
            anti_patterns=data.get('anti_patterns', []),
            components=data.get('components', [])
        )
```

### DesignSystem 数据类

```python
@dataclass
class DesignSystem:
    """设计系统"""
    pattern: dict              # 设计模式
    style: dict                # 风格指南
    colors: ColorPalette       # 色彩系统
    typography: TypographySystem  # 字体排版系统
    effects: dict              # 视觉效果
    anti_patterns: List[str]   # 反模式列表
    components: List[dict]     # 组件库

@dataclass
class ColorPalette:
    """色彩系统"""
    primary: str               # 主色
    secondary: str             # 辅助色
    accent: str                # 强调色
    background: str            # 背景色
    surface: str               # 表面色
    error: str                 # 错误色
    warning: str               # 警告色
    success: str               # 成功色
    info: str                  # 信息色
    text_primary: str          # 主文本色
    text_secondary: str        # 次文本色
    dark_mode: Optional[dict]  # 暗色模式色彩

@dataclass
class TypographySystem:
    """字体排版系统"""
    font_family: str           # 字体族
    font_size_base: int        # 基础字号
    heading_sizes: dict        # 标题字号
    line_height_base: float    # 基础行高
    font_weights: dict         # 字重
    letter_spacing: dict       # 字间距
```

## UX规则查询

### 功能概述

UX规则查询功能提供对99+条UX设计规则的按领域搜索和详情获取。

### 支持的领域 (10个)

| 领域 | 说明 | 规则数量 |
|------|------|---------|
| accessibility | 无障碍访问 | 15+ |
| touch_targets | 触摸目标 | 8+ |
| animation | 动画效果 | 12+ |
| forms | 表单设计 | 15+ |
| navigation | 导航设计 | 10+ |
| color | 色彩使用 | 10+ |
| spacing | 间距规范 | 8+ |
| typography | 排版规范 | 10+ |
| responsive | 响应式设计 | 8+ |
| interaction | 交互设计 | 12+ |

### 核心方法

#### search_ux_rules() 方法

```python
class UXIntegration:
    def search_ux_rules(
        self,
        domain: str,
        query: str = ''
    ) -> List[UXRule]:
        """
        搜索UX规则

        Args:
            domain: 领域 (accessibility/touch_targets/animation/forms/navigation/color/spacing/typography/responsive/interaction)
            query: 搜索关键词

        Returns:
            List[UXRule]: 匹配的规则列表
        """
        # 调用ui-ux-pro-max
        cmd_args = ['--domain', domain]
        if query:
            cmd_args.extend([query])

        result = self._call_ui_ux_pro_max(cmd_args)

        # 解析结果
        rules = self._parse_ux_rules(result)

        return rules

    def get_rule_detail(self, rule_id: str) -> UXRule:
        """
        获取规则详情

        Args:
            rule_id: 规则ID

        Returns:
            UXRule: 规则详情
        """
        cmd_args = ['--rule-detail', rule_id]

        result = self._call_ui_ux_pro_max(cmd_args)

        return self._parse_single_rule(result)
```

### UXRule 数据类

```python
@dataclass
class UXRule:
    """UX规则"""
    id: str                    # 规则ID
    title: str                 # 规则标题
    domain: str                # 所属领域
    description: str           # 规则描述
    rationale: str             # 设计理由
    implementation: str        # 实现建议
    examples: List[str]        # 示例
    anti_examples: List[str]   # 反例
    wcag_level: Optional[str]  # WCAG级别 (如有)
    priority: str              # 优先级 (must/should/nice_to_have)
    references: List[str]      # 参考资料
```

## UI代码验证

### 功能概述

UI代码验证功能自动对照UX设计规则检查前端代码，从7个维度评估代码质量。

### 验证维度 (7个)

#### 1. 对比度检查 (Contrast Check)

**检查内容**:
- 文本与背景的对比度是否符合WCAG AA标准 (4.5:1)
- 大文本对比度是否符合WCAG AAA标准 (7:1)
- 焦点状态对比度是否足够

**实现方式**:
```python
class UXIntegration:
    def _validate_contrast(self, code: str) -> ValidationResult:
        """验证颜色对比度"""
        issues = []

        # 提取颜色组合
        color_pairs = self._extract_color_pairs(code)

        for fg, bg in color_pairs:
            ratio = self._calculate_contrast_ratio(fg, bg)

            if ratio < 4.5:
                issues.append(ValidationIssue(
                    dimension='contrast',
                    severity='error',
                    message=f'对比度不足: {fg} on {bg} = {ratio:.2f}:1 (需要≥4.5:1)',
                    suggestion='增加前景色与背景色的亮度差异'
                ))
            elif ratio < 7.0:
                issues.append(ValidationIssue(
                    dimension='contrast',
                    severity='warning',
                    message=f'对比度偏低: {fg} on {bg} = {ratio:.2f}:1 (建议≥7:1)',
                    suggestion='考虑提高对比度以增强可读性'
                ))

        return ValidationResult(dimension='contrast', issues=issues)
```

#### 2. 间距一致性检查 (Spacing Consistency)

**检查内容**:
- 内边距(padding)是否使用一致的值
- 外边距(margin)是否遵循间距系统
- 组件间距离是否统一

#### 3. 交互状态检查 (Interaction States)

**检查内容**:
- 是否定义了hover状态
- 是否定义了focus状态
- 是否定义了active/disabled状态
- 过渡动画是否合理

#### 4. 可访问性检查 (Accessibility)

**检查内容**:
- 图片是否有alt属性
- 表单元素是否有关联标签
- ARIA属性使用是否正确
- 键盘导航是否支持

#### 5. 响应式断点检查 (Responsive Breakpoints)

**检查内容**:
- 是否定义了响应式断点
- 断点值是否合理
- 移动端优先策略是否采用

#### 6. 字体排版检查 (Typography)

**检查内容**:
- 字号是否遵循层级体系
- 行高是否合适
- 字重使用是否一致
- 字间距是否正确

#### 7. 组件一致性检查 (Component Consistency)

**检查内容**:
- 相同类型的组件样式是否一致
- 命名规范是否统一
- 变量使用是否合理

### 核心方法

#### validate_ui_code() 方法

```python
class UXIntegration:
    def validate_ui_code(
        self,
        code: str,
        stack: str = 'react'
    ) -> ValidationResult:
        """
        验证UI代码

        Args:
            code: 要验证的代码
            stack: 技术栈 (react/vue/angular/html/css)

        Returns:
            ValidationResult: 验证结果
        """
        all_issues = []

        # 7个维度的验证
        validators = [
            ('contrast', self._validate_contrast),
            ('spacing', self._validate_spacing),
            ('interaction_states', self._validate_interaction_states),
            ('accessibility', self._validate_accessibility),
            ('responsive', self._validate_responsive),
            ('typography', self._validate_typography),
            ('component_consistency', self._validate_component_consistency)
        ]

        for dimension, validator in validators:
            try:
                result = validator(code)
                all_issues.extend(result.issues)
            except Exception as e:
                logger.warning(f"验证{dimension}时出错: {e}")

        # 计算总分
        total_checks = len(validators)
        passed_checks = sum(1 for d, v in validators if not any(i.severity == 'error' for i in v(code).issues))

        score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0

        return ValidationResult(
            overall_score=score,
            dimensions={d: v(code) for d, v in validators},
            issues=all_issues,
            passed=len([i for i in all_issues if i.severity != 'error']),
            failed=len([i for i in all_issues if i.severity == 'error'])
        )
```

## 交付前检查清单

### 功能概述

交付前检查清单提供21项检查项，覆盖视觉质量、交互体验、暗色模式、布局结构和无障碍访问5个方面。

### 检查项列表 (21项)

#### 视觉质量 (6项)

| ID | 检查项 | 描述 | 优先级 |
|----|--------|------|--------|
| V1 | 色彩一致性 | 主色调、辅助色、强调色是否在整个界面中保持一致 | MUST |
| V2 | 圆角统一 | 圆角半径是否遵循设计系统的规范 | SHOULD |
| V3 | 阴影层级 | 阴影效果是否体现正确的层级关系 | SHOULD |
| V4 | 图标风格 | 图标风格（线性/填充）是否统一 | MUST |
| V5 | 空状态设计 | 所有空状态是否有友好的提示和引导 | SHOULD |
| V6 | 加载状态 | 异步操作的加载状态是否明确 | MUST |

#### 交互体验 (5项)

| ID | 检查项 | 描述 | 优先级 |
|----|--------|------|--------|
| I1 | Hover反馈 | 可点击元素是否有明确的hover反馈 | MUST |
| I2 | Focus可见 | 键盘焦点是否清晰可见 | MUST |
| I3 | 点击区域 | 最小触摸目标是否达到44x44px | MUST |
| I4 | 过渡动画 | 状态切换是否有平滑过渡 | SHOULD |
| I5 | 错误反馈 | 表单错误信息是否清晰且有帮助 | MUST |

#### 暗色模式 (4项)

| ID | 检查项 | 描述 | 优先级 |
|----|--------|------|--------|
| D1 | 色彩适配 | 暗色模式下所有颜色是否适配 | MUST |
| D2 | 对比度保持 | 暗色模式的对比度是否达标 | MUST |
| D3 | 图片处理 | 图片在暗色模式下是否正确显示 | SHOULD |
| D4 | 切换流畅 | 明暗模式切换是否无闪烁 | SHOULD |

#### 布局结构 (3项)

| ID | 检查项 | 描述 | 优先级 |
|----|--------|------|--------|
| L1 | 栅格系统 | 布局是否基于栅格系统 | SHOULD |
| L2 | 内容层次 | 信息层次是否清晰 | MUST |
| L3 | 响应式适配 | 不同屏幕尺寸下布局是否合理 | MUST |

#### 无障碍访问 (3项)

| ID | 检查项 | 描述 | 优先级 |
|----|--------|------|--------|
| A1 | 屏幕阅读器 | 屏幕阅读器能否正确朗读所有内容 | MUST |
| A2 | 键盘操作 | 所有功能是否可通过键盘完成 | MUST |
| A3 | 色盲友好 | 不依赖颜色传达信息 | SHOULD |

### 核心方法

#### get_pre_delivery_checklist() 方法

```python
class UXIntegration:
    def get_pre_delivery_checklist(
        self,
        project_type: str = 'web'
    ) -> List[CheckItem]:
        """
        获取交付前检查清单

        Args:
            project_type: 项目类型 (web/mobile/desktop)

        Returns:
            List[CheckItem]: 检查项列表
        """
        checklist = []

        # 视觉质量检查项
        visual_items = [
            CheckItem(id='V1', category='visual', name='色彩一致性',
                      description='主色调、辅助色、强调色是否在整个界面中保持一致',
                      priority='MUST'),
            CheckItem(id='V2', category='visual', name='圆角统一',
                      description='圆角半径是否遵循设计系统的规范',
                      priority='SHOULD'),
            CheckItem(id='V3', category='visual', name='阴影层级',
                      description='阴影效果是否体现正确的层级关系',
                      priority='SHOULD'),
            CheckItem(id='V4', category='visual', name='图标风格',
                      description='图标风格（线性/填充）是否统一',
                      priority='MUST'),
            CheckItem(id='V5', category='visual', name='空状态设计',
                      description='所有空状态是否有友好的提示和引导',
                      priority='SHOULD'),
            CheckItem(id='V6', category='visual', name='加载状态',
                      description='异步操作的加载状态是否明确',
                      priority='MUST')
        ]
        checklist.extend(visual_items)

        # 交互体验检查项
        interaction_items = [
            CheckItem(id='I1', category='interaction', name='Hover反馈',
                      description='可点击元素是否有明确的hover反馈',
                      priority='MUST'),
            CheckItem(id='I2', category='interaction', name='Focus可见',
                      description='键盘焦点是否清晰可见',
                      priority='MUST'),
            CheckItem(id='I3', category='interaction', name='点击区域',
                      description='最小触摸目标是否达到44x44px',
                      priority='MUST'),
            CheckItem(id='I4', category='interaction', name='过渡动画',
                      description='状态切换是否有平滑过渡',
                      priority='SHOULD'),
            CheckItem(id='I5', category='interaction', name='错误反馈',
                      description='表单错误信息是否清晰且有帮助',
                      priority='MUST')
        ]
        checklist.extend(interaction_items)

        # ... 其他类别检查项

        return checklist

    def run_checklist(
        self,
        code: str,
        project_type: str = 'web'
    ) -> ChecklistResult:
        """
        运行检查清单

        Args:
            code: 要检查的代码
            project_type: 项目类型

        Returns:
            ChecklistResult: 检查结果
        """
        checklist = self.get_pre_delivery_checklist(project_type)
        results = []

        for item in checklist:
            # 执行检查
            check_result = self._execute_check(item, code)
            results.append(CheckItemResult(
                item=item,
                passed=check_result.passed,
                details=check_result.details,
                suggestions=check_result.suggestions
            ))

        passed_count = sum(1 for r in results if r.passed)
        total_count = len(results)
        score = (passed_count / total_count) * 100 if total_count > 0 else 0

        return ChecklistResult(
            total_items=total_count,
            passed_items=passed_count,
            failed_items=total_count - passed_count,
            score=score,
            items=results
        )
```

## 使用示例

### 示例1: 生成设计系统

```python
from integration.ux_integration import UXIntegration

# 初始化
ux = UXIntegration()

# 生成SaaS产品设计系统
design_system = ux.generate_design_system(
    product_type='saas',
    keywords='dashboard,data-dense,real-time,analytics'
)

print(f"=== 设计系统 ===")
print(f"主色: {design_system.colors.primary}")
print(f"辅助色: {design_system.colors.secondary}")
print(f"字体族: {design_system.typography.font_family}")
print(f"基础字号: {design_system.typography.font_size_base}px")
```

### 示例2: 查询UX规则

```python
# 查询无障碍相关规则
rules = ux.search_ux_rules(domain='accessibility', query='keyboard')

print(f"找到 {len(rules)} 条规则:")
for rule in rules[:5]:
    print(f"\n[{rule.id}] {rule.title}")
    print(f"  领域: {rule.domain}")
    print(f"  优先级: {rule.priority}")
    print(f"  描述: {rule.description[:100]}...")
```

### 示例3: 验证UI代码

```python
# 验证React组件代码
code = '''
const Button = ({ children, variant = 'primary' }) => (
  <button className={`btn btn-${variant}`}>
    {children}
  </button>
);
'''

result = ux.validate_ui_code(code, stack='react')

print(f"=== UI代码验证结果 ===")
print(f"总分: {result.overall_score:.1f}/100")
print(f"通过: {result.passed} 项")
print(f"失败: {result.failed} 项")

if result.issues:
    print("\n问题列表:")
    for issue in result.issues[:10]:
        icon = "❌" if issue.severity == 'error' else "⚠️"
        print(f"{icon} [{issue.dimension}] {issue.message}")
```

### 示例4: 运行交付前检查清单

```python
# 运行检查清单
checklist_result = ux.run_checklist(code, project_type='web')

print(f"=== 交付前检查清单 ===")
print(f"总项数: {checklist_result.total_items}")
print(f"通过: {checklist_result.passed_items}")
print(f"失败: {checklist_result.failed_items}")
print(f"得分: {checklist_result.score:.1f}%")

print("\n失败的检查项:")
for item_result in checklist_result.items:
    if not item_result.passed:
        print(f"  ❌ [{item_result.item.id}] {item_result.item.name}")
        print(f"     {item_result.item.description}")
        if item_result.suggestions:
            print(f"     建议: {item_result.suggestions[0]}")
```

### 示例5: 完整的前端开发流程

```python
# 1. 生成设计系统
design_system = ux.generate_design_system(
    product_type='admin',
    keywords='dashboard,form-heavy,permission-based'
)

# 2. 查询特定领域的规则
form_rules = ux.search_ux_rules(domain='forms')
print(f"表单设计规则: {len(form_rules)} 条")

# 3. 编写代码
code = generate_component_code(design_system, form_rules)

# 4. 验证代码
validation_result = ux.validate_ui_code(code, stack='react')

if validation_result.overall_score >= 80:
    print("✅ 代码质量良好")
else:
    print("⚠️  需要改进:")
    for issue in validation_result.issues:
        print(f"  - {issue.message}")

# 5. 运行交付前检查
checklist_result = ux.run_checklist(code)

if checklist_result.score >= 90:
    print("✅ 可以交付")
else:
    print("⚠️  还需要完善一些细节")
```

## 配置参数

```yaml
ux_integration:
  # ui-ux-pro-max配置
  ui_ux_pro_max_path: ".trae/skills/ui-ux-pro-max"
  enabled: true
  fallback_enabled: true  # 当ui-ux-pro-max不可用时使用内置规则

  # 设计系统配置
  design_system:
    cache_enabled: true
    cache_ttl: 3600  # 1小时缓存
    default_product_type: "saas"

  # 规则查询配置
  rules_query:
    max_results: 20
    cache_rules: true

  # 代码验证配置
  validation:
    enabled: true
    dimensions:
      contrast: true
      spacing: true
      interaction_states: true
      accessibility: true
      responsive: true
      typography: true
      component_consistency: true
    strictness: "standard"  # relaxed/standard/strict

  # 检查清单配置
  checklist:
    enabled: true
    categories:
      - visual
      - interaction
      - dark_mode
      - layout
      - accessibility
    pass_threshold: 80  # 得分超过此阈值视为通过
```

## 最佳实践

### 1. 在项目初始化时生成设计系统

在新项目开始时，先生成设计系统作为开发基础。

```python
from integration.ux_integration import UXIntegration

ux = UXIntegration()

# 生成设计系统
ds = ux.generate_design_system(product_type='saas')

# 导出为CSS变量或Design Tokens
export_css_variables(ds, 'src/styles/design-tokens.css')
export_tailwind_config(ds, 'tailwind.config.js')
```

### 2. 在代码审查时运行验证

将UI代码验证集成到代码审查流程中。

```python
# 在四维防线第3层中使用
from four_d_defense import RuleValidationLayer

class RuleValidationLayer:
    def validate_ui_output(self, output: str):
        """验证UI输出"""
        ux = UXIntegration()
        result = ux.validate_ui_code(output)

        if result.overall_score < 70:
            return LayerResult(
                status=LayerStatus.REJECTED,
                metadata={'reason': f'UI代码评分过低: {result.overall_score}'}
            )

        return LayerResult(status=LayerStatus.PASSED, metadata=result)
```

### 3. 在交付前运行完整检查清单

在每次发布前运行完整的交付前检查清单。

```python
def pre_release_check():
    """发布前检查"""
    ux = UXIntegration()

    # 扫描所有组件文件
    component_files = glob.glob('src/components/**/*.tsx', recursive=True)

    all_passed = True
    for file_path in component_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        result = ux.run_checklist(code)

        if result.score < 90:
            all_passed = False
            print(f"⚠️  {file_path}: {result.score:.1f}%")

    if all_passed:
        print("✅ 所有组件通过检查，可以发布")
    else:
        print("❌ 存在问题，请修复后重新检查")
```

### 4. 利用暗色模式支持

确保设计系统和代码都支持暗色模式。

```python
# 生成包含暗色模式的设计系统
ds = ux.generate_design_system(
    product_type='saas',
    keywords='dark-mode,theme-switching'
)

# 验证暗色模式
dark_mode_result = ux.run_checklist(code, project_type='web_dark')
print(f"暗色模式得分: {dark_mode_result.score:.1f}%")
```

### 5. 定期更新设计规则

定期同步最新的UX设计规则。

```python
import time

while True:
    # 清除缓存
    ux.clear_cache()

    # 重新扫描规则
    rules = ux.search_ux_rules(domain='all')
    print(f"已更新 {len(rules)} 条UX规则")

    # 等待下次更新
    time.sleep(86400)  # 24小时
```

## 与其他模块的集成

### 与Agency Bridge的集成

可以通过Agency Bridge调用 `design-ui-ux-designer` Agent 进行更深入的设计评审。

```python
from integration.agency_bridge import AgencyBridge

bridge = AgencyBridge()
ux = UXIntegration()

# 先进行基本验证
basic_result = ux.validate_ui_code(code)

# 如果发现问题，调用专业Agent深度分析
if basic_result.overall_score < 80:
    agent_result = bridge.invoke_agent_sync(
        agent_id='design-ui-ux-designer',
        task=f'审查以下代码的UX质量问题:\n{code}',
        context={'issues': [i.message for i in basic_result.issues]}
    )

    print("专业Agent建议:")
    print(agent_result.output)
```

### 与四维防线的集成

四维防线可以将UI/UX验证作为第3层的一部分。

```python
from four_d_defense import FourDimensionalDefense

defense = FourDimensionalDefense()

# 在RuleValidationLayer中添加UX验证
input_data.metadata['ux_validation'] = {
    'enabled': True,
    'stack': 'react',
    'strictness': 'strict'
}

result = defense.run_full_check(input_data)
```

## 故障排查

### 问题1: ui-ux-pro-max不可用

**症状**: 调用ui-ux-pro-max时返回错误。

**解决方案**:
```python
# 启用内置fallback规则
ux = UXIntegration(config={
    'fallback_enabled': True,
    'ui_ux_pro_max_path': '.trae/skills/ui-ux-pro-max'
})

# 使用内置规则
rules = ux.search_ux_rules_fallback(domain='accessibility')
```

### 问题2: 验证结果不准确

**症状**: 验证结果与实际不符。

**排查步骤**:
1. 检查代码格式是否正确解析
2. 检查技术栈参数是否正确
3. 检查是否有自定义CSS变量未被识别

**解决方案**:
```python
# 提供更多上下文
result = ux.validate_ui_code(
    code,
    stack='react',
    context={
        'css_variables': {'--primary': '#3B82F6'},
        'component_library': 'shadcn/ui',
        'framework': 'Next.js'
    }
)
```

### 问题3: 性能问题

**症状**: 大量文件验证耗时过长。

**解决方案**:
```python
# 并行验证
from concurrent.futures import ThreadPoolExecutor

def validate_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
    return ux.validate_ui_code(code), file_path

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(validate_file, f) for f in component_files]
    results = [f.result() for f in futures]
```

## 总结

UI/UX设计协同集成层是Sanliu v4.0与ui-ux-pro-max技能的深度连接桥梁，通过设计系统生成、UX规则查询、UI代码验证和交付前检查清单等子系统，确保前端开发符合最佳用户体验实践。该系统具有以下特点:

- **专业性**: 基于99+条经过验证的UX设计规则
- **全面性**: 覆盖设计、开发、验证、交付全流程
- **自动化**: 自动化代码验证和检查清单执行
- **灵活性**: 支持多种技术栈和产品类型
- **可扩展性**: 易于添加新的验证规则和检查项

通过合理配置和使用UI/UX集成层，可以显著提升前端产品的用户体验质量和开发效率。
