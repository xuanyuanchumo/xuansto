#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ui-ux-pro-max 集成脚本

用于自动发现需要 UI/UX 设计的任务，调用 ui-ux-pro-max 进行设计，生成 UI 校验报告。

使用方法:
    python scripts/ui_ux_integration.py [command] [options]

命令:
    discover     - 发现需要 UI/UX 设计的任务
    design       - 执行 UI/UX 设计
    validate     - 执行 UI 校验
    system       - 生成设计系统
    review       - UI 代码审查
    report       - 生成 UI 设计报告

示例:
    python scripts/ui_ux_integration.py discover --scope=all
    python scripts/ui_ux_integration.py design --type=page --name=dashboard
    python scripts/ui_ux_integration.py validate --path=src/components/
    python scripts/ui_ux_integration.py system --generate --theme=modern
"""

import os
import re
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from abc import ABC, abstractmethod


UI_UX_REGISTRY_PATH = get_path_config().SKILL_ROOT / "resources" / "waiji_zhuce_biao.md"


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

try:
    from skillscripts.utils.enhanced_path_config_manager import create_path_manager, PathKey
    _path_manager = create_path_manager()
    _log_path = _path_manager.resolve_path(PathKey.LOGS_DIR) / "ui_ux_integration.log"
    logging.getLogger().addHandler(
        logging.FileHandler(str(_log_path), encoding='utf-8', mode='a')
    )
except Exception:
    try:
        from skillscripts.utils.enhanced_path_config_manager import create_path_manager, OutputType
        _fallback_manager = create_path_manager()
        _fallback_log_path = _fallback_manager.get_output_path(OutputType.LOG, filename="ui_ux_integration.log")
        logging.getLogger().addHandler(
            logging.FileHandler(str(_fallback_log_path), encoding='utf-8', mode='a')
        )
    except Exception:
        logging.getLogger().addHandler(
            logging.FileHandler(str(get_path_config().LOGS_DIR / 'ui_ux_integration.log'), encoding='utf-8', mode='a')
        )

logger = logging.getLogger(__name__)


class DesignType(Enum):
    """设计类型"""
    PAGE = "page"
    COMPONENT = "component"
    SYSTEM = "system"
    LAYOUT = "layout"
    THEME = "theme"
    ICON = "icon"
    ANIMATION = "animation"


class ValidationStatus(Enum):
    """校验状态"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    NOT_CHECKED = "not_checked"


class DesignStatus(Enum):
    """设计状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NEEDS_REVISION = "needs_revision"
    ARCHIVED = "archived"


class DesignPriority(Enum):
    """设计优先级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ValidationDimension(Enum):
    """校验维度"""
    ACCESSIBILITY = "accessibility"
    RESPONSIVE = "responsive"
    PERFORMANCE = "performance"
    CONSISTENCY = "consistency"
    USABILITY = "usability"
    SEO = "seo"
    SECURITY = "security"
    INTERACTION = "interaction"
    ANIMATION = "animation"
    COLOR_CONTRAST = "color_contrast"


class UXPattern(Enum):
    """UX模式"""
    ONBOARDING = "onboarding"
    FORM_VALIDATION = "form_validation"
    ERROR_HANDLING = "error_handling"
    LOADING_STATE = "loading_state"
    EMPTY_STATE = "empty_state"
    NAVIGATION = "navigation"
    SEARCH = "search"
    FEEDBACK = "feedback"
    PROGRESSIVE_DISCLOSURE = "progressive_disclosure"
    GESTURE = "gesture"


class ThemeType(Enum):
    """主题类型"""
    MODERN = "modern"
    CLASSIC = "classic"
    MINIMAL = "minimal"
    CORPORATE = "corporate"
    CREATIVE = "creative"
    DARK = "dark"
    LIGHT = "light"


@dataclass
class DesignTask:
    """设计任务"""
    task_id: str
    task_type: DesignType
    name: str
    description: str
    project_type: str
    tech_stack: str
    status: DesignStatus
    priority: DesignPriority = DesignPriority.MEDIUM
    created_at: str = None
    updated_at: str = None
    assigned_to: str = "工部"
    requirements: Dict[str, Any] = None
    design_outputs: List[str] = None
    validation_score: float = 0.0
    theme: ThemeType = ThemeType.MODERN
    tags: List[str] = None
    
    def __post_init__(self):
        if self.design_outputs is None:
            self.design_outputs = []
        if self.requirements is None:
            self.requirements = {}
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()


@dataclass
class DesignToken:
    """设计令牌"""
    name: str
    category: str
    value: str
    description: str = ""
    css_variable: str = ""
    usage: List[str] = None
    
    def __post_init__(self):
        if self.usage is None:
            self.usage = []


@dataclass
class DesignSystem:
    """设计系统"""
    name: str
    version: str
    theme: ThemeType
    colors: Dict[str, str]
    typography: Dict[str, Any]
    spacing: Dict[str, str]
    border_radius: Dict[str, str]
    shadows: Dict[str, str] = None
    breakpoints: Dict[str, str] = None
    tokens: List[DesignToken] = None
    components: Dict[str, Any] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.shadows is None:
            self.shadows = {}
        if self.breakpoints is None:
            self.breakpoints = {}
        if self.tokens is None:
            self.tokens = []
        if self.components is None:
            self.components = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass
class ValidationResult:
    """校验结果"""
    validation_id: str
    target_path: str
    timestamp: str
    overall_status: ValidationStatus
    overall_score: float
    accessibility_score: float
    design_consistency_score: float
    responsive_score: float
    performance_score: float
    usability_score: float = 0.0
    seo_score: float = 0.0
    interaction_score: float = 0.0
    animation_score: float = 0.0
    color_contrast_score: float = 0.0
    issues: List[Dict[str, Any]] = None
    recommendations: List[str] = None
    details: Dict[str, Any] = None
    ux_patterns: List[str] = None
    wcag_compliance: Dict[str, bool] = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.recommendations is None:
            self.recommendations = []
        if self.details is None:
            self.details = {}
        if self.ux_patterns is None:
            self.ux_patterns = []
        if self.wcag_compliance is None:
            self.wcag_compliance = {}


@dataclass
class UIIntegrationLog:
    """UI 集成日志"""
    log_id: str
    timestamp: str
    operation: str
    task_name: str
    project_type: str
    tech_stack: str
    requesting_department: str
    status: str
    duration_ms: int = 0
    design_outputs: List[str] = None
    validation_results: Dict[str, Any] = None
    errors: List[Dict[str, str]] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.design_outputs is None:
            self.design_outputs = []
        if self.validation_results is None:
            self.validation_results = {}
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}


class UIValidator(ABC):
    """UI校验器抽象基类"""
    
    @abstractmethod
    def validate(self, target: Path) -> float:
        """校验目标"""
        pass
    
    @abstractmethod
    def get_issues(self, target: Path) -> List[Dict[str, Any]]:
        """获取校验问题"""
        pass


class AccessibilityValidator(UIValidator):
    """可访问性校验器"""
    
    def validate(self, target: Path) -> float:
        score = 0.9
        
        if target.is_file():
            content = target.read_text(encoding='utf-8')
            
            if '<img' in content and 'alt=' not in content:
                score -= 0.15
            
            if '<button' in content and 'aria-' not in content:
                score -= 0.1
            
            semantic_tags = ['<header', '<nav', '<main', '<article', '<section', '<aside', '<footer']
            semantic_count = sum(1 for tag in semantic_tags if tag in content)
            if semantic_count < 2:
                score -= 0.1
            
            if 'role=' not in content and 'aria-' not in content:
                score -= 0.05
            
            if '<label' not in content and 'htmlFor' not in content:
                if '<input' in content:
                    score -= 0.1
        
        return max(score, 0)
    
    def get_issues(self, target: Path) -> List[Dict[str, Any]]:
        issues = []
        
        if target.is_file():
            content = target.read_text(encoding='utf-8')
            
            if '<img' in content:
                img_count = content.count('<img')
                alt_count = content.count('alt=')
                if alt_count < img_count:
                    issues.append({
                        "type": "accessibility",
                        "severity": "high",
                        "message": f"发现 {img_count - alt_count} 个图片缺少 alt 属性",
                        "line": None,
                        "suggestion": "为所有图片添加描述性 alt 属性"
                    })
            
            if '<input' in content:
                input_count = content.count('<input')
                label_count = content.count('<label') + content.count('htmlFor')
                if label_count < input_count:
                    issues.append({
                        "type": "accessibility",
                        "severity": "medium",
                        "message": "部分表单元素缺少关联标签",
                        "line": None,
                        "suggestion": "为表单元素添加 label 或使用 aria-label"
                    })
            
            if 'tabindex' not in content and '<button' in content:
                issues.append({
                    "type": "accessibility",
                    "severity": "low",
                    "message": "建议添加 tabindex 以改善键盘导航",
                    "line": None,
                    "suggestion": "为交互元素添加适当的 tabindex 属性"
                })
        
        return issues


class ResponsiveValidator(UIValidator):
    """响应式校验器"""
    
    def validate(self, target: Path) -> float:
        score = 0.7
        
        if target.is_file():
            content = target.read_text(encoding='utf-8')
            
            responsive_patterns = ['sm:', 'md:', 'lg:', 'xl:', '2xl:', '@media', 'media-query']
            responsive_count = sum(1 for p in responsive_patterns if p in content)
            score += min(responsive_count * 0.05, 0.2)
            
            if 'viewport' in content or 'meta name="viewport"' in content:
                score += 0.1
            
            if 'flex' in content or 'grid' in content:
                score += 0.05
        
        return min(score, 1.0)
    
    def get_issues(self, target: Path) -> List[Dict[str, Any]]:
        issues = []
        
        if target.is_file():
            content = target.read_text(encoding='utf-8')
            
            responsive_patterns = ['sm:', 'md:', 'lg:', 'xl:', '@media']
            if not any(p in content for p in responsive_patterns):
                issues.append({
                    "type": "responsive",
                    "severity": "high",
                    "message": "未发现响应式断点样式",
                    "line": None,
                    "suggestion": "添加响应式断点以支持不同屏幕尺寸"
                })
            
            if 'viewport' not in content and 'meta name="viewport"' not in content:
                issues.append({
                    "type": "responsive",
                    "severity": "medium",
                    "message": "缺少 viewport meta 标签",
                    "line": None,
                    "suggestion": "添加 <meta name='viewport' content='width=device-width, initial-scale=1'>"
                })
            
            if 'fixed' in content and 'px' in content:
                issues.append({
                    "type": "responsive",
                    "severity": "low",
                    "message": "发现固定像素值，可能影响响应式布局",
                    "line": None,
                    "suggestion": "考虑使用相对单位（rem, em, %, vw, vh）"
                })
        
        return issues


class PerformanceValidator(UIValidator):
    """性能校验器"""
    
    def validate(self, target: Path) -> float:
        score = 0.9
        
        if target.is_file():
            content = target.read_text(encoding='utf-8')
            
            if '<img' in content and 'loading=' not in content:
                score -= 0.1
            
            if 'import ' in content and content.count('import ') > 10:
                score -= 0.05
            
            if 'async' not in content and 'defer' not in content:
                if '<script' in content:
                    score -= 0.05
            
            if len(content) > 50000:
                score -= 0.1
        
        return max(score, 0)
    
    def get_issues(self, target: Path) -> List[Dict[str, Any]]:
        issues = []
        
        if target.is_file():
            content = target.read_text(encoding='utf-8')
            file_size = len(content)
            
            if '<img' in content and 'loading=' not in content:
                issues.append({
                    "type": "performance",
                    "severity": "medium",
                    "message": "图片未使用懒加载",
                    "line": None,
                    "suggestion": "为图片添加 loading='lazy' 属性"
                })
            
            if file_size > 50000:
                issues.append({
                    "type": "performance",
                    "severity": "medium",
                    "message": f"文件较大 ({file_size} 字符)，可能影响加载性能",
                    "line": None,
                    "suggestion": "考虑拆分组件或使用代码分割"
                })
            
            if content.count('import ') > 15:
                issues.append({
                    "type": "performance",
                    "severity": "low",
                    "message": "导入语句较多，建议检查是否有冗余依赖",
                    "line": None,
                    "suggestion": "移除未使用的导入，使用 tree-shaking"
                })
        
        return issues


class ConsistencyValidator(UIValidator):
    """设计一致性校验器"""
    
    def __init__(self, design_system: DesignSystem = None):
        self.design_system = design_system
    
    def validate(self, target: Path) -> float:
        score = 0.8
        
        if target.is_file():
            content = target.read_text(encoding='utf-8')
            
            if self.design_system:
                for color_name, color_value in self.design_system.colors.items():
                    if color_value in content or color_name in content:
                        score += 0.02
            
            if 'className=' in content:
                class_pattern = r'className="([^"]+)"'
                classes = re.findall(class_pattern, content)
                unique_prefixes = set(c.split('-')[0] for c in ' '.join(classes).split() if '-' in c)
                if len(unique_prefixes) <= 3:
                    score += 0.05
        
        return min(score, 1.0)
    
    def get_issues(self, target: Path) -> List[Dict[str, Any]]:
        issues = []
        
        if target.is_file():
            content = target.read_text(encoding='utf-8')
            
            inline_style_count = content.count('style={')
            if inline_style_count > 3:
                issues.append({
                    "type": "consistency",
                    "severity": "medium",
                    "message": f"发现 {inline_style_count} 处内联样式",
                    "line": None,
                    "suggestion": "使用 CSS 类或设计令牌替代内联样式"
                })
            
            hardcoded_colors = re.findall(r'#[0-9a-fA-F]{3,6}', content)
            if len(hardcoded_colors) > 2:
                issues.append({
                    "type": "consistency",
                    "severity": "medium",
                    "message": f"发现 {len(hardcoded_colors)} 处硬编码颜色值",
                    "line": None,
                    "suggestion": "使用设计系统中的颜色变量"
                })
        
        return issues


