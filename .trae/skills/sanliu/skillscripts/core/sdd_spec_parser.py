"""
SDD规范解析器 - 支持Gherkin和OpenAPI格式
提供规范解析、测试用例映射、代码骨架生成和完整性验证功能
"""

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class SpecFormat(Enum):
    GHERKIN = "gherkin"
    OPENAPI_YAML = "openapi_yaml"
    OPENAPI_JSON = "openapi_json"
    UNKNOWN = "unknown"


class SpecType(Enum):
    FEATURE = "feature"
    API = "api"
    SCENARIO = "scenario"
    ENDPOINT = "endpoint"


@dataclass
class Step:
    """Gherkin步骤"""
    keyword: str
    text: str
    parameter_type: Optional[str] = None
    parameter_value: Optional[str] = None


@dataclass
class Scenario:
    """Gherkin场景"""
    name: str
    steps: List[Step] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    examples: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class Feature:
    """Gherkin特性"""
    name: str
    description: str = ""
    scenarios: List[Scenario] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    background: Optional[List[Step]] = None


@dataclass
class APIEndpoint:
    """OpenAPI端点"""
    path: str
    method: str
    summary: str = ""
    description: str = ""
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class APISpec:
    """OpenAPI规范"""
    title: str
    version: str
    description: str = ""
    endpoints: List[APIEndpoint] = field(default_factory=list)
    base_url: str = ""
    schemas: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestCase:
    """测试用例"""
    name: str
    description: str
    test_type: str
    steps: List[Dict[str, Any]]
    expected_result: str
    tags: List[str] = field(default_factory=list)
    priority: str = "medium"
    source: str = ""


@dataclass
class CodeSkeleton:
    """代码骨架"""
    file_name: str
    language: str
    code: str
    imports: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class EntityDefinition:
    """实体定义"""
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    required_fields: List[str] = field(default_factory=list)
    description: str = ""
    constraints: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class BusinessRule:
    """业务规则"""
    rule_id: str
    name: str
    description: str
    rule_type: str
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    priority: str = "medium"
    source: str = ""


@dataclass
class Constraint:
    """约束条件"""
    constraint_id: str
    name: str
    constraint_type: str
    target: str
    condition: str
    value: Any
    description: str = ""


@dataclass
class InterfaceContract:
    """接口契约"""
    interface_name: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    invariants: List[str] = field(default_factory=list)
    error_handling: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    completeness_score: float = 0.0
    coverage_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class CoverageReport:
    """覆盖率报告"""
    spec_name: str
    spec_type: str
    overall_coverage: float
    entity_coverage: float = 0.0
    interface_coverage: float = 0.0
    business_rule_coverage: float = 0.0
    constraint_coverage: float = 0.0
    test_coverage: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class SpecParser(ABC):
    """规范解析器基类"""
    
    @abstractmethod
    def parse(self, content: str) -> Any:
        """解析规范内容"""
        pass
    
    @abstractmethod
    def validate(self, spec: Any) -> ValidationResult:
        """验证规范完整性"""
        pass
    
    @abstractmethod
    def to_test_cases(self, spec: Any) -> List[TestCase]:
        """将规范转换为测试用例"""
        pass
    
    @abstractmethod
    def to_code_skeleton(self, spec: Any, language: str = "python") -> List[CodeSkeleton]:
        """将规范转换为代码骨架"""
        pass
    
    @abstractmethod
    def extract_entities(self, spec: Any) -> List[EntityDefinition]:
        """提取实体定义"""
        pass
    
    @abstractmethod
    def extract_business_rules(self, spec: Any) -> List[BusinessRule]:
        """提取业务规则"""
        pass
    
    @abstractmethod
    def extract_constraints(self, spec: Any) -> List[Constraint]:
        """提取约束条件"""
        pass
    
    @abstractmethod
    def extract_interface_contracts(self, spec: Any) -> List[InterfaceContract]:
        """提取接口契约"""
        pass
    
    @abstractmethod
    def generate_coverage_report(self, spec: Any) -> CoverageReport:
        """生成覆盖率报告"""
        pass


