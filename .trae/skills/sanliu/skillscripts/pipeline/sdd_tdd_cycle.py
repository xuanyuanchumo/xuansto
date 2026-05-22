#!/usr/bin/env python3
"""
SDD-TDD 融合循环脚本 (增强版)

实现规范驱动开发(SDD)与测试驱动开发(TDD)的完整融合循环：
1. 规范解析 (Spec Parse): 解析SDD规范文件
2. 测试生成 (Test Generate): 从规范自动生成测试用例
3. 红阶段 (Red Phase): 确认测试失败
4. 绿阶段 (Green Phase): 实现代码使测试通过
5. 重构阶段 (Refactor Phase): 优化代码并保持测试通过
6. 合规验证 (Compliance Check): 验证代码符合规范
7. 一致性检查 (Consistency Check): 确保重构后规范一致性

特性：
- 支持配置化的循环参数
- 支持循环状态跟踪
- 支持循环中断和恢复机制
- 生成详细的循环执行报告

用法:
    python sdd_tdd_cycle.py run --spec <规范文件路径> [--config <配置文件>]
    python sdd_tdd_cycle.py resume --state <状态文件路径>
    python sdd_tdd_cycle.py report --state <状态文件路径>
    python sdd_tdd_cycle.py full-cycle --spec <规范文件路径>
"""

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable
import hashlib
import shutil


class SpecType(Enum):
    FUNCTION = "function_spec"
    API = "api_spec"
    BUSINESS_RULE = "business_rule_spec"
    CONSTRAINT = "constraint_spec"