class InteractionValidator(UIValidator):
    """交互校验器"""
    
    INTERACTION_PATTERNS = [
        ('onClick', 'click'),
        ('onHover', 'hover'),
        ('onFocus', 'focus'),
        ('onBlur', 'blur'),
        ('onKeyDown', 'keyboard'),
        ('onSubmit', 'form'),
        ('onChange', 'input'),
    ]
    
    def validate(self, target: Path) -> float:
        score = 0.7
        
        if target.is_file():
            content = target.read_text(encoding='utf-8')
            
            interaction_count = 0
            for pattern, _ in self.INTERACTION_PATTERNS:
                if pattern in content:
                    interaction_count += 1
            
            score += min(interaction_count * 0.03, 0.2)
            
            if 'disabled' in content or 'isDisabled' in content:
                score += 0.05
            
            if 'loading' in content.lower() or 'isLoading' in content:
                score += 0.05
        
        return min(score, 1.0)
    
    def get_issues(self, target: Path) -> List[Dict[str, Any]]:
        issues = []
        
        if target.is_file():
            content = target.read_text(encoding='utf-8')
            
            has_click = 'onClick' in content
            has_keyboard = 'onKeyDown' in content or 'onKeyUp' in content
            
            if has_click and not has_keyboard:
                issues.append({
                    "type": "interaction",
                    "severity": "medium",
                    "message": "存在点击事件但缺少键盘事件支持",
                    "line": None,
                    "suggestion": "添加键盘事件处理以提高可访问性"
                })
            
            if '<button' in content or 'onClick' in content:
                if 'cursor-pointer' not in content and 'cursor' not in content:
                    issues.append({
                        "type": "interaction",
                        "severity": "low",
                        "message": "交互元素可能缺少视觉反馈",
                        "line": None,
                        "suggestion": "添加 cursor-pointer 或其他交互状态样式"
                    })
        
        return issues


class AnimationValidator(UIValidator):
    """动画校验器"""
    
    def validate(self, target: Path) -> float:
        score = 0.8
        
        if target.is_file():
            content = target.read_text(encoding='utf-8')
            
            animation_patterns = [
                'transition', 'animate', 'animation', '@keyframes',
                'motion', 'framer-motion', 'spring'
            ]
            
            for pattern in animation_patterns:
                if pattern in content:
                    score += 0.03
            
            if 'duration' in content:
                score += 0.02
            
            if 'ease' in content:
                score += 0.02
        
        return min(score, 1.0)
    
    def get_issues(self, target: Path) -> List[Dict[str, Any]]:
        issues = []
        
        if target.is_file():
            content = target.read_text(encoding='utf-8')
            
            if 'transition' in content or 'animation' in content:
                if 'prefers-reduced-motion' not in content:
                    issues.append({
                        "type": "animation",
                        "severity": "medium",
                        "message": "存在动画但未考虑减少动画偏好",
                        "line": None,
                        "suggestion": "添加 @media (prefers-reduced-motion: reduce) 支持"
                    })
            
            duration_matches = re.findall(r'duration["\s:]+(\d+)', content)
            for duration in duration_matches:
                if int(duration) > 500:
                    issues.append({
                        "type": "animation",
                        "severity": "low",
                        "message": f"动画时长 {duration}ms 可能过长",
                        "line": None,
                        "suggestion": "建议动画时长控制在 200-500ms 之间"
                    })
        
        return issues


class ColorContrastValidator(UIValidator):
    """颜色对比度校验器"""
    
    def validate(self, target: Path) -> float:
        score = 0.85
        
        if target.is_file():
            content = target.read_text(encoding='utf-8')
            
            text_color_patterns = [
                r'text-\[([^\]]+)\]',
                r'color:\s*([^;]+)',
                r'#[0-9a-fA-F]{3,6}',
            ]
            
            has_text_colors = any(re.search(p, content) for p in text_color_patterns)
            if has_text_colors:
                score += 0.05
            
            if 'text-white' in content or 'text-black' in content:
                score += 0.05
            
            if 'bg-' in content:
                score += 0.05
        
        return min(score, 1.0)
    
    def get_issues(self, target: Path) -> List[Dict[str, Any]]:
        issues = []
        
        if target.is_file():
            content = target.read_text(encoding='utf-8')
            
            low_contrast_combos = [
                ('text-gray-300', 'bg-white'),
                ('text-gray-400', 'bg-gray-100'),
                ('text-white', 'bg-yellow-200'),
            ]
            
            for text_class, bg_class in low_contrast_combos:
                if text_class in content and bg_class in content:
                    issues.append({
                        "type": "color_contrast",
                        "severity": "high",
                        "message": f"可能存在低对比度组合: {text_class} + {bg_class}",
                        "line": None,
                        "suggestion": "检查颜色对比度是否符合 WCAG AA 标准 (4.5:1)"
                    })
            
            if 'text-xs' in content or 'text-sm' in content:
                issues.append({
                    "type": "color_contrast",
                    "severity": "low",
                    "message": "小字体需要更高的对比度",
                    "line": None,
                    "suggestion": "小字体建议对比度达到 WCAG AAA 标准 (7:1)"
                })
        
        return issues


class UsabilityValidator(UIValidator):
    """可用性校验器"""
    
    def validate(self, target: Path) -> float:
        score = 0.75
        
        if target.is_file():
            content = target.read_text(encoding='utf-8')
            
            usability_indicators = [
                ('placeholder=', 0.03),
                ('aria-label', 0.05),
                ('title=', 0.03),
                ('tooltip', 0.03),
                ('help', 0.02),
                ('hint', 0.02),
            ]
            
            for indicator, bonus in usability_indicators:
                if indicator in content:
                    score += bonus
            
            if 'error' in content.lower() and 'message' in content.lower():
                score += 0.05
            
            if 'loading' in content.lower():
                score += 0.05
        
        return min(score, 1.0)
    
    def get_issues(self, target: Path) -> List[Dict[str, Any]]:
        issues = []
        
        if target.is_file():
            content = target.read_text(encoding='utf-8')
            
            if '<form' in content:
                if 'onSubmit' not in content:
                    issues.append({
                        "type": "usability",
                        "severity": "medium",
                        "message": "表单缺少提交处理",
                        "line": None,
                        "suggestion": "添加表单提交处理和验证"
                    })
                
                if 'required' not in content and 'validation' not in content.lower():
                    issues.append({
                        "type": "usability",
                        "severity": "medium",
                        "message": "表单可能缺少验证",
                        "line": None,
                        "suggestion": "添加表单验证和错误提示"
                    })
            
            if '<input' in content:
                if 'placeholder' not in content:
                    issues.append({
                        "type": "usability",
                        "severity": "low",
                        "message": "输入框缺少占位符提示",
                        "line": None,
                        "suggestion": "添加 placeholder 提示用户输入内容"
                    })
        
        return issues


class ComponentLibrary(Enum):
    """组件库类型"""
    ANTD = "antd"
    MATERIAL_UI = "material_ui"
    CHAKRA_UI = "chakra_ui"
    TAILWIND_UI = "tailwind_ui"
    SHADCN = "shadcn"
    RADIX = "radix"
    HEADLESS_UI = "headless_ui"
    CUSTOM = "custom"


@dataclass
class ComponentInfo:
    """组件信息"""
    name: str
    library: ComponentLibrary
    category: str
    description: str
    props: Dict[str, Any]
    import_statement: str
    usage_example: str
    accessibility_support: bool = True
    responsive_support: bool = True
    design_tokens: Dict[str, str] = None
    variants: List[str] = None
    
    def __post_init__(self):
        if self.design_tokens is None:
            self.design_tokens = {}
        if self.variants is None:
            self.variants = []


@dataclass
class UXGuideline:
    """UX规范"""
    guideline_id: str
    category: str
    title: str
    description: str
    severity: str
    check_function: str
    recommendation: str
    wcag_reference: str = ""
    examples: List[str] = None
    
    def __post_init__(self):
        if self.examples is None:
            self.examples = []


