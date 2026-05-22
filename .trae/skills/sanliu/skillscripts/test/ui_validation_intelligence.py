#!/usr/bin/env python3
"""
UI智能校验器 - Sanliu 技能

功能：
- UI规范检查（设计系统规范、颜色对比度、字体规范）
- 组件一致性检查
- 响应式布局验证
- 性能检查
- 深度集成ui-ux-pro-max技能
- 自动生成多格式报告

使用方法：
    python ui_validation_intelligence.py --help
    python ui_validation_intelligence.py --check-all
    python ui_validation_intelligence.py --visual-regression
    python ui_validation_intelligence.py --consistency-check
    python ui_validation_intelligence.py --accessibility
    python ui_validation_intelligence.py --design-system
    python ui_validation_intelligence.py --performance
"""

import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from skillscripts.core.script_base import ScriptBase, ReportFormat, ScriptResult, ScriptStatus


class IssueSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IssueCategory(Enum):
    ACCESSIBILITY = "accessibility"
    CONSISTENCY = "consistency"
    VISUAL = "visual"
    PERFORMANCE = "performance"
    BEST_PRACTICE = "best_practice"
    RESPONSIVE = "responsive"
    DESIGN_SYSTEM = "design_system"
    COLOR = "color"
    TYPOGRAPHY = "typography"


@dataclass
class UIIssue:
    file_path: str
    line_number: int
    category: IssueCategory
    severity: IssueSeverity
    message: str
    suggestion: str
    element: str = ""
    rule_id: str = ""
    wcag_level: str = ""
    fix_code: str = ""


@dataclass
class ComponentSnapshot:
    component_name: str
    file_path: str
    content_hash: str
    timestamp: datetime
    props: List[str] = field(default_factory=list)
    events: List[str] = field(default_factory=list)
    slots: List[str] = field(default_factory=list)


@dataclass
class VisualDiff:
    component_name: str
    baseline_hash: str
    current_hash: str
    diff_percentage: float
    has_changes: bool
    changes: List[str] = field(default_factory=list)


@dataclass
class ColorContrastResult:
    foreground: str
    background: str
    ratio: float
    wcag_aa: bool
    wcag_aaa: bool
    element: str


@dataclass
class PerformanceMetric:
    metric_name: str
    value: float
    threshold: float
    status: str
    file_path: str


class ColorUtils:
    """颜色工具类 - 用于颜色对比度计算"""
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """将十六进制颜色转换为RGB"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def rgb_to_luminance(r: int, g: int, b: int) -> float:
        """计算相对亮度"""
        def adjust(c):
            c = c / 255.0
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)
    
    @staticmethod
    def calculate_contrast_ratio(color1: str, color2: str) -> float:
        """计算两个颜色之间的对比度比率"""
        try:
            rgb1 = ColorUtils.hex_to_rgb(color1)
            rgb2 = ColorUtils.hex_to_rgb(color2)
            l1 = ColorUtils.rgb_to_luminance(*rgb1)
            l2 = ColorUtils.rgb_to_luminance(*rgb2)
            lighter = max(l1, l2)
            darker = min(l1, l2)
            return (lighter + 0.05) / (darker + 0.05)
        except Exception:
            return 0.0
    
    @staticmethod
    def extract_colors_from_style(style_str: str) -> List[str]:
        """从样式字符串中提取颜色值"""
        colors = []
        hex_pattern = r'#[0-9a-fA-F]{3,8}'
        rgb_pattern = r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)'
        rgba_pattern = r'rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*[\d.]+\s*\)'
        
        colors.extend(re.findall(hex_pattern, style_str))
        
        for match in re.finditer(rgb_pattern, style_str):
            r, g, b = match.groups()
            colors.append(f"#{int(r):02x}{int(g):02x}{int(b):02x}")
        
        for match in re.finditer(rgba_pattern, style_str):
            r, g, b = match.groups()
            colors.append(f"#{int(r):02x}{int(g):02x}{int(b):02x}")
        
        return colors


class AccessibilityChecker:
    """可访问性检查器 - 增强版"""
    
    def __init__(self):
        self.rules = self._load_rules()
    
    def _load_rules(self) -> List[dict]:
        """加载可访问性规则 - 包含WCAG 2.1标准"""
        return [
            {
                "id": "img-alt",
                "pattern": r'<img[^>]*>',
                "check": lambda m: 'alt=' in m.group(0),
                "message": "图片元素缺少 alt 属性",
                "suggestion": "添加描述性的 alt 属性，如 alt='产品图片'",
                "severity": IssueSeverity.ERROR,
                "wcag_level": "A",
                "fix_code": '<img src="..." alt="描述性文本">'
            },
            {
                "id": "img-alt-empty",
                "pattern": r'<img[^>]*alt=["\']["\'][^>]*>',
                "check": lambda m: False,
                "message": "图片 alt 属性为空，可能需要装饰性标记",
                "suggestion": "如果是装饰性图片，添加 role='presentation'；否则添加描述性文本",
                "severity": IssueSeverity.WARNING,
                "wcag_level": "A",
                "fix_code": '<img src="..." alt="" role="presentation"> 或 <img src="..." alt="描述性文本">'
            },
            {
                "id": "button-aria",
                "pattern": r'<button[^>]*>',
                "check": lambda m: 'aria-label=' in m.group(0) or re.search(r'>[^<]+</button>', m.group(0)) is not None,
                "message": "按钮可能缺少无障碍标签",
                "suggestion": "添加 aria-label 或确保按钮内有文本内容",
                "severity": IssueSeverity.WARNING,
                "wcag_level": "A",
                "fix_code": '<button aria-label="提交表单">...</button>'
            },
            {
                "id": "input-label",
                "pattern": r'<input[^>]*type=["\'](?:text|email|password|tel|number|search)["\'][^>]*>',
                "check": lambda m: 'aria-label=' in m.group(0) or 'id=' in m.group(0),
                "message": "输入框可能缺少关联的标签",
                "suggestion": "添加 aria-label 或关联 label 元素",
                "severity": IssueSeverity.WARNING,
                "wcag_level": "A",
                "fix_code": '<label for="email">邮箱</label><input id="email" type="email">'
            },
            {
                "id": "heading-order",
                "pattern": r'<h([1-6])[^>]*>',
                "check": lambda m: True,
                "message": "检查标题层级顺序",
                "suggestion": "确保标题层级按顺序递减，不要跳过层级",
                "severity": IssueSeverity.INFO,
                "wcag_level": "AA",
                "fix_code": "<h1>主标题</h1><h2>副标题</h2>"
            },
            {
                "id": "link-text",
                "pattern": r'<a[^>]*>(?:\s*|点击这里|更多|更多详情|阅读更多)\s*</a>',
                "check": lambda m: False,
                "message": "链接文本不够描述性",
                "suggestion": "使用描述性的链接文本，避免使用'点击这里'等通用文本",
                "severity": IssueSeverity.WARNING,
                "wcag_level": "A",
                "fix_code": '<a href="...">查看产品详情</a>'
            },
            {
                "id": "form-submit-button",
                "pattern": r'<form[^>]*>.*?</form>',
                "check": lambda m: re.search(r'<(?:button|input)[^>]*type=["\']submit["\']', m.group(0), re.DOTALL) is not None,
                "message": "表单缺少提交按钮",
                "suggestion": "为表单添加明确的提交按钮",
                "severity": IssueSeverity.WARNING,
                "wcag_level": "A",
                "fix_code": '<button type="submit">提交</button>'
            },
            {
                "id": "table-headers",
                "pattern": r'<table[^>]*>.*?</table>',
                "check": lambda m: '<th' in m.group(0).lower(),
                "message": "表格缺少表头",
                "suggestion": "为表格添加 <th> 元素定义表头",
                "severity": IssueSeverity.WARNING,
                "wcag_level": "A",
                "fix_code": '<table><thead><tr><th>标题</th></tr></thead>...</table>'
            },
            {
                "id": "skip-link",
                "pattern": r'<body[^>]*>',
                "check": lambda m: 'skip' in m.group(0).lower() or 'href="#main"' in m.group(0).lower(),
                "message": "页面可能缺少跳过导航链接",
                "suggestion": "添加跳过导航链接以便键盘用户快速访问主内容",
                "severity": IssueSeverity.INFO,
                "wcag_level": "A",
                "fix_code": '<a href="#main-content" class="skip-link">跳到主内容</a>'
            },
            {
                "id": "aria-hidden-focusable",
                "pattern": r'aria-hidden=["\']true["\'][^>]*>',
                "check": lambda m: 'tabindex="-1"' in m.group(0) or '<button' not in m.group(0).lower(),
                "message": "aria-hidden 元素可能包含可聚焦元素",
                "suggestion": "确保 aria-hidden 元素内的所有元素都不可聚焦",
                "severity": IssueSeverity.ERROR,
                "wcag_level": "A",
                "fix_code": '<div aria-hidden="true" tabindex="-1">...</div>'
            },
            {
                "id": "focus-visible",
                "pattern": r':focus\s*\{[^}]*\}',
                "check": lambda m: 'outline' in m.group(0) or 'box-shadow' in m.group(0),
                "message": "焦点样式可能不够明显",
                "suggestion": "确保焦点状态有明显的视觉指示",
                "severity": IssueSeverity.WARNING,
                "wcag_level": "AA",
                "fix_code": ':focus { outline: 2px solid #007bff; outline-offset: 2px; }'
            },
            {
                "id": "lang-attribute",
                "pattern": r'<html[^>]*>',
                "check": lambda m: 'lang=' in m.group(0),
                "message": "html 元素缺少 lang 属性",
                "suggestion": "添加 lang 属性指定页面语言",
                "severity": IssueSeverity.ERROR,
                "wcag_level": "A",
                "fix_code": '<html lang="zh-CN">'
            },
            {
                "id": "title-element",
                "pattern": r'<head[^>]*>.*?</head>',
                "check": lambda m: '<title' in m.group(0).lower(),
                "message": "页面缺少 title 元素",
                "suggestion": "为页面添加描述性的标题",
                "severity": IssueSeverity.ERROR,
                "wcag_level": "A",
                "fix_code": '<title>页面标题 - 网站名称</title>'
            },
            {
                "id": "color-contrast",
                "pattern": r'(?:color|background-color):\s*([^;]+)',
                "check": lambda m: True,
                "message": "需要检查颜色对比度",
                "suggestion": "确保文本与背景的对比度至少为 4.5:1 (AA级) 或 7:1 (AAA级)",
                "severity": IssueSeverity.INFO,
                "wcag_level": "AA",
                "fix_code": ""
            }
        ]
    
    def check_file(self, file_path: Path) -> List[UIIssue]:
        """检查单个文件的可访问性问题"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for rule in self.rules:
                pattern = re.compile(rule["pattern"], re.IGNORECASE | re.DOTALL)
                for match in pattern.finditer(content):
                    if not rule["check"](match):
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append(UIIssue(
                            file_path=str(file_path),
                            line_number=line_num,
                            category=IssueCategory.ACCESSIBILITY,
                            severity=rule["severity"],
                            message=rule["message"],
                            suggestion=rule["suggestion"],
                            element=match.group(0)[:50],
                            rule_id=rule["id"],
                            wcag_level=rule.get("wcag_level", ""),
                            fix_code=rule.get("fix_code", "")
                        ))
        except Exception:
            pass
        
        return issues


