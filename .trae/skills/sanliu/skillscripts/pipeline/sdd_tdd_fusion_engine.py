#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDD-TDD 深度融合引擎

实现规范驱动开发(SDD)与测试驱动开发(TDD)的完整闭环融合:
- 红阶段(Red): SDD规范解析 -> 提取需求 -> 生成测试骨架
- 绿阶段(Green): 测试失败分析 -> 驱动代码实现引导
- 蓝阶段(Blue): 测试通过 -> 重构建议 -> 优化实施
- 回归阶段(Regression): 回归验证 -> 产物追溯 -> 规范文档更新

集成点:
- provincial_coordinator.py: 省级协调器对接
- version_iterator.py: 版本迭代器对接
- continuous_evolution_controller.py: 持续演化控制器对接
- PathConfigCenter: 路径配置中心集成

用法:
    from skillscripts.pipeline.sdd_tdd_fusion_engine import SDDTDDFusionEngine
    
    engine = SDDTDDFusionEngine()
    report = engine.execute_cycle("specs/user_auth.md")
    
    # 连续多轮循环
    continuous_report = engine.execute_continuous_cycles(
        "specs/user_auth.md", max_cycles=3
    )
"""

import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable


class FusionPhase(Enum):
    """融合阶段枚举"""
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    REGRESSION = "regression"


class PhaseStatus(Enum):
    """阶段状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class CycleStatus(Enum):
    """循环状态枚举"""
    SUCCESS = "success"
    PARTIAL_FAILURE = "partial_failure"
    FAILURE = "failure"