@dataclass
class DesignAutomationResult:
    """设计自动化结果"""
    result_id: str
    task_type: str
    status: str
    generated_files: List[str]
    design_tokens: Dict[str, Any]
    components_used: List[str]
    validation_score: float
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class UIDesignAutomator:
    """UI设计自动化器
    
    负责自动化UI设计流程，包括布局生成、组件选择、
    样式生成和响应式适配。
    """
    
    LAYOUT_TEMPLATES = {
        "dashboard": {
            "structure": ["header", "sidebar", "main", "footer"],
            "grid": "sidebar-left",
            "responsive": True
        },
        "landing": {
            "structure": ["header", "hero", "features", "cta", "footer"],
            "grid": "full-width",
            "responsive": True
        },
        "form": {
            "structure": ["header", "form", "actions"],
            "grid": "centered",
            "responsive": True
        },
        "list": {
            "structure": ["header", "filters", "list", "pagination"],
            "grid": "full-width",
            "responsive": True
        },
        "detail": {
            "structure": ["header", "breadcrumb", "content", "sidebar", "actions"],
            "grid": "content-sidebar",
            "responsive": True
        }
    }
    
    def __init__(self, integration: 'UIUXIntegration'):
        self.integration = integration
        self._design_templates: Dict[str, Dict] = {}
        self._component_mappings: Dict[str, List[str]] = {}
        self._init_design_templates()
        self._init_component_mappings()
        logger.info("UIDesignAutomator initialized")
    
    def _init_design_templates(self) -> None:
        """初始化设计模板"""
        self._design_templates = {
            "modern_dashboard": {
                "layout": "dashboard",
                "theme": ThemeType.MODERN,
                "components": ["Card", "Chart", "Table", "StatCard"],
                "spacing": "comfortable",
                "typography": "sans-serif"
            },
            "minimal_landing": {
                "layout": "landing",
                "theme": ThemeType.MINIMAL,
                "components": ["Hero", "FeatureGrid", "CTA", "Footer"],
                "spacing": "spacious",
                "typography": "sans-serif"
            },
            "corporate_form": {
                "layout": "form",
                "theme": ThemeType.CORPORATE,
                "components": ["Form", "Input", "Select", "Button"],
                "spacing": "compact",
                "typography": "sans-serif"
            }
        }
    
    def _init_component_mappings(self) -> None:
        """初始化组件映射"""
        self._component_mappings = {
            "input": ["Input", "TextField", "TextInput"],
            "button": ["Button", "IconButton", "LoadingButton"],
            "select": ["Select", "Dropdown", "ComboBox"],
            "table": ["Table", "DataTable", "DataGrid"],
            "card": ["Card", "Panel", "Box"],
            "modal": ["Modal", "Dialog", "Drawer"],
            "form": ["Form", "FormBuilder"],
            "chart": ["Chart", "LineChart", "BarChart", "PieChart"],
            "navigation": ["Nav", "Navbar", "Sidebar", "Menu"],
            "feedback": ["Alert", "Toast", "Notification", "Message"]
        }
    
    def automate_design(self, page_type: str, requirements: Dict[str, Any],
                        tech_stack: str = "react", 
                        component_library: ComponentLibrary = ComponentLibrary.ANTD) -> DesignAutomationResult:
        """自动化设计
        
        Args:
            page_type: 页面类型
            requirements: 需求描述
            tech_stack: 技术栈
            component_library: 组件库
            
        Returns:
            设计自动化结果
        """
        logger.info(f"自动化设计: {page_type}")
        
        result_id = f"DESIGN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        result = DesignAutomationResult(
            result_id=result_id,
            task_type=page_type,
            status="in_progress",
            generated_files=[],
            design_tokens={},
            components_used=[],
            validation_score=0.0,
            issues=[],
            recommendations=[]
        )
        
        try:
            layout_template = self.LAYOUT_TEMPLATES.get(page_type, self.LAYOUT_TEMPLATES["landing"])
            
            design_system = self.integration.get_design_system()
            if not design_system:
                design_system = self.integration.generate_design_system()
            
            result.design_tokens = {
                "colors": design_system.colors,
                "typography": design_system.typography,
                "spacing": design_system.spacing
            }
            
            components = self._select_components(page_type, requirements, component_library)
            result.components_used = components
            
            layout_code = self._generate_layout_code(
                page_type, layout_template, components, tech_stack, component_library
            )
            
            output_path = self.integration.design_output_path / f"{page_type}_auto_generated.{self._get_file_extension(tech_stack)}"
            output_path.write_text(layout_code, encoding='utf-8')
            result.generated_files.append(str(output_path))
            
            styles = self._generate_styles(page_type, design_system, layout_template)
            style_path = self.integration.design_output_path / f"{page_type}_styles.module.css"
            style_path.write_text(styles, encoding='utf-8')
            result.generated_files.append(str(style_path))
            
            validation = self.integration.validate_ui(str(output_path))
            result.validation_score = validation.overall_score
            result.issues = validation.issues
            
            if validation.overall_score < 0.7:
                result.recommendations = validation.recommendations
            
            result.status = "completed"
            
        except Exception as e:
            result.status = "failed"
            result.issues.append({"type": "automation_error", "message": str(e)})
            logger.error(f"自动化设计失败: {e}")
        
        return result
    
    def _select_components(self, page_type: str, requirements: Dict,
                           library: ComponentLibrary) -> List[str]:
        """选择组件"""
        components = []
        
        layout = self.LAYOUT_TEMPLATES.get(page_type, {})
        structure = layout.get("structure", [])
        
        component_map = {
            "header": "Header",
            "sidebar": "Sidebar",
            "main": "MainContent",
            "footer": "Footer",
            "hero": "Hero",
            "features": "FeatureGrid",
            "cta": "CTA",
            "form": "Form",
            "filters": "FilterPanel",
            "list": "List",
            "pagination": "Pagination",
            "breadcrumb": "Breadcrumb",
            "content": "ContentArea",
            "actions": "ActionPanel"
        }
        
        for section in structure:
            if section in component_map:
                components.append(component_map[section])
        
        required_features = requirements.get("features", [])
        for feature in required_features:
            feature_lower = feature.lower()
            for key, comps in self._component_mappings.items():
                if key in feature_lower:
                    components.append(comps[0])
        
        return list(set(components))
    
    def _generate_layout_code(self, page_type: str, layout_template: Dict,
                              components: List[str], tech_stack: str,
                              library: ComponentLibrary) -> str:
        """生成布局代码"""
        if tech_stack in ["react", "next.js"]:
            return self._generate_react_layout(page_type, layout_template, components, library)
        elif tech_stack == "vue":
            return self._generate_vue_layout(page_type, layout_template, components, library)
        else:
            return self._generate_react_layout(page_type, layout_template, components, library)
    
    def _generate_react_layout(self, page_type: str, layout_template: Dict,
                                components: List[str], library: ComponentLibrary) -> str:
        """生成React布局代码"""
        imports = self._generate_imports(components, library)
        
        structure = layout_template.get("structure", [])
        
        layout_sections = []
        for section in structure:
            section_name = section.title()
            layout_sections.append(f"""        <{section_name} className="{section}">
          <!-- {section_name} content -->
        </{section_name}>""")
        
        return f"""{imports}

interface {page_type.title()}PageProps {{
  // Add props here
}}

const {page_type.title()}Page: React.FC<{page_type.title()}PageProps> = () => {{
  return (
    <div className="{page_type}-page">
{chr(10).join(layout_sections)}
    </div>
  );
}};

export default {page_type.title()}Page;
"""
    
    def _generate_vue_layout(self, page_type: str, layout_template: Dict,
                              components: List[str], library: ComponentLibrary) -> str:
        """生成Vue布局代码"""
        structure = layout_template.get("structure", [])
        
        layout_sections = []
        for section in structure:
            layout_sections.append(f"""    <{section.title()} class="{section}">
      <!-- {section.title()} content -->
    </{section.title()}>""")
        
        return f"""<template>
  <div class="{page_type}-page">
{chr(10).join(layout_sections)}
  </div>
</template>

<script setup lang="ts">
// Component logic
</script>

<style scoped>
.{page_type}-page {{
  /* Page styles */
}}
</style>
"""
    
    def _generate_imports(self, components: List[str], library: ComponentLibrary) -> str:
        """生成导入语句"""
        import_map = {
            ComponentLibrary.ANTD: {
                "Button": "import { Button } from 'antd';",
                "Input": "import { Input } from 'antd';",
                "Select": "import { Select } from 'antd';",
                "Table": "import { Table } from 'antd';",
                "Card": "import { Card } from 'antd';",
                "Modal": "import { Modal } from 'antd';",
                "Form": "import { Form } from 'antd';",
            },
            ComponentLibrary.MATERIAL_UI: {
                "Button": "import {{ Button }} from '@mui/material';",
                "Input": "import {{ TextField }} from '@mui/material';",
                "Select": "import {{ Select }} from '@mui/material';",
                "Table": "import {{ Table }} from '@mui/material';",
                "Card": "import {{ Card }} from '@mui/material';",
            },
            ComponentLibrary.CHAKRA_UI: {
                "Button": "import {{ Button }} from '@chakra-ui/react';",
                "Input": "import {{ Input }} from '@chakra-ui/react';",
                "Select": "import {{ Select }} from '@chakra-ui/react';",
                "Table": "import {{ Table }} from '@chakra-ui/react';",
            }
        }
        
        imports = ["import React from 'react';"]
        lib_imports = import_map.get(library, import_map[ComponentLibrary.ANTD])
        
        for comp in components:
            if comp in lib_imports:
                imports.append(lib_imports[comp])
        
        return "\n".join(imports)
    
    def _generate_styles(self, page_type: str, design_system: DesignSystem,
                         layout_template: Dict) -> str:
        """生成样式"""
        structure = layout_template.get("structure", [])
        
        styles = f""".{page_type}-page {{
  min-height: 100vh;
  background-color: {design_system.colors.get('background', '#ffffff')};
  color: {design_system.colors.get('foreground', '#000000')};
}}
"""
        
        for section in structure:
            styles += f"""
.{section} {{
  padding: {design_system.spacing.get('md', '16px')};
}}
"""
        
        styles += """
/* Responsive styles */
@media (max-width: 768px) {
  .sidebar {
    display: none;
  }
}
"""
        
        return styles
    
    def _get_file_extension(self, tech_stack: str) -> str:
        """获取文件扩展名"""
        extensions = {
            "react": "tsx",
            "next.js": "tsx",
            "vue": "vue"
        }
        return extensions.get(tech_stack, "tsx")
    
    def generate_component_variants(self, component_name: str,
                                     base_props: Dict[str, Any],
                                     variants: List[str]) -> Dict[str, str]:
        """生成组件变体
        
        Args:
            component_name: 组件名称
            base_props: 基础属性
            variants: 变体列表
            
        Returns:
            变体代码字典
        """
        variant_codes = {}
        
        for variant in variants:
            variant_props = base_props.copy()
            variant_props["variant"] = variant
            
            code = f"""<{component_name}
  variant="{variant}"
  // Add variant-specific props
>
  {variant.title()} Variant
</{component_name}>"""
            
            variant_codes[variant] = code
        
        return variant_codes
    
    def create_responsive_layout(self, layout_type: str,
                                  breakpoints: Dict[str, int] = None) -> str:
        """创建响应式布局
        
        Args:
            layout_type: 布局类型
            breakpoints: 断点配置
            
        Returns:
            响应式布局代码
        """
        if breakpoints is None:
            breakpoints = {
                "sm": 640,
                "md": 768,
                "lg": 1024,
                "xl": 1280
            }
        
        return f"""/* Responsive Layout: {layout_type} */

.container {{
  width: 100%;
  max-width: {breakpoints.get('xl', 1280)}px;
  margin: 0 auto;
  padding: 0 1rem;
}}

@media (min-width: {breakpoints.get('sm', 640)}px) {{
  .container {{
    padding: 0 1.5rem;
  }}
}}

@media (min-width: {breakpoints.get('md', 768)}px) {{
  .container {{
    padding: 0 2rem;
  }}
}}

@media (min-width: {breakpoints.get('lg', 1024)}px) {{
  .container {{
    padding: 0 2.5rem;
  }}
}}

/* Grid System */
.grid {{
  display: grid;
  gap: 1rem;
}}

.grid-cols-1 {{ grid-template-columns: repeat(1, 1fr); }}
.grid-cols-2 {{ grid-template-columns: repeat(2, 1fr); }}
.grid-cols-3 {{ grid-template-columns: repeat(3, 1fr); }}
.grid-cols-4 {{ grid-template-columns: repeat(4, 1fr); }}

@media (min-width: {breakpoints.get('md', 768)}px) {{
  .md\\:grid-cols-2 {{ grid-template-columns: repeat(2, 1fr); }}
  .md\\:grid-cols-3 {{ grid-template-columns: repeat(3, 1fr); }}
  .md\\:grid-cols-4 {{ grid-template-columns: repeat(4, 1fr); }}
}}
"""


class UXGuidelineChecker:
    """UX规范检查器
    
    负责检查UI设计是否符合UX规范和最佳实践。
    """
    
    def __init__(self, integration: 'UIUXIntegration'):
        self.integration = integration
        self._guidelines: List[UXGuideline] = []
        self._init_guidelines()
        logger.info("UXGuidelineChecker initialized")
    
    def _init_guidelines(self) -> None:
        """初始化UX规范"""
        self._guidelines = [
            UXGuideline(
                guideline_id="UX-001",
                category="accessibility",
                title="图片必须有alt属性",
                description="所有图片元素必须包含描述性的alt属性",
                severity="high",
                check_function="check_img_alt",
                recommendation="为所有图片添加描述性alt属性，装饰性图片使用alt=''",
                wcag_reference="WCAG 2.1 - 1.1.1",
                examples=["<img src='photo.jpg' alt='产品展示图'>"]
            ),
            UXGuideline(
                guideline_id="UX-002",
                category="accessibility",
                title="表单元素必须有标签",
                description="所有表单控件必须有关联的label元素",
                severity="high",
                check_function="check_form_labels",
                recommendation="使用label元素或aria-label属性",
                wcag_reference="WCAG 2.1 - 1.3.1",
                examples=["<label for='email'>邮箱</label><input id='email' type='email'>"]
            ),
            UXGuideline(
                guideline_id="UX-003",
                category="interaction",
                title="可点击元素必须有视觉反馈",
                description="按钮和链接在hover/focus状态下应有明显的视觉变化",
                severity="medium",
                check_function="check_clickable_feedback",
                recommendation="添加hover、focus和active状态样式"
            ),
            UXGuideline(
                guideline_id="UX-004",
                category="usability",
                title="加载状态指示",
                description="异步操作应显示加载状态",
                severity="medium",
                check_function="check_loading_states",
                recommendation="添加spinner或skeleton加载指示器"
            ),
            UXGuideline(
                guideline_id="UX-005",
                category="usability",
                title="错误处理反馈",
                description="用户操作失败时应提供明确的错误信息",
                severity="high",
                check_function="check_error_handling",
                recommendation="显示具体的错误原因和解决建议"
            ),
            UXGuideline(
                guideline_id="UX-006",
                category="responsive",
                title="触摸目标大小",
                description="移动端触摸目标至少44x44像素",
                severity="medium",
                check_function="check_touch_targets",
                recommendation="增大按钮和链接的点击区域"
            ),
            UXGuideline(
                guideline_id="UX-007",
                category="accessibility",
                title="颜色对比度",
                description="文本与背景的对比度至少4.5:1",
                severity="high",
                check_function="check_color_contrast",
                recommendation="使用对比度检查工具验证颜色组合",
                wcag_reference="WCAG 2.1 - 1.4.3"
            ),
            UXGuideline(
                guideline_id="UX-008",
                category="navigation",
                title="键盘导航支持",
                description="所有交互元素应可通过键盘访问",
                severity="high",
                check_function="check_keyboard_nav",
                recommendation="添加tabIndex和键盘事件处理",
                wcag_reference="WCAG 2.1 - 2.1.1"
            )
        ]
    
    def check_guidelines(self, target_path: str, 
                          categories: List[str] = None) -> Dict[str, Any]:
        """检查UX规范
        
        Args:
            target_path: 目标路径
            categories: 检查类别，为None时检查所有
            
        Returns:
            检查结果
        """
        logger.info(f"检查UX规范: {target_path}")
        
        target = Path(target_path)
        result = {
            "target": target_path,
            "timestamp": datetime.now().isoformat(),
            "passed": [],
            "failed": [],
            "warnings": [],
            "summary": {
                "total": 0,
                "passed_count": 0,
                "failed_count": 0,
                "warning_count": 0
            }
        }
        
        if not target.exists():
            result["error"] = "目标不存在"
            return result
        
        content = target.read_text(encoding='utf-8') if target.is_file() else ""
        
        for guideline in self._guidelines:
            if categories and guideline.category not in categories:
                continue
            
            check_result = self._check_guideline(guideline, content, target)
            
            result["summary"]["total"] += 1
            
            if check_result["status"] == "passed":
                result["passed"].append({
                    "guideline_id": guideline.guideline_id,
                    "title": guideline.title,
                    "category": guideline.category
                })
                result["summary"]["passed_count"] += 1
            elif check_result["status"] == "failed":
                result["failed"].append({
                    "guideline_id": guideline.guideline_id,
                    "title": guideline.title,
                    "category": guideline.category,
                    "severity": guideline.severity,
                    "recommendation": guideline.recommendation,
                    "details": check_result.get("details", [])
                })
                result["summary"]["failed_count"] += 1
            else:
                result["warnings"].append({
                    "guideline_id": guideline.guideline_id,
                    "title": guideline.title,
                    "category": guideline.category,
                    "message": check_result.get("message", "")
                })
                result["summary"]["warning_count"] += 1
        
        return result
    
    def _check_guideline(self, guideline: UXGuideline, content: str, 
                         target: Path) -> Dict[str, Any]:
        """检查单个规范"""
        check_function = getattr(self, f"_{guideline.check_function}", None)
        
        if check_function:
            return check_function(content, target)
        
        return {"status": "skipped", "message": "检查函数未实现"}
    
    def _check_img_alt(self, content: str, target: Path) -> Dict[str, Any]:
        """检查图片alt属性"""
        issues = []
        
        img_pattern = r'<img[^>]*>'
        imgs = re.findall(img_pattern, content)
        
        for img in imgs:
            if 'alt=' not in img:
                issues.append(f"图片缺少alt属性: {img[:50]}...")
        
        if issues:
            return {"status": "failed", "details": issues}
        return {"status": "passed"}
    
    def _check_form_labels(self, content: str, target: Path) -> Dict[str, Any]:
        """检查表单标签"""
        issues = []
        
        input_pattern = r'<input[^>]*type=["\'](?!(hidden|submit|reset|button))[^"\']*["\'][^>]*>'
        inputs = re.findall(input_pattern, content, re.IGNORECASE)
        
        for inp in inputs:
            has_label = False
            if 'id=' in inp:
                input_id = re.search(r'id=["\']([^"\']+)["\']', inp)
                if input_id:
                    label_pattern = f'<label[^>]*for=["\']?{input_id.group(1)}["\']?'
                    if re.search(label_pattern, content):
                        has_label = True
            
            if 'aria-label=' in inp or 'aria-labelledby=' in inp:
                has_label = True
            
            if not has_label:
                issues.append(f"表单元素缺少标签: {inp[:50]}...")
        
        if issues:
            return {"status": "failed", "details": issues}
        return {"status": "passed"}
    
    def _check_clickable_feedback(self, content: str, target: Path) -> Dict[str, Any]:
        """检查点击反馈"""
        has_hover = ':hover' in content or 'hover:' in content
        has_focus = ':focus' in content or 'focus:' in content
        
        if has_hover and has_focus:
            return {"status": "passed"}
        elif has_hover or has_focus:
            return {"status": "warning", "message": "部分交互状态缺失"}
        return {"status": "failed", "details": ["缺少交互状态样式"]}
    
    def _check_loading_states(self, content: str, target: Path) -> Dict[str, Any]:
        """检查加载状态"""
        loading_indicators = ['loading', 'isLoading', 'spinner', 'skeleton', 'Loading']
        
        has_loading = any(indicator in content for indicator in loading_indicators)
        
        if has_loading:
            return {"status": "passed"}
        return {"status": "warning", "message": "未发现加载状态处理"}
    
    def _check_error_handling(self, content: str, target: Path) -> Dict[str, Any]:
        """检查错误处理"""
        error_indicators = ['error', 'Error', 'onError', 'errorMessage', 'catch']
        
        has_error_handling = any(indicator in content for indicator in error_indicators)
        
        if has_error_handling:
            return {"status": "passed"}
        return {"status": "warning", "message": "未发现错误处理逻辑"}
    
    def _check_touch_targets(self, content: str, target: Path) -> Dict[str, Any]:
        """检查触摸目标"""
        return {"status": "passed", "message": "需要手动验证触摸目标大小"}
    
    def _check_color_contrast(self, content: str, target: Path) -> Dict[str, Any]:
        """检查颜色对比度"""
        return {"status": "passed", "message": "需要使用工具验证颜色对比度"}
    
    def _check_keyboard_nav(self, content: str, target: Path) -> Dict[str, Any]:
        """检查键盘导航"""
        has_tabindex = 'tabIndex' in content or 'tabindex' in content
        has_keyboard_events = 'onKeyDown' in content or 'onKeyUp' in content
        
        if has_tabindex or has_keyboard_events:
            return {"status": "passed"}
        return {"status": "warning", "message": "未发现键盘导航支持"}
    
    def get_guidelines(self, category: str = None) -> List[UXGuideline]:
        """获取规范列表"""
        if category:
            return [g for g in self._guidelines if g.category == category]
        return self._guidelines
    
    def add_custom_guideline(self, guideline: UXGuideline) -> None:
        """添加自定义规范"""
        self._guidelines.append(guideline)
        logger.info(f"添加自定义规范: {guideline.guideline_id}")