class ConsistencyChecker:
    """一致性检查器 - 增强版"""
    
    def __init__(self):
        self.component_patterns = {
            "button": {
                "variants": ["primary", "secondary", "danger", "success", "warning", "ghost", "outline"],
                "sizes": ["small", "medium", "large", "sm", "md", "lg"],
                "required_props": ["type"],
                "recommended_props": ["disabled", "loading"]
            },
            "input": {
                "variants": ["default", "filled", "outlined", "underline"],
                "sizes": ["small", "medium", "large", "sm", "md", "lg"],
                "required_props": [],
                "recommended_props": ["placeholder", "disabled", "error"]
            },
            "card": {
                "variants": ["default", "outlined", "elevated", "filled"],
                "sizes": [],
                "required_props": [],
                "recommended_props": ["title", "subtitle"]
            },
            "modal": {
                "variants": ["default", "fullscreen", "drawer"],
                "sizes": ["small", "medium", "large"],
                "required_props": [],
                "recommended_props": ["title", "onClose", "footer"]
            },
            "table": {
                "variants": ["default", "striped", "bordered"],
                "sizes": [],
                "required_props": [],
                "recommended_props": ["columns", "dataSource", "pagination"]
            }
        }
        self.naming_conventions = {
            "component": r'^[A-Z][a-zA-Z0-9]*$',
            "prop": r'^[a-z][a-zA-Z0-9]*$',
            "event": r'^on[A-Z][a-zA-Z0-9]*$',
            "css_class": r'^[a-z][a-z0-9-]*$'
        }
    
    def check_consistency(self, file_path: Path) -> List[UIIssue]:
        """检查文件的一致性问题"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            issues.extend(self._check_naming_conventions(file_path, content))
            issues.extend(self._check_component_usage(file_path, content))
            issues.extend(self._check_style_consistency(file_path, content))
            issues.extend(self._check_import_consistency(file_path, content))
            issues.extend(self._check_event_handlers(file_path, content))
            
        except Exception:
            pass
        
        return issues
    
    def _check_naming_conventions(self, file_path: Path, content: str) -> List[UIIssue]:
        """检查命名规范"""
        issues = []
        
        class_patterns = re.findall(r'class=["\']([^"\']+)["\']', content)
        for class_str in class_patterns:
            classes = class_str.split()
            for cls in classes:
                if re.match(r'^[A-Z]', cls) and not cls.startswith('__'):
                    issues.append(UIIssue(
                        file_path=str(file_path),
                        line_number=0,
                        category=IssueCategory.CONSISTENCY,
                        severity=IssueSeverity.WARNING,
                        message=f"CSS类名应使用kebab-case: {cls}",
                        suggestion="使用小写字母和连字符，如 'btn-primary'",
                        element=cls,
                        rule_id="naming-css-class"
                    ))
        
        event_patterns = re.findall(r'(@|on)([a-zA-Z]+)=["\']([^"\']+)["\']', content)
        for prefix, event_name, handler in event_patterns:
            if not event_name.startswith('on') and prefix != 'on':
                issues.append(UIIssue(
                    file_path=str(file_path),
                    line_number=0,
                    category=IssueCategory.CONSISTENCY,
                    severity=IssueSeverity.INFO,
                    message=f"事件处理器命名建议使用on前缀: {event_name}",
                    suggestion="使用 onClick, onChange 等标准命名",
                    element=f"{prefix}{event_name}",
                    rule_id="naming-event"
                ))
        
        return issues
    
    def _check_component_usage(self, file_path: Path, content: str) -> List[UIIssue]:
        """检查组件使用规范"""
        issues = []
        
        for component_name, config in self.component_patterns.items():
            pattern = rf'<{component_name}[^>]*>'
            matches = re.finditer(pattern, content, re.IGNORECASE)
            
            for match in matches:
                element = match.group(0)
                
                for prop in config.get("required_props", []):
                    if f'{prop}=' not in element and f':{prop}=' not in element:
                        issues.append(UIIssue(
                            file_path=str(file_path),
                            line_number=content[:match.start()].count('\n') + 1,
                            category=IssueCategory.CONSISTENCY,
                            severity=IssueSeverity.WARNING,
                            message=f"{component_name} 组件缺少推荐的 {prop} 属性",
                            suggestion=f"添加 {prop} 属性以提高组件一致性",
                            element=element[:50],
                            rule_id=f"component-{component_name}-{prop}"
                        ))
                
                for prop in config.get("recommended_props", []):
                    if f'{prop}=' not in element and f':{prop}=' not in element:
                        issues.append(UIIssue(
                            file_path=str(file_path),
                            line_number=content[:match.start()].count('\n') + 1,
                            category=IssueCategory.CONSISTENCY,
                            severity=IssueSeverity.INFO,
                            message=f"{component_name} 组件建议添加 {prop} 属性",
                            suggestion=f"添加 {prop} 属性以增强用户体验",
                            element=element[:50],
                            rule_id=f"component-{component_name}-{prop}-recommended"
                        ))
        
        return issues
    
    def _check_style_consistency(self, file_path: Path, content: str) -> List[UIIssue]:
        """检查样式一致性"""
        issues = []
        
        inline_styles = re.findall(r'style=["\']([^"\']+)["\']', content)
        if len(inline_styles) > 3:
            issues.append(UIIssue(
                file_path=str(file_path),
                line_number=0,
                category=IssueCategory.CONSISTENCY,
                severity=IssueSeverity.INFO,
                message=f"发现 {len(inline_styles)} 个内联样式，建议使用CSS类",
                suggestion="将内联样式提取到CSS类中以保持一致性和可维护性",
                element="",
                rule_id="style-inline"
            ))
        
        hardcoded_colors = re.findall(r'(?:color|background|border-color):\s*(#[0-9a-fA-F]{3,8}|rgb\([^)]+\))', content)
        if len(hardcoded_colors) > 5:
            issues.append(UIIssue(
                file_path=str(file_path),
                line_number=0,
                category=IssueCategory.CONSISTENCY,
                severity=IssueSeverity.WARNING,
                message=f"发现 {len(hardcoded_colors)} 处硬编码颜色，建议使用设计系统变量",
                suggestion="使用 CSS 变量或设计系统颜色 token",
                element="",
                rule_id="style-hardcoded-colors"
            ))
        
        spacing_values = re.findall(r'(?:margin|padding|gap):\s*(\d+)px', content)
        inconsistent_spacing = set(spacing_values)
        if len(inconsistent_spacing) > 6:
            issues.append(UIIssue(
                file_path=str(file_path),
                line_number=0,
                category=IssueCategory.CONSISTENCY,
                severity=IssueSeverity.INFO,
                message=f"发现 {len(inconsistent_spacing)} 种不同的间距值，建议统一",
                suggestion="使用 4px 或 8px 为基准的间距系统",
                element="",
                rule_id="style-spacing"
            ))
        
        return issues
    
    def _check_import_consistency(self, file_path: Path, content: str) -> List[UIIssue]:
        """检查导入一致性"""
        issues = []
        
        import_patterns = re.findall(r'import\s+.*?from\s+["\']([^"\']+)["\']', content)
        
        duplicate_imports = {}
        for imp in import_patterns:
            if imp in duplicate_imports:
                duplicate_imports[imp] += 1
            else:
                duplicate_imports[imp] = 1
        
        for module, count in duplicate_imports.items():
            if count > 1:
                issues.append(UIIssue(
                    file_path=str(file_path),
                    line_number=0,
                    category=IssueCategory.CONSISTENCY,
                    severity=IssueSeverity.WARNING,
                    message=f"模块 {module} 被多次导入",
                    suggestion="合并相同的导入语句",
                    element=module,
                    rule_id="import-duplicate"
                ))
        
        return issues
    
    def _check_event_handlers(self, file_path: Path, content: str) -> List[UIIssue]:
        """检查事件处理器"""
        issues = []
        
        arrow_handlers = re.findall(r'onClick=\{\s*\(\s*\)\s*=>', content)
        if len(arrow_handlers) > 3:
            issues.append(UIIssue(
                file_path=str(file_path),
                line_number=0,
                category=IssueCategory.PERFORMANCE,
                severity=IssueSeverity.INFO,
                message=f"发现 {len(arrow_handlers)} 个内联箭头函数事件处理器",
                suggestion="考虑使用 useCallback 或提取为独立函数以避免不必要的重渲染",
                element="",
                rule_id="event-inline-handler"
            ))
        
        return issues


class ResponsiveLayoutValidator:
    """响应式布局验证器 - 增强版"""
    
    def __init__(self):
        self.breakpoints = {
            'xs': 0,
            'sm': 576,
            'md': 768,
            'lg': 992,
            'xl': 1200,
            'xxl': 1400
        }
        self.mobile_first_breakpoints = [576, 768, 992, 1200, 1400]
    
    def validate_file(self, file_path: Path) -> List[UIIssue]:
        """验证文件的响应式布局"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            issues.extend(self._check_media_queries(file_path, content))
            issues.extend(self._check_flexible_units(file_path, content))
            issues.extend(self._check_viewport_meta(file_path, content))
            issues.extend(self._check_flexbox_grid(file_path, content))
            issues.extend(self._check_touch_targets(file_path, content))
            
        except Exception:
            pass
        
        return issues
    
    def _check_media_queries(self, file_path: Path, content: str) -> List[UIIssue]:
        """检查媒体查询"""
        issues = []
        
        media_queries = re.findall(r'@media\s*\([^)]+\)', content)
        
        if not media_queries and self._has_layout_content(content):
            issues.append(UIIssue(
                file_path=str(file_path),
                line_number=0,
                category=IssueCategory.RESPONSIVE,
                severity=IssueSeverity.WARNING,
                message="未发现媒体查询，可能缺少响应式设计",
                suggestion="添加媒体查询以支持不同屏幕尺寸",
                element="",
                rule_id="responsive-media-query"
            ))
        
        used_breakpoints = set()
        for mq in media_queries:
            for bp_name, bp_value in self.breakpoints.items():
                if str(bp_value) in mq:
                    used_breakpoints.add(bp_name)
        
        if len(used_breakpoints) < 2 and media_queries:
            issues.append(UIIssue(
                file_path=str(file_path),
                line_number=0,
                category=IssueCategory.RESPONSIVE,
                severity=IssueSeverity.INFO,
                message=f"仅使用了 {len(used_breakpoints)} 个断点，建议覆盖更多屏幕尺寸",
                suggestion="考虑添加更多断点以支持平板和桌面设备",
                element="",
                rule_id="responsive-breakpoints"
            ))
        
        return issues
    
    def _check_flexible_units(self, file_path: Path, content: str) -> List[UIIssue]:
        """检查灵活单位使用"""
        issues = []
        
        fixed_widths = re.findall(r'width:\s*(\d+)px', content)
        if len(fixed_widths) > 5:
            issues.append(UIIssue(
                file_path=str(file_path),
                line_number=0,
                category=IssueCategory.RESPONSIVE,
                severity=IssueSeverity.INFO,
                message=f"发现 {len(fixed_widths)} 处固定宽度(px)，建议使用相对单位",
                suggestion="使用 %、rem、em 或 vw/vh 等相对单位",
                element="",
                rule_id="responsive-fixed-width"
            ))
        
        font_sizes_px = re.findall(r'font-size:\s*(\d+)px', content)
        if len(font_sizes_px) > 3:
            issues.append(UIIssue(
                file_path=str(file_path),
                line_number=0,
                category=IssueCategory.RESPONSIVE,
                severity=IssueSeverity.INFO,
                message=f"发现 {len(font_sizes_px)} 处固定字体大小(px)，建议使用rem",
                suggestion="使用 rem 单位以支持用户字体大小偏好",
                element="",
                rule_id="responsive-font-size"
            ))
        
        return issues
    
    def _check_viewport_meta(self, file_path: Path, content: str) -> List[UIIssue]:
        """检查viewport meta标签"""
        issues = []
        
        if '.vue' in str(file_path) or '.html' in str(file_path):
            if 'viewport' not in content and '<meta' in content:
                issues.append(UIIssue(
                    file_path=str(file_path),
                    line_number=0,
                    category=IssueCategory.RESPONSIVE,
                    severity=IssueSeverity.WARNING,
                    message="缺少 viewport meta 标签",
                    suggestion="添加 <meta name='viewport' content='width=device-width, initial-scale=1'>",
                    element="",
                    rule_id="responsive-viewport"
                ))
            
            viewport_match = re.search(r'name=["\']viewport["\'][^>]*content=["\']([^"\']+)["\']', content)
            if viewport_match:
                viewport_content = viewport_match.group(1)
                if 'width=device-width' not in viewport_content:
                    issues.append(UIIssue(
                        file_path=str(file_path),
                        line_number=0,
                        category=IssueCategory.RESPONSIVE,
                        severity=IssueSeverity.WARNING,
                        message="viewport meta 标签缺少 width=device-width",
                        suggestion="确保 viewport 包含 width=device-width",
                        element="",
                        rule_id="responsive-viewport-width"
                    ))
        
        return issues
    
    def _check_flexbox_grid(self, file_path: Path, content: str) -> List[UIIssue]:
        """检查Flexbox和Grid使用"""
        issues = []
        
        has_flex = 'display:' in content and 'flex' in content
        has_grid = 'display:' in content and 'grid' in content
        has_float = 'float:' in content
        
        if has_float and not (has_flex or has_grid):
            issues.append(UIIssue(
                file_path=str(file_path),
                line_number=0,
                category=IssueCategory.BEST_PRACTICE,
                severity=IssueSeverity.INFO,
                message="使用 float 进行布局，建议使用 Flexbox 或 Grid",
                suggestion="使用 display: flex 或 display: grid 替代 float 布局",
                element="",
                rule_id="layout-float"
            ))
        
        return issues
    
    def _check_touch_targets(self, file_path: Path, content: str) -> List[UIIssue]:
        """检查触摸目标大小"""
        issues = []
        
        small_buttons = re.findall(r'(?:button|a|\.btn)[^}]*\{[^}]*(?:width|height|padding):\s*(\d+)px[^}]*\}', content, re.IGNORECASE)
        for match in small_buttons:
            size = int(match)
            if size < 44:
                issues.append(UIIssue(
                    file_path=str(file_path),
                    line_number=0,
                    category=IssueCategory.ACCESSIBILITY,
                    severity=IssueSeverity.WARNING,
                    message=f"触摸目标可能过小 ({size}px)，建议至少 44x44px",
                    suggestion="增加按钮/链接的点击区域大小",
                    element="",
                    rule_id="touch-target-size"
                ))
        
        return issues
    
    def _has_layout_content(self, content: str) -> bool:
        """检查是否包含布局内容"""
        layout_indicators = ['display:', 'flex', 'grid', 'width:', 'height:', 'position:']
        return any(indicator in content for indicator in layout_indicators)


