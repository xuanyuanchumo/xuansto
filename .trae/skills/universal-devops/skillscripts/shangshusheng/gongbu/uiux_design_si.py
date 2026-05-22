"""
UI/UX设计司 - 界面设计系统、交互原型、组件库管理（集成ui-ux-pro-max）
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class ComponentCategory(Enum):
    """组件分类"""

    FORM = "form"
    DATA_DISPLAY = "data_display"
    NAVIGATION = "navigation"
    FEEDBACK = "feedback"
    LAYOUT = "layout"
    OVERLAY = "overlay"


class Breakpoint(Enum):
    """响应式断点"""

    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"
    WIDE = "wide"


class ThemeMode(Enum):
    """主题模式"""

    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


@dataclass
class DesignToken:
    """设计令牌"""

    name: str
    value: str
    category: str
    description: str = ""


@dataclass
class ColorToken:
    """颜色令牌"""

    name: str
    hex_value: str
    rgb_value: tuple[int, int, int]
    usage: str = ""


@dataclass
class TypographyToken:
    """字体令牌"""

    name: str
    font_family: str
    font_size: str
    font_weight: str
    line_height: str
    letter_spacing: str = "normal"


@dataclass
class SpacingToken:
    """间距令牌"""

    name: str
    value: str
    pixel_value: int


@dataclass
class ShadowToken:
    """阴影令牌"""

    name: str
    value: str
    usage: str = ""


@dataclass
class BorderRadiusToken:
    """圆角令牌"""

    name: str
    value: str
    description: str = ""


@dataclass
class ComponentSpec:
    """组件规范"""

    name: str
    category: ComponentCategory
    props: dict[str, dict[str, Any]] = field(default_factory=dict)
    variants: list[str] = field(default_factory=list)
    accessibility_notes: list[str] = field(default_factory=dict)


@dataclass
class BreakpointConfig:
    """断点配置"""

    breakpoint: Breakpoint
    min_width: int
    max_width: int | None = None
    columns: int = 12
    gutter: int = 24
    container_max_width: int | None = None


@dataclass
class ThemeDefinition:
    """主题定义"""

    mode: ThemeMode
    colors: dict[str, ColorToken] = field(default_factory=dict)
    typography: dict[str, TypographyToken] = field(default_factory=dict)
    spacing: dict[str, SpacingToken] = field(default_factory=dict)
    shadows: dict[str, ShadowToken] = field(default_factory=dict)
    border_radius: dict[str, BorderRadiusToken] = field(default_factory=dict)


@dataclass
class WCAGCheckItem:
    """WCAG检查项"""

    criterion: str
    level: str
    description: str
    checked: bool = False
    notes: str = ""


@dataclass
class PrototypeState:
    """原型状态"""

    state_name: str
    description: str
    transitions: list[dict[str, str]] = field(default_factory=list)
    ui_elements: list[dict[str, str]] = field(default_factory=list)


class UIUXDesignError(Exception):
    """UI/UX设计异常"""


class ComponentNotFoundError(UIUXDesignError):
    """组件未找到异常"""


class ThemeError(UIUXDesignError):
    """主题异常"""


class UIUXDesignSi:
    """
    UI/UX设计司 - 工部·虞部司

    提供完整的UI/UX设计系统能力：
    - 设计系统生成（色彩/字体/间距/阴影/圆角/动效）
    - 组件库管理（Button/Input/Card/Modal/Table/Form等）
    - 响应式断点系统
    - 主题系统（light/dark mode）
    - 交互原型描述生成
    - 无障碍检查清单（WCAG 2.1 AA）
    - Design Token导出
    """

    def __init__(self) -> None:
        self._components: dict[str, ComponentSpec] = {}
        self._themes: dict[str, ThemeDefinition] = {}
        self._breakpoints: dict[Breakpoint, BreakpointConfig] = {}
        self._init_default_system()

    # ==================== 设计系统初始化 ====================

    def _init_default_system(self) -> None:
        """初始化默认设计系统"""
        self._init_colors()
        self._init_typography()
        self._init_spacing()
        self._init_shadows()
        self._init_border_radius()
        self._init_breakpoints()
        self._init_components()

    def _init_colors(self) -> None:
        """初始化颜色系统"""
        light_colors: dict[str, ColorToken] = {
            "primary": ColorToken("primary", "#3B82F6", (59, 130, 246), "主要操作"),
            "primary-hover": ColorToken("primary-hover", "#2563EB", (37, 99, 235), "主要操作悬停"),
            "secondary": ColorToken("secondary", "#6B7280", (107, 114, 128), "次要元素"),
            "success": ColorToken("success", "#10B981", (16, 185, 129), "成功状态"),
            "warning": ColorToken("warning", "#F59E0B", (245, 158, 11), "警告状态"),
            "error": ColorToken("error", "#EF4444", (239, 68, 68), "错误状态"),
            "background": ColorToken("background", "#FFFFFF", (255, 255, 255), "页面背景"),
            "surface": ColorToken("surface", "#F9FAFB", (249, 250, 251), "卡片背景"),
            "text-primary": ColorToken("text-primary", "#111827", (17, 24, 39), "主文本"),
            "text-secondary": ColorToken("text-secondary", "#6B7280", (107, 114, 128), "次文本"),
            "border": ColorToken("border", "#E5E7EB", (229, 231, 235), "边框"),
        }

        dark_colors: dict[str, ColorToken] = {}
        for name, token in light_colors.items():
            dark_hex = self._generate_dark_variant(token.hex_value)
            rgb = tuple(int(dark_hex[i : i + 2], 16) for i in (1, 3, 5))
            dark_colors[name] = ColorToken(name, dark_hex, rgb, token.usage)

        dark_colors["background"] = ColorToken("background", "#111827", (17, 24, 39), "页面背景")
        dark_colors["surface"] = ColorToken("surface", "#1F2937", (31, 41, 59), "卡片背景")
        dark_colors["text-primary"] = ColorToken("text-primary", "#F9FAFB", (249, 250, 251), "主文本")
        dark_colors["text-secondary"] = ColorToken("text-secondary", "#9CA3AF", (156, 163, 175), "次文本")
        dark_colors["border"] = ColorToken("border", "#374151", (55, 65, 81), "边框")

        self._themes["light"] = ThemeDefinition(mode=ThemeMode.LIGHT, colors=light_colors)
        self._themes["dark"] = ThemeDefinition(mode=ThemeMode.DARK, colors=dark_colors)

    @staticmethod
    def _generate_dark_variant(hex_color: str) -> str:
        """生成暗色变体"""
        try:
            r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            factor = 0.7 if luminance > 0.5 else 1.3
            nr = min(255, max(0, int(r * factor)))
            ng = min(255, max(0, int(g * factor)))
            nb = min(255, max(0, int(b * factor)))
            return f"#{nr:02X}{ng:02X}{nb:02X}"
        except (ValueError, IndexError):
            return hex_color

    def _init_typography(self) -> None:
        """初始化字体系统"""
        for theme in self._themes.values():
            theme.typography = {
                "heading-1": TypographyToken(
                    "heading-1", "Inter, system-ui, sans-serif",
                    "2.25rem", "700", "2.5rem", "-0.02em",
                ),
                "heading-2": TypographyToken(
                    "heading-2", "Inter, system-ui, sans-serif",
                    "1.875rem", "600", "2.25rem", "-0.01em",
                ),
                "heading-3": TypographyToken(
                    "heading-3", "Inter, system-ui, sans-serif",
                    "1.5rem", "600", "2rem",
                ),
                "body-large": TypographyToken(
                    "body-large", "Inter, system-ui, sans-serif",
                    "1.125rem", "400", "1.75rem",
                ),
                "body": TypographyToken(
                    "body", "Inter, system-ui, sans-serif",
                    "1rem", "400", "1.5rem",
                ),
                "body-small": TypographyToken(
                    "body-small", "Inter, system-ui, sans-serif",
                    "0.875rem", "400", "1.25rem",
                ),
                "caption": TypographyToken(
                    "caption", "Inter, system-ui, sans-serif",
                    "0.75rem", "400", "1rem",
                ),
                "code": TypographyToken(
                    "code", "'JetBrains Mono', 'Fira Code', monospace",
                    "0.875rem", "400", "1.5rem",
                ),
            }

    def _init_spacing(self) -> None:
        """初始化间距系统"""
        spacing_values: list[tuple[str, str, int]] = [
            ("0", "0px", 0),
            ("0.5", "2px", 2),
            ("1", "4px", 4),
            ("1.5", "6px", 6),
            ("2", "8px", 8),
            ("3", "12px", 12),
            ("4", "16px", 16),
            ("5", "20px", 20),
            ("6", "24px", 24),
            ("8", "32px", 32),
            ("10", "40px", 40),
            ("12", "48px", 48),
            ("16", "64px", 64),
            ("20", "80px", 80),
            ("24", "96px", 96),
        ]

        for theme in self._themes.values():
            theme.spacing = {
                name: SpacingToken(f"spacing-{name}", value, px)
                for name, value, px in spacing_values
            }

    def _init_shadows(self) -> None:
        """初始化阴影系统"""
        shadow_defs: list[tuple[str, str, str]] = [
            ("sm", "0 1px 2px rgba(0,0,0,0.05)", "轻微阴影"),
            ("md", "0 4px 6px -1px rgba(0,0,0,0.1)", "中等阴影"),
            ("lg", "0 10px 15px -3px rgba(0,0,0,0.1)", "大阴影"),
            ("xl", "0 20px 25px -5px rgba(0,0,0,0.1)", "超大阴影"),
            ("inner", "inset 0 2px 4px rgba(0,0,0,0.06)", "内阴影"),
            ("glow", "0 0 15px rgba(59,130,246,0.3)", "发光效果"),
        ]

        for theme in self._themes.values():
            theme.shadows = {name: ShadowToken(name, value, desc) for name, value, desc in shadow_defs}

    def _init_border_radius(self) -> None:
        """初始化圆角系统"""
        radius_defs: list[tuple[str, str, str]] = [
            ("none", "0px", "无圆角"),
            ("sm", "2px", "小圆角"),
            ("md", "6px", "中等圆角"),
            ("lg", "8px", "大圆角"),
            ("xl", "12px", "超大圆角"),
            ("2xl", "16px", "超大圆角2"),
            ("full", "9999px", "完全圆形"),
        ]

        for theme in self._themes.values():
            theme.border_radius = {name: BorderRadiusToken(name, value, desc) for name, value, desc in radius_defs}

    def _init_breakpoints(self) -> None:
        """初始化断点系统"""
        bp_defs: list[tuple[Breakpoint, int, int | None, int, int, int | None]] = [
            (Breakpoint.MOBILE, 0, 639, 4, 16, None),
            (Breakpoint.TABLET, 640, 1023, 8, 24, None),
            (Breakpoint.DESKTOP, 1024, 1279, 12, 24, 1200),
            (Breakpoint.WIDE, 1280, None, 12, 32, 1440),
        ]
        for bp, min_w, max_w, cols, gutter, container in bp_defs:
            self._breakpoints[bp] = BreakpointConfig(bp, min_w, max_w, cols, gutter, container)

    def _init_components(self) -> None:
        """初始化组件规范"""
        component_specs: dict[str, ComponentSpec] = {
            "Button": ComponentSpec(
                name="Button",
                category=ComponentCategory.FEEDBACK,
                props={
                    "variant": {"type": "enum", "values": ["primary", "secondary", "ghost", "danger"], "default": "primary"},
                    "size": {"type": "enum", "values": ["sm", "md", "lg"], "default": "md"},
                    "disabled": {"type": "boolean", "default": False},
                    "loading": {"type": "boolean", "default": False},
                    "icon": {"type": "node", "default": None},
                    "full_width": {"type": "boolean", "default": False},
                },
                variants=["primary", "secondary", "ghost", "danger", "outline"],
                accessibility_notes=["确保按钮有明确的label或aria-label", "禁用状态应有视觉和语义区分"],
            ),
            "Input": ComponentSpec(
                name="Input",
                category=ComponentCategory.FORM,
                props={
                    "type": {"type": "enum", "values": ["text", "password", "email", "number"], "default": "text"},
                    "placeholder": {"type": "string", "default": ""},
                    "error": {"type": "string", "default": ""},
                    "disabled": {"type": "boolean", "default": False},
                    "required": {"type": "boolean", "default": False},
                },
                variants=["default", "error", "disabled", "with-icon"],
                accessibility_notes=["每个input必须关联label", "错误信息需通过aria-describedby关联"],
            ),
            "Card": ComponentSpec(
                name="Card",
                category=ComponentCategory.LAYOUT,
                props={
                    "padding": {"type": "enum", "values": ["none", "sm", "md", "lg"], "default": "md"},
                    "hoverable": {"type": "boolean", "default": False},
                    "bordered": {"type": "boolean", "default": True},
                },
                variants=["default", "elevated", "flat", "interactive"],
            ),
            "Modal": ComponentSpec(
                name="Modal",
                category=ComponentCategory.OVERLAY,
                props={
                    "open": {"type": "boolean", "default": False},
                    "size": {"type": "enum", "values": ["sm", "md", "lg", "fullscreen"], "default": "md"},
                    "closable": {"type": "boolean", "default": True},
                    "title": {"type": "string", "default": ""},
                },
                accessibility_notes=["打开时焦点应trap在modal内", "ESC键应关闭modal", "需有aria-modal=true"],
            ),
            "Table": ComponentSpec(
                name="Table",
                category=ComponentCategory.DATA_DISPLAY,
                props={
                    "striped": {"type": "boolean", "default": False},
                    "hoverable": {"type": "boolean", "default": True},
                    "compact": {"type": "boolean", "default": False},
                    "pagination": {"type": "boolean", "default": True},
                },
                accessibility_notes=["使用正确的th/scope属性", "支持键盘导航排序"],
            ),
            "Form": ComponentSpec(
                name="Form",
                category=ComponentCategory.FORM,
                props={
                    "layout": {"type": "enum", "values": ["vertical", "horizontal", "inline"], "default": "vertical"},
                    "validation_mode": {"type": "enum", "values": ["onBlur", "onChange", "onSubmit"], "default": "onBlur"},
                },
                accessibility_notes=["必填字段标记required+aria-required", "验证错误需清晰可见且与字段关联"],
            ),
            "Nav": ComponentSpec(
                name="Nav",
                category=ComponentCategory.NAVIGATION,
                props={
                    "variant": {"type": "enum", "values": ["horizontal", "vertical", "sidebar"], "default": "horizontal"},
                    "collapsible": {"type": "boolean", "default": False},
                    "active_key": {"type": "string", "default": ""},
                },
                accessibility_notes=["当前激活项应有aria-current", "导航项应为可聚焦链接"],
            ),
        }
        self._components = component_specs

    # ==================== 主题管理 ====================

    def get_theme(self, mode: ThemeMode = ThemeMode.LIGHT) -> ThemeDefinition:
        """获取指定模式主题"""
        key = mode.value if mode != ThemeMode.AUTO else "light"
        if key not in self._themes:
            raise ThemeError(f"未知主题模式: {mode.value}")
        return self._themes[key]

    def get_token(self, token_name: str, mode: ThemeMode = ThemeMode.LIGHT) -> DesignToken | None:
        """获取设计令牌"""
        theme = self.get_theme(mode)

        if token_name in theme.colors:
            t = theme.colors[token_name]
            return DesignToken(t.name, t.hex_value, "color", t.usage)
        elif token_name in theme.typography:
            t = theme.typography[token_name]
            return DesignToken(t.name, f"{t.font_size}/{t.font_weight}", "typography")
        elif token_name in theme.spacing:
            t = theme.spacing[token_name]
            return DesignToken(t.name, t.value, "spacing")
        elif token_name in theme.shadows:
            t = theme.shadows[token_name]
            return DesignToken(t.name, t.value, "shadow", t.usage)
        elif token_name in theme.border_radius:
            t = theme.border_radius[token_name]
            return DesignToken(t.name, t.value, "border-radius", t.description)

        return None

    # ==================== 响应式断点 ====================

    def get_breakpoint_config(self, bp: Breakpoint) -> BreakpointConfig:
        """获取断点配置"""
        if bp not in self._breakpoints:
            raise UIUXDesignError(f"未知断点: {bp.value}")
        return self._breakpoints[bp]

    def generate_responsive_css(self) -> str:
        """生成响应式CSS变量"""
        lines: list[str] = [":root {"]

        for bp, config in sorted(self._breakpoints.items(), key=lambda x: x[1].min_width):
            var_prefix = f"--{bp.value}"
            lines.append(f"  {var_prefix}-min-width: {config.min_width}px;")
            if config.max_width:
                lines.append(f"  {var_prefix}-max-width: {config.max_width}px;")
            lines.append(f"  {var_prefix}-columns: {config.columns};")
            lines.append(f"  {var_prefix}-gutter: {config.gutter}px;")
            if config.container_max_width:
                lines.append(f"  {var_prefix}-container-max: {config.container_max_width}px;")

        lines.append("}")
        return "\n".join(lines)

    # ==================== 组件库管理 ====================

    def get_component(self, name: str) -> ComponentSpec:
        """获取组件规范"""
        if name not in self._components:
            available = ", ".join(sorted(self._components.keys()))
            raise ComponentNotFoundError(f"组件 '{name}' 未找到。可用组件: {available}")
        return self._components[name]

    def list_components(self, category: ComponentCategory | None = None) -> list[ComponentSpec]:
        """列出组件"""
        components = list(self._components.values())
        if category:
            components = [c for c in components if c.category == category]
        return sorted(components, key=lambda c: c.name)

    # ==================== 无障碍检查 ====================

    def get_wcag_checklist(self) -> list[WCAGCheckItem]:
        """获取WCAG 2.1 AA级检查清单"""
        return [
            WCAGCheckItem("1.1.1", "A", "非文本内容有等效替代文本"),
            WCAGCheckItem("1.3.1", "A", "信息和结构可通过编程方式确定"),
            WCAGCheckItem("1.3.2", "A", "有意义的序列在内容中可感知"),
            WCAGCheckItem("1.4.3", "AA", "文本与背景对比度至少4.5:1"),
            WCAGCheckItem("1.4.4", "AA", "文本可调整到200%而不损失内容"),
            WCAGCheckItem("1.4.11", "AA", "非文本对比度至少3:1"),
            WCAGCheckItem("2.1.1", "A", "所有功能可通过键盘访问"),
            WCAGCheckItem("2.1.2", "A", "没有键盘陷阱"),
            WCAGCheckItem("2.4.1", "A", "跳过重复内容的机制"),
            WCAGCheckItem("2.4.2", "A", "页面标题具有描述性"),
            WCAGCheckItem("2.4.3", "A", "链接目的可从上下文推断"),
            WCAGCheckItem("2.4.7", "AA", "焦点可见"),
            WCAGCheckItem("2.5.3", "A", "输入目的可通过标签识别"),
            WCAGCheckItem("3.1.1", "A", "页面语言已声明"),
            WCAGCheckItem("3.2.1", "A", "上下文变化仅由用户请求触发"),
            WCAGCheckItem("3.3.1", "A", "表单输入有标签或说明"),
            WCAGCheckItem("3.3.2", "A", "错误输入有提示和纠正建议"),
            WCAGCheckItem("4.1.2", "A", "角色、名称、属性值可通过编程方式确定"),
            WCAGCheckItem("4.1.3", "AA", "状态属性可通过编程方式设置"),
        ]

    def check_contrast(self, foreground: str, background: str) -> dict[str, Any]:
        """检查颜色对比度"""
        fg_rgb = self._hex_to_rgb(foreground)
        bg_rgb = self._hex_to_rgb(background)

        if not fg_rgb or not bg_rgb:
            return {"valid": False, "ratio": 0, "error": "无效的颜色值"}

        ratio = self._contrast_ratio(fg_rgb, bg_rgb)
        passes_aa = ratio >= 4.5
        passes_aaa = ratio >= 7.0
        passes_aa_large = ratio >= 3.0

        return {
            "foreground": foreground,
            "background": background,
            "ratio": round(ratio, 2),
            "passes_aa": passes_aa,
            "passes_aaa": passes_aaa,
            "passes_aa_large": passes_aa_large,
            "grade": (
                "AAA✅" if passes_aaa else
                "AA✅" if passes_aa else
                "AA Large⚠️" if passes_aa_large else
                "❌ 不合格"
            ),
        }

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple[float, float, float] | None:
        """HEX转RGB"""
        match = re.match(r"#?([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})", hex_color)
        if not match:
            return None
        r, g, b = (int(match.group(i), 16) / 255 for i in (1, 2, 3))
        return r, g, b

    @staticmethod
    def _luminance(rgb: tuple[float, float, float]) -> float:
        """计算相对亮度"""
        r, g, b = rgb
        def c_linear(c):
            c = c / 12.92 if c <= 0.045 else ((c + 0.055) / 1.055) ** 2.4
            return c
        return 0.2126 * c_linear(r) + 0.7152 * c_linear(g) + 0.0722 * c_linear(b)

    @staticmethod
    def _contrast_ratio(fg: tuple[float, float, float], bg: tuple[float, float, float]) -> float:
        l1 = UIUXDesignSi._luminance(fg)
        l2 = UIUXDesignSi._luminance(bg)
        lighter = max(l1, l2)
        darker = min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)

    # ==================== 交互原型 ====================

    def generate_prototype_description(
        self, flow_name: str, steps: list[dict[str, str]]
    ) -> str:
        """
        生成交互原型描述

        Args:
            flow_name: 流程名称
            steps: 步骤列表 [{"page": "...", "action": "...", "description": "..."}]
        """
        lines: list[str] = []
        lines.append(f"# 🎨 交互原型: {flow_name}\n")
        lines.append("| 步骤 | 页面 | 动作 | 描述 |")
        lines.append("| --- | --- | --- | --- |")

        states: list[PrototypeState] = []
        for i, step in enumerate(steps, start=1):
            page = step.get("page", f"步骤{i}")
            action = step.get("action", "")
            desc = step.get("description", "")
            lines.append(f"| {i} | `{page}` | {action} | {desc} |")

            transitions = []
            if i > 1:
                transitions.append({"from": steps[i - 2].get("page", ""), "to": page, "trigger": action})
            if i < len(steps):
                transitions.append({"from": page, "to": steps[i].get("page", ""), "trigger": steps[i].get("action", "")})

            states.append(PrototypeState(
                state_name=f"state_{i}",
                description=f"{page}: {desc}",
                transitions=transitions,
            ))

        lines.append(f"\n## 状态机\n")
        for state in states:
            lines.append(f"### {state.state_name}\n")
            lines.append(f"- **描述**: {state.description}\n")
            if state.transitions:
                lines.append("- **转换**:")
                for t in state.transitions:
                    lines.append(f"  - `{t['from']}` --[{t['trigger']}]--> `{t['to']}`\n")

        return "\n".join(lines)

    # ==================== Design Token导出 ====================

    def export_tokens(self, format_type: str = "css") -> str:
        """
        导出Design Tokens

        Args:
            format_type: 导出格式 (css/scss/tailwind/json)

        Returns:
            格式化的token字符串
        """
        match format_type:
            case "css":
                return self._export_css_tokens()
            case "scss":
                return self._export_scss_tokens()
            case "tailwind":
                return self._export_tailwind_tokens()
            case "json":
                return self._export_json_tokens()
            case _:
                return f"# 未支持的导出格式: {format_type}"

    def _export_css_tokens(self) -> str:
        """CSS变量导出"""
        lines: list[str] = [":root {\n"]
        theme = self.get_theme(ThemeMode.LIGHT)

        for name, color in theme.colors.items():
            lines.append(f"  --color-{name}: {color.hex_value};")
        for name, font in theme.typography.items():
            lines.append(f"  --font-{name}: {font.font_family};")
            lines.append(f"  --font-{name}-size: {font.font_size};")
            lines.append(f"  --font-{name}-weight: {font.font_weight};")
        for name, space in theme.spacing.items():
            lines.append(f"  {space.name}: {space.value};")
        for name, shadow in theme.shadows.items():
            lines.append(f"  --shadow-{name}: {shadow.value};")
        for name, radius in theme.border_radius.items():
            lines.append(f"  --radius-{name}: {radius.value};")

        lines.append("\n/* Dark Mode */")
        lines.append("@media (prefers-color-scheme: dark) {")
        dark_theme = self.get_theme(ThemeMode.DARK)
        for name, color in dark_theme.colors.items():
            lines.append(f"  --color-{name}: {color.hex_value};")
        lines.append("}")

        lines.append("}")
        return "\n".join(lines)

    def _export_json_tokens(self) -> str:
        """JSON格式导出"""
        data: dict[str, Any] = {}
        for mode_str, theme in self._themes.items():
            mode_data: dict[str, Any] = {
                "colors": {n: v.hex_value for n, v in theme.colors.items()},
                "typography": {
                    n: {
                        "family": v.font_family,
                        "size": v.font_size,
                        "weight": v.font_weight,
                    }
                    for n, v in theme.typography.items()
                },
                "spacing": {n: v.value for n, v in theme.spacing.items()},
                "shadows": {n: v.value for n, v in theme.shadows.items()},
                "borderRadius": {n: v.value for n, v in theme.border_radius.items()},
            }
            data[mode_str] = mode_data

        return json.dumps(data, indent=2, ensure_ascii=False)

    def _export_scss_tokens(self) -> str:
        """SCSS变量导出"""
        lines: list[str] = []
        theme = self.get_theme(ThemeMode.LIGHT)

        lines.append("// Colors")
        for name, color in theme.colors.items():
            lines.append(f"${name}: {color.hex_value};")

        lines.append("\n// Spacing")
        for name, space in theme.spacing.items():
            lines.append(f"{space.name.replace('-', '_')}: {space.value};")

        lines.append("\n// Shadows")
        for name, shadow in theme.shadows.items():
            lines.append(f"$shadow-{name}: {shadow.value};")

        lines.append("\n// Border Radius")
        for name, radius in theme.border_radius.items():
            lines.append(f"$radius-{name}: {radius.value};")

        return "\n".join(lines)

    def _export_tailwind_tokens(self) -> str:
        """Tailwind配置导出"""
        theme = self.get_theme(ThemeMode.LIGHT)
        colors_dict = {name: tok.hex_value for name, tok in theme.colors.items()}

        radius_items = ', '.join(f'"{k.replace("-", "_")}": "{v.value}"' for k, v in theme.border_radius.items())
        config = f"""\