class DesignSystemIntegrator:
    """设计系统集成器
    
    负责设计系统的创建、管理和导出。
    """
    
    def __init__(self, integration: 'UIUXIntegration'):
        self.integration = integration
        self._token_registry: Dict[str, DesignToken] = {}
        self._component_tokens: Dict[str, Dict[str, str]] = {}
        logger.info("DesignSystemIntegrator initialized")
    
    def create_design_token(self, name: str, category: str, value: str,
                            description: str = "", css_variable: str = "",
                            usage: List[str] = None) -> DesignToken:
        """创建设计令牌
        
        Args:
            name: 令牌名称
            category: 类别
            value: 值
            description: 描述
            css_variable: CSS变量名
            usage: 使用场景
            
        Returns:
            设计令牌
        """
        token = DesignToken(
            name=name,
            category=category,
            value=value,
            description=description,
            css_variable=css_variable or f"--{category}-{name}",
            usage=usage or []
        )
        
        self._token_registry[f"{category}.{name}"] = token
        
        logger.info(f"创建设计令牌: {category}.{name}")
        return token
    
    def get_token(self, name: str, category: str = None) -> Optional[DesignToken]:
        """获取设计令牌"""
        if category:
            return self._token_registry.get(f"{category}.{name}")
        
        for key, token in self._token_registry.items():
            if token.name == name:
                return token
        return None
    
    def export_tokens(self, format: str = "css") -> str:
        """导出设计令牌
        
        Args:
            format: 导出格式 (css|scss|json|js)
            
        Returns:
            导出内容
        """
        if format == "css":
            return self._export_css_tokens()
        elif format == "scss":
            return self._export_scss_tokens()
        elif format == "json":
            return self._export_json_tokens()
        elif format == "js":
            return self._export_js_tokens()
        else:
            return self._export_css_tokens()
    
    def _export_css_tokens(self) -> str:
        """导出CSS令牌"""
        css = ":root {\n"
        
        categories = {}
        for key, token in self._token_registry.items():
            if token.category not in categories:
                categories[token.category] = []
            categories[token.category].append(token)
        
        for category, tokens in categories.items():
            css += f"\n  /* {category.title()} */\n"
            for token in tokens:
                css += f"  {token.css_variable}: {token.value};\n"
        
        css += "}\n"
        return css
    
    def _export_scss_tokens(self) -> str:
        """导出SCSS令牌"""
        scss = ""
        
        for key, token in self._token_registry.items():
            var_name = token.css_variable.replace("--", "$")
            scss += f"{var_name}: {token.value};\n"
        
        return scss
    
    def _export_json_tokens(self) -> str:
        """导出JSON令牌"""
        tokens = {}
        for key, token in self._token_registry.items():
            tokens[key] = asdict(token)
        return json.dumps(tokens, ensure_ascii=False, indent=2)
    
    def _export_js_tokens(self) -> str:
        """导出JS令牌"""
        js = "export const tokens = {\n"
        
        categories = {}
        for key, token in self._token_registry.items():
            if token.category not in categories:
                categories[token.category] = {}
            categories[token.category][token.name] = token.value
        
        for category, tokens in categories.items():
            js += f"  {category}: {{\n"
            for name, value in tokens.items():
                js += f"    {name}: '{value}',\n"
            js += "  },\n"
        
        js += "};\n"
        return js
    
    def sync_with_design_system(self, design_system: DesignSystem) -> None:
        """与设计系统同步
        
        Args:
            design_system: 设计系统
        """
        for name, value in design_system.colors.items():
            self.create_design_token(
                name=name,
                category="color",
                value=value,
                description=f"颜色令牌: {name}"
            )
        
        for name, value in design_system.spacing.items():
            self.create_design_token(
                name=name,
                category="spacing",
                value=value,
                description=f"间距令牌: {name}"
            )
        
        for name, value in design_system.border_radius.items():
            self.create_design_token(
                name=name,
                category="radius",
                value=value,
                description=f"圆角令牌: {name}"
            )
        
        logger.info("设计系统同步完成")
    
    def create_component_tokens(self, component_name: str,
                                 tokens: Dict[str, str]) -> None:
        """创建组件令牌
        
        Args:
            component_name: 组件名称
            tokens: 令牌字典
        """
        self._component_tokens[component_name] = tokens
        
        for token_name, value in tokens.items():
            self.create_design_token(
                name=f"{component_name}-{token_name}",
                category="component",
                value=value,
                description=f"{component_name}组件令牌"
            )
        
        logger.info(f"创建组件令牌: {component_name}")