class ComplianceStatus(Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    PARTIAL = "PARTIAL"


class ConsistencyStatus(Enum):
    CONSISTENT = "CONSISTENT"
    INCONSISTENT = "INCONSISTENT"
    WARNING = "WARNING"


class CyclePhase(Enum):
    INIT = "init"
    SPEC_PARSE = "spec_parse"
    TEST_GENERATE = "test_generate"
    RED = "red"
    GREEN = "green"
    REFACTOR = "refactor"
    COMPLIANCE = "compliance"
    CONSISTENCY = "consistency"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class PhaseStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class CycleConfig:
    max_iterations: int = 10
    auto_fix_enabled: bool = True
    coverage_threshold: float = 80.0
    test_timeout: int = 300
    fail_fast: bool = False
    output_dir: str = None
    state_file: str = "cycle_state.json"
    spec_dir: str = "specs"
    test_dir: str = "tests/generated"
    code_dir: str = "app"
    enable_refactor: bool = True
    enable_compliance: bool = True
    enable_consistency: bool = True
    generate_report: bool = True
    verbose: bool = False
    
    def __post_init__(self):
        if self.output_dir is None:
            try:
                from skillscripts.utils.enhanced_path_config_manager import create_path_manager, OutputType
                _path_mgr = create_path_manager()
                self.output_dir = str(_path_mgr.get_output_path(OutputType.REPORT, subdirectory="sdd_tdd"))
            except Exception:
                self.output_dir = "reports/sdd_tdd"


@dataclass
class SpecElement:
    name: str
    element_type: str
    description: str = ""
    constraints: Dict[str, Any] = field(default_factory=dict)
    test_coverage: bool = False


@dataclass
class TestCase:
    id: str
    name: str
    spec_id: str
    spec_element: str
    test_type: str
    status: str = "pending"
    arrange: str = ""
    act: str = ""
    assert_: str = ""


@dataclass
class Violation:
    violation_id: str
    type: str
    severity: str
    element: str
    message: str
    suggestion: str = ""


@dataclass
class Inconsistency:
    inconsistency_id: str
    type: str
    severity: str
    spec_element: str
    description: str
    expected: str = ""
    actual: str = ""


@dataclass
class PhaseResult:
    phase: CyclePhase
    status: PhaseStatus
    start_time: str = ""
    end_time: str = ""
    duration: float = 0.0
    output: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceReport:
    report_id: str
    spec_id: str
    spec_version: str
    status: ComplianceStatus
    compliance_rate: Dict[str, float]
    violations: List[Violation] = field(default_factory=list)
    coverage_details: Dict[str, float] = field(default_factory=dict)
    trace_completeness: Dict[str, float] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ConsistencyReport:
    report_id: str
    spec_id: str
    spec_version: str
    code_version: str
    status: ConsistencyStatus
    inconsistencies: List[Inconsistency] = field(default_factory=list)
    impact_analysis: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TraceMatrix:
    spec_to_test: Dict[str, List[str]] = field(default_factory=dict)
    test_to_spec: Dict[str, str] = field(default_factory=dict)
    spec_to_code: Dict[str, List[str]] = field(default_factory=dict)
    code_to_spec: Dict[str, str] = field(default_factory=dict)


@dataclass
class CycleState:
    cycle_id: str
    spec_path: str
    current_phase: CyclePhase
    iteration: int
    phase_results: Dict[str, PhaseResult] = field(default_factory=dict)
    spec_data: Dict[str, Any] = field(default_factory=dict)
    test_cases: List[Dict[str, Any]] = field(default_factory=list)
    test_file: str = ""
    code_file: str = ""
    compliance_report: Optional[Dict[str, Any]] = None
    consistency_report: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed: bool = False
    success: bool = False
    error_message: str = ""


class SpecParser:
    """规范解析器"""
    
    def __init__(self):
        self.supported_formats = [".yaml", ".yml", ".json", ".md"]
    
    def parse(self, spec_path: str) -> Dict[str, Any]:
        """解析规范文件"""
        path = Path(spec_path)
        if not path.exists():
            raise FileNotFoundError(f"规范文件不存在: {spec_path}")
        
        suffix = path.suffix.lower()
        if suffix in [".yaml", ".yml"]:
            return self._parse_yaml(path)
        elif suffix == ".json":
            return self._parse_json(path)
        elif suffix == ".md":
            return self._parse_markdown(path)
        else:
            raise ValueError(f"不支持的规范格式: {suffix}")
    
    def _parse_yaml(self, path: Path) -> Dict[str, Any]:
        try:
            import yaml
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except ImportError:
            raise RuntimeError("需要安装 PyYAML: pip install pyyaml")
    
    def _parse_json(self, path: Path) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _parse_markdown(self, path: Path) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        spec = {
            "id": self._extract_id(content),
            "name": self._extract_name(content),
            "version": self._extract_version(content),
            "type": self._detect_spec_type(content),
            "elements": self._extract_elements(content),
            "source_file": str(path)
        }
        return spec
    
    def _extract_id(self, content: str) -> str:
        match = re.search(r"规范ID[：:]\s*(\S+)", content)
        return match.group(1) if match else f"SPC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def _extract_name(self, content: str) -> str:
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        return match.group(1) if match else "未命名规范"
    
    def _extract_version(self, content: str) -> str:
        match = re.search(r"版本[：:]\s*(\S+)", content)
        return match.group(1) if match else "v1.0"
    
    def _detect_spec_type(self, content: str) -> str:
        if "接口路径" in content or "API" in content:
            return SpecType.API.value
        elif "业务规则" in content or "规则编号" in content:
            return SpecType.BUSINESS_RULE.value
        elif "约束" in content:
            return SpecType.CONSTRAINT.value
        else:
            return SpecType.FUNCTION.value
    
    def _extract_elements(self, content: str) -> List[Dict[str, Any]]:
        elements = []
        
        input_pattern = r"##\s*输入条件\s*\n((?:\s*[-*]\s*.+\n?)+)"
        for match in re.finditer(input_pattern, content):
            inputs = [line.strip("- *").strip() for line in match.group(1).strip().split("\n") if line.strip()]
            for inp in inputs:
                name_part = inp.split(":")[0].strip() if ":" in inp else inp
                desc_part = inp.split(":")[1].strip() if ":" in inp else ""
                elements.append({
                    "name": name_part,
                    "type": "input",
                    "description": desc_part
                })
        
        output_pattern = r"##\s*输出结果\s*\n((?:\s*[-*]\s*.+\n?)+)"
        for match in re.finditer(output_pattern, content):
            outputs = [line.strip("- *").strip() for line in match.group(1).strip().split("\n") if line.strip()]
            for out in outputs:
                name_part = out.split(":")[0].strip() if ":" in out else out
                desc_part = out.split(":")[1].strip() if ":" in out else ""
                elements.append({
                    "name": name_part,
                    "type": "output",
                    "description": desc_part
                })
        
        exception_pattern = r"##\s*异常处理\s*\n((?:\s*[-*]\s*.+\n?)+)"
        for match in re.finditer(exception_pattern, content):
            exceptions = [line.strip("- *").strip() for line in match.group(1).strip().split("\n") if line.strip()]
            for exc in exceptions:
                name_part = exc.split(":")[0].strip() if ":" in exc else exc
                desc_part = exc.split(":")[1].strip() if ":" in exc else ""
                elements.append({
                    "name": name_part,
                    "type": "exception",
                    "description": desc_part
                })
        
        return elements


class TestCaseGenerator:
    """测试用例生成器"""
    
    MAPPING_RULES = {
        SpecType.FUNCTION: {
            "min_test_cases": 3,
            "must_cover": ["happy_path", "error_path", "boundary"],
            "naming": "test_{feature}_{scenario}_{expected_result}"
        },
        SpecType.API: {
            "min_test_cases": 5,
            "must_cover": ["valid_request", "invalid_request", "unauthorized", "forbidden", "error_response"],
            "naming": "test_{api}_{method}_{scenario}"
        },
        SpecType.BUSINESS_RULE: {
            "min_test_cases": 2,
            "must_cover": ["rule_triggered", "rule_not_triggered"],
            "naming": "test_{rule}_when_{condition}_then_{action}"
        }
    }
    
    def __init__(self, output_dir: str = "tests/generated"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.trace_matrix = TraceMatrix()
    
    def generate_from_spec(self, spec: Dict[str, Any]) -> List[TestCase]:
        """从规范生成测试用例"""
        spec_type = SpecType(spec.get("type", "function_spec"))
        rules = self.MAPPING_RULES.get(spec_type, self.MAPPING_RULES[SpecType.FUNCTION])
        
        test_cases = []
        spec_id = spec.get("id", "UNKNOWN")
        spec_name = spec.get("name", "unknown")
        
        elements = spec.get("elements", [])
        
        for element in elements:
            element_type = element.get("type", "")
            element_name = element.get("name", "")
            
            if element_type == "input":
                test_cases.extend(self._generate_input_tests(spec_id, spec_name, element, rules))
            elif element_type == "output":
                test_cases.extend(self._generate_output_tests(spec_id, spec_name, element, rules))
            elif element_type == "exception":
                test_cases.extend(self._generate_exception_tests(spec_id, spec_name, element, rules))
        
        for tc in test_cases:
            self.trace_matrix.spec_to_test.setdefault(spec_id, []).append(tc.id)
            self.trace_matrix.test_to_spec[tc.id] = spec_id
        
        return test_cases
    
    def _generate_input_tests(self, spec_id: str, spec_name: str, element: Dict, rules: Dict) -> List[TestCase]:
        tests = []
        naming = rules["naming"]
        
        valid_test = TestCase(
            id=f"TC-{spec_id}-INPUT-{len(tests)+1:03d}",
            name=naming.format(feature=spec_name, scenario="valid_input", expected_result="success"),
            spec_id=spec_id,
            spec_element=element["name"],
            test_type="unit_test",
            arrange=f"# 准备有效的{element['name']}",
            act=f"# 使用{element['name']}执行操作",
            assert_=f"# 验证操作成功"
        )
        tests.append(valid_test)
        
        boundary_test = TestCase(
            id=f"TC-{spec_id}-INPUT-{len(tests)+1:03d}",
            name=naming.format(feature=spec_name, scenario="boundary_input", expected_result="handled"),
            spec_id=spec_id,
            spec_element=element["name"],
            test_type="unit_test",
            arrange=f"# 准备边界值{element['name']}",
            act=f"# 使用边界值执行操作",
            assert_=f"# 验证边界处理正确"
        )
        tests.append(boundary_test)
        
        return tests
    
    def _generate_output_tests(self, spec_id: str, spec_name: str, element: Dict, rules: Dict) -> List[TestCase]:
        tests = []
        naming = rules["naming"]
        
        output_test = TestCase(
            id=f"TC-{spec_id}-OUTPUT-{len(tests)+1:03d}",
            name=naming.format(feature=spec_name, scenario="output_validation", expected_result="matches_spec"),
            spec_id=spec_id,
            spec_element=element["name"],
            test_type="unit_test",
            arrange=f"# 准备输入数据",
            act=f"# 执行操作获取{element['name']}",
            assert_=f"# 验证{element['name']}符合规范"
        )
        tests.append(output_test)
        
        return tests
    
    def _generate_exception_tests(self, spec_id: str, spec_name: str, element: Dict, rules: Dict) -> List[TestCase]:
        tests = []
        naming = rules["naming"]
        
        exception_test = TestCase(
            id=f"TC-{spec_id}-EXC-{len(tests)+1:03d}",
            name=naming.format(feature=spec_name, scenario="exception", expected_result="raised"),
            spec_id=spec_id,
            spec_element=element["name"],
            test_type="unit_test",
            arrange=f"# 准备触发异常的条件",
            act=f"# 执行操作",
            assert_=f"# 验证抛出{element['name']}异常"
        )
        tests.append(exception_test)
        
        return tests
    
    def generate_test_file(self, test_cases: List[TestCase], spec_name: str) -> str:
        """生成测试文件内容"""
        module_name = spec_name.lower().replace(" ", "_").replace("-", "_")
        class_name = "".join(word.capitalize() for word in spec_name.split())
        
        content = f'''#!/usr/bin/env python3
"""
自动生成的测试文件
规范: {spec_name}
生成时间: {datetime.now().isoformat()}

注意: 此文件由SDD-TDD融合工具自动生成
"""

import pytest


class Test{class_name}:
    """测试类: {spec_name}"""
    
'''
        
        for tc in test_cases:
            content += f'''    def {tc.name}(self):
        """测试: {tc.name}"""
        # Arrange
        {tc.arrange}
        
        # Act
        {tc.act}
        
        # Assert
        {tc.assert_}
        assert False, "测试尚未实现"

'''
        
        return content
    
    def save_test_file(self, content: str, spec_name: str) -> Path:
        """保存测试文件"""
        filename = f"test_{spec_name.lower().replace(' ', '_')}.py"
        filepath = self.output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath


class ComplianceChecker:
    """规范合规性检查器"""
    
    def __init__(self):
        self.violation_counter = 0
    
    def check_compliance(
        self,
        spec: Dict[str, Any],
        test_results: Dict[str, Any]
    ) -> ComplianceReport:
        """检查规范合规性"""
        spec_id = spec.get("id", "UNKNOWN")
        spec_version = spec.get("version", "v1.0")
        
        violations = []
        elements = spec.get("elements", [])
        
        for element in elements:
            element_name = element.get("name", "")
            element_type = element.get("type", "")
            
            covered = self._check_element_coverage(element_name, test_results)
            
            if not covered:
                self.violation_counter += 1
                violations.append(Violation(
                    violation_id=f"VIO-{self.violation_counter:03d}",
                    type=f"{element_type.upper()}_NOT_TESTED",
                    severity="HIGH" if element_type in ["exception", "input"] else "MEDIUM",
                    element=element_name,
                    message=f"{element_type} '{element_name}' 缺少测试覆盖",
                    suggestion=f"添加测试用例 test_{spec_id}_{element_name}"
                ))
        
        total_elements = len(elements)
        covered_elements = total_elements - len([v for v in violations if "NOT_TESTED" in v.type])
        
        compliance_rate = {
            "总体": (covered_elements / total_elements * 100) if total_elements > 0 else 100,
            "功能合规": self._calculate_type_compliance(elements, test_results, "input"),
            "接口合规": self._calculate_type_compliance(elements, test_results, "output"),
            "业务规则合规": self._calculate_type_compliance(elements, test_results, "exception")
        }
        
        status = ComplianceStatus.COMPLIANT
        if compliance_rate["总体"] < 100:
            status = ComplianceStatus.NON_COMPLIANT if compliance_rate["总体"] < 80 else ComplianceStatus.PARTIAL
        
        return ComplianceReport(
            report_id=f"CR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            spec_id=spec_id,
            spec_version=spec_version,
            status=status,
            compliance_rate=compliance_rate,
            violations=violations,
            coverage_details=self._extract_coverage_details(test_results),
            trace_completeness={
                "规范→测试": self._calculate_trace_completeness(spec, test_results, "spec_to_test"),
                "测试→规范": self._calculate_trace_completeness(spec, test_results, "test_to_spec")
            }
        )
    
    def _check_element_coverage(self, element_name: str, test_results: Dict) -> bool:
        """检查元素是否被测试覆盖"""
        test_cases = test_results.get("test_cases", [])
        for tc in test_cases:
            if element_name.lower() in tc.get("name", "").lower():
                return True
            if tc.get("spec_element", "").lower() == element_name.lower():
                return True
        return False
    
    def _calculate_type_compliance(
        self,
        elements: List[Dict],
        test_results: Dict,
        element_type: str
    ) -> float:
        """计算特定类型的合规率"""
        type_elements = [e for e in elements if e.get("type") == element_type]
        if not type_elements:
            return 100.0
        
        covered = sum(1 for e in type_elements if self._check_element_coverage(e["name"], test_results))
        return (covered / len(type_elements)) * 100
    
    def _extract_coverage_details(self, test_results: Dict) -> Dict[str, float]:
        """提取覆盖率详情"""
        return {
            "语句覆盖": test_results.get("statement_coverage", 0),
            "分支覆盖": test_results.get("branch_coverage", 0),
            "异常覆盖": test_results.get("exception_coverage", 0)
        }
    
    def _calculate_trace_completeness(
        self,
        spec: Dict,
        test_results: Dict,
        direction: str
    ) -> float:
        """计算追溯完整性"""
        if direction == "spec_to_test":
            elements = spec.get("elements", [])
            test_cases = test_results.get("test_cases", [])
            traced = sum(1 for e in elements if any(
                e["name"].lower() in tc.get("name", "").lower()
                for tc in test_cases
            ))
            return (traced / len(elements) * 100) if elements else 100
        else:
            test_cases = test_results.get("test_cases", [])
            traced = sum(1 for tc in test_cases if tc.get("spec_element"))
            return (traced / len(test_cases) * 100) if test_cases else 100


class ConsistencyChecker:
    """规范一致性检查器"""
    
    def __init__(self):
        self.inconsistency_counter = 0
    
    def check_consistency(
        self,
        spec: Dict[str, Any],
        code_snapshot: Dict[str, Any]
    ) -> ConsistencyReport:
        """检查规范与代码的一致性"""
        spec_id = spec.get("id", "UNKNOWN")
        spec_version = spec.get("version", "v1.0")
        code_version = code_snapshot.get("version", "unknown")
        
        inconsistencies = []
        elements = spec.get("elements", [])
        
        for element in elements:
            element_name = element.get("name", "")
            element_type = element.get("type", "")
            constraints = element.get("constraints", {})
            
            code_element = self._find_code_element(element_name, code_snapshot)
            
            if not code_element:
                self.inconsistency_counter += 1
                inconsistencies.append(Inconsistency(
                    inconsistency_id=f"INC-{self.inconsistency_counter:03d}",
                    type="ELEMENT_NOT_IMPLEMENTED",
                    severity="HIGH",
                    spec_element=element_name,
                    description=f"规范元素 '{element_name}' 在代码中未找到实现"
                ))
            else:
                type_mismatch = self._check_type_consistency(element, code_element)
                if type_mismatch:
                    self.inconsistency_counter += 1
                    inconsistencies.append(Inconsistency(
                        inconsistency_id=f"INC-{self.inconsistency_counter:03d}",
                        type="TYPE_MISMATCH",
                        severity="HIGH",
                        spec_element=element_name,
                        description=type_mismatch,
                        expected=element.get("description", ""),
                        actual=code_element.get("type", "")
                    ))
                
                constraint_violations = self._check_constraint_consistency(element, code_element)
                for violation in constraint_violations:
                    self.inconsistency_counter += 1
                    inconsistencies.append(Inconsistency(
                        inconsistency_id=f"INC-{self.inconsistency_counter:03d}",
                        type="CONSTRAINT_MISMATCH",
                        severity="MEDIUM",
                        spec_element=element_name,
                        description=violation
                    ))
        
        status = ConsistencyStatus.CONSISTENT
        if inconsistencies:
            high_severity = any(i.severity == "HIGH" for i in inconsistencies)
            status = ConsistencyStatus.INCONSISTENT if high_severity else ConsistencyStatus.WARNING
        
        return ConsistencyReport(
            report_id=f"CONS-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            spec_id=spec_id,
            spec_version=spec_version,
            code_version=code_version,
            status=status,
            inconsistencies=inconsistencies,
            impact_analysis=self._analyze_impact(inconsistencies, spec, code_snapshot),
            suggestions=self._generate_suggestions(inconsistencies)
        )
    
    def _find_code_element(self, element_name: str, code_snapshot: Dict) -> Optional[Dict]:
        """在代码快照中查找元素"""
        functions = code_snapshot.get("functions", [])
        for func in functions:
            if element_name.lower() in func.get("name", "").lower():
                return func
        
        variables = code_snapshot.get("variables", [])
        for var in variables:
            if element_name.lower() in var.get("name", "").lower():
                return var
        
        return None
    
    def _check_type_consistency(self, spec_element: Dict, code_element: Dict) -> Optional[str]:
        """检查类型一致性"""
        spec_type = spec_element.get("constraints", {}).get("type", "")
        code_type = code_element.get("type", "")
        
        if spec_type and code_type and spec_type.lower() != code_type.lower():
            return f"类型不匹配: 规范要求 '{spec_type}', 代码实现 '{code_type}'"
        
        return None
    
    def _check_constraint_consistency(self, spec_element: Dict, code_element: Dict) -> List[str]:
        """检查约束一致性"""
        violations = []
        constraints = spec_element.get("constraints", {})
        
        if "min_length" in constraints:
            code_min = code_element.get("min_length")
            if code_min and code_min != constraints["min_length"]:
                violations.append(
                    f"最小长度不一致: 规范要求 {constraints['min_length']}, 代码实现 {code_min}"
                )
        
        if "max_length" in constraints:
            code_max = code_element.get("max_length")
            if code_max and code_max != constraints["max_length"]:
                violations.append(
                    f"最大长度不一致: 规范要求 {constraints['max_length']}, 代码实现 {code_max}"
                )
        
        return violations
    
    def _analyze_impact(
        self,
        inconsistencies: List[Inconsistency],
        spec: Dict,
        code_snapshot: Dict
    ) -> Dict[str, Any]:
        """分析不一致的影响"""
        return {
            "受影响规范": len(set(i.spec_element for i in inconsistencies)),
            "受影响测试": len(inconsistencies) * 2,
            "受影响代码文件": min(len(inconsistencies), len(code_snapshot.get("files", [])))
        }
    
    def _generate_suggestions(self, inconsistencies: List[Inconsistency]) -> List[str]:
        """生成处理建议"""
        suggestions = []
        
        element_missing = [i for i in inconsistencies if i.type == "ELEMENT_NOT_IMPLEMENTED"]
        if element_missing:
            suggestions.append(f"实现缺失的规范元素: {', '.join(i.spec_element for i in element_missing)}")
        
        type_mismatch = [i for i in inconsistencies if i.type == "TYPE_MISMATCH"]
        if type_mismatch:
            suggestions.append("同步代码类型定义与规范要求")
        
        return suggestions


class CycleStateManager:
    """循环状态管理器 - 支持中断和恢复"""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def save_state(self, state: CycleState) -> Path:
        """保存循环状态"""
        state.updated_at = datetime.now().isoformat()
        state_file = self.output_dir / f"cycle_{state.cycle_id}.json"
        
        state_dict = {
            "cycle_id": state.cycle_id,
            "spec_path": state.spec_path,
            "current_phase": state.current_phase.value,
            "iteration": state.iteration,
            "phase_results": {k: asdict(v) for k, v in state.phase_results.items()},
            "spec_data": state.spec_data,
            "test_cases": state.test_cases,
            "test_file": state.test_file,
            "code_file": state.code_file,
            "compliance_report": state.compliance_report,
            "consistency_report": state.consistency_report,
            "created_at": state.created_at,
            "updated_at": state.updated_at,
            "completed": state.completed,
            "success": state.success,
            "error_message": state.error_message
        }
        
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, ensure_ascii=False, indent=2, default=str)
        
        return state_file
    
    def load_state(self, state_path: str) -> CycleState:
        """加载循环状态"""
        path = Path(state_path)
        if not path.exists():
            raise FileNotFoundError(f"状态文件不存在: {state_path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        phase_results = {}
        for k, v in data.get("phase_results", {}).items():
            phase_results[k] = PhaseResult(
                phase=CyclePhase(v["phase"]),
                status=PhaseStatus(v["status"]),
                start_time=v.get("start_time", ""),
                end_time=v.get("end_time", ""),
                duration=v.get("duration", 0.0),
                output=v.get("output", {}),
                errors=v.get("errors", []),
                warnings=v.get("warnings", []),
                metrics=v.get("metrics", {})
            )
        
        return CycleState(
            cycle_id=data["cycle_id"],
            spec_path=data["spec_path"],
            current_phase=CyclePhase(data["current_phase"]),
            iteration=data["iteration"],
            phase_results=phase_results,
            spec_data=data.get("spec_data", {}),
            test_cases=data.get("test_cases", []),
            test_file=data.get("test_file", ""),
            code_file=data.get("code_file", ""),
            compliance_report=data.get("compliance_report"),
            consistency_report=data.get("consistency_report"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            completed=data.get("completed", False),
            success=data.get("success", False),
            error_message=data.get("error_message", "")
        )


class CycleReportGenerator:
    """循环执行报告生成器"""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(self, state: CycleState) -> Dict[str, Any]:
        """生成循环执行报告"""
        report = {
            "report_id": f"RPT-{state.cycle_id}",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "cycle_id": state.cycle_id,
                "spec_path": state.spec_path,
                "spec_name": state.spec_data.get("name", "Unknown"),
                "spec_id": state.spec_data.get("id", "Unknown"),
                "total_iterations": state.iteration,
                "completed": state.completed,
                "success": state.success,
                "error_message": state.error_message
            },
            "phases": {},
            "metrics": {},
            "recommendations": []
        }
        
        for phase_name, phase_result in state.phase_results.items():
            report["phases"][phase_name] = {
                "phase": phase_result.phase.value,
                "status": phase_result.status.value,
                "duration": phase_result.duration,
                "start_time": phase_result.start_time,
                "end_time": phase_result.end_time,
                "errors": phase_result.errors,
                "warnings": phase_result.warnings,
                "metrics": phase_result.metrics
            }
        
        report["metrics"] = self._calculate_metrics(state)
        report["recommendations"] = self._generate_recommendations(state)
        
        return report
    
    def _calculate_metrics(self, state: CycleState) -> Dict[str, Any]:
        """计算循环指标"""
        total_duration = sum(
            pr.duration for pr in state.phase_results.values()
        )
        
        total_errors = sum(
            len(pr.errors) for pr in state.phase_results.values()
        )
        
        total_warnings = sum(
            len(pr.warnings) for pr in state.phase_results.values()
        )
        
        return {
            "total_duration": total_duration,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "test_cases_generated": len(state.test_cases),
            "phases_completed": sum(
                1 for pr in state.phase_results.values()
                if pr.status == PhaseStatus.PASSED
            ),
            "phases_failed": sum(
                1 for pr in state.phase_results.values()
                if pr.status == PhaseStatus.FAILED
            )
        }
    
    def _generate_recommendations(self, state: CycleState) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if state.iteration > 3:
            recommendations.append(
                "循环迭代次数较多，建议检查规范是否足够清晰或测试用例是否合理"
            )
        
        failed_phases = [
            name for name, pr in state.phase_results.items()
            if pr.status == PhaseStatus.FAILED
        ]
        if failed_phases:
            recommendations.append(
                f"以下阶段失败需要关注: {', '.join(failed_phases)}"
            )
        
        if state.compliance_report:
            compliance_rate = state.compliance_report.get("compliance_rate", {}).get("总体", 0)
            if compliance_rate < 100:
                recommendations.append(
                    f"合规率为 {compliance_rate:.1f}%，建议补充缺失的测试用例"
                )
        
        if state.consistency_report:
            inconsistencies = state.consistency_report.get("inconsistencies", [])
            if inconsistencies:
                recommendations.append(
                    f"发现 {len(inconsistencies)} 个一致性问题，建议同步规范与代码"
                )
        
        if not recommendations:
            recommendations.append("循环执行顺利，建议继续保持当前的开发流程")
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any], filename: str = None) -> Path:
        """保存报告"""
        if not filename:
            filename = f"cycle_report_{report['report_id']}.json"
        
        report_file = self.output_dir / filename
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        md_report = self._generate_markdown_report(report)
        md_file = report_file.with_suffix(".md")
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_report)
        
        return report_file
    
    def _generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """生成Markdown格式报告"""
        lines = [
            "# SDD-TDD 融合循环执行报告",
            "",
            f"**报告ID**: {report['report_id']}",
            f"**生成时间**: {report['generated_at']}",
            "",
            "## 执行摘要",
            "",
            f"- **循环ID**: {report['summary']['cycle_id']}",
            f"- **规范文件**: {report['summary']['spec_path']}",
            f"- **规范名称**: {report['summary']['spec_name']}",
            f"- **迭代次数**: {report['summary']['total_iterations']}",
            f"- **执行状态**: {'✅ 成功' if report['summary']['success'] else '❌ 失败' if report['summary']['completed'] else '⏸️ 暂停'}",
            "",
            "## 阶段执行详情",
            ""
        ]
        
        for phase_name, phase_data in report["phases"].items():
            status_icon = "✅" if phase_data["status"] == "passed" else "❌" if phase_data["status"] == "failed" else "⏭️"
            lines.append(f"### {phase_name} {status_icon}")
            lines.append("")
            lines.append(f"- **状态**: {phase_data['status']}")
            lines.append(f"- **耗时**: {phase_data['duration']:.2f}s")
            
            if phase_data.get("errors"):
                lines.append("- **错误**:")
                for error in phase_data["errors"]:
                    lines.append(f"  - {error}")
            
            if phase_data.get("warnings"):
                lines.append("- **警告**:")
                for warning in phase_data["warnings"]:
                    lines.append(f"  - {warning}")
            
            lines.append("")
        
        lines.extend([
            "## 执行指标",
            "",
            f"- **总耗时**: {report['metrics']['total_duration']:.2f}s",
            f"- **错误数**: {report['metrics']['total_errors']}",
            f"- **警告数**: {report['metrics']['total_warnings']}",
            f"- **生成测试用例数**: {report['metrics']['test_cases_generated']}",
            f"- **完成阶段数**: {report['metrics']['phases_completed']}",
            f"- **失败阶段数**: {report['metrics']['phases_failed']}",
            "",
            "## 改进建议",
            ""
        ])
        
        for rec in report["recommendations"]:
            lines.append(f"- {rec}")
        
        return "\n".join(lines)