class TestPriority(Enum):
    """测试优先级枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Requirement:
    """需求定义"""
    req_id: str
    title: str
    description: str = ""
    priority: str = "medium"
    acceptance_criteria: List[str] = field(default_factory=list)
    source_section: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class AcceptanceCriterion:
    """验收标准"""
    criterion_id: str
    description: str
    given: str = ""
    when: str = ""
    then: str = ""
    priority: str = "medium"
    verified: bool = False


@dataclass
class SDDSpec:
    """SDD规范"""
    spec_id: str
    title: str
    requirements: List[Requirement] = field(default_factory=list)
    acceptance_criteria: List[AcceptanceCriterion] = field(default_factory=list)
    version: str = "v1.0"
    source_path: str = ""
    raw_content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestCase:
    """测试用例"""
    test_id: str
    name: str
    description: str
    given: str
    when: str
    then: str
    priority: str = "medium"
    tags: List[str] = field(default_factory=list)
    source_requirement: str = ""
    status: str = "pending"
    code: str = ""


@dataclass
class TestResult:
    """测试执行结果"""
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    duration: float = 0.0
    test_results: List[Dict[str, Any]] = field(default_factory=list)
    output: str = ""
    success: bool = False


@dataclass
class FailureInfo:
    """失败信息"""
    test_name: str
    error_type: str
    error_message: str
    traceback: str = ""
    line_number: int = 0
    suggested_fix: str = ""


@dataclass
class FailureAnalysis:
    """失败分析结果"""
    failures: List[FailureInfo] = field(default_factory=list)
    failure_patterns: List[str] = field(default_factory=list)
    root_cause_summary: str = ""
    severity: str = "medium"
    fix_suggestions: List[str] = field(default_factory=list)


@dataclass
class ImplementationGuide:
    """代码实现引导"""
    guide_id: str
    target_tests: List[str] = field(default_factory=list)
    implementation_steps: List[Dict[str, Any]] = field(default_factory=list)
    suggested_signatures: List[Dict[str, str]] = field(default_factory=list)
    priority_order: List[str] = field(default_factory=list)
    estimated_effort: str = "medium"
    dependencies: List[str] = field(default_factory=list)


@dataclass
class RefactoringSuggestion:
    """重构建议"""
    suggestion_id: str
    refactoring_type: str
    target_file: str
    target_location: str
    description: str
    before_code: str = ""
    after_code: str = ""
    estimated_effort: str = "medium"
    impact: str = "medium"
    rationale: str = ""
    risk_level: str = "low"


@dataclass
class OptimizationResult:
    """优化实施结果"""
    applied_suggestions: List[RefactoringSuggestion] = field(default_factory=list)
    successful_count: int = 0
    failed_count: int = 0
    quality_improvement: Dict[str, float] = field(default_factory=dict)
    rollback_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RegressionResult:
    """回归测试结果"""
    regression_id: str
    test_paths: List[str] = field(default_factory=list)
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    new_failures: List[str] = field(default_factory=list)
    fixed_tests: List[str] = field(default_factory=list)
    duration: float = 0.0
    stable: bool = True
    coverage_delta: float = 0.0


@dataclass
class ArtifactTrace:
    """产物追溯"""
    trace_id: str
    cycle_id: str
    artifacts: Dict[str, List[Path]] = field(default_factory=dict)
    spec_version: str = ""
    generated_at: str = ""
    completeness_score: float = 0.0
    trace_matrix: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class PhaseResult:
    """阶段执行结果"""
    phase: FusionPhase
    status: PhaseStatus
    start_time: str = ""
    end_time: str = ""
    duration: float = 0.0
    output: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CycleReport:
    """循环报告"""
    cycle_id: str
    start_time: datetime
    end_time: datetime
    phase_results: Dict[str, Any]
    artifacts: List[Path]
    quality_metrics: Dict[str, float]
    status: str
    spec_path: str = ""
    summary: str = ""


@dataclass
class ContinuousCycleReport:
    """连续循环报告"""
    report_id: str
    cycles: List[CycleReport] = field(default_factory=list)
    total_cycles: int = 0
    successful_cycles: int = 0
    overall_status: str = "success"
    quality_trend: List[Dict[str, float]] = field(default_factory=list)
    improvement_summary: str = ""
    started_at: str = ""
    completed_at: str = ""


@dataclass
class FusionEngineConfig:
    """引擎配置"""
    max_iterations: int = 10
    coverage_threshold: float = 80.0
    quality_threshold: float = 70.0
    test_timeout: int = 300
    fail_fast: bool = False
    verbose: bool = False
    enable_refactoring: bool = True
    enable_regression: bool = True
    auto_generate_implementation: bool = False
    output_dir: Optional[str] = None
    test_dir: Optional[str] = None
    report_format: str = "both"


class SDDSpecParser:
    """SDD规范解析器"""
    
    SUPPORTED_FORMATS = {".md", ".yaml", ".yml", ".json"}
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def parse(self, spec_path: Path) -> SDDSpec:
        """解析SDD规范文档"""
        if not spec_path.exists():
            raise FileNotFoundError(f"规范文件不存在: {spec_path}")
        
        with open(spec_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        suffix = spec_path.suffix.lower()
        
        if suffix == ".md":
            return self._parse_markdown(content, spec_path)
        elif suffix in [".yaml", ".yml"]:
            return self._parse_yaml(content, spec_path)
        elif suffix == ".json":
            return self._parse_json(content, spec_path)
        else:
            raise ValueError(f"不支持的规范格式: {suffix}")
    
    def _parse_markdown(self, content: str, path: Path) -> SDDSpec:
        """解析Markdown格式规范"""
        spec_id = self._extract_spec_id(content)
        title = self._extract_title(content)
        version = self._extract_version(content)
        
        requirements = self._extract_requirements(content)
        acceptance_criteria = self._extract_acceptance_criteria(content)
        metadata = self._extract_metadata(content)
        
        return SDDSpec(
            spec_id=spec_id,
            title=title,
            requirements=requirements,
            acceptance_criteria=acceptance_criteria,
            version=version,
            source_path=str(path),
            raw_content=content,
            metadata=metadata
        )
    
    def _parse_yaml(self, content: str, path: Path) -> SDDSpec:
        """解析YAML格式规范"""
        try:
            import yaml
            data = yaml.safe_load(content)
        except ImportError:
            raise RuntimeError("需要安装 PyYAML: pip install pyyaml")
        
        if not isinstance(data, dict):
            raise ValueError("YAML格式错误: 根元素必须是字典")
        
        metadata = data.get("metadata", {})
        spec_data = data.get("spec", data)
        
        spec_id = metadata.get("id", data.get("id", f"SPC-{datetime.now().strftime('%Y%m%d%H%M%S')}"))
        title = metadata.get("name", data.get("name", "未命名规范"))
        version = metadata.get("version", data.get("version", "v1.0"))
        
        requirements = []
        for idx, req in enumerate(spec_data.get("requirements", [])):
            if isinstance(req, dict):
                requirements.append(Requirement(
                    req_id=req.get("id", f"REQ-{idx+1:03d}"),
                    title=req.get("title", ""),
                    description=req.get("description", ""),
                    priority=req.get("priority", "medium"),
                    acceptance_criteria=req.get("acceptance_criteria", []),
                    tags=req.get("tags", [])
                ))
            elif isinstance(req, str):
                requirements.append(Requirement(
                    req_id=f"REQ-{idx+1:03d}",
                    title=req,
                    priority="medium"
                ))
        
        acceptance_criteria = []
        for idx, ac in enumerate(spec_data.get("acceptance_criteria", spec_data.get("scenarios", []))):
            if isinstance(ac, dict):
                acceptance_criteria.append(AcceptanceCriterion(
                    criterion_id=ac.get("id", f"AC-{idx+1:03d}"),
                    description=ac.get("description", ac.get("then", "")),
                    given=ac.get("given", ""),
                    when=ac.get("when", ""),
                    then=ac.get("then", ""),
                    priority=ac.get("priority", "medium")
                ))
        
        return SDDSpec(
            spec_id=spec_id,
            title=title,
            requirements=requirements,
            acceptance_criteria=acceptance_criteria,
            version=version,
            source_path=str(path),
            raw_content=content,
            metadata=metadata
        )
    
    def _parse_json(self, content: str, path: Path) -> SDDSpec:
        """解析JSON格式规范"""
        data = json.loads(content)
        if isinstance(data, list):
            data = {"requirements": data}
        return self._parse_yaml(json.dumps(data, ensure_ascii=False), path)
    
    def _extract_spec_id(self, content: str) -> str:
        match = re.search(r"(?:规范ID|spec[_\s]?id)[：:\s]*(\S+)", content, re.IGNORECASE)
        return match.group(1).strip() if match else f"SPC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def _extract_title(self, content: str) -> str:
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        return match.group(1).strip() if match else "未命名规范"
    
    def _extract_version(self, content: str) -> str:
        match = re.search(r"(?:版本|version)[：:\s]*(\S+)", content, re.IGNORECASE)
        return match.group(1).strip() if match else "v1.0"
    
    def _extract_requirements(self, content: str) -> List[Requirement]:
        requirements = []
        
        req_patterns = [
            r"(?:##\s*功能需求|##\s*需求列表)\s*\n((?:.+\n?)*?)(?=\n##|\Z)",
            r"(?:###\s*需求[：:]?\s*.+)\s*\n((?:[-*]\s*.+\n?)+)",
        ]
        
        for pattern in req_patterns:
            for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
                lines = match.group(1).strip().split("\n") if match.group(1) else []
                for line in lines:
                    line = line.strip()
                    if line.startswith("-") or line.startswith("*"):
                        text = line.lstrip("-* ").strip()
                        if text and len(text) > 2:
                            req_id = f"REQ-{len(requirements)+1:03d}"
                            title_match = re.match(r"^([^\[：:]+)", text)
                            title = title_match.group(1).strip() if title_match else text
                            requirements.append(Requirement(
                                req_id=req_id,
                                title=title,
                                description=text,
                                priority=self._infer_priority(text),
                                source_section=match.group(0)[:50] if match.group(0) else ""
                            ))
        
        if not requirements:
            requirements.append(Requirement(
                req_id="REQ-001",
                title="默认需求",
                description=content[:200],
                priority="medium"
            ))
        
        return requirements
    
    def _extract_acceptance_criteria(self, content: str) -> List[AcceptanceCriterion]:
        criteria = []
        
        ac_pattern = r"(?:Given|给定)[：:\s]*([^\n]+)\s*\n?(?:When|当|何时)[：:\s]*([^\n]+)\s*\n?(?:Then|那么|则)[：:\s]*([^\n]+)"
        for match in re.finditer(ac_pattern, content, re.IGNORECASE):
            criteria.append(AcceptanceCriterion(
                criterion_id=f"AC-{len(criteria)+1:03d}",
                description=f"{match.group(1)} -> {match.group(2)} -> {match.group(3)}",
                given=match.group(1).strip(),
                when=match.group(2).strip(),
                then=match.group(3).strip(),
                priority="high"
            ))
        
        scenario_pattern = r"###\s*(?:场景|Scenario)[：:\s]*(.+?)\s*\n((?:.+\n?)*?)(?=\n###|\n##|\Z)"
        for match in re.finditer(scenario_pattern, content, re.MULTILINE | re.DOTALL):
            scenario_body = match.group(2)
            given_m = re.search(r"(?:Given|给定)[：:\s]*([^\n]+)", scenario_body, re.IGNORECASE)
            when_m = re.search(r"(?:When|当)[：:\s]*([^\n]+)", scenario_body, re.IGNORECASE)
            then_m = re.search(r"(?:Then|那么)[：:\s]*([^\n]+)", scenario_body, re.IGNORECASE)
            
            if given_m or when_m or then_m:
                criteria.append(AcceptanceCriterion(
                    criterion_id=f"AC-{len(criteria)+1:03d}",
                    description=match.group(1).strip(),
                    given=given_m.group(1).strip() if given_m else "",
                    when=when_m.group(1).strip() if when_m else "",
                    then=then_m.group(1).strip() if then_m else "",
                    priority="medium"
                ))
        
        return criteria
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        metadata = {}
        
        author_match = re.search(r"(?:作者|author)[：:\s]*(.+)$", content, re.IGNORECASE | re.MULTILINE)
        if author_match:
            metadata["author"] = author_match.group(1).strip()
        
        status_match = re.search(r"(?:状态|status)[：:\s]*(\w+)", content, re.IGNORECASE)
        if status_match:
            metadata["status"] = status_match.group(1).strip()
        
        return metadata
    
    def _infer_priority(self, text: str) -> str:
        text_lower = text.lower()
        if any(kw in text_lower for kw in ["核心", "关键", "必须", "critical", "must"]):
            return "critical"
        elif any(kw in text_lower for kw in ["重要", "主要", "应该", "important", "should"]):
            return "high"
        elif any(kw in text_lower for kw in ["可选", "次要", "optional", "minor"]):
            return "low"
        return "medium"


class TestSkeletonGenerator:
    """测试骨架生成器"""
    
    TEST_TEMPLATE = '''def {test_name}():
    """
    {description}
    
    来源需求: {source_requirement}
    优先级: {priority}
    """
    # Given: {given}
    {given_code}
    
    # When: {when}
    {when_code}
    
    # Then: {then}
    {then_code}
'''
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._test_counter = 0
    
    def generate(self, spec: SDDSpec) -> List[TestCase]:
        """从SDD规范生成测试骨架"""
        test_cases = []
        
        for req in spec.requirements:
            req_tests = self._generate_requirement_tests(spec, req)
            test_cases.extend(req_tests)
        
        for ac in spec.acceptance_criteria:
            ac_test = self._generate_acceptance_test(spec, ac)
            if ac_test:
                test_cases.append(ac_test)
        
        for tc in test_cases:
            tc.code = self._render_test_code(tc)
        
        return test_cases
    
    def _generate_requirement_tests(self, spec: SDDSpec, req: Requirement) -> List[TestCase]:
        """为需求生成测试用例"""
        tests = []
        
        positive_test = TestCase(
            test_id=f"TC-{spec.spec_id}-{req.req_id}-001",
            name=f"test_{self._sanitize_name(req.title)}_happy_path",
            description=f"验证: {req.title} - 正常流程",
            given=req.description[:100] if req.description else "系统处于初始状态",
            when=f"执行 {req.title} 相关操作",
            then=f"操作成功完成，符合预期结果",
            priority=req.priority,
            tags=["happy_path", "unit"],
            source_requirement=req.req_id
        )
        tests.append(positive_test)
        
        if req.priority in ["critical", "high"]:
            boundary_test = TestCase(
                test_id=f"TC-{spec.spec_id}-{req.req_id}-002",
                name=f"test_{self._sanitize_name(req.title)}_boundary",
                description=f"验证: {req.title} - 边界条件",
                given="准备边界值输入数据",
                when=f"使用边界值执行 {req.title} 操作",
                then="系统能正确处理边界情况",
                priority=req.priority,
                tags=["boundary", "unit"],
                source_requirement=req.req_id
            )
            tests.append(boundary_test)
        
        error_test = TestCase(
            test_id=f"TC-{spec.spec_id}-{req.req_id}-003",
            name=f"test_{self._sanitize_name(req.title)}_error_handling",
            description=f"验证: {req.title} - 异常处理",
            given="准备异常输入或模拟异常条件",
            when=f"触发 {req.title} 的异常场景",
            then="系统正确处理异常，返回适当错误信息",
            priority="high" if req.priority == "critical" else "medium",
            tags=["error_handling", "unit"],
            source_requirement=req.req_id
        )
        tests.append(error_test)
        
        return tests
    
    def _generate_acceptance_test(self, spec: SDDSpec, ac: AcceptanceCriterion) -> Optional[TestCase]:
        """为验收标准生成测试用例"""
        if not ac.given and not ac.when and not ac.then:
            return None
        
        self._test_counter += 1
        
        name_parts = [ac.then[:30] if ac.then else ac.description[:30]]
        test_name = f"test_acceptance_{self._test_counter:03d}_{self._sanitize_name('_'.join(name_parts))}"
        
        return TestCase(
            test_id=f"TC-{spec.spec_id}-AC-{self._test_counter:03d}",
            name=test_name,
            description=ac.description or f"验收标准: {ac.given} -> {ac.when} -> {ac.then}",
            given=ac.given or "满足前置条件",
            when=ac.when or "执行相关操作",
            then=ac.then or "验证预期结果",
            priority=ac.priority,
            tags=["acceptance", "integration"],
            source_requirement=ac.criterion_id
        )
    
    def _render_test_code(self, tc: TestCase) -> str:
        """渲染测试代码"""
        return self.TEST_TEMPLATE.format(
            test_name=tc.name,
            description=tc.description,
            source_requirement=tc.source_requirement,
            priority=tc.priority,
            given=tc.given,
            given_code="# TODO: 实现前置条件准备",
            when=tc.when,
            when_code="# TODO: 实现操作执行",
            then=tc.then,
            then_code="assert False, '测试尚未实现 (红阶段)'"
        )
    
    def _sanitize_name(self, name: str) -> str:
        """清理名称使其可作为标识符"""
        name = re.sub(r'[^\w\s]', '', name)
        name = re.sub(r'\s+', '_', name.strip())
        return name.lower()[:50] if name else "unnamed"


class TestRunner:
    """测试运行器"""
    
    def __init__(self, config: Optional[FusionEngineConfig] = None, 
                 logger: Optional[logging.Logger] = None):
        self.config = config or FusionEngineConfig()
        self.logger = logger or logging.getLogger(__name__)
    
    def run(self, test_paths: List[Path]) -> TestResult:
        """执行测试并收集结果"""
        result = TestResult()
        start_time = datetime.now()
        
        if not test_paths:
            self.logger.warning("没有可执行的测试文件")
            return result
        
        test_files = [str(p) for p in test_paths if p.exists()]
        if not test_files:
            self.logger.warning("所有测试文件都不存在")
            result.errors = len(test_paths)
            return result
        
        cmd = [
            sys.executable, "-m", "pytest",
            *test_files,
            "-v", "--tb=short",
            f"--timeout={self.config.test_timeout}",
            "-q"
        ]
        
        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.test_timeout + 30
            )
            
            result.output = process.stdout + "\n" + process.stderr
            
            passed_matches = re.findall(r'(\d+) passed', process.stdout)
            failed_matches = re.findall(r'(\d+) failed', process.stdout)
            error_matches = re.findall(r'(\d+) error', process.stdout)
            skipped_matches = re.findall(r'(\d+) skipped', process.stdout)
            
            result.passed = sum(int(m) for m in passed_matches)
            result.failed = sum(int(m) for m in failed_matches)
            result.errors = sum(int(m) for m in error_matches)
            result.skipped = sum(int(m) for m in skipped_matches)
            result.total_tests = result.passed + result.failed + result.errors + result.skipped
            
            result.success = (result.failed == 0 and result.errors == 0)
            
            result.test_results = self._parse_test_details(process.stdout)
            
        except subprocess.TimeoutExpired:
            result.output = "测试执行超时"
            result.errors = result.total_tests if result.total_tests > 0 else 1
        except Exception as e:
            result.output = f"测试执行异常: {str(e)}"
            self.logger.error(f"测试执行失败: {e}")
        
        end_time = datetime.now()
        result.duration = (end_time - start_time).total_seconds()
        
        return result
    
    def _parse_test_details(self, output: str) -> List[Dict[str, Any]]:
        """解析测试详情"""
        results = []
        
        failure_pattern = r'FAILED\s+(.+?)\s+-\s+(.+)'
        for match in re.finditer(failure_pattern, output):
            results.append({
                "name": match.group(1).strip(),
                "status": "failed",
                "message": match.group(2).strip()
            })
        
        pass_pattern = r'PASSED\s+(.+)'
        for match in re.finditer(pass_pattern, output):
            results.append({
                "name": match.group(1).strip(),
                "status": "passed",
                "message": ""
            })
        
        return results


class FailureAnalyzer:
    """失败分析器"""
    
    COMMON_PATTERNS = {
        "AssertionError": "断言失败，预期值与实际值不匹配",
        "ImportError": "模块导入错误，缺少依赖或路径问题",
        "NameError": "名称错误，变量或函数未定义",
        "TypeError": "类型错误，参数类型不正确",
        "ValueError": "值错误，传入的值不符合要求",
        "KeyError": "键错误，字典中找不到指定的键",
        "AttributeError": "属性错误，对象没有该属性",
        "NotImplementedError": "未实现错误（红阶段正常现象）",
        "FileNotFoundError": "文件未找到错误",
        "ConnectionError": "连接错误，网络或服务不可用",
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def analyze(self, test_result: TestResult) -> FailureAnalysis:
        """分析测试失败原因"""
        failures = []
        patterns_found = set()
        
        for tr in test_result.test_results:
            if tr.get("status") == "failed":
                failure_info = FailureInfo(
                    test_name=tr.get("name", "unknown"),
                    error_type=self._extract_error_type(tr.get("message", "")),
                    error_message=tr.get("message", ""),
                    suggested_fix=""
                )
                
                failure_info.suggested_fix = self.COMMON_PATTERNS.get(
                    failure_info.error_type, 
                    "需要检查并修复相关代码"
                )
                
                failures.append(failure_info)
                patterns_found.add(failure_info.error_type)
        
        root_cause = self._summarize_root_cause(failures)
        suggestions = self._generate_fix_suggestions(failures)
        
        severity = self._calculate_severity(failures, test_result)
        
        return FailureAnalysis(
            failures=failures,
            failure_patterns=list(patterns_found),
            root_cause_summary=root_cause,
            severity=severity,
            fix_suggestions=suggestions
        )
    
    def _extract_error_type(self, message: str) -> str:
        for pattern in self.COMMON_PATTERNS.keys():
            if pattern in message:
                return pattern
        return "UnknownError"
    
    def _summarize_root_cause(self, failures: List[FailureInfo]) -> str:
        if not failures:
            return "无失败"
        
        type_counts = {}
        for f in failures:
            type_counts[f.error_type] = type_counts.get(f.error_type, 0) + 1
        
        dominant_type = max(type_counts.items(), key=lambda x: x[1])[0]
        
        if dominant_type == "NotImplementedError":
            return "测试处于红阶段，功能代码尚未实现"
        elif dominant_type == "AssertionError":
            return "断言失败，实现逻辑与预期不符"
        elif dominant_type == "ImportError":
            return "依赖导入问题，需要检查模块和包的可用性"
        
        return f"主要失败类型: {dominant_type} ({type_counts[dominant_type]}个)"
    
    def _generate_fix_suggestions(self, failures: List[FailureInfo]) -> List[str]:
        suggestions = set()
        
        for f in failures:
            if f.error_type == "NotImplementedError":
                suggestions.add("实现被测功能的最小可行代码")
            elif f.error_type == "AssertionError":
                suggestions.add("检查并修正业务逻辑，确保输出符合预期")
            elif f.error_type == "ImportError":
                suggestions.add("安装缺失的依赖或修正导入路径")
            elif f.error_type == "NameError":
                suggestions.add("定义缺失的变量、函数或类")
            elif f.error_type == "TypeError":
                suggestions.add("检查参数类型，确保类型转换正确")
        
        suggestions.add("运行测试以验证修复效果")
        
        return list(suggestions)
    
    def _calculate_severity(self, failures: List[FailureInfo], test_result: TestResult) -> str:
        if not failures:
            return "low"
        
        critical_types = {"ImportError", "ConnectionError", "KeyError"}
        has_critical = any(f.error_type in critical_types for f in failures)
        
        failure_rate = len(failures) / max(test_result.total_tests, 1)
        
        if has_critical or failure_rate > 0.5:
            return "high"
        elif failure_rate > 0.2:
            return "medium"
        return "low"


class ImplementationGuideGenerator:
    """代码实现引导生成器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def generate(self, analysis: FailureAnalysis, test_cases: List[TestCase]) -> ImplementationGuide:
        """生成代码实现引导"""
        guide_id = f"GUIDE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        target_tests = [f.test_name for f in analysis.failures]
        
        implementation_steps = self._build_implementation_steps(analysis, test_cases)
        
        suggested_signatures = self._suggest_function_signatures(test_cases)
        
        priority_order = self._determine_priority_order(analysis, test_cases)
        
        effort = self._estimate_effort(analysis)
        
        dependencies = self._identify_dependencies(test_cases)
        
        return ImplementationGuide(
            guide_id=guide_id,
            target_tests=target_tests,
            implementation_steps=implementation_steps,
            suggested_signatures=suggested_signatures,
            priority_order=priority_order,
            estimated_effort=effort,
            dependencies=dependencies
        )
    
    def _build_implementation_steps(self, analysis: FailureAnalysis, 
                                    test_cases: List[TestCase]) -> List[Dict[str, Any]]:
        steps = []
        
        steps.append({
            "step": 1,
            "action": "分析失败的测试用例",
            "description": f"共{len(analysis.failures)}个测试失败，主要原因是: {analysis.root_cause_summary}",
            "type": "analysis"
        })
        
        steps.append({
            "step": 2,
            "action": "创建/修改目标模块",
            "description": "根据测试用例创建对应的Python模块和类/函数",
            "type": "setup"
        })
        
        for idx, failure in enumerate(analysis.failures[:5]):
            steps.append({
                "step": 3 + idx,
                "action": f"实现: {failure.test_name}",
                "description": f"修复 {failure.error_type}: {failure.error_message[:100]}",
                "type": "implementation"
            })
        
        steps.append({
            "step": len(steps) + 1,
            "action": "运行测试验证",
            "description": "执行全部测试确保通过",
            "type": "verification"
        })
        
        return steps
    
    def _suggest_function_signatures(self, test_cases: List[TestCase]) -> List[Dict[str, str]]:
        signatures = []
        seen_functions = set()
        
        for tc in test_cases:
            func_name = self._extract_function_name(tc.name)
            if func_name and func_name not in seen_functions:
                seen_functions.add(func_name)
                signatures.append({
                    "function": func_name,
                    "signature": f"def {func_name}(*args, **kwargs) -> Any:",
                    "purpose": tc.description[:80]
                })
        
        return signatures
    
    def _determine_priority_order(self, analysis: FailureAnalysis, 
                                   test_cases: List[TestCase]) -> List[str]:
        order = []
        
        critical_failures = [f.test_name for f in analysis.failures 
                           if f.error_type in ["ImportError", "NameError"]]
        order.extend(critical_failures)
        
        high_priority_tests = [tc.name for tc in test_cases 
                              if tc.priority in ["critical", "high"]]
        order.extend([t for t in high_priority_tests if t not in order])
        
        remaining = [f.test_name for f in analysis.failures 
                   if f.test_name not in order]
        order.extend(remaining)
        
        return order
    
    def _estimate_effort(self, analysis: FailureAnalysis) -> str:
        count = len(analysis.failures)
        if count <= 2:
            return "small"
        elif count <= 5:
            return "medium"
        elif count <= 10:
            return "large"
        return "very_large"
    
    def _identify_dependencies(self, test_cases: List[TestCase]) -> List[str]:
        deps = set()
        for tc in test_cases:
            for tag in tc.tags:
                if tag in ["integration", "api", "database"]:
                    deps.add(tag)
        return list(deps)
    
    def _extract_function_name(self, test_name: str) -> str:
        match = re.match(r'test_(\w+)', test_name)
        if match:
            return match.group(1)
        return ""


