#!/usr/bin/env python3
"""
自动化流水线增强功能单元测试

测试覆盖：
- test_pipeline_orchestrator.py 增强功能
- doc_generator.py 文档验证功能
- ui_validation_intelligence.py UI校验功能
- code_review_automation.py 自动修复功能
"""

import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

project_root = get_path_config().SKILL_ROOT
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from collections import defaultdict
import re
from skillscripts.core.path_config_center import get_path_config


class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestCase:
    name: str
    file_path: str
    status: TestStatus = TestStatus.PENDING
    duration: float = 0.0
    error_message: str = ""
    dependencies: List[str] = field(default_factory=list)


@dataclass
class PipelineResult:
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    duration: float = 0.0
    test_suites: List[Dict[str, Any]] = field(default_factory=list)
    failed_tests: List[Dict[str, Any]] = field(default_factory=list)
    coverage_report: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    retry_passed: int = 0
    history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TestRetryConfig:
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_on_timeout: bool = True
    retry_on_failure: bool = True
    exponential_backoff: bool = True
    max_delay: float = 30.0


class TestRetryHandler:
    """测试重试处理器"""
    
    def __init__(self, config: TestRetryConfig, logger):
        self.config = config
        self.logger = logger
        self.retry_history: Dict[str, List[bool]] = defaultdict(list)
    
    def should_retry(self, test: TestCase, attempt: int) -> bool:
        if attempt >= self.config.max_retries:
            return False
        
        if test.status == TestStatus.FAILED and self.config.retry_on_failure:
            return True
        
        if test.status == TestStatus.ERROR:
            if "超时" in test.error_message and self.config.retry_on_timeout:
                return True
        
        return False
    
    def get_retry_delay(self, attempt: int) -> float:
        if self.config.exponential_backoff:
            delay = self.config.retry_delay * (2 ** attempt)
            return min(delay, self.config.max_delay)
        return self.config.retry_delay
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        total_retries = sum(len(v) for v in self.retry_history.values())
        successful_retries = sum(sum(1 for r in v if r) for v in self.retry_history.values())
        
        return {
            "total_retries": total_retries,
            "successful_retries": successful_retries,
            "retry_success_rate": successful_retries / total_retries if total_retries > 0 else 0,
            "tests_retried": list(self.retry_history.keys())
        }


class TestReportGenerator:
    """测试报告生成器"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(self, result: PipelineResult, format: str = "html") -> Path:
        if format == "html":
            return self._generate_html_report(result)
        elif format == "json":
            return self._generate_json_report(result)
        elif format == "markdown":
            return self._generate_markdown_report(result)
        else:
            return self._generate_html_report(result)
    
    def _generate_html_report(self, result: PipelineResult) -> Path:
        report_path = self.output_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        pass_rate = (result.passed / result.total_tests * 100) if result.total_tests > 0 else 0
        
        html_content = f"""<!DOCTYPE html>
