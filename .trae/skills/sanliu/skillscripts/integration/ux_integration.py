#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI/UX 设计协同集成层

提供与 ui-ux-pro-max 技能的深度集成，包括设计系统生成、UX 规则查询、
UI 代码验证和交付前检查清单等功能。
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


# ============================================================
# 数据类定义
# ============================================================


@dataclass
class ColorPalette:
    """色彩方案数据结构"""

    primary: str = ""
    secondary: str = ""
    accent: str = ""
    background: str = ""
    surface: str = ""
    error: str = ""
    success: str = ""
    warning: str = ""
    text_primary: str = ""
    text_secondary: str = ""
    border: str = ""
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class TypographySystem:
    """字体方案数据结构"""

    font_family: str = ""
    heading_font: str = ""
    body_font: str = ""
    mono_font: str = ""
    base_size: int = 16
    scale_ratio: float = 1.25
    line_height_base: float = 1.5
    heading_sizes: dict[str, int] = field(default_factory=dict)
    weight_regular: int = 400
    weight_medium: int = 500
    weight_bold: int = 700
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class DesignSystem:
    """完整的设计系统数据对象"""

    pattern: str = ""
    style: str = ""
    colors: ColorPalette = field(default_factory=ColorPalette)
    typography: TypographySystem = field(default_factory=TypographySystem)
    effects: dict[str, Any] = field(default_factory=dict)
    anti_patterns: list[str] = field(default_factory=list)
    raw_output: str = ""


class RuleCategory(Enum):
    """UX 规则分类枚举"""

    ACCESSIBILITY = "accessibility"
    TOUCH = "touch"
    ANIMATION = "animation"
    FORMS = "forms"
    NAVIGATION = "navigation"
    CHART = "chart"
    TYPOGRAPHY = "typography"
    COLOR = "color"
    LAYOUT = "layout"
    PERFORMANCE = "performance"
    INTERACTION = "interaction"


@dataclass
class UXRule:
    """单条 UX 规则数据"""

    rule_id: str = ""
    category: str = ""
    priority: str = ""
    title: str = ""
    description: str = ""
    anti_pattern: str = ""
    stack_specific: str = ""
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationIssue:
    """单条验证问题"""

    check_name: str = ""
    severity: str = "warning"  # warning | error
    message: str = ""
    location: str = ""
    suggestion: str = ""


@dataclass
class ValidationResult:
    """UI 代码验证结果"""

    passed: bool = True
    warnings: list[ValidationIssue] = field(default_factory=list)
    errors: list[ValidationIssue] = field(default_factory=list)
    stack: str = "react"
    total_checks: int = 0


class CheckCategory(Enum):
    """检查项分类枚举"""

    VISUAL_QUALITY = "visual_quality"
    INTERACTION = "interaction"
    DARK_MODE = "dark_mode"
    LAYOUT = "layout"
    ACCESSIBILITY = "accessibility"


@dataclass
class CheckItem:
    """单条检查清单项"""

    id: str = ""
    category: CheckCategory = CheckCategory.VISUAL_QUALITY
    title: str = ""
    description: str = ""
    severity: str = "medium"  # critical | high | medium | low
    checked: bool = False


# ============================================================
# UXIntegration 主类
# ============================================================


