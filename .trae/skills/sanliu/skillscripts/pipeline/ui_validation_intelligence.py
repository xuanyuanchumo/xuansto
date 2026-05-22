#!/usr/bin/env python3
"""
UI校验智能系统 - Sanliu 技能

功能：
- UI规范检查（组件规范、样式规范、布局规范）
- UI报告自动生成（多格式支持）
- ui-ux-pro-max技能集成
- 可访问性检查（WCAG标准）
- 响应式设计验证
- 性能优化建议
- 设计一致性检查
- UX模式检测

使用方法：
    python ui_validation_intelligence.py --help
    python ui_validation_intelligence.py --target frontend/src
    python ui_validation_intelligence.py --target frontend/src --report html
    python ui_validation_intelligence.py --target frontend/src --check-accessibility
    python ui_validation_intelligence.py --target frontend/src --integrate-ui-ux
"""

import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from skillscripts.core.script_base import ScriptBase, ReportFormat, ScriptResult, ScriptStatus


class SeverityLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationCategory(Enum):
    ACCESSIBILITY = "accessibility"
    RESPONSIVE = "responsive"
    PERFORMANCE = "performance"
    CONSISTENCY = "consistency"
    USABILITY = "usability"
    DESIGN_SYSTEM = "design_system"
    COMPONENT = "component"
    LAYOUT = "layout"
    INTERACTION = "interaction"
    ANIMATION = "animation"


class WCAGLevel(Enum):
    A = "A"
    AA = "AA"
    AAA = "AAA"


@dataclass
class UIIssue:
    category: ValidationCategory
    severity: SeverityLevel
    message: str
    file_path: str
    line: Optional[int] = None
    column: Optional[int] = None
    suggestion: str = ""
    wcag_criterion: Optional[str] = None
    fix_example: str = ""


@dataclass
class ComponentSpec:
    name: str
    file_path: str
    has_props_validation: bool = False
    has_accessibility_labels: bool = False
    has_responsive_styles: bool = False
    has_loading_state: bool = False
    has_error_state: bool = False
    has_hover_state: bool = False
    has_focus_state: bool = False
    has_disabled_state: bool = False
    uses_design_tokens: bool = False
    has_unit_tests: bool = False


@dataclass
class ValidationResult:
    total_files: int = 0
    total_issues: int = 0
    issues: List[UIIssue] = field(default_factory=list)
    components: List[ComponentSpec] = field(default_factory=list)
    accessibility_score: float = 0.0
    responsive_score: float = 0.0
    performance_score: float = 0.0
    consistency_score: float = 0.0
    usability_score: float = 0.0
    overall_score: float = 0.0
    wcag_compliance: Dict[str, bool] = field(default_factory=dict)
    design_tokens_used: List[str] = field(default_factory=list)
    ux_patterns_detected: List[str] = field(default_factory=list)


