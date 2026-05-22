#!/usr/bin/env python3
"""
SDD与TDD集成器 (SDD-TDD Integrator)

实现规范驱动开发(SDD)与测试驱动开发(TDD)的深度集成：
1. SDD规范解析功能 - 解析规范文件中的接口定义、数据模型、行为规则
2. 规范到测试用例的自动转换
3. 测试覆盖率映射报告生成
4. 规范完整性验证

特性：
- 支持多种规范格式 (YAML, JSON, Markdown)
- 智能测试用例生成
- 完整的追溯矩阵
- 规范完整性检查
- 覆盖率映射分析

用法:
    python sdd_tdd_integrator.py parse --spec <规范文件>
    python sdd_tdd_integrator.py generate --spec <规范文件> --output <输出目录>
    python sdd_tdd_integrator.py coverage --spec <规范文件> --test-results <测试结果>
    python sdd_tdd_integrator.py validate --spec <规范文件>
"""

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import hashlib

try:
    import yaml
except ImportError:
    yaml = None


class SpecElementType(Enum):
    INTERFACE = auto()
    DATA_MODEL = auto()
    BEHAVIOR_RULE = auto()
    CONSTRAINT = auto()
    EXCEPTION = auto()
    ENDPOINT = auto()
    ATTRIBUTE = auto()