class UXIntegration:
    """
    UI/UX 设计协同集成层

    通过 subprocess 调用 ui-ux-pro-max 技能的 search.py 脚本，
    实现设计系统生成、规则查询、代码验证和交付前检查等功能。
    当 ui-ux-pro-max 不可用时，自动降级为内置默认值或友好提示。

    用法示例::

        ux = UXIntegration()
        ds = ux.generate_design_system("mobile-app", "电商购物")
        rules = ux.search_ux_rules("touch", "按钮点击区域")
        result = ux.validate_ui_code("<button>提交</button>", "react")
        checklist = ux.get_pre_delivery_checklist()
    """

    # 支持的 UX 领域类型
    VALID_DOMAINS = {
        "accessibility", "touch", "animation", "forms",
        "navigation", "chart", "typography", "color",
        "layout", "performance", "interaction",
    }

    # 支持的技术栈
    VALID_STACKS = {
        "react", "vue", "swiftui", "flutter",
        "tailwind", "html-css",
    }

    def __init__(self, skill_root: Optional[Path] = None):
        """
        初始化集成层

        Args:
            skill_root: 技能根目录路径，默认为相对于当前文件的 skills 目录
        """
        if skill_root is None:
            self._skill_root = Path(__file__).resolve().parent.parent.parent.parent
        else:
            self._skill_root = Path(skill_root).resolve()

        self._search_script = (
            self._skill_root / "skills" / "ui-ux-pro-max" / "scripts" / "search.py"
        )

    @property
    def is_available(self) -> bool:
        """检查 ui-ux-pro-max 搜索脚本是否可用"""
        return self._search_script.exists()

    # ----------------------------------------------------------
    # 1. 设计系统生成接口
    # ----------------------------------------------------------

    def generate_design_system(
        self,
        product_type: str,
        keywords: str,
        project_name: str = "",
    ) -> DesignSystem:
        """
        根据产品类型和关键词生成完整的设计系统

        调用 ui-ux-pro-max 的 search.py 脚本获取设计系统配置，
        返回包含色彩、字体、特效等完整规范的数据对象。

        Args:
            product_type: 产品类型（如 mobile-app, web-dashboard, saas 等）
            keywords: 设计关键词（如"电商购物""金融科技""社交平台"）
            project_name: 项目名称，可选，用于个性化输出

        Returns:
            DesignSystem: 完整的设计系统数据对象
        """
        query = f"{product_type} {keywords}".strip()
        args = [query, "--design-system"]
        if project_name:
            args.extend(["-p", project_name])

        result = self._run_search_command(args)

        if result.returncode != 0 or not result.stdout.strip():
            return self._fallback_design_system(product_type, keywords)

        return self._parse_design_system_output(result.stdout)

    # ----------------------------------------------------------
    # 2. UX 规则查询接口
    # ----------------------------------------------------------

    def search_ux_rules(
        self,
        domain: str,
        query: str,
        max_results: int = 20,
    ) -> list[UXRule]:
        """
        按领域和关键词查询 UX 设计规则

        Args:
            domain: 规则领域，支持以下类型：
                accessibility | touch | animation | forms |
                navigation | chart | typography | color |
                layout | performance | interaction
            query: 搜索关键词
            max_results: 最大返回结果数，默认 20

        Returns:
            list[UXRule]: 匹配的 UX 规则列表

        Raises:
            ValueError: domain 不在支持列表中时抛出
        """
        domain_lower = domain.lower().strip()
        if domain_lower not in self.VALID_DOMAINS:
            supported = ", ".join(sorted(self.VALID_DOMAINS))
            raise ValueError(
                f"不支持的 domain 类型: '{domain}'，"
                f"支持的类型为: {supported}"
            )

        args = [query, "--domain", domain_lower]
        if max_results != 20:
            args.extend(["-n", str(max_results)])

        result = self._run_search_command(args)

        if result.returncode != 0 or not result.stdout.strip():
            return self._fallback_ux_rules(domain_lower, query)

        return self._parse_ux_rules_output(result.stdout)

    # ----------------------------------------------------------
    # 3. UI 代码验证接口
    # ----------------------------------------------------------

    def validate_ui_code(
        self,
        code: str,
        stack: str = "react",
    ) -> ValidationResult:
        """
        对 UI 代码进行多维度质量验证

        根据 target 技术栈选择对应的规则集，执行以下检查项：

        - 图标使用：禁止 emoji 作为图标，优先使用 SVG
        - 触控目标尺寸：可交互元素 ≥44×44pt
        - 颜色对比度：正常文本 ≥4.5:1
        - 动画时长：微交互 150~300ms
        - 表单标签：必须存在可见标签，不能仅依赖 placeholder
        - 导航模式：返回行为应可预测
        - 深色模式：独立验证暗色适配

        Args:
            code: 待验证的 UI 代码文本
            stack: 目标技术栈，支持 react/vue/swiftui/flutter/tailwind/html-css

        Returns:
            ValidationResult: 包含 passed/warnings/errors 的验证结果
        """
        stack_lower = stack.lower().strip()
        if stack_lower not in self.VALID_STACKS:
            supported = ", ".join(sorted(self.VALID_STACKS))
            raise ValueError(
                f"不支持的 stack 类型: '{stack}'，"
                f"支持的类型为: {supported}"
            )

        result = ValidationResult(stack=stack_lower, passed=True)
        code_lower = code.lower()

        result.total_checks = 7

        # --- 检查 1：图标使用 ---
        self._check_icon_usage(code, code_lower, stack_lower, result)

        # --- 检查 2：触控目标尺寸 ---
        self._check_touch_target(code, code_lower, stack_lower, result)

        # --- 检查 3：颜色对比度 ---
        self._check_color_contrast(code, code_lower, stack_lower, result)

        # --- 检查 4：动画时长 ---
        self._check_animation_duration(code, code_lower, stack_lower, result)

        # --- 检查 5：表单标签 ---
        self._check_form_labels(code, code_lower, stack_lower, result)

        # --- 检查 6：导航模式 ---
        self._check_navigation_pattern(code, code_lower, stack_lower, result)

        # --- 检查 7：深色模式支持 ---
        self._check_dark_mode_support(code, code_lower, stack_lower, result)

        result.passed = len(result.errors) == 0
        return result

    # ----------------------------------------------------------
    # 4. 交付前检查清单生成
    # ----------------------------------------------------------

    def get_pre_delivery_checklist(self) -> list[CheckItem]:
        """
        生成交付前的完整 UI/UX 检查清单

        覆盖五大类别共 22 项检查点：

        - Visual Quality（4 项）：图标一致性、视觉层次、状态清晰度、暗色模式配对
        - Interaction（4 项）：触控反馈、动画时机、手势冲突、禁用状态语义
        - Dark Mode（4 项）：文本对比度、次要文本对比度、分割线可见性、模态框不透明度
        - Layout（4 项）：安全区域、内容宽度、间距节奏、z-index 管理
        - Accessibility（6 项）：alt 文本、aria-label、键盘导航、焦点顺序、减少运动支持

        Returns:
            list[CheckItem]: 结构化的检查清单列表
        """
        checklist: list[CheckItem] = []

        idx = 1

        # === Visual Quality 类 ===
        vq_items = [
            ("VQ-01", "图标一致性",
             "全站图标风格统一（线性/填充/双色），同一功能在不同页面使用相同图标",
             "high"),
            ("VQ-02", "视觉层次清晰",
             "通过字号、字重、颜色深浅建立明确的信息层级，用户 3 秒内识别主次内容",
             "high"),
            ("VQ-03", "状态清晰度",
             "交互元素的所有状态（default/hover/active/disabled/focus）均有视觉区分",
             "critical"),
            ("VQ-04", "暗色模式配对",
             "每个亮色模式下的设计决策都有对应的暗色模式实现，无遗漏组件",
             "medium"),
        ]
        for cid, title, desc, sev in vq_items:
            checklist.append(CheckItem(
                id=cid, category=CheckCategory.VISUAL_QUALITY,
                title=title, description=desc, severity=sev,
            ))
            idx += 1

        # === Interaction 类 ===
        ix_items = [
            ("IX-01", "触控反馈即时",
             "用户操作后 100ms 内产生视觉/触觉反馈（按下态、波纹、缩放等）",
             "critical"),
            ("IX-02", "动画时机恰当",
             "入场动画在内容就绪后触发，退出动画不阻塞导航；尊重 prefers-reduced-motion",
             "high"),
            ("IX-03", "手势冲突避免",
             "水平滚动区域与侧滑返回手势不冲突；多指手势有明确的激活区域",
             "high"),
            ("IX-04", "禁用状态语义正确",
             "禁用的交互元素视觉上灰显且不可聚焦，使用 disabled 属性而非 CSS pointer-events",
             "critical"),
        ]
        for cid, title, desc, sev in ix_items:
            checklist.append(CheckItem(
                id=cid, category=CheckCategory.INTERACTION,
                title=title, description=desc, severity=sev,
            ))
            idx += 1

        # === Dark Mode 类 ===
        dm_items = [
            ("DM-01", "主文本对比度达标",
             "暗色模式下正文文字与背景对比度 ≥ 4.5:1（WCAG AA 标准）",
             "critical"),
            ("DM-02", "次要文本可读",
             "辅助说明、placeholder 等次要文本在暗色背景下仍保持足够辨识度（≥ 3:1）",
             "high"),
            ("DM-03", "分割线可见性",
             "暗色模式下边框/分割线使用适当亮度，不会与背景融为一体",
             "medium"),
            ("DM-04", "模态框/弹窗不透明度",
             "暗色模式下遮罩层和模态框背景不透明度充足，确保内容层级清晰",
             "high"),
        ]
        for cid, title, desc, sev in dm_items:
            checklist.append(CheckItem(
                id=cid, category=CheckCategory.DARK_MODE,
                title=title, description=desc, severity=sev,
            ))
            idx += 1

        # === Layout 类 ===
        ly_items = [
            ("LY-01", "安全区域适配",
             "内容不被刘海屏、底部指示器、系统 Dock 等系统 UI 遮挡",
             "critical"),
            ("LY-02", "内容阅读宽度合理",
             "正文行宽控制在 60~80 字符（约 720px 以内），超长内容分栏处理",
             "high"),
            ("LY-03", "间距节奏一致",
             "使用统一的间距基准单位（如 4px 或 8px 倍数），全局节奏协调",
             "medium"),
            ("LY-04", "z-index 管理规范",
             "建立 z-index 分层体系（modal > popover > sticky > static），避免随意叠加",
             "high"),
        ]
        for cid, title, desc, sev in ly_items:
            checklist.append(CheckItem(
                id=cid, category=CheckCategory.LAYOUT,
                title=title, description=desc, severity=sev,
            ))
            idx += 1

        # === Accessibility 类 ===
        a11y_items = [
            ("A11Y-01", "图片 alt 文本完整",
             "所有 <img> 和装饰性图片均配有语义准确的 alt 属性，纯装饰图 alt 为空字符串",
             "critical"),
            ("A11Y-02", "aria-label 准确",
             "图标按钮、无文本链接等纯视觉元素配有描述性的 aria-label 或 aria-labelledby",
             "critical"),
            ("A11Y-03", "键盘导航完备",
             "所有可交互元素可通过 Tab 键到达，Tab 顺序符合视觉阅读顺序",
             "critical"),
            ("A11Y-04", "焦点管理正确",
             "模态框打开时焦点 trapped 在内部，关闭后焦点回到触发元素",
             "high"),
            ("A11Y-05", "减少动画偏好支持",
             "检测到 prefers-reduced-motion: reduce 时禁用或大幅简化动画效果",
             "high"),
        ]
        for cid, title, desc, sev in a11y_items:
            checklist.append(CheckItem(
                id=cid, category=CheckCategory.ACCESSIBILITY,
                title=title, description=desc, severity=sev,
            ))
            idx += 1

        return checklist

    # ===========================================================
    # 辅助方法 —— 子进程命令执行
    # ===========================================================

    def _run_search_command(self, args: list[str]) -> subprocess.CompletedProcess:
        """
        执行 ui-ux-pro-max 的搜索命令并捕获输出

        Args:
            args: 传递给 search.py 的参数列表（不含脚本路径和 python）

        Returns:
            subprocess.CompletedProcess: 包含 returncode/stdout/stderr 的结果对象
        """
        cmd = [sys.executable, str(self._search_script)] + args

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self._skill_root),
                encoding="utf-8",
                errors="replace",
            )
            return result
        except FileNotFoundError:
            return subprocess.CompletedProcess(
                cmd, returncode=-1, stdout="", stderr="搜索脚本未找到"
            )
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(
                cmd, returncode=-1, stdout="", stderr="命令执行超时（30s）"
            )
        except Exception as exc:
            return subprocess.CompletedProcess(
                cmd, returncode=-1, stdout="", stderr=f"执行异常: {exc}"
            )

    # ===========================================================
    # 辅助方法 —— 输出解析
    # ===========================================================

    def _parse_design_system_output(self, output: str) -> DesignSystem:
        """
        解析设计系统命令的结构化输出

        支持 JSON 格式和键值对格式两种解析策略。

        Args:
            output: search.py 的原始标准输出

        Returns:
            DesignSystem: 解析后的设计系统数据对象
        """
        ds = DesignSystem(raw_output=output)
        output_stripped = output.strip()

        # 策略一：尝试 JSON 解析
        try:
            data = json.loads(output_stripped)
            return self._build_design_system_from_dict(data, ds)
        except (json.JSONDecodeError, TypeError):
            pass

        # 策略二：从格式化文本中提取字段
        ds.pattern = self._extract_field(output, r"(?:design\s*[- ])?pattern[:\s]*", "")
        ds.style = self._extract_field(output, r"(?:design\s*[- ])?style|风格[:\s]*", "")

        colors = ColorPalette()
        colors.primary = self._extract_field(output, r"primary(?:\s*color)?[:\s]*", "#1976D2")
        colors.secondary = self._extract_field(output, r"secondary(?:\s*color)?[:\s]*", "#424242")
        colors.accent = self._extract_field(output, r"accent(?:\s*color)?[:\s]*", "#FF4081")
        colors.background = self._extract_field(output, r"(?:bg|background)(?:\s*color)?[:\s]*", "#FAFAFA")
        colors.surface = self._extract_field(output, r"surface(?:\s*color)?[:\s]*", "#FFFFFF")
        ds.colors = colors

        typo = TypographySystem()
        typo.font_family = self._extract_field(
            output, r"font[\s_-]?family|字体(?:家族)?[:\s]*", "system-ui, sans-serif"
        )
        size_match = re.search(r"base(?:\s*font)?\s*(?:size)?[:\s]*(\d+)", output, re.IGNORECASE)
        if size_match:
            typo.base_size = int(size_match.group(1))
        ds.typography = typo

        anti_section = self._extract_block(output, "anti.?pattern|反模式|avoid")
        if anti_section:
            ds.anti_patterns = [
                line.strip("- *").strip()
                for line in anti_section.split("\n")
                if line.strip() and not line.strip().startswith("#")
            ]

        return ds

    def _build_design_system_from_dict(
        self, data: dict[str, Any], ds: DesignSystem
    ) -> DesignSystem:
        """从字典数据构建 DesignSystem 对象"""
        ds.pattern = data.get("pattern", data.get("design_pattern", ""))
        ds.style = data.get("style", data.get("design_style", ""))
        ds.anti_patterns = data.get("anti_patterns", data.get("antiPatterns", []))

        if isinstance(data.get("colors"), dict):
            c = data["colors"]
            ds.colors = ColorPalette(
                primary=c.get("primary", ""),
                secondary=c.get("secondary", ""),
                accent=c.get("accent", ""),
                background=c.get("background", ""),
                surface=c.get("surface", ""),
                error=c.get("error", ""),
                success=c.get("success", ""),
                warning=c.get("warning", ""),
                text_primary=c.get("text_primary", c.get("textPrimary", "")),
                text_secondary=c.get("text_secondary", c.get("textSecondary", "")),
                border=c.get("border", ""),
                raw_data=c,
            )

        if isinstance(data.get("typography"), dict):
            t = data["typography"]
            ds.typography = TypographySystem(
                font_family=t.get("font_family", t.get("fontFamily", "")),
                heading_font=t.get("heading_font", t.get("headingFont", "")),
                body_font=t.get("body_font", t.get("bodyFont", "")),
                mono_font=t.get("mono_font", t.get("monoFont", "")),
                base_size=int(t.get("base_size", t.get("baseSize", 16))),
                scale_ratio=float(t.get("scale_ratio", t.get("scaleRatio", 1.25))),
                line_height_base=float(t.get("line_height_base", t.get("lineHeightBase", 1.5))),
                heading_sizes=t.get("heading_sizes", t.get("headingSizes", {})),
                weight_regular=int(t.get("weight_regular", t.get("weightRegular", 400))),
                weight_medium=int(t.get("weight_medium", t.get("weightMedium", 500))),
                weight_bold=int(t.get("weight_bold", t.get("weightBold", 700))),
                raw_data=t,
            )

        ds.effects = data.get("effects", {})
        return ds

    def _parse_ux_rules_output(self, output: str) -> list[UXRule]:
        """
        解析 UX 规则查询的结构化输出

        支持 JSON 数组和格式化文本两种格式。

        Args:
            output: search.py 的原始标准输出

        Returns:
            list[UXRule]: 解析后的 UX 规则列表
        """
        rules: list[UXRule] = []
        output_stripped = output.strip()

        # 策略一：JSON 解析
        try:
            data = json.loads(output_stripped)
            if isinstance(data, list):
                for item in data:
                    rules.append(UXRule(
                        rule_id=item.get("rule_id", item.get("ruleId", "")),
                        category=item.get("category", ""),
                        priority=item.get("priority", ""),
                        title=item.get("title", ""),
                        description=item.get("description", ""),
                        anti_pattern=item.get("anti_pattern", item.get("antiPattern", "")),
                        stack_specific=item.get("stack_specific", item.get("stackSpecific", "")),
                        raw_data=item,
                    ))
                return rules
        except (json.JSONDecodeError, TypeError):
            pass

        # 策略二：逐块解析格式化文本
        blocks = re.split(r"\n(?=##?\s|\d+\.\s)", output)
        for block in blocks:
            block = block.strip()
            if not block or block.startswith("#") and len(block) < 10:
                continue
            rule = UXRule(
                rule_id=self._extract_field(block, r"(?:rule[_-]?)?id[:\s]*", ""),
                category=self._extract_field(block, r"category[:\s]*", ""),
                priority=self._extract_field(block, r"priority[:\s]*", "medium"),
                title=self._extract_field(block, r"title|标题[:\s]*", block[:60]),
                description=self._extract_field(block, r"description|描述[:\s]*", ""),
                anti_pattern=self._extract_field(
                    block, r"anti.?pattern|反模式|avoid[:\s]*", ""
                ),
                stack_specific=self._extract_field(
                    block, r"stack.?specific|技术栈相关[:\s]*", ""
                ),
            )
            if rule.title:
                rules.append(rule)

        return rules

    # ===========================================================
    # 内部验证检查方法
    # ===========================================================

    def _check_icon_usage(
        self, code: str, code_lower: str, stack: str, result: ValidationResult
    ) -> None:
        """检查图标使用规范：禁止 emoji 作为图标，推荐 SVG"""
        emoji_icon_patterns = [
            (r"<[^>]*>[🔍✏️🗑️❤️⭐🔔📁➕−×][^<]*</[^>]*>", "emoji 直接作为图标内容"),
            (r"icon\s*=\s*[\"'][^\"']*[{][^}]*[a-z]{2,}", "emoji 字符用于 icon 属性"),
        ]

        for pattern, hint in emoji_icon_patterns:
            matches = re.findall(pattern, code, re.IGNORECASE)
            for m in matches:
                result.warnings.append(ValidationIssue(
                    check_name="icon_usage",
                    severity="warning",
                    message=f"检测到可能使用 emoji 作为图标: {m[:50]}",
                    suggestion="建议使用 SVG 图标组件替代 emoji，确保跨平台一致性",
                ))

        has_svg = bool(re.search(r"<svg\b", code))
        has_icon_component = bool(re.search(
            r"(?:Icon|icon)\s*(?:Component|component)?[\s.{(<]", code
        ))

        if not has_svg and not has_icon_component:
            result.warnings.append(ValidationIssue(
                check_name="icon_usage",
                severity="warning",
                message="未检测到 SVG 图标或图标组件的使用",
                suggestion="推荐引入 SVG 图标库（如 lucide-react、heroicons）以获得更好的可访问性和可缩放性",
            ))

    def _check_touch_target(
        self, code: str, code_lower: str, stack: str, result: ValidationResult
    ) -> None:
        """检查触控目标尺寸：可交互元素 ≥44×44pt"""
        small_size_patterns = [
            (r"(?:width|w)[\s=:]+['\"]?(\d+(?:\.\d+)?)?(?:px|rem)?['\"]?"
             r"[^}]{0,80}(?:height|h)[\s=:]+['\"]?(\d+(?:\.\d+)?)?(?:px|rem)?", "inline"),
            (r"min-(?:width|height)[\s:]+['\"]?(\d+(?:\.\d+)?)?(?:px|rem)?['\"]?", "tailwind"),
        ]

        min_size_pt = 44
        for pattern, source in small_size_patterns:
            for match in re.finditer(pattern, code, re.IGNORECASE):
                groups = match.groups()
                w = float(groups[0]) if groups and groups[0] else 0
                h = float(groups[1]) if groups and len(groups) > 1 and groups[1] else w
                if 0 < w < min_size_pt or 0 < h < min_size_pt:
                    result.warnings.append(ValidationIssue(
                        check_name="touch_target",
                        severity="warning",
                        message=f"触控目标尺寸偏小 ({w}x{h}px)，建议 ≥{min_size_pt}x{min_size_pt}px",
                        location=f"位置 ~第{code[:match.start()].count(chr(10)) + 1}行",
                        suggestion="增加 padding 或设置 min-width/min-height 确保触控区域足够大",
                    ))

    def _check_color_contrast(
        self, code: str, code_lower: str, stack: str, result: ValidationResult
    ) -> None:
        """检查颜色对比度：正常文本 ≥4.5:1"""
        low_contrast_pairs = [
            (r"#(?:f0f0f0|eeeeee|e0e0e0).{0,30}#(?:999|aaa|bbb|ccc)", "浅灰配浅灰"),
            (r"color:\s*#[89abCDEF]{3,6}.{0,40}background:\s*#[0-9a-fA-F]{3,6}", "相似色值组合"),
        ]

        for pattern, desc in low_contrast_pairs:
            for match in re.finditer(pattern, code, re.IGNORECASE):
                result.warnings.append(ValidationIssue(
                    check_name="color_contrast",
                    severity="warning",
                    message=f"可能存在低对比度颜色组合 ({desc}): {match.group()[:60]}",
                    suggestion="使用 WCAG 对比度检查工具确保正常文本对比度 ≥4.5:1",
                ))

    def _check_animation_duration(
        self, code: str, code_lower: str, stack: str, result: ValidationResult
    ) -> None:
        """检查动画时长：微交互 150~300ms"""
        duration_pattern = re.compile(
            r"(?:duration|transition-duration|animation-duration)"
            r"\s*[:\(]\s*(\d+(?:\.\d+)?)\s*(ms|s)",
            re.IGNORECASE,
        )

        for m in duration_pattern.finditer(code):
            value = float(m.group(1))
            unit = m.group(2).lower()
            ms_value = value if unit == "ms" else value * 1000

            if ms_value < 150:
                result.warnings.append(ValidationIssue(
                    check_name="animation_duration",
                    severity="warning",
                    message=f"动画时长过短 ({ms_value:.0f}ms)，可能感知不明显",
                    suggestion="微交互建议时长 150~300ms，确保用户能感知状态变化",
                ))
            elif ms_value > 300:
                result.errors.append(ValidationIssue(
                    check_name="animation_duration",
                    severity="error",
                    message=f"微交互动画时长过长 ({ms_value:.0f}ms)，影响操作流畅感",
                    suggestion="将微交互时长缩短至 300ms 以内；复杂转场动画可保留更长但需有明确目的",
                ))

    def _check_form_labels(
        self, code: str, code_lower: str, stack: str, result: ValidationResult
    ) -> None:
        """检查表单标签：必须存在可见标签，不能仅依赖 placeholder"""
        inputs_without_label = re.findall(
            r"<(?:input|textarea|select)\b([^>]*?(?:type=['\"](?:text|email|password|search|tel|url)['\"])?[^>]*)>",
            code,
            re.IGNORECASE,
        )

        for attrs in inputs_without_label:
            has_id = bool(re.search(r"id=['\"]([^'\"]+)['\"]", attrs))
            has_aria_label = bool(re.search(r"aria-label|aria-labelledby", attrs))
            has_placeholder_only = (
                re.search(r"placeholder=", attrs)
                and not has_id
                and not has_aria_label
            )

            if has_placeholder_only:
                result.errors.append(ValidationIssue(
                    check_name="form_labels",
                    severity="error",
                    message="表单控件仅有 placeholder 无可见 label",
                    suggestion="添加 <label htmlFor={id}> 或 aria-label 属性，placeholder 不能替代标签",
                ))
            elif not has_aria_label and not has_id:
                result.warnings.append(ValidationIssue(
                    check_name="form_labels",
                    severity="warning",
                    message="表单控件缺少关联的 label 或 aria-label",
                    suggestion="为每个表单控件添加语义关联的标签，提升可访问性",
                ))

    def _check_navigation_pattern(
        self, code: str, code_lower: str, stack: str, result: ValidationResult
    ) -> None:
        """检查导航模式：返回行为应可预测"""
        risky_nav_patterns = [
            (r"window\.history\.pushState\([^)]*\);\s*$", "无条件 pushState 可能导致返回行为异常"),
            (r"event\.preventDefault\(\).*?(?:back|history\.go\(-1\))", "拦截返回事件但自定义逻辑不完善"),
            (r"<Link[^>]*to=['\"][^'\"]*['\"][^>]*onClick=\{.*?\}", "Link 组件同时绑定 onClick 可能干扰导航"),
        ]

        for pattern, hint in risky_nav_patterns:
            for m in re.finditer(pattern, code, re.IGNORECASE | re.DOTALL):
                result.warnings.append(ValidationIssue(
                    check_name="navigation_pattern",
                    severity="warning",
                    message=f"潜在导航模式风险: {hint}",
                    location=f"位置 ~第{code[:m.start()].count(chr(10)) + 1}行",
                    suggestion="确保自定义导航逻辑与浏览器历史记录同步，测试物理返回键行为",
                ))

    def _check_dark_mode_support(
        self, code: str, code_lower: str, stack: str, result: ValidationResult
    ) -> None:
        """检查深色模式支持：独立验证暗色适配"""
        has_dark_token = any(kw in code_lower for kw in [
            "dark:", "prefers-color-scheme", "[data-theme",
            "darkMode", "dark-mode", "isDark",
        ])
        has_hardcoded_light = bool(re.search(
            r"(?:color|background|bg)[^;]{0,30}(?:#[fF]{3}[0-9a-fA-F]{3}|white|#fff)\b",
            code,
        ))

        if not has_dark_token:
            result.warnings.append(ValidationIssue(
                check_name="dark_mode_support",
                severity="warning",
                message="未检测到暗色模式的任何适配实现",
                suggestion="考虑使用 CSS 变量 + media(prefers-color-scheme) 或 Tailwind dark: 前缀实现暗色模式",
            ))

        if has_hardcoded_light and has_dark_token:
            result.warnings.append(ValidationIssue(
                check_name="dark_mode_support",
                severity="warning",
                message="存在硬编码浅色值（white/#fff），可能在暗色模式下显示异常",
                suggestion="将硬编码颜色替换为 CSS 自定义属性或主题 token，确保暗色模式自动适配",
            ))

    # ===========================================================
    # 降级（Fallback）方法
    # ===========================================================

    def _fallback_design_system(
        self, product_type: str, keywords: str
    ) -> DesignSystem:
        """
        当 ui-ux-pro-max 不可用时返回合理的默认设计系统

        Args:
            product_type: 产品类型（用于选择默认配色倾向）
            keywords: 关键词（备用参考）

        Returns:
            DesignSystem: 内置默认设计系统
        """
        pt = product_type.lower()
        if "mobile" in pt or "app" in pt:
            colors = ColorPalette(
                primary="#1976D2", secondary="#424242", accent="#FF4081",
                background="#FAFAFA", surface="#FFFFFF",
                text_primary="#212121", text_secondary="#757575",
                border="#E0E0E0",
            )
            pattern = "Material Design 3"
            style = "移动端原生体验，卡片式布局，圆角 16dp"
        elif "dashboard" in pt or "admin" in pt or "saas" in pt:
            colors = ColorPalette(
                primary="#2563EB", secondary="#475569", accent="#8B5CF6",
                background="#F8FAFC", surface="#FFFFFF",
                text_primary="#0F172A", text_secondary="#64748B",
                border="#E2E8F0",
            )
            pattern = "Enterprise SaaS"
            style = "企业级仪表盘风格，侧边栏导航，数据密集型布局"
        elif "ecommerce" in pt or "电商" in keywords:
            colors = ColorPalette(
                primary="#DC2626", secondary="#374151", accent="#F59E0B",
                background="#FFFFFF", surface="#F9FAFB",
                text_primary="#111827", text_secondary="#6B7280",
                border="#E5E7EB",
            )
            pattern = "E-commerce"
            style = "电商风格，高转化导向，醒目 CTA 按钮"
        else:
            colors = ColorPalette(
                primary="#3B82F6", secondary="#64748B", accent="#EC4899",
                background="#FFFFFF", surface="#F8fafc",
                text_primary="#1E293B", text_secondary="#94A3B8",
                border="#E2E8F0",
            )
            pattern = "Modern Clean"
            style = "现代简约风格，大量留白，清晰的视觉层次"

        return DesignSystem(
            pattern=pattern,
            style=style,
            colors=colors,
            typography=TypographySystem(
                font_family="system-ui, -apple-system, sans-serif",
                base_size=16,
                scale_ratio=1.25,
                line_height_base=1.5,
            ),
            anti_patterns=[
                "ui-ux-pro-max 技能暂不可用，当前为内置默认设计系统",
                "建议安装 ui-ux-pro-max 技能以获取更精准的设计系统生成",
            ],
            raw_output="(fallback: ui-ux-pro-max unavailable)",
        )

    def _fallback_ux_rules(self, domain: str, query: str) -> list[UXRule]:
        """
        当 ui-ux-pro-max 不可用时返回该领域的通用 UX 规则

        Args:
            domain: 规则领域
            query: 查询关键词

        Returns:
            list[UXRule]: 内置默认规则列表
        """
        fallback_map: dict[str, list[dict[str, str]]] = {
            "accessibility": [
                {
                    "rule_id": "A11Y-FB-01", "category": "accessibility",
                    "priority": "critical", "title": "颜色不可作为唯一信息载体",
                    "description": "不能仅依靠颜色传达信息（如红色表示错误），必须配合文字或图标。",
                    "anti_pattern": "仅用红/绿颜色区分成功/失败状态",
                    "stack_specific": "",
                },
                {
                    "rule_id": "A11Y-FB-02", "category": "accessibility",
                    "priority": "critical", "title": "键盘可访问性",
                    "description": "所有功能必须可通过键盘完成操作，不支持键盘的操作等于对部分用户不可用。",
                    "anti_pattern": "依赖 hover/mouseover 触发核心功能",
                    "stack_specific": "React 中确保 onFocus/onBlur 与 onClick 行为一致",
                },
            ],
            "touch": [
                {
                    "rule_id": "TOUCH-FB-01", "category": "touch",
                    "priority": "high", "title": "最小触控目标 44x44pt",
                    "description": "Apple HIG 和 Google Material Design 均推荐触控目标至少 44x44 逻辑像素。",
                    "anti_pattern": "小图标按钮无 padding 扩展触控区",
                    "stack_specific": "SwiftUI 使用 .frame(minWidth:44, minHeight:44)",
                },
                {
                    "rule_id": "TOUCH-FB-02", "category": "touch",
                    "priority": "high", "title": "触控目标间距 ≥8pt",
                    "description": "相邻触控目标之间保持足够间距，防止误触。",
                    "anti_pattern": "紧凑排列的小按钮组无间隔",
                    "stack_specific": "",
                },
            ],
            "animation": [
                {
                    "rule_id": "ANIM-FB-01", "category": "animation",
                    "priority": "medium", "title": "微交互时长 150-300ms",
                    "description": "按钮按压、hover 状态切换等微交互应在 150-300ms 内完成，既可感知又不拖沓。",
                    "anti_pattern": "过渡动画超过 500ms 导致界面迟钝感",
                    "stack_specific": "CSS transition-duration: 200ms",
                },
            ],
        }

        rules_data = fallback_map.get(domain, [
            {
                "rule_id": f"{domain.upper()}-FB-01",
                "category": domain,
                "priority": "medium",
                "title": f"{domain} 领域通用规则",
                "description": (
                    f"关于 '{query}' 的 {domain} 设计建议："
                    "请查阅 ui-ux-pro-max 技能获取更详细的规则说明。"
                ),
                "anti_pattern": "",
                "stack_specific": "",
            },
        ])

        return [
            UXRule(**rd, raw_data=rd) for rd in rules_data
        ]

    # ===========================================================
    # 通用文本解析工具方法
    # ===========================================================

    @staticmethod
    def _extract_field(text: str, pattern: str, default: str = "") -> str:
        """
        从文本中按正则表达式提取字段值

        Args:
            text: 源文本
            pattern: 正则表达式（匹配字段名后紧跟冒号或等号的场景）
            default: 提取失败时的默认值

        Returns:
            str: 提取到的字段值
        """
        match = re.search(pattern + r"([^\n\r#<>{\[]+)", text, re.IGNORECASE)
        if match:
            value = match.group(1).strip().rstrip(":;, ")
            if value:
                return value
        return default

    @staticmethod
    def _extract_block(text: str, header_pattern: str) -> str:
        """
        从文本中提取指定标题下的整段内容

        Args:
            text: 源文本
            header_pattern: 区块标题的正则匹配模式

        Returns:
            str: 标题下方的文本块内容，未找到则返回空串
        """
        match = re.search(
            rf"(?:^|\n)(?:##?\s*)({header_pattern})\s*\n(.*?)(?=(?:\n##?\s)|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        return match.group(2).strip() if match else ""