class UIUXProMaxIntegration:
    """ui-ux-pro-max 技能集成"""
    
    SKILL_PATH = Path(".trae/skills/ui-ux-pro-max-skill-main/.claude/skills/ui-ux-pro-max/SKILL.md")
    
    DESIGN_PRINCIPLES = {
        "visual_hierarchy": {
            "description": "视觉层次",
            "checks": ["heading_order", "font_size_hierarchy", "color_contrast_hierarchy"]
        },
        "consistency": {
            "description": "一致性",
            "checks": ["naming_convention", "component_structure", "spacing_consistency"]
        },
        "feedback": {
            "description": "反馈",
            "checks": ["loading_states", "error_states", "success_states", "hover_effects"]
        },
        "accessibility": {
            "description": "可访问性",
            "checks": ["aria_labels", "keyboard_navigation", "color_contrast", "focus_indicators"]
        },
        "responsiveness": {
            "description": "响应式",
            "checks": ["breakpoints", "flexible_layouts", "touch_targets"]
        }
    }
    
    COMPONENT_PATTERNS = {
        "button": {
            "required_props": ["onClick", "children"],
            "recommended_props": ["disabled", "loading", "aria-label"],
            "states": ["default", "hover", "active", "disabled", "loading", "focus"]
        },
        "input": {
            "required_props": ["value", "onChange"],
            "recommended_props": ["label", "placeholder", "error", "disabled"],
            "states": ["default", "focus", "error", "disabled", "filled"]
        },
        "modal": {
            "required_props": ["isOpen", "onClose"],
            "recommended_props": ["title", "aria-labelledby", "closeOnOverlayClick"],
            "accessibility": ["focus_trap", "escape_close", "overlay_click_close"]
        },
        "card": {
            "recommended_props": ["title", "description", "image"],
            "states": ["default", "hover", "selected"]
        },
        "form": {
            "required_props": ["onSubmit"],
            "recommended_props": ["validation", "errorHandling"],
            "accessibility": ["form_labels", "error_announcements", "submit_on_enter"]
        }
    }
    
    def __init__(self, logger):
        self.logger = logger
        self.design_system: Optional[Dict[str, Any]] = None
    
    def load_design_system(self, project_path: Path) -> Optional[Dict[str, Any]]:
        design_system_paths = [
            project_path / "design-system.json",
            project_path / "design" / "tokens.json",
            project_path / "src" / "styles" / "design-tokens.css",
            project_path / "tailwind.config.js"
        ]
        
        for path in design_system_paths:
            if path.exists():
                try:
                    if path.suffix == ".json":
                        self.design_system = json.loads(path.read_text(encoding='utf-8'))
                    elif path.suffix == ".js":
                        content = path.read_text(encoding='utf-8')
                        self.design_system = self._parse_tailwind_config(content)
                    return self.design_system
                except Exception as e:
                    self.logger.warning(f"Failed to load design system from {path}: {e}")
        
        return None
    
    def _parse_tailwind_config(self, content: str) -> Dict[str, Any]:
        design_system = {"colors": {}, "spacing": {}, "typography": {}}
        
        color_match = re.search(r'colors:\s*\{([^}]+)\}', content, re.DOTALL)
        if color_match:
            colors_str = color_match.group(1)
            color_pairs = re.findall(r"(\w+):\s*['\"]([^'\"]+)['\"]", colors_str)
            for name, value in color_pairs:
                design_system["colors"][name] = value
        
        return design_system
    
    def validate_component(self, component_name: str, component_content: str, 
                          file_path: str) -> List[UIIssue]:
        issues = []
        
        pattern = self.COMPONENT_PATTERNS.get(component_name.lower())
        if not pattern:
            return issues
        
        for prop in pattern.get("required_props", []):
            prop_patterns = [
                rf'{prop}=',
                rf'{prop}={{',
                rf':{prop}='
            ]
            if not any(re.search(p, component_content) for p in prop_patterns):
                issues.append(UIIssue(
                    category=ValidationCategory.COMPONENT,
                    severity=SeverityLevel.ERROR,
                    message=f"组件缺少必需属性: {prop}",
                    file_path=file_path,
                    suggestion=f"添加 {prop} 属性以满足组件规范"
                ))
        
        for prop in pattern.get("recommended_props", []):
            prop_patterns = [
                rf'{prop}=',
                rf'{prop}={{',
                rf':{prop}='
            ]
            if not any(re.search(p, component_content) for p in prop_patterns):
                issues.append(UIIssue(
                    category=ValidationCategory.COMPONENT,
                    severity=SeverityLevel.WARNING,
                    message=f"组件建议添加属性: {prop}",
                    file_path=file_path,
                    suggestion=f"考虑添加 {prop} 属性以改善用户体验"
                ))
        
        for state in pattern.get("states", []):
            state_patterns = [
                rf'{state}',
                rf'is{state.capitalize()}',
                rf'_{state}',
                rf':{state}'
            ]
        
        return issues
    
    def check_design_principle(self, principle: str, content: str, 
                               file_path: str) -> List[UIIssue]:
        issues = []
        principle_config = self.DESIGN_PRINCIPLES.get(principle)
        
        if not principle_config:
            return issues
        
        for check in principle_config["checks"]:
            if check == "heading_order":
                headings = re.findall(r'<h([1-6])', content)
                if headings:
                    levels = [int(h) for h in headings]
                    for i in range(len(levels) - 1):
                        if levels[i+1] > levels[i] + 1:
                            issues.append(UIIssue(
                                category=ValidationCategory.ACCESSIBILITY,
                                severity=SeverityLevel.WARNING,
                                message=f"标题层级跳跃: h{levels[i]} 到 h{levels[i+1]}",
                                file_path=file_path,
                                suggestion="保持标题层级连续，不要跳过层级",
                                wcag_criterion="1.3.1"
                            ))
            
            elif check == "color_contrast_hierarchy":
                pass
            
            elif check == "loading_states":
                if "onClick" in content or "onSubmit" in content:
                    if "loading" not in content.lower() and "isLoading" not in content:
                        issues.append(UIIssue(
                            category=ValidationCategory.USABILITY,
                            severity=SeverityLevel.WARNING,
                            message="交互组件缺少加载状态",
                            file_path=file_path,
                            suggestion="添加加载状态以改善用户体验"
                        ))
            
            elif check == "error_states":
                if "<form" in content or "<input" in content:
                    if "error" not in content.lower():
                        issues.append(UIIssue(
                            category=ValidationCategory.USABILITY,
                            severity=SeverityLevel.WARNING,
                            message="表单组件缺少错误状态处理",
                            file_path=file_path,
                            suggestion="添加错误状态显示和验证"
                        ))
            
            elif check == "aria_labels":
                interactive_elements = re.findall(r'<(button|input|select|textarea|a)\s', content)
                for elem in interactive_elements:
                    if f'<{elem}' in content and 'aria-label' not in content and 'aria-labelledby' not in content:
                        issues.append(UIIssue(
                            category=ValidationCategory.ACCESSIBILITY,
                            severity=SeverityLevel.WARNING,
                            message=f"交互元素 <{elem}> 缺少ARIA标签",
                            file_path=file_path,
                            suggestion="添加 aria-label 或 aria-labelledby 属性",
                            wcag_criterion="4.1.2"
                        ))
                        break
            
            elif check == "focus_indicators":
                if "onClick" in content or "onKeyDown" in content:
                    if "focus" not in content.lower() and ":focus" not in content:
                        issues.append(UIIssue(
                            category=ValidationCategory.ACCESSIBILITY,
                            severity=SeverityLevel.WARNING,
                            message="交互元素缺少焦点指示器",
                            file_path=file_path,
                            suggestion="添加 :focus 样式以改善键盘导航体验",
                            wcag_criterion="2.4.7"
                        ))
        
        return issues