class SddTddCycle:
    """SDD-TDD融合循环主控制器"""
    
    def __init__(self, config: CycleConfig):
        self.config = config
        self.spec_parser = SpecParser()
        self.test_generator = TestCaseGenerator(output_dir=config.test_dir)
        self.compliance_checker = ComplianceChecker()
        self.consistency_checker = ConsistencyChecker()
        self.state_manager = CycleStateManager(config.output_dir)
        self.report_generator = CycleReportGenerator(config.output_dir)
        self.state: Optional[CycleState] = None
    
    def _generate_cycle_id(self, spec_path: str) -> str:
        """生成循环ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        spec_hash = hashlib.md5(spec_path.encode()).hexdigest()[:8]
        return f"CYC-{timestamp}-{spec_hash}"
    
    def _create_phase_result(self, phase: CyclePhase) -> PhaseResult:
        """创建阶段结果"""
        return PhaseResult(
            phase=phase,
            status=PhaseStatus.RUNNING,
            start_time=datetime.now().isoformat()
        )
    
    def _complete_phase_result(
        self,
        result: PhaseResult,
        status: PhaseStatus,
        output: Dict = None,
        errors: List = None,
        warnings: List = None,
        metrics: Dict = None
    ) -> PhaseResult:
        """完成阶段结果"""
        result.status = status
        result.end_time = datetime.now().isoformat()
        if result.start_time:
            start = datetime.fromisoformat(result.start_time)
            end = datetime.fromisoformat(result.end_time)
            result.duration = (end - start).total_seconds()
        result.output = output or {}
        result.errors = errors or []
        result.warnings = warnings or []
        result.metrics = metrics or {}
        return result
    
    def run_spec_parse_phase(self) -> PhaseResult:
        """执行规范解析阶段"""
        result = self._create_phase_result(CyclePhase.SPEC_PARSE)
        
        try:
            spec = self.spec_parser.parse(self.state.spec_path)
            self.state.spec_data = spec
            
            result = self._complete_phase_result(
                result,
                PhaseStatus.PASSED,
                output={"spec": spec},
                metrics={
                    "elements_count": len(spec.get("elements", [])),
                    "spec_type": spec.get("type", "unknown")
                }
            )
            
            if self.config.verbose:
                print(f"[规范解析] 完成: {spec.get('id')} - {spec.get('name')}")
                
        except Exception as e:
            result = self._complete_phase_result(
                result,
                PhaseStatus.FAILED,
                errors=[str(e)]
            )
        
        return result
    
    def run_test_generate_phase(self) -> PhaseResult:
        """执行测试生成阶段"""
        result = self._create_phase_result(CyclePhase.TEST_GENERATE)
        
        try:
            test_cases = self.test_generator.generate_from_spec(self.state.spec_data)
            self.state.test_cases = [asdict(tc) for tc in test_cases]
            
            test_content = self.test_generator.generate_test_file(
                test_cases,
                self.state.spec_data.get("name", "unknown")
            )
            test_file = self.test_generator.save_test_file(
                test_content,
                self.state.spec_data.get("name", "unknown")
            )
            self.state.test_file = str(test_file)
            
            result = self._complete_phase_result(
                result,
                PhaseStatus.PASSED,
                output={
                    "test_file": str(test_file),
                    "test_cases_count": len(test_cases)
                },
                metrics={
                    "test_cases_generated": len(test_cases),
                    "test_file": str(test_file)
                }
            )
            
            if self.config.verbose:
                print(f"[测试生成] 生成 {len(test_cases)} 个测试用例")
                print(f"[测试生成] 测试文件: {test_file}")
                
        except Exception as e:
            result = self._complete_phase_result(
                result,
                PhaseStatus.FAILED,
                errors=[str(e)]
            )
        
        return result
    
    def run_red_phase(self) -> PhaseResult:
        """执行红阶段 - 确认测试失败"""
        result = self._create_phase_result(CyclePhase.RED)
        
        try:
            test_file = Path(self.state.test_file)
            if not test_file.exists():
                raise FileNotFoundError(f"测试文件不存在: {test_file}")
            
            red_result = self._execute_tests_and_confirm_red(test_file)
            
            if red_result["confirmed"]:
                result = self._complete_phase_result(
                    result,
                    PhaseStatus.PASSED,
                    output=red_result,
                    metrics={
                        "failures": len(red_result.get("failures", [])),
                        "red_confirmed": True
                    }
                )
                if self.config.verbose:
                    print(f"[红阶段] 🔴 红灯确认: {len(red_result.get('failures', []))} 个测试失败")
            else:
                result = self._complete_phase_result(
                    result,
                    PhaseStatus.FAILED,
                    output=red_result,
                    warnings=["测试未处于红灯状态，可能测试已实现或测试用例有问题"]
                )
                
        except Exception as e:
            result = self._complete_phase_result(
                result,
                PhaseStatus.FAILED,
                errors=[str(e)]
            )
        
        return result
    
    def _execute_tests_and_confirm_red(self, test_file: Path) -> Dict[str, Any]:
        """执行测试并确认红灯状态"""
        try:
            cmd = [
                sys.executable, "-m", "pytest",
                str(test_file),
                "-v", "--tb=short",
                "--timeout=60"
            ]
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.test_timeout
            )
            
            failures = []
            for line in process.stdout.split("\n"):
                if "FAILED" in line or "ERROR" in line:
                    failures.append(line.strip())
            
            return {
                "confirmed": len(failures) > 0,
                "failures": failures,
                "output": process.stdout
            }
            
        except subprocess.TimeoutExpired:
            return {"confirmed": False, "failures": ["测试执行超时"]}
        except Exception as e:
            return {"confirmed": False, "failures": [str(e)]}
    
    def run_green_phase(self) -> PhaseResult:
        """执行绿阶段 - 提示实现代码"""
        result = self._create_phase_result(CyclePhase.GREEN)
        
        result = self._complete_phase_result(
            result,
            PhaseStatus.PASSED,
            output={
                "message": "绿阶段需要人工实现代码",
                "test_file": self.state.test_file,
                "instructions": [
                    "1. 根据测试用例实现功能代码",
                    "2. 运行测试确认通过",
                    "3. 继续下一阶段"
                ]
            },
            warnings=["绿阶段需要人工干预"]
        )
        
        if self.config.verbose:
            print(f"[绿阶段] 请实现功能代码使测试通过")
            print(f"[绿阶段] 测试文件: {self.state.test_file}")
        
        return result
    
    def run_refactor_phase(self) -> PhaseResult:
        """执行重构阶段"""
        result = self._create_phase_result(CyclePhase.REFACTOR)
        
        if not self.config.enable_refactor:
            result = self._complete_phase_result(
                result,
                PhaseStatus.SKIPPED,
                warnings=["重构阶段已禁用"]
            )
            return result
        
        result = self._complete_phase_result(
            result,
            PhaseStatus.PASSED,
            output={
                "message": "重构阶段完成",
                "recommendations": [
                    "优化代码结构",
                    "消除重复代码",
                    "提高代码可读性"
                ]
            }
        )
        
        if self.config.verbose:
            print(f"[重构阶段] 代码重构建议已生成")
        
        return result
    
    def run_compliance_phase(self) -> PhaseResult:
        """执行合规验证阶段"""
        result = self._create_phase_result(CyclePhase.COMPLIANCE)
        
        if not self.config.enable_compliance:
            result = self._complete_phase_result(
                result,
                PhaseStatus.SKIPPED,
                warnings=["合规验证阶段已禁用"]
            )
            return result
        
        try:
            test_results = {
                "test_cases": self.state.test_cases,
                "statement_coverage": 0,
                "branch_coverage": 0,
                "exception_coverage": 0
            }
            
            report = self.compliance_checker.check_compliance(
                self.state.spec_data,
                test_results
            )
            self.state.compliance_report = asdict(report)
            
            status = PhaseStatus.PASSED if report.status == ComplianceStatus.COMPLIANT else PhaseStatus.FAILED
            
            result = self._complete_phase_result(
                result,
                status,
                output={"compliance_report": asdict(report)},
                metrics={
                    "compliance_rate": report.compliance_rate.get("总体", 0),
                    "violations_count": len(report.violations)
                }
            )
            
            if self.config.verbose:
                print(f"[合规验证] 状态: {report.status.value}")
                print(f"[合规验证] 合规率: {report.compliance_rate.get('总体', 0):.1f}%")
                
        except Exception as e:
            result = self._complete_phase_result(
                result,
                PhaseStatus.FAILED,
                errors=[str(e)]
            )
        
        return result
    
    def run_consistency_phase(self) -> PhaseResult:
        """执行一致性检查阶段"""
        result = self._create_phase_result(CyclePhase.CONSISTENCY)
        
        if not self.config.enable_consistency:
            result = self._complete_phase_result(
                result,
                PhaseStatus.SKIPPED,
                warnings=["一致性检查阶段已禁用"]
            )
            return result
        
        try:
            code_snapshot = {
                "version": "current",
                "functions": [],
                "variables": [],
                "files": []
            }
            
            report = self.consistency_checker.check_consistency(
                self.state.spec_data,
                code_snapshot
            )
            self.state.consistency_report = asdict(report)
            
            status = PhaseStatus.PASSED if report.status == ConsistencyStatus.CONSISTENT else PhaseStatus.FAILED
            
            result = self._complete_phase_result(
                result,
                status,
                output={"consistency_report": asdict(report)},
                metrics={
                    "inconsistencies_count": len(report.inconsistencies)
                }
            )
            
            if self.config.verbose:
                print(f"[一致性检查] 状态: {report.status.value}")
                
        except Exception as e:
            result = self._complete_phase_result(
                result,
                PhaseStatus.FAILED,
                errors=[str(e)]
            )
        
        return result
    
    def run_cycle(self, spec_path: str) -> CycleState:
        """运行完整的SDD-TDD融合循环"""
        self.state = CycleState(
            cycle_id=self._generate_cycle_id(spec_path),
            spec_path=spec_path,
            current_phase=CyclePhase.INIT,
            iteration=0
        )
        
        print("=" * 60)
        print("SDD-TDD 融合循环")
        print("=" * 60)
        print(f"循环ID: {self.state.cycle_id}")
        print(f"规范文件: {spec_path}")
        print()
        
        phases = [
            ("spec_parse", self.run_spec_parse_phase),
            ("test_generate", self.run_test_generate_phase),
            ("red", self.run_red_phase),
            ("green", self.run_green_phase),
            ("refactor", self.run_refactor_phase),
            ("compliance", self.run_compliance_phase),
            ("consistency", self.run_consistency_phase),
        ]
        
        for phase_name, phase_func in phases:
            self.state.current_phase = CyclePhase(phase_name)
            
            print(f"\n>>> 执行阶段: {phase_name}")
            
            try:
                phase_result = phase_func()
                self.state.phase_results[phase_name] = phase_result
                
                self.state_manager.save_state(self.state)
                
                if phase_result.status == PhaseStatus.FAILED:
                    if self.config.fail_fast:
                        self.state.error_message = f"阶段 {phase_name} 失败"
                        self.state.current_phase = CyclePhase.FAILED
                        break
                
            except KeyboardInterrupt:
                self.state.current_phase = CyclePhase.PAUSED
                self.state_manager.save_state(self.state)
                print("\n[中断] 循环已暂停，状态已保存")
                return self.state
            except Exception as e:
                self.state.error_message = str(e)
                self.state.current_phase = CyclePhase.FAILED
                self.state.phase_results[phase_name] = self._complete_phase_result(
                    self._create_phase_result(CyclePhase(phase_name)),
                    PhaseStatus.FAILED,
                    errors=[str(e)]
                )
                break
        
        if self.state.current_phase not in [CyclePhase.FAILED, CyclePhase.PAUSED]:
            self.state.current_phase = CyclePhase.COMPLETED
            self.state.completed = True
            self.state.success = all(
                pr.status in [PhaseStatus.PASSED, PhaseStatus.SKIPPED]
                for pr in self.state.phase_results.values()
            )
        
        self.state_manager.save_state(self.state)
        
        if self.config.generate_report:
            report = self.report_generator.generate_report(self.state)
            report_file = self.report_generator.save_report(report)
            print(f"\n报告已生成: {report_file}")
        
        print("\n" + "=" * 60)
        print(f"SDD-TDD 融合循环 {'完成' if self.state.completed else '终止'}")
        print(f"状态: {'✅ 成功' if self.state.success else '❌ 失败'}")
        print("=" * 60)
        
        return self.state
    
    def resume_cycle(self, state_path: str) -> CycleState:
        """恢复中断的循环"""
        self.state = self.state_manager.load_state(state_path)
        
        print("=" * 60)
        print("恢复 SDD-TDD 融合循环")
        print("=" * 60)
        print(f"循环ID: {self.state.cycle_id}")
        print(f"当前阶段: {self.state.current_phase.value}")
        print()
        
        if self.state.current_phase == CyclePhase.COMPLETED:
            print("循环已完成，无需恢复")
            return self.state
        
        if self.state.current_phase == CyclePhase.FAILED:
            print("循环已失败，无法恢复")
            return self.state
        
        completed_phases = set(self.state.phase_results.keys())
        
        phases = [
            ("spec_parse", self.run_spec_parse_phase),
            ("test_generate", self.run_test_generate_phase),
            ("red", self.run_red_phase),
            ("green", self.run_green_phase),
            ("refactor", self.run_refactor_phase),
            ("compliance", self.run_compliance_phase),
            ("consistency", self.run_consistency_phase),
        ]
        
        for phase_name, phase_func in phases:
            if phase_name in completed_phases:
                continue
            
            self.state.current_phase = CyclePhase(phase_name)
            
            print(f"\n>>> 执行阶段: {phase_name}")
            
            try:
                phase_result = phase_func()
                self.state.phase_results[phase_name] = phase_result
                
                self.state_manager.save_state(self.state)
                
                if phase_result.status == PhaseStatus.FAILED and self.config.fail_fast:
                    self.state.error_message = f"阶段 {phase_name} 失败"
                    self.state.current_phase = CyclePhase.FAILED
                    break
                    
            except KeyboardInterrupt:
                self.state.current_phase = CyclePhase.PAUSED
                self.state_manager.save_state(self.state)
                print("\n[中断] 循环已暂停，状态已保存")
                return self.state
            except Exception as e:
                self.state.error_message = str(e)
                self.state.current_phase = CyclePhase.FAILED
                break
        
        if self.state.current_phase not in [CyclePhase.FAILED, CyclePhase.PAUSED]:
            self.state.current_phase = CyclePhase.COMPLETED
            self.state.completed = True
            self.state.success = all(
                pr.status in [PhaseStatus.PASSED, PhaseStatus.SKIPPED]
                for pr in self.state.phase_results.values()
            )
        
        self.state_manager.save_state(self.state)
        
        if self.config.generate_report:
            report = self.report_generator.generate_report(self.state)
            self.report_generator.save_report(report)
        
        return self.state
    
    def generate_report_from_state(self, state_path: str) -> Dict[str, Any]:
        """从状态文件生成报告"""
        self.state = self.state_manager.load_state(state_path)
        report = self.report_generator.generate_report(self.state)
        return self.report_generator.save_report(report)


def load_config(config_path: str = None) -> CycleConfig:
    """加载配置文件"""
    config = CycleConfig()
    
    if config_path:
        path = Path(config_path)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                if path.suffix in [".yaml", ".yml"]:
                    try:
                        import yaml
                        data = yaml.safe_load(f)
                    except ImportError:
                        data = json.load(f)
                else:
                    data = json.load(f)
                
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
    
    return config


def main():
    parser = argparse.ArgumentParser(
        description="SDD-TDD融合循环工具 (增强版)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行完整循环
  python sdd_tdd_cycle.py run --spec specs/user_auth.yaml
  
  # 使用配置文件
  python sdd_tdd_cycle.py run --spec specs/user_auth.yaml --config cycle_config.yaml
  
  # 恢复中断的循环
  python sdd_tdd_cycle.py resume --state reports/sdd_tdd/cycle_XXX.json
  
  # 从状态生成报告
  python sdd_tdd_cycle.py report --state reports/sdd_tdd/cycle_XXX.json
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    run_parser = subparsers.add_parser("run", help="运行SDD-TDD融合循环")
    run_parser.add_argument("--spec", required=True, help="规范文件路径")
    run_parser.add_argument("--config", help="配置文件路径")
    run_parser.add_argument("--output-dir", default="reports/sdd_tdd", help="输出目录")
    run_parser.add_argument("--verbose", action="store_true", help="详细输出")
    run_parser.add_argument("--fail-fast", action="store_true", help="遇到失败立即停止")
    run_parser.add_argument("--max-iterations", type=int, default=10, help="最大迭代次数")
    run_parser.add_argument("--coverage-threshold", type=float, default=80.0, help="覆盖率阈值")
    run_parser.add_argument("--disable-refactor", action="store_true", help="禁用重构阶段")
    run_parser.add_argument("--disable-compliance", action="store_true", help="禁用合规验证")
    run_parser.add_argument("--disable-consistency", action="store_true", help="禁用一致性检查")
    
    resume_parser = subparsers.add_parser("resume", help="恢复中断的循环")
    resume_parser.add_argument("--state", required=True, help="状态文件路径")
    resume_parser.add_argument("--config", help="配置文件路径")
    
    report_parser = subparsers.add_parser("report", help="生成循环报告")
    report_parser.add_argument("--state", required=True, help="状态文件路径")
    report_parser.add_argument("--output-dir", default="reports/sdd_tdd", help="输出目录")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == "run":
            config = load_config(args.config)
            config.output_dir = args.output_dir
            config.verbose = args.verbose
            config.fail_fast = args.fail_fast
            config.max_iterations = args.max_iterations
            config.coverage_threshold = args.coverage_threshold
            config.enable_refactor = not args.disable_refactor
            config.enable_compliance = not args.disable_compliance
            config.enable_consistency = not args.disable_consistency
            
            cycle = SddTddCycle(config)
            state = cycle.run_cycle(args.spec)
            
            sys.exit(0 if state.success else 1)
            
        elif args.command == "resume":
            config = load_config(args.config)
            cycle = SddTddCycle(config)
            state = cycle.resume_cycle(args.state)
            
            sys.exit(0 if state.success else 1)
            
        elif args.command == "report":
            config = CycleConfig()
            config.output_dir = args.output_dir
            cycle = SddTddCycle(config)
            report_file = cycle.generate_report_from_state(args.state)
            print(f"报告已生成: {report_file}")
            
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