class PerformanceChecker:
    """性能检查器 - 新增"""
    
    def __init__(self):
        self.rules = self._load_rules()
    
    def _load_rules(self) -> List[dict]:
        """加载性能检查规则"""
        return [
            {
                "id": "large-bundle",
                "pattern": r'import\s+.*?from\s+["\']([^"\']+)["\']',
                "check": self._check_large_import,
                "message": "可能导入了大型库",
                "suggestion": "考虑使用按需导入或更轻量的替代方案",
                "severity": IssueSeverity.WARNING
            },
            {
                "id": "inline-styles",
                "pattern": r'style=\{',
                "check": lambda m: True,
                "message": "使用内联样式对象",
                "suggestion": "考虑使用 CSS 类或 styled-components 以提高性能",
                "severity": IssueSeverity.INFO
            },
            {
                "id": "image-optimization",
                "pattern": r'<img[^>]*src=["\']([^"\']+)["\']',
                "check": self._check_image_optimization,
                "message": "图片可能未优化",
                "suggestion": "使用 WebP 格式、添加 lazy loading、设置尺寸",
                "severity": IssueSeverity.INFO
            }
        ]
    
    def _check_large_import(self, match) -> bool:
        """检查是否导入大型库"""
        large_libs = ['lodash', 'moment', 'jquery', 'd3', 'chart.js', 'three']
        import_path = match.group(1) if match.lastindex else ""
        return not any(lib in import_path.lower() for lib in large_libs)
    
    def _check_image_optimization(self, match) -> bool:
        """检查图片优化"""
        img_tag = match.group(0)
        has_loading = 'loading=' in img_tag
        has_width = 'width=' in img_tag
        has_height = 'height=' in img_tag
        return has_loading and has_width and has_height
    
    def check_file(self, file_path: Path) -> List[UIIssue]:
        """检查文件性能问题"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            issues.extend(self._check_imports(file_path, content))
            issues.extend(self._check_images(file_path, content))
            issues.extend(self._check_re_render(file_path, content))
            issues.extend(self._check_bundle_size(file_path, content))
            
        except Exception:
            pass
        
        return issues
    
    def _check_imports(self, file_path: Path, content: str) -> List[UIIssue]:
        """检查导入优化"""
        issues = []
        
        lodash_imports = re.findall(r'import\s+.*?from\s+["\']lodash["\']', content)
        if lodash_imports:
            issues.append(UIIssue(
                file_path=str(file_path),
                line_number=0,
                category=IssueCategory.PERFORMANCE,
                severity=IssueSeverity.WARNING,
                message="导入整个 lodash 库",
                suggestion="使用 import { func } from 'lodash-es' 按需导入",
                element="lodash",
                rule_id="perf-lodash"
            ))
        
        moment_imports = re.findall(r'import\s+.*?from\s+["\']moment["\']', content)
        if moment_imports:
            issues.append(UIIssue(
                file_path=str(file_path),
                line_number=0,
                category=IssueCategory.PERFORMANCE,
                severity=IssueSeverity.WARNING,
                message="使用 moment.js（体积较大）",
                suggestion="考虑使用 dayjs 或 date-fns 等轻量替代方案",
                element="moment",
                rule_id="perf-moment"
            ))
        
        return issues
    
    def _check_images(self, file_path: Path, content: str) -> List[UIIssue]:
        """检查图片优化"""
        issues = []
        
        img_tags = re.finditer(r'<img[^>]*>', content)
        for match in img_tags:
            img_tag = match.group(0)
            
            if 'loading=' not in img_tag:
                issues.append(UIIssue(
                    file_path=str(file_path),
                    line_number=content[:match.start()].count('\n') + 1,
                    category=IssueCategory.PERFORMANCE,
                    severity=IssueSeverity.INFO,
                    message="图片缺少 lazy loading",
                    suggestion="添加 loading='lazy' 属性",
                    element=img_tag[:50],
                    rule_id="perf-img-lazy"
                ))
            
            if 'width=' not in img_tag or 'height=' not in img_tag:
                issues.append(UIIssue(
                    file_path=str(file_path),
                    line_number=content[:match.start()].count('\n') + 1,
                    category=IssueCategory.PERFORMANCE,
                    severity=IssueSeverity.INFO,
                    message="图片缺少尺寸属性，可能导致布局偏移",
                    suggestion="添加 width 和 height 属性",
                    element=img_tag[:50],
                    rule_id="perf-img-dimensions"
                ))
            
            src = re.search(r'src=["\']([^"\']+)["\']', img_tag)
            if src and not src.group(1).startswith('data:'):
                if not any(fmt in src.group(1).lower() for fmt in ['.webp', '.avif']):
                    issues.append(UIIssue(
                        file_path=str(file_path),
                        line_number=content[:match.start()].count('\n') + 1,
                        category=IssueCategory.PERFORMANCE,
                        severity=IssueSeverity.INFO,
                        message="图片未使用现代格式",
                        suggestion="考虑使用 WebP 或 AVIF 格式",
                        element=img_tag[:50],
                        rule_id="perf-img-format"
                    ))
        
        return issues
    
    def _check_re_render(self, file_path: Path, content: str) -> List[UIIssue]:
        """检查可能导致重渲染的问题"""
        issues = []
        
        inline_objects = re.findall(r'style=\{\s*\{[^}]+\}\s*\}', content)
        if len(inline_objects) > 3:
            issues.append(UIIssue(
                file_path=str(file_path),
                line_number=0,
                category=IssueCategory.PERFORMANCE,
                severity=IssueSeverity.INFO,
                message=f"发现 {len(inline_objects)} 个内联样式对象",
                suggestion="将样式对象提取到组件外部或使用 useMemo",
                element="",
                rule_id="perf-inline-style-obj"
            ))
        
        inline_functions = re.findall(r'(?:onClick|onChange|onSubmit)=\{\s*(?:\([^)]*\)\s*=>|\(\)\s*=>)', content)
        if len(inline_functions) > 3:
            issues.append(UIIssue(
                file_path=str(file_path),
                line_number=0,
                category=IssueCategory.PERFORMANCE,
                severity=IssueSeverity.INFO,
                message=f"发现 {len(inline_functions)} 个内联函数",
                suggestion="使用 useCallback 缓存回调函数",
                element="",
                rule_id="perf-inline-function"
            ))
        
        return issues
    
    def _check_bundle_size(self, file_path: Path, content: str) -> List[UIIssue]:
        """检查包大小相关问题"""
        issues = []
        
        console_logs = re.findall(r'console\.(log|debug|info|warn|error)', content)
        if len(console_logs) > 5:
            issues.append(UIIssue(
                file_path=str(file_path),
                line_number=0,
                category=IssueCategory.PERFORMANCE,
                severity=IssueSeverity.INFO,
                message=f"发现 {len(console_logs)} 个 console 语句",
                suggestion="生产环境应移除 console 语句",
                element="",
                rule_id="perf-console"
            ))
        
        return issues


class DesignSystemChecker:
    """设计系统规范检查器 - 新增"""
    
    def __init__(self, design_system_config: Optional[Dict] = None):
        self.design_system = design_system_config or self._get_default_design_system()
        self.color_utils = ColorUtils()
    
    def _get_default_design_system(self) -> Dict:
        """获取默认设计系统配置"""
        return {
            "colors": {
                "primary": "#2563EB",
                "secondary": "#3B82F6",
                "accent": "#F97316",
                "background": "#FFFFFF",
                "foreground": "#1E293B",
                "muted": "#64748B",
                "border": "#E2E8F0"
            },
            "spacing": [0, 4, 8, 12, 16, 24, 32, 48, 64, 96],
            "font_sizes": [12, 14, 16, 18, 20, 24, 30, 36, 48],
            "border_radius": [0, 4, 8, 12, 16, 24],
            "shadows": ["sm", "md", "lg", "xl"]
        }
    
    def check_file(self, file_path: Path) -> List[UIIssue]:
        """检查文件的设计系统规范"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            issues.extend(self._check_color_usage(file_path, content))
            issues.extend(self._check_spacing_system(file_path, content))
            issues.extend(self._check_typography(file_path, content))
            issues.extend(self._check_border_radius(file_path, content))
            
        except Exception:
            pass
        
        return issues
    
    def _check_color_usage(self, file_path: Path, content: str) -> List[UIIssue]:
        """检查颜色使用规范"""
        issues = []
        
        css_vars = re.findall(r'var\(--[\w-]+\)', content)
        hardcoded_colors = re.findall(r'(?:color|background|border-color):\s*(#[0-9a-fA-F]{3,8})(?:\s*;|\s*!important)?', content)
        
        if len(hardcoded_colors) > 3 and len(css_vars) < len(hardcoded_colors):
            issues.append(UIIssue(
                file_path=str(file_path),
                line_number=0,
                category=IssueCategory.DESIGN_SYSTEM,
                severity=IssueSeverity.WARNING,
                message=f"发现 {len(hardcoded_colors)} 处硬编码颜色，建议使用设计系统变量",
                suggestion="使用 var(--color-primary) 等设计系统变量",
                element="",
                rule_id="design-color-variables"
            ))
        
        return issues
    
    def _check_spacing_system(self, file_path: Path, content: str) -> List[UIIssue]:
        """检查间距系统"""
        issues = []
        
        spacing_values = re.findall(r'(?:margin|padding|gap):\s*(\d+)(px|rem)', content)
        allowed_spacing = self.design_system["spacing"]
        
        non_standard_spacing = []
        for value, unit in spacing_values:
            if unit == 'px':
                px_value = int(value)
                if px_value not in allowed_spacing and px_value % 4 != 0:
                    non_standard_spacing.append(f"{value}{unit}")
            elif unit == 'rem':
                rem_value = float(value)
                px_equivalent = int(rem_value * 16)
                if px_equivalent not in allowed_spacing:
                    non_standard_spacing.append(f"{value}{unit}")
        
        if len(non_standard_spacing) > 3:
            issues.append(UIIssue(
                file_path=str(file_path),
                line_number=0,
                category=IssueCategory.DESIGN_SYSTEM,
                severity=IssueSeverity.INFO,
                message=f"发现 {len(non_standard_spacing)} 处非标准间距值",
                suggestion=f"使用设计系统标准间距: {allowed_spacing}",
                element=", ".join(non_standard_spacing[:5]),
                rule_id="design-spacing"
            ))
        
        return issues
    
    def _check_typography(self, file_path: Path, content: str) -> List[UIIssue]:
        """检查字体规范"""
        issues = []
        
        font_sizes = re.findall(r'font-size:\s*(\d+)(px|rem|em)', content)
        allowed_sizes = self.design_system["font_sizes"]
        
        non_standard_sizes = []
        for value, unit in font_sizes:
            if unit == 'px':
                px_value = int(value)
                if px_value not in allowed_sizes:
                    non_standard_sizes.append(f"{value}{unit}")
        
        if len(non_standard_sizes) > 3:
            issues.append(UIIssue(
                file_path=str(file_path),
                line_number=0,
                category=IssueCategory.DESIGN_SYSTEM,
                severity=IssueSeverity.INFO,
                message=f"发现 {len(non_standard_sizes)} 处非标准字体大小",
                suggestion=f"使用设计系统标准字体大小: {allowed_sizes}",
                element=", ".join(non_standard_sizes[:5]),
                rule_id="design-typography"
            ))
        
        return issues
    
    def _check_border_radius(self, file_path: Path, content: str) -> List[UIIssue]:
        """检查圆角规范"""
        issues = []
        
        border_radius = re.findall(r'border-radius:\s*(\d+)(px|rem)', content)
        allowed_radius = self.design_system["border_radius"]
        
        non_standard_radius = []
        for value, unit in border_radius:
            if unit == 'px':
                px_value = int(value)
                if px_value not in allowed_radius:
                    non_standard_radius.append(f"{value}{unit}")
        
        if len(non_standard_radius) > 3:
            issues.append(UIIssue(
                file_path=str(file_path),
                line_number=0,
                category=IssueCategory.DESIGN_SYSTEM,
                severity=IssueSeverity.INFO,
                message=f"发现 {len(non_standard_radius)} 处非标准圆角值",
                suggestion=f"使用设计系统标准圆角: {allowed_radius}",
                element=", ".join(non_standard_radius[:5]),
                rule_id="design-border-radius"
            ))
        
        return issues