class AccessibilityChecker:
    """可访问性检查器"""
    
    WCAG_CRITERIA = {
        "1.1.1": {"level": WCAGLevel.A, "name": "非文本内容"},
        "1.3.1": {"level": WCAGLevel.A, "name": "信息和关系"},
        "1.4.3": {"level": WCAGLevel.AA, "name": "对比度（最小值）"},
        "2.1.1": {"level": WCAGLevel.A, "name": "键盘"},
        "2.4.7": {"level": WCAGLevel.AA, "name": "焦点可见"},
        "4.1.2": {"level": WCAGLevel.A, "name": "名称、角色、值"}
    }
    
    def __init__(self, logger):
        self.logger = logger
    
    def check_file(self, file_path: Path, content: str) -> List[UIIssue]:
        issues = []
        
        issues.extend(self._check_images(content, file_path))
        issues.extend(self._check_forms(content, file_path))
        issues.extend(self._check_headings(content, file_path))
        issues.extend(self._check_links(content, file_path))
        issues.extend(self._check_keyboard(content, file_path))
        issues.extend(self._check_aria(content, file_path))
        issues.extend(self._check_color_contrast(content, file_path))
        
        return issues
    
    def _check_images(self, content: str, file_path: Path) -> List[UIIssue]:
        issues = []
        
        img_pattern = r'<img[^>]*>'
        imgs = re.findall(img_pattern, content)
        
        for img in imgs:
            if 'alt=' not in img:
                issues.append(UIIssue(
                    category=ValidationCategory.ACCESSIBILITY,
                    severity=SeverityLevel.ERROR,
                    message="图片缺少alt属性",
                    file_path=str(file_path),
                    suggestion="添加描述性alt属性，装饰性图片使用alt=\"\"",
                    wcag_criterion="1.1.1"
                ))
        
        return issues
    
    def _check_forms(self, content: str, file_path: Path) -> List[UIIssue]:
        issues = []
        
        input_pattern = r'<input[^>]*>'
        inputs = re.findall(input_pattern, content)
        
        for inp in inputs:
            input_type = re.search(r'type=["\']([^"\']+)["\']', inp)
            if input_type and input_type.group(1) in ['text', 'email', 'password', 'tel', 'number']:
                input_id = re.search(r'id=["\']([^"\']+)["\']', inp)
                input_name = re.search(r'name=["\']([^"\']+)["\']', inp)
                
                if input_id:
                    label_pattern = rf'<label[^>]*for=["\']?{input_id.group(1)}["\']?'
                    if not re.search(label_pattern, content):
                        if 'aria-label' not in inp and 'aria-labelledby' not in inp:
                            issues.append(UIIssue(
                                category=ValidationCategory.ACCESSIBILITY,
                                severity=SeverityLevel.ERROR,
                                message="表单输入缺少关联标签",
                                file_path=str(file_path),
                                suggestion="添加label元素或aria-label属性",
                                wcag_criterion="1.3.1"
                            ))
        
        return issues
    
    def _check_headings(self, content: str, file_path: Path) -> List[UIIssue]:
        issues = []
        
        headings = re.findall(r'<h([1-6])[^>]*>', content)
        if headings:
            levels = [int(h) for h in headings]
            
            if levels[0] != 1:
                issues.append(UIIssue(
                    category=ValidationCategory.ACCESSIBILITY,
                    severity=SeverityLevel.WARNING,
                    message="页面应该从h1开始",
                    file_path=str(file_path),
                    suggestion="确保页面有且仅有一个h1标题",
                    wcag_criterion="1.3.1"
                ))
            
            for i in range(len(levels) - 1):
                if levels[i+1] > levels[i] + 1:
                    issues.append(UIIssue(
                        category=ValidationCategory.ACCESSIBILITY,
                        severity=SeverityLevel.WARNING,
                        message=f"标题层级跳跃: h{levels[i]} 到 h{levels[i+1]}",
                        file_path=str(file_path),
                        suggestion="保持标题层级连续",
                        wcag_criterion="1.3.1"
                    ))
        
        return issues
    
    def _check_links(self, content: str, file_path: Path) -> List[UIIssue]:
        issues = []
        
        link_pattern = r'<a[^>]*>([^<]*)</a>'
        links = re.findall(link_pattern, content)
        
        for link_text in links:
            if not link_text.strip() or link_text.strip() in ['点击这里', '更多', 'click here', 'more']:
                issues.append(UIIssue(
                    category=ValidationCategory.ACCESSIBILITY,
                    severity=SeverityLevel.WARNING,
                    message="链接文本不够描述性",
                    file_path=str(file_path),
                    suggestion="使用描述性链接文本，避免'点击这里'等模糊文本",
                    wcag_criterion="2.4.4"
                ))
        
        return issues
    
    def _check_keyboard(self, content: str, file_path: Path) -> List[UIIssue]:
        issues = []
        
        onclick_pattern = r'onClick=\{[^}]+\}'
        onclicks = re.findall(onclick_pattern, content)
        
        for _ in onclicks:
            if 'onKeyDown' not in content and 'onKeyPress' not in content:
                issues.append(UIIssue(
                    category=ValidationCategory.ACCESSIBILITY,
                    severity=SeverityLevel.WARNING,
                    message="onClick事件缺少键盘事件支持",
                    file_path=str(file_path),
                    suggestion="添加onKeyDown事件处理以支持键盘操作",
                    wcag_criterion="2.1.1"
                ))
                break
        
        return issues
    
    def _check_aria(self, content: str, file_path: Path) -> List[UIIssue]:
        issues = []
        
        role_pattern = r'role=["\']([^"\']+)["\']'
        roles = re.findall(role_pattern, content)
        
        required_aria = {
            "button": ["aria-label", "aria-pressed"],
            "checkbox": ["aria-checked"],
            "dialog": ["aria-labelledby", "aria-modal"],
            "tablist": ["aria-label"],
            "tab": ["aria-selected", "aria-controls"],
            "progressbar": ["aria-valuenow", "aria-valuemin", "aria-valuemax"]
        }
        
        for role in roles:
            if role in required_aria:
                for aria_attr in required_aria[role]:
                    if aria_attr not in content:
                        issues.append(UIIssue(
                            category=ValidationCategory.ACCESSIBILITY,
                            severity=SeverityLevel.WARNING,
                            message=f"角色 '{role}' 缺少 {aria_attr} 属性",
                            file_path=str(file_path),
                            suggestion=f"添加 {aria_attr} 属性以完整描述元素状态",
                            wcag_criterion="4.1.2"
                        ))
        
        return issues
    
    def _check_color_contrast(self, content: str, file_path: Path) -> List[UIIssue]:
        issues = []
        
        low_contrast_patterns = [
            (r'text-gray-[34]00', 'bg-white', "灰色文字在白色背景上对比度可能不足"),
            (r'text-gray-[23]00', 'bg-gray-100', "浅灰色文字在浅灰色背景上对比度不足"),
        ]
        
        for text_pattern, bg_pattern, message in low_contrast_patterns:
            if re.search(text_pattern, content) and re.search(bg_pattern, content):
                issues.append(UIIssue(
                    category=ValidationCategory.ACCESSIBILITY,
                    severity=SeverityLevel.WARNING,
                    message=message,
                    file_path=str(file_path),
                    suggestion="确保文字与背景对比度至少达到4.5:1（WCAG AA标准）",
                    wcag_criterion="1.4.3"
                ))
        
        return issues