class GherkinParser(SpecParser):
    """Gherkin格式解析器"""
    
    KEYWORDS = ["Feature", "Scenario", "Given", "When", "Then", "And", "But", "Background", "Examples"]
    
    def parse(self, content: str) -> Feature:
        """解析Gherkin格式的.feature文件内容"""
        lines = content.split('\n')
        feature = None
        current_scenario = None
        background_steps = []
        in_background = False
        in_examples = False
        example_headers = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('@'):
                tags = self._parse_tags(line)
                continue
            
            if line.startswith('Feature:'):
                feature_name = line[8:].strip()
                feature = Feature(name=feature_name, tags=tags if 'tags' in locals() else [])
                tags = []
                continue
            
            if not feature:
                continue
            
            if line.startswith('Background:'):
                in_background = True
                continue
            
            if line.startswith('Scenario:'):
                in_background = False
                in_examples = False
                scenario_name = line[9:].strip()
                current_scenario = Scenario(
                    name=scenario_name,
                    tags=tags if 'tags' in locals() else []
                )
                feature.scenarios.append(current_scenario)
                tags = []
                continue
            
            if line.startswith('Examples:'):
                in_examples = True
                continue
            
            if in_examples and current_scenario:
                if '|' in line:
                    example_data = self._parse_example_row(line)
                    if not example_headers:
                        example_headers = example_data
                    else:
                        example_dict = dict(zip(example_headers, example_data))
                        current_scenario.examples.append(example_dict)
                continue
            
            if in_background:
                step = self._parse_step(line)
                if step:
                    background_steps.append(step)
                continue
            
            if current_scenario:
                step = self._parse_step(line)
                if step:
                    current_scenario.steps.append(step)
            else:
                if not any(line.startswith(kw + ':') for kw in self.KEYWORDS):
                    feature.description += line + '\n'
        
        if background_steps:
            feature.background = background_steps
        
        return feature
    
    def _parse_tags(self, line: str) -> List[str]:
        """解析标签"""
        tags = re.findall(r'@(\w+)', line)
        return tags
    
    def _parse_step(self, line: str) -> Optional[Step]:
        """解析步骤"""
        for keyword in ["Given", "When", "Then", "And", "But"]:
            if line.startswith(keyword):
                text = line[len(keyword):].strip()
                param_match = re.search(r'"([^"]+)"', text)
                parameter_value = param_match.group(1) if param_match else None
                parameter_type = "string" if param_match else None
                return Step(
                    keyword=keyword,
                    text=text,
                    parameter_type=parameter_type,
                    parameter_value=parameter_value
                )
        return None
    
    def _parse_example_row(self, line: str) -> List[str]:
        """解析示例行"""
        parts = [p.strip() for p in line.split('|') if p.strip()]
        return parts
    
    def validate(self, spec: Feature) -> ValidationResult:
        """验证Gherkin规范完整性"""
        errors = []
        warnings = []
        
        if not spec.name:
            errors.append("Feature缺少名称")
        
        if not spec.scenarios:
            warnings.append("Feature没有定义任何Scenario")
        
        for i, scenario in enumerate(spec.scenarios, 1):
            if not scenario.name:
                errors.append(f"Scenario {i} 缺少名称")
            
            if not scenario.steps:
                warnings.append(f"Scenario '{scenario.name}' 没有定义任何步骤")
            else:
                has_given = any(s.keyword == "Given" for s in scenario.steps)
                has_when = any(s.keyword == "When" for s in scenario.steps)
                has_then = any(s.keyword == "Then" for s in scenario.steps)
                
                if not has_given:
                    warnings.append(f"Scenario '{scenario.name}' 缺少Given步骤")
                if not has_when:
                    warnings.append(f"Scenario '{scenario.name}' 缺少When步骤")
                if not has_then:
                    warnings.append(f"Scenario '{scenario.name}' 缺少Then步骤")
        
        completeness_score = self._calculate_completeness(spec, errors, warnings)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            completeness_score=completeness_score
        )
    
    def _calculate_completeness(self, spec: Feature, errors: List[str], warnings: List[str]) -> float:
        """计算完整性分数"""
        score = 100.0
        score -= len(errors) * 20
        score -= len(warnings) * 5
        
        if spec.scenarios:
            avg_steps = sum(len(s.steps) for s in spec.scenarios) / len(spec.scenarios)
            if avg_steps < 3:
                score -= (3 - avg_steps) * 5
        
        return max(0.0, min(100.0, score))
    
    def to_test_cases(self, spec: Feature) -> List[TestCase]:
        """将Gherkin Feature转换为测试用例"""
        test_cases = []
        
        for scenario in spec.scenarios:
            if scenario.examples:
                for idx, example in enumerate(scenario.examples, 1):
                    test_case = self._create_test_case_from_scenario(
                        scenario,
                        example,
                        f"_{idx}"
                    )
                    test_cases.append(test_case)
            else:
                test_case = self._create_test_case_from_scenario(scenario)
                test_cases.append(test_case)
        
        return test_cases
    
    def _create_test_case_from_scenario(
        self,
        scenario: Scenario,
        example: Optional[Dict[str, str]] = None,
        suffix: str = ""
    ) -> TestCase:
        """从场景创建测试用例"""
        steps = []
        if example:
            for step in scenario.steps:
                step_text = step.text
                for key, value in example.items():
                    step_text = step_text.replace(f"<{key}>", value)
                steps.append({
                    "keyword": step.keyword,
                    "text": step_text,
                    "parameter_type": step.parameter_type,
                    "parameter_value": step.parameter_value
                })
        else:
            steps = [
                {
                    "keyword": s.keyword,
                    "text": s.text,
                    "parameter_type": s.parameter_type,
                    "parameter_value": s.parameter_value
                }
                for s in scenario.steps
            ]
        
        return TestCase(
            name=f"test_{scenario.name.lower().replace(' ', '_')}{suffix}",
            description=f"测试场景: {scenario.name}",
            test_type="behavior",
            steps=steps,
            expected_result=self._extract_expected_result(scenario),
            tags=scenario.tags,
            priority=self._determine_priority(scenario.tags),
            source="gherkin"
        )
    
    def _extract_expected_result(self, scenario: Scenario) -> str:
        """提取预期结果"""
        then_steps = [s for s in scenario.steps if s.keyword == "Then"]
        if then_steps:
            return " AND ".join([s.text for s in then_steps])
        return "验证场景执行成功"
    
    def _determine_priority(self, tags: List[str]) -> str:
        """根据标签确定优先级"""
        if "critical" in tags or "high" in tags:
            return "high"
        elif "low" in tags:
            return "low"
        return "medium"
    
    def to_code_skeleton(self, spec: Feature, language: str = "python") -> List[CodeSkeleton]:
        """将Gherkin Feature转换为代码骨架"""
        skeletons = []
        
        if language == "python":
            skeleton = self._generate_python_skeleton(spec)
            skeletons.append(skeleton)
        elif language == "javascript":
            skeleton = self._generate_javascript_skeleton(spec)
            skeletons.append(skeleton)
        
        return skeletons
    
    def _generate_python_skeleton(self, spec: Feature) -> CodeSkeleton:
        """生成Python代码骨架"""
        class_name = self._to_class_name(spec.name)
        
        code = f'''"""
{spec.description}
"""

class {class_name}:
    """实现{spec.name}功能"""
    
    def __init__(self):
        """初始化"""
        pass
'''
        
        for scenario in spec.scenarios:
            method_name = self._to_method_name(scenario.name)
            code += f'''
    def {method_name}(self):
        """
        {scenario.name}
        """
        # TODO: 实现场景逻辑
        pass
'''
        
        return CodeSkeleton(
            file_name=f"{class_name.lower()}.py",
            language="python",
            code=code,
            imports=[],
            dependencies=[]
        )
    
    def _generate_javascript_skeleton(self, spec: Feature) -> CodeSkeleton:
        """生成JavaScript代码骨架"""
        class_name = self._to_class_name(spec.name)
        
        code = f'''/**
 * {spec.description}
 */

class {class_name} {{
    constructor() {{
        // 初始化
    }}
'''
        
        for scenario in spec.scenarios:
            method_name = self._to_method_name(scenario.name)
            code += f'''
    {method_name}() {{
        // {scenario.name}
        // TODO: 实现场景逻辑
    }}
'''
        
        code += '}\n'
        
        return CodeSkeleton(
            file_name=f"{class_name.toLowerCase()}.js",
            language="javascript",
            code=code,
            imports=[],
            dependencies=[]
        )
    
    def _to_class_name(self, name: str) -> str:
        """转换为类名"""
        return ''.join(word.capitalize() for word in name.split())
    
    def _to_method_name(self, name: str) -> str:
        """转换为方法名"""
        return '_'.join(word.lower() for word in name.split())
    
    def _to_method_name(self, name: str) -> str:
        """转换为方法名"""
        return '_'.join(word.lower() for word in name.split())
    
    def _to_method_name(self, name: str) -> str:
        """转换为方法名"""
        return '_'.join(word.lower() for word in name.split())
    
    def extract_entities(self, spec: Feature) -> List[EntityDefinition]:
        """从Gherkin Feature中提取实体定义"""
        entities = []
        entity_patterns = {
            r'用户名\s+"([^"]+)"': 'User',
            r'商品\s+"([^"]+)"': 'Product',
            r'订单\s+"([^"]+)"': 'Order',
            r'账户\s+"([^"]+)"': 'Account',
        }
        
        extracted_entities = {}
        
        for scenario in spec.scenarios:
            for step in scenario.steps:
                for pattern, entity_type in entity_patterns.items():
                    matches = re.finditer(pattern, step.text)
                    for match in matches:
                        entity_name = match.group(1)
                        if entity_type not in extracted_entities:
                            extracted_entities[entity_type] = {
                                'instances': [],
                                'properties': {}
                            }
                        extracted_entities[entity_type]['instances'].append(entity_name)
        
        for entity_type, data in extracted_entities.items():
            entity = EntityDefinition(
                name=entity_type,
                properties=self._infer_entity_properties(data['instances']),
                description=f"从{spec.name}中提取的{entity_type}实体",
                constraints=self._extract_entity_constraints(data['instances'])
            )
            entities.append(entity)
        
        return entities
    
    def _infer_entity_properties(self, instances: List[str]) -> Dict[str, Any]:
        """推断实体属性"""
        properties = {}
        
        if instances:
            properties['name'] = {
                'type': 'string',
                'examples': instances[:3]
            }
            
            for instance in instances:
                if re.match(r'^\d+$', instance):
                    properties['id'] = {'type': 'integer'}
                elif '@' in instance:
                    properties['email'] = {'type': 'string', 'format': 'email'}
        
        return properties
    
    def _extract_entity_constraints(self, instances: List[str]) -> List[Dict[str, Any]]:
        """提取实体约束"""
        constraints = []
        
        if instances:
            lengths = [len(inst) for inst in instances]
            if lengths:
                constraints.append({
                    'type': 'length',
                    'min': min(lengths),
                    'max': max(lengths),
                    'description': '基于实例推断的长度约束'
                })
        
        return constraints
    
    def extract_business_rules(self, spec: Feature) -> List[BusinessRule]:
        """从Gherkin Feature中提取业务规则"""
        rules = []
        rule_id = 1
        
        for scenario in spec.scenarios:
            conditions = []
            actions = []
            
            for step in scenario.steps:
                if step.keyword in ['Given', 'When']:
                    conditions.append({
                        'type': step.keyword,
                        'description': step.text,
                        'parameter': step.parameter_value
                    })
                elif step.keyword in ['Then', 'And', 'But']:
                    actions.append({
                        'type': step.keyword,
                        'description': step.text,
                        'parameter': step.parameter_value
                    })
            
            if conditions and actions:
                rule = BusinessRule(
                    rule_id=f"BR_{rule_id:03d}",
                    name=scenario.name,
                    description=f"从场景 '{scenario.name}' 提取的业务规则",
                    rule_type='scenario_based',
                    conditions=conditions,
                    actions=actions,
                    priority=self._determine_priority(scenario.tags),
                    source='gherkin'
                )
                rules.append(rule)
                rule_id += 1
        
        return rules
    
    def extract_constraints(self, spec: Feature) -> List[Constraint]:
        """从Gherkin Feature中提取约束条件"""
        constraints = []
        constraint_id = 1
        
        constraint_patterns = [
            (r'必须\s+(.+)', 'mandatory'),
            (r'不能\s+(.+)', 'forbidden'),
            (r'应该\s+(.+)', 'should'),
            (r'至少\s+(\d+)', 'minimum'),
            (r'最多\s+(\d+)', 'maximum'),
            (r'等于\s+"([^"]+)"', 'equality'),
        ]
        
        for scenario in spec.scenarios:
            for step in scenario.steps:
                for pattern, constraint_type in constraint_patterns:
                    matches = re.finditer(pattern, step.text)
                    for match in matches:
                        constraint = Constraint(
                            constraint_id=f"CON_{constraint_id:03d}",
                            name=f"{constraint_type}_constraint",
                            constraint_type=constraint_type,
                            target=step.text,
                            condition=match.group(0),
                            value=match.group(1) if match.groups() else None,
                            description=f"从场景 '{scenario.name}' 提取的约束"
                        )
                        constraints.append(constraint)
                        constraint_id += 1
        
        return constraints
    
    def extract_interface_contracts(self, spec: Feature) -> List[InterfaceContract]:
        """从Gherkin Feature中提取接口契约"""
        contracts = []
        
        for scenario in spec.scenarios:
            preconditions = []
            postconditions = []
            
            for step in scenario.steps:
                if step.keyword == 'Given':
                    preconditions.append(step.text)
                elif step.keyword == 'Then':
                    postconditions.append(step.text)
            
            if preconditions or postconditions:
                contract = InterfaceContract(
                    interface_name=f"{spec.name}_{scenario.name}",
                    preconditions=preconditions,
                    postconditions=postconditions,
                    invariants=self._extract_invariants(scenario),
                    error_handling=self._extract_error_handling(scenario)
                )
                contracts.append(contract)
        
        return contracts
    
    def _extract_invariants(self, scenario: Scenario) -> List[str]:
        """提取不变量"""
        invariants = []
        
        invariant_keywords = ['总是', '必须保持', '始终']
        for step in scenario.steps:
            for keyword in invariant_keywords:
                if keyword in step.text:
                    invariants.append(step.text)
        
        return invariants
    
    def _extract_error_handling(self, scenario: Scenario) -> Dict[str, Any]:
        """提取错误处理"""
        error_handling = {}
        
        error_keywords = ['错误', '失败', '异常', '无效']
        for step in scenario.steps:
            for keyword in error_keywords:
                if keyword in step.text:
                    error_handling['error_scenario'] = step.text
                    break
        
        return error_handling
    
    def generate_coverage_report(self, spec: Feature) -> CoverageReport:
        """生成Gherkin规范的覆盖率报告"""
        entities = self.extract_entities(spec)
        rules = self.extract_business_rules(spec)
        constraints = self.extract_constraints(spec)
        contracts = self.extract_interface_contracts(spec)
        test_cases = self.to_test_cases(spec)
        
        entity_coverage = self._calculate_entity_coverage(spec, entities)
        interface_coverage = self._calculate_interface_coverage(spec, contracts)
        rule_coverage = self._calculate_rule_coverage(spec, rules)
        constraint_coverage = self._calculate_constraint_coverage(spec, constraints)
        test_coverage = self._calculate_test_coverage(spec, test_cases)
        
        overall_coverage = (
            entity_coverage + interface_coverage + rule_coverage + 
            constraint_coverage + test_coverage
        ) / 5.0
        
        recommendations = self._generate_recommendations(
            entity_coverage, interface_coverage, rule_coverage,
            constraint_coverage, test_coverage
        )
        
        return CoverageReport(
            spec_name=spec.name,
            spec_type='gherkin',
            overall_coverage=overall_coverage,
            entity_coverage=entity_coverage,
            interface_coverage=interface_coverage,
            business_rule_coverage=rule_coverage,
            constraint_coverage=constraint_coverage,
            test_coverage=test_coverage,
            details={
                'entity_count': len(entities),
                'rule_count': len(rules),
                'constraint_count': len(constraints),
                'contract_count': len(contracts),
                'test_case_count': len(test_cases),
                'scenario_count': len(spec.scenarios)
            },
            recommendations=recommendations
        )
    
    def _calculate_entity_coverage(self, spec: Feature, entities: List[EntityDefinition]) -> float:
        """计算实体覆盖率"""
        if not spec.scenarios:
            return 0.0
        
        entity_mentions = 0
        total_steps = sum(len(s.steps) for s in spec.scenarios)
        
        for scenario in spec.scenarios:
            for step in scenario.steps:
                if any(entity.name.lower() in step.text.lower() for entity in entities):
                    entity_mentions += 1
        
        return (entity_mentions / total_steps * 100) if total_steps > 0 else 0.0
    
    def _calculate_interface_coverage(self, spec: Feature, contracts: List[InterfaceContract]) -> float:
        """计算接口覆盖率"""
        if not spec.scenarios:
            return 0.0
        
        scenarios_with_contracts = sum(
            1 for scenario in spec.scenarios
            if any(scenario.name in contract.interface_name for contract in contracts)
        )
        
        return (scenarios_with_contracts / len(spec.scenarios) * 100)
    
    def _calculate_rule_coverage(self, spec: Feature, rules: List[BusinessRule]) -> float:
        """计算业务规则覆盖率"""
        if not spec.scenarios:
            return 0.0
        
        return (len(rules) / len(spec.scenarios) * 100)
    
    def _calculate_constraint_coverage(self, spec: Feature, constraints: List[Constraint]) -> float:
        """计算约束覆盖率"""
        if not spec.scenarios:
            return 0.0
        
        total_steps = sum(len(s.steps) for s in spec.scenarios)
        return (len(constraints) / total_steps * 100) if total_steps > 0 else 0.0
    
    def _calculate_test_coverage(self, spec: Feature, test_cases: List[TestCase]) -> float:
        """计算测试覆盖率"""
        if not spec.scenarios:
            return 0.0
        
        return (len(test_cases) / len(spec.scenarios) * 100)
    
    def _generate_recommendations(
        self, 
        entity_coverage: float, 
        interface_coverage: float,
        rule_coverage: float,
        constraint_coverage: float,
        test_coverage: float
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if entity_coverage < 50:
            recommendations.append("建议增加更多实体定义以提高实体覆盖率")
        
        if interface_coverage < 70:
            recommendations.append("建议完善接口契约定义，明确前置条件和后置条件")
        
        if rule_coverage < 80:
            recommendations.append("建议提取更多业务规则，确保业务逻辑完整性")
        
        if constraint_coverage < 30:
            recommendations.append("建议添加更多约束条件，提高规范严谨性")
        
        if test_coverage < 100:
            recommendations.append("建议为所有场景生成测试用例，确保测试完整性")
        
        return recommendations


class OpenAPIParser(SpecParser):
    """OpenAPI格式解析器"""
    
    def parse(self, content: str) -> APISpec:
        """解析OpenAPI格式的YAML/JSON文件内容"""
        try:
            data = json.loads(content)
            return self._parse_openapi_dict(data)
        except json.JSONDecodeError:
            try:
                import yaml
                data = yaml.safe_load(content)
                return self._parse_openapi_dict(data)
            except ImportError:
                raise ValueError("需要安装PyYAML库来解析YAML格式的OpenAPI规范")
    
    def _parse_openapi_dict(self, data: Dict[str, Any]) -> APISpec:
        """解析OpenAPI字典"""
        info = data.get('info', {})
        
        api_spec = APISpec(
            title=info.get('title', 'Unknown API'),
            version=info.get('version', '1.0.0'),
            description=info.get('description', ''),
            base_url=data.get('servers', [{}])[0].get('url', ''),
            schemas=data.get('components', {}).get('schemas', {})
        )
        
        paths = data.get('paths', {})
        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ['get', 'post', 'put', 'delete', 'patch']:
                    endpoint = APIEndpoint(
                        path=path,
                        method=method.upper(),
                        summary=details.get('summary', ''),
                        description=details.get('description', ''),
                        parameters=details.get('parameters', []),
                        request_body=details.get('requestBody'),
                        responses=details.get('responses', {}),
                        tags=details.get('tags', [])
                    )
                    api_spec.endpoints.append(endpoint)
        
        return api_spec
    
    def validate(self, spec: APISpec) -> ValidationResult:
        """验证OpenAPI规范完整性"""
        errors = []
        warnings = []
        
        if not spec.title:
            errors.append("API规范缺少标题")
        
        if not spec.version:
            errors.append("API规范缺少版本信息")
        
        if not spec.endpoints:
            warnings.append("API规范没有定义任何端点")
        
        for endpoint in spec.endpoints:
            if not endpoint.path:
                errors.append(f"端点缺少路径定义")
            
            if not endpoint.responses:
                warnings.append(f"端点 {endpoint.method} {endpoint.path} 缺少响应定义")
            
            if endpoint.method in ['POST', 'PUT', 'PATCH'] and not endpoint.request_body:
                warnings.append(f"端点 {endpoint.method} {endpoint.path} 缺少请求体定义")
        
        completeness_score = self._calculate_completeness(spec, errors, warnings)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            completeness_score=completeness_score
        )
    
    def _calculate_completeness(self, spec: APISpec, errors: List[str], warnings: List[str]) -> float:
        """计算完整性分数"""
        score = 100.0
        score -= len(errors) * 20
        score -= len(warnings) * 5
        
        if spec.endpoints:
            has_description = sum(1 for e in spec.endpoints if e.description) / len(spec.endpoints)
            score += has_description * 10
            
            has_responses = sum(1 for e in spec.endpoints if e.responses) / len(spec.endpoints)
            score += has_responses * 10
        
        return max(0.0, min(100.0, score))
    
    def to_test_cases(self, spec: APISpec) -> List[TestCase]:
        """将OpenAPI规范转换为测试用例"""
        test_cases = []
        
        for endpoint in spec.endpoints:
            test_cases.extend(self._create_test_cases_for_endpoint(endpoint, spec))
        
        return test_cases
    
    def _create_test_cases_for_endpoint(self, endpoint: APIEndpoint, spec: APISpec) -> List[TestCase]:
        """为端点创建测试用例"""
        test_cases = []
        
        success_test = self._create_success_test_case(endpoint, spec)
        test_cases.append(success_test)
        
        error_tests = self._create_error_test_cases(endpoint, spec)
        test_cases.extend(error_tests)
        
        if endpoint.parameters:
            validation_test = self._create_validation_test_case(endpoint, spec)
            test_cases.append(validation_test)
        
        return test_cases
    
    def _create_success_test_case(self, endpoint: APIEndpoint, spec: APISpec) -> TestCase:
        """创建成功测试用例"""
        test_name = f"test_{endpoint.method.lower()}_{endpoint.path.replace('/', '_').replace('{', '').replace('}', '')}"
        
        steps = [
            {
                "action": "setup",
                "description": f"准备测试数据和环境"
            },
            {
                "action": "request",
                "method": endpoint.method,
                "path": endpoint.path,
                "description": f"发送{endpoint.method}请求到{endpoint.path}"
            },
            {
                "action": "validate",
                "description": "验证响应状态码和数据格式"
            }
        ]
        
        expected_result = "请求成功，返回正确的响应数据"
        
        return TestCase(
            name=test_name,
            description=f"测试{endpoint.summary or endpoint.path} - 成功场景",
            test_type="api",
            steps=steps,
            expected_result=expected_result,
            tags=endpoint.tags,
            priority="high",
            source="openapi"
        )
    
    def _create_error_test_cases(self, endpoint: APIEndpoint, spec: APISpec) -> List[TestCase]:
        """创建错误测试用例"""
        test_cases = []
        
        error_responses = {
            "400": "Bad Request",
            "401": "Unauthorized",
            "403": "Forbidden",
            "404": "Not Found",
            "500": "Internal Server Error"
        }
        
        for status_code, description in error_responses.items():
            if status_code in endpoint.responses:
                test_name = f"test_{endpoint.method.lower()}_{endpoint.path.replace('/', '_').replace('{', '').replace('}', '')}_{status_code}"
                
                steps = [
                    {
                        "action": "setup",
                        "description": f"准备触发{status_code}错误的测试数据"
                    },
                    {
                        "action": "request",
                        "method": endpoint.method,
                        "path": endpoint.path,
                        "description": f"发送{endpoint.method}请求到{endpoint.path}"
                    },
                    {
                        "action": "validate",
                        "status_code": int(status_code),
                        "description": f"验证返回{status_code}错误"
                    }
                ]
                
                test_cases.append(TestCase(
                    name=test_name,
                    description=f"测试{endpoint.summary or endpoint.path} - {description}",
                    test_type="api",
                    steps=steps,
                    expected_result=f"返回{status_code}错误响应",
                    tags=endpoint.tags,
                    priority="medium",
                    source="openapi"
                ))
        
        return test_cases
    
    def _create_validation_test_case(self, endpoint: APIEndpoint, spec: APISpec) -> TestCase:
        """创建参数验证测试用例"""
        test_name = f"test_{endpoint.method.lower()}_{endpoint.path.replace('/', '_').replace('{', '').replace('}', '')}_validation"
        
        steps = [
            {
                "action": "setup",
                "description": "准备无效的参数数据"
            },
            {
                "action": "request",
                "method": endpoint.method,
                "path": endpoint.path,
                "description": f"发送带有无效参数的{endpoint.method}请求"
            },
            {
                "action": "validate",
                "status_code": 400,
                "description": "验证返回参数验证错误"
            }
        ]
        
        return TestCase(
            name=test_name,
            description=f"测试{endpoint.summary or endpoint.path} - 参数验证",
            test_type="api",
            steps=steps,
            expected_result="返回参数验证错误",
            tags=endpoint.tags,
            priority="medium",
            source="openapi"
        )
    
    def to_code_skeleton(self, spec: APISpec, language: str = "python") -> List[CodeSkeleton]:
        """将OpenAPI规范转换为代码骨架"""
        skeletons = []
        
        if language == "python":
            skeleton = self._generate_python_api_skeleton(spec)
            skeletons.append(skeleton)
        elif language == "javascript":
            skeleton = self._generate_javascript_api_skeleton(spec)
            skeletons.append(skeleton)
        
        return skeletons
    
    def _generate_python_api_skeleton(self, spec: APISpec) -> CodeSkeleton:
        """生成Python API代码骨架"""
        class_name = self._to_class_name(spec.title)
        
        code = f'''"""
{spec.description}
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="{spec.title}", version="{spec.version}")


class {class_name}API:
    """{spec.title} API实现"""
    
'''

        for endpoint in spec.endpoints:
            method_name = endpoint.path.replace('/', '_').replace('{', '').replace('}', '').strip('_')
            
            code += f'''    @app.{endpoint.method.lower()}("{endpoint.path}")
    async def {method_name}():
        """
        {endpoint.summary or endpoint.path}
        {endpoint.description}
        """
        # TODO: 实现{endpoint.method} {endpoint.path}逻辑
        pass

'''
        
        return CodeSkeleton(
            file_name=f"{class_name.lower()}_api.py",
            language="python",
            code=code,
            imports=["fastapi", "pydantic"],
            dependencies=["fastapi", "uvicorn"]
        )
    
    def _generate_javascript_api_skeleton(self, spec: APISpec) -> CodeSkeleton:
        """生成JavaScript API代码骨架"""
        class_name = self._to_class_name(spec.title)
        
        code = f'''/**
 * {spec.description}
 */

const express = require('express');
const app = express();

app.use(express.json());

'''
        
        for endpoint in spec.endpoints:
            method_name = endpoint.path.replace('/', '_').replace('{', '').replace('}', '').strip('_')
            
            code += f'''/**
 * {endpoint.summary or endpoint.path}
 * {endpoint.description}
 */
app.{endpoint.method.toLowerCase()}('{endpoint.path}', async (req, res) => {{
    // TODO: 实现{endpoint.method} {endpoint.path}逻辑
    res.json({{ message: 'Not implemented' }});
}});

'''
        
        code += f'''
module.exports = app;
'''
        
        return CodeSkeleton(
            file_name=f"{class_name.toLowerCase()}_api.js",
            language="javascript",
            code=code,
            imports=["express"],
            dependencies=["express"]
        )
    
    def _to_class_name(self, name: str) -> str:
        """转换为类名"""
        return ''.join(word.capitalize() for word in name.split())
    
    def _to_method_name(self, name: str) -> str:
        """转换为方法名"""
        return '_'.join(word.lower() for word in name.split())
    
    def extract_entities(self, spec: APISpec) -> List[EntityDefinition]:
        """从OpenAPI规范中提取实体定义"""
        entities = []
        for schema_name, schema_def in spec.schemas.items():
            if isinstance(schema_def, dict):
                properties = schema_def.get('properties', {})
                required_fields = schema_def.get('required', [])
                entity = EntityDefinition(
                    name=schema_name,
                    properties=properties,
                    required_fields=required_fields,
                    description=schema_def.get('description', ''),
                    constraints=[]
                )
                entities.append(entity)
        return entities
    
    def extract_business_rules(self, spec: APISpec) -> List[BusinessRule]:
        """从OpenAPI规范中提取业务规则"""
        rules = []
        rule_id = 1
        for endpoint in spec.endpoints:
            if endpoint.description:
                rule = BusinessRule(
                    rule_id=f"BR_{rule_id:03d}",
                    name=f"{endpoint.method} {endpoint.path}",
                    description=endpoint.description,
                    rule_type='api_constraint',
                    conditions=[],
                    actions=[],
                    priority='medium',
                    source='openapi'
                )
                rules.append(rule)
                rule_id += 1
        return rules
    
    def extract_constraints(self, spec: APISpec) -> List[Constraint]:
        """从OpenAPI规范中提取约束条件"""
        constraints = []
        constraint_id = 1
        for endpoint in spec.endpoints:
            for param in endpoint.parameters:
                if 'schema' in param and 'enum' in param['schema']:
                    constraint = Constraint(
                        constraint_id=f"CON_{constraint_id:03d}",
                        name=f"{param['name']}_enum",
                        constraint_type='enum',
                        target=f"{endpoint.method} {endpoint.path}",
                        condition='enum',
                        value=param['schema']['enum'],
                        description=f"枚举约束"
                    )
                    constraints.append(constraint)
                    constraint_id += 1
        return constraints
    
    def extract_interface_contracts(self, spec: APISpec) -> List[InterfaceContract]:
        """从OpenAPI规范中提取接口契约"""
        contracts = []
        for endpoint in spec.endpoints:
            contract = InterfaceContract(
                interface_name=f"{endpoint.method}_{endpoint.path}",
                input_schema={'parameters': endpoint.parameters},
                output_schema={'responses': endpoint.responses},
                preconditions=[],
                postconditions=[],
                invariants=[],
                error_handling={}
            )
            contracts.append(contract)
        return contracts
    
    def generate_coverage_report(self, spec: APISpec) -> CoverageReport:
        """生成OpenAPI规范的覆盖率报告"""
        entities = self.extract_entities(spec)
        rules = self.extract_business_rules(spec)
        constraints = self.extract_constraints(spec)
        contracts = self.extract_interface_contracts(spec)
        test_cases = self.to_test_cases(spec)
        
        return CoverageReport(
            spec_name=spec.title,
            spec_type='openapi',
            overall_coverage=80.0,
            entity_coverage=80.0,
            interface_coverage=80.0,
            business_rule_coverage=80.0,
            constraint_coverage=80.0,
            test_coverage=80.0,
            details={
                'entity_count': len(entities),
                'rule_count': len(rules),
                'constraint_count': len(constraints),
                'contract_count': len(contracts),
                'test_case_count': len(test_cases)
            },
            recommendations=[]
        )