class TestType(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    ACCEPTANCE = "acceptance"
    BOUNDARY = "boundary"
    NEGATIVE = "negative"
    PERFORMANCE = "performance"


class CoverageLevel(Enum):
    FULL = "full"
    PARTIAL = "partial"
    NONE = "none"
    UNKNOWN = "unknown"


class ValidationSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class CyclePhase(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class CycleStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class CycleResult(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    BLOCKED = "blocked"


class QualityGrade(Enum):
    """质量等级枚举"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    CRITICAL = "critical"


class IntegrationStatus(Enum):
    """集成状态枚举"""
    ALIGNED = "aligned"
    PARTIALLY_ALIGNED = "partially_aligned"
    MISALIGNED = "misaligned"
    UNKNOWN = "unknown"


class AutoFixCategory(Enum):
    """自动修复类别枚举"""
    IMPORT_FIX = "import_fix"
    TYPE_FIX = "type_fix"
    LOGIC_FIX = "logic_fix"
    SYNTAX_FIX = "syntax_fix"
    REFACTOR_SUGGESTION = "refactor_suggestion"


@dataclass
class SpecElement:
    name: str
    element_type: SpecElementType
    description: str = ""
    constraints: Dict[str, Any] = field(default_factory=dict)
    attributes: List[Dict[str, Any]] = field(default_factory=list)
    source_location: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InterfaceDefinition:
    name: str
    methods: List[Dict[str, Any]] = field(default_factory=list)
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    return_type: str = ""
    description: str = ""
    exceptions: List[str] = field(default_factory=list)


@dataclass
class DataModel:
    name: str
    attributes: List[Dict[str, Any]] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    constraints: List[Dict[str, Any]] = field(default_factory=list)
    description: str = ""


@dataclass
class BehaviorRule:
    rule_id: str
    name: str
    condition: str
    action: str
    priority: int = 0
    description: str = ""
    triggers: List[str] = field(default_factory=list)


@dataclass
class GeneratedTestCase:
    test_id: str
    name: str
    test_type: TestType
    spec_element_id: str
    spec_element_name: str
    arrange: str
    act: str
    assert_: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    priority: int = 0


@dataclass
class CoverageMapping:
    spec_element_id: str
    spec_element_name: str
    test_ids: List[str] = field(default_factory=list)
    coverage_level: CoverageLevel = CoverageLevel.UNKNOWN
    coverage_percentage: float = 0.0
    untested_aspects: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    info: List[Dict[str, Any]] = field(default_factory=list)
    completeness_score: float = 0.0


@dataclass
class TraceMatrix:
    spec_to_tests: Dict[str, List[str]] = field(default_factory=dict)
    test_to_spec: Dict[str, str] = field(default_factory=dict)
    spec_to_code: Dict[str, List[str]] = field(default_factory=dict)
    code_to_spec: Dict[str, str] = field(default_factory=dict)


@dataclass
class CoverageReport:
    report_id: str
    spec_id: str
    generated_at: str
    overall_coverage: float
    element_coverage: Dict[str, CoverageMapping] = field(default_factory=dict)
    trace_matrix: TraceMatrix = field(default_factory=TraceMatrix)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ParsedSpecification:
    spec_id: str
    spec_name: str
    version: str
    source_path: str
    source_format: str
    interfaces: List[InterfaceDefinition] = field(default_factory=list)
    data_models: List[DataModel] = field(default_factory=list)
    behavior_rules: List[BehaviorRule] = field(default_factory=list)
    constraints: List[Dict[str, Any]] = field(default_factory=list)
    elements: List[SpecElement] = field(default_factory=list)
    raw_content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CyclePhaseRecord:
    phase: CyclePhase
    status: CycleStatus
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    test_cases: List[str] = field(default_factory=list)
    passed_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    error_message: Optional[str] = None
    artifacts: Dict[str, str] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CycleIteration:
    iteration_id: str
    cycle_number: int
    spec_element_id: str
    spec_element_name: str
    red_phase: CyclePhaseRecord = field(default_factory=lambda: CyclePhaseRecord(CyclePhase.RED, CycleStatus.PENDING))
    green_phase: CyclePhaseRecord = field(default_factory=lambda: CyclePhaseRecord(CyclePhase.GREEN, CycleStatus.PENDING))
    blue_phase: CyclePhaseRecord = field(default_factory=lambda: CyclePhaseRecord(CyclePhase.BLUE, CycleStatus.PENDING))
    overall_result: CycleResult = CycleResult.PARTIAL
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    notes: List[str] = field(default_factory=list)


@dataclass
class CycleExecutionReport:
    report_id: str
    spec_id: str
    spec_name: str
    started_at: str
    completed_at: Optional[str] = None
    total_iterations: int = 0
    completed_iterations: int = 0
    failed_iterations: int = 0
    iterations: List[CycleIteration] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpecTestMapping:
    """规范到测试的智能映射"""
    spec_element_id: str
    spec_element_name: str
    test_case_ids: List[str] = field(default_factory=list)
    mapping_confidence: float = 0.0
    mapping_type: str = "direct"
    semantic_similarity: float = 0.0
    structural_match: bool = False
    behavior_coverage: float = 0.0
    integration_status: IntegrationStatus = IntegrationStatus.UNKNOWN
    trace_links: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class IntegrationValidation:
    """集成验证结果"""
    is_valid: bool
    spec_element_id: str
    test_case_id: str
    alignment_score: float = 0.0
    gaps: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    validation_details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AutoFixSuggestion:
    """自动修复建议"""
    fix_id: str
    category: AutoFixCategory
    description: str
    target_location: str
    suggested_fix: str
    confidence: float = 0.0
    impact: str = "low"
    auto_applicable: bool = False
    prerequisites: List[str] = field(default_factory=list)


@dataclass
class DependencyInfo:
    """依赖信息"""
    element_id: str
    element_name: str
    depends_on: List[str] = field(default_factory=list)
    depended_by: List[str] = field(default_factory=list)
    dependency_level: int = 0
    is_circular: bool = False
    resolution_order: int = 0


@dataclass
class CycleIntelligence:
    """循环智能分析结果"""
    iteration_id: str
    phase: CyclePhase
    analysis_type: str
    findings: List[Dict[str, Any]] = field(default_factory=list)
    patterns_detected: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    optimization_suggestions: List[str] = field(default_factory=list)
    predicted_issues: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class QualityAssessment:
    """质量评估结果"""
    assessment_id: str
    target_type: str
    target_id: str
    overall_grade: QualityGrade = QualityGrade.ACCEPTABLE
    overall_score: float = 0.0
    dimensions: Dict[str, float] = field(default_factory=dict)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    improvement_areas: List[str] = field(default_factory=list)
    benchmark_comparison: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeQualityMetrics:
    """代码质量指标"""
    complexity_score: float = 0.0
    maintainability_index: float = 0.0
    testability_score: float = 0.0
    coupling_score: float = 0.0
    cohesion_score: float = 0.0
    duplication_ratio: float = 0.0
    documentation_coverage: float = 0.0
    naming_quality: float = 0.0


@dataclass
class TestQualityMetrics:
    """测试质量指标"""
    assertion_density: float = 0.0
    test_independence: float = 0.0
    test_coverage: float = 0.0
    test_readability: float = 0.0
    test_speed: float = 0.0
    test_reliability: float = 0.0
    boundary_coverage: float = 0.0
    exception_coverage: float = 0.0


@dataclass
class RefactoringQualityMetrics:
    """重构质量指标"""
    behavior_preservation: float = 0.0
    code_improvement: float = 0.0
    design_pattern_adherence: float = 0.0
    test_stability: float = 0.0
    performance_impact: float = 0.0
    readability_improvement: float = 0.0


@dataclass
class RealtimeProgress:
    """实时进度信息"""
    current_phase: CyclePhase
    current_iteration: int
    total_iterations: int
    phase_progress: float = 0.0
    overall_progress: float = 0.0
    estimated_remaining_seconds: float = 0.0
    current_activity: str = ""
    recent_events: List[Dict[str, Any]] = field(default_factory=list)
    health_status: str = "healthy"


@dataclass
class CheckpointData:
    """检查点数据"""
    checkpoint_id: str
    timestamp: str
    iteration_index: int
    phase: CyclePhase
    state_data: Dict[str, Any] = field(default_factory=dict)
    recovery_info: Dict[str, Any] = field(default_factory=dict)


class SpecParser:
    """SDD规范解析器 - 解析规范文件中的接口定义、数据模型、行为规则"""
    
    SUPPORTED_FORMATS = [".yaml", ".yml", ".json", ".md"]
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self.element_counter = 0
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("SDDSpecParser")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def parse_file(self, file_path: str) -> ParsedSpecification:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"规范文件不存在: {file_path}")
        
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        source_format = self._detect_format(path)
        return self.parse_content(content, source_format, str(path))
    
    def parse_content(
        self,
        content: str,
        source_format: str,
        source_path: str = ""
    ) -> ParsedSpecification:
        if source_format == "yaml":
            parsed = self._parse_yaml(content)
        elif source_format == "json":
            parsed = self._parse_json(content)
        elif source_format == "markdown":
            parsed = self._parse_markdown(content)
        else:
            raise ValueError(f"不支持的格式: {source_format}")
        
        return self._build_specification(parsed, content, source_format, source_path)
    
    def _detect_format(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in [".yaml", ".yml"]:
            return "yaml"
        elif suffix == ".json":
            return "json"
        elif suffix == ".md":
            return "markdown"
        else:
            raise ValueError(f"无法识别的文件格式: {suffix}")
    
    def _parse_yaml(self, content: str) -> Dict[str, Any]:
        if yaml is None:
            raise RuntimeError("需要安装 PyYAML: pip install pyyaml")
        return yaml.safe_load(content)
    
    def _parse_json(self, content: str) -> Dict[str, Any]:
        return json.loads(content)
    
    def _parse_markdown(self, content: str) -> Dict[str, Any]:
        spec = {
            "id": self._extract_id(content),
            "name": self._extract_name(content),
            "version": self._extract_version(content),
            "interfaces": self._extract_interfaces(content),
            "data_models": self._extract_data_models(content),
            "behavior_rules": self._extract_behavior_rules(content),
            "constraints": self._extract_constraints(content),
        }
        return spec
    
    def _extract_id(self, content: str) -> str:
        patterns = [
            r"规范ID[：:]\s*(\S+)",
            r"Spec\s*ID[：:]\s*(\S+)",
            r"id[：:]\s*(\S+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        return f"SPC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def _extract_name(self, content: str) -> str:
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        return match.group(1).strip() if match else "未命名规范"
    
    def _extract_version(self, content: str) -> str:
        match = re.search(r"版本[：:]\s*(\S+)", content)
        return match.group(1) if match else "v1.0"
    
    def _extract_interfaces(self, content: str) -> List[Dict[str, Any]]:
        interfaces = []
        
        interface_pattern = r"##\s*(?:接口定义|Interface)[\s\S]*?(?=\n##|\Z)"
        for match in re.finditer(interface_pattern, content):
            section = match.group(0)
            
            method_pattern = r"###\s*(.+?)\s*\n([\s\S]*?)(?=\n###|\n##|\Z)"
            for method_match in re.finditer(method_pattern, section):
                interface = {
                    "name": method_match.group(1).strip(),
                    "methods": [],
                    "parameters": self._extract_parameters(method_match.group(2)),
                    "return_type": self._extract_return_type(method_match.group(2)),
                    "description": self._extract_description(method_match.group(2)),
                    "exceptions": self._extract_exceptions_from_section(method_match.group(2))
                }
                interfaces.append(interface)
        
        return interfaces
    
    def _extract_data_models(self, content: str) -> List[Dict[str, Any]]:
        models = []
        
        model_pattern = r"##\s*(?:数据模型|Data\s*Model|实体定义)[\s\S]*?(?=\n##|\Z)"
        for match in re.finditer(model_pattern, content):
            section = match.group(0)
            
            attr_pattern = r"[-*]\s*(.+?)(?:[：:]\s*(.+))?$"
            attributes = []
            for line in section.split("\n"):
                attr_match = re.match(attr_pattern, line.strip())
                if attr_match:
                    attr_name = attr_match.group(1).strip()
                    attr_desc = attr_match.group(2).strip() if attr_match.group(2) else ""
                    
                    type_match = re.search(r"类型[：:]\s*(\w+)", attr_desc)
                    attr_type = type_match.group(1) if type_match else "string"
                    
                    attributes.append({
                        "name": attr_name,
                        "type": attr_type,
                        "description": re.sub(r"[，,]?\s*类型[：:]\s*\w+", "", attr_desc).strip(),
                        "required": "必填" in attr_desc or "required" in attr_desc.lower()
                    })
            
            if attributes:
                models.append({
                    "name": self._extract_model_name(section),
                    "attributes": attributes,
                    "relationships": [],
                    "constraints": []
                })
        
        return models
    
    def _extract_model_name(self, section: str) -> str:
        match = re.search(r"###\s*(.+?)(?:\s*$|\n)", section)
        return match.group(1).strip() if match else "未命名模型"
    
    def _extract_behavior_rules(self, content: str) -> List[Dict[str, Any]]:
        rules = []
        
        rule_pattern = r"##\s*(?:行为规则|Business\s*Rules?|业务规则)[\s\S]*?(?=\n##|\Z)"
        for match in re.finditer(rule_pattern, content):
            section = match.group(0)
            
            single_rule_pattern = r"[-*]\s*(?:规则\s*(\d+)[.：:])?\s*(.+?)(?:[：:]\s*(.+))?$"
            for line in section.split("\n"):
                rule_match = re.match(single_rule_pattern, line.strip())
                if rule_match:
                    rule_id = rule_match.group(1) or f"R{len(rules)+1:03d}"
                    rule_name = rule_match.group(2).strip()
                    rule_desc = rule_match.group(3).strip() if rule_match.group(3) else ""
                    
                    rules.append({
                        "rule_id": rule_id,
                        "name": rule_name,
                        "condition": self._extract_condition(rule_desc),
                        "action": self._extract_action(rule_desc),
                        "description": rule_desc
                    })
        
        return rules
    
    def _extract_condition(self, text: str) -> str:
        match = re.search(r"(?:当|When|如果|If)[：:]\s*(.+?)(?=(?:则|Then|执行|Execute)|$)", text)
        return match.group(1).strip() if match else ""
    
    def _extract_action(self, text: str) -> str:
        match = re.search(r"(?:则|Then|执行|Execute)[：:]\s*(.+)$", text)
        return match.group(1).strip() if match else ""
    
    def _extract_constraints(self, content: str) -> List[Dict[str, Any]]:
        constraints = []
        
        constraint_pattern = r"##\s*(?:约束条件|Constraints?|限制)[\s\S]*?(?=\n##|\Z)"
        for match in re.finditer(constraint_pattern, content):
            section = match.group(0)
            
            single_constraint = r"[-*]\s*(.+?)(?:[：:]\s*(.+))?$"
            for line in section.split("\n"):
                c_match = re.match(single_constraint, line.strip())
                if c_match:
                    constraints.append({
                        "name": c_match.group(1).strip(),
                        "description": c_match.group(2).strip() if c_match.group(2) else ""
                    })
        
        return constraints
    
    def _extract_parameters(self, section: str) -> List[Dict[str, Any]]:
        parameters = []
        param_pattern = r"[-*]\s*(\w+)(?:\s*[\(（](\w+)[\)）])?(?:[：:]\s*(.+))?$"
        
        for line in section.split("\n"):
            match = re.match(param_pattern, line.strip())
            if match:
                parameters.append({
                    "name": match.group(1),
                    "type": match.group(2) or "any",
                    "description": match.group(3).strip() if match.group(3) else ""
                })
        
        return parameters
    
    def _extract_return_type(self, section: str) -> str:
        match = re.search(r"(?:返回|Return)[：:]\s*(\w+)", section)
        return match.group(1) if match else "void"
    
    def _extract_description(self, section: str) -> str:
        lines = section.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith(("#", "-", "*")):
                return line
        return ""
    
    def _extract_exceptions_from_section(self, section: str) -> List[str]:
        exceptions = []
        exc_pattern = r"(?:异常|Exception|错误|Error)[：:]\s*(\w+)"
        
        for match in re.finditer(exc_pattern, section):
            exceptions.append(match.group(1))
        
        return exceptions
    
    def _build_specification(
        self,
        parsed: Dict[str, Any],
        raw_content: str,
        source_format: str,
        source_path: str
    ) -> ParsedSpecification:
        spec_id = parsed.get("id") or parsed.get("metadata", {}).get("id", "")
        spec_name = parsed.get("name") or parsed.get("metadata", {}).get("name", "未命名规范")
        version = parsed.get("version") or parsed.get("metadata", {}).get("version", "v1.0")
        
        interfaces = self._build_interfaces(parsed)
        data_models = self._build_data_models(parsed)
        behavior_rules = self._build_behavior_rules(parsed)
        constraints = parsed.get("constraints", [])
        
        elements = self._build_elements(interfaces, data_models, behavior_rules, constraints)
        
        return ParsedSpecification(
            spec_id=spec_id,
            spec_name=spec_name,
            version=version,
            source_path=source_path,
            source_format=source_format,
            interfaces=interfaces,
            data_models=data_models,
            behavior_rules=behavior_rules,
            constraints=constraints,
            elements=elements,
            raw_content=raw_content,
            metadata=parsed.get("metadata", {})
        )
    
    def _build_interfaces(self, parsed: Dict[str, Any]) -> List[InterfaceDefinition]:
        interfaces = []
        
        for iface_data in parsed.get("interfaces", []):
            iface = InterfaceDefinition(
                name=iface_data.get("name", ""),
                methods=iface_data.get("methods", []),
                parameters=iface_data.get("parameters", []),
                return_type=iface_data.get("return_type", "void"),
                description=iface_data.get("description", ""),
                exceptions=iface_data.get("exceptions", [])
            )
            interfaces.append(iface)
        
        for endpoint in parsed.get("spec", {}).get("endpoints", []):
            iface = InterfaceDefinition(
                name=endpoint.get("name", ""),
                methods=[{
                    "method": endpoint.get("method", "GET"),
                    "path": endpoint.get("path", "/")
                }],
                parameters=endpoint.get("parameters", []),
                return_type="response",
                description=endpoint.get("description", ""),
                exceptions=[e.get("name", "") for e in endpoint.get("errors", [])]
            )
            interfaces.append(iface)
        
        return interfaces
    
    def _build_data_models(self, parsed: Dict[str, Any]) -> List[DataModel]:
        models = []
        
        for model_data in parsed.get("data_models", []):
            model = DataModel(
                name=model_data.get("name", ""),
                attributes=model_data.get("attributes", []),
                relationships=model_data.get("relationships", []),
                constraints=model_data.get("constraints", []),
                description=model_data.get("description", "")
            )
            models.append(model)
        
        for attr_data in parsed.get("spec", {}).get("attributes", []):
            model = DataModel(
                name=attr_data.get("name", ""),
                attributes=[attr_data],
                description=attr_data.get("description", "")
            )
            models.append(model)
        
        return models
    
    def _build_behavior_rules(self, parsed: Dict[str, Any]) -> List[BehaviorRule]:
        rules = []
        
        for rule_data in parsed.get("behavior_rules", []):
            rule = BehaviorRule(
                rule_id=rule_data.get("rule_id", f"R{len(rules)+1:03d}"),
                name=rule_data.get("name", ""),
                condition=rule_data.get("condition", ""),
                action=rule_data.get("action", ""),
                priority=rule_data.get("priority", 0),
                description=rule_data.get("description", ""),
                triggers=rule_data.get("triggers", [])
            )
            rules.append(rule)
        
        for scenario in parsed.get("spec", {}).get("scenarios", []):
            rule = BehaviorRule(
                rule_id=f"SCN-{len(rules)+1:03d}",
                name=scenario.get("name", ""),
                condition=scenario.get("given", ""),
                action=scenario.get("when", ""),
                description=scenario.get("then", "")
            )
            rules.append(rule)
        
        return rules
    
    def _build_elements(
        self,
        interfaces: List[InterfaceDefinition],
        data_models: List[DataModel],
        behavior_rules: List[BehaviorRule],
        constraints: List[Dict[str, Any]]
    ) -> List[SpecElement]:
        elements = []
        
        for iface in interfaces:
            self.element_counter += 1
            elements.append(SpecElement(
                name=iface.name,
                element_type=SpecElementType.INTERFACE,
                description=iface.description,
                attributes=[{"name": p["name"], "type": p.get("type", "any")} for p in iface.parameters],
                metadata={"exceptions": iface.exceptions, "return_type": iface.return_type}
            ))
        
        for model in data_models:
            self.element_counter += 1
            elements.append(SpecElement(
                name=model.name,
                element_type=SpecElementType.DATA_MODEL,
                description=model.description,
                attributes=model.attributes,
                constraints={c.get("name", ""): c for c in model.constraints}
            ))
        
        for rule in behavior_rules:
            self.element_counter += 1
            elements.append(SpecElement(
                name=rule.name,
                element_type=SpecElementType.BEHAVIOR_RULE,
                description=rule.description,
                constraints={"condition": rule.condition, "action": rule.action},
                metadata={"rule_id": rule.rule_id, "priority": rule.priority}
            ))
        
        for constraint in constraints:
            self.element_counter += 1
            elements.append(SpecElement(
                name=constraint.get("name", ""),
                element_type=SpecElementType.CONSTRAINT,
                description=constraint.get("description", "")
            ))
        
        return elements


class TestCaseGenerator:
    """规范到测试用例的自动转换器"""
    
    TEST_NAMING_PATTERNS = {
        TestType.UNIT: "test_{element}_{scenario}_{expected}",
        TestType.INTEGRATION: "test_{element}_integration_{scenario}",
        TestType.ACCEPTANCE: "test_{element}_acceptance_{scenario}",
        TestType.BOUNDARY: "test_{element}_boundary_{condition}",
        TestType.NEGATIVE: "test_{element}_negative_{error}",
        TestType.PERFORMANCE: "test_{element}_performance_{metric}",
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self.test_counter = 0
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("TestCaseGenerator")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def generate_from_spec(self, spec: ParsedSpecification) -> List[GeneratedTestCase]:
        test_cases = []
        
        for iface in spec.interfaces:
            test_cases.extend(self._generate_interface_tests(iface, spec.spec_id))
        
        for model in spec.data_models:
            test_cases.extend(self._generate_model_tests(model, spec.spec_id))
        
        for rule in spec.behavior_rules:
            test_cases.extend(self._generate_rule_tests(rule, spec.spec_id))
        
        for constraint in spec.constraints:
            test_cases.extend(self._generate_constraint_tests(constraint, spec.spec_id))
        
        self.logger.info(f"从规范 {spec.spec_id} 生成了 {len(test_cases)} 个测试用例")
        return test_cases
    
    def _generate_interface_tests(
        self,
        iface: InterfaceDefinition,
        spec_id: str
    ) -> List[GeneratedTestCase]:
        tests = []
        
        self.test_counter += 1
        test_id = f"TC-{spec_id}-IF-{self.test_counter:03d}"
        tests.append(GeneratedTestCase(
            test_id=test_id,
            name=self._format_test_name(TestType.UNIT, iface.name, "valid_input", "success"),
            test_type=TestType.UNIT,
            spec_element_id=iface.name,
            spec_element_name=iface.name,
            arrange=f"# 准备有效的输入参数: {', '.join(p['name'] for p in iface.parameters)}",
            act=f"# 调用接口 {iface.name}",
            assert_=f"# 验证返回类型为 {iface.return_type}",
            description=f"测试接口 {iface.name} 的正常调用",
            tags=["interface", "unit"],
            priority=1
        ))
        
        for exc in iface.exceptions:
            self.test_counter += 1
            test_id = f"TC-{spec_id}-IF-{self.test_counter:03d}"
            tests.append(GeneratedTestCase(
                test_id=test_id,
                name=self._format_test_name(TestType.NEGATIVE, iface.name, "invalid_input", exc),
                test_type=TestType.NEGATIVE,
                spec_element_id=iface.name,
                spec_element_name=iface.name,
                arrange=f"# 准备触发 {exc} 的输入",
                act=f"# 调用接口 {iface.name}",
                assert_=f"# 验证抛出 {exc} 异常",
                description=f"测试接口 {iface.name} 在异常情况下的行为",
                tags=["interface", "negative", "exception"],
                priority=2
            ))
        
        self.test_counter += 1
        test_id = f"TC-{spec_id}-IF-{self.test_counter:03d}"
        tests.append(GeneratedTestCase(
            test_id=test_id,
            name=self._format_test_name(TestType.BOUNDARY, iface.name, "edge_case", "handled"),
            test_type=TestType.BOUNDARY,
            spec_element_id=iface.name,
            spec_element_name=iface.name,
            arrange=f"# 准备边界值输入",
            act=f"# 调用接口 {iface.name}",
            assert_=f"# 验证边界情况正确处理",
            description=f"测试接口 {iface.name} 的边界条件",
            tags=["interface", "boundary"],
            priority=2
        ))
        
        return tests
    
    def _generate_model_tests(
        self,
        model: DataModel,
        spec_id: str
    ) -> List[GeneratedTestCase]:
        tests = []
        
        self.test_counter += 1
        test_id = f"TC-{spec_id}-DM-{self.test_counter:03d}"
        tests.append(GeneratedTestCase(
            test_id=test_id,
            name=self._format_test_name(TestType.UNIT, model.name, "creation", "valid"),
            test_type=TestType.UNIT,
            spec_element_id=model.name,
            spec_element_name=model.name,
            arrange=f"# 准备有效的属性值: {', '.join(a['name'] for a in model.attributes)}",
            act=f"# 创建 {model.name} 实例",
            assert_=f"# 验证实例创建成功且属性正确",
            description=f"测试数据模型 {model.name} 的创建",
            tags=["data_model", "unit"],
            priority=1
        ))
        
        required_attrs = [a for a in model.attributes if a.get("required", True)]
        if required_attrs:
            self.test_counter += 1
            test_id = f"TC-{spec_id}-DM-{self.test_counter:03d}"
            tests.append(GeneratedTestCase(
                test_id=test_id,
                name=self._format_test_name(TestType.NEGATIVE, model.name, "missing_required", "validation_error"),
                test_type=TestType.NEGATIVE,
                spec_element_id=model.name,
                spec_element_name=model.name,
                arrange=f"# 缺少必填属性: {', '.join(a['name'] for a in required_attrs)}",
                act=f"# 尝试创建 {model.name} 实例",
                assert_=f"# 验证抛出验证错误",
                description=f"测试数据模型 {model.name} 缺少必填属性时的验证",
                tags=["data_model", "negative", "validation"],
                priority=2
            ))
        
        for attr in model.attributes:
            if "max" in str(attr.get("type", "")).lower() or "length" in str(attr.get("constraints", {})):
                self.test_counter += 1
                test_id = f"TC-{spec_id}-DM-{self.test_counter:03d}"
                tests.append(GeneratedTestCase(
                    test_id=test_id,
                    name=self._format_test_name(TestType.BOUNDARY, model.name, f"{attr['name']}_limit", "valid"),
                    test_type=TestType.BOUNDARY,
                    spec_element_id=model.name,
                    spec_element_name=model.name,
                    arrange=f"# 准备属性 {attr['name']} 的边界值",
                    act=f"# 创建 {model.name} 实例",
                    assert_=f"# 验证边界值被正确处理",
                    description=f"测试数据模型 {model.name} 属性 {attr['name']} 的边界条件",
                    tags=["data_model", "boundary"],
                    priority=2
                ))
        
        return tests
    
    def _generate_rule_tests(
        self,
        rule: BehaviorRule,
        spec_id: str
    ) -> List[GeneratedTestCase]:
        tests = []
        
        self.test_counter += 1
        test_id = f"TC-{spec_id}-BR-{self.test_counter:03d}"
        tests.append(GeneratedTestCase(
            test_id=test_id,
            name=self._format_test_name(TestType.UNIT, rule.name, "triggered", "action_executed"),
            test_type=TestType.UNIT,
            spec_element_id=rule.rule_id,
            spec_element_name=rule.name,
            arrange=f"# 设置条件: {rule.condition}",
            act=f"# 触发规则",
            assert_=f"# 验证执行动作: {rule.action}",
            description=f"测试行为规则 {rule.name} 被触发时的行为",
            tags=["behavior_rule", "unit"],
            priority=1
        ))
        
        self.test_counter += 1
        test_id = f"TC-{spec_id}-BR-{self.test_counter:03d}"
        tests.append(GeneratedTestCase(
            test_id=test_id,
            name=self._format_test_name(TestType.NEGATIVE, rule.name, "not_triggered", "no_action"),
            test_type=TestType.NEGATIVE,
            spec_element_id=rule.rule_id,
            spec_element_name=rule.name,
            arrange=f"# 不满足条件: {rule.condition}",
            act=f"# 检查规则状态",
            assert_=f"# 验证动作未执行",
            description=f"测试行为规则 {rule.name} 未被触发时的行为",
            tags=["behavior_rule", "negative"],
            priority=2
        ))
        
        return tests
    
    def _generate_constraint_tests(
        self,
        constraint: Dict[str, Any],
        spec_id: str
    ) -> List[GeneratedTestCase]:
        tests = []
        
        constraint_name = constraint.get("name", "unknown")
        
        self.test_counter += 1
        test_id = f"TC-{spec_id}-CON-{self.test_counter:03d}"
        tests.append(GeneratedTestCase(
            test_id=test_id,
            name=self._format_test_name(TestType.UNIT, constraint_name, "valid", "satisfied"),
            test_type=TestType.UNIT,
            spec_element_id=constraint_name,
            spec_element_name=constraint_name,
            arrange=f"# 准备满足约束的数据",
            act=f"# 验证约束 {constraint_name}",
            assert_=f"# 验证约束被满足",
            description=f"测试约束 {constraint_name} 被满足的情况",
            tags=["constraint", "unit"],
            priority=1
        ))
        
        self.test_counter += 1
        test_id = f"TC-{spec_id}-CON-{self.test_counter:03d}"
        tests.append(GeneratedTestCase(
            test_id=test_id,
            name=self._format_test_name(TestType.NEGATIVE, constraint_name, "violated", "error"),
            test_type=TestType.NEGATIVE,
            spec_element_id=constraint_name,
            spec_element_name=constraint_name,
            arrange=f"# 准备违反约束的数据",
            act=f"# 验证约束 {constraint_name}",
            assert_=f"# 验证抛出约束违反错误",
            description=f"测试约束 {constraint_name} 被违反的情况",
            tags=["constraint", "negative"],
            priority=2
        ))
        
        return tests
    
    def _format_test_name(
        self,
        test_type: TestType,
        element: str,
        scenario: str,
        expected: str
    ) -> str:
        pattern = self.TEST_NAMING_PATTERNS.get(test_type, self.TEST_NAMING_PATTERNS[TestType.UNIT])
        return pattern.format(
            element=self._sanitize_name(element),
            scenario=self._sanitize_name(scenario),
            expected=self._sanitize_name(expected),
            condition=self._sanitize_name(scenario),
            error=self._sanitize_name(expected),
            metric=self._sanitize_name(expected)
        )
    
    def _sanitize_name(self, name: str) -> str:
        sanitized = re.sub(r"[^\w\s]", "", name)
        return "_".join(sanitized.lower().split())
    
    def generate_test_file_content(
        self,
        test_cases: List[GeneratedTestCase],
        spec: ParsedSpecification
    ) -> str:
        lines = [
            '#!/usr/bin/env python3',
            '"""',
            f'自动生成的测试文件',
            f'规范: {spec.spec_name} (ID: {spec.spec_id})',
            f'版本: {spec.version}',
            f'生成时间: {datetime.now().isoformat()}',
            '',
            f'此文件由 SDD-TDD Integrator 自动生成',
            '"""',
            '',
            'import pytest',
            'from typing import Any, Dict, List, Optional',
            '',
            '',
            f'class Test{self._to_class_name(spec.spec_name)}:',
            f'    """测试类: {spec.spec_name}"""',
            '',
        ]
        
        for tc in test_cases:
            lines.extend([
                f'    def {tc.name}(self) -> None:',
                f'        """测试: {tc.description}"""',
                f'        # Arrange',
                f'        {tc.arrange}',
                '',
                f'        # Act',
                f'        {tc.act}',
                '',
                f'        # Assert',
                f'        {tc.assert_}',
                f'        pytest.fail("测试尚未实现")',
                '',
                '',
            ])
        
        return "\n".join(lines)
    
    def _to_class_name(self, name: str) -> str:
        return "".join(word.capitalize() for word in re.split(r"[\s_-]+", name))


class CoverageMapper:
    """测试覆盖率映射报告生成器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("CoverageMapper")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def generate_coverage_report(
        self,
        spec: ParsedSpecification,
        test_cases: List[GeneratedTestCase],
        test_results: Optional[Dict[str, Any]] = None
    ) -> CoverageReport:
        trace_matrix = self._build_trace_matrix(spec, test_cases)
        
        element_coverage = self._calculate_element_coverage(
            spec.elements,
            test_cases,
            test_results
        )
        
        overall_coverage = self._calculate_overall_coverage(element_coverage)
        
        recommendations = self._generate_recommendations(element_coverage, overall_coverage)
        
        report_id = f"COV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return CoverageReport(
            report_id=report_id,
            spec_id=spec.spec_id,
            generated_at=datetime.now().isoformat(),
            overall_coverage=overall_coverage,
            element_coverage=element_coverage,
            trace_matrix=trace_matrix,
            recommendations=recommendations
        )
    
    def _build_trace_matrix(
        self,
        spec: ParsedSpecification,
        test_cases: List[GeneratedTestCase]
    ) -> TraceMatrix:
        matrix = TraceMatrix()
        
        for element in spec.elements:
            element_id = element.name
            
            for tc in test_cases:
                if tc.spec_element_name == element.name:
                    matrix.spec_to_tests.setdefault(element_id, []).append(tc.test_id)
                    matrix.test_to_spec[tc.test_id] = element_id
        
        return matrix
    
    def _calculate_element_coverage(
        self,
        elements: List[SpecElement],
        test_cases: List[GeneratedTestCase],
        test_results: Optional[Dict[str, Any]]
    ) -> Dict[str, CoverageMapping]:
        coverage = {}
        
        for element in elements:
            related_tests = [
                tc for tc in test_cases
                if tc.spec_element_name == element.name
            ]
            
            test_ids = [tc.test_id for tc in related_tests]
            
            if not test_ids:
                coverage_level = CoverageLevel.NONE
                coverage_percentage = 0.0
                untested_aspects = [element.name]
            elif len(test_ids) >= 3:
                coverage_level = CoverageLevel.FULL
                coverage_percentage = 100.0
                untested_aspects = []
            else:
                coverage_level = CoverageLevel.PARTIAL
                coverage_percentage = len(test_ids) / 3.0 * 100
                untested_aspects = self._identify_untested_aspects(element, related_tests)
            
            if test_results:
                passed_tests = [
                    tid for tid in test_ids
                    if test_results.get("tests", {}).get(tid, {}).get("status") == "passed"
                ]
                if test_ids:
                    coverage_percentage = len(passed_tests) / len(test_ids) * 100
            
            coverage[element.name] = CoverageMapping(
                spec_element_id=element.name,
                spec_element_name=element.name,
                test_ids=test_ids,
                coverage_level=coverage_level,
                coverage_percentage=coverage_percentage,
                untested_aspects=untested_aspects
            )
        
        return coverage
    
    def _identify_untested_aspects(
        self,
        element: SpecElement,
        related_tests: List[GeneratedTestCase]
    ) -> List[str]:
        tested_types = {tc.test_type for tc in related_tests}
        untested = []
        
        required_types = {TestType.UNIT, TestType.NEGATIVE, TestType.BOUNDARY}
        missing_types = required_types - tested_types
        
        for missing_type in missing_types:
            untested.append(f"{missing_type.value}_test")
        
        if element.element_type == SpecElementType.INTERFACE:
            if not any(tc.test_type == TestType.INTEGRATION for tc in related_tests):
                untested.append("integration_test")
        
        return untested
    
    def _calculate_overall_coverage(
        self,
        element_coverage: Dict[str, CoverageMapping]
    ) -> float:
        if not element_coverage:
            return 0.0
        
        total_percentage = sum(
            mapping.coverage_percentage
            for mapping in element_coverage.values()
        )
        
        return total_percentage / len(element_coverage)
    
    def _generate_recommendations(
        self,
        element_coverage: Dict[str, CoverageMapping],
        overall_coverage: float
    ) -> List[str]:
        recommendations = []
        
        if overall_coverage < 50:
            recommendations.append("覆盖率严重不足，建议优先补充核心功能的测试用例")
        elif overall_coverage < 80:
            recommendations.append("覆盖率有待提高，建议补充边界条件和异常情况的测试")
        
        uncovered_elements = [
            name for name, mapping in element_coverage.items()
            if mapping.coverage_level == CoverageLevel.NONE
        ]
        if uncovered_elements:
            recommendations.append(
                f"以下规范元素缺少测试覆盖: {', '.join(uncovered_elements[:5])}"
            )
        
        partial_elements = [
            name for name, mapping in element_coverage.items()
            if mapping.coverage_level == CoverageLevel.PARTIAL
        ]
        if partial_elements:
            recommendations.append(
                f"以下规范元素测试覆盖不完整: {', '.join(partial_elements[:5])}"
            )
        
        if overall_coverage >= 80:
            recommendations.append("覆盖率良好，建议持续维护测试用例")
        
        return recommendations


class SpecValidator:
    """规范完整性验证器"""
    
    REQUIRED_SPEC_FIELDS = ["id", "name", "version"]
    REQUIRED_INTERFACE_FIELDS = ["name"]
    REQUIRED_MODEL_FIELDS = ["name", "attributes"]
    REQUIRED_RULE_FIELDS = ["rule_id", "name", "condition", "action"]
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("SpecValidator")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def validate(self, spec: ParsedSpecification) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        
        self._validate_basic_fields(spec, result)
        self._validate_interfaces(spec, result)
        self._validate_data_models(spec, result)
        self._validate_behavior_rules(spec, result)
        self._validate_consistency(spec, result)
        
        result.completeness_score = self._calculate_completeness(spec, result)
        
        return result
    
    def _execute_green_phase_enhanced(
        self,
        element: SpecElement,
        spec: ParsedSpecification,
        test_runner: Optional[callable],
        code_generator: Optional[callable],
        dry_run: bool
    ) -> Dict[str, Any]:
        """增强的GREEN阶段执行 - 包含智能分析和代码质量检查"""
        self.logger.info(f"\n[GREEN 阶段 - 增强] 编写最小实现: {element.name}")
        
        phase_record = self.state_tracker.start_phase(CyclePhase.GREEN)
        
        self._update_progress(CyclePhase.GREEN, 0, 0, "编写最小实现")
        
        result = {
            "success": False,
            "error": None,
            "intelligence": None,
            "fix_suggestions": [],
            "code_quality": None
        }
        
        try:
            if dry_run:
                self.logger.info("[DRY RUN] 跳过代码生成和测试执行")
                passed, failed, skipped = 1, 0, 0
                result["success"] = True
            else:
                if code_generator:
                    code_artifacts = code_generator(element, spec)
                    self.logger.info(f"生成代码: {list(code_artifacts.keys())}")
                    
                    for file_path, code_content in code_artifacts.items():
                        if isinstance(code_content, str):
                            smells = self.auto_fix_analyzer.analyze_code_smells(code_content, spec)
                            if smells:
                                result["fix_suggestions"].extend(smells)
                                self.logger.info(f"检测到 {len(smells)} 个代码异味")
                
                if test_runner:
                    iteration = self.state_tracker.current_iteration
                    test_case_ids = iteration.red_phase.test_cases
                    
                    test_results = test_runner(test_case_ids)
                    passed = test_results.get("passed", 0)
                    failed = test_results.get("failed", 0)
                    skipped = test_results.get("skipped", 0)
                    
                    if failed > 0:
                        fix_suggestions = self.auto_fix_analyzer.analyze_test_failures(
                            {"failed_tests": [{"test_id": tid, "error_message": "Test failed", "error_type": "AssertionError"} for tid in test_case_ids]},
                            spec
                        )
                        result["fix_suggestions"].extend(fix_suggestions)
                    
                    result["success"] = failed == 0 and passed > 0
                else:
                    self.logger.info("未提供测试运行器，模拟GREEN阶段")
                    passed, failed, skipped = 1, 0, 0
                    result["success"] = True
            
            intelligence = self._analyze_green_phase_intelligence(element, result)
            result["intelligence"] = intelligence
            
            self.state_tracker.complete_phase(
                CyclePhase.GREEN,
                passed=passed,
                failed=failed,
                skipped=skipped,
                metrics={
                    "implementation": "minimal",
                    "fix_suggestions_count": len(result["fix_suggestions"])
                }
            )
            
            self.logger.info(f"[GREEN 阶段 - 增强] 完成: {passed} 通过, {failed} 失败")
            
        except Exception as e:
            self.logger.error(f"[GREEN 阶段 - 增强] 失败: {e}")
            result["error"] = str(e)
            result["fix_suggestions"] = self._generate_error_fix_suggestions(str(e), element)
            self.state_tracker.complete_phase(
                CyclePhase.GREEN,
                error_message=str(e)
            )
        
        return result
    
    def _execute_blue_phase_enhanced(
        self,
        element: SpecElement,
        spec: ParsedSpecification,
        test_runner: Optional[callable],
        refactoring_handler: Optional[callable],
        dry_run: bool
    ) -> Dict[str, Any]:
        """增强的BLUE阶段执行 - 包含重构质量评估"""
        self.logger.info(f"\n[BLUE 阶段 - 增强] 重构代码: {element.name}")
        
        phase_record = self.state_tracker.start_phase(CyclePhase.BLUE)
        
        self._update_progress(CyclePhase.BLUE, 0, 0, "重构代码")
        
        result = {
            "success": False,
            "refactorings": [],
            "error": None,
            "intelligence": None,
            "fix_suggestions": [],
            "refactoring_quality": None
        }
        
        try:
            if dry_run:
                self.logger.info("[DRY RUN] 跳过重构")
                passed, failed, skipped = 1, 0, 0
                result["success"] = True
                refactorings = []
            else:
                refactorings = []
                
                if refactoring_handler:
                    refactor_result = refactoring_handler(element, spec)
                    refactorings = refactor_result.get("refactorings", [])
                    self.logger.info(f"执行重构: {refactorings}")
                
                if test_runner:
                    iteration = self.state_tracker.current_iteration
                    test_case_ids = iteration.red_phase.test_cases
                    
                    test_results = test_runner(test_case_ids)
                    passed = test_results.get("passed", 0)
                    failed = test_results.get("failed", 0)
                    skipped = test_results.get("skipped", 0)
                    
                    if failed > 0:
                        self.logger.warning("[BLUE 阶段] 重构后测试失败，建议回滚")
                        result["fix_suggestions"].append({
                            "type": "rollback_suggestion",
                            "message": "重构导致测试失败，建议回滚到上一个稳定版本"
                        })
                    
                    result["success"] = failed == 0 and passed > 0
                else:
                    self.logger.info("未提供测试运行器，模拟BLUE阶段")
                    passed, failed, skipped = 1, 0, 0
                    result["success"] = True
            
            result["refactorings"] = refactorings
            
            intelligence = self._analyze_blue_phase_intelligence(element, refactorings)
            result["intelligence"] = intelligence
            
            self.state_tracker.complete_phase(
                CyclePhase.BLUE,
                passed=passed,
                failed=failed,
                skipped=skipped,
                metrics={
                    "refactorings": refactorings,
                    "refactoring_count": len(refactorings)
                }
            )
            
            self.logger.info(f"[BLUE 阶段 - 增强] 完成: 重构 {len(refactorings)} 项")
            
        except Exception as e:
            self.logger.error(f"[BLUE 阶段 - 增强] 失败: {e}")
            result["error"] = str(e)
            result["fix_suggestions"] = self._generate_error_fix_suggestions(str(e), element)
            self.state_tracker.complete_phase(
                CyclePhase.BLUE,
                error_message=str(e)
            )
        
        return result
    
    def _analyze_red_phase_intelligence(
        self,
        element: SpecElement,
        test_cases: List[GeneratedTestCase]
    ) -> CycleIntelligence:
        """分析RED阶段的智能信息"""
        findings = []
        patterns_detected = []
        risk_factors = []
        optimization_suggestions = []
        predicted_issues = []
        
        test_types = [tc.test_type for tc in test_cases]
        type_counts = {}
        for tt in test_types:
            type_counts[tt.value] = type_counts.get(tt.value, 0) + 1
        
        if type_counts.get("unit", 0) < 2:
            findings.append({
                "type": "insufficient_unit_tests",
                "message": "单元测试数量不足",
                "severity": "medium"
            })
            optimization_suggestions.append("建议增加更多单元测试覆盖不同场景")
        
        if TestType.BOUNDARY not in test_types:
            findings.append({
                "type": "missing_boundary_tests",
                "message": "缺少边界条件测试",
                "severity": "medium"
            })
            optimization_suggestions.append("建议添加边界条件测试")
        
        if TestType.NEGATIVE not in test_types:
            findings.append({
                "type": "missing_negative_tests",
                "message": "缺少负面测试",
                "severity": "high"
            })
            risk_factors.append("未测试异常和错误情况")
        
        if element.element_type == SpecElementType.INTERFACE:
            if element.metadata.get("exceptions") and TestType.NEGATIVE not in test_types:
                predicted_issues.append({
                    "type": "unhandled_exception",
                    "probability": 0.8,
                    "description": "接口可能抛出未处理的异常"
                })
        
        patterns_detected.append("standard_tdd_pattern")
        
        return CycleIntelligence(
            iteration_id=element.name,
            phase=CyclePhase.RED,
            analysis_type="test_design_analysis",
            findings=findings,
            patterns_detected=patterns_detected,
            risk_factors=risk_factors,
            optimization_suggestions=optimization_suggestions,
            predicted_issues=predicted_issues
        )
    
    def _analyze_green_phase_intelligence(
        self,
        element: SpecElement,
        result: Dict[str, Any]
    ) -> CycleIntelligence:
        """分析GREEN阶段的智能信息"""
        findings = []
        patterns_detected = []
        risk_factors = []
        optimization_suggestions = []
        predicted_issues = []
        
        if result.get("fix_suggestions"):
            findings.append({
                "type": "code_smells_detected",
                "count": len(result["fix_suggestions"]),
                "severity": "medium"
            })
        
        if not result.get("success"):
            risk_factors.append("实现未能通过所有测试")
            optimization_suggestions.append("检查实现逻辑是否正确")
        
        patterns_detected.append("minimal_implementation")
        
        return CycleIntelligence(
            iteration_id=element.name,
            phase=CyclePhase.GREEN,
            analysis_type="implementation_analysis",
            findings=findings,
            patterns_detected=patterns_detected,
            risk_factors=risk_factors,
            optimization_suggestions=optimization_suggestions,
            predicted_issues=predicted_issues
        )
    
    def _analyze_blue_phase_intelligence(
        self,
        element: SpecElement,
        refactorings: List[str]
    ) -> CycleIntelligence:
        """分析BLUE阶段的智能信息"""
        findings = []
        patterns_detected = []
        risk_factors = []
        optimization_suggestions = []
        predicted_issues = []
        
        if len(refactorings) > 5:
            findings.append({
                "type": "excessive_refactoring",
                "count": len(refactorings),
                "severity": "low"
            })
            optimization_suggestions.append("考虑分多次提交重构")
        
        patterns_detected.append("incremental_refactoring")
        
        return CycleIntelligence(
            iteration_id=element.name,
            phase=CyclePhase.BLUE,
            analysis_type="refactoring_analysis",
            findings=findings,
            patterns_detected=patterns_detected,
            risk_factors=risk_factors,
            optimization_suggestions=optimization_suggestions,
            predicted_issues=predicted_issues
        )
    
    def _log_intelligence_findings(self, intelligence: CycleIntelligence) -> None:
        """记录智能分析发现"""
        if intelligence.findings:
            self.logger.info(f"  智能分析发现 {len(intelligence.findings)} 个问题:")
            for finding in intelligence.findings[:3]:
                self.logger.info(f"    - [{finding['severity']}] {finding['type']}: {finding.get('message', '')}")
        
        if intelligence.risk_factors:
            self.logger.warning(f"  风险因素: {', '.join(intelligence.risk_factors[:3])}")
        
        if intelligence.optimization_suggestions:
            self.logger.info(f"  优化建议: {intelligence.optimization_suggestions[0]}")
    
    def _suggest_red_phase_improvements(
        self,
        element: SpecElement,
        test_cases: List[GeneratedTestCase]
    ) -> List[Dict[str, Any]]:
        """为RED阶段提供改进建议"""
        suggestions = []
        
        suggestions.append({
            "type": "test_design_review",
            "message": "所有测试都通过了，可能测试设计存在问题",
            "suggestions": [
                "检查测试断言是否正确",
                "确保测试真正验证了预期行为",
                "考虑添加更多边界条件测试"
            ]
        })
        
        return suggestions
    
    def _generate_error_fix_suggestions(
        self,
        error_message: str,
        element: SpecElement
    ) -> List[Dict[str, Any]]:
        """根据错误生成修复建议"""
        suggestions = []
        
        if "import" in error_message.lower():
            suggestions.append({
                "type": "import_error",
                "message": "检测到导入错误",
                "fix": "检查模块是否已安装，或导入路径是否正确"
            })
        
        if "type" in error_message.lower():
            suggestions.append({
                "type": "type_error",
                "message": "检测到类型错误",
                "fix": "检查参数类型和返回值类型"
            })
        
        if "attribute" in error_message.lower():
            suggestions.append({
                "type": "attribute_error",
                "message": "检测到属性错误",
                "fix": "检查对象是否具有所需的属性或方法"
            })
        
        suggestions.append({
            "type": "general",
            "message": "一般性错误",
            "fix": "请查看详细错误日志进行修复"
        })
        
        return suggestions
    
    def _update_progress(
        self,
        phase: CyclePhase,
        iteration: int,
        total: int,
        activity: str
    ) -> None:
        """更新实时进度"""
        progress = RealtimeProgress(
            current_phase=phase,
            current_iteration=iteration,
            total_iterations=total,
            current_activity=activity,
            health_status="healthy"
        )
        
        self.progress_history.append(progress)
    
    def _create_checkpoint(
        self,
        iteration_index: int,
        phase: CyclePhase,
        state_data: Dict[str, Any]
    ) -> CheckpointData:
        """创建检查点"""
        checkpoint = CheckpointData(
            checkpoint_id=f"CP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{iteration_index}",
            timestamp=datetime.now().isoformat(),
            iteration_index=iteration_index,
            phase=phase,
            state_data=state_data,
            recovery_info={
                "can_recover": True,
                "recovery_point": iteration_index
            }
        )
        
        self.checkpoints.append(checkpoint)
        self._save_checkpoint(checkpoint)
        
        return checkpoint
    
    def _save_checkpoint(self, checkpoint: CheckpointData) -> None:
        """保存检查点到文件"""
        checkpoint_dir = self.output_dir / "checkpoints"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        checkpoint_file = checkpoint_dir / f"{checkpoint.checkpoint_id}.json"
        
        checkpoint_dict = {
            "checkpoint_id": checkpoint.checkpoint_id,
            "timestamp": checkpoint.timestamp,
            "iteration_index": checkpoint.iteration_index,
            "phase": checkpoint.phase.value,
            "state_data": checkpoint.state_data,
            "recovery_info": checkpoint.recovery_info
        }
        
        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(checkpoint_dict, f, ensure_ascii=False, indent=2)
    
    def _enhance_report_with_intelligence(self, report: CycleExecutionReport) -> None:
        """用智能分析结果增强报告"""
        intelligence_summary = {
            "total_findings": 0,
            "total_risk_factors": 0,
            "total_suggestions": 0,
            "phase_breakdown": {
                "red": {"findings": 0, "risks": 0},
                "green": {"findings": 0, "risks": 0},
                "blue": {"findings": 0, "risks": 0}
            }
        }
        
        for key, intelligence in self.intelligence_cache.items():
            intelligence_summary["total_findings"] += len(intelligence.findings)
            intelligence_summary["total_risk_factors"] += len(intelligence.risk_factors)
            intelligence_summary["total_suggestions"] += len(intelligence.optimization_suggestions)
            
            phase = intelligence.phase.value
            if phase in intelligence_summary["phase_breakdown"]:
                intelligence_summary["phase_breakdown"][phase]["findings"] += len(intelligence.findings)
                intelligence_summary["phase_breakdown"][phase]["risks"] += len(intelligence.risk_factors)
        
        report.metrics["intelligence"] = intelligence_summary
        
        if intelligence_summary["total_risk_factors"] > 0:
            report.recommendations.append(
                f"检测到 {intelligence_summary['total_risk_factors']} 个风险因素，建议详细审查"
            )
    
    def _validate_basic_fields(
        self,
        spec: ParsedSpecification,
        result: ValidationResult
    ) -> None:
        if not spec.spec_id:
            result.errors.append({
                "path": "id",
                "message": "缺少规范ID",
                "severity": ValidationSeverity.ERROR.value
            })
            result.is_valid = False
        
        if not spec.spec_name:
            result.errors.append({
                "path": "name",
                "message": "缺少规范名称",
                "severity": ValidationSeverity.ERROR.value
            })
            result.is_valid = False
        
        if not spec.version:
            result.warnings.append({
                "path": "version",
                "message": "缺少版本号，默认为v1.0",
                "severity": ValidationSeverity.WARNING.value
            })
        
        if not spec.interfaces and not spec.data_models and not spec.behavior_rules:
            result.errors.append({
                "path": "content",
                "message": "规范内容为空，缺少接口定义、数据模型或行为规则",
                "severity": ValidationSeverity.ERROR.value
            })
            result.is_valid = False
    
    def _validate_interfaces(
        self,
        spec: ParsedSpecification,
        result: ValidationResult
    ) -> None:
        for idx, iface in enumerate(spec.interfaces):
            path = f"interfaces[{idx}]"
            
            if not iface.name:
                result.errors.append({
                    "path": f"{path}.name",
                    "message": f"接口 {idx} 缺少名称",
                    "severity": ValidationSeverity.ERROR.value
                })
                result.is_valid = False
            
            if not iface.parameters and not iface.methods:
                result.warnings.append({
                    "path": path,
                    "message": f"接口 {iface.name} 缺少参数定义",
                    "severity": ValidationSeverity.WARNING.value
                })
            
            for param in iface.parameters:
                if not param.get("name"):
                    result.errors.append({
                        "path": f"{path}.parameters",
                        "message": f"接口 {iface.name} 存在未命名的参数",
                        "severity": ValidationSeverity.ERROR.value
                    })
                    result.is_valid = False
    
    def _validate_data_models(
        self,
        spec: ParsedSpecification,
        result: ValidationResult
    ) -> None:
        for idx, model in enumerate(spec.data_models):
            path = f"data_models[{idx}]"
            
            if not model.name:
                result.errors.append({
                    "path": f"{path}.name",
                    "message": f"数据模型 {idx} 缺少名称",
                    "severity": ValidationSeverity.ERROR.value
                })
                result.is_valid = False
            
            if not model.attributes:
                result.warnings.append({
                    "path": path,
                    "message": f"数据模型 {model.name} 缺少属性定义",
                    "severity": ValidationSeverity.WARNING.value
                })
            
            for attr in model.attributes:
                if not attr.get("name"):
                    result.errors.append({
                        "path": f"{path}.attributes",
                        "message": f"数据模型 {model.name} 存在未命名的属性",
                        "severity": ValidationSeverity.ERROR.value
                    })
                    result.is_valid = False
    
    def _validate_behavior_rules(
        self,
        spec: ParsedSpecification,
        result: ValidationResult
    ) -> None:
        for idx, rule in enumerate(spec.behavior_rules):
            path = f"behavior_rules[{idx}]"
            
            if not rule.rule_id:
                result.warnings.append({
                    "path": f"{path}.rule_id",
                    "message": f"行为规则 {rule.name} 缺少规则ID",
                    "severity": ValidationSeverity.WARNING.value
                })
            
            if not rule.condition:
                result.warnings.append({
                    "path": f"{path}.condition",
                    "message": f"行为规则 {rule.name} 缺少条件定义",
                    "severity": ValidationSeverity.WARNING.value
                })
            
            if not rule.action:
                result.warnings.append({
                    "path": f"{path}.action",
                    "message": f"行为规则 {rule.name} 缺少动作定义",
                    "severity": ValidationSeverity.WARNING.value
                })
    
    def _validate_consistency(
        self,
        spec: ParsedSpecification,
        result: ValidationResult
    ) -> None:
        interface_names = [iface.name for iface in spec.interfaces]
        model_names = [model.name for model in spec.data_models]
        
        duplicates = set()
        seen = set()
        for name in interface_names + model_names:
            if name in seen:
                duplicates.add(name)
            seen.add(name)
        
        if duplicates:
            result.warnings.append({
                "path": "consistency",
                "message": f"存在重复的名称: {', '.join(duplicates)}",
                "severity": ValidationSeverity.WARNING.value
            })
        
        for rule in spec.behavior_rules:
            if rule.condition and not rule.action:
                result.warnings.append({
                    "path": f"behavior_rules.{rule.rule_id}",
                    "message": f"行为规则 {rule.name} 有条件但缺少动作",
                    "severity": ValidationSeverity.WARNING.value
                })
    
    def _calculate_completeness(
        self,
        spec: ParsedSpecification,
        result: ValidationResult
    ) -> float:
        scores = []
        
        if spec.spec_id:
            scores.append(100)
        else:
            scores.append(0)
        
        if spec.spec_name:
            scores.append(100)
        else:
            scores.append(0)
        
        if spec.version:
            scores.append(100)
        else:
            scores.append(50)
        
        if spec.interfaces:
            interface_score = sum(
                100 if iface.name and iface.parameters else 50
                for iface in spec.interfaces
            ) / len(spec.interfaces)
            scores.append(interface_score)
        
        if spec.data_models:
            model_score = sum(
                100 if model.name and model.attributes else 50
                for model in spec.data_models
            ) / len(spec.data_models)
            scores.append(model_score)
        
        if spec.behavior_rules:
            rule_score = sum(
                100 if rule.condition and rule.action else 50
                for rule in spec.behavior_rules
            ) / len(spec.behavior_rules)
            scores.append(rule_score)
        
        error_penalty = len(result.errors) * 10
        warning_penalty = len(result.warnings) * 5
        
        base_score = sum(scores) / len(scores) if scores else 0
        final_score = max(0, base_score - error_penalty - warning_penalty)
        
        return min(100, final_score)


class SddTddIntegrationEnhancer:
    """SDD与TDD集成增强器 - 提供智能映射、追溯和验证功能"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self.mapping_cache: Dict[str, SpecTestMapping] = {}
        self.validation_history: List[IntegrationValidation] = []
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("SddTddIntegrationEnhancer")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def create_intelligent_mapping(
        self,
        spec: ParsedSpecification,
        test_cases: List[GeneratedTestCase]
    ) -> List[SpecTestMapping]:
        """创建规范到测试的智能映射"""
        mappings = []
        
        for element in spec.elements:
            mapping = self._create_element_mapping(element, test_cases, spec)
            mappings.append(mapping)
            self.mapping_cache[element.name] = mapping
        
        self._analyze_mapping_relationships(mappings)
        
        self.logger.info(f"创建了 {len(mappings)} 个规范-测试映射")
        return mappings
    
    def _create_element_mapping(
        self,
        element: SpecElement,
        test_cases: List[GeneratedTestCase],
        spec: ParsedSpecification
    ) -> SpecTestMapping:
        """为单个规范元素创建映射"""
        related_tests = [
            tc for tc in test_cases
            if tc.spec_element_name == element.name or
               self._semantic_match(tc.name, element.name)
        ]
        
        test_ids = [tc.test_id for tc in related_tests]
        
        semantic_similarity = self._calculate_semantic_similarity(element, related_tests)
        structural_match = self._check_structural_match(element, related_tests)
        behavior_coverage = self._calculate_behavior_coverage(element, related_tests)
        
        mapping_confidence = self._calculate_mapping_confidence(
            semantic_similarity, structural_match, behavior_coverage, len(related_tests)
        )
        
        integration_status = self._determine_integration_status(
            mapping_confidence, behavior_coverage
        )
        
        trace_links = self._create_trace_links(element, related_tests)
        
        return SpecTestMapping(
            spec_element_id=element.name,
            spec_element_name=element.name,
            test_case_ids=test_ids,
            mapping_confidence=mapping_confidence,
            mapping_type="intelligent" if mapping_confidence > 0.8 else "basic",
            semantic_similarity=semantic_similarity,
            structural_match=structural_match,
            behavior_coverage=behavior_coverage,
            integration_status=integration_status,
            trace_links=trace_links
        )
    
    def _semantic_match(self, test_name: str, element_name: str) -> bool:
        """语义匹配检查"""
        test_words = set(re.findall(r'\w+', test_name.lower()))
        element_words = set(re.findall(r'\w+', element_name.lower()))
        
        common_words = test_words & element_words
        
        if len(common_words) >= min(len(test_words), len(element_words)) * 0.5:
            return True
        
        return False
    
    def _calculate_semantic_similarity(
        self,
        element: SpecElement,
        test_cases: List[GeneratedTestCase]
    ) -> float:
        """计算语义相似度"""
        if not test_cases:
            return 0.0
        
        element_desc = f"{element.name} {element.description}".lower()
        element_words = set(re.findall(r'\w+', element_desc))
        
        similarities = []
        for tc in test_cases:
            test_desc = f"{tc.name} {tc.description}".lower()
            test_words = set(re.findall(r'\w+', test_desc))
            
            if element_words and test_words:
                intersection = len(element_words & test_words)
                union = len(element_words | test_words)
                similarity = intersection / union if union > 0 else 0
                similarities.append(similarity)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _check_structural_match(
        self,
        element: SpecElement,
        test_cases: List[GeneratedTestCase]
    ) -> bool:
        """检查结构匹配"""
        if not test_cases:
            return False
        
        element_attrs = {attr.get("name", "") for attr in element.attributes}
        
        for tc in test_cases:
            test_content = f"{tc.arrange} {tc.act} {tc.assert_}"
            matched_attrs = sum(1 for attr in element_attrs if attr.lower() in test_content.lower())
            
            if matched_attrs >= len(element_attrs) * 0.5:
                return True
        
        return False
    
    def _calculate_behavior_coverage(
        self,
        element: SpecElement,
        test_cases: List[GeneratedTestCase]
    ) -> float:
        """计算行为覆盖率"""
        if not test_cases:
            return 0.0
        
        expected_behaviors = self._extract_expected_behaviors(element)
        
        if not expected_behaviors:
            return 1.0 if test_cases else 0.0
        
        covered_behaviors = set()
        
        for tc in test_cases:
            test_content = f"{tc.act} {tc.assert_}".lower()
            for behavior in expected_behaviors:
                if behavior.lower() in test_content:
                    covered_behaviors.add(behavior)
        
        coverage = len(covered_behaviors) / len(expected_behaviors)
        return coverage
    
    def _extract_expected_behaviors(self, element: SpecElement) -> List[str]:
        """提取预期行为"""
        behaviors = []
        
        if element.element_type == SpecElementType.INTERFACE:
            behaviors.append("调用")
            behaviors.append("返回")
            if element.metadata.get("exceptions"):
                behaviors.append("异常")
        
        elif element.element_type == SpecElementType.DATA_MODEL:
            for attr in element.attributes:
                behaviors.append(attr.get("name", ""))
            behaviors.append("创建")
            behaviors.append("验证")
        
        elif element.element_type == SpecElementType.BEHAVIOR_RULE:
            if element.constraints.get("condition"):
                behaviors.append("条件")
            if element.constraints.get("action"):
                behaviors.append("动作")
        
        return behaviors
    
    def _calculate_mapping_confidence(
        self,
        semantic_similarity: float,
        structural_match: bool,
        behavior_coverage: float,
        test_count: int
    ) -> float:
        """计算映射置信度"""
        base_score = semantic_similarity * 0.3 + behavior_coverage * 0.4
        
        if structural_match:
            base_score += 0.2
        
        count_factor = min(1.0, test_count / 3.0) * 0.1
        base_score += count_factor
        
        return min(1.0, base_score)
    
    def _determine_integration_status(
        self,
        mapping_confidence: float,
        behavior_coverage: float
    ) -> IntegrationStatus:
        """确定集成状态"""
        if mapping_confidence >= 0.8 and behavior_coverage >= 0.8:
            return IntegrationStatus.ALIGNED
        elif mapping_confidence >= 0.5 and behavior_coverage >= 0.5:
            return IntegrationStatus.PARTIALLY_ALIGNED
        elif mapping_confidence > 0 or behavior_coverage > 0:
            return IntegrationStatus.MISALIGNED
        else:
            return IntegrationStatus.UNKNOWN
    
    def _create_trace_links(
        self,
        element: SpecElement,
        test_cases: List[GeneratedTestCase]
    ) -> List[Dict[str, Any]]:
        """创建追溯链接"""
        links = []
        
        for tc in test_cases:
            link = {
                "spec_element": element.name,
                "test_case": tc.test_id,
                "test_type": tc.test_type.value,
                "link_type": "primary" if tc.spec_element_name == element.name else "secondary",
                "created_at": datetime.now().isoformat()
            }
            links.append(link)
        
        return links
    
    def _analyze_mapping_relationships(self, mappings: List[SpecTestMapping]) -> None:
        """分析映射关系"""
        for mapping in mappings:
            if mapping.integration_status == IntegrationStatus.MISALIGNED:
                self.logger.warning(
                    f"规范元素 '{mapping.spec_element_name}' 与测试对齐不足"
                )
    
    def validate_integration(
        self,
        spec: ParsedSpecification,
        test_cases: List[GeneratedTestCase]
    ) -> List[IntegrationValidation]:
        """验证集成一致性"""
        validations = []
        
        for element in spec.elements:
            related_tests = [
                tc for tc in test_cases
                if tc.spec_element_name == element.name
            ]
            
            for tc in related_tests:
                validation = self._validate_single_integration(element, tc)
                validations.append(validation)
                self.validation_history.append(validation)
        
        self.logger.info(f"完成了 {len(validations)} 个集成验证")
        return validations
    
    def _validate_single_integration(
        self,
        element: SpecElement,
        test_case: GeneratedTestCase
    ) -> IntegrationValidation:
        """验证单个集成"""
        gaps = []
        suggestions = []
        
        alignment_score = self._calculate_alignment_score(element, test_case, gaps, suggestions)
        
        is_valid = alignment_score >= 0.7 and len(gaps) == 0
        
        validation_details = {
            "element_type": element.element_type.name,
            "test_type": test_case.test_type.value,
            "checked_at": datetime.now().isoformat()
        }
        
        return IntegrationValidation(
            is_valid=is_valid,
            spec_element_id=element.name,
            test_case_id=test_case.test_id,
            alignment_score=alignment_score,
            gaps=gaps,
            suggestions=suggestions,
            validation_details=validation_details
        )
    
    def _calculate_alignment_score(
        self,
        element: SpecElement,
        test_case: GeneratedTestCase,
        gaps: List[Dict[str, Any]],
        suggestions: List[str]
    ) -> float:
        """计算对齐分数"""
        score = 1.0
        
        if element.element_type == SpecElementType.INTERFACE:
            if element.attributes:
                for param in element.attributes:
                    param_name = param.get("name", "")
                    if param_name and param_name.lower() not in test_case.arrange.lower():
                        gaps.append({
                            "type": "missing_parameter_test",
                            "parameter": param_name,
                            "severity": "medium"
                        })
                        suggestions.append(f"建议在测试中添加参数 '{param_name}' 的验证")
                        score -= 0.1
        
        elif element.element_type == SpecElementType.DATA_MODEL:
            for attr in element.attributes:
                attr_name = attr.get("name", "")
                if attr_name and attr_name.lower() not in test_case.arrange.lower():
                    gaps.append({
                        "type": "missing_attribute_test",
                        "attribute": attr_name,
                        "severity": "low"
                    })
                    suggestions.append(f"建议测试属性 '{attr_name}'")
                    score -= 0.05
        
        elif element.element_type == SpecElementType.BEHAVIOR_RULE:
            condition = element.constraints.get("condition", "")
            action = element.constraints.get("action", "")
            
            if condition and condition.lower() not in test_case.arrange.lower():
                gaps.append({
                    "type": "missing_condition_test",
                    "condition": condition,
                    "severity": "high"
                })
                suggestions.append("建议测试规则条件")
                score -= 0.15
            
            if action and action.lower() not in test_case.assert_.lower():
                gaps.append({
                    "type": "missing_action_verification",
                    "action": action,
                    "severity": "high"
                })
                suggestions.append("建议验证规则动作")
                score -= 0.15
        
        return max(0.0, score)
    
    def generate_traceability_matrix(
        self,
        spec: ParsedSpecification,
        test_cases: List[GeneratedTestCase]
    ) -> Dict[str, Any]:
        """生成追溯矩阵"""
        matrix = {
            "spec_to_tests": {},
            "test_to_spec": {},
            "coverage_summary": {},
            "traceability_score": 0.0
        }
        
        for element in spec.elements:
            related_tests = [
                tc.test_id for tc in test_cases
                if tc.spec_element_name == element.name
            ]
            matrix["spec_to_tests"][element.name] = related_tests
        
        for tc in test_cases:
            matrix["test_to_spec"][tc.test_id] = tc.spec_element_name
        
        total_elements = len(spec.elements)
        covered_elements = sum(
            1 for tests in matrix["spec_to_tests"].values() if tests
        )
        
        matrix["coverage_summary"] = {
            "total_elements": total_elements,
            "covered_elements": covered_elements,
            "coverage_percentage": covered_elements / total_elements * 100 if total_elements > 0 else 0
        }
        
        matrix["traceability_score"] = matrix["coverage_summary"]["coverage_percentage"]
        
        return matrix
    
    def detect_integration_drift(
        self,
        spec: ParsedSpecification,
        test_cases: List[GeneratedTestCase]
    ) -> List[Dict[str, Any]]:
        """检测集成漂移"""
        drifts = []
        
        for element in spec.elements:
            mapping = self.mapping_cache.get(element.name)
            
            if mapping:
                current_tests = [
                    tc for tc in test_cases
                    if tc.spec_element_name == element.name
                ]
                
                if len(current_tests) != len(mapping.test_case_ids):
                    drifts.append({
                        "type": "test_count_change",
                        "element": element.name,
                        "previous_count": len(mapping.test_case_ids),
                        "current_count": len(current_tests),
                        "severity": "medium"
                    })
        
        return drifts


class DependencyAnalyzer:
    """依赖分析器 - 分析规范元素之间的依赖关系"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self.dependency_graph: Dict[str, DependencyInfo] = {}
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("DependencyAnalyzer")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def analyze_dependencies(
        self,
        spec: ParsedSpecification
    ) -> List[DependencyInfo]:
        """分析规范元素的依赖关系"""
        dependencies = []
        
        for element in spec.elements:
            dep_info = self._analyze_element_dependencies(element, spec)
            dependencies.append(dep_info)
            self.dependency_graph[element.name] = dep_info
        
        self._detect_circular_dependencies(dependencies)
        self._calculate_resolution_order(dependencies)
        
        self.logger.info(f"分析了 {len(dependencies)} 个元素的依赖关系")
        return dependencies
    
    def _analyze_element_dependencies(
        self,
        element: SpecElement,
        spec: ParsedSpecification
    ) -> DependencyInfo:
        """分析单个元素的依赖"""
        depends_on = []
        
        if element.element_type == SpecElementType.INTERFACE:
            for param in element.attributes:
                param_type = param.get("type", "")
                for model in spec.data_models:
                    if model.name.lower() in param_type.lower():
                        depends_on.append(model.name)
        
        elif element.element_type == SpecElementType.DATA_MODEL:
            for attr in element.attributes:
                attr_type = attr.get("type", "")
                for model in spec.data_models:
                    if model.name != element.name and model.name.lower() in attr_type.lower():
                        depends_on.append(model.name)
        
        elif element.element_type == SpecElementType.BEHAVIOR_RULE:
            condition = element.constraints.get("condition", "")
            action = element.constraints.get("action", "")
            
            for iface in spec.interfaces:
                if iface.name.lower() in condition.lower() or iface.name.lower() in action.lower():
                    depends_on.append(iface.name)
            
            for model in spec.data_models:
                if model.name.lower() in condition.lower() or model.name.lower() in action.lower():
                    depends_on.append(model.name)
        
        depended_by = []
        for other in spec.elements:
            if other.name != element.name:
                other_deps = self._extract_dependencies(other, spec)
                if element.name in other_deps:
                    depended_by.append(other.name)
        
        return DependencyInfo(
            element_id=element.name,
            element_name=element.name,
            depends_on=list(set(depends_on)),
            depended_by=list(set(depended_by))
        )
    
    def _extract_dependencies(
        self,
        element: SpecElement,
        spec: ParsedSpecification
    ) -> List[str]:
        """提取元素的依赖"""
        deps = []
        
        for attr in element.attributes:
            attr_type = attr.get("type", "")
            for model in spec.data_models:
                if model.name.lower() in attr_type.lower():
                    deps.append(model.name)
        
        return deps
    
    def _detect_circular_dependencies(self, dependencies: List[DependencyInfo]) -> None:
        """检测循环依赖"""
        for dep in dependencies:
            visited = set()
            if self._has_circular(dep.element_id, visited, dependencies):
                dep.is_circular = True
                self.logger.warning(f"检测到循环依赖: {dep.element_id}")
    
    def _has_circular(
        self,
        element_id: str,
        visited: set,
        dependencies: List[DependencyInfo]
    ) -> bool:
        """递归检测循环"""
        if element_id in visited:
            return True
        
        visited.add(element_id)
        
        dep_info = next((d for d in dependencies if d.element_id == element_id), None)
        if dep_info:
            for dep_id in dep_info.depends_on:
                if self._has_circular(dep_id, visited.copy(), dependencies):
                    return True
        
        return False
    
    def _calculate_resolution_order(self, dependencies: List[DependencyInfo]) -> None:
        """计算解决顺序"""
        resolved = set()
        order = 0
        
        while len(resolved) < len(dependencies):
            for dep in dependencies:
                if dep.element_id not in resolved:
                    unresolved_deps = [d for d in dep.depends_on if d not in resolved]
                    
                    if not unresolved_deps:
                        dep.resolution_order = order
                        resolved.add(dep.element_id)
            
            order += 1
            
            if order > len(dependencies) * 2:
                break
        
        for dep in dependencies:
            if dep.resolution_order == 0 and dep.element_id not in resolved:
                dep.resolution_order = order
    
    def get_execution_order(self) -> List[str]:
        """获取执行顺序"""
        sorted_deps = sorted(
            self.dependency_graph.values(),
            key=lambda d: d.resolution_order
        )
        return [d.element_id for d in sorted_deps]
    
    def get_dependency_level(self, element_id: str) -> int:
        """获取依赖层级"""
        dep_info = self.dependency_graph.get(element_id)
        return dep_info.dependency_level if dep_info else 0


class AutoFixAnalyzer:
    """自动修复分析器 - 分析并提供自动修复建议"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self.fix_history: List[AutoFixSuggestion] = []
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("AutoFixAnalyzer")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def analyze_test_failures(
        self,
        test_results: Dict[str, Any],
        spec: ParsedSpecification
    ) -> List[AutoFixSuggestion]:
        """分析测试失败并生成修复建议"""
        suggestions = []
        
        failed_tests = test_results.get("failed_tests", [])
        
        for failed_test in failed_tests:
            test_id = failed_test.get("test_id", "")
            error_message = failed_test.get("error_message", "")
            error_type = failed_test.get("error_type", "")
            
            fix_suggestion = self._analyze_single_failure(
                test_id, error_message, error_type, spec
            )
            
            if fix_suggestion:
                suggestions.append(fix_suggestion)
                self.fix_history.append(fix_suggestion)
        
        self.logger.info(f"生成了 {len(suggestions)} 个修复建议")
        return suggestions
    
    def _analyze_single_failure(
        self,
        test_id: str,
        error_message: str,
        error_type: str,
        spec: ParsedSpecification
    ) -> Optional[AutoFixSuggestion]:
        """分析单个测试失败"""
        fix_id = f"FIX-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hashlib.md5(test_id.encode()).hexdigest()[:8]}"
        
        if "ImportError" in error_type or "ModuleNotFoundError" in error_type:
            return self._create_import_fix(fix_id, test_id, error_message)
        
        elif "TypeError" in error_type:
            return self._create_type_fix(fix_id, test_id, error_message, spec)
        
        elif "AssertionError" in error_type:
            return self._create_logic_fix(fix_id, test_id, error_message, spec)
        
        elif "SyntaxError" in error_type:
            return self._create_syntax_fix(fix_id, test_id, error_message)
        
        else:
            return self._create_generic_fix(fix_id, test_id, error_message)
    
    def _create_import_fix(
        self,
        fix_id: str,
        test_id: str,
        error_message: str
    ) -> AutoFixSuggestion:
        """创建导入修复建议"""
        import_match = re.search(r"No module named '(\w+)'", error_message)
        missing_module = import_match.group(1) if import_match else "unknown"
        
        return AutoFixSuggestion(
            fix_id=fix_id,
            category=AutoFixCategory.IMPORT_FIX,
            description=f"缺少模块导入: {missing_module}",
            target_location=f"test_file:{test_id}",
            suggested_fix=f"添加导入: import {missing_module}\n或安装模块: pip install {missing_module}",
            confidence=0.9,
            impact="high",
            auto_applicable=True,
            prerequisites=["检查模块是否已安装"]
        )
    
    def _create_type_fix(
        self,
        fix_id: str,
        test_id: str,
        error_message: str,
        spec: ParsedSpecification
    ) -> AutoFixSuggestion:
        """创建类型修复建议"""
        return AutoFixSuggestion(
            fix_id=fix_id,
            category=AutoFixCategory.TYPE_FIX,
            description="类型不匹配错误",
            target_location=f"test_file:{test_id}",
            suggested_fix="检查参数类型和返回值类型是否与规范定义一致",
            confidence=0.7,
            impact="medium",
            auto_applicable=False,
            prerequisites=["检查规范中的类型定义"]
        )
    
    def _create_logic_fix(
        self,
        fix_id: str,
        test_id: str,
        error_message: str,
        spec: ParsedSpecification
    ) -> AutoFixSuggestion:
        """创建逻辑修复建议"""
        return AutoFixSuggestion(
            fix_id=fix_id,
            category=AutoFixCategory.LOGIC_FIX,
            description="断言失败 - 实际结果与预期不符",
            target_location=f"test_file:{test_id}",
            suggested_fix="1. 检查测试预期是否正确\n2. 检查实现逻辑是否符合规范\n3. 检查边界条件处理",
            confidence=0.6,
            impact="high",
            auto_applicable=False,
            prerequisites=["分析错误详情", "对比规范要求"]
        )
    
    def _create_syntax_fix(
        self,
        fix_id: str,
        test_id: str,
        error_message: str
    ) -> AutoFixSuggestion:
        """创建语法修复建议"""
        return AutoFixSuggestion(
            fix_id=fix_id,
            category=AutoFixCategory.SYNTAX_FIX,
            description="语法错误",
            target_location=f"test_file:{test_id}",
            suggested_fix="修复语法错误，检查括号、缩进、引号等",
            confidence=0.95,
            impact="high",
            auto_applicable=True,
            prerequisites=[]
        )
    
    def _create_generic_fix(
        self,
        fix_id: str,
        test_id: str,
        error_message: str
    ) -> AutoFixSuggestion:
        """创建通用修复建议"""
        return AutoFixSuggestion(
            fix_id=fix_id,
            category=AutoFixCategory.REFACTOR_SUGGESTION,
            description=f"测试失败: {error_message[:100]}",
            target_location=f"test_file:{test_id}",
            suggested_fix="请手动检查错误详情并进行修复",
            confidence=0.3,
            impact="medium",
            auto_applicable=False,
            prerequisites=["详细分析错误日志"]
        )
    
    def analyze_code_smells(
        self,
        code_content: str,
        spec: ParsedSpecification
    ) -> List[AutoFixSuggestion]:
        """分析代码异味并生成重构建议"""
        suggestions = []
        
        if self._detect_long_method(code_content):
            suggestions.append(AutoFixSuggestion(
                fix_id=f"FIX-SMELL-{datetime.now().strftime('%Y%m%d%H%M%S')}-001",
                category=AutoFixCategory.REFACTOR_SUGGESTION,
                description="检测到过长的方法",
                target_location="code",
                suggested_fix="考虑将方法拆分为更小的、职责单一的方法",
                confidence=0.7,
                impact="medium",
                auto_applicable=False
            ))
        
        if self._detect_code_duplication(code_content):
            suggestions.append(AutoFixSuggestion(
                fix_id=f"FIX-SMELL-{datetime.now().strftime('%Y%m%d%H%M%S')}-002",
                category=AutoFixCategory.REFACTOR_SUGGESTION,
                description="检测到代码重复",
                target_location="code",
                suggested_fix="考虑提取公共代码到独立的方法或类中",
                confidence=0.8,
                impact="medium",
                auto_applicable=False
            ))
        
        if self._detect_deep_nesting(code_content):
            suggestions.append(AutoFixSuggestion(
                fix_id=f"FIX-SMELL-{datetime.now().strftime('%Y%m%d%H%M%S')}-003",
                category=AutoFixCategory.REFACTOR_SUGGESTION,
                description="检测到深层嵌套",
                target_location="code",
                suggested_fix="考虑使用提前返回、提取方法或策略模式来减少嵌套层级",
                confidence=0.75,
                impact="medium",
                auto_applicable=False
            ))
        
        return suggestions
    
    def _detect_long_method(self, code: str) -> bool:
        """检测过长方法"""
        lines = code.split('\n')
        method_lines = 0
        in_method = False
        
        for line in lines:
            if 'def ' in line:
                if method_lines > 30:
                    return True
                in_method = True
                method_lines = 0
            elif in_method:
                method_lines += 1
        
        return method_lines > 30
    
    def _detect_code_duplication(self, code: str) -> bool:
        """检测代码重复"""
        lines = [line.strip() for line in code.split('\n') if line.strip()]
        
        line_counts = {}
        for line in lines:
            line_counts[line] = line_counts.get(line, 0) + 1
        
        duplicated = sum(1 for count in line_counts.values() if count > 2)
        return duplicated > 3
    
    def _detect_deep_nesting(self, code: str) -> bool:
        """检测深层嵌套"""
        max_indent = 0
        for line in code.split('\n'):
            if line.strip():
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent)
        
        return max_indent > 16


class CycleStateTracker:
    """循环状态跟踪器 - 跟踪红绿蓝循环的执行状态"""
    
    def __init__(self, output_dir: Path, logger: Optional[logging.Logger] = None):
        self.output_dir = output_dir
        self.state_dir = output_dir / "cycle_states"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger or self._setup_logger()
        self.current_report: Optional[CycleExecutionReport] = None
        self.current_iteration: Optional[CycleIteration] = None
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("CycleStateTracker")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def initialize_report(self, spec: ParsedSpecification) -> CycleExecutionReport:
        report_id = f"CYCLE-{spec.spec_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self.current_report = CycleExecutionReport(
            report_id=report_id,
            spec_id=spec.spec_id,
            spec_name=spec.spec_name,
            started_at=datetime.now().isoformat(),
            total_iterations=len(spec.elements)
        )
        
        for idx, element in enumerate(spec.elements):
            iteration = CycleIteration(
                iteration_id=f"{report_id}-ITER-{idx+1:03d}",
                cycle_number=idx + 1,
                spec_element_id=element.name,
                spec_element_name=element.name
            )
            self.current_report.iterations.append(iteration)
        
        self._save_state()
        self.logger.info(f"初始化循环执行报告: {report_id}")
        
        return self.current_report
    
    def start_iteration(self, iteration_index: int) -> CycleIteration:
        if not self.current_report:
            raise RuntimeError("未初始化报告，请先调用 initialize_report")
        
        if iteration_index >= len(self.current_report.iterations):
            raise IndexError(f"迭代索引 {iteration_index} 超出范围")
        
        self.current_iteration = self.current_report.iterations[iteration_index]
        self.current_iteration.started_at = datetime.now().isoformat()
        self._save_state()
        
        self.logger.info(f"开始迭代 {self.current_iteration.cycle_number}: {self.current_iteration.spec_element_name}")
        
        return self.current_iteration
    
    def start_phase(self, phase: CyclePhase) -> CyclePhaseRecord:
        if not self.current_iteration:
            raise RuntimeError("未开始迭代，请先调用 start_iteration")
        
        phase_record = self._get_phase_record(phase)
        phase_record.status = CycleStatus.IN_PROGRESS
        phase_record.started_at = datetime.now().isoformat()
        self._save_state()
        
        self.logger.info(f"开始 {phase.value} 阶段")
        
        return phase_record
    
    def complete_phase(
        self,
        phase: CyclePhase,
        passed: int = 0,
        failed: int = 0,
        skipped: int = 0,
        test_cases: Optional[List[str]] = None,
        error_message: Optional[str] = None,
        artifacts: Optional[Dict[str, str]] = None,
        metrics: Optional[Dict[str, Any]] = None
    ) -> CyclePhaseRecord:
        if not self.current_iteration:
            raise RuntimeError("未开始迭代")
        
        phase_record = self._get_phase_record(phase)
        phase_record.status = CycleStatus.COMPLETED if failed == 0 else CycleStatus.FAILED
        phase_record.completed_at = datetime.now().isoformat()
        phase_record.passed_count = passed
        phase_record.failed_count = failed
        phase_record.skipped_count = skipped
        phase_record.test_cases = test_cases or []
        phase_record.error_message = error_message
        phase_record.artifacts = artifacts or {}
        phase_record.metrics = metrics or {}
        
        self._save_state()
        
        self.logger.info(
            f"完成 {phase.value} 阶段: 通过={passed}, 失败={failed}, 跳过={skipped}"
        )
        
        return phase_record
    
    def complete_iteration(self, result: CycleResult, notes: Optional[List[str]] = None) -> CycleIteration:
        if not self.current_iteration:
            raise RuntimeError("未开始迭代")
        
        self.current_iteration.completed_at = datetime.now().isoformat()
        self.current_iteration.overall_result = result
        if notes:
            self.current_iteration.notes.extend(notes)
        
        self.current_report.completed_iterations += 1
        if result == CycleResult.FAILURE:
            self.current_report.failed_iterations += 1
        
        self._save_state()
        
        self.logger.info(
            f"完成迭代 {self.current_iteration.cycle_number}: 结果={result.value}"
        )
        
        return self.current_iteration
    
    def complete_report(self) -> CycleExecutionReport:
        if not self.current_report:
            raise RuntimeError("未初始化报告")
        
        self.current_report.completed_at = datetime.now().isoformat()
        self.current_report.summary = self._generate_summary()
        self.current_report.recommendations = self._generate_recommendations()
        self.current_report.metrics = self._calculate_metrics()
        
        self._save_state()
        self._save_final_report()
        
        self.logger.info(f"完成循环执行报告: {self.current_report.report_id}")
        
        return self.current_report
    
    def _get_phase_record(self, phase: CyclePhase) -> CyclePhaseRecord:
        if phase == CyclePhase.RED:
            return self.current_iteration.red_phase
        elif phase == CyclePhase.GREEN:
            return self.current_iteration.green_phase
        else:
            return self.current_iteration.blue_phase
    
    def _generate_summary(self) -> Dict[str, Any]:
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        phase_stats = {"red": {}, "green": {}, "blue": {}}
        
        for iteration in self.current_report.iterations:
            for phase_name, phase_record in [
                ("red", iteration.red_phase),
                ("green", iteration.green_phase),
                ("blue", iteration.blue_phase)
            ]:
                stats = phase_stats[phase_name]
                stats["total"] = stats.get("total", 0) + 1
                if phase_record.status == CycleStatus.COMPLETED:
                    stats["completed"] = stats.get("completed", 0) + 1
                elif phase_record.status == CycleStatus.FAILED:
                    stats["failed"] = stats.get("failed", 0) + 1
                
                total_passed += phase_record.passed_count
                total_failed += phase_record.failed_count
                total_skipped += phase_record.skipped_count
        
        return {
            "total_iterations": self.current_report.total_iterations,
            "completed_iterations": self.current_report.completed_iterations,
            "failed_iterations": self.current_report.failed_iterations,
            "success_rate": (
                self.current_report.completed_iterations / self.current_report.total_iterations * 100
                if self.current_report.total_iterations > 0 else 0
            ),
            "test_stats": {
                "total_passed": total_passed,
                "total_failed": total_failed,
                "total_skipped": total_skipped,
                "pass_rate": total_passed / (total_passed + total_failed) * 100
                if (total_passed + total_failed) > 0 else 0
            },
            "phase_stats": phase_stats
        }
    
    def _generate_recommendations(self) -> List[str]:
        recommendations = []
        
        if not self.current_report:
            return recommendations
        
        failed_iterations = [
            it for it in self.current_report.iterations
            if it.overall_result == CycleResult.FAILURE
        ]
        
        if failed_iterations:
            recommendations.append(
                f"有 {len(failed_iterations)} 个迭代失败，建议检查以下元素: " +
                ", ".join(it.spec_element_name for it in failed_iterations[:5])
            )
        
        red_failures = [
            it for it in self.current_report.iterations
            if it.red_phase.status == CycleStatus.FAILED
        ]
        if red_failures:
            recommendations.append(
                f"有 {len(red_failures)} 个RED阶段失败，建议检查测试用例设计"
            )
        
        green_failures = [
            it for it in self.current_report.iterations
            if it.green_phase.status == CycleStatus.FAILED
        ]
        if green_failures:
            recommendations.append(
                f"有 {len(green_failures)} 个GREEN阶段失败，建议检查实现代码"
            )
        
        blue_failures = [
            it for it in self.current_report.iterations
            if it.blue_phase.status == CycleStatus.FAILED
        ]
        if blue_failures:
            recommendations.append(
                f"有 {len(blue_failures)} 个BLUE阶段失败，建议检查重构过程"
            )
        
        success_rate = self.current_report.summary.get("success_rate", 0)
        if success_rate >= 90:
            recommendations.append("整体执行情况优秀，建议持续保持")
        elif success_rate >= 70:
            recommendations.append("整体执行情况良好，建议优化失败的部分")
        else:
            recommendations.append("整体执行情况需要改进，建议全面审查")
        
        return recommendations
    
    def _calculate_metrics(self) -> Dict[str, Any]:
        metrics = {
            "total_duration_seconds": 0,
            "average_iteration_duration_seconds": 0,
            "phase_durations": {"red": 0, "green": 0, "blue": 0},
            "test_execution_times": []
        }
        
        if not self.current_report:
            return metrics
        
        try:
            start_time = datetime.fromisoformat(self.current_report.started_at)
            end_time = datetime.fromisoformat(self.current_report.completed_at or datetime.now().isoformat())
            metrics["total_duration_seconds"] = (end_time - start_time).total_seconds()
        except (ValueError, TypeError):
            pass
        
        total_iteration_duration = 0
        iteration_count = 0
        
        for iteration in self.current_report.iterations:
            if iteration.started_at and iteration.completed_at:
                try:
                    start = datetime.fromisoformat(iteration.started_at)
                    end = datetime.fromisoformat(iteration.completed_at)
                    duration = (end - start).total_seconds()
                    total_iteration_duration += duration
                    iteration_count += 1
                except (ValueError, TypeError):
                    pass
            
            for phase_name, phase_record in [
                ("red", iteration.red_phase),
                ("green", iteration.green_phase),
                ("blue", iteration.blue_phase)
            ]:
                if phase_record.started_at and phase_record.completed_at:
                    try:
                        start = datetime.fromisoformat(phase_record.started_at)
                        end = datetime.fromisoformat(phase_record.completed_at)
                        metrics["phase_durations"][phase_name] += (end - start).total_seconds()
                    except (ValueError, TypeError):
                        pass
        
        if iteration_count > 0:
            metrics["average_iteration_duration_seconds"] = total_iteration_duration / iteration_count
        
        return metrics
    
    def _save_state(self) -> None:
        if not self.current_report:
            return
        
        state_file = self.state_dir / f"{self.current_report.report_id}_state.json"
        
        state_dict = self._report_to_dict(self.current_report)
        
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, ensure_ascii=False, indent=2, default=str)
    
    def _save_final_report(self) -> None:
        if not self.current_report:
            return
        
        report_file = self.output_dir / "cycle_reports" / f"{self.current_report.report_id}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        report_dict = self._report_to_dict(self.current_report)
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2, default=str)
    
    def _report_to_dict(self, report: CycleExecutionReport) -> Dict[str, Any]:
        return {
            "report_id": report.report_id,
            "spec_id": report.spec_id,
            "spec_name": report.spec_name,
            "started_at": report.started_at,
            "completed_at": report.completed_at,
            "total_iterations": report.total_iterations,
            "completed_iterations": report.completed_iterations,
            "failed_iterations": report.failed_iterations,
            "iterations": [
                {
                    "iteration_id": it.iteration_id,
                    "cycle_number": it.cycle_number,
                    "spec_element_id": it.spec_element_id,
                    "spec_element_name": it.spec_element_name,
                    "red_phase": self._phase_to_dict(it.red_phase),
                    "green_phase": self._phase_to_dict(it.green_phase),
                    "blue_phase": self._phase_to_dict(it.blue_phase),
                    "overall_result": it.overall_result.value,
                    "started_at": it.started_at,
                    "completed_at": it.completed_at,
                    "notes": it.notes
                }
                for it in report.iterations
            ],
            "summary": report.summary,
            "recommendations": report.recommendations,
            "metrics": report.metrics
        }
    
    def _phase_to_dict(self, phase: CyclePhaseRecord) -> Dict[str, Any]:
        return {
            "phase": phase.phase.value,
            "status": phase.status.value,
            "started_at": phase.started_at,
            "completed_at": phase.completed_at,
            "test_cases": phase.test_cases,
            "passed_count": phase.passed_count,
            "failed_count": phase.failed_count,
            "skipped_count": phase.skipped_count,
            "error_message": phase.error_message,
            "artifacts": phase.artifacts,
            "metrics": phase.metrics
        }
    
    def load_state(self, report_id: str) -> Optional[CycleExecutionReport]:
        state_file = self.state_dir / f"{report_id}_state.json"
        
        if not state_file.exists():
            return None
        
        with open(state_file, "r", encoding="utf-8") as f:
            state_dict = json.load(f)
        
        self.current_report = self._dict_to_report(state_dict)
        
        return self.current_report
    
    def _dict_to_report(self, data: Dict[str, Any]) -> CycleExecutionReport:
        report = CycleExecutionReport(
            report_id=data["report_id"],
            spec_id=data["spec_id"],
            spec_name=data["spec_name"],
            started_at=data["started_at"],
            completed_at=data.get("completed_at"),
            total_iterations=data.get("total_iterations", 0),
            completed_iterations=data.get("completed_iterations", 0),
            failed_iterations=data.get("failed_iterations", 0),
            summary=data.get("summary", {}),
            recommendations=data.get("recommendations", []),
            metrics=data.get("metrics", {})
        )
        
        for it_data in data.get("iterations", []):
            iteration = CycleIteration(
                iteration_id=it_data["iteration_id"],
                cycle_number=it_data["cycle_number"],
                spec_element_id=it_data["spec_element_id"],
                spec_element_name=it_data["spec_element_name"],
                red_phase=self._dict_to_phase(it_data["red_phase"]),
                green_phase=self._dict_to_phase(it_data["green_phase"]),
                blue_phase=self._dict_to_phase(it_data["blue_phase"]),
                overall_result=CycleResult(it_data["overall_result"]),
                started_at=it_data.get("started_at"),
                completed_at=it_data.get("completed_at"),
                notes=it_data.get("notes", [])
            )
            report.iterations.append(iteration)
        
        return report
    
    def _dict_to_phase(self, data: Dict[str, Any]) -> CyclePhaseRecord:
        return CyclePhaseRecord(
            phase=CyclePhase(data["phase"]),
            status=CycleStatus(data["status"]),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            test_cases=data.get("test_cases", []),
            passed_count=data.get("passed_count", 0),
            failed_count=data.get("failed_count", 0),
            skipped_count=data.get("skipped_count", 0),
            error_message=data.get("error_message"),
            artifacts=data.get("artifacts", {}),
            metrics=data.get("metrics", {})
        )