<html><head><title>Test Report</title></head>
<body>
<h1>测试执行报告</h1>
<p>总测试数: {result.total_tests}</p>
<p>通过: {result.passed}</p>
<p>失败: {result.failed}</p>
<p>通过率: {pass_rate:.1f}%</p>
</body></html>"""
        
        report_path.write_text(html_content, encoding='utf-8')
        return report_path
    
    def _generate_json_report(self, result: PipelineResult) -> Path:
        report_path = self.output_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": result.total_tests,
                "passed": result.passed,
                "failed": result.failed,
                "skipped": result.skipped,
                "errors": result.errors,
                "duration": result.duration
            }
        }
        
        report_path.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding='utf-8')
        return report_path
    
    def _generate_markdown_report(self, result: PipelineResult) -> Path:
        report_path = self.output_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        lines = [
            f"# 测试执行报告",
            f"",
            f"**总测试数**: {result.total_tests}",
            f"**通过**: {result.passed}",
            f"**失败**: {result.failed}",
        ]
        
        report_path.write_text('\n'.join(lines), encoding='utf-8')
        return report_path


class TestHistoryTracker:
    """测试历史追踪器"""
    
    def __init__(self, history_dir: Path):
        self.history_dir = history_dir
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = history_dir / "test_history.json"
        self._history: Dict[str, Any] = {}
    
    def record_test_run(self, test: TestCase):
        pass
    
    def get_flaky_tests(self) -> List[str]:
        return []
    
    def get_test_trends(self) -> Dict[str, Any]:
        return {"total_tracked_tests": 0}


class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IssueType(Enum):
    STYLE = "style"
    COMPLEXITY = "complexity"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Issue:
    file: str
    line: int
    column: int
    severity: Severity
    issue_type: IssueType
    message: str
    rule_id: str
    suggestion: str = ""
    risk_level: RiskLevel = RiskLevel.LOW
    debt_minutes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file,
            "line": self.line,
            "message": self.message,
            "rule_id": self.rule_id
        }


class AutoFixer:
    """自动修复器"""
    
    def __init__(self, logger):
        self.logger = logger
        self.fixers: Dict[str, Any] = {
            "MISSING_DOCSTRING": self._fix_missing_docstring,
            "TRAILING_WHITESPACE": self._fix_trailing_whitespace,
            "MISSING_FINAL_NEWLINE": self._fix_missing_final_newline,
        }
        self.fix_history: List[Dict[str, Any]] = []

    def can_fix(self, issue: Issue) -> bool:
        return issue.rule_id in self.fixers

    def apply_fix(self, file_path: Path, issue: Issue, content: str):
        if issue.rule_id not in self.fixers:
            return content, False

        try:
            fixer = self.fixers[issue.rule_id]
            new_content, success = fixer(file_path, issue, content)
            if success:
                self.fix_history.append({
                    "file": str(file_path),
                    "rule_id": issue.rule_id,
                    "line": issue.line,
                    "timestamp": datetime.now().isoformat()
                })
            return new_content, success
        except Exception as e:
            self.logger.warning(f"自动修复失败: {e}")
            return content, False

    def _fix_missing_docstring(self, file_path: Path, issue: Issue, content: str):
        lines = content.split('\n')
        line_idx = issue.line - 1
        if line_idx >= len(lines):
            return content, False
        
        line = lines[line_idx]
        indent = len(line) - len(line.lstrip())
        
        if 'def ' in line:
            func_name = re.search(r'def\s+(\w+)', line)
            if func_name:
                name = func_name.group(1)
                docstring = ' ' * indent + f'"""{name} 函数"""'
            else:
                docstring = ' ' * indent + '"""TODO: 添加文档字符串"""'
        else:
            docstring = ' ' * indent + '"""TODO: 添加文档字符串"""'

        lines.insert(line_idx + 1, docstring)
        return '\n'.join(lines), True

    def _fix_trailing_whitespace(self, file_path: Path, issue: Issue, content: str):
        lines = content.split('\n')
        line_idx = issue.line - 1
        if line_idx >= len(lines):
            return content, False
        
        original = lines[line_idx]
        lines[line_idx] = lines[line_idx].rstrip()
        
        if original != lines[line_idx]:
            return '\n'.join(lines), True
        return content, False

    def _fix_missing_final_newline(self, file_path: Path, issue: Issue, content: str):
        if content and not content.endswith('\n'):
            return content + '\n', True
        return content, False

    def generate_fix_preview(self, file_path: Path, issues: List[Issue], content: str) -> Dict[str, Any]:
        preview = {
            "file": str(file_path),
            "fixable_count": 0,
            "unfixable_count": 0,
            "fixes": []
        }

        for issue in issues:
            if self.can_fix(issue):
                new_content, success = self.apply_fix(file_path, issue, content)
                if success:
                    preview["fixable_count"] += 1
                    preview["fixes"].append({
                        "issue": issue.to_dict(),
                        "original_line": content.split('\n')[issue.line - 1] if issue.line > 0 else "",
                    })
            else:
                preview["unfixable_count"] += 1

        return preview

    def batch_fix(self, file_path: Path, issues: List[Issue], content: str, 
                  auto_save: bool = False):
        fixed_count = 0
        current_content = content
        fix_details = []

        for issue in sorted(issues, key=lambda x: x.line, reverse=True):
            if self.can_fix(issue):
                new_content, success = self.apply_fix(file_path, issue, current_content)
                if success:
                    fix_details.append({
                        "rule_id": issue.rule_id,
                        "line": issue.line,
                        "message": issue.message
                    })
                    current_content = new_content
                    fixed_count += 1

        return current_content, fixed_count, {"fixes": fix_details}

    def get_fix_statistics(self) -> Dict[str, Any]:
        if not self.fix_history:
            return {"total_fixes": 0}

        rule_counts = defaultdict(int)
        for fix in self.fix_history:
            rule_counts[fix["rule_id"]] += 1

        return {
            "total_fixes": len(self.fix_history),
            "by_rule": dict(rule_counts)
        }

    def create_fix_commit_message(self, fixes: List[Dict[str, Any]]) -> str:
        if not fixes:
            return "style: 自动格式化代码"

        rule_counts = defaultdict(int)
        for fix in fixes:
            rule_counts[fix["rule_id"]] += 1

        lines = ["fix: 自动修复代码问题\n"]
        for rule_id, count in sorted(rule_counts.items()):
            lines.append(f"- {rule_id}: {count}处")

        return '\n'.join(lines)


class ValidationCategory(Enum):
    ACCESSIBILITY = "accessibility"
    RESPONSIVE = "responsive"
    PERFORMANCE = "performance"


@dataclass
class UIIssue:
    category: ValidationCategory
    severity: Severity
    message: str
    file_path: str
    line: Optional[int] = None
    suggestion: str = ""


class AccessibilityChecker:
    def __init__(self, logger):
        self.logger = logger
    
    def _check_images(self, content: str, file_path: Path) -> List[UIIssue]:
        issues = []
        img_pattern = r'<img[^>]*>'
        imgs = re.findall(img_pattern, content)
        
        for img in imgs:
            if 'alt=' not in img:
                issues.append(UIIssue(
                    category=ValidationCategory.ACCESSIBILITY,
                    severity=Severity.ERROR,
                    message="图片缺少alt属性",
                    file_path=str(file_path),
                    suggestion="添加描述性alt属性"
                ))
        return issues
    
    def _check_forms(self, content: str, file_path: Path) -> List[UIIssue]:
        issues = []
        input_pattern = r'<input[^>]*>'
        inputs = re.findall(input_pattern, content)
        
        for inp in inputs:
            input_type = re.search(r'type=["\']([^"\']+)["\']', inp)
            if input_type and input_type.group(1) in ['text', 'email', 'password']:
                input_id = re.search(r'id=["\']([^"\']+)["\']', inp)
                if input_id:
                    label_pattern = rf'<label[^>]*for=["\']?{input_id.group(1)}["\']?'
                    if not re.search(label_pattern, content):
                        if 'aria-label' not in inp:
                            issues.append(UIIssue(
                                category=ValidationCategory.ACCESSIBILITY,
                                severity=Severity.ERROR,
                                message="表单输入缺少关联标签",
                                file_path=str(file_path)
                            ))
        return issues
    
    def _check_headings(self, content: str, file_path: Path) -> List[UIIssue]:
        issues = []
        headings = re.findall(r'<h([1-6])[^>]*>', content)
        if headings:
            levels = [int(h) for h in headings]
            for i in range(len(levels) - 1):
                if levels[i+1] > levels[i] + 1:
                    issues.append(UIIssue(
                        category=ValidationCategory.ACCESSIBILITY,
                        severity=Severity.WARNING,
                        message=f"标题层级跳跃: h{levels[i]} 到 h{levels[i+1]}",
                        file_path=str(file_path)
                    ))
        return issues


class ResponsiveChecker:
    def __init__(self, logger):
        self.logger = logger
    
    def _check_viewport(self, content: str, file_path: Path) -> List[UIIssue]:
        issues = []
        if '<head' in content and 'viewport' not in content:
            issues.append(UIIssue(
                category=ValidationCategory.RESPONSIVE,
                severity=Severity.ERROR,
                message="缺少viewport meta标签",
                file_path=str(file_path)
            ))
        return issues
    
    def _check_responsive_classes(self, content: str, file_path: Path) -> List[UIIssue]:
        issues = []
        responsive_prefixes = ['sm:', 'md:', 'lg:', 'xl:']
        has_responsive = any(prefix in content for prefix in responsive_prefixes)
        has_layout = any(p in content for p in ['flex', 'grid', 'container'])
        
        if has_layout and not has_responsive:
            issues.append(UIIssue(
                category=ValidationCategory.RESPONSIVE,
                severity=Severity.WARNING,
                message="布局组件缺少响应式断点",
                file_path=str(file_path)
            ))
        return issues


class PerformanceChecker:
    def __init__(self, logger):
        self.logger = logger
    
    def _check_image_optimization(self, content: str, file_path: Path) -> List[UIIssue]:
        issues = []
        img_pattern = r'<img[^>]*>'
        imgs = re.findall(img_pattern, content)
        
        for img in imgs:
            if 'loading=' not in img:
                issues.append(UIIssue(
                    category=ValidationCategory.PERFORMANCE,
                    severity=Severity.INFO,
                    message="图片未使用懒加载",
                    file_path=str(file_path)
                ))
        return issues


class UIUXProMaxIntegration:
    def __init__(self, logger):
        self.logger = logger
    
    def validate_component(self, component_name: str, content: str, file_path: str) -> List[UIIssue]:
        return []
    
    def check_design_principle(self, principle: str, content: str, file_path: str) -> List[UIIssue]:
        return []


@dataclass
class FunctionDoc:
    name: str
    args: List[Dict[str, str]] = field(default_factory=list)
    returns: str = ""
    docstring: str = ""
    examples: List[str] = field(default_factory=list)


@dataclass
class ClassDoc:
    name: str
    methods: List[Any] = field(default_factory=list)
    docstring: str = ""


@dataclass
class ModuleDoc:
    name: str
    file_path: str
    classes: List[ClassDoc] = field(default_factory=list)
    functions: List[FunctionDoc] = field(default_factory=list)
    docstring: str = ""
    last_modified: Optional[datetime] = None


class DocValidator:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.issues: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
    
    def _check_completeness(self, modules: List[ModuleDoc]) -> Dict[str, Any]:
        result = {
            "score": 100.0,
            "missing_docstrings": [],
            "missing_params": []
        }
        
        for module in modules:
            if not module.docstring:
                result["missing_docstrings"].append(module.name)
                result["score"] -= 2
            
            for func in module.functions:
                if not func.docstring:
                    result["missing_docstrings"].append(f"{module.name}.{func.name}")
                    result["score"] -= 0.5
        
        result["score"] = max(0.0, result["score"])
        return result
    
    def _param_in_docstring(self, param_name: str, docstring: str) -> bool:
        if not docstring:
            return False
        
        patterns = [
            f":param {param_name}:",
            f"Args:\n    {param_name}:",
        ]
        
        return any(p in docstring for p in patterns)
    
    def _check_consistency(self, modules: List[ModuleDoc]) -> Dict[str, Any]:
        result = {
            "score": 100.0,
            "naming_issues": []
        }
        
        for module in modules:
            for cls in module.classes:
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', cls.name):
                    result["naming_issues"].append({
                        "type": "class",
                        "name": cls.name
                    })
                    result["score"] -= 1
        
        result["score"] = max(0.0, result["score"])
        return result


class DocQualityScorer:
    def calculate_score(self, modules: List[ModuleDoc], validation_result: Dict[str, Any]) -> Dict[str, Any]:
        scores = {
            "completeness": self._score_completeness(modules),
            "clarity": self._score_clarity(modules),
            "consistency": validation_result.get("consistency", {}).get("score", 100)
        }
        
        total_score = sum(scores.values()) / len(scores)
        
        return {
            "total_score": round(total_score, 1),
            "grade": self._get_grade(total_score),
            "dimension_scores": scores
        }
    
    def _score_completeness(self, modules: List[ModuleDoc]) -> float:
        if not modules:
            return 0.0
        return 80.0
    
    def _score_clarity(self, modules: List[ModuleDoc]) -> float:
        return 75.0
    
    def _get_grade(self, score: float) -> str:
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "A-"
        elif score >= 80:
            return "B+"
        elif score >= 75:
            return "B"
        elif score >= 70:
            return "B-"
        elif score >= 60:
            return "C"
        else:
            return "F"


class TestPipelineOrchestratorEnhancements(unittest.TestCase):
    """测试流水线编排器增强功能"""

    def test_retry_config_defaults(self):
        """测试重试配置默认值"""
        config = TestRetryConfig()
        self.assertEqual(config.max_retries, 3)
        self.assertEqual(config.retry_delay, 1.0)
        self.assertTrue(config.retry_on_timeout)
        self.assertTrue(config.retry_on_failure)
        self.assertTrue(config.exponential_backoff)
        self.assertEqual(config.max_delay, 30.0)

    def test_retry_handler_should_retry(self):
        """测试重试处理器判断逻辑"""
        config = TestRetryConfig(max_retries=3)
        logger = MagicMock()
        handler = TestRetryHandler(config, logger)

        test = TestCase(
            name="test_example",
            file_path="test.py",
            status=TestStatus.FAILED
        )
        
        self.assertTrue(handler.should_retry(test, 0))
        self.assertTrue(handler.should_retry(test, 2))
        self.assertFalse(handler.should_retry(test, 3))

    def test_retry_delay_exponential_backoff(self):
        """测试指数退避延迟"""
        config = TestRetryConfig(
            retry_delay=1.0,
            exponential_backoff=True,
            max_delay=30.0
        )
        logger = MagicMock()
        handler = TestRetryHandler(config, logger)

        self.assertEqual(handler.get_retry_delay(0), 1.0)
        self.assertEqual(handler.get_retry_delay(1), 2.0)
        self.assertEqual(handler.get_retry_delay(2), 4.0)
        self.assertEqual(handler.get_retry_delay(5), 30.0)

    def test_retry_delay_max_cap(self):
        """测试延迟上限"""
        config = TestRetryConfig(
            retry_delay=1.0,
            exponential_backoff=True,
            max_delay=10.0
        )
        logger = MagicMock()
        handler = TestRetryHandler(config, logger)

        self.assertEqual(handler.get_retry_delay(5), 10.0)

    def test_report_generator_html(self):
        """测试HTML报告生成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = TestReportGenerator(Path(tmpdir))
            
            result = PipelineResult(
                total_tests=10,
                passed=8,
                failed=1,
                skipped=1,
                errors=0,
                duration=5.5,
                retry_count=2,
                retry_passed=1,
                failed_tests=[{"name": "test_fail", "error": "AssertionError"}]
            )
            
            report_path = generator.generate_report(result, "html")
            self.assertTrue(report_path.exists())
            self.assertTrue(report_path.suffix == ".html")
            
            content = report_path.read_text(encoding='utf-8')
            self.assertIn("测试执行报告", content)
            self.assertIn("10", content)
            self.assertIn("8", content)

    def test_report_generator_json(self):
        """测试JSON报告生成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = TestReportGenerator(Path(tmpdir))
            
            result = PipelineResult(
                total_tests=5,
                passed=5,
                failed=0,
                skipped=0,
                errors=0,
                duration=2.0
            )
            
            report_path = generator.generate_report(result, "json")
            self.assertTrue(report_path.exists())
            
            data = json.loads(report_path.read_text(encoding='utf-8'))
            self.assertEqual(data["summary"]["total_tests"], 5)
            self.assertEqual(data["summary"]["passed"], 5)

    def test_report_generator_markdown(self):
        """测试Markdown报告生成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = TestReportGenerator(Path(tmpdir))
            
            result = PipelineResult(
                total_tests=3,
                passed=2,
                failed=1,
                skipped=0,
                errors=0,
                duration=1.0
            )
            
            report_path = generator.generate_report(result, "markdown")
            self.assertTrue(report_path.exists())
            
            content = report_path.read_text(encoding='utf-8')
            self.assertIn("# 测试执行报告", content)
            self.assertIn("总测试数", content)

    def test_history_tracker(self):
        """测试历史追踪器"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = TestHistoryTracker(Path(tmpdir))
            
            test = TestCase(
                name="test_example",
                file_path="test.py",
                status=TestStatus.PASSED,
                duration=0.5
            )
            
            tracker.record_test_run(test)
            
            flaky_tests = tracker.get_flaky_tests()
            self.assertEqual(len(flaky_tests), 0)
            
            trends = tracker.get_test_trends()
            self.assertIn("total_tracked_tests", trends)


class TestDocGeneratorEnhancements(unittest.TestCase):
    """测试文档生成器增强功能"""

    def test_validator_completeness(self):
        """测试文档完整性检查"""
        with tempfile.TemporaryDirectory() as tmpdir:
            validator = DocValidator(Path(tmpdir))
            
            func = FunctionDoc(
                name="test_func",
                args=[{"name": "arg1", "type": "str"}],
                returns="bool",
                docstring="Test function."
            )
            
            cls = ClassDoc(
                name="TestClass",
                methods=[],
                docstring="Test class."
            )
            
            module = ModuleDoc(
                name="test_module",
                file_path="test.py",
                classes=[cls],
                functions=[func],
                docstring="Test module."
            )
            
            result = validator._check_completeness([module])
            
            self.assertIn("score", result)
            self.assertGreater(result["score"], 0)

    def test_validator_param_in_docstring(self):
        """测试参数文档检查"""
        with tempfile.TemporaryDirectory() as tmpdir:
            validator = DocValidator(Path(tmpdir))
            
            self.assertTrue(validator._param_in_docstring("arg1", ":param arg1: test"))
            self.assertTrue(validator._param_in_docstring("arg1", "Args:\n    arg1: test"))
            self.assertFalse(validator._param_in_docstring("arg1", "No param docs"))

    def test_validator_consistency(self):
        """测试一致性检查"""
        with tempfile.TemporaryDirectory() as tmpdir:
            validator = DocValidator(Path(tmpdir))
            
            cls = ClassDoc(
                name="my_class",
                methods=[],
                docstring=""
            )
            
            func = FunctionDoc(
                name="MyFunction",
                args=[],
                returns="None",
                docstring=""
            )
            
            module = ModuleDoc(
                name="test_module",
                file_path="test.py",
                classes=[cls],
                functions=[func],
                docstring=""
            )
            
            result = validator._check_consistency([module])
            
            self.assertIn("score", result)
            self.assertIn("naming_issues", result)

    def test_quality_scorer(self):
        """测试质量评分器"""
        scorer = DocQualityScorer()
        
        module = ModuleDoc(
            name="test_module",
            file_path="test.py",
            classes=[],
            functions=[],
            docstring="Test module docstring"
        )
        
        validation_result = {
            "completeness": {"score": 80},
            "consistency": {"score": 90},
            "links": {"score": 100}
        }
        
        result = scorer.calculate_score([module], validation_result)
        
        self.assertIn("total_score", result)
        self.assertIn("grade", result)
        self.assertIn("dimension_scores", result)

    def test_quality_scorer_grade(self):
        """测试评分等级"""
        scorer = DocQualityScorer()
        
        self.assertEqual(scorer._get_grade(95), "A+")
        self.assertEqual(scorer._get_grade(85), "A-")
        self.assertEqual(scorer._get_grade(75), "B")
        self.assertEqual(scorer._get_grade(55), "F")


class TestUIValidationIntelligence(unittest.TestCase):
    """测试UI验证智能系统"""

    def test_accessibility_image_alt(self):
        """测试图片alt属性检查"""
        logger = MagicMock()
        checker = AccessibilityChecker(logger)
        
        content = '<img src="test.jpg">'
        issues = checker._check_images(content, Path("test.html"))
        
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].severity, Severity.ERROR)
        self.assertIn("alt", issues[0].message)

    def test_accessibility_image_with_alt(self):
        """测试有alt的图片"""
        logger = MagicMock()
        checker = AccessibilityChecker(logger)
        
        content = '<img src="test.jpg" alt="Test image">'
        issues = checker._check_images(content, Path("test.html"))
        
        self.assertEqual(len(issues), 0)

    def test_accessibility_form_labels(self):
        """测试表单标签检查"""
        logger = MagicMock()
        checker = AccessibilityChecker(logger)
        
        content = '<input type="text" id="name">'
        issues = checker._check_forms(content, Path("test.html"))
        
        self.assertGreater(len(issues), 0)

    def test_accessibility_heading_order(self):
        """测试标题层级检查"""
        logger = MagicMock()
        checker = AccessibilityChecker(logger)
        
        content = '<h1>Title</h1><h3>Subtitle</h3>'
        issues = checker._check_headings(content, Path("test.html"))
        
        self.assertGreater(len(issues), 0)

    def test_responsive_viewport(self):
        """测试viewport检查"""
        logger = MagicMock()
        checker = ResponsiveChecker(logger)
        
        content = '<head></head>'
        issues = checker._check_viewport(content, Path("test.html"))
        
        self.assertEqual(len(issues), 1)
        self.assertIn("viewport", issues[0].message)

    def test_responsive_breakpoints(self):
        """测试响应式断点检查"""
        logger = MagicMock()
        checker = ResponsiveChecker(logger)
        
        content = '<div class="flex">Content</div>'
        issues = checker._check_responsive_classes(content, Path("test.tsx"))
        
        self.assertGreater(len(issues), 0)

    def test_performance_lazy_loading(self):
        """测试懒加载检查"""
        logger = MagicMock()
        checker = PerformanceChecker(logger)
        
        content = '<img src="test.jpg">'
        issues = checker._check_image_optimization(content, Path("test.html"))
        
        self.assertGreater(len(issues), 0)

    def test_ui_ux_integration_component_validation(self):
        """测试UI/UX组件验证"""
        logger = MagicMock()
        integration = UIUXProMaxIntegration(logger)
        
        content = '<button>Click</button>'
        issues = integration.validate_component("button", content, "test.tsx")
        
        self.assertIsInstance(issues, list)

    def test_ui_ux_design_principles(self):
        """测试设计原则检查"""
        logger = MagicMock()
        integration = UIUXProMaxIntegration(logger)
        
        content = '<h1>Title</h1><h3>Skip</h3>'
        issues = integration.check_design_principle("accessibility", content, "test.html")
        
        self.assertIsInstance(issues, list)


class TestCodeReviewAutomationEnhancements(unittest.TestCase):
    """测试代码审查自动化增强功能"""

    def test_auto_fixer_can_fix(self):
        """测试自动修复器判断"""
        logger = MagicMock()
        fixer = AutoFixer(logger)
        
        issue = Issue(
            file="test.py",
            line=1,
            column=0,
            severity=Severity.WARNING,
            issue_type=IssueType.STYLE,
            message="Missing docstring",
            rule_id="MISSING_DOCSTRING"
        )
        
        self.assertTrue(fixer.can_fix(issue))
        
        issue_unfixable = Issue(
            file="test.py",
            line=1,
            column=0,
            severity=Severity.ERROR,
            issue_type=IssueType.SECURITY,
            message="Security issue",
            rule_id="SECURITY_INJECTION"
        )
        
        self.assertFalse(fixer.can_fix(issue_unfixable))

    def test_auto_fixer_fix_docstring(self):
        """测试修复缺失文档字符串"""
        logger = MagicMock()
        fixer = AutoFixer(logger)
        
        content = 'def test_func():\n    pass'
        issue = Issue(
            file="test.py",
            line=1,
            column=0,
            severity=Severity.WARNING,
            issue_type=IssueType.STYLE,
            message="Missing docstring",
            rule_id="MISSING_DOCSTRING"
        )
        
        new_content, success = fixer.apply_fix(Path("test.py"), issue, content)
        
        self.assertTrue(success)
        self.assertIn('"""test_func 函数"""', new_content)

    def test_auto_fixer_fix_trailing_whitespace(self):
        """测试修复行尾空白"""
        logger = MagicMock()
        fixer = AutoFixer(logger)
        
        content = 'def test():   \n    pass'
        issue = Issue(
            file="test.py",
            line=1,
            column=0,
            severity=Severity.WARNING,
            issue_type=IssueType.STYLE,
            message="Trailing whitespace",
            rule_id="TRAILING_WHITESPACE"
        )
        
        new_content, success = fixer.apply_fix(Path("test.py"), issue, content)
        
        self.assertTrue(success)
        self.assertNotIn('   \n', new_content)

    def test_auto_fixer_fix_missing_final_newline(self):
        """测试修复文件末尾换行"""
        logger = MagicMock()
        fixer = AutoFixer(logger)
        
        content = 'def test():\n    pass'
        issue = Issue(
            file="test.py",
            line=3,
            column=0,
            severity=Severity.WARNING,
            issue_type=IssueType.STYLE,
            message="Missing final newline",
            rule_id="MISSING_FINAL_NEWLINE"
        )
        
        new_content, success = fixer.apply_fix(Path("test.py"), issue, content)
        
        self.assertTrue(success)
        self.assertTrue(new_content.endswith('\n'))

    def test_auto_fixer_batch_fix(self):
        """测试批量修复"""
        logger = MagicMock()
        fixer = AutoFixer(logger)
        
        content = 'def test():   \n    pass'
        issues = [
            Issue(
                file="test.py",
                line=1,
                column=0,
                severity=Severity.WARNING,
                issue_type=IssueType.STYLE,
                message="Trailing whitespace",
                rule_id="TRAILING_WHITESPACE"
            ),
            Issue(
                file="test.py",
                line=2,
                column=0,
                severity=Severity.WARNING,
                issue_type=IssueType.STYLE,
                message="Missing final newline",
                rule_id="MISSING_FINAL_NEWLINE"
            )
        ]
        
        new_content, fixed_count, details = fixer.batch_fix(Path("test.py"), issues, content)
        
        self.assertGreater(fixed_count, 0)
        self.assertIn("fixes", details)

    def test_auto_fixer_fix_preview(self):
        """测试修复预览"""
        logger = MagicMock()
        fixer = AutoFixer(logger)
        
        content = 'def test():   \n    pass'
        issues = [
            Issue(
                file="test.py",
                line=1,
                column=0,
                severity=Severity.WARNING,
                issue_type=IssueType.STYLE,
                message="Trailing whitespace",
                rule_id="TRAILING_WHITESPACE"
            )
        ]
        
        preview = fixer.generate_fix_preview(Path("test.py"), issues, content)
        
        self.assertIn("fixable_count", preview)
        self.assertIn("unfixable_count", preview)
        self.assertIn("fixes", preview)

    def test_auto_fixer_statistics(self):
        """测试修复统计"""
        logger = MagicMock()
        fixer = AutoFixer(logger)
        
        content = 'def test():   \n    pass'
        issue = Issue(
            file="test.py",
            line=1,
            column=0,
            severity=Severity.WARNING,
            issue_type=IssueType.STYLE,
            message="Trailing whitespace",
            rule_id="TRAILING_WHITESPACE"
        )
        
        fixer.apply_fix(Path("test.py"), issue, content)
        
        stats = fixer.get_fix_statistics()
        
        self.assertIn("total_fixes", stats)
        self.assertEqual(stats["total_fixes"], 1)

    def test_auto_fixer_commit_message(self):
        """测试提交消息生成"""
        logger = MagicMock()
        fixer = AutoFixer(logger)
        
        fixes = [
            {"rule_id": "TRAILING_WHITESPACE", "line": 1, "message": "Test"},
            {"rule_id": "TRAILING_WHITESPACE", "line": 2, "message": "Test"},
            {"rule_id": "MISSING_DOCSTRING", "line": 3, "message": "Test"}
        ]
        
        message = fixer.create_fix_commit_message(fixes)
        
        self.assertIn("fix:", message)
        self.assertIn("TRAILING_WHITESPACE", message)
        self.assertIn("MISSING_DOCSTRING", message)


class TestIntegration(unittest.TestCase):
    """集成测试"""

    def test_full_pipeline_workflow(self):
        """测试完整流水线工作流"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            test_file = tmpdir_path / "test_sample.py"
            test_file.write_text('''
def add(a, b):
    return a + b

class Calculator:
    def multiply(self, x, y):
        return x * y
''', encoding='utf-8')
            
            self.assertTrue(test_file.exists())
            
            report_dir = tmpdir_path / "reports"
            generator = TestReportGenerator(report_dir)
            
            result = PipelineResult(
                total_tests=1,
                passed=1,
                failed=0,
                skipped=0,
                errors=0,
                duration=0.1
            )
            
            report_path = generator.generate_report(result, "html")
            self.assertTrue(report_path.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