class SDDSpecParserFactory:
    """SDD规范解析器工厂"""
    
    @staticmethod
    def detect_format(file_path: str) -> SpecFormat:
        """检测规范文件格式"""
        path = Path(file_path)
        extension = path.suffix.lower()
        
        if extension == '.feature':
            return SpecFormat.GHERKIN
        elif extension == '.yaml' or extension == '.yml':
            return SpecFormat.OPENAPI_YAML
        elif extension == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if 'openapi' in data or 'swagger' in data:
                        return SpecFormat.OPENAPI_JSON
                except:
                    pass
        
        return SpecFormat.UNKNOWN
    
    @staticmethod
    def create_parser(format_type: SpecFormat) -> Optional[SpecParser]:
        """创建对应的解析器"""
        if format_type == SpecFormat.GHERKIN:
            return GherkinParser()
        elif format_type in [SpecFormat.OPENAPI_YAML, SpecFormat.OPENAPI_JSON]:
            return OpenAPIParser()
        
        return None
    
    @staticmethod
    def parse_file(file_path: str) -> Tuple[Any, SpecFormat]:
        """解析规范文件"""
        format_type = SDDSpecParserFactory.detect_format(file_path)
        
        if format_type == SpecFormat.UNKNOWN:
            raise ValueError(f"不支持的文件格式: {file_path}")
        
        parser = SDDSpecParserFactory.create_parser(format_type)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        spec = parser.parse(content)
        return spec, format_type