class ColorContrastChecker:
    """颜色对比度检查器 - 新增"""
    
    def __init__(self):
        self.color_utils = ColorUtils()
        self.min_ratio_aa = 4.5
        self.min_ratio_aaa = 7.0
        self.min_ratio_large_aa = 3.0
    
    def check_file(self, file_path: Path) -> List[UIIssue]:
        """检查文件的颜色对比度"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            issues.extend(self._check_inline_styles(file_path, content))
            issues.extend(self._check_css_rules(file_path, content))
            
        except Exception:
            pass
        
        return issues
    
    def _check_inline_styles(self, file_path: Path, content: str) -> List[UIIssue]:
        """检查内联样式的颜色对比度"""
        issues = []
        
        style_matches = re.finditer(r'style=["\']([^"\']+)["\']', content)
        for match in style_matches:
            style_content = match.group(1)
            colors = self._extract_color_pairs(style_content)
            
            for fg, bg in colors:
                ratio = self.color_utils.calculate_contrast_ratio(fg, bg)
                if ratio < self.min_ratio_aa:
                    issues.append(UIIssue(
                        file_path=str(file_path),
                        line_number=content[:match.start()].count('\n') + 1,
                        category=IssueCategory.COLOR,
                        severity=IssueSeverity.WARNING,
                        message=f"颜色对比度不足 ({ratio:.2f}:1，需要至少 4.5:1)",
                        suggestion=f"调整颜色以提高对比度。前景: {fg}，背景: {bg}",
                        element=match.group(0)[:50],
                        rule_id="color-contrast"
                    ))
        
        return issues
    
    def _check_css_rules(self, file_path: Path, content: str) -> List[UIIssue]:
        """检查CSS规则中的颜色对比度"""
        issues = []
        
        css_rules = re.finditer(r'([^{]+)\{([^}]+)\}', content)
        for match in css_rules:
            selector = match.group(1).strip()
            rules = match.group(2)
            
            colors = self._extract_color_pairs(rules)
            for fg, bg in colors:
                ratio = self.color_utils.calculate_contrast_ratio(fg, bg)
                if ratio < self.min_ratio_aa:
                    issues.append(UIIssue(
                        file_path=str(file_path),
                        line_number=content[:match.start()].count('\n') + 1,
                        category=IssueCategory.COLOR,
                        severity=IssueSeverity.WARNING,
                        message=f"CSS规则颜色对比度不足 ({ratio:.2f}:1)",
                        suggestion=f"选择器: {selector[:30]}",
                        element=f"fg: {fg}, bg: {bg}",
                        rule_id="color-contrast-css"
                    ))
        
        return issues
    
    def _extract_color_pairs(self, style_str: str) -> List[Tuple[str, str]]:
        """从样式字符串中提取颜色对"""
        pairs = []
        
        fg_match = re.search(r'color:\s*(#[0-9a-fA-F]{3,8})', style_str)
        bg_match = re.search(r'background(?:-color)?:\s*(#[0-9a-fA-F]{3,8})', style_str)
        
        if fg_match and bg_match:
            pairs.append((fg_match.group(1), bg_match.group(1)))
        elif fg_match:
            pairs.append((fg_match.group(1), "#FFFFFF"))
        elif bg_match:
            pairs.append(("#000000", bg_match.group(1)))
        
        return pairs


class UIUXProMaxIntegration:
    """ui-ux-pro-max技能集成 - 新增"""
    
    def __init__(self, skill_path: Optional[Path] = None):
        self.skill_path = skill_path or Path(__file__).parent.parent.parent.parent / "ui-ux-pro-max"
        self.bm25_engine = None
        self.design_system_generator = None
        self._load_skill()
    
    def _load_skill(self):
        """加载ui-ux-pro-max技能"""
        try:
            core_path = self.skill_path / "scripts" / "core.py"
            design_path = self.skill_path / "scripts" / "design_system.py"
            
            if core_path.exists():
                import importlib.util
                spec = importlib.util.spec_from_file_location("ui_ux_core", core_path)
                if spec and spec.loader:
                    self.core_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(self.core_module)
            
            if design_path.exists():
                import importlib.util
                spec = importlib.util.spec_from_file_location("design_system", design_path)
                if spec and spec.loader:
                    self.design_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(self.design_module)
                    
        except Exception:
            pass
    
    def get_design_recommendations(self, context: str) -> Dict[str, Any]:
        """获取设计建议"""
        recommendations = {
            "styles": [],
            "colors": [],
            "typography": [],
            "ux_guidelines": []
        }
        
        try:
            if hasattr(self, 'core_module') and hasattr(self.core_module, 'search'):
                style_result = self.core_module.search(context, "style", max_results=3)
                recommendations["styles"] = style_result.get("results", [])
                
                color_result = self.core_module.search(context, "color", max_results=2)
                recommendations["colors"] = color_result.get("results", [])
                
                ux_result = self.core_module.search(context, "ux", max_results=3)
                recommendations["ux_guidelines"] = ux_result.get("results", [])
                
                typo_result = self.core_module.search(context, "typography", max_results=2)
                recommendations["typography"] = typo_result.get("results", [])
        except Exception:
            pass
        
        return recommendations
    
    def generate_design_system(self, project_type: str, project_name: str = None) -> Dict[str, Any]:
        """生成设计系统"""
        try:
            if hasattr(self, 'design_module') and hasattr(self.design_module, 'generate_design_system'):
                result = self.design_module.generate_design_system(project_type, project_name)
                return {"success": True, "design_system": result}
        except Exception:
            pass
        
        return {"success": False, "message": "设计系统生成器不可用"}
    
    def analyze_ui_issues(self, issues: List[UIIssue]) -> Dict[str, Any]:
        """分析UI问题并提供改进建议"""
        analysis = {
            "summary": {},
            "recommendations": [],
            "priority_fixes": []
        }
        
        severity_counts = {}
        category_counts = {}
        
        for issue in issues:
            sev = issue.severity.value
            cat = issue.category.value
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        analysis["summary"] = {
            "total_issues": len(issues),
            "by_severity": severity_counts,
            "by_category": category_counts
        }
        
        critical_issues = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
        error_issues = [i for i in issues if i.severity == IssueSeverity.ERROR]
        
        if critical_issues:
            analysis["priority_fixes"].append({
                "priority": "critical",
                "count": len(critical_issues),
                "message": f"发现 {len(critical_issues)} 个严重问题需要立即修复"
            })
        
        if error_issues:
            analysis["priority_fixes"].append({
                "priority": "high",
                "count": len(error_issues),
                "message": f"发现 {len(error_issues)} 个错误需要优先处理"
            })
        
        if category_counts.get("accessibility", 0) > 5:
            analysis["recommendations"].append({
                "category": "accessibility",
                "message": "可访问性问题较多，建议进行全面的WCAG合规审查"
            })
        
        if category_counts.get("performance", 0) > 3:
            analysis["recommendations"].append({
                "category": "performance",
                "message": "存在性能优化机会，建议优化资源加载和渲染策略"
            })
        
        return analysis


class VisualRegressionDetector:
    """视觉回归检测器"""
    
    def __init__(self, baseline_dir: Path = None):
        self.baseline_dir = baseline_dir or Path("baselines/ui")
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.baseline_file = self.baseline_dir / "component_baselines.json"
        self.baselines: Dict[str, ComponentSnapshot] = {}
        self._load_baselines()
    
    def _load_baselines(self):
        """加载基线数据"""
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for name, info in data.items():
                    self.baselines[name] = ComponentSnapshot(
                        component_name=name,
                        file_path=info['file_path'],
                        content_hash=info['content_hash'],
                        timestamp=datetime.fromisoformat(info['timestamp']),
                        props=info.get('props', []),
                        events=info.get('events', []),
                        slots=info.get('slots', [])
                    )
            except Exception:
                pass
    
    def _save_baselines(self):
        """保存基线数据"""
        data = {}
        for name, snapshot in self.baselines.items():
            data[name] = {
                'file_path': snapshot.file_path,
                'content_hash': snapshot.content_hash,
                'timestamp': snapshot.timestamp.isoformat(),
                'props': snapshot.props,
                'events': snapshot.events,
                'slots': snapshot.slots
            }
        with open(self.baseline_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def create_baseline(self, file_path: Path) -> ComponentSnapshot:
        """创建组件基线"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        props = re.findall(r'props:\s*\{([^}]+)\}', content, re.DOTALL)
        events = re.findall(r'@(\w+)=', content)
        slots = re.findall(r'<slot\s+name=["\']([^"\']+)["\']', content)
        
        snapshot = ComponentSnapshot(
            component_name=file_path.stem,
            file_path=str(file_path),
            content_hash=content_hash,
            timestamp=datetime.now(),
            props=props[0].split(',') if props else [],
            events=events,
            slots=slots
        )
        
        self.baselines[file_path.stem] = snapshot
        self._save_baselines()
        
        return snapshot
    
    def detect_changes(self, file_path: Path) -> Optional[VisualDiff]:
        """检测组件变化"""
        component_name = file_path.stem
        if component_name not in self.baselines:
            return None
        
        baseline = self.baselines[component_name]
        
        with open(file_path, 'r', encoding='utf-8') as f:
            current_content = f.read()
        
        current_hash = hashlib.sha256(current_content.encode()).hexdigest()
        
        if baseline.content_hash == current_hash:
            return VisualDiff(
                component_name=component_name,
                baseline_hash=baseline.content_hash,
                current_hash=current_hash,
                diff_percentage=0.0,
                has_changes=False
            )
        
        changes = []
        current_props = re.findall(r'props:\s*\{([^}]+)\}', current_content, re.DOTALL)
        current_events = re.findall(r'@(\w+)=', current_content)
        
        if current_props and baseline.props:
            new_props = set(current_props[0].split(',')) - set(baseline.props)
            removed_props = set(baseline.props) - set(current_props[0].split(','))
            if new_props:
                changes.append(f"新增属性: {', '.join(new_props)}")
            if removed_props:
                changes.append(f"移除属性: {', '.join(removed_props)}")
        
        new_events = set(current_events) - set(baseline.events)
        if new_events:
            changes.append(f"新增事件: {', '.join(new_events)}")
        
        diff_percentage = self._calculate_diff_percentage(
            baseline.content_hash, current_content
        )
        
        return VisualDiff(
            component_name=component_name,
            baseline_hash=baseline.content_hash,
            current_hash=current_hash,
            diff_percentage=diff_percentage,
            has_changes=True,
            changes=changes
        )
    
    def _calculate_diff_percentage(self, baseline_hash: str, current_content: str) -> float:
        """计算差异百分比"""
        current_hash = hashlib.sha256(current_content.encode()).hexdigest()
        if baseline_hash == current_hash:
            return 0.0
        
        baseline_bytes = bytes.fromhex(baseline_hash)
        current_bytes = bytes.fromhex(current_hash)
        
        diff_count = sum(1 for a, b in zip(baseline_bytes, current_bytes) if a != b)
        return (diff_count / len(baseline_bytes)) * 100