class ResponsiveChecker:
    """响应式设计检查器"""
    
    BREAKPOINTS = {
        "sm": 640,
        "md": 768,
        "lg": 1024,
        "xl": 1280,
        "2xl": 1536
    }
    
    def __init__(self, logger):
        self.logger = logger
    
    def check_file(self, file_path: Path, content: str) -> List[UIIssue]:
        issues = []
        
        issues.extend(self._check_viewport(content, file_path))
        issues.extend(self._check_responsive_classes(content, file_path))
        issues.extend(self._check_fixed_sizes(content, file_path))
        issues.extend(self._check_touch_targets(content, file_path))
        
        return issues
    
    def _check_viewport(self, content: str, file_path: Path) -> List[UIIssue]:
        issues = []
        
        if file_path.suffix in ['.html', '.tsx', '.jsx']:
            if '<head' in content and 'viewport' not in content:
                issues.append(UIIssue(
                    category=ValidationCategory.RESPONSIVE,
                    severity=SeverityLevel.ERROR,
                    message="缺少viewport meta标签",
                    file_path=str(file_path),
                    suggestion="添加 <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
                ))
        
        return issues
    
    def _check_responsive_classes(self, content: str, file_path: Path) -> List[UIIssue]:
        issues = []
        
        responsive_prefixes = ['sm:', 'md:', 'lg:', 'xl:', '2xl:']
        has_responsive = any(prefix in content for prefix in responsive_prefixes)
        
        has_layout = any(p in content for p in ['flex', 'grid', 'container'])
        
        if has_layout and not has_responsive:
            issues.append(UIIssue(
                category=ValidationCategory.RESPONSIVE,
                severity=SeverityLevel.WARNING,
                message="布局组件缺少响应式断点",
                file_path=str(file_path),
                suggestion="添加响应式断点类名以支持不同屏幕尺寸"
            ))
        
        return issues
    
    def _check_fixed_sizes(self, content: str, file_path: Path) -> List[UIIssue]:
        issues = []
        
        fixed_width = re.findall(r'width:\s*(\d+)px', content)
        fixed_height = re.findall(r'height:\s*(\d+)px', content)
        
        large_fixed = [w for w in fixed_width if int(w) > 500]
        if large_fixed:
            issues.append(UIIssue(
                category=ValidationCategory.RESPONSIVE,
                severity=SeverityLevel.INFO,
                message=f"发现固定宽度值: {large_fixed[0]}px",
                file_path=str(file_path),
                suggestion="考虑使用相对单位或max-width替代固定像素值"
            ))
        
        return issues
    
    def _check_touch_targets(self, content: str, file_path: Path) -> List[UIIssue]:
        issues = []
        
        button_pattern = r'<button[^>]*>'
        buttons = re.findall(button_pattern, content)
        
        for _ in buttons:
            if 'p-' not in content and 'padding' not in content:
                issues.append(UIIssue(
                    category=ValidationCategory.USABILITY,
                    severity=SeverityLevel.WARNING,
                    message="按钮可能触摸目标过小",
                    file_path=str(file_path),
                    suggestion="确保触摸目标至少44x44像素"
                ))
                break
        
        return issues