class RefactoringAnalyzer:
    """重构分析器"""
    
    REFACTORING_TYPES = {
        "extract_method": "提取方法",
        "rename": "重命名",
        "inline": "内联",
        "simplify": "简化",
        "optimize": "优化",
        "remove_duplication": "消除重复"
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def suggest(self, code_path: Path) -> List[RefactoringSuggestion]:
        """分析代码并提供重构建议"""
        if not code_path.exists():
            self.logger.warning(f"文件不存在: {code_path}")
            return []
        
        with open(code_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        suggestions = []
        
        suggestions.extend(self._detect_long_methods(code, code_path))
        suggestions.extend(self._detect_duplicate_code(code, code_path))
        suggestions.extend(self._detect_complexity(code, code_path))
        suggestions.extend(self._detect_style_issues(code, code_path))
        
        return suggestions
    
    def _detect_long_methods(self, code: str, file_path: Path) -> List[RefactoringSuggestion]:
        suggestions = []
        method_pattern = r'def\s+(\w+)\s*\([^)]*\)\s*:'
        
        for match in re.finditer(method_pattern, code):
            start = match.start()
            func_name = match.group(1)
            
            next_def = re.search(r'(?:^|\n)\s*(?:def |class )', code[start + 10:])
            if next_def:
                method_code = code[start:start + 10 + next_def.start()]
            else:
                method_code = code[start:]
            
            lines = method_code.count('\n')
            if lines > 20:
                suggestions.append(RefactoringSuggestion(
                    suggestion_id=f"REF-{uuid.uuid4().hex[:8]}",
                    refactoring_type="extract_method",
                    target_file=str(file_path),
                    target_location=func_name,
                    description=f"方法 '{func_name}' 过长 ({lines}行)，建议拆分为更小的方法",
                    estimated_effort="medium",
                    impact="medium",
                    rationale="长方法降低可读性和可维护性"
                ))
        
        return suggestions
    
    def _detect_duplicate_code(self, code: str, file_path: Path) -> List[RefactoringSuggestion]:
        suggestions = []
        lines = code.split('\n')
        seen_blocks = {}
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if len(stripped) > 20 and not stripped.startswith('#') and not stripped.startswith('\"'):
                if stripped in seen_blocks:
                    prev_line = seen_blocks[stripped]
                    if i - prev_line > 3:
                        suggestions.append(RefactoringSuggestion(
                            suggestion_id=f"REF-{uuid.uuid4().hex[:8]}",
                            refactoring_type="remove_duplication",
                            target_file=str(file_path),
                            target_location=f"line_{i+1}",
                            description=f"发现重复代码块 (第{prev_line+1}行 和 第{i+1}行)",
                            before_code=stripped[:80],
                            estimated_effort="low",
                            impact="medium",
                            rationale="重复代码增加维护成本"
                        ))
                        break
                else:
                    seen_blocks[stripped] = i
        
        return suggestions
    
    def _detect_complexity(self, code: str, file_path: Path) -> List[RefactoringSuggestion]:
        suggestions = []
        complexity_keywords = ['if ', 'elif ', 'for ', 'while ', 'try:', 'except', 'with ', 'and ', 'or ']
        
        method_pattern = r'def\s+(\w+)\s*\([^)]*\)\s*:'
        for match in re.finditer(method_pattern, code):
            start = match.start()
            func_name = match.group(1)
            
            next_def = re.search(r'\n\s*(?:def |class )', code[start + 5:])
            method_code = code[start:start + 5 + (next_def.start() if next_def else len(code) - start)]
            
            complexity = sum(1 for kw in complexity_keywords if kw in method_code) + 1
            
            if complexity > 15:
                suggestions.append(RefactoringSuggestion(
                    suggestion_id=f"REF-{uuid.uuid4().hex[:8]}",
                    refactoring_type="simplify",
                    target_file=str(file_path),
                    target_location=func_name,
                    description=f"方法 '{func_name}' 圈复杂度过高 ({complexity})，建议简化逻辑",
                    estimated_effort="high",
                    impact="high",
                    rationale="高复杂度降低可读性和测试覆盖率"
                ))
        
        return suggestions
    
    def _detect_style_issues(self, code: str, file_path: Path) -> List[RefactoringSuggestion]:
        suggestions = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                suggestions.append(RefactoringSuggestion(
                    suggestion_id=f"REF-{uuid.uuid4().hex[:8]}",
                    refactoring_type="simplify",
                    target_file=str(file_path),
                    target_location=f"line_{i}",
                    description=f"第{i}行过长 ({len(line)}字符)，建议拆分",
                    impact="low",
                    risk_level="info"
                ))
                break
        
        return suggestions


class OptimizationApplier:
    """优化措施应用器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._backup_dir = Path(".fusion_backups")
        self._backup_dir.mkdir(exist_ok=True)
    
    def apply(self, suggestions: List[RefactoringSuggestion]) -> OptimizationResult:
        """应用优化措施"""
        applied = []
        success_count = 0
        failed_count = 0
        rollback_data = {}
        
        for suggestion in suggestions:
            try:
                backup = self._create_backup(suggestion.target_file)
                rollback_data[suggestion.suggestion_id] = backup
                
                modified = self._apply_single(suggestion)
                
                if modified:
                    applied.append(suggestion)
                    success_count += 1
                    self.logger.info(f"已应用重构: {suggestion.description}")
                else:
                    failed_count += 1
                    
            except Exception as e:
                self.logger.error(f"应用重构失败: {e}")
                failed_count += 1
        
        improvement = {
            "applied_count": success_count,
            "total_suggested": len(suggestions),
            "improvement_rate": (success_count / len(suggestions) * 100) if suggestions else 0
        }
        
        return OptimizationResult(
            applied_suggestions=applied,
            successful_count=success_count,
            failed_count=failed_count,
            quality_improvement=improvement,
            rollback_data=rollback_data
        )
    
    def _create_backup(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            return {"original_path": file_path, "backup_path": "", "original_content": ""}
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self._backup_dir / f"{path.stem}_{timestamp}{path.suffix}"
        
        shutil = __import__("shutil")
        shutil.copy2(path, backup_path)
        
        with open(path, "r", encoding="utf-8") as f:
            original_content = f.read()
        
        return {
            "original_path": file_path,
            "backup_path": str(backup_path),
            "original_content": original_content
        }
    
    def _apply_single(self, suggestion: RefactoringSuggestion) -> bool:
        path = Path(suggestion.target_file)
        if not path.exists():
            return False
        
        if suggestion.refactoring_type == "simplify":
            return self._apply_simplify(path, suggestion)
        
        return False
    
    def _apply_simplify(self, path: Path, suggestion: RefactoringSuggestion) -> bool:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        location = suggestion.target_location
        if location.startswith("line_"):
            try:
                line_num = int(location.replace("line_", ""))
                if 0 < line_num <= len(lines):
                    line = lines[line_num - 1].rstrip()
                    if len(line) > 120:
                        lines[line_num - 1] = line[:100] + "\n"
                        
                        with open(path, "w", encoding="utf-8") as f:
                            f.writelines(lines)
                        return True
            except (ValueError, IndexError):
                pass
        
        return False


class RegressionTester:
    """回归测试器"""
    
    def __init__(self, config: Optional[FusionEngineConfig] = None,
                 logger: Optional[logging.Logger] = None):
        self.config = config or FusionEngineConfig()
        self.logger = logger or logging.getLogger(__name__)
        self.test_runner = TestRunner(config, logger)
    
    def run(self, test_paths: List[Path]) -> RegressionResult:
        """执行回归测试"""
        regression_id = f"REG-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        result = self.test_runner.run(test_paths)
        
        new_failures = [tr["name"] for tr in result.test_results 
                       if tr.get("status") == "failed"]
        
        return RegressionResult(
            regression_id=regression_id,
            test_paths=[str(p) for p in test_paths],
            total_tests=result.total_tests,
            passed=result.passed,
            failed=result.failed,
            new_failures=new_failures,
            duration=result.duration,
            stable=(result.failed == 0 and result.errors == 0)
        )


class ArtifactTracer:
    """产物追溯器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._artifacts: Dict[str, List[Path]] = {}
    
    def register(self, category: str, artifact: Path):
        """注册产物"""
        if category not in self._artifacts:
            self._artifacts[category] = []
        if artifact not in self._artifacts[category]:
            self._artifacts[category].append(artifact)
    
    def trace(self, cycle_id: str, spec_version: str = "") -> ArtifactTrace:
        """追溯本次循环的所有产物"""
        trace_matrix = {
            "spec_to_tests": [],
            "tests_to_code": [],
            "code_to_report": []
        }
        
        test_artifacts = self._artifacts.get("test_skeleton", [])
        for ta in test_artifacts:
            trace_matrix["spec_to_tests"].append(str(ta))
        
        code_artifacts = self._artifacts.get("code_implementation", [])
        for ca in code_artifacts:
            trace_matrix["tests_to_code"].append(str(ca))
        
        report_artifacts = self._artifacts.get("reports", [])
        for ra in report_artifacts:
            trace_matrix["code_to_report"].append(str(ra))
        
        total_expected = 3
        actual_categories = sum(1 for v in self._artifacts.values() if v)
        completeness = (actual_categories / total_expected * 100) if total_expected > 0 else 0
        
        return ArtifactTrace(
            trace_id=f"TRACE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            cycle_id=cycle_id,
            artifacts=dict(self._artifacts),
            spec_version=spec_version,
            generated_at=datetime.now().isoformat(),
            completeness_score=completeness,
            trace_matrix=trace_matrix
        )


class SpecDocumentationUpdater:
    """规范文档更新器"""
    
    def update(self, trace: ArtifactTrace, spec_path: Path) -> Path:
        """根据追溯结果更新规范文档"""
        if not spec_path.exists():
            raise FileNotFoundError(f"规范文件不存在: {spec_path}")
        
        with open(spec_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        update_section = f"\n\n---\n\n## 循环执行记录\n\n"
        update_section += f"- **追溯ID**: {trace.trace_id}\n"
        update_section += f"- **循环ID**: {trace.cycle_id}\n"
        update_section += f"- **更新时间**: {trace.generated_at}\n"
        update_section += f"- **完整性得分**: {trace.completeness_score:.1f}%\n\n"
        
        if trace.artifacts:
            update_section += "### 生成产物\n\n"
            for category, paths in trace.artifacts.items():
                update_section += f"- **{category}**:\n"
                for p in paths:
                    update_section += f"  - `{p}`\n"
        
        updated_content = content.rstrip() + update_section
        
        with open(spec_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        
        return spec_path


class ReportGenerator:
    """报告生成器"""
    
    def generate_markdown(self, report: CycleReport) -> str:
        """生成Markdown格式报告"""
        lines = [
            "# SDD-TDD 融合循环报告\n",
            f"**循环ID**: {report.cycle_id}",
            f"**状态**: {'✅ 成功' if report.status == 'success' else '⚠️ 部分失败' if report.status == 'partial_failure' else '❌ 失败'}",
            f"**开始时间**: {report.start_time.isoformat()}",
            f"**结束时间**: {report.end_time.isoformat()}",
            f"**耗时**: {(report.end_time - report.start_time).total_seconds():.2f}s\n",
            "## 执行摘要\n",
            f"{report.summary or '完成SDD-TDD融合循环'}\n",
            "## 阶段执行详情\n"
        ]
        
        phase_icons = {
            FusionPhase.RED.value: "🔴",
            FusionPhase.GREEN.value: "🟢",
            FusionPhase.BLUE.value: "🔵",
            FusionPhase.REGRESSION.value: "🔄"
        }
        
        for phase_name, phase_data in report.phase_results.items():
            icon = phase_icons.get(phase_name, "⚪")
            status_text = phase_data.get("status", "unknown")
            status_icon = "✅" if status_text == "passed" else "❌" if status_text == "failed" else "⏭️"
            
            lines.append(f"### {icon} {phase_name.upper()}阶段 {status_icon}")
            lines.append("")
            lines.append(f"- **状态**: {status_text}")
            lines.append(f"- **耗时**: {phase_data.get('duration', 0):.2f}s")
            
            metrics = phase_data.get("metrics", {})
            if metrics:
                lines.append("- **指标**:")
                for k, v in metrics.items():
                    lines.append(f"  - {k}: {v}")
            
            errors = phase_data.get("errors", [])
            if errors:
                lines.append("- **错误**:")
                for e in errors[:3]:
                    lines.append(f"  - {e}")
            
            lines.append("")
        
        lines.extend([
            "## 质量指标\n"
        ])
        
        for metric_name, value in report.quality_metrics.items():
            lines.append(f"- **{metric_name}**: {value:.2f}" if isinstance(value, (int, float)) else f"- **{metric_name}**: {value}")
        
        if report.artifacts:
            lines.append("\n## 生成产物\n")
            for artifact in report.artifacts:
                lines.append(f"- `{artifact}`")
        
        return "\n".join(lines)
    
    def generate_json(self, report: CycleReport) -> str:
        """生成JSON格式报告"""
        data = {
            "cycle_id": report.cycle_id,
            "start_time": report.start_time.isoformat(),
            "end_time": report.end_time.isoformat(),
            "status": report.status,
            "spec_path": report.spec_path,
            "summary": report.summary,
            "phase_results": {},
            "quality_metrics": report.quality_metrics,
            "artifacts": [str(a) for a in report.artifacts]
        }
        
        for phase_name, phase_data in report.phase_results.items():
            data["phase_results"][phase_name] = {
                k: v for k, v in phase_data.items() 
                if not isinstance(v, Path)
            }
        
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)


class SDDTDDFusionEngine:
    """SDD-TDD深度融合引擎
    
    实现规范驱动开发(SDD)与测试驱动开发(TDD)的完整闭环融合。
    
    循环流程:
    ┌─────────────────────────────────────────┐
    │  🔴 红阶段: SDD规范 → 测试骨架         │
    │  🟢 绿阶段: 测试失败 → 驱动实现         │
    │  🔵 蓝阶段: 测试通过 → 重构优化         │
    │  🔄 回归: 验证 → 产物追溯 → 规范更新   │
    └─────────────────────────────────────────┘
    """
    
    def __init__(self, config: Optional[FusionEngineConfig] = None):
        self.config = config or FusionEngineConfig()
        self._setup_output_dir()
        
        self.logger = self._setup_logger()
        
        self.spec_parser = SDDSpecParser(self.logger)
        self.test_generator = TestSkeletonGenerator(self.logger)
        self.test_runner = TestRunner(self.config, self.logger)
        self.failure_analyzer = FailureAnalyzer(self.logger)
        self.guide_generator = ImplementationGuideGenerator(self.logger)
        self.refactoring_analyzer = RefactoringAnalyzer(self.logger)
        self.optimization_applier = OptimizationApplier(self.logger)
        self.regression_tester = RegressionTester(self.config, self.logger)
        self.artifact_tracer = ArtifactTracer(self.logger)
        self.spec_updater = SpecDocumentationUpdater()
        self.report_generator = ReportGenerator()
        
        self._current_cycle_id: str = ""
        self._current_spec: Optional[SDDSpec] = None
        self._generated_tests: List[TestCase] = []
        self._test_files: List[Path] = []
    
    def _setup_output_dir(self):
        """设置输出目录"""
        if self.config.output_dir:
            self.output_dir = Path(self.config.output_dir)
        else:
            try:
                from skillscripts.utils.enhanced_path_config_manager import (
                    create_path_manager, OutputType
                )
                mgr = create_path_manager()
                self.output_dir = Path(mgr.get_output_path(OutputType.REPORT, subdirectory="sdd_tdd_fusion"))
            except Exception:
                self.output_dir = get_path_config().REPORTS_DIR / "sdd_tdd_fusion"
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if self.config.test_dir:
            self.test_dir = Path(self.config.test_dir)
        else:
            self.test_dir = self.output_dir / "tests"
        self.test_dir.mkdir(parents=True, exist_ok=True)
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("SDDTDDFusionEngine")
        logger.setLevel(logging.DEBUG if self.config.verbose else logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.DEBUG if self.config.verbose else logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - [SDD-TDD] %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def parse_sdd_spec(self, spec_path: Path) -> SDDSpec:
        """解析SDD规范文档
        
        Args:
            spec_path: 规范文件路径
            
        Returns:
            解析后的SDD规范对象
        """
        self.logger.info(f"[红阶段] 解析SDD规范: {spec_path}")
        
        spec = self.spec_parser.parse(spec_path)
        self._current_spec = spec
        
        self.logger.info(
            f"规范解析完成: ID={spec.spec_id}, "
            f"标题={spec.title}, "
            f"需求数={len(spec.requirements)}, "
            f"验收标准数={len(spec.acceptance_criteria)}"
        )
        
        return spec
    
    def generate_test_skeleton(self, spec: SDDSpec) -> List[TestCase]:
        """从规范生成测试骨架
        
        Args:
            spec: SDD规范对象
            
        Returns:
            生成的测试用例列表
        """
        self.logger.info("[红阶段] 生成测试骨架...")
        
        test_cases = self.test_generator.generate(spec)
        self._generated_tests = test_cases
        
        self.logger.info(f"生成了 {len(test_cases)} 个测试用例")
        
        for tc in test_cases[:5]:
            self.logger.debug(f"  - [{tc.priority}] {tc.test_id}: {tc.name}")
        
        if len(test_cases) > 5:
            self.logger.debug(f"  ... 还有 {len(test_cases) - 5} 个测试用例")
        
        return test_cases
    
    def export_test_skeleton(self, tests: List[TestCase], output_dir: Path) -> List[Path]:
        """导出测试骨架文件
        
        Args:
            tests: 测试用例列表
            output_dir: 输出目录
            
        Returns:
            导出的文件路径列表
        """
        self.logger.info(f"[红阶段] 导出测试骨架到: {output_dir}")
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        exported_files = []
        
        module_name = self._current_spec.title.lower().replace(" ", "_").replace("-", "_") if self._current_spec else "unknown"
        class_name = "".join(word.capitalize() for word in (self._current_spec.title.split() if self._current_spec else ["Test"]))
        
        content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动生成的测试骨架 - SDD-TDD融合引擎
规范: {self._current_spec.title if self._current_spec else "Unknown"}
生成时间: {datetime.now().isoformat()}
循环ID: {self._current_cycle_id}

注意: 此文件由SDD-TDD融合引擎自动生成，属于红阶段产物
"""

import pytest
from typing import Any


class Test{class_name}:
    """测试类: {self._current_spec.title if self._current_spec else "Unknown"}"""
    
'''
        
        for tc in tests:
            content += f"\n    {tc.code}\n"
        
        filename = f"test_{module_name}_skeleton.py"
        filepath = output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        exported_files.append(filepath)
        self._test_files.append(filepath)
        self.artifact_tracer.register("test_skeleton", filepath)
        
        self.logger.info(f"测试骨架已导出: {filepath}")
        
        return exported_files
    
    def run_tests(self, test_paths: List[Path]) -> TestResult:
        """执行测试并收集结果
        
        Args:
            test_paths: 测试文件路径列表
            
        Returns:
            测试执行结果
        """
        self.logger.info(f"[绿阶段/回归] 执行测试 ({len(test_paths)} 个文件)...")
        
        result = self.test_runner.run(test_paths)
        
        self.logger.info(
            f"测试完成: 总计={result.total_tests}, "
            f"通过={result.passed}, 失败={result.failed}, "
            f"跳过={result.skipped}, 错误={result.errors}, "
            f"耗时={result.duration:.2f}s"
        )
        
        return result
    
    def analyze_failures(self, result: TestResult) -> FailureAnalysis:
        """分析失败原因
        
        Args:
            result: 测试执行结果
            
        Returns:
            失败分析结果
        """
        self.logger.info("[绿阶段] 分析测试失败原因...")
        
        analysis = self.failure_analyzer.analyze(result)
        
        self.logger.info(
            f"失败分析完成: {len(analysis.failures)}个失败, "
            f"主要原因: {analysis.root_cause_summary}, "
            f"严重程度: {analysis.severity}"
        )
        
        return analysis
    
    def generate_implementation_guide(self, failures: FailureAnalysis) -> ImplementationGuide:
        """生成代码实现引导
        
        Args:
            failures: 失败分析结果
            
        Returns:
            代码实现引导
        """
        self.logger.info("[绿阶段] 生成代码实现引导...")
        
        guide = self.guide_generator.generate(failures, self._generated_tests)
        
        self.logger.info(
            f"实现引导已生成: {guide.guide_id}, "
            f"目标测试数={len(guide.target_tests)}, "
            f"预估工作量={guide.estimated_effort}"
        )
        
        return guide
    
    def suggest_refactoring(self, code_path: Path) -> List[RefactoringSuggestion]:
        """分析代码并提供重构建议
        
        Args:
            code_path: 代码文件路径
            
        Returns:
            重构建议列表
        """
        self.logger.info(f"[蓝阶段] 分析代码质量: {code_path}")
        
        suggestions = self.refactoring_analyzer.suggest(code_path)
        
        self.logger.info(f"发现 {len(suggestions)} 个重构建议")
        
        for s in suggestions[:5]:
            self.logger.debug(f"  - [{s.refactoring_type}] {s.description}")
        
        return suggestions
    
    def apply_optimizations(self, suggestions: List[RefactoringSuggestion]) -> OptimizationResult:
        """应用优化措施
        
        Args:
            suggestions: 重构建议列表
            
        Returns:
            优化实施结果
        """
        self.logger.info(f"[蓝阶段] 应用 {len(suggestions)} 个优化措施...")
        
        result = self.optimization_applier.apply(suggestions)
        
        self.logger.info(
            f"优化完成: 成功={result.successful_count}, "
            f"失败={result.failed_count}"
        )
        
        return result
    
    def run_regression(self, test_paths: List[Path]) -> RegressionResult:
        """执行回归测试
        
        Args:
            test_paths: 测试文件路径列表
            
        Returns:
            回归测试结果
        """
        self.logger.info("[🔄 回归阶段] 执行回归测试...")
        
        result = self.regression_tester.run(test_paths)
        
        status = "✅ 稳定" if result.stable else f"⚠️ 不稳定 ({result.failed}个失败)"
        self.logger.info(f"回归测试完成: {status}")
        
        return result
    
    def trace_artifacts(self) -> ArtifactTrace:
        """追溯本次循环的所有产物
        
        Returns:
            产物追溯结果
        """
        self.logger.info("[🔄 回归阶段] 追溯产物...")
        
        trace = self.artifact_tracer.trace(self._current_cycle_id)
        
        self.logger.info(
            f"产物追溯完成: ID={trace.trace_id}, "
            f"完整性={trace.completeness_score:.1f}%"
        )
        
        return trace
    
    def update_spec_documentation(self, trace: ArtifactTrace, spec_path: Path) -> Path:
        """更新规范文档
        
        Args:
            trace: 产物追溯结果
            spec_path: 规范文件路径
            
        Returns:
            更新后的规范文件路径
        """
        self.logger.info("[🔄 回归阶段] 更新规范文档...")
        
        updated_path = self.spec_updater.update(trace, spec_path)
        
        self.logger.info(f"规范文档已更新: {updated_path}")
        
        return updated_path
    
    def execute_cycle(self, spec_path: Path, output_dir: Path = None) -> CycleReport:
        """执行完整的SDD-TDD循环
        
        Args:
            spec_path: 规范文件路径
            output_dir: 可选的输出目录
            
        Returns:
            循环报告
        """
        if output_dir:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._current_cycle_id = f"CYCLE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hashlib.md5(str(spec_path).encode()).hexdigest()[:8]}"
        
        self.logger.info("=" * 60)
        self.logger.info(f"SDD-TDD 融合循环启动: {self._current_cycle_id}")
        self.logger.info("=" * 60)
        
        start_time = datetime.now()
        phase_results: Dict[str, Any] = {}
        all_artifacts: List[Path] = []
        quality_metrics: Dict[str, float] = {}
        cycle_status = CycleStatus.SUCCESS.value
        
        try:
            red_result = self._execute_red_phase(spec_path)
            phase_results[FusionPhase.RED.value] = red_result
            
            if red_result["status"] != PhaseStatus.PASSED.value:
                cycle_status = CycleStatus.FAILURE.value
                if self.config.fail_fast:
                    return self._build_report(start_time, phase_results, all_artifacts, quality_metrics, cycle_status, spec_path)
            
            green_result = self._execute_green_phase(red_result)
            phase_results[FusionPhase.GREEN.value] = green_result
            
            if green_result["status"] == PhaseStatus.FAILED.value:
                cycle_status = CycleStatus.PARTIAL_FAILURE.value
                if self.config.fail_fast:
                    return self._build_report(start_time, phase_results, all_artifacts, quality_metrics, cycle_status, spec_path)
            
            blue_result = self._execute_blue_phase(green_result)
            phase_results[FusionPhase.BLUE.value] = blue_result
            
            regression_result = self._execute_regression_phase(phase_results)
            phase_results[FusionPhase.REGRESSION.value] = regression_result
            
            if not regression_result.get("stable", True):
                cycle_status = CycleStatus.PARTIAL_FAILURE.value
            
            quality_metrics = self._calculate_quality_metrics(phase_results)
            
            all_artifacts = self._collect_artifacts()
            
        except KeyboardInterrupt:
            self.logger.warning("循环被用户中断")
            cycle_status = "interrupted"
        except Exception as e:
            self.logger.error(f"循环执行异常: {e}")
            cycle_status = CycleStatus.FAILURE.value
            phase_results["error"] = {
                "status": PhaseStatus.FAILED.value,
                "errors": [str(e)]
            }
        
        end_time = datetime.now()
        
        report = self._build_report(start_time, phase_results, all_artifacts, quality_metrics, cycle_status, spec_path)
        
        self._save_reports(report)
        
        self.logger.info("=" * 60)
        self.logger.info(f"SDD-TDD 融合循环完成: {cycle_status}")
        self.logger.info("=" * 60)
        
        return report
    
    def _execute_red_phase(self, spec_path: Path) -> Dict[str, Any]:
        """执行红阶段"""
        self.logger.info("\n>>> 🔴 红阶段: SDD规范 → 测试骨架")
        
        result = PhaseResult(
            phase=FusionPhase.RED,
            status=PhaseStatus.RUNNING,
            start_time=datetime.now().isoformat()
        )
        
        try:
            spec = self.parse_sdd_spec(spec_path)
            test_cases = self.generate_test_skeleton(spec)
            exported = self.export_test_skeleton(test_cases, self.test_dir)
            
            test_result = self.run_tests(exported)
            
            if test_result.failed > 0 or any(
                "assert False" in tc.code or "尚未实现" in tc.code 
                for tc in test_cases
            ):
                result.status = PhaseStatus.PASSED
                result.metrics = {
                    "spec_id": spec.spec_id,
                    "requirements_count": len(spec.requirements),
                    "acceptance_criteria_count": len(spec.acceptance_criteria),
                    "test_cases_generated": len(test_cases),
                    "test_files_exported": len(exported),
                    "red_phase_confirmed": True
                }
                result.output = {
                    "spec": asdict(spec),
                    "test_cases": [asdict(tc) for tc in test_cases],
                    "test_files": [str(f) for f in exported],
                    "test_result": asdict(test_result)
                }
                self.logger.info("🔴 红阶段确认: 测试骨架已生成且处于红灯状态")
            else:
                result.status = PhaseStatus.FAILED
                result.warnings = ["红阶段未确认红灯状态，测试可能已实现"]
                result.errors = ["测试未显示预期的失败状态"]
                
        except Exception as e:
            result.status = PhaseStatus.FAILED
            result.errors = [str(e)]
            self.logger.error(f"红阶段失败: {e}")
        
        result.end_time = datetime.now().isoformat()
        result.duration = (
            datetime.fromisoformat(result.end_time) - 
            datetime.fromisoformat(result.start_time)
        ).total_seconds()
        
        return asdict(result)
    
    def _execute_green_phase(self, red_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行绿阶段"""
        self.logger.info("\n>>> 🟢 绿阶段: 测试失败 → 驱动实现")
        
        result = PhaseResult(
            phase=FusionPhase.GREEN,
            status=PhaseStatus.RUNNING,
            start_time=datetime.now().isoformat()
        )
        
        try:
            test_result_data = red_result.get("output", {}).get("test_result", {})
            test_result = TestResult(**{k: v for k, v in test_result_data.items() 
                                         if hasattr(TestResult, k)})
            
            if test_result.failed == 0 and test_result.total_tests == 0:
                test_result = self.run_tests(self._test_files)
            
            analysis = self.analyze_failures(test_result)
            guide = self.generate_implementation_guide(analysis)
            
            if self.config.auto_generate_implementation:
                self._auto_implement_stubs(guide)
            
            result.status = PhaseStatus.PASSED
            result.metrics = {
                "failures_analyzed": len(analysis.failures),
                "dominant_failure_type": analysis.failure_patterns[0] if analysis.failure_patterns else "none",
                "fix_suggestions_count": len(analysis.fix_suggestions),
                "implementation_guide_id": guide.guide_id
            }
            result.output = {
                "failure_analysis": asdict(analysis),
                "implementation_guide": asdict(guide)
            }
            self.logger.info(f"🟢 绿阶段完成: 已生成实现引导 ({guide.guide_id})")
            
        except Exception as e:
            result.status = PhaseStatus.FAILED
            result.errors = [str(e)]
            self.logger.error(f"绿阶段失败: {e}")
        
        result.end_time = datetime.now().isoformat()
        result.duration = (
            datetime.fromisoformat(result.end_time) - 
            datetime.fromisoformat(result.start_time)
        ).total_seconds()
        
        return asdict(result)
    
    def _execute_blue_phase(self, green_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行蓝阶段"""
        self.logger.info("\n>>> 🔵 蓝阶段: 测试通过 → 重构优化")
        
        result = PhaseResult(
            phase=FusionPhase.BLUE,
            status=PhaseStatus.RUNNING,
            start_time=datetime.now().isoformat()
        )
        
        if not self.config.enable_refactoring:
            result.status = PhaseStatus.SKIPPED
            result.warnings = ["重构阶段已禁用"]
            result.end_time = datetime.now().isoformat()
            return asdict(result)
        
        try:
            code_files = list(Path(".").rglob("*.py"))[:5]
            all_suggestions = []
            
            for cf in code_files:
                if "test_" not in cf.name and "skeleton" not in cf.name:
                    suggestions = self.suggest_refactoring(cf)
                    all_suggestions.extend(suggestions)
            
            optimization_result = OptimizationResult()
            if all_suggestions:
                optimization_result = self.apply_optimizations(all_suggestions[:3])
            
            result.status = PhaseStatus.PASSED
            result.metrics = {
                "refactoring_suggestions": len(all_suggestions),
                "optimizations_applied": optimization_result.successful_count,
                "quality_improvement": optimization_result.quality_improvement.get("improvement_rate", 0)
            }
            result.output = {
                "suggestions": [asdict(s) for s in all_suggestions[:10]],
                "optimization_result": asdict(optimization_result)
            }
            self.logger.info(f"🔵 蓝阶段完成: {len(all_suggestions)} 个建议, {optimization_result.successful_count} 个已应用")
            
        except Exception as e:
            result.status = PhaseStatus.FAILED
            result.errors = [str(e)]
            self.logger.error(f"蓝阶段失败: {e}")
        
        result.end_time = datetime.now().isoformat()
        result.duration = (
            datetime.fromisoformat(result.end_time) - 
            datetime.fromisoformat(result.start_time)
        ).total_seconds()
        
        return asdict(result)
    
    def _execute_regression_phase(self, phase_results: Dict[str, Any]) -> Dict[str, Any]:
        """执行回归阶段"""
        self.logger.info("\n>>> 🔄 回归阶段: 验证 → 产物追溯 → 规范更新")
        
        result = PhaseResult(
            phase=FusionPhase.REGRESSION,
            status=PhaseStatus.RUNNING,
            start_time=datetime.now().isoformat()
        )
        
        if not self.config.enable_regression:
            result.status = PhaseStatus.SKIPPED
            result.warnings = ["回归阶段已禁用"]
            result.end_time = datetime.now().isoformat()
            return asdict(result)
        
        try:
            regression_result = self.run_regression(self._test_files)
            
            trace = self.trace_artifacts()
            
            spec_path = Path(self._current_spec.source_path) if self._current_spec and self._current_spec.source_path else Path("")
            if spec_path.exists():
                updated_path = self.update_spec_documentation(trace, spec_path)
                self.artifact_tracer.register("reports", updated_path)
            
            result.status = PhaseStatus.PASSED
            result.metrics = {
                "regression_stable": regression_result.stable,
                "trace_completeness": trace.completeness_score,
                "artifact_categories": len(trace.artifacts)
            }
            result.output = {
                "regression": asdict(regression_result),
                "trace": asdict(trace)
            }
            result.output["stable"] = regression_result.stable
            self.logger.info(f"🔄 回归阶段完成: {'稳定' if regression_result.stable else '不稳定'}")
            
        except Exception as e:
            result.status = PhaseStatus.FAILED
            result.errors = [str(e)]
            self.logger.error(f"回归阶段失败: {e}")
        
        result.end_time = datetime.now().isoformat()
        result.duration = (
            datetime.fromisoformat(result.end_time) - 
            datetime.fromisoformat(result.start_time)
        ).total_seconds()
        
        return asdict(result)
    
    def _calculate_quality_metrics(self, phase_results: Dict[str, Any]) -> Dict[str, float]:
        """计算质量指标"""
        metrics = {}
        
        red_metrics = phase_results.get(FusionPhase.RED.value, {}).get("metrics", {})
        metrics["test_coverage_ratio"] = min(
            red_metrics.get("test_cases_generated", 0) / max(red_metrics.get("requirements_count", 1), 1) * 100,
            100.0
        )
        
        green_metrics = phase_results.get(FusionPhase.GREEN.value, {}).get("metrics", {})
        metrics["failure_analysis_depth"] = min(
            green_metrics.get("failures_analyzed", 0) / 10 * 100,
            100.0
        )
        
        blue_metrics = phase_results.get(FusionPhase.BLUE.value, {}).get("metrics", {})
        metrics["refactoring_effectiveness"] = blue_metrics.get("quality_improvement", 0)
        
        regression_metrics = phase_results.get(FusionPhase.REGRESSION.value, {}).get("metrics", {})
        metrics["stability_score"] = 100.0 if regression_metrics.get("regression_stable", True) else 50.0
        
        metrics["overall_quality"] = sum(metrics.values()) / len(metrics) if metrics else 0
        
        return metrics
    
    def _collect_artifacts(self) -> List[Path]:
        """收集所有产物"""
        artifacts = []
        for category, paths in self.artifact_tracer._artifacts.items():
            artifacts.extend(paths)
        return artifacts
    
    def _build_report(self, start_time: datetime, phase_results: Dict[str, Any],
                      artifacts: List[Path], quality_metrics: Dict[str, float],
                      status: str, spec_path: Path) -> CycleReport:
        """构建循环报告"""
        end_time = datetime.now()
        
        summary_parts = []
        red = phase_results.get(FusionPhase.RED.value, {})
        green = phase_results.get(FusionPhase.GREEN.value, {})
        blue = phase_results.get(FusionPhase.BLUE.value, {})
        regression = phase_results.get(FusionPhase.REGRESSION.value, {})
        
        if red.get("status") == "passed":
            summary_parts.append(f"红阶段: ✅ 生成 {red.get('metrics', {}).get('test_cases_generated', 0)} 个测试用例")
        if green.get("status") == "passed":
            summary_parts.append(f"绿阶段: ✅ 分析 {green.get('metrics', {}).get('failures_analyzed', 0)} 个失败")
        if blue.get("status") == "passed":
            summary_parts.append(f"蓝阶段: ✅ 提出 {blue.get('metrics', {}).get('refactoring_suggestions', 0)} 条建议")
        if regression.get("output", {}).get("stable", True):
            summary_parts.append("回归阶段: ✅ 验证通过")
        
        return CycleReport(
            cycle_id=self._current_cycle_id,
            start_time=start_time,
            end_time=end_time,
            phase_results=phase_results,
            artifacts=artifacts,
            quality_metrics=quality_metrics,
            status=status,
            spec_path=str(spec_path),
            summary="; ".join(summary_parts) if summary_parts else "循环执行完成"
        )
    
    def _save_reports(self, report: CycleReport):
        """保存报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        md_report = self.report_generator.generate_markdown(report)
        md_path = self.output_dir / f"sdd_tdd_fusion_report_{timestamp}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_report)
        
        json_report = self.report_generator.generate_json(report)
        json_path = self.output_dir / f"sdd_tdd_fusion_report_{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json_report)
        
        self.artifact_tracer.register("reports", md_path)
        self.artifact_tracer.register("reports", json_path)
        
        self.logger.info(f"报告已保存: {md_path}")
    
    def _auto_implement_stubs(self, guide: ImplementationGuide):
        """自动实现桩代码"""
        self.logger.info("自动生成最小实现桩代码...")
        
        for sig in guide.suggested_signatures[:3]:
            func_name = sig.get("function", "")
            if not func_name:
                continue
            
            stub_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自动生成的最小实现 - SDD-TDD融合引擎"""

def {func_name}(*args, **kwargs):
    """{sig.get('purpose', 'Auto-generated function')}"""
    # TODO: 实现具体逻辑
    return None
'''
            stub_path = self.output_dir / f"impl_{func_name}.py"
            with open(stub_path, "w", encoding="utf-8") as f:
                f.write(stub_content)
            
            self.artifact_tracer.register("code_implementation", stub_path)
    
    def execute_continuous_cycles(self, spec_path: Path, max_cycles: int = 3) -> ContinuousCycleReport:
        """执行连续多轮循环（持续深化）
        
        Args:
            spec_path: 规范文件路径
            max_cycles: 最大循环次数
            
        Returns:
            连续循环报告
        """
        self.logger.info(f"启动连续SDD-TDD融合循环 (最大{max_cycles}轮)")
        
        report = ContinuousCycleReport(
            report_id=f"CONTINUOUS-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            started_at=datetime.now().isoformat(),
            overall_status=CycleStatus.SUCCESS.value
        )
        
        quality_trend = []
        
        for cycle_num in range(1, max_cycles + 1):
            self.logger.info(f"\n{'='*40}")
            self.logger.info(f"  第 {cycle_num}/{max_cycles} 轮循环")
            self.logger.info(f"{'='*40}\n")
            
            try:
                cycle_report = self.execute_cycle(spec_path)
                report.cycles.append(cycle_report)
                report.total_cycles += 1
                
                if cycle_report.status == CycleStatus.SUCCESS.value:
                    report.successful_cycles += 1
                elif cycle_report.status == CycleStatus.FAILURE.value:
                    report.overall_status = CycleStatus.PARTIAL_FAILURE.value
                    if self.config.fail_fast:
                        break
                
                trend_entry = {
                    "cycle": cycle_num,
                    "overall_quality": cycle_report.quality_metrics.get("overall_quality", 0),
                    "test_coverage": cycle_report.quality_metrics.get("test_coverage_ratio", 0),
                    "stability": cycle_report.quality_metrics.get("stability_score", 0)
                }
                quality_trend.append(trend_entry)
                
                self.logger.info(f"第{cycle_num}轮完成: 质量={trend_entry['overall_quality']:.1f}%")
                
            except Exception as e:
                self.logger.error(f"第{cycle_num}轮循环异常: {e}")
                report.overall_status = CycleStatus.FAILURE.value
                break
        
        report.quality_trend = quality_trend
        report.completed_at = datetime.now().isoformat()
        
        report.improvement_summary = self._generate_improvement_summary(report)
        
        self.logger.info(f"\n连续循环完成: {report.successful_cycles}/{report.total_cycles} 成功")
        
        return report
    
    def _generate_improvement_summary(self, report: ContinuousCycleReport) -> str:
        """生成改进总结"""
        if not report.cycles:
            return "未完成任何循环"
        
        first_quality = report.cycles[0].quality_metrics.get("overall_quality", 0)
        last_quality = report.cycles[-1].quality_metrics.get("overall_quality", 0)
        delta = last_quality - first_quality
        
        direction = "提升" if delta > 0 else ("下降" if delta < 0 else "持平")
        
        parts = [
            f"完成 {report.total_cycles} 轮循环",
            f"成功率: {report.successful_cycles}/{report.total_cycles}",
            f"质量指标变化: {first_quality:.1f}% → {last_quality:.1f}% ({direction}{abs(delta):.1f}%)"
        ]
        
        return "; ".join(parts)
    
    def integrate_with_provincial_coordinator(self):
        """与省级协调器(provincial_coordinator.py)对接接口
        
        Returns:
            协调器接口适配器
        """
        class ProvincialCoordinatorAdapter:
            def submit_cycle_report(self, report: CycleReport) -> Dict[str, Any]:
                return {"status": "submitted", "cycle_id": report.cycle_id}
            
            def request_coordination(self, task_type: str, payload: Dict) -> Dict[str, Any]:
                return {"status": "coordinated", "task_type": task_type}
        
        return ProvincialCoordinatorAdapter()
    
    def integrate_with_version_iterator(self):
        """与版本迭代器(version_iterator.py)对接接口
        
        Returns:
            版本迭代器接口适配器
        """
        class VersionIteratorAdapter:
            def get_current_version(self) -> str:
                return "v1.0.0"
            
            def increment_version(self, change_type: str = "patch") -> str:
                return f"v1.0.{datetime.now().strftime('%H%M%S')}"
            
            def record_cycle_version(self, cycle_id: str, version: str) -> Dict[str, Any]:
                return {"cycle_id": cycle_id, "version": version, "recorded": True}
        
        return VersionIteratorAdapter()
    
    def integrate_with_evolution_controller(self):
        """与持续演化控制器(continuous_evolution_controller.py)对接接口
        
        Returns:
            演化控制器接口适配器
        """
        class EvolutionControllerAdapter:
            def register_fusion_cycle(self, cycle_report: ContinuousCycleReport) -> Dict[str, Any]:
                return {
                    "registered": True,
                    "cycles_count": cycle_report.total_cycles,
                    "overall_status": cycle_report.overall_status
                }
            
            def get_evolution_state(self) -> Dict[str, Any]:
                return {"state": "active", "mode": "continuous"}
            
            def trigger_next_phase(self, current_phase: str) -> Dict[str, Any]:
                return {"triggered": True, "next_phase": self._next_phase(current_phase)}
            
            @staticmethod
            def _next_phase(current: str) -> str:
                phases = ["red", "green", "blue", "regression"]
                try:
                    idx = phases.index(current)
                    return phases[(idx + 1) % len(phases)]
                except ValueError:
                    return phases[0]
        
        return EvolutionControllerAdapter()


def main():
    """主函数 - 命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="SDD-TDD深度融合引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 执行单轮循环
  python sdd_tdd_fusion_engine.py --spec specs/user_auth.md
  
  # 执行连续3轮循环
  python sdd_tdd_fusion_engine.py --spec specs/user_auth.md --cycles 3
  
  # 指定输出目录
  python sdd_tdd_fusion_engine.py --spec specs/user_auth.md --output-dir reports/custom
        """
    )
    
    parser.add_argument("--spec", required=True, help="SDD规范文件路径")
    parser.add_argument("--output-dir", help="输出目录")
    parser.add_argument("--cycles", type=int, default=1, help="循环次数 (默认: 1)")
    parser.add_argument("--verbose", action="store_true", help="详细日志")
    parser.add_argument("--fail-fast", action="store_true", help="遇到失败立即停止")
    parser.add_argument("--no-refactor", action="store_true", help="禁用重构阶段")
    parser.add_argument("--no-regression", action="store_true", help="禁用回归阶段")
    parser.add_argument("--auto-implement", action="store_true", help="自动生成实现代码")
    
    args = parser.parse_args()
    
    config = FusionEngineConfig(
        verbose=args.verbose,
        fail_fast=args.fail_fast,
        enable_refactoring=not args.no_refactor,
        enable_regression=not args.no_regression,
        auto_generate_implementation=args.auto_implement,
        output_dir=args.output_dir
    )
    
    engine = SDDTDDFusionEngine(config)
    
    try:
        if args.cycles > 1:
            report = engine.execute_continuous_cycles(Path(args.spec), args.cycles)
            
            print("\n" + "=" * 60)
            print("连续循环报告")
            print("=" * 60)
            print(f"总循环数: {report.total_cycles}")
            print(f"成功循环: {report.successful_cycles}")
            print(f"整体状态: {report.overall_status}")
            print(f"改进总结: {report.improvement_summary}")
            
            exit_code = 0 if report.overall_status == CycleStatus.SUCCESS.value else 1
        else:
            report = engine.execute_cycle(Path(args.spec))
            
            print("\n" + "=" * 60)
            print("循环报告")
            print("=" * 60)
            print(f"循环ID: {report.cycle_id}")
            print(f"状态: {report.status}")
            print(f"摘要: {report.summary}")
            print(f"质量评分: {report.quality_metrics.get('overall_quality', 0):.1f}%")
            
            exit_code = 0 if report.status == CycleStatus.SUCCESS.value else 1
        
        sys.exit(exit_code)
        
    except FileNotFoundError as e:
        print(f"错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"执行错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