class UIReportGenerator:
    """UI报告生成器 - 增强版"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_html_report(self, result: Dict[str, Any], filename: str = "ui_validation_report.html") -> str:
        """生成HTML格式报告"""
        report_path = self.output_dir / filename
        
        html_content = self._build_html_report(result)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(report_path)
    
    def _build_html_report(self, result: Dict[str, Any]) -> str:
        """构建HTML报告内容"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        severity_colors = {
            "critical": "#dc3545",
            "error": "#fd7e14",
            "warning": "#ffc107",
            "info": "#17a2b8"
        }
        
        category_icons = {
            "accessibility": "♿",
            "consistency": "🔄",
            "visual": "🎨",
            "performance": "⚡",
            "best_practice": "✓",
            "responsive": "📱",
            "design_system": "📐",
            "color": "🎨",
            "typography": "🔤"
        }
        
        issues_html = ""
        for category, issues in result.get("issues", {}).items():
            if issues:
                icon = category_icons.get(category, "📋")
                issues_html += f"""
                <div class="issue-category">
                    <h3>{icon} {category.title()} 问题 ({len(issues)})</h3>
                    <div class="issues-list">
                """
                for issue in issues[:10]:
                    severity = issue.get("severity", "info")
                    color = severity_colors.get(severity, "#6c757d")
                    issues_html += f"""
                    <div class="issue-item severity-{severity}">
                        <div class="issue-header">
                            <span class="severity-badge" style="background-color: {color}">{severity.upper()}</span>
                            <span class="issue-file">{issue.get('file', 'N/A')}</span>
                            {f'<span class="issue-line">Line {issue.get("line", "N/A")}</span>' if issue.get('line') else ''}
                        </div>
                        <div class="issue-message">{issue.get('message', '')}</div>
                        <div class="issue-suggestion">💡 {issue.get('suggestion', '')}</div>
                        {f'<div class="issue-wcag">WCAG Level: {issue.get("wcag_level", "")}</div>' if issue.get('wcag_level') else ''}
                    </div>
                    """
                issues_html += "</div></div>"
        
        recommendations_html = ""
        for rec in result.get("recommendations", []):
            recommendations_html += f"<li>{rec}</li>"
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UI校验报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header .timestamp {{ opacity: 0.8; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .stat-card h3 {{ font-size: 14px; color: #666; margin-bottom: 10px; }}
        .stat-card .value {{ font-size: 32px; font-weight: bold; color: #333; }}
        .stat-card.danger .value {{ color: #dc3545; }}
        .stat-card.warning .value {{ color: #ffc107; }}
        .stat-card.success .value {{ color: #28a745; }}
        .issue-category {{ background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .issue-category h3 {{ font-size: 18px; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #eee; }}
        .issue-item {{ padding: 15px; margin-bottom: 10px; border-radius: 8px; background: #f8f9fa; border-left: 4px solid #ccc; }}
        .issue-item.severity-critical {{ border-left-color: #dc3545; background: #fff5f5; }}
        .issue-item.severity-error {{ border-left-color: #fd7e14; background: #fff8f0; }}
        .issue-item.severity-warning {{ border-left-color: #ffc107; background: #fffdf0; }}
        .issue-item.severity-info {{ border-left-color: #17a2b8; background: #f0faff; }}
        .issue-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }}
        .severity-badge {{ padding: 2px 8px; border-radius: 4px; color: white; font-size: 11px; font-weight: bold; }}
        .issue-file {{ font-family: monospace; font-size: 12px; color: #666; }}
        .issue-line {{ font-size: 12px; color: #999; }}
        .issue-message {{ font-weight: 500; margin-bottom: 5px; }}
        .issue-suggestion {{ font-size: 14px; color: #666; }}
        .issue-wcag {{ font-size: 12px; color: #888; margin-top: 5px; }}
        .recommendations {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .recommendations h3 {{ margin-bottom: 15px; }}
        .recommendations ul {{ list-style: none; }}
        .recommendations li {{ padding: 10px; margin-bottom: 8px; background: #e8f5e9; border-radius: 6px; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎨 UI校验报告</h1>
            <div class="timestamp">生成时间: {timestamp}</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card {'danger' if result.get('total_issues', 0) > 10 else 'warning' if result.get('total_issues', 0) > 0 else 'success'}">
                <h3>总问题数</h3>
                <div class="value">{result.get('total_issues', 0)}</div>
            </div>
            <div class="stat-card {'danger' if result.get('accessibility_issues', 0) > 5 else ''}">
                <h3>♿ 可访问性问题</h3>
                <div class="value">{result.get('accessibility_issues', 0)}</div>
            </div>
            <div class="stat-card">
                <h3>🔄 一致性问题</h3>
                <div class="value">{result.get('consistency_issues', 0)}</div>
            </div>
            <div class="stat-card">
                <h3>📱 响应式问题</h3>
                <div class="value">{result.get('responsive_issues', 0)}</div>
            </div>
            <div class="stat-card">
                <h3>⚡ 性能问题</h3>
                <div class="value">{result.get('performance_issues', 0)}</div>
            </div>
            <div class="stat-card">
                <h3>🎨 视觉变化</h3>
                <div class="value">{result.get('visual_changes', 0)}</div>
            </div>
        </div>
        
        {issues_html}
        
        {f'''<div class="recommendations">
            <h3>💡 改进建议</h3>
            <ul>{recommendations_html}</ul>
        </div>''' if recommendations_html else ''}
        
        <div class="footer">
            由 UI Validation Intelligence 生成 | Sanliu 技能
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def generate_markdown_report(self, result: Dict[str, Any], filename: str = "ui_validation_report.md") -> str:
        """生成Markdown格式报告"""
        report_path = self.output_dir / filename
        
        md_content = self._build_markdown_report(result)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return str(report_path)
    
    def _build_markdown_report(self, result: Dict[str, Any]) -> str:
        """构建Markdown报告内容"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        lines = [
            "# 🎨 UI校验报告",
            "",
            f"**生成时间**: {timestamp}",
            "",
            "## 📊 概览",
            "",
            "| 指标 | 数量 |",
            "|------|------|",
            f"| 总问题数 | {result.get('total_issues', 0)} |",
            f"| ♿ 可访问性问题 | {result.get('accessibility_issues', 0)} |",
            f"| 🔄 一致性问题 | {result.get('consistency_issues', 0)} |",
            f"| 📱 响应式问题 | {result.get('responsive_issues', 0)} |",
            f"| ⚡ 性能问题 | {result.get('performance_issues', 0)} |",
            f"| 🎨 视觉变化 | {result.get('visual_changes', 0)} |",
            ""
        ]
        
        by_severity = result.get("by_severity", {})
        if by_severity:
            lines.extend([
                "### 按严重程度分布",
                "",
                "| 严重程度 | 数量 |",
                "|----------|------|",
                f"| 🔴 Critical | {by_severity.get('critical', 0)} |",
                f"| 🟠 Error | {by_severity.get('error', 0)} |",
                f"| 🟡 Warning | {by_severity.get('warning', 0)} |",
                f"| 🔵 Info | {by_severity.get('info', 0)} |",
                ""
            ])
        
        for category, issues in result.get("issues", {}).items():
            if issues:
                lines.extend([
                    f"## 📋 {category.title()}问题",
                    ""
                ])
                for issue in issues[:10]:
                    lines.extend([
                        f"### {issue.get('message', 'N/A')}",
                        "",
                        f"- **文件**: `{issue.get('file', 'N/A')}`",
                        f"- **行号**: {issue.get('line', 'N/A')}",
                        f"- **严重程度**: {issue.get('severity', 'N/A')}",
                        f"- **建议**: {issue.get('suggestion', 'N/A')}",
                        ""
                    ])
        
        recommendations = result.get("recommendations", [])
        if recommendations:
            lines.extend([
                "## 💡 改进建议",
                ""
            ])
            for rec in recommendations:
                lines.append(f"- {rec}")
            lines.append("")
        
        return "\n".join(lines)
    
    def generate_json_report(self, result: Dict[str, Any], filename: str = "ui_validation_report.json") -> str:
        """生成JSON格式报告"""
        report_path = self.output_dir / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        return str(report_path)


class UIValidationIntelligence(ScriptBase):
    """UI智能校验器 - 增强版"""
    
    def __init__(self):
        super().__init__(
            name="ui_validation_intelligence",
            version="2.0.0",
            description="UI智能校验器 - 支持规范检查、一致性检查、响应式布局验证、性能检查、设计系统集成",
            author="Sanliu"
        )
        self._setup_arguments()
        self.accessibility_checker: Optional[AccessibilityChecker] = None
        self.consistency_checker: Optional[ConsistencyChecker] = None
        self.responsive_validator: Optional[ResponsiveLayoutValidator] = None
        self.visual_detector: Optional[VisualRegressionDetector] = None
        self.performance_checker: Optional[PerformanceChecker] = None
        self.design_system_checker: Optional[DesignSystemChecker] = None
        self.color_contrast_checker: Optional[ColorContrastChecker] = None
        self.ui_ux_integration: Optional[UIUXProMaxIntegration] = None
        self.report_generator: Optional[UIReportGenerator] = None
    
    def _setup_arguments(self):
        """设置命令行参数"""
        self._command_parser.add_argument(
            '--frontend-dir',
            type=str,
            default='./frontend/src',
            help='前端源码目录'
        )
        self._command_parser.add_argument(
            '--output-dir',
            type=str,
            default=str(get_path_config().REPORTS_DIR / "ui_validation"),
            help='报告输出目录'
        )
        self._command_parser.add_argument(
            '--check-all',
            action='store_true',
            help='执行所有检查'
        )
        self._command_parser.add_argument(
            '--accessibility',
            action='store_true',
            help='可访问性检查'
        )
        self._command_parser.add_argument(
            '--consistency',
            action='store_true',
            help='一致性检查'
        )
        self._command_parser.add_argument(
            '--responsive',
            action='store_true',
            help='响应式布局验证'
        )
        self._command_parser.add_argument(
            '--visual-regression',
            action='store_true',
            help='视觉回归检测'
        )
        self._command_parser.add_argument(
            '--performance',
            action='store_true',
            help='性能检查'
        )
        self._command_parser.add_argument(
            '--design-system',
            action='store_true',
            help='设计系统规范检查'
        )
        self._command_parser.add_argument(
            '--color-contrast',
            action='store_true',
            help='颜色对比度检查'
        )
        self._command_parser.add_argument(
            '--create-baseline',
            action='store_true',
            help='创建基线'
        )
        self._command_parser.add_argument(
            '--report-format',
            type=str,
            choices=['html', 'markdown', 'json', 'all'],
            default='html',
            help='报告格式'
        )
        self._command_parser.add_argument(
            '--project-type',
            type=str,
            default='web',
            help='项目类型（用于设计系统建议）'
        )
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """初始化校验器"""
        super().initialize(config)
        self.accessibility_checker = AccessibilityChecker()
        self.consistency_checker = ConsistencyChecker()
        self.responsive_validator = ResponsiveLayoutValidator()
        self.performance_checker = PerformanceChecker()
        self.design_system_checker = DesignSystemChecker()
        self.color_contrast_checker = ColorContrastChecker()
        self.ui_ux_integration = UIUXProMaxIntegration()
        
        output_dir_config = config.get('output_dir')
        if output_dir_config is None:
            try:
                from skillscripts.utils.enhanced_path_config_manager import create_path_manager, OutputType
                _path_mgr = create_path_manager()
                output_dir = _path_mgr.get_output_path(OutputType.REPORT, subdirectory="ui_validation")
            except Exception:
                output_dir = get_path_config().REPORTS_DIR / "ui_validation"
        else:
            output_dir = Path(output_dir_config)
        self.visual_detector = VisualRegressionDetector(output_dir / 'baselines')
        self.report_generator = UIReportGenerator(output_dir)
    
    def validate_inputs(self, *args, **kwargs) -> bool:
        """验证输入参数"""
        frontend_dir = kwargs.get('frontend_dir', './frontend/src')
        frontend_path = Path(frontend_dir)
        if not frontend_path.exists():
            self._logger.warning(f"前端目录不存在: {frontend_dir}")
        return True
    
    def run(self, *args, **kwargs) -> Any:
        """执行UI校验"""
        frontend_dir = kwargs.get('frontend_dir', './frontend/src')
        output_dir_kwarg = kwargs.get('output_dir')
        if output_dir_kwarg is None:
            try:
                from skillscripts.utils.enhanced_path_config_manager import create_path_manager, OutputType
                _path_mgr = create_path_manager()
                output_dir = str(_path_mgr.get_output_path(OutputType.REPORT, subdirectory="ui_validation"))
            except Exception:
                output_dir = get_path_config().REPORTS_DIR / "ui_validation"
        else:
            output_dir = output_dir_kwarg
        check_all = kwargs.get('check_all', False)
        check_accessibility = kwargs.get('accessibility', False)
        check_consistency = kwargs.get('consistency', False)
        check_responsive = kwargs.get('responsive', False)
        visual_regression = kwargs.get('visual_regression', False)
        check_performance = kwargs.get('performance', False)
        check_design_system = kwargs.get('design_system', False)
        check_color_contrast = kwargs.get('color_contrast', False)
        create_baseline = kwargs.get('create_baseline', False)
        report_format = kwargs.get('report_format', 'html')
        project_type = kwargs.get('project_type', 'web')
        
        frontend_path = Path(frontend_dir)
        output_path = Path(output_dir)
        
        self.accessibility_checker = AccessibilityChecker()
        self.consistency_checker = ConsistencyChecker()
        self.responsive_validator = ResponsiveLayoutValidator()
        self.performance_checker = PerformanceChecker()
        self.design_system_checker = DesignSystemChecker()
        self.color_contrast_checker = ColorContrastChecker()
        self.ui_ux_integration = UIUXProMaxIntegration()
        self.visual_detector = VisualRegressionDetector(output_path / 'baselines')
        self.report_generator = UIReportGenerator(output_path)
        
        self._logger.info(f"开始UI校验 - 目标: {frontend_dir}")
        self._report.add_section("配置信息", {
            "frontend_dir": frontend_dir,
            "output_dir": output_dir,
            "check_all": check_all,
            "project_type": project_type
        })
        
        vue_files = list(frontend_path.rglob("*.vue")) if frontend_path.exists() else []
        tsx_files = list(frontend_path.rglob("*.tsx")) if frontend_path.exists() else []
        jsx_files = list(frontend_path.rglob("*.jsx")) if frontend_path.exists() else []
        ts_files = list(frontend_path.rglob("*.ts")) if frontend_path.exists() else []
        css_files = list(frontend_path.rglob("*.css")) + list(frontend_path.rglob("*.scss"))
        html_files = list(frontend_path.rglob("*.html")) if frontend_path.exists() else []
        
        all_files = vue_files + tsx_files + jsx_files + ts_files + css_files + html_files
        component_files = vue_files + tsx_files + jsx_files
        
        all_accessibility_issues: List[UIIssue] = []
        all_consistency_issues: List[UIIssue] = []
        all_responsive_issues: List[UIIssue] = []
        all_performance_issues: List[UIIssue] = []
        all_design_system_issues: List[UIIssue] = []
        all_color_issues: List[UIIssue] = []
        all_visual_diffs: List[VisualDiff] = []
        
        if check_all or check_accessibility:
            self._logger.info("执行可访问性检查...")
            for file_path in all_files:
                issues = self.accessibility_checker.check_file(file_path)
                all_accessibility_issues.extend(issues)
            self._logger.info(f"发现 {len(all_accessibility_issues)} 个可访问性问题")
        
        if check_all or check_consistency:
            self._logger.info("执行一致性检查...")
            for file_path in component_files:
                issues = self.consistency_checker.check_consistency(file_path)
                all_consistency_issues.extend(issues)
            self._logger.info(f"发现 {len(all_consistency_issues)} 个一致性问题")
        
        if check_all or check_responsive:
            self._logger.info("执行响应式布局验证...")
            for file_path in component_files + css_files:
                issues = self.responsive_validator.validate_file(file_path)
                all_responsive_issues.extend(issues)
            self._logger.info(f"发现 {len(all_responsive_issues)} 个响应式问题")
        
        if check_all or check_performance:
            self._logger.info("执行性能检查...")
            for file_path in component_files + ts_files:
                issues = self.performance_checker.check_file(file_path)
                all_performance_issues.extend(issues)
            self._logger.info(f"发现 {len(all_performance_issues)} 个性能问题")
        
        if check_all or check_design_system:
            self._logger.info("执行设计系统规范检查...")
            for file_path in component_files + css_files:
                issues = self.design_system_checker.check_file(file_path)
                all_design_system_issues.extend(issues)
            self._logger.info(f"发现 {len(all_design_system_issues)} 个设计系统问题")
        
        if check_all or check_color_contrast:
            self._logger.info("执行颜色对比度检查...")
            for file_path in component_files + css_files:
                issues = self.color_contrast_checker.check_file(file_path)
                all_color_issues.extend(issues)
            self._logger.info(f"发现 {len(all_color_issues)} 个颜色对比度问题")
        
        if visual_regression:
            self._logger.info("执行视觉回归检测...")
            if create_baseline:
                for file_path in component_files:
                    self.visual_detector.create_baseline(file_path)
                self._logger.info(f"已创建 {len(component_files)} 个组件基线")
            else:
                for file_path in component_files:
                    diff = self.visual_detector.detect_changes(file_path)
                    if diff:
                        all_visual_diffs.append(diff)
                changed = len([d for d in all_visual_diffs if d.has_changes])
                self._logger.info(f"检测到 {changed} 个组件有变化")
        
        total_issues = (
            len(all_accessibility_issues) +
            len(all_consistency_issues) +
            len(all_responsive_issues) +
            len(all_performance_issues) +
            len(all_design_system_issues) +
            len(all_color_issues)
        )
        
        all_issues = (
            all_accessibility_issues +
            all_consistency_issues +
            all_responsive_issues +
            all_performance_issues +
            all_design_system_issues +
            all_color_issues
        )
        
        ui_ux_analysis = self.ui_ux_integration.analyze_ui_issues(all_issues)
        design_recommendations = self.ui_ux_integration.get_design_recommendations(project_type)
        
        result = {
            "total_issues": total_issues,
            "accessibility_issues": len(all_accessibility_issues),
            "consistency_issues": len(all_consistency_issues),
            "responsive_issues": len(all_responsive_issues),
            "performance_issues": len(all_performance_issues),
            "design_system_issues": len(all_design_system_issues),
            "color_issues": len(all_color_issues),
            "visual_changes": len([d for d in all_visual_diffs if d.has_changes]),
            "by_severity": self._count_by_severity(all_issues),
            "by_category": self._count_by_category(all_issues),
            "issues": {
                "accessibility": [self._format_issue(i) for i in all_accessibility_issues[:20]],
                "consistency": [self._format_issue(i) for i in all_consistency_issues[:20]],
                "responsive": [self._format_issue(i) for i in all_responsive_issues[:20]],
                "performance": [self._format_issue(i) for i in all_performance_issues[:20]],
                "design_system": [self._format_issue(i) for i in all_design_system_issues[:20]],
                "color": [self._format_issue(i) for i in all_color_issues[:20]]
            },
            "visual_diffs": [self._format_diff(d) for d in all_visual_diffs],
            "recommendations": self._generate_recommendations(
                all_accessibility_issues,
                all_consistency_issues,
                all_responsive_issues,
                all_performance_issues,
                all_design_system_issues,
                all_color_issues,
                all_visual_diffs
            ),
            "ui_ux_analysis": ui_ux_analysis,
            "design_recommendations": design_recommendations,
            "files_checked": len(all_files),
            "timestamp": datetime.now().isoformat()
        }
        
        self._report.add_section("校验结果", {
            "total_issues": total_issues,
            "accessibility_issues": len(all_accessibility_issues),
            "consistency_issues": len(all_consistency_issues),
            "responsive_issues": len(all_responsive_issues),
            "performance_issues": len(all_performance_issues),
            "design_system_issues": len(all_design_system_issues),
            "color_issues": len(all_color_issues),
            "visual_changes": result["visual_changes"]
        })
        
        if report_format in ['html', 'all']:
            html_path = self.report_generator.generate_html_report(result)
            result["html_report"] = html_path
            self._logger.info(f"HTML报告已生成: {html_path}")
        
        if report_format in ['markdown', 'all']:
            md_path = self.report_generator.generate_markdown_report(result)
            result["markdown_report"] = md_path
            self._logger.info(f"Markdown报告已生成: {md_path}")
        
        if report_format in ['json', 'all']:
            json_path = self.report_generator.generate_json_report(result)
            result["json_report"] = json_path
            self._logger.info(f"JSON报告已生成: {json_path}")
        
        return result
    
    def _count_by_severity(self, issues: List[UIIssue]) -> Dict[str, int]:
        """按严重程度统计问题"""
        counts = {s.value: 0 for s in IssueSeverity}
        for issue in issues:
            counts[issue.severity.value] += 1
        return counts
    
    def _count_by_category(self, issues: List[UIIssue]) -> Dict[str, int]:
        """按类别统计问题"""
        counts = {c.value: 0 for c in IssueCategory}
        for issue in issues:
            counts[issue.category.value] += 1
        return counts
    
    def _format_issue(self, issue: UIIssue) -> Dict[str, Any]:
        """格式化问题信息"""
        return {
            "file": issue.file_path,
            "line": issue.line_number,
            "category": issue.category.value,
            "severity": issue.severity.value,
            "message": issue.message,
            "suggestion": issue.suggestion,
            "element": issue.element,
            "rule_id": issue.rule_id,
            "wcag_level": issue.wcag_level,
            "fix_code": issue.fix_code
        }
    
    def _format_diff(self, diff: VisualDiff) -> Dict[str, Any]:
        """格式化视觉差异信息"""
        return {
            "component": diff.component_name,
            "has_changes": diff.has_changes,
            "diff_percentage": diff.diff_percentage,
            "changes": diff.changes
        }
    
    def _generate_recommendations(
        self,
        accessibility_issues: List[UIIssue],
        consistency_issues: List[UIIssue],
        responsive_issues: List[UIIssue],
        performance_issues: List[UIIssue],
        design_system_issues: List[UIIssue],
        color_issues: List[UIIssue],
        visual_diffs: List[VisualDiff]
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        critical_accessibility = [
            i for i in accessibility_issues if i.severity == IssueSeverity.CRITICAL
        ]
        if critical_accessibility:
            recommendations.append(
                f"🔴 发现 {len(critical_accessibility)} 个严重的可访问性问题，请优先修复"
            )
        
        error_accessibility = [
            i for i in accessibility_issues if i.severity == IssueSeverity.ERROR
        ]
        if error_accessibility:
            recommendations.append(
                f"🟠 发现 {len(error_accessibility)} 个可访问性错误，建议尽快修复"
            )
        
        wcag_a_issues = [i for i in accessibility_issues if i.wcag_level == "A"]
        if wcag_a_issues:
            recommendations.append(
                f"♿ 发现 {len(wcag_a_issues)} 个WCAG A级问题，这是最低可访问性标准"
            )
        
        if len(consistency_issues) > 10:
            recommendations.append(
                "🔄 发现较多一致性问题，建议统一组件使用规范"
            )
        
        if len(responsive_issues) > 5:
            recommendations.append(
                "📱 发现较多响应式问题，建议优化移动端适配"
            )
        
        if len(performance_issues) > 5:
            recommendations.append(
                "⚡ 发现较多性能问题，建议优化资源加载和渲染策略"
            )
        
        if len(design_system_issues) > 5:
            recommendations.append(
                "📐 发现较多设计系统规范问题，建议统一使用设计系统变量"
            )
        
        if len(color_issues) > 3:
            recommendations.append(
                "🎨 发现颜色对比度问题，建议检查文本可读性"
            )
        
        changed_components = [d for d in visual_diffs if d.has_changes]
        if changed_components:
            recommendations.append(
                f"🖼️ {len(changed_components)} 个组件发生视觉变化，请确认是否符合预期"
            )
        
        if not recommendations:
            recommendations.append("✅ UI校验通过，未发现明显问题")
        
        return recommendations
    
    def cleanup(self) -> None:
        """清理资源"""
        self._logger.info("清理UI校验器资源")


def main():
    """主函数"""
    validator = UIValidationIntelligence()
    result = validator.run_from_command_line()
    
    print("\n" + "=" * 60)
    print("🎨 UI校验报告")
    print("=" * 60)
    print(f"总问题数: {result.data.get('total_issues', 0)}")
    print(f"♿ 可访问性问题: {result.data.get('accessibility_issues', 0)}")
    print(f"🔄 一致性问题: {result.data.get('consistency_issues', 0)}")
    print(f"📱 响应式问题: {result.data.get('responsive_issues', 0)}")
    print(f"⚡ 性能问题: {result.data.get('performance_issues', 0)}")
    print(f"📐 设计系统问题: {result.data.get('design_system_issues', 0)}")
    print(f"🎨 颜色问题: {result.data.get('color_issues', 0)}")
    print(f"🖼️ 视觉变化: {result.data.get('visual_changes', 0)}")
    
    if result.data.get('recommendations'):
        print("\n💡 建议:")
        for rec in result.data['recommendations']:
            print(f"  {rec}")
    
    if result.data.get('html_report'):
        print(f"\n📄 HTML报告: {result.data.get('html_report')}")
    
    print("=" * 60)
    
    if result.data.get('total_issues', 0) > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