class ComponentLibraryIntegrator:
    """UI组件库集成器
    
    负责与各种UI组件库的集成和管理。
    """
    
    COMPONENT_REGISTRY: Dict[ComponentLibrary, Dict[str, ComponentInfo]] = {}
    
    def __init__(self, integration: 'UIUXIntegration'):
        self.integration = integration
        self._installed_libraries: List[ComponentLibrary] = []
        self._component_cache: Dict[str, ComponentInfo] = {}
        self._init_component_registry()
        logger.info("ComponentLibraryIntegrator initialized")
    
    def _init_component_registry(self) -> None:
        """初始化组件注册表"""
        if ComponentLibraryIntegrator.COMPONENT_REGISTRY:
            return
        
        ComponentLibraryIntegrator.COMPONENT_REGISTRY = {
            ComponentLibrary.ANTD: {
                "Button": ComponentInfo(
                    name="Button",
                    library=ComponentLibrary.ANTD,
                    category="input",
                    description="按钮组件",
                    props={"type": "string", "size": "string", "loading": "boolean"},
                    import_statement="import { Button } from 'antd';",
                    usage_example="<Button type='primary'>点击</Button>",
                    accessibility_support=True,
                    responsive_support=True,
                    variants=["primary", "default", "dashed", "text", "link"]
                ),
                "Input": ComponentInfo(
                    name="Input",
                    library=ComponentLibrary.ANTD,
                    category="input",
                    description="输入框组件",
                    props={"placeholder": "string", "disabled": "boolean", "size": "string"},
                    import_statement="import { Input } from 'antd';",
                    usage_example="<Input placeholder='请输入' />",
                    accessibility_support=True,
                    responsive_support=True
                ),
                "Table": ComponentInfo(
                    name="Table",
                    library=ComponentLibrary.ANTD,
                    category="display",
                    description="表格组件",
                    props={"columns": "array", "dataSource": "array", "pagination": "object"},
                    import_statement="import { Table } from 'antd';",
                    usage_example="<Table columns={columns} dataSource={data} />",
                    accessibility_support=True,
                    responsive_support=True
                )
            },
            ComponentLibrary.MATERIAL_UI: {
                "Button": ComponentInfo(
                    name="Button",
                    library=ComponentLibrary.MATERIAL_UI,
                    category="input",
                    description="Material Design按钮",
                    props={"variant": "string", "color": "string", "size": "string"},
                    import_statement="import { Button } from '@mui/material';",
                    usage_example="<Button variant='contained'>点击</Button>",
                    accessibility_support=True,
                    responsive_support=True,
                    variants=["text", "contained", "outlined"]
                ),
                "TextField": ComponentInfo(
                    name="TextField",
                    library=ComponentLibrary.MATERIAL_UI,
                    category="input",
                    description="文本输入框",
                    props={"label": "string", "variant": "string", "error": "boolean"},
                    import_statement="import { TextField } from '@mui/material';",
                    usage_example="<TextField label='名称' variant='outlined' />",
                    accessibility_support=True,
                    responsive_support=True
                )
            },
            ComponentLibrary.CHAKRA_UI: {
                "Button": ComponentInfo(
                    name="Button",
                    library=ComponentLibrary.CHAKRA_UI,
                    category="input",
                    description="Chakra UI按钮",
                    props={"colorScheme": "string", "size": "string", "variant": "string"},
                    import_statement="import { Button } from '@chakra-ui/react';",
                    usage_example="<Button colorScheme='blue'>点击</Button>",
                    accessibility_support=True,
                    responsive_support=True,
                    variants=["solid", "outline", "ghost", "link"]
                )
            }
        }
    
    def register_library(self, library: ComponentLibrary) -> Tuple[bool, str]:
        """注册组件库
        
        Args:
            library: 组件库类型
            
        Returns:
            (成功状态, 消息)
        """
        if library in self._installed_libraries:
            return False, f"组件库 {library.value} 已注册"
        
        self._installed_libraries.append(library)
        
        if library in self.COMPONENT_REGISTRY:
            for comp_name, comp_info in self.COMPONENT_REGISTRY[library].items():
                self._component_cache[comp_name] = comp_info
        
        logger.info(f"注册组件库: {library.value}")
        return True, f"组件库 {library.value} 注册成功"
    
    def get_component(self, name: str, 
                       library: ComponentLibrary = None) -> Optional[ComponentInfo]:
        """获取组件信息
        
        Args:
            name: 组件名称
            library: 组件库，为None时搜索所有库
            
        Returns:
            组件信息
        """
        if library:
            lib_components = self.COMPONENT_REGISTRY.get(library, {})
            return lib_components.get(name)
        
        return self._component_cache.get(name)
    
    def list_components(self, library: ComponentLibrary = None,
                        category: str = None) -> List[ComponentInfo]:
        """列出组件
        
        Args:
            library: 组件库
            category: 类别
            
        Returns:
            组件列表
        """
        components = []
        
        if library:
            lib_components = self.COMPONENT_REGISTRY.get(library, {})
            components = list(lib_components.values())
        else:
            components = list(self._component_cache.values())
        
        if category:
            components = [c for c in components if c.category == category]
        
        return components
    
    def generate_component_code(self, component_name: str,
                                 props: Dict[str, Any],
                                 library: ComponentLibrary = None) -> str:
        """生成组件代码
        
        Args:
            component_name: 组件名称
            props: 属性
            library: 组件库
            
        Returns:
            组件代码
        """
        component = self.get_component(component_name, library)
        
        if not component:
            return f"<!-- 组件 {component_name} 未找到 -->"
        
        props_str = " ".join([f'{k}="{v}"' if isinstance(v, str) else f'{k}={{{v}}}'
                              for k, v in props.items()])
        
        return f"{component.import_statement}\n\n<{component.name} {props_str} />"
    
    def check_library_compatibility(self, library: ComponentLibrary,
                                     tech_stack: str) -> Dict[str, Any]:
        """检查组件库兼容性
        
        Args:
            library: 组件库
            tech_stack: 技术栈
            
        Returns:
            兼容性信息
        """
        compatibility_map = {
            ComponentLibrary.ANTD: {
                "react": {"compatible": True, "version": ">=16.9.0"},
                "next.js": {"compatible": True, "version": ">=10.0.0"},
                "vue": {"compatible": False, "alternative": "ant-design-vue"}
            },
            ComponentLibrary.MATERIAL_UI: {
                "react": {"compatible": True, "version": ">=17.0.0"},
                "next.js": {"compatible": True, "version": ">=10.0.0"},
                "vue": {"compatible": False, "alternative": "vuetify"}
            },
            ComponentLibrary.CHAKRA_UI: {
                "react": {"compatible": True, "version": ">=16.8.0"},
                "next.js": {"compatible": True, "version": ">=10.0.0"},
                "vue": {"compatible": False, "alternative": "chakra-ui-vue"}
            },
            ComponentLibrary.TAILWIND_UI: {
                "react": {"compatible": True, "version": "any"},
                "next.js": {"compatible": True, "version": "any"},
                "vue": {"compatible": True, "version": "any"}
            }
        }
        
        lib_compat = compatibility_map.get(library, {})
        return lib_compat.get(tech_stack, {"compatible": False, "reason": "未知技术栈"})
    
    def suggest_components(self, requirements: str,
                            library: ComponentLibrary = None) -> List[ComponentInfo]:
        """根据需求建议组件
        
        Args:
            requirements: 需求描述
            library: 组件库
            
        Returns:
            建议的组件列表
        """
        suggestions = []
        requirements_lower = requirements.lower()
        
        keyword_mapping = {
            "button": ["Button", "IconButton"],
            "按钮": ["Button", "IconButton"],
            "input": ["Input", "TextField", "TextArea"],
            "输入框": ["Input", "TextField", "TextArea"],
            "输入": ["Input", "TextField", "TextArea"],
            "form": ["Form", "FormBuilder"],
            "表单": ["Form", "FormBuilder"],
            "table": ["Table", "DataTable"],
            "表格": ["Table", "DataTable"],
            "list": ["List", "ListView"],
            "列表": ["List", "ListView"],
            "card": ["Card", "Panel"],
            "卡片": ["Card", "Panel"],
            "modal": ["Modal", "Dialog", "Drawer"],
            "弹窗": ["Modal", "Dialog", "Drawer"],
            "对话框": ["Modal", "Dialog", "Drawer"],
            "menu": ["Menu", "Dropdown", "Nav"],
            "菜单": ["Menu", "Dropdown", "Nav"],
            "chart": ["Chart", "LineChart", "BarChart"],
            "图表": ["Chart", "LineChart", "BarChart"],
            "image": ["Image", "Avatar"],
            "图片": ["Image", "Avatar"],
            "notification": ["Alert", "Toast", "Notification"],
            "通知": ["Alert", "Toast", "Notification"],
            "提示": ["Alert", "Toast", "Notification"]
        }
        
        for keyword, component_names in keyword_mapping.items():
            if keyword in requirements_lower:
                for comp_name in component_names:
                    component = self.get_component(comp_name, library)
                    if component:
                        suggestions.append(component)
        
        return suggestions