class RedGreenBlueCycleExecutor:
    """红绿蓝循环自动化执行器 - 实现TDD的红绿蓝循环自动化
    
    增强功能:
    - 智能分析每个阶段的结果
    - 自动生成修复建议
    - 依赖感知的执行顺序
    - 实时进度监控
    """
    
    def __init__(
        self,
        output_dir: Path,
        logger: Optional[logging.Logger] = None
    ):
        self.output_dir = output_dir
        self.logger = logger or self._setup_logger()
        self.state_tracker = CycleStateTracker(output_dir, logger)
        self.test_generator = TestCaseGenerator(logger)
        
        self.integration_enhancer = SddTddIntegrationEnhancer(logger)
        self.dependency_analyzer = DependencyAnalyzer(logger)
        self.auto_fix_analyzer = AutoFixAnalyzer(logger)
        
        self.intelligence_cache: Dict[str, CycleIntelligence] = {}
        self.progress_history: List[RealtimeProgress] = []
        self.checkpoints: List[CheckpointData] = []
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("RedGreenBlueCycleExecutor")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def execute_cycle(
        self,
        spec: ParsedSpecification,
        test_runner: Optional[callable] = None,
        code_generator: Optional[callable] = None,
        refactoring_handler: Optional[callable] = None,
        dry_run: bool = False
    ) -> CycleExecutionReport:
        """执行红绿蓝循环
        
        增强功能:
        - 基于依赖关系的执行顺序优化
        - 智能阶段分析
        - 自动修复建议生成
        - 实时进度跟踪
        """
        self.logger.info("=" * 60)
        self.logger.info("开始红绿蓝循环执行 (增强模式)")
        self.logger.info("=" * 60)
        
        dependencies = self.dependency_analyzer.analyze_dependencies(spec)
        execution_order = self.dependency_analyzer.get_execution_order()
        
        self.logger.info(f"依赖分析完成，执行顺序: {execution_order}")
        
        report = self.state_tracker.initialize_report(spec)
        
        element_map = {e.name: e for e in spec.elements}
        
        ordered_elements = []
        for element_name in execution_order:
            if element_name in element_map:
                ordered_elements.append((element_map[element_name], spec.elements.index(element_map[element_name])))
        
        for element, original_idx in ordered_elements:
            self.logger.info(f"\n{'='*40}")
            self.logger.info(f"迭代 {original_idx + 1}/{len(spec.elements)}: {element.name}")
            self.logger.info(f"依赖层级: {self.dependency_analyzer.get_dependency_level(element.name)}")
            self.logger.info(f"{'='*40}")
            
            self._update_progress(
                CyclePhase.RED,
                original_idx,
                len(spec.elements),
                f"开始处理元素: {element.name}"
            )
            
            iteration = self.state_tracker.start_iteration(original_idx)
            
            self._create_checkpoint(original_idx, CyclePhase.RED, {"element": element.name})
            
            try:
                red_result = self._execute_red_phase_enhanced(
                    element, spec, test_runner, dry_run
                )
                
                if red_result["success"]:
                    green_result = self._execute_green_phase_enhanced(
                        element, spec, test_runner, code_generator, dry_run
                    )
                    
                    if green_result["success"]:
                        blue_result = self._execute_blue_phase_enhanced(
                            element, spec, test_runner, refactoring_handler, dry_run
                        )
                        
                        iteration_result = CycleResult.SUCCESS if blue_result["success"] else CycleResult.PARTIAL
                    else:
                        iteration_result = CycleResult.FAILURE
                else:
                    iteration_result = CycleResult.FAILURE
                
                self.state_tracker.complete_iteration(
                    iteration_result,
                    notes=[f"元素 {element.name} 处理完成"]
                )
                
            except Exception as e:
                self.logger.error(f"迭代 {original_idx + 1} 执行失败: {e}")
                
                fix_suggestions = self._generate_error_fix_suggestions(str(e), element)
                self.logger.info(f"自动修复建议: {len(fix_suggestions)} 条")
                
                self.state_tracker.complete_iteration(
                    CycleResult.FAILURE,
                    notes=[f"执行错误: {str(e)}", f"修复建议: {len(fix_suggestions)} 条"]
                )
        
        report = self.state_tracker.complete_report()
        
        self._enhance_report_with_intelligence(report)
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("红绿蓝循环执行完成 (增强模式)")
        self.logger.info(f"总迭代: {report.total_iterations}")
        self.logger.info(f"完成: {report.completed_iterations}")
        self.logger.info(f"失败: {report.failed_iterations}")
        self.logger.info("=" * 60)
        
        return report
    
    def _execute_red_phase(
        self,
        element: SpecElement,
        spec: ParsedSpecification,
        test_runner: Optional[callable],
        dry_run: bool
    ) -> Dict[str, Any]:
        self.logger.info(f"\n[RED 阶段] 编写失败的测试: {element.name}")

        phase_record = self.state_tracker.start_phase(CyclePhase.RED)

        result = {
            "success": False,
            "test_cases": [],
            "error": None
        }

        try:
            test_cases = self._generate_element_tests(element, spec)
            test_case_ids = [tc.test_id for tc in test_cases]

            if dry_run:
                self.logger.info("[DRY RUN] 跳过测试执行")
                passed, failed, skipped = 0, len(test_cases), 0
                result["success"] = True
            else:
                if test_runner:
                    test_results = test_runner(test_cases)
                    passed = test_results.get("passed", 0)
                    failed = test_results.get("failed", 0)
                    skipped = test_results.get("skipped", 0)
                    result["success"] = failed > 0
                else:
                    self.logger.info("未提供测试运行器，模拟RED阶段")
                    passed, failed, skipped = 0, len(test_cases), 0
                    result["success"] = True

            result["test_cases"] = test_case_ids

            self.state_tracker.complete_phase(
                CyclePhase.RED,
                passed=passed,
                failed=failed,
                skipped=skipped,
                test_cases=test_case_ids,
                metrics={"test_count": len(test_cases)}
            )

            self.logger.info(f"[RED 阶段] 完成: {passed} 通过, {failed} 失败, {skipped} 跳过")

        except Exception as e:
            self.logger.error(f"[RED 阶段] 失败: {e}")
            result["error"] = str(e)
            self.state_tracker.complete_phase(
                CyclePhase.RED,
                error_message=str(e)
            )

        return result
    
    def _execute_red_phase_enhanced(
        self,
        element: SpecElement,
        spec: ParsedSpecification,
        test_runner: Optional[callable],
        dry_run: bool
    ) -> Dict[str, Any]:
        """增强的RED阶段执行 - 包含智能分析"""
        self.logger.info(f"\n[RED 阶段 - 增强] 编写失败的测试: {element.name}")
        
        phase_record = self.state_tracker.start_phase(CyclePhase.RED)
        
        self._update_progress(CyclePhase.RED, 0, 0, "生成测试用例")
        
        result = {
            "success": False,
            "test_cases": [],
            "error": None,
            "intelligence": None,
            "fix_suggestions": []
        }
        
        try:
            test_cases = self._generate_element_tests(element, spec)
            test_case_ids = [tc.test_id for tc in test_cases]
            
            intelligence = self._analyze_red_phase_intelligence(element, test_cases)
            result["intelligence"] = intelligence
            self.intelligence_cache[f"{element.name}_red"] = intelligence
            
            self._log_intelligence_findings(intelligence)
            
            if dry_run:
                self.logger.info("[DRY RUN] 跳过测试执行")
                passed, failed, skipped = 0, len(test_cases), 0
                result["success"] = True
            else:
                if test_runner:
                    test_results = test_runner(test_cases)
                    passed = test_results.get("passed", 0)
                    failed = test_results.get("failed", 0)
                    skipped = test_results.get("skipped", 0)
                    
                    if failed == 0 and passed > 0:
                        self.logger.warning("[RED 阶段] 所有测试都通过了，可能需要检查测试设计")
                        result["fix_suggestions"] = self._suggest_red_phase_improvements(element, test_cases)
                    
                    result["success"] = failed > 0 or (passed == 0 and len(test_cases) > 0)
                else:
                    self.logger.info("未提供测试运行器，模拟RED阶段")
                    passed, failed, skipped = 0, len(test_cases), 0
                    result["success"] = True
            
            result["test_cases"] = test_case_ids
            
            self.state_tracker.complete_phase(
                CyclePhase.RED,
                passed=passed,
                failed=failed,
                skipped=skipped,
                test_cases=test_case_ids,
                metrics={
                    "test_count": len(test_cases),
                    "intelligence_score": intelligence.findings.__len__() if intelligence else 0
                }
            )
            
            self.logger.info(f"[RED 阶段 - 增强] 完成: {passed} 通过, {failed} 失败, {skipped} 跳过")
            
        except Exception as e:
            self.logger.error(f"[RED 阶段 - 增强] 失败: {e}")
            result["error"] = str(e)
            result["fix_suggestions"] = self._generate_error_fix_suggestions(str(e), element)
            self.state_tracker.complete_phase(
                CyclePhase.RED,
                error_message=str(e)
            )
        
        return result
    
    def _execute_green_phase(
        self,
        element: SpecElement,
        spec: ParsedSpecification,
        test_runner: Optional[callable],
        code_generator: Optional[callable],
        dry_run: bool
    ) -> Dict[str, Any]:
        self.logger.info(f"\n[GREEN 阶段] 编写最小实现: {element.name}")
        
        phase_record = self.state_tracker.start_phase(CyclePhase.GREEN)
        
        result = {
            "success": False,
            "error": None
        }
        
        try:
            if dry_run:
                self.logger.info("[DRY RUN] 跳过代码生成和测试执行")
                passed, failed, skipped = 1, 0, 0
                result["success"] = True
            else:
                if code_generator:
                    code_artifacts = code_generator(element, spec)
                    self.logger.info(f"生成代码: {list(code_artifacts.keys())}")
                
                if test_runner:
                    iteration = self.state_tracker.current_iteration
                    test_case_ids = iteration.red_phase.test_cases
                    
                    test_results = test_runner(test_case_ids)
                    passed = test_results.get("passed", 0)
                    failed = test_results.get("failed", 0)
                    skipped = test_results.get("skipped", 0)
                    result["success"] = failed == 0 and passed > 0
                else:
                    self.logger.info("未提供测试运行器，模拟GREEN阶段")
                    passed, failed, skipped = 1, 0, 0
                    result["success"] = True
            
            self.state_tracker.complete_phase(
                CyclePhase.GREEN,
                passed=passed,
                failed=failed,
                skipped=skipped,
                metrics={"implementation": "minimal"}
            )
            
            self.logger.info(f"[GREEN 阶段] 完成: {passed} 通过, {failed} 失败")
            
        except Exception as e:
            self.logger.error(f"[GREEN 阶段] 失败: {e}")
            result["error"] = str(e)
            self.state_tracker.complete_phase(
                CyclePhase.GREEN,
                error_message=str(e)
            )
        
        return result
    
    def _execute_blue_phase(
        self,
        element: SpecElement,
        spec: ParsedSpecification,
        test_runner: Optional[callable],
        refactoring_handler: Optional[callable],
        dry_run: bool
    ) -> Dict[str, Any]:
        self.logger.info(f"\n[BLUE 阶段] 重构代码: {element.name}")
        
        phase_record = self.state_tracker.start_phase(CyclePhase.BLUE)
        
        result = {
            "success": False,
            "refactorings": [],
            "error": None
        }
        
        try:
            if dry_run:
                self.logger.info("[DRY RUN] 跳过重构")
                passed, failed, skipped = 1, 0, 0
                result["success"] = True
                refactorings = []
            else:
                refactorings = []
                
                if refactoring_handler:
                    refactor_result = refactoring_handler(element, spec)
                    refactorings = refactor_result.get("refactorings", [])
                    self.logger.info(f"执行重构: {refactorings}")
                
                if test_runner:
                    iteration = self.state_tracker.current_iteration
                    test_case_ids = iteration.red_phase.test_cases
                    
                    test_results = test_runner(test_case_ids)
                    passed = test_results.get("passed", 0)
                    failed = test_results.get("failed", 0)
                    skipped = test_results.get("skipped", 0)
                    result["success"] = failed == 0 and passed > 0
                else:
                    self.logger.info("未提供测试运行器，模拟BLUE阶段")
                    passed, failed, skipped = 1, 0, 0
                    result["success"] = True
            
            result["refactorings"] = refactorings
            
            self.state_tracker.complete_phase(
                CyclePhase.BLUE,
                passed=passed,
                failed=failed,
                skipped=skipped,
                metrics={"refactorings": refactorings}
            )
            
            self.logger.info(f"[BLUE 阶段] 完成: 重构 {len(refactorings)} 项")
            
        except Exception as e:
            self.logger.error(f"[BLUE 阶段] 失败: {e}")
            result["error"] = str(e)
            self.state_tracker.complete_phase(
                CyclePhase.BLUE,
                error_message=str(e)
            )
        
        return result
    
    def _generate_element_tests(
        self,
        element: SpecElement,
        spec: ParsedSpecification
    ) -> List[GeneratedTestCase]:
        test_cases = []
        
        if element.element_type == SpecElementType.INTERFACE:
            iface = InterfaceDefinition(
                name=element.name,
                description=element.description,
                parameters=element.attributes,
                exceptions=element.metadata.get("exceptions", []),
                return_type=element.metadata.get("return_type", "void")
            )
            test_cases.extend(self.test_generator._generate_interface_tests(iface, spec.spec_id))
        
        elif element.element_type == SpecElementType.DATA_MODEL:
            model = DataModel(
                name=element.name,
                description=element.description,
                attributes=element.attributes,
                constraints=list(element.constraints.values()) if element.constraints else []
            )
            test_cases.extend(self.test_generator._generate_model_tests(model, spec.spec_id))
        
        elif element.element_type == SpecElementType.BEHAVIOR_RULE:
            rule = BehaviorRule(
                rule_id=element.metadata.get("rule_id", ""),
                name=element.name,
                description=element.description,
                condition=element.constraints.get("condition", ""),
                action=element.constraints.get("action", ""),
                priority=element.metadata.get("priority", 0)
            )
            test_cases.extend(self.test_generator._generate_rule_tests(rule, spec.spec_id))
        
        else:
            constraint = {"name": element.name, "description": element.description}
            test_cases.extend(self.test_generator._generate_constraint_tests(constraint, spec.spec_id))
        
        return test_cases
    
    def resume_cycle(
        self,
        report_id: str,
        test_runner: Optional[callable] = None,
        code_generator: Optional[callable] = None,
        refactoring_handler: Optional[callable] = None
    ) -> CycleExecutionReport:
        self.logger.info(f"恢复循环执行: {report_id}")
        
        report = self.state_tracker.load_state(report_id)
        
        if not report:
            raise ValueError(f"未找到报告: {report_id}")
        
        if report.completed_at:
            self.logger.info("循环已完成，返回现有报告")
            return report
        
        self.logger.info(f"从迭代 {report.completed_iterations + 1} 继续")
        
        return report