class PerformanceChecker:
    """性能检查器"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def check_file(self, file_path: Path, content: str) -> List[UIIssue]:
        issues = []
        
        issues.extend(self._check_image_optimization(content, file_path))
        issues.extend(self._check_bundle_size(content, file_path))
        issues.extend(self._check_lazy_loading(content, file_path))
        issues.extend(self._check_inline_styles(content, file_path))
        
        return issues
    
    def _check_image_optimization(self, content: str, file_path: Path) -> List[UIIssue]:
        issues = []
        
        img_pattern = r'<img[^>]*>'
        imgs = re.findall(img_pattern, content)
        
        for img in imgs:
            if 'loading=' not in img:
                issues.append(UIssue(
                    category=ValidationCategory.PERFORMANCE,
                    severity=SeverityLevel.INFO,
                    message="图片未使用懒加载",
                    file_path=str(file_path),
                    suggestion="添加 loading=\"lazy\" 属性以延迟加载视口外图片"
                ))
            
            if 'srcset=' not in img and 'sizes=' not in img:
                issues.append(UIssue(
                    category=ValidationCategory.PERFORMANCE,
                    severity=SeverityLevel.INFO,
                    message="图片未使用响应式srcset",
                    file_path=str(file_path),
                    suggestion="使用srcset和sizes属性提供不同尺寸的图片"
                ))
        
        return issues
    
    def _check_bundle_size(self, content: str, file_path: Path) -> List[UIIssue]:
        issues = []
        
        import_count = content.count('import ')
        
        if import_count > 20:
            issues.append(UIIssue(
                category=ValidationCategory.PERFORMANCE,
                severity=SeverityLevel.WARNING,
                message=f"导入数量过多 ({import_count}个)",
                file_path=str(file_path),
                suggestion="考虑代码分割或合并相关导入"
            ))
        
        return issues
    
    def _check_lazy_loading(self, content: str, file_path: Path) -> List[UIIssue]:
        issues = []
        
        if 'React.lazy' not in content and 'lazy' not in content:
            if 'import(' not in content:
                pass
        
        return issues
    
    def _check_inline_styles(self, content: str, file_path: Path) -> List[UIIssue]:
        issues = []
        
        inline_style_count = content.count('style={')
        
        if inline_style_count > 5:
            issues.append(UIssue(
                category=ValidationCategory.PERFORMANCE,
                severity=SeverityLevel.WARNING,
                message=f"内联样式过多 ({inline_style_count}个)",
                file_path=str(file_path),
                suggestion="将样式提取到CSS类或styled-components中"
            ))
        
        return issues


class UIValidationReportGenerator:
    """UI验证报告生成器"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(self, result: ValidationResult, format: str = "html") -> Path:
        if format == "html":
            return self._generate_html_report(result)
        elif format == "json":
            return self._generate_json_report(result)
        elif format == "markdown":
            return self._generate_markdown_report(result)
        else:
            return self._generate_html_report(result)
    
    def _generate_html_report(self, result: ValidationResult) -> Path:
        report_path = self.output_dir / f"ui_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        issues_by_category = defaultdict(list)
        for issue in result.issues:
            issues_by_category[issue.category.value].append(issue)
        
        issues_html = ""
        for category, issues in issues_by_category.items():
            issues_html += f"""
            <div class="category-section">
                <h3>{category.upper()} ({len(issues)} issues)</h3>
                <div class="issues-list">
            """
            for issue in issues[:10]:
                severity_class = f"severity-{issue.severity.value}"
                issues_html += f"""
                    <div class="issue-item {severity_class}">
                        <div class="issue-header">
                            <span class="severity-badge">{issue.severity.value}</span>
                            <span class="file-path">{issue.file_path}</span>
                        </div>
                        <div class="issue-message">{issue.message}</div>
                        {f'<div class="issue-suggestion">💡 {issue.suggestion}</div>' if issue.suggestion else ''}
                    </div>
                """
            issues_html += "</div></div>"
        
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UI验证报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0 0 10px 0; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat-value {{ font-size: 36px; font-weight: bold; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        .score-good {{ color: #10b981; }}
        .score-warning {{ color: #f59e0b; }}
        .score-bad {{ color: #ef4444; }}
        .progress-bar {{ height: 24px; background: #e5e7eb; border-radius: 12px; overflow: hidden; margin: 10px 0; }}
        .progress {{ height: 100%; transition: width 0.3s; border-radius: 12px; }}
        .category-section {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .category-section h3 {{ margin: 0 0 15px 0; color: #374151; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }}
        .issue-item {{ padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid; }}
        .severity-error {{ background: #fef2f2; border-color: #ef4444; }}
        .severity-warning {{ background: #fffbeb; border-color: #f59e0b; }}
        .severity-info {{ background: #eff6ff; border-color: #3b82f6; }}
        .severity-critical {{ background: #fef2f2; border-color: #dc2626; }}
        .severity-badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.75em; font-weight: 600; text-transform: uppercase; background: #e5e7eb; }}
        .file-path {{ color: #6b7280; font-size: 0.85em; margin-left: 10px; }}
        .issue-message {{ font-weight: 500; margin: 8px 0; }}
        .issue-suggestion {{ color: #059669; font-size: 0.9em; margin-top: 5px; }}
        .wcag-section {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .wcag-item {{ display: flex; align-items: center; padding: 10px; border-bottom: 1px solid #e5e7eb; }}
        .wcag-item:last-child {{ border-bottom: none; }}
        .wcag-status {{ width: 24px; height: 24px; border-radius: 50%; margin-right: 10px; }}
        .wcag-pass {{ background: #10b981; }}
        .wcag-fail {{ background: #ef4444; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎨 UI验证报告</h1>
            <p>验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 文件数: {result.total_files}</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value {self._get_score_class(result.overall_score)}">{result.overall_score:.1f}</div>
                <div class="stat-label">综合评分</div>
            </div>
            <div class="stat-card">
                <div class="stat-value {self._get_score_class(result.accessibility_score)}">{result.accessibility_score:.1f}</div>
                <div class="stat-label">可访问性</div>
            </div>
            <div class="stat-card">
                <div class="stat-value {self._get_score_class(result.responsive_score)}">{result.responsive_score:.1f}</div>
                <div class="stat-label">响应式</div>
            </div>
            <div class="stat-card">
                <div class="stat-value {self._get_score_class(result.performance_score)}">{result.performance_score:.1f}</div>
                <div class="stat-label">性能</div>
            </div>
            <div class="stat-card">
                <div class="stat-value {self._get_score_class(result.consistency_score)}">{result.consistency_score:.1f}</div>
                <div class="stat-label">一致性</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{result.total_issues}</div>
                <div class="stat-label">问题总数</div>
            </div>
        </div>
        
        <div class="wcag-section">
            <h3>WCAG合规性</h3>
            <div class="wcag-item">
                <div class="wcag-status {'wcag-pass' if result.wcag_compliance.get('A', False) else 'wcag-fail'}"></div>
                <span>WCAG Level A: {'✅ 通过' if result.wcag_compliance.get('A', False) else '❌ 未通过'}</span>
            </div>
            <div class="wcag-item">
                <div class="wcag-status {'wcag-pass' if result.wcag_compliance.get('AA', False) else 'wcag-fail'}"></div>
                <span>WCAG Level AA: {'✅ 通过' if result.wcag_compliance.get('AA', False) else '❌ 未通过'}</span>
            </div>
            <div class="wcag-item">
                <div class="wcag-status {'wcag-pass' if result.wcag_compliance.get('AAA', False) else 'wcag-fail'}"></div>
                <span>WCAG Level AAA: {'✅ 通过' if result.wcag_compliance.get('AAA', False) else '❌ 未通过'}</span>
            </div>
        </div>
        
        {issues_html}
    </div>
</body>
</html>"""
        
        report_path.write_text(html_content, encoding='utf-8')
        return report_path
    
    def _get_score_class(self, score: float) -> str:
        if score >= 80:
            return "score-good"
        elif score >= 60:
            return "score-warning"
        else:
            return "score-bad"
    
    def _generate_json_report(self, result: ValidationResult) -> Path:
        report_path = self.output_dir / f"ui_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_files": result.total_files,
                "total_issues": result.total_issues,
                "overall_score": result.overall_score,
                "scores": {
                    "accessibility": result.accessibility_score,
                    "responsive": result.responsive_score,
                    "performance": result.performance_score,
                    "consistency": result.consistency_score,
                    "usability": result.usability_score
                },
                "wcag_compliance": result.wcag_compliance
            },
            "issues": [
                {
                    "category": issue.category.value,
                    "severity": issue.severity.value,
                    "message": issue.message,
                    "file": issue.file_path,
                    "line": issue.line,
                    "suggestion": issue.suggestion,
                    "wcag_criterion": issue.wcag_criterion
                }
                for issue in result.issues
            ],
            "components": [
                {
                    "name": comp.name,
                    "file": comp.file_path,
                    "checks": {
                        "props_validation": comp.has_props_validation,
                        "accessibility": comp.has_accessibility_labels,
                        "responsive": comp.has_responsive_styles,
                        "loading_state": comp.has_loading_state,
                        "error_state": comp.has_error_state
                    }
                }
                for comp in result.components
            ]
        }
        
        report_path.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding='utf-8')
        return report_path
    
    def _generate_markdown_report(self, result: ValidationResult) -> Path:
        report_path = self.output_dir / f"ui_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        lines = [
            f"# UI验证报告",
            f"",
            f"**验证时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**文件数**: {result.total_files}",
            f"",
            f"## 📊 评分概览",
            f"",
            f"| 维度 | 分数 |",
            f"|------|------|",
            f"| 综合评分 | {result.overall_score:.1f} |",
            f"| 可访问性 | {result.accessibility_score:.1f} |",
            f"| 响应式 | {result.responsive_score:.1f} |",
            f"| 性能 | {result.performance_score:.1f} |",
            f"| 一致性 | {result.consistency_score:.1f} |",
            f"| 可用性 | {result.usability_score:.1f} |",
            f"",
            f"## ♿ WCAG合规性",
            f"",
        ]
        
        for level in ["A", "AA", "AAA"]:
            status = "✅ 通过" if result.wcag_compliance.get(level, False) else "❌ 未通过"
            lines.append(f"- WCAG Level {level}: {status}")
        
        if result.issues:
            lines.extend([
                f"",
                f"## 🐛 问题列表 ({result.total_issues}个)",
                f""
            ])
            
            issues_by_category = defaultdict(list)
            for issue in result.issues:
                issues_by_category[issue.category.value].append(issue)
            
            for category, issues in issues_by_category.items():
                lines.append(f"### {category.upper()}")
                lines.append("")
                for issue in issues[:10]:
                    lines.append(f"- **[{issue.severity.value}]** {issue.message}")
                    lines.append(f"  - 文件: `{issue.file_path}`")
                    if issue.suggestion:
                        lines.append(f"  - 建议: {issue.suggestion}")
                lines.append("")
        
        report_path.write_text('\n'.join(lines), encoding='utf-8')
        return report_path


class UIValidationIntelligence(ScriptBase):
    """UI验证智能系统主类"""
    
    def __init__(self):
        super().__init__(
            name="ui_validation_intelligence",
            version="1.0.0",
            description="UI验证智能系统 - 支持UI规范检查、报告生成和ui-ux-pro-max集成",
            author="Sanliu"
        )
        self._setup_arguments()
        self.result = ValidationResult()
        self.ui_ux_integration: Optional[UIUXProMaxIntegration] = None
        self.accessibility_checker: Optional[AccessibilityChecker] = None
        self.responsive_checker: Optional[ResponsiveChecker] = None
        self.performance_checker: Optional[PerformanceChecker] = None
        self.report_generator: Optional[UIValidationReportGenerator] = None
    
    def _setup_arguments(self):
        self._command_parser.add_argument(
            '--target',
            type=str,
            default='./frontend/src',
            help='要验证的UI代码目录'
        )
        self._command_parser.add_argument(
            '--output',
            type=str,
            default=str(get_path_config().REPORTS_DIR / "ui_validation",
            help='报告输出目录'
        )
        self._command_parser.add_argument(
            '--report',
            type=str,
            choices=['html', 'json', 'markdown'],
            default='html',
            help='报告格式'
        )
        self._command_parser.add_argument(
            '--check-accessibility',
            action='store_true',
            help='执行可访问性检查'
        )
        self._command_parser.add_argument(
            '--check-responsive',
            action='store_true',
            help='执行响应式检查'
        )
        self._command_parser.add_argument(
            '--check-performance',
            action='store_true',
            help='执行性能检查'
        )
        self._command_parser.add_argument(
            '--check-all',
            action='store_true',
            help='执行所有检查'
        )
        self._command_parser.add_argument(
            '--integrate-ui-ux',
            action='store_true',
            help='集成ui-ux-pro-max技能'
        )
        self._command_parser.add_argument(
            '--wcag-level',
            type=str,
            choices=['A', 'AA', 'AAA'],
            default='AA',
            help='WCAG合规级别'
        )
        self._command_parser.add_argument(
            '--design-system',
            type=str,
            help='设计系统配置文件路径'
        )
    
    def initialize(self, config: Dict[str, Any]) -> None:
        super().initialize(config)
        self.ui_ux_integration = UIUXProMaxIntegration(self._logger)
        self.accessibility_checker = AccessibilityChecker(self._logger)
        self.responsive_checker = ResponsiveChecker(self._logger)
        self.performance_checker = PerformanceChecker(self._logger)
        self.report_generator = UIValidationReportGenerator(Path(config.get('output', str(get_path_config().REPORTS_DIR / 'ui_validation')))
    
    def validate_inputs(self, *args, **kwargs) -> bool:
        target = kwargs.get('target', './frontend/src')
        target_path = Path(target)
        if not target_path.exists():
            self._logger.error(f"目标目录不存在: {target}")
            return False
        return True
    
    def run(self, *args, **kwargs) -> Any:
        target = kwargs.get('target', './frontend/src')
        output = kwargs.get('output', str(get_path_config().REPORTS_DIR / "ui_validation")
        report_format = kwargs.get('report', 'html')
        check_accessibility = kwargs.get('check_accessibility', False)
        check_responsive = kwargs.get('check_responsive', False)
        check_performance = kwargs.get('check_performance', False)
        check_all = kwargs.get('check_all', True)
        integrate_ui_ux = kwargs.get('integrate_ui_ux', False)
        wcag_level = kwargs.get('wcag_level', 'AA')
        design_system_path = kwargs.get('design_system')
        
        target_path = Path(target)
        output_path = Path(output)
        
        self._logger.info(f"开始UI验证 - 目标: {target}")
        self._report.add_section("配置信息", {
            "target": target,
            "output": output,
            "report_format": report_format,
            "check_accessibility": check_accessibility or check_all,
            "check_responsive": check_responsive or check_all,
            "check_performance": check_performance or check_all,
            "wcag_level": wcag_level
        })
        
        self.report_generator = UIValidationReportGenerator(output_path)
        
        if integrate_ui_ux:
            self.ui_ux_integration.load_design_system(target_path)
        
        files_to_check = self._collect_files(target_path)
        self.result.total_files = len(files_to_check)
        self._logger.info(f"找到 {len(files_to_check)} 个文件需要验证")
        
        for file_path in files_to_check:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                if check_accessibility or check_all:
                    issues = self.accessibility_checker.check_file(file_path, content)
                    self.result.issues.extend(issues)
                
                if check_responsive or check_all:
                    issues = self.responsive_checker.check_file(file_path, content)
                    self.result.issues.extend(issues)
                
                if check_performance or check_all:
                    issues = self.performance_checker.check_file(file_path, content)
                    self.result.issues.extend(issues)
                
                if integrate_ui_ux:
                    issues = self.ui_ux_integration.check_design_principle("accessibility", content, str(file_path))
                    self.result.issues.extend(issues)
                    
                    component_issues = self._check_components(file_path, content)
                    self.result.issues.extend(component_issues)
                
            except Exception as e:
                self._logger.warning(f"处理文件 {file_path} 时出错: {e}")
        
        self._calculate_scores()
        self._check_wcag_compliance(wcag_level)
        self.result.total_issues = len(self.result.issues)
        
        report_path = self.report_generator.generate_report(self.result, report_format)
        self._logger.info(f"验证报告已生成: {report_path}")
        
        self._report.add_section("验证结果", {
            "total_files": self.result.total_files,
            "total_issues": self.result.total_issues,
            "overall_score": self.result.overall_score,
            "accessibility_score": self.result.accessibility_score,
            "responsive_score": self.result.responsive_score,
            "performance_score": self.result.performance_score,
            "consistency_score": self.result.consistency_score,
            "report_path": str(report_path)
        })
        
        return {
            "total_files": self.result.total_files,
            "total_issues": self.result.total_issues,
            "overall_score": self.result.overall_score,
            "scores": {
                "accessibility": self.result.accessibility_score,
                "responsive": self.result.responsive_score,
                "performance": self.result.performance_score,
                "consistency": self.result.consistency_score,
                "usability": self.result.usability_score
            },
            "wcag_compliance": self.result.wcag_compliance,
            "report_path": str(report_path)
        }
    
    def _collect_files(self, target_dir: Path) -> List[Path]:
        files = []
        
        extensions = ['.tsx', '.jsx', '.vue', '.html', '.css', '.scss', '.less']
        
        for ext in extensions:
            files.extend(target_dir.rglob(f'*{ext}'))
        
        exclude_patterns = ['node_modules', '.next', 'dist', 'build', '__tests__', '__mocks__']
        files = [f for f in files if not any(p in str(f) for p in exclude_patterns)]
        
        return sorted(files)
    
    def _check_components(self, file_path: Path, content: str) -> List[UIIssue]:
        issues = []
        
        component_pattern = r'(?:export\s+(?:default\s+)?(?:function|const)\s+(\w+)|(?:export\s+default\s+)?class\s+(\w+)\s+extends\s+React\.Component)'
        components = re.findall(component_pattern, content)
        
        for match in components:
            component_name = match[0] or match[1]
            
            if self.ui_ux_integration:
                component_issues = self.ui_ux_integration.validate_component(
                    component_name, content, str(file_path)
                )
                issues.extend(component_issues)
        
        return issues
    
    def _calculate_scores(self):
        if self.result.total_files == 0:
            return
        
        category_weights = {
            ValidationCategory.ACCESSIBILITY: 0.25,
            ValidationCategory.RESPONSIVE: 0.20,
            ValidationCategory.PERFORMANCE: 0.20,
            ValidationCategory.CONSISTENCY: 0.15,
            ValidationCategory.USABILITY: 0.20
        }
        
        category_penalties = defaultdict(float)
        
        for issue in self.result.issues:
            severity_penalty = {
                SeverityLevel.CRITICAL: 10,
                SeverityLevel.ERROR: 5,
                SeverityLevel.WARNING: 2,
                SeverityLevel.INFO: 0.5
            }.get(issue.severity, 1)
            
            category_penalties[issue.category] += severity_penalty
        
        max_penalty_per_category = 50
        
        scores = {}
        for category, weight in category_weights.items():
            penalty = min(category_penalties[category], max_penalty_per_category)
            score = max(0, 100 - penalty)
            scores[category] = score
        
        self.result.accessibility_score = scores.get(ValidationCategory.ACCESSIBILITY, 100)
        self.result.responsive_score = scores.get(ValidationCategory.RESPONSIVE, 100)
        self.result.performance_score = scores.get(ValidationCategory.PERFORMANCE, 100)
        self.result.consistency_score = scores.get(ValidationCategory.CONSISTENCY, 100)
        self.result.usability_score = scores.get(ValidationCategory.USABILITY, 100)
        
        self.result.overall_score = sum(
            score * category_weights.get(cat, 0.1)
            for cat, score in scores.items()
        )
    
    def _check_wcag_compliance(self, target_level: str):
        levels = ["A", "AA", "AAA"]
        target_idx = levels.index(target_level)
        
        critical_issues = [i for i in self.result.issues if i.severity == SeverityLevel.CRITICAL]
        error_issues = [i for i in self.result.issues if i.severity == SeverityLevel.ERROR]
        warning_issues = [i for i in self.result.issues if i.severity == SeverityLevel.WARNING]
        
        self.result.wcag_compliance = {
            "A": len(critical_issues) == 0 and len(error_issues) == 0,
            "AA": len(critical_issues) == 0 and len(error_issues) == 0 and len(warning_issues) < 5,
            "AAA": len(critical_issues) == 0 and len(error_issues) == 0 and len(warning_issues) == 0
        }
    
    def cleanup(self) -> None:
        self._logger.info("清理UI验证器资源")


def main():
    validator = UIValidationIntelligence()
    result = validator.run_from_command_line()
    
    print("\n" + "=" * 60)
    print("UI验证报告")
    print("=" * 60)
    print(f"验证文件数: {result.data.get('total_files', 0)}")
    print(f"问题总数: {result.data.get('total_issues', 0)}")
    print(f"综合评分: {result.data.get('overall_score', 0):.1f}")
    
    scores = result.data.get('scores', {})
    print(f"\n维度评分:")
    print(f"  可访问性: {scores.get('accessibility', 0):.1f}")
    print(f"  响应式: {scores.get('responsive', 0):.1f}")
    print(f"  性能: {scores.get('performance', 0):.1f}")
    print(f"  一致性: {scores.get('consistency', 0):.1f}")
    print(f"  可用性: {scores.get('usability', 0):.1f}")
    
    wcag = result.data.get('wcag_compliance', {})
    print(f"\nWCAG合规性:")
    for level, passed in wcag.items():
        status = "✅" if passed else "❌"
        print(f"  Level {level}: {status}")
    
    print(f"\n报告路径: {result.data.get('report_path', '')}")
    print("=" * 60)
    
    if result.data.get('overall_score', 0) < 60:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