class UIUXIntegration:
    """ui-ux-pro-max 集成管理器"""
    
    VALIDATORS: Dict[ValidationDimension, UIValidator] = {}
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.ui_ux_skill_path = Path(".trae/skills/ui-ux-pro-max-skill-main/.claude/skills/ui-ux-pro-max/SKILL.md")
        try:
            from skillscripts.utils.enhanced_path_config_manager import create_path_manager, OutputType
            _path_mgr = create_path_manager()
            self.logs_path = _path_mgr.get_output_path(OutputType.LOG, subdirectory="ui_integration")
            self.reports_path = _path_mgr.get_output_path(OutputType.REPORT, subdirectory="ui_design")
        except Exception:
            self.logs_path = get_path_config().LOGS_DIR / "ui_integration"
            self.reports_path = get_path_config().REPORTS_DIR / "ui_design"
        self.design_output_path = Path("design")
        self.systems_path = Path("design/systems")
        self.registry_path = UI_UX_REGISTRY_PATH
        
        self.logs_path.mkdir(parents=True, exist_ok=True)
        self.reports_path.mkdir(parents=True, exist_ok=True)
        self.design_output_path.mkdir(parents=True, exist_ok=True)
        self.systems_path.mkdir(parents=True, exist_ok=True)
        
        self._design_system: Optional[DesignSystem] = None
        self._task_cache: Dict[str, DesignTask] = {}
        
        self._init_validators()
        
        self.design_automator = UIDesignAutomator(self)
        self.ux_checker = UXGuidelineChecker(self)
        self.design_integrator = DesignSystemIntegrator(self)
        self.component_integrator = ComponentLibraryIntegrator(self)
        
        logger.info(f"UIUXIntegration initialized with project path: {project_path}")
    
    def _init_validators(self):
        """初始化校验器"""
        self.VALIDATORS = {
            ValidationDimension.ACCESSIBILITY: AccessibilityValidator(),
            ValidationDimension.RESPONSIVE: ResponsiveValidator(),
            ValidationDimension.PERFORMANCE: PerformanceValidator(),
            ValidationDimension.CONSISTENCY: ConsistencyValidator(self._design_system),
            ValidationDimension.USABILITY: UsabilityValidator(),
            ValidationDimension.INTERACTION: InteractionValidator(),
            ValidationDimension.ANIMATION: AnimationValidator(),
            ValidationDimension.COLOR_CONTRAST: ColorContrastValidator(),
        }
    
    def discover_tasks(self, scope: str = "all") -> List[DesignTask]:
        """
        发现需要 UI/UX 设计的任务
        
        Args:
            scope: 发现范围 (all|pages|components|systems|pending)
            
        Returns:
            设计任务列表
        """
        logger.info(f"Starting UI/UX task discovery with scope: {scope}")
        
        tasks = []
        
        # 扫描项目结构发现设计需求
        if scope in ["all", "pages"]:
            page_tasks = self._discover_page_tasks()
            tasks.extend(page_tasks)
        
        if scope in ["all", "components"]:
            component_tasks = self._discover_component_tasks()
            tasks.extend(component_tasks)
        
        if scope in ["all", "systems"]:
            system_tasks = self._discover_system_tasks()
            tasks.extend(system_tasks)
        
        # 检查待办设计任务
        if scope in ["all", "pending"]:
            pending_tasks = self._load_pending_tasks()
            tasks.extend(pending_tasks)
        
        logger.info(f"Discovered {len(tasks)} UI/UX design tasks")
        return tasks
    
    def _discover_page_tasks(self) -> List[DesignTask]:
        """发现页面设计任务"""
        tasks = []
        
        page_paths = [
            "src/pages",
            "src/views",
            "pages",
            "app"
        ]
        
        for page_path in page_paths:
            full_path = self.project_path / page_path
            if full_path.exists():
                for item in full_path.iterdir():
                    if item.is_file() and item.suffix in ['.tsx', '.vue', '.jsx']:
                        needs_redesign = self._check_needs_redesign(item)
                        if needs_redesign:
                            task = DesignTask(
                                task_id=f"PAGE-{item.stem.upper()}-{datetime.now().strftime('%Y%m%d')}",
                                task_type=DesignType.PAGE,
                                name=item.stem,
                                description=f"页面 '{item.stem}' 需要 UI/UX 优化",
                                project_type=self._detect_project_type(),
                                tech_stack=self._detect_tech_stack(),
                                status=DesignStatus.PENDING,
                                priority=DesignPriority.MEDIUM,
                                requirements={"path": str(item), "reason": "needs_redesign"}
                            )
                            tasks.append(task)
        
        return tasks
    
    def _discover_component_tasks(self) -> List[DesignTask]:
        """发现组件设计任务"""
        tasks = []
        
        component_paths = [
            "src/components",
            "components"
        ]
        
        for comp_path in component_paths:
            full_path = self.project_path / comp_path
            if full_path.exists():
                for item in full_path.iterdir():
                    if item.is_dir():
                        component_files = list(item.glob("*"))
                        if len(component_files) < 2:
                            task = DesignTask(
                                task_id=f"COMP-{item.name.upper()}-{datetime.now().strftime('%Y%m%d')}",
                                task_type=DesignType.COMPONENT,
                                name=item.name,
                                description=f"组件 '{item.name}' 需要完善设计",
                                project_type=self._detect_project_type(),
                                tech_stack=self._detect_tech_stack(),
                                status=DesignStatus.PENDING,
                                priority=DesignPriority.MEDIUM,
                                requirements={"path": str(item), "missing_files": True}
                            )
                            tasks.append(task)
        
        return tasks
    
    def _discover_system_tasks(self) -> List[DesignTask]:
        """发现设计系统任务"""
        tasks = []
        
        design_system_paths = [
            "design-system.json",
            "design/tokens.json",
            "src/styles/design-tokens.css"
        ]
        
        has_design_system = any(
            (self.project_path / path).exists() 
            for path in design_system_paths
        )
        
        if not has_design_system:
            task = DesignTask(
                task_id=f"SYSTEM-DESIGN-{datetime.now().strftime('%Y%m%d')}",
                task_type=DesignType.SYSTEM,
                name="Design System",
                description="项目缺少统一的设计系统",
                project_type=self._detect_project_type(),
                tech_stack=self._detect_tech_stack(),
                status=DesignStatus.PENDING,
                priority=DesignPriority.HIGH,
                requirements={"missing": "design_system"}
            )
            tasks.append(task)
        
        return tasks
    
    def _load_pending_tasks(self) -> List[DesignTask]:
        """加载待办设计任务"""
        tasks = []
        
        tasks_file = self.project_path / "design_tasks.json"
        if tasks_file.exists():
            try:
                data = json.loads(tasks_file.read_text(encoding='utf-8'))
                for task_data in data.get("tasks", []):
                    if task_data.get("status") == "pending":
                        priority_str = task_data.get("priority", "medium")
                        try:
                            priority = DesignPriority(priority_str.lower())
                        except ValueError:
                            priority = DesignPriority.MEDIUM
                        
                        task = DesignTask(
                            task_id=task_data["task_id"],
                            task_type=DesignType(task_data["task_type"]),
                            name=task_data["name"],
                            description=task_data["description"],
                            project_type=task_data["project_type"],
                            tech_stack=task_data["tech_stack"],
                            status=DesignStatus(task_data["status"]),
                            priority=priority,
                            requirements=task_data.get("requirements", {})
                        )
                        tasks.append(task)
            except Exception as e:
                logger.error(f"Failed to load pending tasks: {e}")
        
        return tasks
    
    def _check_needs_redesign(self, file_path: Path) -> bool:
        """检查文件是否需要重新设计"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # 检查是否缺少样式
            if 'className=' not in content and 'class=' not in content:
                return True
            
            # 检查是否使用内联样式（不推荐）
            if 'style={' in content and content.count('style={') > 3:
                return True
            
            # 检查文件大小（过小可能表示不完整）
            if len(content) < 200:
                return True
            
            return False
        except Exception:
            return False
    
    def _detect_project_type(self) -> str:
        """检测项目类型"""
        if (self.project_path / "package.json").exists():
            try:
                package = json.loads((self.project_path / "package.json").read_text(encoding='utf-8'))
                deps = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
                
                if "next" in deps:
                    return "Next.js Web App"
                elif "react" in deps:
                    return "React Web App"
                elif "vue" in deps:
                    return "Vue Web App"
                elif "@angular/core" in deps:
                    return "Angular Web App"
            except Exception:
                pass
        
        return "Web Application"
    
    def _detect_tech_stack(self) -> str:
        """检测技术栈"""
        tech_stack = []
        
        if (self.project_path / "package.json").exists():
            try:
                package = json.loads((self.project_path / "package.json").read_text(encoding='utf-8'))
                deps = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
                
                if "react" in deps:
                    tech_stack.append("React")
                if "vue" in deps:
                    tech_stack.append("Vue")
                if "next" in deps:
                    tech_stack.append("Next.js")
                if "tailwindcss" in deps:
                    tech_stack.append("Tailwind CSS")
                if "typescript" in deps:
                    tech_stack.append("TypeScript")
            except Exception:
                pass
        
        return "+".join(tech_stack) if tech_stack else "Unknown"
    
    def design_page(self, page_name: str, project_type: str, tech_stack: str,
                    page_type: str = "dashboard", requirements: Dict = None) -> Tuple[bool, str]:
        """
        设计页面
        
        Args:
            page_name: 页面名称
            project_type: 项目类型
            tech_stack: 技术栈
            page_type: 页面类型
            requirements: 需求描述
            
        Returns:
            (成功状态, 消息)
        """
        logger.info(f"Designing page: {page_name}")
        
        log_entry = self._create_log_entry("design-page", page_name, project_type, tech_stack)
        
        try:
            # 步骤1: 分析设计需求
            logger.info("Step 1: Analyzing design requirements...")
            design_requirements = self._analyze_design_requirements(
                page_type, project_type, requirements
            )
            
            # 步骤2: 生成设计系统（如果不存在）
            logger.info("Step 2: Generating/loading design system...")
            design_system = self._get_or_create_design_system(project_type)
            
            # 步骤3: 设计页面布局
            logger.info("Step 3: Designing page layout...")
            layout = self._design_page_layout(page_name, page_type, design_requirements)
            
            # 步骤4: 生成页面代码
            logger.info("Step 4: Generating page code...")
            output_path = self._generate_page_code(
                page_name, layout, design_system, tech_stack
            )
            
            # 步骤5: 执行 UI 校验
            logger.info("Step 5: Validating UI...")
            validation = self.validate_ui(str(output_path))
            
            # 记录成功日志
            log_entry.status = "success"
            log_entry.design_outputs = [str(output_path), str(self.design_output_path / f"{page_name}-layout.json")]
            log_entry.validation_results = asdict(validation)
            self._save_log(log_entry)
            
            logger.info(f"Page designed successfully: {page_name}")
            return True, f"页面 '{page_name}' 设计成功，UI 校验分数: {validation.accessibility_score:.2f}"
            
        except Exception as e:
            logger.error(f"Failed to design page: {e}")
            log_entry.status = "failure"
            log_entry.errors = [{"type": "design_error", "message": str(e)}]
            self._save_log(log_entry)
            return False, f"页面设计失败: {str(e)}"
    
    def design_component(self, component_name: str, component_type: str,
                         tech_stack: str, features: List[str] = None) -> Tuple[bool, str]:
        """
        设计组件
        
        Args:
            component_name: 组件名称
            component_type: 组件类型
            tech_stack: 技术栈
            features: 功能特性列表
            
        Returns:
            (成功状态, 消息)
        """
        logger.info(f"Designing component: {component_name}")
        
        log_entry = self._create_log_entry("design-component", component_name, "component", tech_stack)
        
        try:
            # 步骤1: 分析组件需求
            logger.info("Step 1: Analyzing component requirements...")
            component_spec = self._analyze_component_requirements(
                component_name, component_type, features
            )
            
            # 步骤2: 设计组件
            logger.info("Step 2: Designing component...")
            component_design = self._design_component(component_spec)
            
            # 步骤3: 生成组件代码
            logger.info("Step 3: Generating component code...")
            output_dir = self._generate_component_code(
                component_name, component_design, tech_stack
            )
            
            # 步骤4: 可访问性校验
            logger.info("Step 4: Validating accessibility...")
            validation = self.validate_ui(str(output_dir), validation_type="accessibility")
            
            # 记录日志
            log_entry.status = "success"
            log_entry.design_outputs = [str(output_dir)]
            log_entry.validation_results = asdict(validation)
            self._save_log(log_entry)
            
            logger.info(f"Component designed successfully: {component_name}")
            return True, f"组件 '{component_name}' 设计成功"
            
        except Exception as e:
            logger.error(f"Failed to design component: {e}")
            log_entry.status = "failure"
            log_entry.errors = [{"type": "design_error", "message": str(e)}]
            self._save_log(log_entry)
            return False, f"组件设计失败: {str(e)}"
    
    def validate_ui(self, target_path: str, validation_type: str = "comprehensive",
                    dimensions: List[str] = None) -> ValidationResult:
        """
        执行 UI 校验
        
        Args:
            target_path: 目标路径
            validation_type: 校验类型 (comprehensive|accessibility|responsive|performance|ux)
            dimensions: 校验维度列表
            
        Returns:
            校验结果
        """
        logger.info(f"Validating UI: {target_path}")
        
        target = Path(target_path)
        
        if dimensions is None:
            if validation_type == "accessibility":
                dimensions = [ValidationDimension.ACCESSIBILITY.value, ValidationDimension.COLOR_CONTRAST.value]
            elif validation_type == "responsive":
                dimensions = [ValidationDimension.RESPONSIVE.value]
            elif validation_type == "performance":
                dimensions = [ValidationDimension.PERFORMANCE.value]
            elif validation_type == "ux":
                dimensions = [
                    ValidationDimension.USABILITY.value,
                    ValidationDimension.INTERACTION.value,
                    ValidationDimension.ANIMATION.value
                ]
            else:
                dimensions = [d.value for d in ValidationDimension]
        
        scores = {}
        all_issues = []
        
        for dimension, validator in self.VALIDATORS.items():
            if dimension.value in dimensions:
                scores[dimension.value] = validator.validate(target)
                all_issues.extend(validator.get_issues(target))
        
        accessibility_score = scores.get(ValidationDimension.ACCESSIBILITY.value, 0.0)
        responsive_score = scores.get(ValidationDimension.RESPONSIVE.value, 0.0)
        performance_score = scores.get(ValidationDimension.PERFORMANCE.value, 0.0)
        consistency_score = scores.get(ValidationDimension.CONSISTENCY.value, 0.0)
        usability_score = scores.get(ValidationDimension.USABILITY.value, 0.0)
        interaction_score = scores.get(ValidationDimension.INTERACTION.value, 0.0)
        animation_score = scores.get(ValidationDimension.ANIMATION.value, 0.0)
        color_contrast_score = scores.get(ValidationDimension.COLOR_CONTRAST.value, 0.0)
        
        score_values = [v for v in scores.values() if v > 0]
        overall_score = sum(score_values) / len(score_values) if score_values else 0.0
        
        if overall_score >= 0.9:
            overall_status = ValidationStatus.PASSED
        elif overall_score >= 0.7:
            overall_status = ValidationStatus.WARNING
        else:
            overall_status = ValidationStatus.FAILED
        
        recommendations = self._generate_validation_recommendations(all_issues)
        
        ux_patterns = self._detect_ux_patterns(target)
        
        wcag_compliance = self._check_wcag_compliance(all_issues)
        
        result = ValidationResult(
            validation_id=f"UI-VAL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            target_path=target_path,
            timestamp=datetime.now().isoformat(),
            overall_status=overall_status,
            overall_score=overall_score,
            accessibility_score=accessibility_score,
            design_consistency_score=consistency_score,
            responsive_score=responsive_score,
            performance_score=performance_score,
            usability_score=usability_score,
            interaction_score=interaction_score,
            animation_score=animation_score,
            color_contrast_score=color_contrast_score,
            issues=all_issues,
            recommendations=recommendations,
            ux_patterns=ux_patterns,
            wcag_compliance=wcag_compliance
        )
        
        self._save_validation_result(result)
        
        return result
    
    def _detect_ux_patterns(self, target: Path) -> List[str]:
        """检测UX模式"""
        patterns = []
        
        if target.is_file():
            content = target.read_text(encoding='utf-8')
            
            pattern_indicators = {
                UXPattern.FORM_VALIDATION: ['validation', 'validate', 'isValid', 'error'],
                UXPattern.LOADING_STATE: ['loading', 'isLoading', 'skeleton', 'spinner'],
                UXPattern.EMPTY_STATE: ['empty', 'noData', 'no-result', 'isEmpty'],
                UXPattern.ERROR_HANDLING: ['error', 'catch', 'onError', 'errorMessage'],
                UXPattern.NAVIGATION: ['nav', 'menu', 'sidebar', 'breadcrumb'],
                UXPattern.SEARCH: ['search', 'filter', 'query'],
                UXPattern.FEEDBACK: ['toast', 'notification', 'alert', 'message'],
            }
            
            for pattern, indicators in pattern_indicators.items():
                if any(ind in content for ind in indicators):
                    patterns.append(pattern.value)
        
        return patterns
    
    def _check_wcag_compliance(self, issues: List[Dict]) -> Dict[str, bool]:
        """检查WCAG合规性"""
        compliance = {
            "wcag_a": True,
            "wcag_aa": True,
            "wcag_aaa": True,
        }
        
        for issue in issues:
            severity = issue.get("severity", "")
            issue_type = issue.get("type", "")
            
            if severity == "critical":
                compliance["wcag_a"] = False
                compliance["wcag_aa"] = False
                compliance["wcag_aaa"] = False
            elif severity == "high":
                compliance["wcag_aa"] = False
                compliance["wcag_aaa"] = False
            elif severity == "medium":
                compliance["wcag_aaa"] = False
        
        return compliance
    
    def check_ux_patterns(self, target_path: str) -> Dict[str, Any]:
        """
        检查UX模式
        
        Args:
            target_path: 目标路径
            
        Returns:
            UX模式检查结果
        """
        logger.info(f"Checking UX patterns: {target_path}")
        
        target = Path(target_path)
        result = {
            "target": target_path,
            "timestamp": datetime.now().isoformat(),
            "patterns": {},
            "missing_patterns": [],
            "recommendations": []
        }
        
        if target.is_file():
            content = target.read_text(encoding='utf-8')
            
            pattern_checks = {
                "loading_state": {
                    "indicators": ["loading", "isLoading", "spinner", "skeleton"],
                    "importance": "high",
                    "description": "加载状态处理"
                },
                "error_handling": {
                    "indicators": ["error", "catch", "onError", "errorMessage"],
                    "importance": "high",
                    "description": "错误处理"
                },
                "empty_state": {
                    "indicators": ["empty", "noData", "no-result", "isEmpty"],
                    "importance": "medium",
                    "description": "空状态处理"
                },
                "form_validation": {
                    "indicators": ["validation", "validate", "isValid", "touched"],
                    "importance": "high",
                    "description": "表单验证"
                },
                "accessibility": {
                    "indicators": ["aria-", "role=", "alt=", "tabIndex"],
                    "importance": "critical",
                    "description": "可访问性支持"
                },
                "responsive": {
                    "indicators": ["sm:", "md:", "lg:", "@media", "responsive"],
                    "importance": "high",
                    "description": "响应式设计"
                },
                "keyboard_navigation": {
                    "indicators": ["onKeyDown", "onKeyUp", "tabIndex", "focus"],
                    "importance": "high",
                    "description": "键盘导航"
                },
                "feedback": {
                    "indicators": ["toast", "notification", "alert", "message"],
                    "importance": "medium",
                    "description": "用户反馈"
                }
            }
            
            for pattern_name, check_info in pattern_checks.items():
                found = any(ind in content for ind in check_info["indicators"])
                result["patterns"][pattern_name] = {
                    "found": found,
                    "importance": check_info["importance"],
                    "description": check_info["description"]
                }
                
                if not found:
                    result["missing_patterns"].append({
                        "pattern": pattern_name,
                        "importance": check_info["importance"],
                        "description": check_info["description"]
                    })
            
            for missing in result["missing_patterns"]:
                if missing["importance"] in ["critical", "high"]:
                    result["recommendations"].append(
                        f"建议添加 {missing['description']} ({missing['pattern']}) 支持"
                    )
        
        return result
    
    def generate_design_system(self, name: str = "default", theme: ThemeType = ThemeType.MODERN,
                                   colors: Dict[str, str] = None, 
                                   typography: Dict[str, Any] = None) -> DesignSystem:
        """
        生成设计系统
        
        Args:
            name: 设计系统名称
            theme: 主题类型
            colors: 自定义颜色
            typography: 自定义排版
            
        Returns:
            设计系统
        """
        logger.info(f"Generating design system: {name} with theme: {theme.value}")
        
        default_colors = self._get_default_colors(theme)
        default_typography = self._get_default_typography(theme)
        
        final_colors = {**default_colors, **(colors or {})}
        final_typography = {**default_typography, **(typography or {})}
        
        design_system = DesignSystem(
            name=name,
            version="1.0.0",
            theme=theme,
            colors=final_colors,
            typography=final_typography,
            spacing={
                "xs": "4px",
                "sm": "8px",
                "md": "16px",
                "lg": "24px",
                "xl": "32px",
                "2xl": "48px"
            },
            border_radius={
                "sm": "2px",
                "md": "4px",
                "lg": "8px",
                "xl": "16px",
                "full": "9999px"
            },
            shadows={
                "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
                "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
                "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1)"
            },
            breakpoints={
                "sm": "640px",
                "md": "768px",
                "lg": "1024px",
                "xl": "1280px",
                "2xl": "1536px"
            }
        )
        
        self._design_system = design_system
        
        self._init_validators()
        
        system_file = self.systems_path / f"{name}-design-system.json"
        data = asdict(design_system)
        data['theme'] = design_system.theme.value
        system_file.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                              encoding='utf-8')
        
        css_file = self.systems_path / f"{name}-tokens.css"
        css_content = self._generate_css_tokens(design_system)
        css_file.write_text(css_content, encoding='utf-8')
        
        logger.info(f"Design system generated: {name}")
        return design_system
    
    def _get_default_colors(self, theme: ThemeType) -> Dict[str, str]:
        """获取默认颜色"""
        theme_colors = {
            ThemeType.MODERN: {
                "primary": "#3B82F6",
                "secondary": "#8B5CF6",
                "accent": "#F59E0B",
                "success": "#10B981",
                "warning": "#F59E0B",
                "error": "#EF4444",
                "info": "#3B82F6",
                "background": "#FFFFFF",
                "foreground": "#1F2937",
                "muted": "#6B7280",
                "border": "#E5E7EB"
            },
            ThemeType.DARK: {
                "primary": "#60A5FA",
                "secondary": "#A78BFA",
                "accent": "#FBBF24",
                "success": "#34D399",
                "warning": "#FBBF24",
                "error": "#F87171",
                "info": "#60A5FA",
                "background": "#111827",
                "foreground": "#F9FAFB",
                "muted": "#9CA3AF",
                "border": "#374151"
            },
            ThemeType.MINIMAL: {
                "primary": "#000000",
                "secondary": "#4B5563",
                "accent": "#6B7280",
                "success": "#22C55E",
                "warning": "#EAB308",
                "error": "#EF4444",
                "info": "#3B82F6",
                "background": "#FFFFFF",
                "foreground": "#000000",
                "muted": "#9CA3AF",
                "border": "#E5E7EB"
            },
            ThemeType.CORPORATE: {
                "primary": "#1E40AF",
                "secondary": "#1E3A8A",
                "accent": "#0369A1",
                "success": "#059669",
                "warning": "#D97706",
                "error": "#DC2626",
                "info": "#2563EB",
                "background": "#F8FAFC",
                "foreground": "#0F172A",
                "muted": "#64748B",
                "border": "#E2E8F0"
            },
            ThemeType.CREATIVE: {
                "primary": "#EC4899",
                "secondary": "#8B5CF6",
                "accent": "#F59E0B",
                "success": "#10B981",
                "warning": "#F59E0B",
                "error": "#EF4444",
                "info": "#06B6D4",
                "background": "#FAFAFA",
                "foreground": "#18181B",
                "muted": "#71717A",
                "border": "#E4E4E7"
            }
        }
        
        return theme_colors.get(theme, theme_colors[ThemeType.MODERN])
    
    def _get_default_typography(self, theme: ThemeType) -> Dict[str, Any]:
        """获取默认排版"""
        return {
            "font_family": {
                "sans": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
                "serif": "Georgia, Cambria, 'Times New Roman', Times, serif",
                "mono": "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace"
            },
            "font_sizes": {
                "xs": "0.75rem",
                "sm": "0.875rem",
                "base": "1rem",
                "lg": "1.125rem",
                "xl": "1.25rem",
                "2xl": "1.5rem",
                "3xl": "1.875rem",
                "4xl": "2.25rem"
            },
            "font_weights": {
                "light": "300",
                "normal": "400",
                "medium": "500",
                "semibold": "600",
                "bold": "700"
            },
            "line_heights": {
                "tight": "1.25",
                "normal": "1.5",
                "relaxed": "1.75"
            }
        }
    
    def _generate_css_tokens(self, design_system: DesignSystem) -> str:
        """生成CSS令牌"""
        css = f""":root {{
  /* Colors */
"""
        for name, value in design_system.colors.items():
            css += f"  --color-{name}: {value};\n"
        
        css += "\n  /* Typography */\n"
        for name, value in design_system.typography.get("font_sizes", {}).items():
            css += f"  --font-size-{name}: {value};\n"
        
        css += "\n  /* Spacing */\n"
        for name, value in design_system.spacing.items():
            css += f"  --spacing-{name}: {value};\n"
        
        css += "\n  /* Border Radius */\n"
        for name, value in design_system.border_radius.items():
            css += f"  --radius-{name}: {value};\n"
        
        css += "\n  /* Shadows */\n"
        for name, value in design_system.shadows.items():
            css += f"  --shadow-{name}: {value};\n"
        
        css += "}\n"
        
        return css
    
    def get_design_system(self) -> Optional[DesignSystem]:
        """获取当前设计系统"""
        return self._design_system
    
    def load_design_system(self, name: str) -> Optional[DesignSystem]:
        """加载设计系统"""
        system_file = self.systems_path / f"{name}-design-system.json"
        if system_file.exists():
            data = json.loads(system_file.read_text(encoding='utf-8'))
            data['theme'] = ThemeType(data['theme'])
            self._design_system = DesignSystem(**data)
            self._init_validators()
            return self._design_system
        return None
    
    def generate_report(self, output_format: str = "markdown") -> str:
        """
        生成 UI 设计报告
        
        Args:
            output_format: 输出格式
            
        Returns:
            报告内容
        """
        logger.info(f"Generating UI design report in {output_format} format")
        
        # 收集所有任务
        all_tasks = self.discover_tasks("all")
        
        # 统计信息
        stats = {
            "total_tasks": len(all_tasks),
            "pending": len([t for t in all_tasks if t.status == DesignStatus.PENDING]),
            "in_progress": len([t for t in all_tasks if t.status == DesignStatus.IN_PROGRESS]),
            "completed": len([t for t in all_tasks if t.status == DesignStatus.COMPLETED]),
            "needs_revision": len([t for t in all_tasks if t.status == DesignStatus.NEEDS_REVISION])
        }
        
        if output_format == "json":
            return json.dumps({
                "timestamp": datetime.now().isoformat(),
                "statistics": stats,
                "tasks": [asdict(t) for t in all_tasks]
            }, ensure_ascii=False, indent=2)
        
        elif output_format == "markdown":
            report = f"""# UI/UX 设计集成报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 统计概览

| 指标 | 数量 |
|------|------|
| 任务总数 | {stats['total_tasks']} |
| 待处理 | {stats['pending']} |
| 进行中 | {stats['in_progress']} |
| 已完成 | {stats['completed']} |
| 需修改 | {stats['needs_revision']} |

## 任务详情

"""
            for task in all_tasks:
                status_emoji = {
                    DesignStatus.PENDING: "⏳",
                    DesignStatus.IN_PROGRESS: "🔄",
                    DesignStatus.COMPLETED: "✅",
                    DesignStatus.NEEDS_REVISION: "⚠️"
                }.get(task.status, "❓")
                
                report += f"""### {status_emoji} {task.name}

- **类型**: {task.task_type.value}
- **状态**: {task.status.value}
- **优先级**: {task.priority}
- **项目类型**: {task.project_type}
- **技术栈**: {task.tech_stack}
- **描述**: {task.description}
- **负责部门**: {task.assigned_to}

"""
            
            return report
        
        else:
            return f"Unsupported format: {output_format}"
    
    def _analyze_design_requirements(self, page_type: str, project_type: str, 
                                     requirements: Dict = None) -> Dict:
        """分析设计需求"""
        return {
            "page_type": page_type,
            "project_type": project_type,
            "requirements": requirements or {},
            "target_platform": "web",
            "responsive": True
        }
    
    def _get_or_create_design_system(self, project_type: str) -> Dict:
        """获取或创建设计系统"""
        design_system_file = self.design_output_path / "design-system.json"
        
        if design_system_file.exists():
            return json.loads(design_system_file.read_text(encoding='utf-8'))
        
        # 创建默认设计系统
        design_system = {
            "colors": {
                "primary": "#1890ff",
                "secondary": "#52c41a",
                "error": "#ff4d4f",
                "warning": "#faad14",
                "success": "#52c41a",
                "text": "#262626",
                "text_secondary": "#595959",
                "background": "#ffffff",
                "border": "#d9d9d9"
            },
            "typography": {
                "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto",
                "font_sizes": {
                    "xs": "12px",
                    "sm": "14px",
                    "base": "16px",
                    "lg": "18px",
                    "xl": "20px",
                    "2xl": "24px"
                }
            },
            "spacing": {
                "xs": "4px",
                "sm": "8px",
                "md": "16px",
                "lg": "24px",
                "xl": "32px"
            },
            "border_radius": {
                "sm": "2px",
                "md": "4px",
                "lg": "8px"
            }
        }
        
        design_system_file.write_text(json.dumps(design_system, ensure_ascii=False, indent=2), 
                                      encoding='utf-8')
        
        return design_system
    
    def _design_page_layout(self, page_name: str, page_type: str, 
                            requirements: Dict) -> Dict:
        """设计页面布局"""
        # 根据页面类型生成布局
        layouts = {
            "dashboard": {
                "header": True,
                "sidebar": True,
                "content_areas": ["stats", "charts", "tables"],
                "grid": "12-column"
            },
            "landing": {
                "header": True,
                "hero": True,
                "features": True,
                "cta": True,
                "footer": True
            },
            "detail": {
                "header": True,
                "breadcrumb": True,
                "main_content": True,
                "sidebar": False
            }
        }
        
        layout = layouts.get(page_type, layouts["detail"])
        layout["page_name"] = page_name
        layout["page_type"] = page_type
        
        # 保存布局
        layout_file = self.design_output_path / f"{page_name}-layout.json"
        layout_file.write_text(json.dumps(layout, ensure_ascii=False, indent=2), 
                               encoding='utf-8')
        
        return layout
    
    def _generate_page_code(self, page_name: str, layout: Dict, 
                           design_system: Dict, tech_stack: str) -> Path:
        """生成页面代码"""
        # 确定输出路径
        if "Next.js" in tech_stack or "React" in tech_stack:
            output_dir = self.project_path / "src" / "pages"
            if not output_dir.exists():
                output_dir = self.project_path / "pages"
            extension = ".tsx"
        elif "Vue" in tech_stack:
            output_dir = self.project_path / "src" / "views"
            extension = ".vue"
        else:
            output_dir = self.project_path / "src"
            extension = ".tsx"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{page_name}{extension}"
        
        # 生成代码（简化版本）
        if extension == ".tsx":
            code = self._generate_react_page_code(page_name, layout, design_system)
        elif extension == ".vue":
            code = self._generate_vue_page_code(page_name, layout, design_system)
        else:
            code = self._generate_react_page_code(page_name, layout, design_system)
        
        output_file.write_text(code, encoding='utf-8')
        
        return output_file
    
    def _generate_react_page_code(self, page_name: str, layout: Dict, 
                                  design_system: Dict) -> str:
        """生成 React 页面代码"""
        header_section = ""
        if layout.get('header', False):
            header_section = f"""
        <header className="border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <h1 className="text-xl font-semibold">{page_name.title()}</h1>
              </div>
            </div>
          </div>
        </header>
"""
        
        return f"""import React from 'react';
import Head from 'next/head';

interface {page_name.title()}PageProps {{
  // 定义 props
}}

const {page_name.title()}Page: React.FC<{page_name.title()}PageProps> = () => {{
  return (
    <>
      <Head>
        <title>{page_name.title()} | App</title>
      </Head>
      
      <div className="min-h-screen bg-white">
        {{/* Header */}}
        {header_section}
        
        {{/* Main Content */}}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="space-y-6">
            {{/* Page content will be added here */}}
            <p className="text-gray-600">{page_name.title()} page content</p>
          </div>
        </main>
      </div>
    </>
  );
}};

export default {page_name.title()}Page;
"""
    
    def _generate_vue_page_code(self, page_name: str, layout: Dict, 
                                design_system: Dict) -> str:
        """生成 Vue 页面代码"""
        return f"""<template>
  <div class="min-h-screen bg-white">
    <!-- Header -->
    <header v-if="hasHeader" class="border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex items-center">
            <h1 class="text-xl font-semibold">{page_name.title()}</h1>
          </div>
        </div>
      </div>
    </header>
    
    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="space-y-6">
        <p class="text-gray-600">{page_name.title()} page content</p>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import {{ ref }} from 'vue';

const hasHeader = ref(true);
</script>
"""
    
    def _analyze_component_requirements(self, component_name: str, 
                                        component_type: str, 
                                        features: List[str] = None) -> Dict:
        """分析组件需求"""
        return {
            "name": component_name,
            "type": component_type,
            "features": features or [],
            "states": ["default", "hover", "active", "disabled"],
            "accessibility_level": "AA"
        }
    
    def _design_component(self, component_spec: Dict) -> Dict:
        """设计组件"""
        return {
            **component_spec,
            "design_tokens": {
                "colors": ["primary", "secondary", "error"],
                "spacing": ["sm", "md", "lg"],
                "typography": ["text-sm", "text-base", "text-lg"]
            }
        }
    
    def _generate_component_code(self, component_name: str, 
                                 component_design: Dict, 
                                 tech_stack: str) -> Path:
        """生成组件代码"""
        output_dir = self.project_path / "src" / "components" / component_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成组件文件
        if "React" in tech_stack:
            component_file = output_dir / f"{component_name}.tsx"
            component_code = f"""import React from 'react';

interface {component_name}Props {{
  // 定义 props
}}

export const {component_name}: React.FC<{component_name}Props> = (props) => {{
  return (
    <div className="{component_name.lower()}">
      {{/* Component content */}}
    </div>
  );
}};

export default {component_name};
"""
        else:
            component_file = output_dir / f"{component_name}.vue"
            component_code = f"""<template>
  <div class="{component_name.lower()}">
    <!-- Component content -->
  </div>
</template>

<script setup lang="ts">
// Component logic
</script>
"""
        
        component_file.write_text(component_code, encoding='utf-8')
        
        # 生成样式文件
        style_file = output_dir / f"{component_name}.module.css"
        style_code = f""".{component_name.lower()} {{
  /* Component styles */
}}
"""
        style_file.write_text(style_code, encoding='utf-8')
        
        return output_dir
    
    def _check_accessibility(self, target: Path) -> float:
        """检查可访问性"""
        score = 0.9  # 基础分
        
        if target.is_file():
            content = target.read_text(encoding='utf-8')
            
            # 检查 alt 属性
            if '<img' in content and 'alt=' not in content:
                score -= 0.1
            
            # 检查语义化标签
            semantic_tags = ['<header', '<nav', '<main', '<article', '<section']
            if not any(tag in content for tag in semantic_tags):
                score -= 0.05
        
        return max(score, 0)
    
    def _check_design_consistency(self, target: Path) -> float:
        """检查设计一致性"""
        score = 0.85
        
        # 检查是否使用设计系统
        design_system_file = self.design_output_path / "design-system.json"
        if design_system_file.exists():
            score += 0.1
        
        return min(score, 1.0)
    
    def _check_responsiveness(self, target: Path) -> float:
        """检查响应式设计"""
        score = 0.8
        
        if target.is_file():
            content = target.read_text(encoding='utf-8')
            
            # 检查响应式类名
            responsive_patterns = ['sm:', 'md:', 'lg:', 'xl:']
            if any(pattern in content for pattern in responsive_patterns):
                score += 0.15
            
            # 检查 viewport meta
            if 'viewport' in content:
                score += 0.05
        
        return min(score, 1.0)
    
    def _check_performance(self, target: Path) -> float:
        """检查性能"""
        score = 0.9
        
        if target.is_file():
            content = target.read_text(encoding='utf-8')
            
            # 检查图片优化
            if '<img' in content and 'loading=' not in content:
                score -= 0.05
        
        return max(score, 0)
    
    def _collect_validation_issues(self, target: Path) -> List[Dict]:
        """收集校验问题"""
        issues = []
        
        if target.is_file():
            content = target.read_text(encoding='utf-8')
            
            # 检查图片 alt
            if '<img' in content and 'alt=' not in content:
                issues.append({
                    "type": "accessibility",
                    "severity": "high",
                    "message": "图片缺少 alt 属性",
                    "line": None
                })
            
            # 检查内联样式
            if 'style={' in content:
                issues.append({
                    "type": "maintainability",
                    "severity": "medium",
                    "message": "使用内联样式，建议使用 CSS 类",
                    "line": None
                })
        
        return issues
    
    def _generate_validation_recommendations(self, issues: List[Dict]) -> List[str]:
        """生成校验建议"""
        recommendations = []
        
        for issue in issues:
            if issue["type"] == "accessibility":
                recommendations.append("添加适当的 ARIA 标签和 alt 属性")
            elif issue["type"] == "maintainability":
                recommendations.append("将样式提取到 CSS 模块或样式组件中")
        
        if not recommendations:
            recommendations.append("UI 质量良好，继续保持")
        
        return recommendations
    
    def _create_log_entry(self, operation: str, task_name: str, 
                          project_type: str, tech_stack: str) -> UIIntegrationLog:
        """创建日志条目"""
        return UIIntegrationLog(
            log_id=f"UI-{operation.upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            timestamp=datetime.now().isoformat(),
            operation=operation,
            task_name=task_name,
            project_type=project_type,
            tech_stack=tech_stack,
            requesting_department="工部",
            status="in_progress",
            duration_ms=0,
            design_outputs=[],
            validation_results={},
            errors=[]
        )
    
    def _save_log(self, log_entry: UIIntegrationLog):
        """保存日志"""
        log_file = self.logs_path / f"{log_entry.log_id}.json"
        log_file.write_text(json.dumps(asdict(log_entry), ensure_ascii=False, indent=2), 
                            encoding='utf-8')
    
    def _save_validation_result(self, result: ValidationResult):
        """保存校验结果"""
        result_file = self.reports_path / f"{result.validation_id}.json"
        data = asdict(result)
        data['overall_status'] = result.overall_status.value
        result_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), 
                               encoding='utf-8')


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="ui-ux-pro-max 集成脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python ui_ux_integration.py discover --scope=all
  python ui_ux_integration.py design --type=page --name=dashboard
  python ui_ux_integration.py validate --path=src/components/
  python ui_ux_integration.py system --generate --name=my-design --theme=modern
  python ui_ux_integration.py report --format=markdown
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    discover_parser = subparsers.add_parser("discover", help="发现需要 UI/UX 设计的任务")
    discover_parser.add_argument("--scope", choices=["all", "pages", "components", "systems", "pending"],
                                 default="all", help="发现范围")
    discover_parser.add_argument("--output", choices=["console", "json"], default="console", help="输出格式")
    
    design_parser = subparsers.add_parser("design", help="执行 UI/UX 设计")
    design_parser.add_argument("--type", choices=["page", "component", "system"], required=True, help="设计类型")
    design_parser.add_argument("--name", required=True, help="设计对象名称")
    design_parser.add_argument("--project-type", default="Web Application", help="项目类型")
    design_parser.add_argument("--tech-stack", default="React+Tailwind", help="技术栈")
    design_parser.add_argument("--page-type", default="dashboard", help="页面类型（仅页面设计）")
    
    validate_parser = subparsers.add_parser("validate", help="执行 UI 校验")
    validate_parser.add_argument("--path", required=True, help="校验目标路径")
    validate_parser.add_argument("--type", choices=["comprehensive", "accessibility", "responsive", "performance", "ux"],
                                 default="comprehensive", help="校验类型")
    validate_parser.add_argument("--dimensions", help="校验维度（逗号分隔）")
    
    ux_check_parser = subparsers.add_parser("ux-check", help="UX模式检查")
    ux_check_parser.add_argument("--path", required=True, help="检查目标路径")
    ux_check_parser.add_argument("--output", choices=["console", "json"], default="console", help="输出格式")
    
    system_parser = subparsers.add_parser("system", help="设计系统管理")
    system_parser.add_argument("--action", choices=["generate", "load", "show"], required=True, help="操作类型")
    system_parser.add_argument("--name", default="default", help="设计系统名称")
    system_parser.add_argument("--theme", choices=["modern", "dark", "minimal", "corporate", "creative"],
                               default="modern", help="主题类型")
    system_parser.add_argument("--colors", help="自定义颜色（JSON格式）")
    
    report_parser = subparsers.add_parser("report", help="生成 UI 设计报告")
    report_parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="报告格式")
    report_parser.add_argument("--output", help="输出文件路径")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    integration = UIUXIntegration()
    
    if args.command == "discover":
        tasks = integration.discover_tasks(args.scope)
        
        if args.output == "json":
            print(json.dumps([asdict(t) for t in tasks], ensure_ascii=False, indent=2))
        else:
            print(f"\n发现 {len(tasks)} 个 UI/UX 设计任务:\n")
            for task in tasks:
                status_icon = {
                    DesignStatus.PENDING: "⏳",
                    DesignStatus.IN_PROGRESS: "🔄",
                    DesignStatus.COMPLETED: "✅",
                    DesignStatus.NEEDS_REVISION: "⚠️",
                    DesignStatus.ARCHIVED: "📦"
                }.get(task.status, "❓")
                print(f"{status_icon} [{task.task_type.value}] {task.name} ({task.priority.value})")
                print(f"   描述: {task.description}")
                print(f"   技术栈: {task.tech_stack}")
                print()
    
    elif args.command == "design":
        if args.type == "page":
            success, message = integration.design_page(
                page_name=args.name,
                project_type=args.project_type,
                tech_stack=args.tech_stack,
                page_type=args.page_type
            )
        elif args.type == "component":
            success, message = integration.design_component(
                component_name=args.name,
                component_type="general",
                tech_stack=args.tech_stack
            )
        elif args.type == "system":
            theme = ThemeType(args.theme)
            design_system = integration.generate_design_system(
                name=args.name,
                theme=theme
            )
            message = f"设计系统 '{args.name}' 生成成功，主题: {theme.value}"
            success = True
        else:
            print(f"不支持的设计类型: {args.type}")
            sys.exit(1)
        
        print(message)
        sys.exit(0 if success else 1)
    
    elif args.command == "validate":
        dimensions = args.dimensions.split(",") if args.dimensions else None
        result = integration.validate_ui(args.path, args.type, dimensions)
        print(f"\nUI 校验结果: {result.target_path}")
        print(f"整体状态: {result.overall_status.value}")
        print(f"综合分数: {result.overall_score:.2f}")
        print(f"可访问性分数: {result.accessibility_score:.2f}")
        print(f"设计一致性分数: {result.design_consistency_score:.2f}")
        print(f"响应式分数: {result.responsive_score:.2f}")
        print(f"性能分数: {result.performance_score:.2f}")
        
        if result.usability_score > 0:
            print(f"可用性分数: {result.usability_score:.2f}")
        if result.interaction_score > 0:
            print(f"交互分数: {result.interaction_score:.2f}")
        if result.animation_score > 0:
            print(f"动画分数: {result.animation_score:.2f}")
        if result.color_contrast_score > 0:
            print(f"颜色对比度分数: {result.color_contrast_score:.2f}")
        
        if result.ux_patterns:
            print(f"\n检测到的UX模式: {', '.join(result.ux_patterns)}")
        
        if result.wcag_compliance:
            print(f"\nWCAG合规性:")
            print(f"  - WCAG A: {'✅' if result.wcag_compliance.get('wcag_a', False) else '❌'}")
            print(f"  - WCAG AA: {'✅' if result.wcag_compliance.get('wcag_aa', False) else '❌'}")
            print(f"  - WCAG AAA: {'✅' if result.wcag_compliance.get('wcag_aaa', False) else '❌'}")
        
        if result.issues:
            print("\n发现的问题:")
            for issue in result.issues:
                print(f"  [{issue['severity']}] {issue['message']}")
                if 'suggestion' in issue:
                    print(f"    建议: {issue['suggestion']}")
        
        if result.recommendations:
            print("\n优化建议:")
            for rec in result.recommendations:
                print(f"  - {rec}")
    
    elif args.command == "ux-check":
        result = integration.check_ux_patterns(args.path)
        
        if args.output == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"\nUX模式检查结果: {result['target']}")
            print(f"\n模式状态:")
            for pattern_name, info in result["patterns"].items():
                status = "✅" if info["found"] else "❌"
                importance = f"[{info['importance']}]"
                print(f"  {status} {importance} {pattern_name}: {info['description']}")
            
            if result["missing_patterns"]:
                print(f"\n缺失的重要模式:")
                for missing in result["missing_patterns"]:
                    if missing["importance"] in ["critical", "high"]:
                        print(f"  ⚠️ {missing['pattern']}: {missing['description']}")
            
            if result["recommendations"]:
                print(f"\n建议:")
                for rec in result["recommendations"]:
                    print(f"  - {rec}")
    
    elif args.command == "system":
        if args.action == "generate":
            theme = ThemeType(args.theme)
            colors = json.loads(args.colors) if args.colors else None
            design_system = integration.generate_design_system(
                name=args.name,
                theme=theme,
                colors=colors
            )
            print(f"设计系统 '{args.name}' 生成成功")
            print(f"主题: {theme.value}")
            print(f"颜色数量: {len(design_system.colors)}")
            print(f"输出文件: design/systems/{args.name}-design-system.json")
        
        elif args.action == "load":
            design_system = integration.load_design_system(args.name)
            if design_system:
                print(f"设计系统 '{args.name}' 加载成功")
                print(f"版本: {design_system.version}")
                print(f"主题: {design_system.theme.value}")
            else:
                print(f"设计系统 '{args.name}' 不存在")
                sys.exit(1)
        
        elif args.action == "show":
            design_system = integration.get_design_system()
            if design_system:
                print(json.dumps(asdict(design_system), ensure_ascii=False, indent=2))
            else:
                print("当前没有加载的设计系统")
    
    elif args.command == "report":
        report = integration.generate_report(args.format)
        if args.output:
            Path(args.output).write_text(report, encoding='utf-8')
            print(f"报告已保存到: {args.output}")
        else:
            print(report)


if __name__ == "__main__":
    main()