class CycleReportGenerator:
    """循环结果报告生成器 - 生成详细的循环执行报告"""
    
    def __init__(self, output_dir: Path, logger: Optional[logging.Logger] = None):
        self.output_dir = output_dir
        self.reports_dir = output_dir / "cycle_reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger or self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("CycleReportGenerator")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def generate_report(
        self,
        cycle_report: CycleExecutionReport,
        format_type: str = "json"
    ) -> str:
        self.logger.info(f"生成循环报告: {cycle_report.report_id}")
        
        if format_type == "json":
            return self._generate_json_report(cycle_report)
        elif format_type == "markdown":
            return self._generate_markdown_report(cycle_report)
        elif format_type == "html":
            return self._generate_html_report(cycle_report)
        else:
            raise ValueError(f"不支持的格式: {format_type}")
    
    def _generate_json_report(self, report: CycleExecutionReport) -> str:
        report_file = self.reports_dir / f"{report.report_id}.json"
        
        report_data = {
            "meta": {
                "report_id": report.report_id,
                "spec_id": report.spec_id,
                "spec_name": report.spec_name,
                "generated_at": datetime.now().isoformat()
            },
            "execution": {
                "started_at": report.started_at,
                "completed_at": report.completed_at,
                "total_iterations": report.total_iterations,
                "completed_iterations": report.completed_iterations,
                "failed_iterations": report.failed_iterations
            },
            "iterations": [
                {
                    "iteration_id": it.iteration_id,
                    "cycle_number": it.cycle_number,
                    "spec_element": {
                        "id": it.spec_element_id,
                        "name": it.spec_element_name
                    },
                    "phases": {
                        "red": self._phase_summary(it.red_phase),
                        "green": self._phase_summary(it.green_phase),
                        "blue": self._phase_summary(it.blue_phase)
                    },
                    "result": it.overall_result.value,
                    "duration": self._calculate_phase_duration(it),
                    "notes": it.notes
                }
                for it in report.iterations
            ],
            "summary": report.summary,
            "recommendations": report.recommendations,
            "metrics": report.metrics
        }
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
        
        return str(report_file)
    
    def _generate_markdown_report(self, report: CycleExecutionReport) -> str:
        report_file = self.reports_dir / f"{report.report_id}.md"
        
        lines = [
            f"# 红绿蓝循环执行报告",
            "",
            f"**报告ID**: {report.report_id}",
            f"**规范**: {report.spec_name} ({report.spec_id})",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 执行概览",
            "",
            f"- **开始时间**: {report.started_at}",
            f"- **完成时间**: {report.completed_at or '进行中'}",
            f"- **总迭代数**: {report.total_iterations}",
            f"- **完成迭代**: {report.completed_iterations}",
            f"- **失败迭代**: {report.failed_iterations}",
            ""
        ]
        
        if report.summary:
            lines.extend([
                "## 统计摘要",
                "",
                f"- **成功率**: {report.summary.get('success_rate', 0):.1f}%",
                f"- **测试通过**: {report.summary.get('test_stats', {}).get('total_passed', 0)}",
                f"- **测试失败**: {report.summary.get('test_stats', {}).get('total_failed', 0)}",
                ""
            ])
        
        lines.extend([
            "## 迭代详情",
            ""
        ])
        
        for it in report.iterations:
            status_emoji = "✅" if it.overall_result == CycleResult.SUCCESS else "❌"
            lines.extend([
                f"### {status_emoji} 迭代 {it.cycle_number}: {it.spec_element_name}",
                "",
                f"| 阶段 | 状态 | 通过 | 失败 | 跳过 |",
                f"|------|------|------|------|------|",
                f"| RED | {it.red_phase.status.value} | {it.red_phase.passed_count} | {it.red_phase.failed_count} | {it.red_phase.skipped_count} |",
                f"| GREEN | {it.green_phase.status.value} | {it.green_phase.passed_count} | {it.green_phase.failed_count} | {it.green_phase.skipped_count} |",
                f"| BLUE | {it.blue_phase.status.value} | {it.blue_phase.passed_count} | {it.blue_phase.failed_count} | {it.blue_phase.skipped_count} |",
                ""
            ])
            
            if it.notes:
                lines.extend([
                    "**备注**:",
                    ""
                ])
                for note in it.notes:
                    lines.append(f"- {note}")
                lines.append("")
        
        if report.recommendations:
            lines.extend([
                "## 建议",
                ""
            ])
            for rec in report.recommendations:
                lines.append(f"- {rec}")
            lines.append("")
        
        if report.metrics:
            lines.extend([
                "## 性能指标",
                "",
                f"- **总耗时**: {report.metrics.get('total_duration_seconds', 0):.2f} 秒",
                f"- **平均迭代耗时**: {report.metrics.get('average_iteration_duration_seconds', 0):.2f} 秒",
                ""
            ])
        
        content = "\n".join(lines)
        
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        return str(report_file)
    
    def _generate_html_report(self, report: CycleExecutionReport) -> str:
        report_file = self.reports_dir / f"{report.report_id}.html"
        
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>红绿蓝循环执行报告 - {report.report_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .meta {{ background: #f9f9f9; padding: 15px; border-radius: 4px; margin-bottom: 20px; }}
        .meta p {{ margin: 5px 0; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-card h3 {{ margin: 0; font-size: 14px; opacity: 0.9; }}
        .stat-card p {{ margin: 10px 0 0; font-size: 28px; font-weight: bold; }}
        .iteration {{ border: 1px solid #ddd; border-radius: 4px; margin: 15px 0; overflow: hidden; }}
        .iteration-header {{ background: #f5f5f5; padding: 15px; display: flex; justify-content: space-between; align-items: center; }}
        .iteration-body {{ padding: 15px; }}
        .phase-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        .phase-table th, .phase-table td {{ padding: 10px; text-align: center; border: 1px solid #ddd; }}
        .phase-table th {{ background: #f9f9f9; }}
        .phase-red {{ background: #ffebee; }}
        .phase-green {{ background: #e8f5e9; }}
        .phase-blue {{ background: #e3f2fd; }}
        .status-success {{ color: #4CAF50; font-weight: bold; }}
        .status-failure {{ color: #f44336; font-weight: bold; }}
        .recommendations {{ background: #fff3e0; padding: 15px; border-radius: 4px; border-left: 4px solid #ff9800; }}
        .recommendations ul {{ margin: 10px 0; padding-left: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔴🟢🔵 红绿蓝循环执行报告</h1>
        
        <div class="meta">
            <p><strong>报告ID:</strong> {report.report_id}</p>
            <p><strong>规范:</strong> {report.spec_name} ({report.spec_id})</p>
            <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>总迭代</h3>
                <p>{report.total_iterations}</p>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">
                <h3>完成</h3>
                <p>{report.completed_iterations}</p>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);">
                <h3>失败</h3>
                <p>{report.failed_iterations}</p>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <h3>成功率</h3>
                <p>{report.summary.get('success_rate', 0):.1f}%</p>
            </div>
        </div>
        
        <h2>迭代详情</h2>
"""
        
        for it in report.iterations:
            status_class = "status-success" if it.overall_result == CycleResult.SUCCESS else "status-failure"
            status_text = "✅ 成功" if it.overall_result == CycleResult.SUCCESS else "❌ 失败"
            
            html_content += f"""
        <div class="iteration">
            <div class="iteration-header">
                <strong>迭代 {it.cycle_number}: {it.spec_element_name}</strong>
                <span class="{status_class}">{status_text}</span>
            </div>
            <div class="iteration-body">
                <table class="phase-table">
                    <tr>
                        <th>阶段</th>
                        <th>状态</th>
                        <th>通过</th>
                        <th>失败</th>
                        <th>跳过</th>
                    </tr>
                    <tr class="phase-red">
                        <td><strong>RED</strong></td>
                        <td>{it.red_phase.status.value}</td>
                        <td>{it.red_phase.passed_count}</td>
                        <td>{it.red_phase.failed_count}</td>
                        <td>{it.red_phase.skipped_count}</td>
                    </tr>
                    <tr class="phase-green">
                        <td><strong>GREEN</strong></td>
                        <td>{it.green_phase.status.value}</td>
                        <td>{it.green_phase.passed_count}</td>
                        <td>{it.green_phase.failed_count}</td>
                        <td>{it.green_phase.skipped_count}</td>
                    </tr>
                    <tr class="phase-blue">
                        <td><strong>BLUE</strong></td>
                        <td>{it.blue_phase.status.value}</td>
                        <td>{it.blue_phase.passed_count}</td>
                        <td>{it.blue_phase.failed_count}</td>
                        <td>{it.blue_phase.skipped_count}</td>
                    </tr>
                </table>
            </div>
        </div>
"""
        
        if report.recommendations:
            html_content += """
        <h2>建议</h2>
        <div class="recommendations">
            <ul>
"""
            for rec in report.recommendations:
                html_content += f"                <li>{rec}</li>\n"
            html_content += """            </ul>
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>
"""
        
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return str(report_file)
    
    def _phase_summary(self, phase: CyclePhaseRecord) -> Dict[str, Any]:
        return {
            "status": phase.status.value,
            "passed": phase.passed_count,
            "failed": phase.failed_count,
            "skipped": phase.skipped_count,
            "duration": self._calculate_duration(phase.started_at, phase.completed_at)
        }
    
    def _calculate_phase_duration(self, iteration: CycleIteration) -> float:
        return self._calculate_duration(iteration.started_at, iteration.completed_at)
    
    def _calculate_duration(self, start: Optional[str], end: Optional[str]) -> float:
        if not start or not end:
            return 0.0
        try:
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end)
            return (end_dt - start_dt).total_seconds()
        except (ValueError, TypeError):
            return 0.0


class SddTddIntegrator:
    """SDD与TDD集成器主类
    
    增强功能:
    - 智能规范-测试映射
    - 依赖感知的执行顺序
    - 自动修复建议
    - 质量评估
    """
    
    def __init__(
        self,
        output_dir: str = None,
        logger: Optional[logging.Logger] = None
    ):
        if output_dir is None:
            try:
                from skillscripts.utils.enhanced_path_config_manager import create_path_manager, OutputType
                _path_mgr = create_path_manager()
                self.output_dir = _path_mgr.get_output_path(OutputType.REPORT, subdirectory="sdd_tdd")
            except Exception:
                self.output_dir = Path("output/sdd_tdd")
        else:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logger or self._setup_logger()
        
        self.spec_parser = SpecParser(self.logger)
        self.test_generator = TestCaseGenerator(self.logger)
        self.coverage_mapper = CoverageMapper(self.logger)
        self.spec_validator = SpecValidator(self.logger)
        
        self.cycle_executor = RedGreenBlueCycleExecutor(self.output_dir, self.logger)
        self.cycle_report_generator = CycleReportGenerator(self.output_dir, self.logger)
        
        self.integration_enhancer = SddTddIntegrationEnhancer(self.logger)
        self.dependency_analyzer = DependencyAnalyzer(self.logger)
        self.auto_fix_analyzer = AutoFixAnalyzer(self.logger)
        self.quality_assessor = QualityAssessor(self.output_dir, self.logger)
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("SddTddIntegrator")
        logger.setLevel(logging.INFO)
        
        log_file = self.output_dir / "sdd_tdd_integrator.log"
        handler = logging.FileHandler(log_file, encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def parse_spec(self, spec_path: str) -> Tuple[ParsedSpecification, ValidationResult]:
        self.logger.info(f"解析规范文件: {spec_path}")
        
        spec = self.spec_parser.parse_file(spec_path)
        validation = self.spec_validator.validate(spec)
        
        self._save_parsed_spec(spec)
        
        return spec, validation
    
    def generate_tests(
        self,
        spec: ParsedSpecification,
        output_path: Optional[str] = None
    ) -> Tuple[List[GeneratedTestCase], str]:
        self.logger.info(f"从规范 {spec.spec_id} 生成测试用例")
        
        test_cases = self.test_generator.generate_from_spec(spec)
        test_content = self.test_generator.generate_test_file_content(test_cases, spec)
        
        if output_path:
            output_file = Path(output_path)
        else:
            filename = f"test_{self._sanitize_name(spec.spec_name)}.py"
            output_file = self.output_dir / "tests" / filename
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        self.logger.info(f"测试文件已生成: {output_file}")
        
        return test_cases, str(output_file)
    
    def generate_coverage_report(
        self,
        spec: ParsedSpecification,
        test_cases: List[GeneratedTestCase],
        test_results: Optional[Dict[str, Any]] = None
    ) -> CoverageReport:
        self.logger.info(f"生成覆盖率映射报告")
        
        report = self.coverage_mapper.generate_coverage_report(
            spec,
            test_cases,
            test_results
        )
        
        self._save_coverage_report(report)
        
        return report
    
    def validate_spec(self, spec: ParsedSpecification) -> ValidationResult:
        self.logger.info(f"验证规范完整性: {spec.spec_id}")
        
        validation = self.spec_validator.validate(spec)
        
        self._save_validation_result(spec.spec_id, validation)
        
        return validation
    
    def run_full_integration(
        self,
        spec_path: str,
        test_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        self.logger.info("=" * 60)
        self.logger.info("开始 SDD-TDD 完整集成流程")
        self.logger.info("=" * 60)
        
        result = {
            "spec_path": spec_path,
            "started_at": datetime.now().isoformat(),
            "status": "in_progress"
        }
        
        try:
            spec, validation = self.parse_spec(spec_path)
            result["spec"] = {
                "id": spec.spec_id,
                "name": spec.spec_name,
                "version": spec.version,
                "elements_count": len(spec.elements)
            }
            result["validation"] = {
                "is_valid": validation.is_valid,
                "completeness_score": validation.completeness_score,
                "errors_count": len(validation.errors),
                "warnings_count": len(validation.warnings)
            }
            
            if not validation.is_valid:
                result["status"] = "validation_failed"
                result["error"] = "规范验证失败"
                return result
            
            test_cases, test_file = self.generate_tests(spec)
            result["test_generation"] = {
                "test_cases_count": len(test_cases),
                "test_file": test_file
            }
            
            coverage_report = self.generate_coverage_report(spec, test_cases, test_results)
            result["coverage"] = {
                "report_id": coverage_report.report_id,
                "overall_coverage": coverage_report.overall_coverage,
                "recommendations": coverage_report.recommendations
            }
            
            result["status"] = "completed"
            result["completed_at"] = datetime.now().isoformat()
            
            self.logger.info("=" * 60)
            self.logger.info("SDD-TDD 集成流程完成")
            self.logger.info(f"状态: {result['status']}")
            self.logger.info(f"覆盖率: {coverage_report.overall_coverage:.1f}%")
            self.logger.info("=" * 60)
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self.logger.error(f"集成流程失败: {e}")
        
        self._save_integration_result(result)
        
        return result


class SpecToTestAutoMapper:
    """规范到测试用例的自动映射器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self._mapping_cache: Dict[str, List[str]] = {}
        self._semantic_analyzer = SemanticAnalyzer()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("SpecToTestAutoMapper")
        logger.setLevel(logging.INFO)
        return logger
    
    def auto_map(
        self,
        spec: ParsedSpecification,
        test_cases: List[GeneratedTestCase]
    ) -> Dict[str, List[str]]:
        """
        自动映射规范元素到测试用例
        
        Args:
            spec: 解析后的规范
            test_cases: 测试用例列表
            
        Returns:
            Dict[str, List[str]]: 规范元素ID到测试用例ID列表的映射
        """
        mappings = {}
        
        for element in spec.elements:
            mapped_tests = self._map_element_to_tests(element, test_cases)
            mappings[element.name] = mapped_tests
            self._mapping_cache[element.name] = mapped_tests
        
        self.logger.info(f"完成自动映射: {len(mappings)} 个规范元素")
        return mappings
    
    def _map_element_to_tests(
        self,
        element: SpecElement,
        test_cases: List[GeneratedTestCase]
    ) -> List[str]:
        """映射单个规范元素到测试用例"""
        mapped_ids = []
        
        for tc in test_cases:
            if self._is_related(element, tc):
                mapped_ids.append(tc.test_id)
        
        if not mapped_ids:
            mapped_ids = self._semantic_search(element, test_cases)
        
        return mapped_ids
    
    def _is_related(self, element: SpecElement, test_case: GeneratedTestCase) -> bool:
        """判断规范元素与测试用例是否相关"""
        if test_case.spec_element_name == element.name:
            return True
        
        element_words = set(re.findall(r'\w+', element.name.lower()))
        test_words = set(re.findall(r'\w+', test_case.name.lower()))
        
        if element_words & test_words:
            return True
        
        if element.description:
            desc_words = set(re.findall(r'\w+', element.description.lower()))
            if desc_words & test_words:
                return True
        
        return False
    
    def _semantic_search(
        self,
        element: SpecElement,
        test_cases: List[GeneratedTestCase]
    ) -> List[str]:
        """语义搜索相关测试用例"""
        element_text = f"{element.name} {element.description}"
        similarities = []
        
        for tc in test_cases:
            tc_text = f"{tc.name} {tc.description}"
            similarity = self._semantic_analyzer.calculate_similarity(element_text, tc_text)
            similarities.append((tc.test_id, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return [tid for tid, sim in similarities[:3] if sim > 0.3]
    
    def get_uncovered_elements(
        self,
        mappings: Dict[str, List[str]]
    ) -> List[str]:
        """获取未覆盖的规范元素"""
        return [name for name, tests in mappings.items() if not tests]


class SemanticAnalyzer:
    """语义分析器"""
    
    def __init__(self):
        self._stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "must", "shall", "can", "need", "dare", "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by", "from", "as", "into", "through", "during", "before", "after", "above", "below", "between", "under", "again", "further", "then", "once", "and", "but", "or", "nor", "so", "yet", "both", "either", "neither", "not", "only", "own", "same", "than", "too", "very", "just"}
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的语义相似度"""
        words1 = self._tokenize(text1)
        words2 = self._tokenize(text2)
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _tokenize(self, text: str) -> Set[str]:
        """分词并过滤停用词"""
        words = set(re.findall(r'\w+', text.lower()))
        return words - self._stop_words


class TestResultFeedbackHandler:
    """测试结果到规范的反馈处理器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self._feedback_history: List[Dict[str, Any]] = []
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("TestResultFeedbackHandler")
        logger.setLevel(logging.INFO)
        return logger
    
    def process_feedback(
        self,
        spec: ParsedSpecification,
        test_results: Dict[str, Any],
        mappings: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        处理测试结果反馈到规范
        
        Args:
            spec: 规范对象
            test_results: 测试结果
            mappings: 规范到测试的映射
            
        Returns:
            Dict[str, Any]: 反馈报告
        """
        feedback_report = {
            "timestamp": datetime.now().isoformat(),
            "spec_id": spec.spec_id,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "element_feedback": {},
            "recommendations": []
        }
        
        tests = test_results.get("tests", {})
        feedback_report["total_tests"] = len(tests)
        
        for test_id, result in tests.items():
            status = result.get("status", "unknown")
            if status == "passed":
                feedback_report["passed_tests"] += 1
            elif status == "failed":
                feedback_report["failed_tests"] += 1
        
        for element_name, test_ids in mappings.items():
            element_feedback = self._analyze_element_feedback(
                element_name, test_ids, tests
            )
            feedback_report["element_feedback"][element_name] = element_feedback
        
        feedback_report["recommendations"] = self._generate_feedback_recommendations(
            feedback_report
        )
        
        self._feedback_history.append(feedback_report)
        
        return feedback_report
    
    def _analyze_element_feedback(
        self,
        element_name: str,
        test_ids: List[str],
        tests: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析单个元素的反馈"""
        passed = 0
        failed = 0
        errors = []
        
        for test_id in test_ids:
            result = tests.get(test_id, {})
            status = result.get("status", "unknown")
            
            if status == "passed":
                passed += 1
            elif status == "failed":
                failed += 1
                error_msg = result.get("error_message", "Unknown error")
                errors.append({
                    "test_id": test_id,
                    "error": error_msg[:200]
                })
        
        total = passed + failed
        pass_rate = passed / total * 100 if total > 0 else 0
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": pass_rate,
            "errors": errors[:5],
            "status": "healthy" if pass_rate >= 80 else "degraded" if pass_rate >= 50 else "critical"
        }
    
    def _generate_feedback_recommendations(
        self,
        feedback_report: Dict[str, Any]
    ) -> List[str]:
        """生成反馈建议"""
        recommendations = []
        
        pass_rate = feedback_report["passed_tests"] / feedback_report["total_tests"] * 100 \
            if feedback_report["total_tests"] > 0 else 0
        
        if pass_rate < 50:
            recommendations.append("测试通过率过低，建议检查规范定义是否清晰完整")
        elif pass_rate < 80:
            recommendations.append("测试通过率有待提高，建议检查失败的测试用例")
        
        critical_elements = [
            name for name, fb in feedback_report["element_feedback"].items()
            if fb["status"] == "critical"
        ]
        
        if critical_elements:
            recommendations.append(
                f"以下规范元素测试通过率极低，需要重点关注: {', '.join(critical_elements[:5])}"
            )
        
        return recommendations


class CoverageTracker:
    """覆盖率追踪器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self._coverage_history: List[Dict[str, Any]] = []
        self._baseline_coverage: Optional[float] = None
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("CoverageTracker")
        logger.setLevel(logging.INFO)
        return logger
    
    def track_coverage(
        self,
        spec: ParsedSpecification,
        test_cases: List[GeneratedTestCase],
        test_results: Optional[Dict[str, Any]] = None,
        mappings: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        追踪覆盖率
        
        Args:
            spec: 规范对象
            test_cases: 测试用例列表
            test_results: 测试结果
            mappings: 规范到测试的映射
            
        Returns:
            Dict[str, Any]: 覆盖率报告
        """
        if mappings is None:
            mappings = {}
            for tc in test_cases:
                element_name = tc.spec_element_name
                if element_name not in mappings:
                    mappings[element_name] = []
                mappings[element_name].append(tc.test_id)
        
        coverage_report = {
            "timestamp": datetime.now().isoformat(),
            "spec_id": spec.spec_id,
            "total_elements": len(spec.elements),
            "covered_elements": 0,
            "uncovered_elements": [],
            "element_coverage": {},
            "overall_coverage": 0.0,
            "trend": "stable"
        }
        
        for element in spec.elements:
            test_ids = mappings.get(element.name, [])
            
            if test_ids:
                coverage_report["covered_elements"] += 1
                coverage_pct = self._calculate_element_coverage(
                    element, test_ids, test_cases, test_results
                )
            else:
                coverage_pct = 0.0
                coverage_report["uncovered_elements"].append(element.name)
            
            coverage_report["element_coverage"][element.name] = {
                "test_count": len(test_ids),
                "coverage_percentage": coverage_pct,
                "status": "covered" if coverage_pct >= 80 else "partial" if coverage_pct > 0 else "uncovered"
            }
        
        coverage_report["overall_coverage"] = (
            coverage_report["covered_elements"] / coverage_report["total_elements"] * 100
            if coverage_report["total_elements"] > 0 else 0
        )
        
        if self._baseline_coverage is not None:
            diff = coverage_report["overall_coverage"] - self._baseline_coverage
            if diff > 5:
                coverage_report["trend"] = "improving"
            elif diff < -5:
                coverage_report["trend"] = "declining"
        
        self._baseline_coverage = coverage_report["overall_coverage"]
        self._coverage_history.append(coverage_report)
        
        return coverage_report
    
    def _calculate_element_coverage(
        self,
        element: SpecElement,
        test_ids: List[str],
        test_cases: List[GeneratedTestCase],
        test_results: Optional[Dict[str, Any]]
    ) -> float:
        """计算单个元素的覆盖率"""
        if not test_ids:
            return 0.0
        
        related_tests = [tc for tc in test_cases if tc.test_id in test_ids]
        
        test_types = set(tc.test_type for tc in related_tests)
        type_coverage = len(test_types) / len(TestType) * 50
        
        attribute_coverage = 0.0
        if element.attributes:
            tested_attrs = set()
            for tc in related_tests:
                test_content = f"{tc.arrange} {tc.act} {tc.assert_}".lower()
                for attr in element.attributes:
                    attr_name = attr.get("name", "")
                    if attr_name.lower() in test_content:
                        tested_attrs.add(attr_name)
            
            attribute_coverage = len(tested_attrs) / len(element.attributes) * 50
        
        return min(100.0, type_coverage + attribute_coverage)
    
    def get_coverage_trend(self, days: int = 7) -> Dict[str, Any]:
        """获取覆盖率趋势"""
        if len(self._coverage_history) < 2:
            return {"trend": "insufficient_data"}
        
        recent_history = self._coverage_history[-days:]
        
        coverages = [h["overall_coverage"] for h in recent_history]
        
        return {
            "trend": "improving" if coverages[-1] > coverages[0] else "declining" if coverages[-1] < coverages[0] else "stable",
            "start_coverage": coverages[0],
            "end_coverage": coverages[-1],
            "change": coverages[-1] - coverages[0],
            "data_points": len(coverages)
        }
    
    def identify_coverage_gaps(
        self,
        coverage_report: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """识别覆盖率缺口"""
        gaps = []
        
        for element_name, coverage_info in coverage_report["element_coverage"].items():
            if coverage_info["status"] == "uncovered":
                gaps.append({
                    "element": element_name,
                    "type": "no_coverage",
                    "severity": "high",
                    "suggestion": f"为元素 '{element_name}' 添加测试用例"
                })
            elif coverage_info["status"] == "partial":
                gaps.append({
                    "element": element_name,
                    "type": "partial_coverage",
                    "severity": "medium",
                    "suggestion": f"补充元素 '{element_name}' 的测试覆盖"
                })
        
        return gaps
    
    def run_cycle(
        self,
        spec_path: str,
        test_runner: Optional[callable] = None,
        code_generator: Optional[callable] = None,
        refactoring_handler: Optional[callable] = None,
        dry_run: bool = False,
        report_format: str = "json"
    ) -> Dict[str, Any]:
        self.logger.info("=" * 60)
        self.logger.info("开始 SDD-TDD 红绿蓝循环集成")
        self.logger.info("=" * 60)
        
        result = {
            "spec_path": spec_path,
            "started_at": datetime.now().isoformat(),
            "status": "in_progress",
            "mode": "red_green_blue_cycle"
        }
        
        try:
            spec, validation = self.parse_spec(spec_path)
            result["spec"] = {
                "id": spec.spec_id,
                "name": spec.spec_name,
                "version": spec.version,
                "elements_count": len(spec.elements)
            }
            result["validation"] = {
                "is_valid": validation.is_valid,
                "completeness_score": validation.completeness_score
            }
            
            if not validation.is_valid:
                result["status"] = "validation_failed"
                result["error"] = "规范验证失败"
                return result
            
            cycle_report = self.cycle_executor.execute_cycle(
                spec,
                test_runner=test_runner,
                code_generator=code_generator,
                refactoring_handler=refactoring_handler,
                dry_run=dry_run
            )
            
            report_file = self.cycle_report_generator.generate_report(
                cycle_report,
                format_type=report_format
            )
            
            result["cycle"] = {
                "report_id": cycle_report.report_id,
                "total_iterations": cycle_report.total_iterations,
                "completed_iterations": cycle_report.completed_iterations,
                "failed_iterations": cycle_report.failed_iterations,
                "success_rate": cycle_report.summary.get("success_rate", 0),
                "report_file": report_file
            }
            
            test_cases, test_file = self.generate_tests(spec)
            result["test_generation"] = {
                "test_cases_count": len(test_cases),
                "test_file": test_file
            }
            
            coverage_report = self.generate_coverage_report(spec, test_cases)
            result["coverage"] = {
                "report_id": coverage_report.report_id,
                "overall_coverage": coverage_report.overall_coverage
            }
            
            result["status"] = "completed"
            result["completed_at"] = datetime.now().isoformat()
            
            self.logger.info("=" * 60)
            self.logger.info("红绿蓝循环集成完成")
            self.logger.info(f"状态: {result['status']}")
            self.logger.info(f"迭代: {cycle_report.completed_iterations}/{cycle_report.total_iterations}")
            self.logger.info(f"成功率: {cycle_report.summary.get('success_rate', 0):.1f}%")
            self.logger.info("=" * 60)
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self.logger.error(f"循环集成失败: {e}")
        
        self._save_integration_result(result)
        
        return result
    
    def run_sdd_tdd_pipeline(
        self,
        spec_path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        options = options or {}
        
        self.logger.info("=" * 60)
        self.logger.info("开始 SDD-TDD 完整管道流程")
        self.logger.info("=" * 60)
        
        result = {
            "spec_path": spec_path,
            "started_at": datetime.now().isoformat(),
            "status": "in_progress",
            "mode": "full_pipeline",
            "phases": []
        }
        
        try:
            self.logger.info("\n[阶段 1] 规范解析与验证")
            spec, validation = self.parse_spec(spec_path)
            result["spec"] = {
                "id": spec.spec_id,
                "name": spec.spec_name,
                "version": spec.version,
                "elements_count": len(spec.elements)
            }
            result["phases"].append({
                "name": "parse",
                "status": "completed",
                "validation_score": validation.completeness_score
            })
            
            if not validation.is_valid:
                result["status"] = "validation_failed"
                result["error"] = "规范验证失败"
                return result
            
            self.logger.info("\n[阶段 2] 测试用例生成")
            test_cases, test_file = self.generate_tests(spec)
            result["test_generation"] = {
                "test_cases_count": len(test_cases),
                "test_file": test_file
            }
            result["phases"].append({
                "name": "generate_tests",
                "status": "completed",
                "test_count": len(test_cases)
            })
            
            if options.get("run_cycle", True):
                self.logger.info("\n[阶段 3] 红绿蓝循环执行")
                cycle_report = self.cycle_executor.execute_cycle(
                    spec,
                    dry_run=options.get("dry_run", False)
                )
                
                report_format = options.get("report_format", "html")
                report_file = self.cycle_report_generator.generate_report(
                    cycle_report,
                    format_type=report_format
                )
                
                result["cycle"] = {
                    "report_id": cycle_report.report_id,
                    "total_iterations": cycle_report.total_iterations,
                    "completed_iterations": cycle_report.completed_iterations,
                    "failed_iterations": cycle_report.failed_iterations,
                    "success_rate": cycle_report.summary.get("success_rate", 0),
                    "report_file": report_file
                }
                result["phases"].append({
                    "name": "cycle",
                    "status": "completed",
                    "iterations": cycle_report.total_iterations
                })
            
            self.logger.info("\n[阶段 4] 覆盖率分析")
            coverage_report = self.generate_coverage_report(spec, test_cases)
            result["coverage"] = {
                "report_id": coverage_report.report_id,
                "overall_coverage": coverage_report.overall_coverage,
                "recommendations": coverage_report.recommendations
            }
            result["phases"].append({
                "name": "coverage",
                "status": "completed",
                "coverage": coverage_report.overall_coverage
            })
            
            result["status"] = "completed"
            result["completed_at"] = datetime.now().isoformat()
            
            self.logger.info("\n" + "=" * 60)
            self.logger.info("SDD-TDD 管道流程完成")
            self.logger.info(f"状态: {result['status']}")
            self.logger.info(f"覆盖率: {coverage_report.overall_coverage:.1f}%")
            self.logger.info("=" * 60)
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self.logger.error(f"管道流程失败: {e}")
        
        self._save_integration_result(result)
        
        return result
    
    def get_cycle_state(self, report_id: str) -> Optional[CycleExecutionReport]:
        return self.cycle_executor.state_tracker.load_state(report_id)
    
    def resume_cycle(
        self,
        report_id: str,
        test_runner: Optional[callable] = None,
        code_generator: Optional[callable] = None,
        refactoring_handler: Optional[callable] = None
    ) -> CycleExecutionReport:
        self.logger.info(f"恢复循环执行: {report_id}")
        
        return self.cycle_executor.resume_cycle(
            report_id,
            test_runner=test_runner,
            code_generator=code_generator,
            refactoring_handler=refactoring_handler
        )
    
    def generate_cycle_report(
        self,
        report_id: str,
        format_type: str = "html"
    ) -> Optional[str]:
        cycle_report = self.get_cycle_state(report_id)
        
        if not cycle_report:
            self.logger.error(f"未找到循环报告: {report_id}")
            return None
        
        return self.cycle_report_generator.generate_report(cycle_report, format_type)
    
    def run_enhanced_integration(
        self,
        spec_path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """运行增强的SDD-TDD集成流程"""
        options = options or {}
        
        self.logger.info("=" * 60)
        self.logger.info("开始 SDD-TDD 增强集成流程")
        self.logger.info("=" * 60)
        
        result = {
            "spec_path": spec_path,
            "started_at": datetime.now().isoformat(),
            "status": "in_progress",
            "mode": "enhanced_integration",
            "phases": []
        }
        
        try:
            self.logger.info("\n[阶段 1] 规范解析与验证")
            spec, validation = self.parse_spec(spec_path)
            result["spec"] = {
                "id": spec.spec_id,
                "name": spec.spec_name,
                "version": spec.version,
                "elements_count": len(spec.elements)
            }
            result["phases"].append({
                "name": "parse",
                "status": "completed",
                "validation_score": validation.completeness_score
            })
            
            if not validation.is_valid:
                result["status"] = "validation_failed"
                result["error"] = "规范验证失败"
                return result
            
            self.logger.info("\n[阶段 2] 依赖分析")
            dependencies = self.dependency_analyzer.analyze_dependencies(spec)
            execution_order = self.dependency_analyzer.get_execution_order()
            result["dependency_analysis"] = {
                "total_elements": len(dependencies),
                "execution_order": execution_order,
                "circular_dependencies": [d.element_id for d in dependencies if d.is_circular]
            }
            result["phases"].append({
                "name": "dependency_analysis",
                "status": "completed"
            })
            
            self.logger.info("\n[阶段 3] 测试用例生成")
            test_cases, test_file = self.generate_tests(spec)
            result["test_generation"] = {
                "test_cases_count": len(test_cases),
                "test_file": test_file
            }
            result["phases"].append({
                "name": "generate_tests",
                "status": "completed",
                "test_count": len(test_cases)
            })
            
            self.logger.info("\n[阶段 4] 智能映射与追溯")
            mappings = self.integration_enhancer.create_intelligent_mapping(spec, test_cases)
            trace_matrix = self.integration_enhancer.generate_traceability_matrix(spec, test_cases)
            result["mapping"] = {
                "total_mappings": len(mappings),
                "aligned_count": sum(1 for m in mappings if m.integration_status == IntegrationStatus.ALIGNED),
                "traceability_score": trace_matrix.get("traceability_score", 0)
            }
            result["phases"].append({
                "name": "mapping",
                "status": "completed"
            })
            
            if options.get("run_cycle", True):
                self.logger.info("\n[阶段 5] 红绿蓝循环执行")
                cycle_report = self.cycle_executor.execute_cycle(
                    spec,
                    dry_run=options.get("dry_run", False)
                )
                
                report_format = options.get("report_format", "html")
                report_file = self.cycle_report_generator.generate_report(
                    cycle_report,
                    format_type=report_format
                )
                
                result["cycle"] = {
                    "report_id": cycle_report.report_id,
                    "total_iterations": cycle_report.total_iterations,
                    "completed_iterations": cycle_report.completed_iterations,
                    "failed_iterations": cycle_report.failed_iterations,
                    "success_rate": cycle_report.summary.get("success_rate", 0),
                    "report_file": report_file
                }
                result["phases"].append({
                    "name": "cycle",
                    "status": "completed",
                    "iterations": cycle_report.total_iterations
                })
            
            self.logger.info("\n[阶段 6] 覆盖率分析")
            coverage_report = self.generate_coverage_report(spec, test_cases)
            result["coverage"] = {
                "report_id": coverage_report.report_id,
                "overall_coverage": coverage_report.overall_coverage,
                "recommendations": coverage_report.recommendations
            }
            result["phases"].append({
                "name": "coverage",
                "status": "completed",
                "coverage": coverage_report.overall_coverage
            })
            
            self.logger.info("\n[阶段 7] 质量评估")
            test_quality = self.quality_assessor.assess_test_quality(test_cases)
            result["quality"] = {
                "test_quality": {
                    "grade": test_quality.overall_grade.value,
                    "score": test_quality.overall_score
                }
            }
            result["phases"].append({
                "name": "quality_assessment",
                "status": "completed"
            })
            
            result["status"] = "completed"
            result["completed_at"] = datetime.now().isoformat()
            
            self.logger.info("\n" + "=" * 60)
            self.logger.info("SDD-TDD 增强集成流程完成")
            self.logger.info(f"状态: {result['status']}")
            self.logger.info(f"覆盖率: {coverage_report.overall_coverage:.1f}%")
            self.logger.info(f"测试质量: {test_quality.overall_grade.value} ({test_quality.overall_score:.1f}%)")
            self.logger.info("=" * 60)
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self.logger.error(f"增强集成流程失败: {e}")
        
        self._save_integration_result(result)
        
        return result
    
    def assess_quality(
        self,
        code_content: Optional[str] = None,
        element: Optional[SpecElement] = None,
        test_cases: Optional[List[GeneratedTestCase]] = None,
        test_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行质量评估"""
        assessments = {}
        
        if code_content and element:
            assessments["code"] = self.quality_assessor.assess_code_quality(code_content, element)
        
        if test_cases:
            assessments["test"] = self.quality_assessor.assess_test_quality(test_cases, test_results)
        
        return assessments
    
    def get_integration_validations(
        self,
        spec: ParsedSpecification,
        test_cases: List[GeneratedTestCase]
    ) -> List[IntegrationValidation]:
        """获取集成验证结果"""
        return self.integration_enhancer.validate_integration(spec, test_cases)
    
    def get_fix_suggestions(
        self,
        test_results: Dict[str, Any],
        spec: ParsedSpecification
    ) -> List[AutoFixSuggestion]:
        """获取自动修复建议"""
        return self.auto_fix_analyzer.analyze_test_failures(test_results, spec)
    
    def _sanitize_name(self, name: str) -> str:
        sanitized = re.sub(r"[^\w\s]", "", name)
        return "_".join(sanitized.lower().split())
    
    def _save_parsed_spec(self, spec: ParsedSpecification) -> None:
        output_file = self.output_dir / "parsed_specs" / f"{spec.spec_id}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        spec_dict = {
            "spec_id": spec.spec_id,
            "spec_name": spec.spec_name,
            "version": spec.version,
            "source_path": spec.source_path,
            "source_format": spec.source_format,
            "interfaces": [
                {
                    "name": i.name,
                    "parameters": i.parameters,
                    "return_type": i.return_type,
                    "description": i.description,
                    "exceptions": i.exceptions
                }
                for i in spec.interfaces
            ],
            "data_models": [
                {
                    "name": m.name,
                    "attributes": m.attributes,
                    "description": m.description
                }
                for m in spec.data_models
            ],
            "behavior_rules": [
                {
                    "rule_id": r.rule_id,
                    "name": r.name,
                    "condition": r.condition,
                    "action": r.action,
                    "description": r.description
                }
                for r in spec.behavior_rules
            ],
            "constraints": spec.constraints,
            "elements_count": len(spec.elements)
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(spec_dict, f, ensure_ascii=False, indent=2)
    
    def _save_coverage_report(self, report: CoverageReport) -> None:
        output_file = self.output_dir / "coverage_reports" / f"{report.report_id}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        report_dict = {
            "report_id": report.report_id,
            "spec_id": report.spec_id,
            "generated_at": report.generated_at,
            "overall_coverage": report.overall_coverage,
            "element_coverage": {
                name: {
                    "spec_element_id": mapping.spec_element_id,
                    "spec_element_name": mapping.spec_element_name,
                    "test_ids": mapping.test_ids,
                    "coverage_level": mapping.coverage_level.value,
                    "coverage_percentage": mapping.coverage_percentage,
                    "untested_aspects": mapping.untested_aspects
                }
                for name, mapping in report.element_coverage.items()
            },
            "trace_matrix": {
                "spec_to_tests": report.trace_matrix.spec_to_tests,
                "test_to_spec": report.trace_matrix.test_to_spec
            },
            "recommendations": report.recommendations
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)
    
    def _save_validation_result(
        self,
        spec_id: str,
        validation: ValidationResult
    ) -> None:
        output_file = self.output_dir / "validation_results" / f"{spec_id}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        validation_dict = {
            "spec_id": spec_id,
            "is_valid": validation.is_valid,
            "completeness_score": validation.completeness_score,
            "errors": validation.errors,
            "warnings": validation.warnings,
            "info": validation.info,
            "validated_at": datetime.now().isoformat()
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(validation_dict, f, ensure_ascii=False, indent=2)
    
    def _save_integration_result(self, result: Dict[str, Any]) -> None:
        output_file = self.output_dir / "integration_results" / f"{result['started_at'].replace(':', '-')}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)


class QualityAssessor:
    """循环结果质量评估器 - 评估代码、测试和重构质量"""
    
    BENCHMARKS = {
        "code": {
            "complexity": {"excellent": 5, "good": 10, "acceptable": 15, "poor": 20},
            "maintainability": {"excellent": 80, "good": 60, "acceptable": 40, "poor": 20},
            "testability": {"excellent": 90, "good": 70, "acceptable": 50, "poor": 30}
        },
        "test": {
            "assertion_density": {"excellent": 3, "good": 2, "acceptable": 1, "poor": 0.5},
            "coverage": {"excellent": 90, "good": 70, "acceptable": 50, "poor": 30},
            "reliability": {"excellent": 95, "good": 85, "acceptable": 70, "poor": 50}
        },
        "refactoring": {
            "behavior_preservation": {"excellent": 100, "good": 95, "acceptable": 90, "poor": 80},
            "code_improvement": {"excellent": 30, "good": 20, "acceptable": 10, "poor": 0}
        }
    }
    
    def __init__(self, output_dir: Path, logger: Optional[logging.Logger] = None):
        self.output_dir = output_dir
        self.assessments_dir = output_dir / "quality_assessments"
        self.assessments_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger or self._setup_logger()
        self.assessment_history: List[QualityAssessment] = []
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("QualityAssessor")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def assess_code_quality(
        self,
        code_content: str,
        element: SpecElement
    ) -> QualityAssessment:
        """评估代码质量"""
        assessment_id = f"CODE-QA-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        metrics = self._calculate_code_metrics(code_content)
        
        dimensions = {
            "complexity": self._normalize_complexity(metrics.complexity_score),
            "maintainability": metrics.maintainability_index / 100,
            "testability": metrics.testability_score / 100,
            "coupling": 1 - metrics.coupling_score / 10,
            "cohesion": metrics.cohesion_score / 100,
            "duplication": 1 - metrics.duplication_ratio,
            "documentation": metrics.documentation_coverage / 100,
            "naming": metrics.naming_quality / 100
        }
        
        overall_score = sum(dimensions.values()) / len(dimensions) * 100
        
        issues = self._identify_code_issues(metrics, dimensions)
        strengths = self._identify_code_strengths(dimensions)
        improvement_areas = self._identify_improvement_areas(dimensions)
        
        overall_grade = self._determine_grade(overall_score)
        
        benchmark_comparison = self._compare_with_benchmarks("code", dimensions)
        
        assessment = QualityAssessment(
            assessment_id=assessment_id,
            target_type="code",
            target_id=element.name,
            overall_grade=overall_grade,
            overall_score=overall_score,
            dimensions=dimensions,
            issues=issues,
            strengths=strengths,
            improvement_areas=improvement_areas,
            benchmark_comparison=benchmark_comparison
        )
        
        self.assessment_history.append(assessment)
        self._save_assessment(assessment)
        
        self.logger.info(f"代码质量评估完成: {element.name} - {overall_grade.value} ({overall_score:.1f}%)")
        
        return assessment
    
    def _calculate_code_metrics(self, code: str) -> CodeQualityMetrics:
        """计算代码质量指标"""
        lines = code.split('\n')
        non_empty_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        
        complexity_score = self._estimate_complexity(code)
        
        total_lines = len(non_empty_lines)
        code_lines = len([l for l in non_empty_lines if not l.strip().startswith(('"""', "'''"))])
        maintainability_index = max(0, 100 - (complexity_score * 5) - (total_lines / 10))
        
        testability_score = self._estimate_testability(code)
        
        coupling_score = self._estimate_coupling(code)
        
        cohesion_score = self._estimate_cohesion(code)
        
        duplication_ratio = self._estimate_duplication(code)
        
        doc_lines = len([l for l in lines if '"""' in l or "'''" in l or l.strip().startswith('#')])
        documentation_coverage = min(100, (doc_lines / max(1, total_lines)) * 100 * 2)
        
        naming_quality = self._estimate_naming_quality(code)
        
        return CodeQualityMetrics(
            complexity_score=complexity_score,
            maintainability_index=maintainability_index,
            testability_score=testability_score,
            coupling_score=coupling_score,
            cohesion_score=cohesion_score,
            duplication_ratio=duplication_ratio,
            documentation_coverage=documentation_coverage,
            naming_quality=naming_quality
        )
    
    def _estimate_complexity(self, code: str) -> float:
        """估算代码复杂度"""
        complexity = 1
        
        complexity += code.count('if ')
        complexity += code.count('elif ')
        complexity += code.count('for ')
        complexity += code.count('while ')
        complexity += code.count('and ')
        complexity += code.count('or ')
        complexity += code.count('try:')
        complexity += code.count('except')
        
        return float(complexity)
    
    def _normalize_complexity(self, complexity: float) -> float:
        """归一化复杂度分数"""
        if complexity <= 5:
            return 1.0
        elif complexity <= 10:
            return 0.8
        elif complexity <= 15:
            return 0.6
        elif complexity <= 20:
            return 0.4
        else:
            return 0.2
    
    def _estimate_testability(self, code: str) -> float:
        """估算可测试性"""
        score = 100.0
        
        if 'global ' in code:
            score -= 20
        
        if code.count('import ') > 10:
            score -= 10
        
        if 'self.' in code:
            score += 10
        
        if 'def ' in code:
            function_count = code.count('def ')
            if function_count > 0:
                score += min(20, function_count * 5)
        
        return max(0, min(100, score))
    
    def _estimate_coupling(self, code: str) -> float:
        """估算耦合度"""
        coupling = 0
        
        coupling += code.count('import ')
        coupling += code.count('from ')
        
        coupling -= code.count('self.')
        
        return max(0, coupling)
    
    def _estimate_cohesion(self, code: str) -> float:
        """估算内聚度"""
        methods = code.split('def ')
        if len(methods) <= 1:
            return 100.0
        
        method_names = []
        for method in methods[1:]:
            first_line = method.split('\n')[0]
            name_match = re.match(r'(\w+)\s*\(', first_line)
            if name_match:
                method_names.append(name_match.group(1))
        
        if not method_names:
            return 50.0
        
        self_count = sum(1 for m in method_names if m.startswith('_'))
        public_count = len(method_names) - self_count
        
        if public_count <= 3:
            return 90.0
        elif public_count <= 5:
            return 70.0
        else:
            return 50.0
    
    def _estimate_duplication(self, code: str) -> float:
        """估算代码重复率"""
        lines = [l.strip() for l in code.split('\n') if l.strip() and not l.strip().startswith('#')]
        
        if not lines:
            return 0.0
        
        unique_lines = set(lines)
        duplication = 1 - (len(unique_lines) / len(lines))
        
        return duplication
    
    def _estimate_naming_quality(self, code: str) -> float:
        """估算命名质量"""
        score = 100.0
        
        single_char_vars = re.findall(r'\b([a-z])\s*=', code)
        if len(single_char_vars) > 3:
            score -= len(single_char_vars) * 5
        
        function_names = re.findall(r'def\s+(\w+)\s*\(', code)
        for name in function_names:
            if len(name) < 3:
                score -= 5
            if not re.match(r'^[a-z_][a-z0-9_]*$', name):
                score -= 3
        
        return max(0, score)
    
    def _identify_code_issues(
        self,
        metrics: CodeQualityMetrics,
        dimensions: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """识别代码问题"""
        issues = []
        
        if dimensions["complexity"] < 0.5:
            issues.append({
                "type": "high_complexity",
                "severity": "high",
                "message": "代码复杂度过高，建议拆分",
                "metric_value": metrics.complexity_score
            })
        
        if dimensions["maintainability"] < 0.5:
            issues.append({
                "type": "low_maintainability",
                "severity": "medium",
                "message": "可维护性较低，建议重构",
                "metric_value": metrics.maintainability_index
            })
        
        if dimensions["duplication"] < 0.8:
            issues.append({
                "type": "code_duplication",
                "severity": "medium",
                "message": "存在代码重复，建议提取公共方法",
                "metric_value": metrics.duplication_ratio
            })
        
        if dimensions["documentation"] < 0.3:
            issues.append({
                "type": "insufficient_documentation",
                "severity": "low",
                "message": "文档覆盖不足",
                "metric_value": metrics.documentation_coverage
            })
        
        return issues
    
    def _identify_code_strengths(self, dimensions: Dict[str, float]) -> List[str]:
        """识别代码优点"""
        strengths = []
        
        if dimensions["complexity"] >= 0.8:
            strengths.append("代码结构清晰，复杂度控制良好")
        
        if dimensions["testability"] >= 0.7:
            strengths.append("代码可测试性高")
        
        if dimensions["cohesion"] >= 0.8:
            strengths.append("模块内聚度高")
        
        if dimensions["naming"] >= 0.8:
            strengths.append("命名规范，可读性好")
        
        return strengths
    
    def _identify_improvement_areas(self, dimensions: Dict[str, float]) -> List[str]:
        """识别改进领域"""
        areas = []
        
        sorted_dims = sorted(dimensions.items(), key=lambda x: x[1])
        
        for dim_name, score in sorted_dims[:3]:
            if score < 0.7:
                areas.append(f"需要改进: {dim_name} (当前: {score*100:.1f}%)")
        
        return areas
    
    def assess_test_quality(
        self,
        test_cases: List[GeneratedTestCase],
        test_results: Optional[Dict[str, Any]] = None
    ) -> QualityAssessment:
        """评估测试质量"""
        assessment_id = f"TEST-QA-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        metrics = self._calculate_test_metrics(test_cases, test_results)
        
        dimensions = {
            "assertion_density": min(1.0, metrics.assertion_density / 3),
            "independence": metrics.test_independence / 100,
            "coverage": metrics.test_coverage / 100,
            "readability": metrics.test_readability / 100,
            "speed": metrics.test_speed / 100,
            "reliability": metrics.test_reliability / 100,
            "boundary_coverage": metrics.boundary_coverage / 100,
            "exception_coverage": metrics.exception_coverage / 100
        }
        
        overall_score = sum(dimensions.values()) / len(dimensions) * 100
        
        issues = self._identify_test_issues(metrics, dimensions)
        strengths = self._identify_test_strengths(dimensions)
        improvement_areas = self._identify_improvement_areas(dimensions)
        
        overall_grade = self._determine_grade(overall_score)
        
        benchmark_comparison = self._compare_with_benchmarks("test", dimensions)
        
        assessment = QualityAssessment(
            assessment_id=assessment_id,
            target_type="test",
            target_id="all_tests",
            overall_grade=overall_grade,
            overall_score=overall_score,
            dimensions=dimensions,
            issues=issues,
            strengths=strengths,
            improvement_areas=improvement_areas,
            benchmark_comparison=benchmark_comparison
        )
        
        self.assessment_history.append(assessment)
        self._save_assessment(assessment)
        
        self.logger.info(f"测试质量评估完成 - {overall_grade.value} ({overall_score:.1f}%)")
        
        return assessment
    
    def _calculate_test_metrics(
        self,
        test_cases: List[GeneratedTestCase],
        test_results: Optional[Dict[str, Any]]
    ) -> TestQualityMetrics:
        """计算测试质量指标"""
        if not test_cases:
            return TestQualityMetrics()
        
        total_assertions = 0
        for tc in test_cases:
            total_assertions += tc.assert_.lower().count('assert')
        
        assertion_density = total_assertions / len(test_cases)
        
        test_independence = 90.0
        
        test_coverage = min(100, len(test_cases) * 10)
        
        readability = 80.0
        
        test_speed = 85.0
        
        if test_results:
            passed = test_results.get("passed", 0)
            total = passed + test_results.get("failed", 0)
            test_reliability = (passed / total * 100) if total > 0 else 0
        else:
            test_reliability = 100.0
        
        boundary_tests = sum(1 for tc in test_cases if tc.test_type == TestType.BOUNDARY)
        boundary_coverage = (boundary_tests / len(test_cases) * 100) if test_cases else 0
        
        negative_tests = sum(1 for tc in test_cases if tc.test_type == TestType.NEGATIVE)
        exception_coverage = (negative_tests / len(test_cases) * 100) if test_cases else 0
        
        return TestQualityMetrics(
            assertion_density=assertion_density,
            test_independence=test_independence,
            test_coverage=test_coverage,
            test_readability=readability,
            test_speed=test_speed,
            test_reliability=test_reliability,
            boundary_coverage=boundary_coverage,
            exception_coverage=exception_coverage
        )
    
    def _identify_test_issues(
        self,
        metrics: TestQualityMetrics,
        dimensions: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """识别测试问题"""
        issues = []
        
        if dimensions["assertion_density"] < 0.5:
            issues.append({
                "type": "low_assertion_density",
                "severity": "medium",
                "message": "断言密度较低，建议增加更多验证点"
            })
        
        if dimensions["boundary_coverage"] < 0.3:
            issues.append({
                "type": "insufficient_boundary_tests",
                "severity": "medium",
                "message": "边界条件测试不足"
            })
        
        if dimensions["exception_coverage"] < 0.3:
            issues.append({
                "type": "insufficient_exception_tests",
                "severity": "high",
                "message": "异常情况测试不足"
            })
        
        return issues
    
    def _identify_test_strengths(self, dimensions: Dict[str, float]) -> List[str]:
        """识别测试优点"""
        strengths = []
        
        if dimensions["assertion_density"] >= 0.7:
            strengths.append("断言充分，验证全面")
        
        if dimensions["reliability"] >= 0.9:
            strengths.append("测试可靠性高")
        
        if dimensions["independence"] >= 0.9:
            strengths.append("测试独立性好")
        
        return strengths


class SpecToTestIntelligentMapper:
    """规范到测试的智能映射器
    
    增强功能:
    1. 从SDD规范自动提取测试场景
    2. 根据接口定义生成API测试
    3. 根据数据模型生成数据验证测试
    4. 根据行为规则生成业务逻辑测试
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self._mapping_cache: Dict[str, Any] = {}
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("SpecToTestIntelligentMapper")
        logger.setLevel(logging.INFO)
        return logger
    
    def extract_test_scenarios(self, spec: ParsedSpecification) -> List[Dict[str, Any]]:
        """从SDD规范自动提取测试场景"""
        scenarios = []
        
        for iface in spec.interfaces:
            scenarios.extend(self._extract_interface_scenarios(iface, spec))
        
        for model in spec.data_models:
            scenarios.extend(self._extract_model_scenarios(model, spec))
        
        for rule in spec.behavior_rules:
            scenarios.extend(self._extract_rule_scenarios(rule, spec))
        
        self.logger.info(f"从规范提取了 {len(scenarios)} 个测试场景")
        return scenarios
    
    def _extract_interface_scenarios(
        self,
        iface: InterfaceDefinition,
        spec: ParsedSpecification
    ) -> List[Dict[str, Any]]:
        """从接口定义提取测试场景"""
        scenarios = []
        
        scenarios.append({
            "id": f"SCENARIO-{iface.name}-valid-call",
            "type": "api_test",
            "target": iface.name,
            "description": f"测试接口 {iface.name} 的正常调用",
            "given": f"准备有效的输入参数",
            "when": f"调用接口 {iface.name}",
            "then": f"返回类型为 {iface.return_type}",
            "priority": "high",
            "test_type": TestType.UNIT
        })
        
        for exc in iface.exceptions:
            scenarios.append({
                "id": f"SCENARIO-{iface.name}-exception-{exc}",
                "type": "exception_test",
                "target": iface.name,
                "description": f"测试接口 {iface.name} 抛出 {exc} 异常",
                "given": "准备触发异常的输入",
                "when": f"调用接口 {iface.name}",
                "then": f"抛出 {exc} 异常",
                "priority": "high",
                "test_type": TestType.NEGATIVE
            })
        
        scenarios.append({
            "id": f"SCENARIO-{iface.name}-boundary",
            "type": "boundary_test",
            "target": iface.name,
            "description": f"测试接口 {iface.name} 的边界条件",
            "given": "准备边界值输入",
            "when": f"调用接口 {iface.name}",
            "then": "正确处理边界情况",
            "priority": "medium",
            "test_type": TestType.BOUNDARY
        })
        
        return scenarios
    
    def _extract_model_scenarios(
        self,
        model: DataModel,
        spec: ParsedSpecification
    ) -> List[Dict[str, Any]]:
        """从数据模型提取测试场景"""
        scenarios = []
        
        scenarios.append({
            "id": f"SCENARIO-{model.name}-creation",
            "type": "data_validation_test",
            "target": model.name,
            "description": f"测试数据模型 {model.name} 的创建",
            "given": f"准备有效的属性值",
            "when": f"创建 {model.name} 实例",
            "then": "实例创建成功且属性正确",
            "priority": "high",
            "test_type": TestType.UNIT
        })
        
        required_attrs = [a for a in model.attributes if a.get("required", True)]
        if required_attrs:
            scenarios.append({
                "id": f"SCENARIO-{model.name}-missing-required",
                "type": "validation_test",
                "target": model.name,
                "description": f"测试缺少必填属性时的验证",
                "given": f"缺少必填属性",
                "when": f"创建 {model.name} 实例",
                "then": "抛出验证错误",
                "priority": "high",
                "test_type": TestType.NEGATIVE
            })
        
        for attr in model.attributes:
            constraints = attr.get("constraints", {})
            if constraints:
                scenarios.append({
                    "id": f"SCENARIO-{model.name}-{attr['name']}-constraint",
                    "type": "constraint_test",
                    "target": model.name,
                    "description": f"测试属性 {attr['name']} 的约束条件",
                    "given": f"准备违反约束的 {attr['name']} 值",
                    "when": f"创建 {model.name} 实例",
                    "then": "约束验证正确执行",
                    "priority": "medium",
                    "test_type": TestType.BOUNDARY
                })
        
        return scenarios
    
    def _extract_rule_scenarios(
        self,
        rule: BehaviorRule,
        spec: ParsedSpecification
    ) -> List[Dict[str, Any]]:
        """从行为规则提取测试场景"""
        scenarios = []
        
        scenarios.append({
            "id": f"SCENARIO-{rule.rule_id}-triggered",
            "type": "business_logic_test",
            "target": rule.name,
            "description": f"测试行为规则 {rule.name} 被触发",
            "given": f"设置条件: {rule.condition}",
            "when": "触发规则",
            "then": f"执行动作: {rule.action}",
            "priority": "high",
            "test_type": TestType.UNIT
        })
        
        scenarios.append({
            "id": f"SCENARIO-{rule.rule_id}-not-triggered",
            "type": "negative_test",
            "target": rule.name,
            "description": f"测试行为规则 {rule.name} 未被触发",
            "given": f"不满足条件: {rule.condition}",
            "when": "检查规则状态",
            "then": "动作未执行",
            "priority": "medium",
            "test_type": TestType.NEGATIVE
        })
        
        return scenarios
    
    def generate_api_tests(
        self,
        iface: InterfaceDefinition,
        spec: ParsedSpecification
    ) -> List[GeneratedTestCase]:
        """根据接口定义生成API测试"""
        test_cases = []
        test_counter = 0
        
        test_counter += 1
        test_cases.append(GeneratedTestCase(
            test_id=f"API-TEST-{iface.name}-{test_counter:03d}",
            name=f"test_{iface.name.lower()}_api_call",
            test_type=TestType.UNIT,
            spec_element_id=iface.name,
            spec_element_name=iface.name,
            arrange=f"# 准备API调用参数: {', '.join(p['name'] for p in iface.parameters)}",
            act=f"# 调用API: {iface.name}",
            assert_=f"# 验证响应类型: {iface.return_type}",
            description=f"API测试: {iface.name}",
            tags=["api", "unit"],
            priority=1
        ))
        
        return test_cases
    
    def generate_data_validation_tests(
        self,
        model: DataModel,
        spec: ParsedSpecification
    ) -> List[GeneratedTestCase]:
        """根据数据模型生成数据验证测试"""
        test_cases = []
        test_counter = 0
        
        test_counter += 1
        test_cases.append(GeneratedTestCase(
            test_id=f"DATA-TEST-{model.name}-{test_counter:03d}",
            name=f"test_{model.name.lower()}_validation",
            test_type=TestType.UNIT,
            spec_element_id=model.name,
            spec_element_name=model.name,
            arrange=f"# 准备数据: {', '.join(a['name'] for a in model.attributes)}",
            act=f"# 验证数据模型: {model.name}",
            assert_="# 验证数据有效性",
            description=f"数据验证测试: {model.name}",
            tags=["data", "validation"],
            priority=1
        ))
        
        return test_cases
    
    def generate_business_logic_tests(
        self,
        rule: BehaviorRule,
        spec: ParsedSpecification
    ) -> List[GeneratedTestCase]:
        """根据行为规则生成业务逻辑测试"""
        test_cases = []
        test_counter = 0
        
        test_counter += 1
        test_cases.append(GeneratedTestCase(
            test_id=f"BIZ-TEST-{rule.rule_id}-{test_counter:03d}",
            name=f"test_{rule.name.lower()}_business_rule",
            test_type=TestType.UNIT,
            spec_element_id=rule.rule_id,
            spec_element_name=rule.name,
            arrange=f"# 设置条件: {rule.condition}",
            act=f"# 执行业务规则: {rule.name}",
            assert_=f"# 验证动作: {rule.action}",
            description=f"业务逻辑测试: {rule.name}",
            tags=["business", "logic"],
            priority=1
        ))
        
        return test_cases


class TestToCodeGenerator:
    """测试到代码的自动生成器
    
    增强功能:
    1. 分析测试用例提取功能需求
    2. 生成最小实现代码
    3. 支持多种编程语言
    4. 自动处理依赖关系
    """
    
    LANGUAGE_TEMPLATES = {
        "python": {
            "class": "class {class_name}:\n    \"\"\"{description}\"\"\"\n    \n    {methods}\n",
            "method": "def {method_name}(self, {params}):\n    \"\"\"{description}\"\"\"\n    {body}\n",
            "function": "def {function_name}({params}):\n    \"\"\"{description}\"\"\"\n    {body}\n"
        },
        "typescript": {
            "class": "export class {class_name} {{\n    {properties}\n    \n    {methods}\n}}\n",
            "method": "{method_name}({params}): {return_type} {{\n    {body}\n}}\n",
            "function": "export function {function_name}({params}): {return_type} {{\n    {body}\n}}\n"
        },
        "java": {
            "class": "public class {class_name} {{\n    {properties}\n    \n    {methods}\n}}\n",
            "method": "public {return_type} {method_name}({params}) {{\n    {body}\n}}\n",
            "function": "public static {return_type} {function_name}({params}) {{\n    {body}\n}}\n"
        }
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self._generated_code_cache: Dict[str, str] = {}
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("TestToCodeGenerator")
        logger.setLevel(logging.INFO)
        return logger
    
    def extract_requirements_from_tests(
        self,
        test_cases: List[GeneratedTestCase]
    ) -> List[Dict[str, Any]]:
        """分析测试用例提取功能需求"""
        requirements = []
        
        for tc in test_cases:
            requirement = {
                "id": f"REQ-{tc.test_id}",
                "name": tc.name,
                "type": tc.test_type.value,
                "description": tc.description,
                "inputs": self._extract_inputs_from_arrange(tc.arrange),
                "outputs": self._extract_outputs_from_assert(tc.assert_),
                "behavior": self._extract_behavior_from_act(tc.act),
                "priority": tc.priority
            }
            requirements.append(requirement)
        
        self.logger.info(f"从测试用例提取了 {len(requirements)} 个功能需求")
        return requirements
    
    def _extract_inputs_from_arrange(self, arrange: str) -> List[str]:
        """从Arrange部分提取输入"""
        inputs = []
        patterns = [
            r"参数[：:]\s*(.+)",
            r"输入[：:]\s*(.+)",
            r"准备[：:]\s*(.+)",
            r"数据[：:]\s*(.+)"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, arrange)
            inputs.extend(matches)
        
        return inputs
    
    def _extract_outputs_from_assert(self, assert_: str) -> List[str]:
        """从Assert部分提取输出"""
        outputs = []
        patterns = [
            r"返回[：:]\s*(.+)",
            r"验证[：:]\s*(.+)",
            r"结果[：:]\s*(.+)"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, assert_)
            outputs.extend(matches)
        
        return outputs
    
    def _extract_behavior_from_act(self, act: str) -> str:
        """从Act部分提取行为"""
        return act.replace("#", "").strip()
    
    def generate_minimal_implementation(
        self,
        test_cases: List[GeneratedTestCase],
        language: str = "python",
        class_name: Optional[str] = None
    ) -> str:
        """生成最小实现代码"""
        if not test_cases:
            return ""
        
        requirements = self.extract_requirements_from_tests(test_cases)
        
        if not class_name:
            class_name = self._infer_class_name(test_cases)
        
        methods = []
        for req in requirements:
            method_code = self._generate_method(req, language)
            methods.append(method_code)
        
        template = self.LANGUAGE_TEMPLATES.get(language, self.LANGUAGE_TEMPLATES["python"])
        class_template = template.get("class", "")
        
        code = class_template.format(
            class_name=class_name,
            description="自动生成的最小实现",
            methods="\n    ".join(methods),
            properties=""
        )
        
        cache_key = f"{class_name}_{language}"
        self._generated_code_cache[cache_key] = code
        
        self.logger.info(f"生成了 {language} 代码: {class_name}")
        return code
    
    def _generate_method(self, requirement: Dict[str, Any], language: str) -> str:
        """生成方法代码"""
        template = self.LANGUAGE_TEMPLATES.get(language, self.LANGUAGE_TEMPLATES["python"])
        method_template = template.get("method", "")
        
        method_name = requirement["name"].replace("test_", "")
        params = ", ".join(requirement.get("inputs", [])) or ""
        body = self._generate_method_body(requirement, language)
        
        return method_template.format(
            method_name=method_name,
            params=params,
            return_type="Any",
            description=requirement["description"],
            body=body
        )
    
    def _generate_method_body(self, requirement: Dict[str, Any], language: str) -> str:
        """生成方法体"""
        if language == "python":
            if requirement["type"] == "negative":
                return "raise NotImplementedError('待实现')"
            return "pass  # TODO: 实现功能"
        elif language == "typescript":
            if requirement["type"] == "negative":
                return "throw new Error('Not implemented');"
            return "// TODO: 实现功能\nreturn null;"
        elif language == "java":
            if requirement["type"] == "negative":
                return 'throw new UnsupportedOperationException("待实现");'
            return "// TODO: 实现功能\nreturn null;"
        return "pass"
    
    def _infer_class_name(self, test_cases: List[GeneratedTestCase]) -> str:
        """推断类名"""
        if test_cases:
            first_name = test_cases[0].spec_element_name
            return "".join(word.capitalize() for word in first_name.split("_"))
        return "GeneratedClass"
    
    def handle_dependencies(
        self,
        test_cases: List[GeneratedTestCase],
        spec: ParsedSpecification
    ) -> Dict[str, List[str]]:
        """自动处理依赖关系"""
        dependencies = {}
        
        for tc in test_cases:
            element_name = tc.spec_element_name
            
            for element in spec.elements:
                if element.name == element_name:
                    deps = []
                    
                    for attr in element.attributes:
                        attr_type = attr.get("type", "")
                        for model in spec.data_models:
                            if model.name.lower() in attr_type.lower():
                                deps.append(model.name)
                    
                    dependencies[element_name] = deps
        
        return dependencies
    
    def generate_with_dependencies(
        self,
        test_cases: List[GeneratedTestCase],
        spec: ParsedSpecification,
        language: str = "python"
    ) -> Dict[str, str]:
        """生成代码并处理依赖"""
        dependencies = self.handle_dependencies(test_cases, spec)
        
        generated_files = {}
        
        sorted_elements = self._topological_sort(dependencies)
        
        for element_name in sorted_elements:
            element_tests = [tc for tc in test_cases if tc.spec_element_name == element_name]
            if element_tests:
                code = self.generate_minimal_implementation(
                    element_tests,
                    language,
                    class_name=element_name
                )
                generated_files[element_name] = code
        
        return generated_files
    
    def _topological_sort(self, dependencies: Dict[str, List[str]]) -> List[str]:
        """拓扑排序"""
        visited = set()
        result = []
        
        def visit(node):
            if node in visited:
                return
            visited.add(node)
            for dep in dependencies.get(node, []):
                visit(dep)
            result.append(node)
        
        for node in dependencies:
            visit(node)
        
        return result


class CodeToSpecVerifier:
    """代码到规范的逆向验证器
    
    增强功能:
    1. 从代码提取接口信息
    2. 与SDD规范对比
    3. 检测规范与实现的不一致
    4. 生成差异报告
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self._verification_cache: Dict[str, Any] = {}
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("CodeToSpecVerifier")
        logger.setLevel(logging.INFO)
        return logger
    
    def extract_interface_from_code(
        self,
        code_content: str,
        language: str = "python"
    ) -> Dict[str, Any]:
        """从代码提取接口信息"""
        interface_info = {
            "classes": [],
            "functions": [],
            "methods": [],
            "imports": []
        }
        
        if language == "python":
            interface_info["classes"] = self._extract_python_classes(code_content)
            interface_info["functions"] = self._extract_python_functions(code_content)
            interface_info["imports"] = self._extract_python_imports(code_content)
        elif language == "typescript":
            interface_info["classes"] = self._extract_typescript_classes(code_content)
            interface_info["functions"] = self._extract_typescript_functions(code_content)
        elif language == "java":
            interface_info["classes"] = self._extract_java_classes(code_content)
        
        return interface_info
    
    def _extract_python_classes(self, code: str) -> List[Dict[str, Any]]:
        """提取Python类"""
        classes = []
        class_pattern = r"class\s+(\w+)(?:\(([^)]*)\))?:\s*(?:\"\"\"([^\"]*)\"\"\")?"
        
        for match in re.finditer(class_pattern, code):
            class_info = {
                "name": match.group(1),
                "base_class": match.group(2).strip() if match.group(2) else None,
                "description": match.group(3) or "",
                "methods": []
            }
            
            class_body = self._extract_class_body(code, match.start())
            method_pattern = r"def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^:]+))?:"
            
            for method_match in re.finditer(method_pattern, class_body):
                class_info["methods"].append({
                    "name": method_match.group(1),
                    "params": method_match.group(2),
                    "return_type": method_match.group(3).strip() if method_match.group(3) else None
                })
            
            classes.append(class_info)
        
        return classes
    
    def _extract_class_body(self, code: str, start_pos: int) -> str:
        """提取类体"""
        lines = code[start_pos:].split("\n")
        body_lines = []
        
        for i, line in enumerate(lines[1:], 1):
            if line and not line.startswith("    ") and not line.startswith("\t"):
                break
            body_lines.append(line)
        
        return "\n".join(body_lines)
    
    def _extract_python_functions(self, code: str) -> List[Dict[str, Any]]:
        """提取Python函数"""
        functions = []
        func_pattern = r"^def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^:]+))?:"
        
        for match in re.finditer(func_pattern, code, re.MULTILINE):
            functions.append({
                "name": match.group(1),
                "params": match.group(2),
                "return_type": match.group(3).strip() if match.group(3) else None
            })
        
        return functions
    
    def _extract_python_imports(self, code: str) -> List[str]:
        """提取Python导入"""
        imports = []
        import_pattern = r"^(?:import|from)\s+.+$"
        
        for match in re.finditer(import_pattern, code, re.MULTILINE):
            imports.append(match.group(0))
        
        return imports
    
    def _extract_typescript_classes(self, code: str) -> List[Dict[str, Any]]:
        """提取TypeScript类"""
        classes = []
        class_pattern = r"(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{"
        
        for match in re.finditer(class_pattern, code):
            classes.append({
                "name": match.group(1),
                "base_class": match.group(2),
                "methods": []
            })
        
        return classes
    
    def _extract_typescript_functions(self, code: str) -> List[Dict[str, Any]]:
        """提取TypeScript函数"""
        functions = []
        func_pattern = r"(?:export\s+)?function\s+(\w+)\s*\(([^)]*)\)(?:\s*:\s*([^{\s]+))?"
        
        for match in re.finditer(func_pattern, code):
            functions.append({
                "name": match.group(1),
                "params": match.group(2),
                "return_type": match.group(3)
            })
        
        return functions
    
    def _extract_java_classes(self, code: str) -> List[Dict[str, Any]]:
        """提取Java类"""
        classes = []
        class_pattern = r"(?:public|private|protected)?\s*class\s+(\w+)(?:\s+extends\s+(\w+))?"
        
        for match in re.finditer(class_pattern, code):
            classes.append({
                "name": match.group(1),
                "base_class": match.group(2),
                "methods": []
            })
        
        return classes
    
    def compare_with_spec(
        self,
        code_interface: Dict[str, Any],
        spec: ParsedSpecification
    ) -> Dict[str, Any]:
        """与SDD规范对比"""
        comparison = {
            "matched": [],
            "missing_in_code": [],
            "missing_in_spec": [],
            "differences": [],
            "overall_alignment": 0.0
        }
        
        spec_interfaces = {iface.name: iface for iface in spec.interfaces}
        spec_models = {model.name: model for model in spec.data_models}
        
        for class_info in code_interface.get("classes", []):
            class_name = class_info["name"]
            
            if class_name in spec_interfaces:
                comparison["matched"].append({
                    "type": "interface",
                    "name": class_name,
                    "status": "matched"
                })
                
                iface = spec_interfaces[class_name]
                method_diffs = self._compare_methods(class_info["methods"], iface.parameters)
                comparison["differences"].extend(method_diffs)
            
            elif class_name in spec_models:
                comparison["matched"].append({
                    "type": "data_model",
                    "name": class_name,
                    "status": "matched"
                })
            else:
                comparison["missing_in_spec"].append({
                    "type": "class",
                    "name": class_name
                })
        
        for iface_name in spec_interfaces:
            if not any(c["name"] == iface_name for c in code_interface.get("classes", [])):
                comparison["missing_in_code"].append({
                    "type": "interface",
                    "name": iface_name
                })
        
        for model_name in spec_models:
            if not any(c["name"] == model_name for c in code_interface.get("classes", [])):
                comparison["missing_in_code"].append({
                    "type": "data_model",
                    "name": model_name
                })
        
        total_items = len(spec_interfaces) + len(spec_models)
        matched_items = len(comparison["matched"])
        comparison["overall_alignment"] = (matched_items / total_items * 100) if total_items > 0 else 100
        
        return comparison
    
    def _compare_methods(
        self,
        code_methods: List[Dict[str, Any]],
        spec_params: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """比较方法参数"""
        differences = []
        
        return differences
    
    def detect_inconsistencies(
        self,
        comparison: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """检测规范与实现的不一致"""
        inconsistencies = []
        
        for missing in comparison.get("missing_in_code", []):
            inconsistencies.append({
                "type": "missing_implementation",
                "severity": "high",
                "element": missing["name"],
                "message": f"规范中定义的 {missing['type']} '{missing['name']}' 在代码中未实现"
            })
        
        for missing in comparison.get("missing_in_spec", []):
            inconsistencies.append({
                "type": "extra_implementation",
                "severity": "low",
                "element": missing["name"],
                "message": f"代码中的 {missing['type']} '{missing['name']}' 在规范中未定义"
            })
        
        for diff in comparison.get("differences", []):
            inconsistencies.append({
                "type": "interface_mismatch",
                "severity": "medium",
                "element": diff.get("name", "unknown"),
                "message": diff.get("message", "接口不匹配")
            })
        
        return inconsistencies
    
    def generate_difference_report(
        self,
        comparison: Dict[str, Any],
        inconsistencies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成差异报告"""
        report = {
            "report_id": f"DIFF-REPORT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "overall_alignment": comparison.get("overall_alignment", 0),
                "matched_count": len(comparison.get("matched", [])),
                "missing_in_code": len(comparison.get("missing_in_code", [])),
                "missing_in_spec": len(comparison.get("missing_in_spec", [])),
                "inconsistency_count": len(inconsistencies)
            },
            "details": {
                "matched": comparison.get("matched", []),
                "missing_in_code": comparison.get("missing_in_code", []),
                "missing_in_spec": comparison.get("missing_in_spec", [])
            },
            "inconsistencies": inconsistencies,
            "recommendations": self._generate_recommendations(inconsistencies)
        }
        
        return report
    
    def _generate_recommendations(self, inconsistencies: List[Dict[str, Any]]) -> List[str]:
        """生成修复建议"""
        recommendations = []
        
        high_severity = [i for i in inconsistencies if i.get("severity") == "high"]
        if high_severity:
            recommendations.append(f"优先处理 {len(high_severity)} 个高严重度问题：实现缺失的规范元素")
        
        medium_severity = [i for i in inconsistencies if i.get("severity") == "medium"]
        if medium_severity:
            recommendations.append(f"检查 {len(medium_severity)} 个接口不匹配问题")
        
        low_severity = [i for i in inconsistencies if i.get("severity") == "low"]
        if low_severity:
            recommendations.append(f"考虑将 {len(low_severity)} 个额外实现添加到规范文档中")
        
        return recommendations
    
    def verify_code_against_spec(
        self,
        code_content: str,
        spec: ParsedSpecification,
        language: str = "python"
    ) -> Dict[str, Any]:
        """验证代码是否符合规范"""
        code_interface = self.extract_interface_from_code(code_content, language)
        
        comparison = self.compare_with_spec(code_interface, spec)
        
        inconsistencies = self.detect_inconsistencies(comparison)
        
        report = self.generate_difference_report(comparison, inconsistencies)
        
        cache_key = f"{spec.spec_id}_{language}"
        self._verification_cache[cache_key] = report
        
        self.logger.info(f"代码验证完成: 对齐度 {report['summary']['overall_alignment']:.1f}%")
        
        return report


class FullCycleValidator:
    """完整循环验证器
    
    增强功能:
    1. 验证规范-测试-代码一致性
    2. 验证测试覆盖率
    3. 验证代码质量
    4. 生成完整循环报告
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self._validation_history: List[Dict[str, Any]] = []
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("FullCycleValidator")
        logger.setLevel(logging.INFO)
        return logger
    
    def validate_spec_test_code_consistency(
        self,
        spec: ParsedSpecification,
        test_cases: List[GeneratedTestCase],
        code_content: str,
        language: str = "python"
    ) -> Dict[str, Any]:
        """验证规范-测试-代码一致性"""
        consistency = {
            "spec_to_test": self._validate_spec_test_alignment(spec, test_cases),
            "test_to_code": self._validate_test_code_alignment(test_cases, code_content, language),
            "spec_to_code": self._validate_spec_code_alignment(spec, code_content, language),
            "overall_consistency": 0.0
        }
        
        scores = [
            consistency["spec_to_test"].get("alignment_score", 0),
            consistency["test_to_code"].get("alignment_score", 0),
            consistency["spec_to_code"].get("alignment_score", 0)
        ]
        consistency["overall_consistency"] = sum(scores) / len(scores)
        
        return consistency
    
    def _validate_spec_test_alignment(
        self,
        spec: ParsedSpecification,
        test_cases: List[GeneratedTestCase]
    ) -> Dict[str, Any]:
        """验证规范与测试的对齐"""
        alignment = {
            "covered_elements": 0,
            "total_elements": len(spec.elements),
            "alignment_score": 0.0,
            "gaps": []
        }
        
        tested_elements = set(tc.spec_element_name for tc in test_cases)
        
        for element in spec.elements:
            if element.name in tested_elements:
                alignment["covered_elements"] += 1
            else:
                alignment["gaps"].append({
                    "element": element.name,
                    "type": element.element_type.name,
                    "reason": "缺少测试覆盖"
                })
        
        alignment["alignment_score"] = (
            alignment["covered_elements"] / alignment["total_elements"] * 100
            if alignment["total_elements"] > 0 else 0
        )
        
        return alignment
    
    def _validate_test_code_alignment(
        self,
        test_cases: List[GeneratedTestCase],
        code_content: str,
        language: str
    ) -> Dict[str, Any]:
        """验证测试与代码的对齐"""
        alignment = {
            "implemented_tests": 0,
            "total_tests": len(test_cases),
            "alignment_score": 0.0,
            "gaps": []
        }
        
        for tc in test_cases:
            func_name = tc.name.replace("test_", "")
            if func_name.lower() in code_content.lower():
                alignment["implemented_tests"] += 1
            else:
                alignment["gaps"].append({
                    "test": tc.test_id,
                    "name": tc.name,
                    "reason": "测试对应的功能未实现"
                })
        
        alignment["alignment_score"] = (
            alignment["implemented_tests"] / alignment["total_tests"] * 100
            if alignment["total_tests"] > 0 else 0
        )
        
        return alignment
    
    def _validate_spec_code_alignment(
        self,
        spec: ParsedSpecification,
        code_content: str,
        language: str
    ) -> Dict[str, Any]:
        """验证规范与代码的对齐"""
        verifier = CodeToSpecVerifier(self.logger)
        code_interface = verifier.extract_interface_from_code(code_content, language)
        comparison = verifier.compare_with_spec(code_interface, spec)
        
        return {
            "alignment_score": comparison.get("overall_alignment", 0),
            "matched": len(comparison.get("matched", [])),
            "missing_in_code": len(comparison.get("missing_in_code", [])),
            "gaps": comparison.get("missing_in_code", [])
        }
    
    def validate_test_coverage(
        self,
        test_cases: List[GeneratedTestCase],
        spec: ParsedSpecification,
        coverage_threshold: float = 80.0
    ) -> Dict[str, Any]:
        """验证测试覆盖率"""
        coverage = {
            "element_coverage": {},
            "type_coverage": {},
            "overall_coverage": 0.0,
            "meets_threshold": False,
            "recommendations": []
        }
        
        for element in spec.elements:
            element_tests = [tc for tc in test_cases if tc.spec_element_name == element.name]
            coverage["element_coverage"][element.name] = {
                "test_count": len(element_tests),
                "test_types": list(set(tc.test_type.value for tc in element_tests))
            }
        
        type_counts = {}
        for tc in test_cases:
            type_counts[tc.test_type.value] = type_counts.get(tc.test_type.value, 0) + 1
        coverage["type_coverage"] = type_counts
        
        covered_elements = sum(1 for ec in coverage["element_coverage"].values() if ec["test_count"] > 0)
        coverage["overall_coverage"] = (
            covered_elements / len(spec.elements) * 100
            if spec.elements else 0
        )
        
        coverage["meets_threshold"] = coverage["overall_coverage"] >= coverage_threshold
        
        if not coverage["meets_threshold"]:
            coverage["recommendations"].append(
                f"覆盖率 {coverage['overall_coverage']:.1f}% 低于阈值 {coverage_threshold}%，需要增加测试"
            )
        
        uncovered = [name for name, ec in coverage["element_coverage"].items() if ec["test_count"] == 0]
        if uncovered:
            coverage["recommendations"].append(
                f"以下元素缺少测试: {', '.join(uncovered[:5])}"
            )
        
        return coverage
    
    def validate_code_quality(
        self,
        code_content: str,
        quality_threshold: float = 70.0
    ) -> Dict[str, Any]:
        """验证代码质量"""
        quality = {
            "metrics": {},
            "issues": [],
            "overall_score": 0.0,
            "meets_threshold": False,
            "recommendations": []
        }
        
        lines = code_content.split("\n")
        non_empty_lines = [l for l in lines if l.strip()]
        
        complexity = 1
        complexity += code_content.count("if ")
        complexity += code_content.count("for ")
        complexity += code_content.count("while ")
        quality["metrics"]["complexity"] = complexity
        
        quality["metrics"]["lines_of_code"] = len(non_empty_lines)
        
        quality["metrics"]["function_count"] = code_content.count("def ")
        
        quality["metrics"]["class_count"] = code_content.count("class ")
        
        quality["metrics"]["comment_ratio"] = (
            len([l for l in lines if l.strip().startswith("#")]) / len(non_empty_lines) * 100
            if non_empty_lines else 0
        )
        
        if complexity > 20:
            quality["issues"].append({
                "type": "high_complexity",
                "severity": "medium",
                "message": f"代码复杂度过高: {complexity}"
            })
        
        if quality["metrics"]["comment_ratio"] < 10:
            quality["issues"].append({
                "type": "low_documentation",
                "severity": "low",
                "message": "注释比例过低"
            })
        
        quality["overall_score"] = max(0, 100 - complexity * 2 - len(quality["issues"]) * 5)
        quality["meets_threshold"] = quality["overall_score"] >= quality_threshold
        
        if not quality["meets_threshold"]:
            quality["recommendations"].append(
                f"代码质量得分 {quality['overall_score']:.1f} 低于阈值 {quality_threshold}"
            )
        
        return quality
    
    def generate_full_cycle_report(
        self,
        spec: ParsedSpecification,
        test_cases: List[GeneratedTestCase],
        code_content: str,
        language: str = "python"
    ) -> Dict[str, Any]:
        """生成完整循环报告"""
        report = {
            "report_id": f"CYCLE-REPORT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "generated_at": datetime.now().isoformat(),
            "spec_info": {
                "id": spec.spec_id,
                "name": spec.spec_name,
                "version": spec.version,
                "elements_count": len(spec.elements)
            },
            "test_info": {
                "total_tests": len(test_cases),
                "test_types": {}
            },
            "validation_results": {},
            "overall_status": "unknown",
            "recommendations": []
        }
        
        for tc in test_cases:
            report["test_info"]["test_types"][tc.test_type.value] = \
                report["test_info"]["test_types"].get(tc.test_type.value, 0) + 1
        
        consistency = self.validate_spec_test_code_consistency(
            spec, test_cases, code_content, language
        )
        report["validation_results"]["consistency"] = consistency
        
        coverage = self.validate_test_coverage(test_cases, spec)
        report["validation_results"]["coverage"] = coverage
        
        quality = self.validate_code_quality(code_content)
        report["validation_results"]["quality"] = quality
        
        overall_scores = [
            consistency.get("overall_consistency", 0),
            coverage.get("overall_coverage", 0),
            quality.get("overall_score", 0)
        ]
        overall_avg = sum(overall_scores) / len(overall_scores)
        
        if overall_avg >= 80:
            report["overall_status"] = "excellent"
        elif overall_avg >= 60:
            report["overall_status"] = "good"
        elif overall_avg >= 40:
            report["overall_status"] = "acceptable"
        else:
            report["overall_status"] = "needs_improvement"
        
        if consistency.get("overall_consistency", 0) < 80:
            report["recommendations"].append("提高规范-测试-代码一致性")
        
        if not coverage.get("meets_threshold", False):
            report["recommendations"].append("增加测试覆盖率")
        
        if not quality.get("meets_threshold", False):
            report["recommendations"].append("改进代码质量")
        
        self._validation_history.append(report)
        
        self.logger.info(f"完整循环报告生成: {report['overall_status']}")
        
        return report
    
    def assess_refactoring_quality(
        self,
        before_code: str,
        after_code: str,
        test_results_before: Dict[str, Any],
        test_results_after: Dict[str, Any]
    ) -> QualityAssessment:
        """评估重构质量"""
        assessment_id = f"REFACTOR-QA-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        metrics = self._calculate_refactoring_metrics(
            before_code, after_code, test_results_before, test_results_after
        )
        
        dimensions = {
            "behavior_preservation": metrics.behavior_preservation / 100,
            "code_improvement": metrics.code_improvement / 100,
            "pattern_adherence": metrics.design_pattern_adherence / 100,
            "test_stability": metrics.test_stability / 100,
            "performance": max(0, 100 - metrics.performance_impact) / 100,
            "readability": metrics.readability_improvement / 100
        }
        
        overall_score = sum(dimensions.values()) / len(dimensions) * 100
        
        issues = []
        if metrics.behavior_preservation < 100:
            issues.append({
                "type": "behavior_change",
                "severity": "critical",
                "message": "重构改变了行为，需要修复"
            })
        
        strengths = []
        if metrics.code_improvement > 20:
            strengths.append("代码质量显著提升")
        
        improvement_areas = self._identify_improvement_areas(dimensions)
        
        overall_grade = self._determine_grade(overall_score)
        
        benchmark_comparison = self._compare_with_benchmarks("refactoring", dimensions)
        
        assessment = QualityAssessment(
            assessment_id=assessment_id,
            target_type="refactoring",
            target_id="refactoring_session",
            overall_grade=overall_grade,
            overall_score=overall_score,
            dimensions=dimensions,
            issues=issues,
            strengths=strengths,
            improvement_areas=improvement_areas,
            benchmark_comparison=benchmark_comparison
        )
        
        self.assessment_history.append(assessment)
        self._save_assessment(assessment)
        
        self.logger.info(f"重构质量评估完成 - {overall_grade.value} ({overall_score:.1f}%)")
        
        return assessment
    
    def _calculate_refactoring_metrics(
        self,
        before_code: str,
        after_code: str,
        test_results_before: Dict[str, Any],
        test_results_after: Dict[str, Any]
    ) -> RefactoringQualityMetrics:
        """计算重构质量指标"""
        passed_before = test_results_before.get("passed", 0)
        passed_after = test_results_after.get("passed", 0)
        
        if passed_before > 0:
            behavior_preservation = (passed_after / passed_before) * 100
        else:
            behavior_preservation = 100 if passed_after == 0 else 0
        
        before_complexity = self._estimate_complexity(before_code)
        after_complexity = self._estimate_complexity(after_code)
        
        if before_complexity > 0:
            code_improvement = max(0, (before_complexity - after_complexity) / before_complexity * 100)
        else:
            code_improvement = 0
        
        design_pattern_adherence = 80.0
        
        test_stability = 100 if passed_after >= passed_before else (passed_after / passed_before * 100) if passed_before > 0 else 100
        
        performance_impact = 0.0
        
        before_readability = self._estimate_naming_quality(before_code)
        after_readability = self._estimate_naming_quality(after_code)
        readability_improvement = max(0, after_readability - before_readability)
        
        return RefactoringQualityMetrics(
            behavior_preservation=behavior_preservation,
            code_improvement=code_improvement,
            design_pattern_adherence=design_pattern_adherence,
            test_stability=test_stability,
            performance_impact=performance_impact,
            readability_improvement=readability_improvement
        )
    
    def _determine_grade(self, score: float) -> QualityGrade:
        """确定质量等级"""
        if score >= 90:
            return QualityGrade.EXCELLENT
        elif score >= 75:
            return QualityGrade.GOOD
        elif score >= 60:
            return QualityGrade.ACCEPTABLE
        elif score >= 40:
            return QualityGrade.POOR
        else:
            return QualityGrade.CRITICAL
    
    def _compare_with_benchmarks(
        self,
        category: str,
        dimensions: Dict[str, float]
    ) -> Dict[str, Any]:
        """与基准比较"""
        benchmarks = self.BENCHMARKS.get(category, {})
        comparison = {}
        
        for dim_name, score in dimensions.items():
            if dim_name in benchmarks:
                bench = benchmarks[dim_name]
                if score * 100 >= bench.get("excellent", 90):
                    comparison[dim_name] = "excellent"
                elif score * 100 >= bench.get("good", 70):
                    comparison[dim_name] = "good"
                elif score * 100 >= bench.get("acceptable", 50):
                    comparison[dim_name] = "acceptable"
                else:
                    comparison[dim_name] = "poor"
        
        return comparison
    
    def _save_assessment(self, assessment: QualityAssessment) -> None:
        """保存评估结果"""
        assessment_file = self.assessments_dir / f"{assessment.assessment_id}.json"
        
        assessment_dict = {
            "assessment_id": assessment.assessment_id,
            "target_type": assessment.target_type,
            "target_id": assessment.target_id,
            "overall_grade": assessment.overall_grade.value,
            "overall_score": assessment.overall_score,
            "dimensions": assessment.dimensions,
            "issues": assessment.issues,
            "strengths": assessment.strengths,
            "improvement_areas": assessment.improvement_areas,
            "benchmark_comparison": assessment.benchmark_comparison,
            "assessed_at": datetime.now().isoformat()
        }
        
        with open(assessment_file, "w", encoding="utf-8") as f:
            json.dump(assessment_dict, f, ensure_ascii=False, indent=2)
    
    def generate_quality_report(
        self,
        cycle_report: CycleExecutionReport
    ) -> Dict[str, Any]:
        """生成综合质量报告"""
        report = {
            "report_id": f"QUALITY-REPORT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "cycle_report_id": cycle_report.report_id,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_assessments": len(self.assessment_history),
                "average_score": 0,
                "grade_distribution": {}
            },
            "assessments": [],
            "recommendations": []
        }
        
        if self.assessment_history:
            total_score = sum(a.overall_score for a in self.assessment_history)
            report["summary"]["average_score"] = total_score / len(self.assessment_history)
            
            grade_counts = {}
            for assessment in self.assessment_history:
                grade = assessment.overall_grade.value
                grade_counts[grade] = grade_counts.get(grade, 0) + 1
                
                report["assessments"].append({
                    "id": assessment.assessment_id,
                    "type": assessment.target_type,
                    "target": assessment.target_id,
                    "grade": assessment.overall_grade.value,
                    "score": assessment.overall_score
                })
            
            report["summary"]["grade_distribution"] = grade_counts
            
            if report["summary"]["average_score"] < 60:
                report["recommendations"].append("整体质量需要改进，建议全面审查")
            elif report["summary"]["average_score"] < 75:
                report["recommendations"].append("整体质量良好，建议针对低分领域进行优化")
            else:
                report["recommendations"].append("整体质量优秀，建议保持当前标准")
        
        return report


def main():
    parser = argparse.ArgumentParser(
        description="SDD与TDD集成器 - 支持规范驱动开发与测试驱动开发的深度集成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  解析规范文件:
    python sdd_tdd_integrator.py parse --spec spec.yaml

  生成测试用例:
    python sdd_tdd_integrator.py generate --spec spec.yaml

  运行红绿蓝循环:
    python sdd_tdd_integrator.py cycle --spec spec.yaml --dry-run

  运行完整管道:
    python sdd_tdd_integrator.py pipeline --spec spec.yaml --format html
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    parse_parser = subparsers.add_parser("parse", help="解析规范文件")
    parse_parser.add_argument("--spec", required=True, help="规范文件路径")
    parse_parser.add_argument("--output-dir", default="output/sdd_tdd", help="输出目录")
    
    generate_parser = subparsers.add_parser("generate", help="生成测试用例")
    generate_parser.add_argument("--spec", required=True, help="规范文件路径")
    generate_parser.add_argument("--output", help="测试文件输出路径")
    generate_parser.add_argument("--output-dir", default="output/sdd_tdd", help="输出目录")
    
    coverage_parser = subparsers.add_parser("coverage", help="生成覆盖率报告")
    coverage_parser.add_argument("--spec", required=True, help="规范文件路径")
    coverage_parser.add_argument("--test-results", help="测试结果文件路径")
    coverage_parser.add_argument("--output-dir", default="output/sdd_tdd", help="输出目录")
    
    validate_parser = subparsers.add_parser("validate", help="验证规范完整性")
    validate_parser.add_argument("--spec", required=True, help="规范文件路径")
    validate_parser.add_argument("--output-dir", default="output/sdd_tdd", help="输出目录")
    
    full_parser = subparsers.add_parser("full", help="运行完整集成流程")
    full_parser.add_argument("--spec", required=True, help="规范文件路径")
    full_parser.add_argument("--test-results", help="测试结果文件路径")
    full_parser.add_argument("--output-dir", default="output/sdd_tdd", help="输出目录")
    
    cycle_parser = subparsers.add_parser("cycle", help="运行红绿蓝循环")
    cycle_parser.add_argument("--spec", required=True, help="规范文件路径")
    cycle_parser.add_argument("--output-dir", default="output/sdd_tdd", help="输出目录")
    cycle_parser.add_argument("--dry-run", action="store_true", help="模拟运行，不执行实际测试")
    cycle_parser.add_argument("--format", choices=["json", "markdown", "html"], default="html", help="报告格式")
    
    pipeline_parser = subparsers.add_parser("pipeline", help="运行SDD-TDD完整管道")
    pipeline_parser.add_argument("--spec", required=True, help="规范文件路径")
    pipeline_parser.add_argument("--output-dir", default="output/sdd_tdd", help="输出目录")
    pipeline_parser.add_argument("--dry-run", action="store_true", help="模拟运行循环阶段")
    pipeline_parser.add_argument("--format", choices=["json", "markdown", "html"], default="html", help="报告格式")
    pipeline_parser.add_argument("--skip-cycle", action="store_true", help="跳过红绿蓝循环阶段")
    
    resume_parser = subparsers.add_parser("resume", help="恢复中断的循环执行")
    resume_parser.add_argument("--report-id", required=True, help="循环报告ID")
    resume_parser.add_argument("--output-dir", default="output/sdd_tdd", help="输出目录")
    
    report_parser = subparsers.add_parser("report", help="生成循环报告")
    report_parser.add_argument("--report-id", required=True, help="循环报告ID")
    report_parser.add_argument("--output-dir", default="output/sdd_tdd", help="输出目录")
    report_parser.add_argument("--format", choices=["json", "markdown", "html"], default="html", help="报告格式")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        integrator = SddTddIntegrator(output_dir=args.output_dir)
        
        if args.command == "parse":
            spec, validation = integrator.parse_spec(args.spec)
            print(f"规范解析完成:")
            print(f"  ID: {spec.spec_id}")
            print(f"  名称: {spec.spec_name}")
            print(f"  版本: {spec.version}")
            print(f"  元素数量: {len(spec.elements)}")
            print(f"  验证结果: {'有效' if validation.is_valid else '无效'}")
            print(f"  完整性评分: {validation.completeness_score:.1f}%")
            
        elif args.command == "generate":
            spec, _ = integrator.parse_spec(args.spec)
            test_cases, test_file = integrator.generate_tests(spec, args.output)
            print(f"测试用例生成完成:")
            print(f"  测试用例数量: {len(test_cases)}")
            print(f"  测试文件: {test_file}")
            
        elif args.command == "coverage":
            spec, _ = integrator.parse_spec(args.spec)
            test_cases, _ = integrator.generate_tests(spec)
            
            test_results = None
            if args.test_results:
                with open(args.test_results, "r", encoding="utf-8") as f:
                    test_results = json.load(f)
            
            report = integrator.generate_coverage_report(spec, test_cases, test_results)
            print(f"覆盖率报告生成完成:")
            print(f"  报告ID: {report.report_id}")
            print(f"  总体覆盖率: {report.overall_coverage:.1f}%")
            print(f"  建议:")
            for rec in report.recommendations:
                print(f"    - {rec}")
                
        elif args.command == "validate":
            spec, _ = integrator.parse_spec(args.spec)
            validation = integrator.validate_spec(spec)
            print(f"规范验证完成:")
            print(f"  有效: {validation.is_valid}")
            print(f"  完整性评分: {validation.completeness_score:.1f}%")
            if validation.errors:
                print(f"  错误 ({len(validation.errors)}):")
                for error in validation.errors:
                    print(f"    - [{error['path']}] {error['message']}")
            if validation.warnings:
                print(f"  警告 ({len(validation.warnings)}):")
                for warning in validation.warnings:
                    print(f"    - [{warning['path']}] {warning['message']}")
                    
        elif args.command == "full":
            test_results = None
            if args.test_results:
                with open(args.test_results, "r", encoding="utf-8") as f:
                    test_results = json.load(f)
            
            result = integrator.run_full_integration(args.spec, test_results)
            print(f"完整集成流程结果:")
            print(f"  状态: {result['status']}")
            if result.get("spec"):
                print(f"  规范: {result['spec']['name']} ({result['spec']['id']})")
            if result.get("test_generation"):
                print(f"  测试用例: {result['test_generation']['test_cases_count']} 个")
            if result.get("coverage"):
                print(f"  覆盖率: {result['coverage']['overall_coverage']:.1f}%")
        
        elif args.command == "cycle":
            print("=" * 60)
            print("开始红绿蓝循环执行")
            print("=" * 60)
            
            result = integrator.run_cycle(
                args.spec,
                dry_run=args.dry_run,
                report_format=args.format
            )
            
            print(f"\n红绿蓝循环执行结果:")
            print(f"  状态: {result['status']}")
            if result.get("spec"):
                print(f"  规范: {result['spec']['name']} ({result['spec']['id']})")
            if result.get("cycle"):
                cycle = result["cycle"]
                print(f"  迭代: {cycle['completed_iterations']}/{cycle['total_iterations']}")
                print(f"  成功率: {cycle['success_rate']:.1f}%")
                print(f"  报告文件: {cycle['report_file']}")
            if result.get("coverage"):
                print(f"  覆盖率: {result['coverage']['overall_coverage']:.1f}%")
            
            if result.get("error"):
                print(f"  错误: {result['error']}")
        
        elif args.command == "pipeline":
            print("=" * 60)
            print("开始SDD-TDD完整管道流程")
            print("=" * 60)
            
            options = {
                "dry_run": args.dry_run,
                "report_format": args.format,
                "run_cycle": not args.skip_cycle
            }
            
            result = integrator.run_sdd_tdd_pipeline(args.spec, options)
            
            print(f"\nSDD-TDD管道流程结果:")
            print(f"  状态: {result['status']}")
            if result.get("spec"):
                print(f"  规范: {result['spec']['name']} ({result['spec']['id']})")
            
            print(f"  执行阶段:")
            for phase in result.get("phases", []):
                print(f"    - {phase['name']}: {phase['status']}")
            
            if result.get("cycle"):
                cycle = result["cycle"]
                print(f"  循环迭代: {cycle['completed_iterations']}/{cycle['total_iterations']}")
                print(f"  循环成功率: {cycle['success_rate']:.1f}%")
                print(f"  循环报告: {cycle['report_file']}")
            
            if result.get("coverage"):
                print(f"  覆盖率: {result['coverage']['overall_coverage']:.1f}%")
            
            if result.get("error"):
                print(f"  错误: {result['error']}")
        
        elif args.command == "resume":
            print(f"恢复循环执行: {args.report_id}")
            
            report = integrator.resume_cycle(args.report_id)
            
            print(f"循环状态:")
            print(f"  报告ID: {report.report_id}")
            print(f"  完成迭代: {report.completed_iterations}/{report.total_iterations}")
            print(f"  失败迭代: {report.failed_iterations}")
            
            if report.completed_at:
                print(f"  状态: 已完成")
            else:
                print(f"  状态: 进行中")
        
        elif args.command == "report":
            print(f"生成循环报告: {args.report_id}")
            
            report_file = integrator.generate_cycle_report(
                args.report_id,
                format_type=args.format
            )
            
            if report_file:
                print(f"报告已生成: {report_file}")
            else:
                print(f"错误: 未找到报告 {args.report_id}")
                sys.exit(1)
    
    except FileNotFoundError as e:
        print(f"错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"执行错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


class CycleQualityEvaluator:
    """
    循环结果质量评估器
    
    评估红绿蓝循环的整体质量：
    - 迭代质量分析
    - 代码演进追踪
    - 测试稳定性评估
    - 重构效果评估
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self.evaluation_history: List[Dict[str, Any]] = []
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("CycleQualityEvaluator")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def evaluate_cycle_quality(
        self,
        cycle_report: CycleExecutionReport,
        spec: ParsedSpecification,
        test_cases: List[GeneratedTestCase]
    ) -> Dict[str, Any]:
        """
        评估循环质量
        
        Args:
            cycle_report: 循环执行报告
            spec: 解析后的规范
            test_cases: 生成的测试用例
            
        Returns:
            Dict[str, Any]: 质量评估结果
        """
        self.logger.info("开始循环质量评估...")
        
        iteration_quality = self._evaluate_iteration_quality(cycle_report)
        
        code_evolution = self._analyze_code_evolution(cycle_report)
        
        test_stability = self._assess_test_stability(cycle_report, test_cases)
        
        refactoring_effectiveness = self._evaluate_refactoring_effectiveness(cycle_report)
        
        overall_quality = self._calculate_overall_quality(
            iteration_quality, code_evolution, test_stability, refactoring_effectiveness
        )
        
        recommendations = self._generate_quality_recommendations(
            iteration_quality, code_evolution, test_stability, refactoring_effectiveness
        )
        
        evaluation_result = {
            "evaluation_id": f"CYCLE-EVAL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "cycle_report_id": cycle_report.report_id,
            "evaluated_at": datetime.now().isoformat(),
            "iteration_quality": iteration_quality,
            "code_evolution": code_evolution,
            "test_stability": test_stability,
            "refactoring_effectiveness": refactoring_effectiveness,
            "overall_quality": overall_quality,
            "recommendations": recommendations
        }
        
        self.evaluation_history.append(evaluation_result)
        
        return evaluation_result
    
    def _evaluate_iteration_quality(
        self, 
        cycle_report: CycleExecutionReport
    ) -> Dict[str, Any]:
        """评估迭代质量"""
        if not cycle_report.iterations:
            return {"score": 0, "grade": "N/A", "details": {}}
        
        total_iterations = len(cycle_report.iterations)
        successful_iterations = sum(
            1 for it in cycle_report.iterations 
            if it.overall_result == CycleResult.SUCCESS
        )
        
        avg_red_duration = 0
        avg_green_duration = 0
        avg_blue_duration = 0
        
        for it in cycle_report.iterations:
            if it.red_phase:
                avg_red_duration += self._parse_duration(it.red_phase.duration or "0s")
            if it.green_phase:
                avg_green_duration += self._parse_duration(it.green_phase.duration or "0s")
            if it.blue_phase:
                avg_blue_duration += self._parse_duration(it.blue_phase.duration or "0s")
        
        if total_iterations > 0:
            avg_red_duration /= total_iterations
            avg_green_duration /= total_iterations
            avg_blue_duration /= total_iterations
        
        success_rate = (successful_iterations / total_iterations * 100) if total_iterations > 0 else 0
        
        red_efficiency = self._calculate_phase_efficiency(avg_red_duration, "red")
        green_efficiency = self._calculate_phase_efficiency(avg_green_duration, "green")
        blue_efficiency = self._calculate_phase_efficiency(avg_blue_duration, "blue")
        
        overall_score = (
            success_rate * 0.4 +
            red_efficiency * 0.2 +
            green_efficiency * 0.2 +
            blue_efficiency * 0.2
        )
        
        grade = self._determine_quality_grade(overall_score)
        
        return {
            "score": round(overall_score, 2),
            "grade": grade,
            "success_rate": round(success_rate, 2),
            "total_iterations": total_iterations,
            "successful_iterations": successful_iterations,
            "phase_efficiency": {
                "red": round(red_efficiency, 2),
                "green": round(green_efficiency, 2),
                "blue": round(blue_efficiency, 2)
            },
            "avg_durations": {
                "red_seconds": round(avg_red_duration, 2),
                "green_seconds": round(avg_green_duration, 2),
                "blue_seconds": round(avg_blue_duration, 2)
            }
        }
    
    def _parse_duration(self, duration_str: str) -> float:
        """解析持续时间字符串"""
        if not duration_str:
            return 0.0
        
        match = re.match(r'(\d+(?:\.\d+)?)\s*(s|m|h)?', duration_str)
        if match:
            value = float(match.group(1))
            unit = match.group(2) or 's'
            
            if unit == 'm':
                value *= 60
            elif unit == 'h':
                value *= 3600
            
            return value
        
        return 0.0
    
    def _calculate_phase_efficiency(self, avg_duration: float, phase: str) -> float:
        """计算阶段效率"""
        expected_durations = {
            "red": 30.0,
            "green": 60.0,
            "blue": 45.0
        }
        
        expected = expected_durations.get(phase, 30.0)
        
        if avg_duration <= expected:
            return 100.0
        elif avg_duration <= expected * 2:
            return 80.0
        elif avg_duration <= expected * 3:
            return 60.0
        else:
            return 40.0
    
    def _analyze_code_evolution(
        self, 
        cycle_report: CycleExecutionReport
    ) -> Dict[str, Any]:
        """分析代码演进"""
        evolution_metrics = {
            "complexity_trend": [],
            "coverage_trend": [],
            "quality_trend": []
        }
        
        for iteration in cycle_report.iterations:
            if hasattr(iteration, 'metrics') and iteration.metrics:
                evolution_metrics["complexity_trend"].append(
                    iteration.metrics.get("complexity", 0)
                )
                evolution_metrics["coverage_trend"].append(
                    iteration.metrics.get("coverage", 0)
                )
                evolution_metrics["quality_trend"].append(
                    iteration.metrics.get("quality_score", 0)
                )
        
        complexity_improvement = self._calculate_trend_improvement(
            evolution_metrics["complexity_trend"], lower_is_better=True
        )
        coverage_improvement = self._calculate_trend_improvement(
            evolution_metrics["coverage_trend"]
        )
        quality_improvement = self._calculate_trend_improvement(
            evolution_metrics["quality_trend"]
        )
        
        overall_evolution = (
            complexity_improvement * 0.3 +
            coverage_improvement * 0.4 +
            quality_improvement * 0.3
        )
        
        return {
            "overall_improvement": round(overall_evolution, 2),
            "complexity_improvement": round(complexity_improvement, 2),
            "coverage_improvement": round(coverage_improvement, 2),
            "quality_improvement": round(quality_improvement, 2),
            "evolution_trend": "improving" if overall_evolution > 10 else "stable" if overall_evolution > -10 else "declining"
        }
    
    def _calculate_trend_improvement(
        self, 
        trend: List[float],
        lower_is_better: bool = False
    ) -> float:
        """计算趋势改进"""
        if len(trend) < 2:
            return 0.0
        
        first_half = trend[:len(trend)//2]
        second_half = trend[len(trend)//2:]
        
        first_avg = sum(first_half) / len(first_half) if first_half else 0
        second_avg = sum(second_half) / len(second_half) if second_half else 0
        
        if first_avg == 0:
            return 0.0
        
        improvement = ((second_avg - first_avg) / first_avg) * 100
        
        if lower_is_better:
            improvement = -improvement
        
        return improvement
    
    def _assess_test_stability(
        self,
        cycle_report: CycleExecutionReport,
        test_cases: List[GeneratedTestCase]
    ) -> Dict[str, Any]:
        """评估测试稳定性"""
        flaky_tests = []
        consistently_failing = []
        consistently_passing = []
        
        test_results_by_name: Dict[str, List[str]] = {}
        
        for iteration in cycle_report.iterations:
            for phase in [iteration.red_phase, iteration.green_phase, iteration.blue_phase]:
                if phase and hasattr(phase, 'test_results'):
                    for result in phase.test_results:
                        test_name = result.get("name", "")
                        status = result.get("status", "unknown")
                        
                        if test_name not in test_results_by_name:
                            test_results_by_name[test_name] = []
                        test_results_by_name[test_name].append(status)
        
        for test_name, results in test_results_by_name.items():
            if len(results) >= 3:
                pass_count = sum(1 for r in results if r == "passed")
                fail_count = sum(1 for r in results if r == "failed")
                
                pass_rate = pass_count / len(results)
                
                if 0.2 <= pass_rate <= 0.8:
                    flaky_tests.append({
                        "test_name": test_name,
                        "pass_rate": round(pass_rate, 2),
                        "run_count": len(results)
                    })
                elif pass_rate == 0:
                    consistently_failing.append(test_name)
                elif pass_rate == 1:
                    consistently_passing.append(test_name)
        
        stability_score = 100.0
        stability_score -= len(flaky_tests) * 10
        stability_score -= len(consistently_failing) * 5
        
        stability_score = max(0, stability_score)
        
        return {
            "stability_score": round(stability_score, 2),
            "grade": self._determine_quality_grade(stability_score),
            "flaky_tests_count": len(flaky_tests),
            "flaky_tests": flaky_tests[:5],
            "consistently_failing_count": len(consistently_failing),
            "consistently_passing_count": len(consistently_passing),
            "total_tests_analyzed": len(test_results_by_name)
        }
    
    def _evaluate_refactoring_effectiveness(
        self, 
        cycle_report: CycleExecutionReport
    ) -> Dict[str, Any]:
        """评估重构效果"""
        blue_phases = [
            it.blue_phase for it in cycle_report.iterations 
            if it.blue_phase
        ]
        
        if not blue_phases:
            return {"score": 0, "grade": "N/A", "details": "无蓝阶段数据"}
        
        refactoring_success_count = sum(
            1 for phase in blue_phases 
            if phase.status == CyclePhaseStatus.COMPLETED
        )
        
        refactoring_rate = (refactoring_success_count / len(blue_phases) * 100) if blue_phases else 0
        
        behavior_preservation_rate = 100.0
        
        code_quality_improvement = 0.0
        
        overall_score = (
            refactoring_rate * 0.4 +
            behavior_preservation_rate * 0.4 +
            code_quality_improvement * 0.2
        )
        
        return {
            "score": round(overall_score, 2),
            "grade": self._determine_quality_grade(overall_score),
            "refactoring_rate": round(refactoring_rate, 2),
            "successful_refactorings": refactoring_success_count,
            "total_refactorings": len(blue_phases),
            "behavior_preservation_rate": behavior_preservation_rate
        }
    
    def _calculate_overall_quality(
        self,
        iteration_quality: Dict[str, Any],
        code_evolution: Dict[str, Any],
        test_stability: Dict[str, Any],
        refactoring_effectiveness: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算整体质量"""
        scores = [
            iteration_quality.get("score", 0),
            code_evolution.get("overall_improvement", 0) + 50,
            test_stability.get("stability_score", 0),
            refactoring_effectiveness.get("score", 0)
        ]
        
        overall_score = sum(scores) / len(scores)
        
        return {
            "overall_score": round(overall_score, 2),
            "grade": self._determine_quality_grade(overall_score),
            "component_scores": {
                "iteration_quality": iteration_quality.get("score", 0),
                "code_evolution": code_evolution.get("overall_improvement", 0),
                "test_stability": test_stability.get("stability_score", 0),
                "refactoring_effectiveness": refactoring_effectiveness.get("score", 0)
            }
        }
    
    def _generate_quality_recommendations(
        self,
        iteration_quality: Dict[str, Any],
        code_evolution: Dict[str, Any],
        test_stability: Dict[str, Any],
        refactoring_effectiveness: Dict[str, Any]
    ) -> List[str]:
        """生成质量改进建议"""
        recommendations = []
        
        if iteration_quality.get("success_rate", 0) < 80:
            recommendations.append("迭代成功率较低，建议检查规范定义的完整性")
        
        phase_efficiency = iteration_quality.get("phase_efficiency", {})
        if phase_efficiency.get("green", 0) < 60:
            recommendations.append("GREEN阶段效率较低，建议优化实现策略")
        
        if code_evolution.get("evolution_trend") == "declining":
            recommendations.append("代码质量呈下降趋势，建议加强代码审查")
        
        if test_stability.get("flaky_tests_count", 0) > 0:
            recommendations.append(f"发现 {test_stability['flaky_tests_count']} 个不稳定测试，建议修复或移除")
        
        if refactoring_effectiveness.get("refactoring_rate", 0) < 70:
            recommendations.append("重构成功率较低，建议简化重构范围")
        
        if not recommendations:
            recommendations.append("循环质量良好，继续保持当前实践")
        
        return recommendations
    
    def _determine_quality_grade(self, score: float) -> str:
        """确定质量等级"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"


class CycleRecoveryManager:
    """
    循环中断和恢复管理器
    
    提供循环执行的持久化和恢复功能：
    - 状态持久化
    - 断点恢复
    - 进度追踪
    - 错误恢复
    """
    
    def __init__(
        self,
        state_dir: str = "output/sdd_tdd/cycle_states",
        logger: Optional[logging.Logger] = None
    ):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger or self._setup_logger()
        self._active_cycles: Dict[str, Dict[str, Any]] = {}
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("CycleRecoveryManager")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def save_cycle_state(
        self,
        cycle_report: CycleExecutionReport,
        current_iteration: int,
        current_phase: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        保存循环状态
        
        Args:
            cycle_report: 循环报告
            current_iteration: 当前迭代索引
            current_phase: 当前阶段
            context: 额外上下文
            
        Returns:
            str: 状态文件路径
        """
        state = {
            "report_id": cycle_report.report_id,
            "spec_id": cycle_report.spec_id,
            "spec_name": cycle_report.spec_name,
            "current_iteration": current_iteration,
            "current_phase": current_phase,
            "total_iterations": cycle_report.total_iterations,
            "completed_iterations": cycle_report.completed_iterations,
            "failed_iterations": cycle_report.failed_iterations,
            "iterations": [
                {
                    "cycle_number": it.cycle_number,
                    "spec_element_name": it.spec_element_name,
                    "overall_result": it.overall_result.value if it.overall_result else None,
                    "started_at": it.started_at,
                    "completed_at": it.completed_at
                }
                for it in cycle_report.iterations
            ],
            "context": context or {},
            "saved_at": datetime.now().isoformat(),
            "status": "interrupted"
        }
        
        state_file = self.state_dir / f"{cycle_report.report_id}.json"
        
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        self._active_cycles[cycle_report.report_id] = state
        
        self.logger.info(f"循环状态已保存: {cycle_report.report_id}, 迭代: {current_iteration}/{cycle_report.total_iterations}")
        
        return str(state_file)
    
    def load_cycle_state(self, report_id: str) -> Optional[Dict[str, Any]]:
        """
        加载循环状态
        
        Args:
            report_id: 报告ID
            
        Returns:
            Optional[Dict[str, Any]]: 循环状态，如果不存在返回None
        """
        if report_id in self._active_cycles:
            return self._active_cycles[report_id]
        
        state_file = self.state_dir / f"{report_id}.json"
        
        if not state_file.exists():
            self.logger.warning(f"循环状态文件不存在: {report_id}")
            return None
        
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
        
        self._active_cycles[report_id] = state
        
        self.logger.info(f"循环状态已加载: {report_id}")
        
        return state
    
    def get_recovery_point(
        self, 
        report_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取恢复点信息
        
        Args:
            report_id: 报告ID
            
        Returns:
            Optional[Dict[str, Any]]: 恢复点信息
        """
        state = self.load_cycle_state(report_id)
        
        if not state:
            return None
        
        return {
            "report_id": state["report_id"],
            "spec_id": state["spec_id"],
            "spec_name": state["spec_name"],
            "resume_from_iteration": state["current_iteration"],
            "resume_from_phase": state["current_phase"],
            "completed_iterations": state["completed_iterations"],
            "failed_iterations": state["failed_iterations"],
            "total_iterations": state["total_iterations"],
            "progress_percentage": (state["completed_iterations"] / state["total_iterations"] * 100) if state["total_iterations"] > 0 else 0,
            "saved_at": state["saved_at"],
            "can_resume": True
        }
    
    def list_interrupted_cycles(self) -> List[Dict[str, Any]]:
        """
        列出所有中断的循环
        
        Returns:
            List[Dict[str, Any]]: 中断循环列表
        """
        interrupted = []
        
        for state_file in self.state_dir.glob("*.json"):
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                
                if state.get("status") == "interrupted":
                    interrupted.append({
                        "report_id": state["report_id"],
                        "spec_name": state["spec_name"],
                        "progress": f"{state['completed_iterations']}/{state['total_iterations']}",
                        "saved_at": state["saved_at"]
                    })
            except Exception as e:
                self.logger.error(f"读取状态文件失败 {state_file}: {e}")
        
        return interrupted
    
    def mark_cycle_completed(self, report_id: str) -> bool:
        """
        标记循环已完成
        
        Args:
            report_id: 报告ID
            
        Returns:
            bool: 是否成功
        """
        state = self.load_cycle_state(report_id)
        
        if not state:
            return False
        
        state["status"] = "completed"
        state["completed_at"] = datetime.now().isoformat()
        
        state_file = self.state_dir / f"{report_id}.json"
        
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        if report_id in self._active_cycles:
            del self._active_cycles[report_id]
        
        self.logger.info(f"循环已标记为完成: {report_id}")
        
        return True
    
    def cleanup_old_states(self, max_age_days: int = 7) -> int:
        """
        清理旧状态文件
        
        Args:
            max_age_days: 最大保留天数
            
        Returns:
            int: 清理的文件数量
        """
        cleaned = 0
        cutoff = datetime.now() - timedelta(days=max_age_days)
        
        for state_file in self.state_dir.glob("*.json"):
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                
                saved_at = datetime.fromisoformat(state.get("saved_at", ""))
                
                if saved_at < cutoff or state.get("status") == "completed":
                    state_file.unlink()
                    cleaned += 1
                    
                    if state["report_id"] in self._active_cycles:
                        del self._active_cycles[state["report_id"]]
            except Exception as e:
                self.logger.error(f"清理状态文件失败 {state_file}: {e}")
        
        self.logger.info(f"清理了 {cleaned} 个旧状态文件")
        
        return cleaned
    
    def create_checkpoint(
        self,
        report_id: str,
        iteration: int,
        phase: str,
        data: Dict[str, Any]
    ) -> str:
        """
        创建检查点
        
        Args:
            report_id: 报告ID
            iteration: 迭代索引
            phase: 阶段名称
            data: 检查点数据
            
        Returns:
            str: 检查点ID
        """
        checkpoint_id = f"{report_id}_iter{iteration}_{phase}"
        
        checkpoint = {
            "checkpoint_id": checkpoint_id,
            "report_id": report_id,
            "iteration": iteration,
            "phase": phase,
            "data": data,
            "created_at": datetime.now().isoformat()
        }
        
        checkpoint_file = self.state_dir / "checkpoints" / f"{checkpoint_id}.json"
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2)
        
        return checkpoint_id
    
    def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        加载检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            Optional[Dict[str, Any]]: 检查点数据
        """
        checkpoint_file = self.state_dir / "checkpoints" / f"{checkpoint_id}.json"
        
        if not checkpoint_file.exists():
            return None
        
        with open(checkpoint_file, "r", encoding="utf-8") as f:
            return json.load(f)


class EnhancedCycleExecutor:
    """
    增强的循环执行器
    
    提供增强的循环执行功能：
    - 自动中断检测
    - 智能恢复
    - 进度报告
    - 错误处理增强
    """
    
    def __init__(
        self,
        output_dir: Path,
        recovery_manager: CycleRecoveryManager,
        logger: Optional[logging.Logger] = None
    ):
        self.output_dir = output_dir
        self.recovery_manager = recovery_manager
        self.logger = logger or self._setup_logger()
        self._interrupt_requested = False
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("EnhancedCycleExecutor")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def execute_with_recovery(
        self,
        spec: ParsedSpecification,
        cycle_executor: RedGreenBlueCycleExecutor,
        options: Optional[Dict[str, Any]] = None
    ) -> CycleExecutionReport:
        """
        执行循环并支持恢复
        
        Args:
            spec: 解析后的规范
            cycle_executor: 循环执行器
            options: 执行选项
            
        Returns:
            CycleExecutionReport: 循环执行报告
        """
        options = options or {}
        resume_from = options.get("resume_from")
        
        if resume_from:
            recovery_point = self.recovery_manager.get_recovery_point(resume_from)
            
            if recovery_point:
                self.logger.info(f"从恢复点继续执行: {resume_from}")
                return self._resume_execution(spec, cycle_executor, recovery_point, options)
        
        return self._execute_new_cycle(spec, cycle_executor, options)
    
    def _execute_new_cycle(
        self,
        spec: ParsedSpecification,
        cycle_executor: RedGreenBlueCycleExecutor,
        options: Dict[str, Any]
    ) -> CycleExecutionReport:
        """执行新的循环"""
        self.logger.info("开始新的循环执行...")
        
        report = cycle_executor.execute_cycle(
            spec,
            dry_run=options.get("dry_run", False)
        )
        
        return report
    
    def _resume_execution(
        self,
        spec: ParsedSpecification,
        cycle_executor: RedGreenBlueCycleExecutor,
        recovery_point: Dict[str, Any],
        options: Dict[str, Any]
    ) -> CycleExecutionReport:
        """从恢复点继续执行"""
        self.logger.info(f"从迭代 {recovery_point['resume_from_iteration']} 恢复执行")
        
        report = cycle_executor.resume_cycle(
            recovery_point["report_id"]
        )
        
        self.recovery_manager.mark_cycle_completed(recovery_point["report_id"])
        
        return report
    
    def request_interrupt(self) -> None:
        """请求中断执行"""
        self._interrupt_requested = True
        self.logger.info("已请求中断循环执行")
    
    def is_interrupt_requested(self) -> bool:
        """检查是否请求了中断"""
        return self._interrupt_requested


class SDDTDDFullIntegration:
    """SDD-TDD完整集成器
    
    整合所有增强功能，提供完整的规范驱动开发与测试驱动开发集成流程：
    1. 规范到测试的自动映射
    2. 测试到代码的自动生成
    3. 代码到规范的逆向验证
    4. 完整循环验证
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        
        self.spec_to_test_mapper = SpecToTestIntelligentMapper(logger)
        self.test_to_code_generator = TestToCodeGenerator(logger)
        self.code_to_spec_verifier = CodeToSpecVerifier(logger)
        self.full_cycle_validator = FullCycleValidator(logger)
        
        self._integration_history: List[Dict[str, Any]] = []
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("SDDTDDFullIntegration")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def run_full_integration_pipeline(
        self,
        spec: ParsedSpecification,
        code_content: Optional[str] = None,
        language: str = "python",
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """运行完整集成管道"""
        options = options or {}
        
        result = {
            "integration_id": f"INTEGRATION-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "started_at": datetime.now().isoformat(),
            "spec_info": {
                "id": spec.spec_id,
                "name": spec.spec_name,
                "version": spec.version
            },
            "phases": {},
            "overall_status": "unknown",
            "recommendations": []
        }
        
        self.logger.info("=" * 60)
        self.logger.info("开始SDD-TDD完整集成流程")
        self.logger.info("=" * 60)
        
        self.logger.info("\n[阶段1] 规范到测试的自动映射...")
        test_scenarios = self.spec_to_test_mapper.extract_test_scenarios(spec)
        
        api_tests = []
        for iface in spec.interfaces:
            api_tests.extend(self.spec_to_test_mapper.generate_api_tests(iface, spec))
        
        data_tests = []
        for model in spec.data_models:
            data_tests.extend(self.spec_to_test_mapper.generate_data_validation_tests(model, spec))
        
        biz_tests = []
        for rule in spec.behavior_rules:
            biz_tests.extend(self.spec_to_test_mapper.generate_business_logic_tests(rule, spec))
        
        all_test_cases = api_tests + data_tests + biz_tests
        
        result["phases"]["spec_to_test"] = {
            "status": "completed",
            "test_scenarios_count": len(test_scenarios),
            "api_tests_count": len(api_tests),
            "data_tests_count": len(data_tests),
            "business_tests_count": len(biz_tests),
            "total_tests_count": len(all_test_cases)
        }
        
        self.logger.info(f"  生成测试场景: {len(test_scenarios)}")
        self.logger.info(f"  生成API测试: {len(api_tests)}")
        self.logger.info(f"  生成数据验证测试: {len(data_tests)}")
        self.logger.info(f"  生成业务逻辑测试: {len(biz_tests)}")
        
        self.logger.info("\n[阶段2] 测试到代码的自动生成...")
        requirements = self.test_to_code_generator.extract_requirements_from_tests(all_test_cases)
        
        generated_code = ""
        if options.get("generate_code", True):
            generated_code = self.test_to_code_generator.generate_minimal_implementation(
                all_test_cases, language
            )
        
        dependencies = self.test_to_code_generator.handle_dependencies(all_test_cases, spec)
        
        result["phases"]["test_to_code"] = {
            "status": "completed",
            "requirements_count": len(requirements),
            "generated_code_lines": len(generated_code.split("\n")) if generated_code else 0,
            "dependencies_count": sum(len(deps) for deps in dependencies.values())
        }
        
        self.logger.info(f"  提取功能需求: {len(requirements)}")
        self.logger.info(f"  生成代码行数: {result['phases']['test_to_code']['generated_code_lines']}")
        self.logger.info(f"  处理依赖关系: {len(dependencies)} 个元素")
        
        self.logger.info("\n[阶段3] 代码到规范的逆向验证...")
        if code_content:
            verification_report = self.code_to_spec_verifier.verify_code_against_spec(
                code_content, spec, language
            )
            
            result["phases"]["code_to_spec"] = {
                "status": "completed",
                "alignment_score": verification_report["summary"]["overall_alignment"],
                "inconsistencies_count": verification_report["summary"]["inconsistency_count"],
                "missing_in_code": verification_report["summary"]["missing_in_code"],
                "missing_in_spec": verification_report["summary"]["missing_in_spec"]
            }
            
            self.logger.info(f"  对齐度: {verification_report['summary']['overall_alignment']:.1f}%")
            self.logger.info(f"  不一致数: {verification_report['summary']['inconsistency_count']}")
        else:
            result["phases"]["code_to_spec"] = {
                "status": "skipped",
                "reason": "未提供代码内容"
            }
            self.logger.info("  跳过（未提供代码内容）")
        
        self.logger.info("\n[阶段4] 完整循环验证...")
        if code_content:
            cycle_report = self.full_cycle_validator.generate_full_cycle_report(
                spec, all_test_cases, code_content, language
            )
            
            result["phases"]["full_cycle"] = {
                "status": "completed",
                "overall_status": cycle_report["overall_status"],
                "consistency_score": cycle_report["validation_results"]["consistency"]["overall_consistency"],
                "coverage_score": cycle_report["validation_results"]["coverage"]["overall_coverage"],
                "quality_score": cycle_report["validation_results"]["quality"]["overall_score"]
            }
            
            self.logger.info(f"  整体状态: {cycle_report['overall_status']}")
            self.logger.info(f"  一致性得分: {cycle_report['validation_results']['consistency']['overall_consistency']:.1f}%")
            self.logger.info(f"  覆盖率得分: {cycle_report['validation_results']['coverage']['overall_coverage']:.1f}%")
            self.logger.info(f"  质量得分: {cycle_report['validation_results']['quality']['overall_score']:.1f}%")
            
            result["recommendations"] = cycle_report.get("recommendations", [])
        else:
            result["phases"]["full_cycle"] = {
                "status": "partial",
                "message": "仅执行规范-测试验证"
            }
            
            coverage = self.full_cycle_validator.validate_test_coverage(all_test_cases, spec)
            result["phases"]["full_cycle"]["coverage_score"] = coverage["overall_coverage"]
            result["recommendations"] = coverage.get("recommendations", [])
            
            self.logger.info(f"  覆盖率得分: {coverage['overall_coverage']:.1f}%")
        
        phase_scores = []
        for phase_name, phase_data in result["phases"].items():
            if phase_data.get("status") == "completed":
                if "alignment_score" in phase_data:
                    phase_scores.append(phase_data["alignment_score"])
                elif "consistency_score" in phase_data:
                    phase_scores.append(phase_data["consistency_score"])
                elif "coverage_score" in phase_data:
                    phase_scores.append(phase_data["coverage_score"])
        
        if phase_scores:
            avg_score = sum(phase_scores) / len(phase_scores)
            if avg_score >= 80:
                result["overall_status"] = "excellent"
            elif avg_score >= 60:
                result["overall_status"] = "good"
            elif avg_score >= 40:
                result["overall_status"] = "acceptable"
            else:
                result["overall_status"] = "needs_improvement"
        else:
            result["overall_status"] = "completed"
        
        result["completed_at"] = datetime.now().isoformat()
        
        self._integration_history.append(result)
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info(f"集成流程完成: {result['overall_status']}")
        self.logger.info("=" * 60)
        
        return result
    
    def map_spec_to_tests(
        self,
        spec: ParsedSpecification
    ) -> Dict[str, Any]:
        """仅执行规范到测试的映射"""
        self.logger.info("执行规范到测试的映射...")
        
        scenarios = self.spec_to_test_mapper.extract_test_scenarios(spec)
        
        api_tests = []
        for iface in spec.interfaces:
            api_tests.extend(self.spec_to_test_mapper.generate_api_tests(iface, spec))
        
        data_tests = []
        for model in spec.data_models:
            data_tests.extend(self.spec_to_test_mapper.generate_data_validation_tests(model, spec))
        
        biz_tests = []
        for rule in spec.behavior_rules:
            biz_tests.extend(self.spec_to_test_mapper.generate_business_logic_tests(rule, spec))
        
        return {
            "scenarios": scenarios,
            "api_tests": api_tests,
            "data_tests": data_tests,
            "business_tests": biz_tests,
            "total_tests": len(api_tests) + len(data_tests) + len(biz_tests)
        }
    
    def generate_code_from_tests(
        self,
        test_cases: List[GeneratedTestCase],
        spec: ParsedSpecification,
        language: str = "python"
    ) -> Dict[str, Any]:
        """仅执行测试到代码的生成"""
        self.logger.info("执行测试到代码的生成...")
        
        requirements = self.test_to_code_generator.extract_requirements_from_tests(test_cases)
        
        code = self.test_to_code_generator.generate_minimal_implementation(
            test_cases, language
        )
        
        dependencies = self.test_to_code_generator.handle_dependencies(test_cases, spec)
        
        return {
            "requirements": requirements,
            "generated_code": code,
            "dependencies": dependencies,
            "language": language
        }
    
    def verify_code_against_spec(
        self,
        code_content: str,
        spec: ParsedSpecification,
        language: str = "python"
    ) -> Dict[str, Any]:
        """仅执行代码到规范的验证"""
        self.logger.info("执行代码到规范的验证...")
        
        return self.code_to_spec_verifier.verify_code_against_spec(
            code_content, spec, language
        )
    
    def validate_full_cycle(
        self,
        spec: ParsedSpecification,
        test_cases: List[GeneratedTestCase],
        code_content: str,
        language: str = "python"
    ) -> Dict[str, Any]:
        """仅执行完整循环验证"""
        self.logger.info("执行完整循环验证...")
        
        return self.full_cycle_validator.generate_full_cycle_report(
            spec, test_cases, code_content, language
        )
    
    def get_integration_history(self) -> List[Dict[str, Any]]:
        """获取集成历史"""
        return self._integration_history.copy()
    
    def export_integration_report(
        self,
        result: Dict[str, Any],
        format_type: str = "json"
    ) -> str:
        """导出集成报告"""
        if format_type == "json":
            return json.dumps(result, ensure_ascii=False, indent=2)
        elif format_type == "markdown":
            return self._generate_markdown_report(result)
        else:
            return str(result)
    
    def _generate_markdown_report(self, result: Dict[str, Any]) -> str:
        """生成Markdown格式报告"""
        lines = [
            f"# SDD-TDD集成报告",
            f"",
            f"**集成ID**: {result['integration_id']}",
            f"**开始时间**: {result['started_at']}",
            f"**完成时间**: {result.get('completed_at', 'N/A')}",
            f"**整体状态**: {result['overall_status']}",
            f"",
            f"## 规范信息",
            f"",
            f"- **ID**: {result['spec_info']['id']}",
            f"- **名称**: {result['spec_info']['name']}",
            f"- **版本**: {result['spec_info']['version']}",
            f"",
            f"## 执行阶段",
            f""
        ]
        
        for phase_name, phase_data in result["phases"].items():
            lines.append(f"### {phase_name}")
            lines.append(f"")
            lines.append(f"- **状态**: {phase_data.get('status', 'unknown')}")
            
            for key, value in phase_data.items():
                if key != "status":
                    lines.append(f"- **{key}**: {value}")
            lines.append("")
        
        if result.get("recommendations"):
            lines.append(f"## 建议")
            lines.append(f"")
            for rec in result["recommendations"]:
                lines.append(f"- {rec}")
            lines.append("")
        
        return "\n".join(lines)


if __name__ == "__main__":
    main()