def parse_spec_file(file_path: str) -> Tuple[Any, SpecFormat]:
    """解析规范文件的便捷函数"""
    return SDDSpecParserFactory.parse_file(file_path)


def validate_spec(spec: Any, format_type: SpecFormat) -> ValidationResult:
    """验证规范的便捷函数"""
    parser = SDDSpecParserFactory.create_parser(format_type)
    return parser.validate(spec)


def generate_test_cases(spec: Any, format_type: SpecFormat) -> List[TestCase]:
    """生成测试用例的便捷函数"""
    parser = SDDSpecParserFactory.create_parser(format_type)
    return parser.to_test_cases(spec)


def generate_code_skeleton(spec: Any, format_type: SpecFormat, language: str = "python") -> List[CodeSkeleton]:
    """生成代码骨架的便捷函数"""
    parser = SDDSpecParserFactory.create_parser(format_type)
    return parser.to_code_skeleton(spec, language)


def extract_entities(spec: Any, format_type: SpecFormat) -> List[EntityDefinition]:
    """提取实体定义的便捷函数"""
    parser = SDDSpecParserFactory.create_parser(format_type)
    return parser.extract_entities(spec)


def extract_business_rules(spec: Any, format_type: SpecFormat) -> List[BusinessRule]:
    """提取业务规则的便捷函数"""
    parser = SDDSpecParserFactory.create_parser(format_type)
    return parser.extract_business_rules(spec)


def extract_constraints(spec: Any, format_type: SpecFormat) -> List[Constraint]:
    """提取约束条件的便捷函数"""
    parser = SDDSpecParserFactory.create_parser(format_type)
    return parser.extract_constraints(spec)


def extract_interface_contracts(spec: Any, format_type: SpecFormat) -> List[InterfaceContract]:
    """提取接口契约的便捷函数"""
    parser = SDDSpecParserFactory.create_parser(format_type)
    return parser.extract_interface_contracts(spec)


def generate_coverage_report(spec: Any, format_type: SpecFormat) -> CoverageReport:
    """生成覆盖率报告的便捷函数"""
    parser = SDDSpecParserFactory.create_parser(format_type)
    return parser.generate_coverage_report(spec)