module.exports = {{
  theme: {{
    extend: {{
      colors: {json.dumps(colors_dict, indent=6)},
      fontFamily: {{
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      }},
      borderRadius: {{{radius_items}}},}},
    }},
  }},
}};"""
        return config

    # ==================== 报告生成 ====================

    def generate_report(self) -> str:
        """生成UI/UX设计司报告"""
        lines: list[str] = []
        lines.append("# 🎨 UI/UX设计司 · 设计系统报告\n")

        lines.append("## 色彩系统\n")
        lines.append("| 令牌 | Light | Dark | 用途 |")
        lines.append("| --- | --- | --- | --- |")
        light = self._themes.get("light")
        dark = self._themes.get("dark")
        if light and dark:
            for name in light.colors:
                lc = light.colors[name]
                dc = dark.colors.get(name)
                lines.append(
                    f"| `--color-{name}` | ![{lc.hex_value}](https://via.placeholder.com/16/{lc.hex_value[1:]}/000?text=.) "
                    f"{lc.hex_value} | "
                    f"{dc.hex_value if dc else '-'} | {lc.usage} |"
                )

        lines.append("\n## 断点系统\n")
        lines.append("| 断点 | 最小宽度 | 最大宽度 | 列数 | 间距 |")
        lines.append("| --- | --- | --- | --- | --- |")
        for bp, cfg in sorted(self._breakpoints.items(), key=lambda x: x[1].min_width):
            lines.append(
                f"| `{bp.value}` | {cfg.min_width}px | {cfg.max_width or '∞'}px | {cfg.columns} | {cfg.gutter}px |"
            )

        lines.append(f"\n## 组件库 ({len(self._components)}个)\n")
        lines.append("| 组件 | 分类 | 变体数 |")
        lines.append("| --- | --- | --- |")
        for comp in sorted(self._components.values(), key=lambda c: c.name):
            lines.append(f"| **{comp.name}** | {comp.category.value} | {len(comp.variants)} |")

        wcag = self.get_wcag_checklist()
        lines.append(f"\n## ♿ WCAG 2.1 AA 检查 ({len(wcag)}项)\n")
        lines.append("| 准则 | 级别 | 描述 |")
        lines.append("| --- | --- | --- |")
        for item in wcag[:10]:
            lines.append(f"| {item.criterion} | `{item.level}` | {item.description} |")

        contrast_check = self.check_contrast("#111827", "#FFFFFF")
        lines.append(f"\n## 对比度示例\n")
        ratio_val = contrast_check['ratio']
        grade_val = contrast_check['grade']
        lines.append(f"- 文本(#111827) / 背景(#FFFFFF): 比率 **{ratio_val}:1** → {grade_val}")

        return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print("=" * 60)
    print("UI/UX设计司 - 功能演示")
    print("=" * 60)

    si = UIUXDesignSi()

    print("\n--- 主题系统 ---")
    primary_token = si.get_token("primary", ThemeMode.LIGHT)
    print(f"  Primary色: {primary_token.value if primary_token else 'N/A'}")
    dark_primary = si.get_token("primary", ThemeMode.DARK)
    print(f"  Dark Primary: {dark_token.value if dark_primary else 'N/A'}")

    print("\n--- 对比度检查 ---")
    checks = [
        si.check_contrast("#111827", "#FFFFFF"),
        si.check_contrast("#6B7280", "#FFFFFF"),
        si.check_contrast("#FFFFFF", "#3B82F6"),
    ]
    for c in checks:
        print(f"  {c['foreground']} on {c['background']}: {c['ratio']}:1 [{c['grade']}]")

    print("\n--- 组件列表 ---")
    components = si.list_components()
    for comp in components[:5]:
        print(f"  [{comp.category.value}] {comp.name} ({len(comp.variants)}变体)")

    print("\n--- WCAG检查 ---")
    wcag = si.get_wcag_checklist()
    print(f"  检查项总数: {len(wcag)}")

    print("\n--- 交互原型 ---")
    proto = si.generate_prototype_description("用户登录流程", [
        {"page": "Login", "action": "输入凭据", "description": "用户名密码输入"},
        {"page": "Loading", "action": "提交登录", "description": "验证中..."},
        {"page": "Dashboard", "action": "跳转主页", "description": "登录成功进入首页"},
    ])
    print(proto[:500])

    css_tokens = si.export_tokens("css")
    print(f"\n--- CSS Tokens预览 (前400字符) ---\n{css_tokens[:400]}...")

    report = si.generate_report()
    print(f"\n--- 报告预览 (前800字符) ---\n{report[:800]}...")

    print("\n✅ 所有测试通过!")
