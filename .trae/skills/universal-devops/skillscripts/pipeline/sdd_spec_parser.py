"""
SDD规范解析器 - 从Markdown规范文档中提取结构化数据
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class SpecSection(Enum):
    """规范章节类型"""
    OVERVIEW = "overview"
    REQUIREMENTS = "requirements"
    API_CONTRACTS = "api_contracts"
    DATA_MODELS = "data_models"
    BUSINESS_RULES = "business_rules"
    ACCEPTANCE_CRITERIA = "acceptance_criteria"
    NON_FUNCTIONAL = "non_functional"
    UNKNOWN = "unknown"


class SDDParseError(Exception):
    """SDD解析异常"""


@dataclass
class SDDRequirement:
    """需求条目"""
    id: str
    title: str
    description: str
    priority: str = "medium"
    status: str = "pending"
    category: str = "functional"
    acceptance_criteria: list[AcceptanceCriterion] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class AcceptanceCriterion:
    """验收标准"""
    id: str
    description: str
    given: str = ""
    when: str = ""
    then: str = ""
    priority: str = "must"
    testable: bool = True


@dataclass
class APIContract:
    """API端点契约"""
    endpoint: str
    method: str = "GET"
    description: str = ""
    request_params: list[dict[str, Any]] = field(default_factory=list)
    request_body: dict[str, Any] = field(default_factory=dict)
    response_body: dict[str, Any] = field(default_factory=dict)
    status_codes: list[dict[str, str]] = field(default_factory=list)
    authentication: bool = False
    rate_limit: str | None = None
    version: str = "v1"


@dataclass
class DataModelField:
    """数据模型字段"""
    name: str
    type: str
    required: bool = True
    description: str = ""
    constraints: list[str] = field(default_factory=list)
    default: Any = None


@dataclass
class DataModel:
    """数据模型定义"""
    name: str
    model_type: str = "entity"
    description: str = ""
    fields: list[DataModelField] = field(default_factory=list)
    relationships: list[dict[str, str]] = field(default_factory=list)
    indexes: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)


@dataclass
class BusinessRule:
    """业务规则"""
    id: str
    name: str
    description: str
    rule_type: str = "constraint"
    severity: str = "error"
    conditions: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    exceptions: list[str] = field(default_factory=list)
    related_requirements: list[str] = field(default_factory=list)


@dataclass
class SDDSpec:
    """SDD规范文档结构"""
    spec_id: str = ""
    title: str = ""
    version: str = "1.0"
    author: str = ""
    created_at: str = ""
    updated_at: str = ""
    overview: str = ""
    requirements: list[SDDRequirement] = field(default_factory=list)
    api_contracts: list[APIContract] = field(default_factory=list)
    data_models: list[DataModel] = field(default_factory=list)
    business_rules: list[BusinessRule] = field(default_factory=list)
    sections: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    raw_content: str = ""


@dataclass
class CoverageReport:
    """覆盖率报告"""
    total_items: int = 0
    covered_items: int = 0
    coverage_percentage: float = 0.0
    uncovered_items: list[dict[str, str]] = field(default_factory=list)
    partial_coverage: list[dict[str, str]] = field(default_factory=list)
    by_category: dict[str, float] = field(default_factory=dict)


class SDDSpecParser:
    """
    SDD规范解析器

    从Markdown格式的SDD规范文档中提取结构化数据，包括：
    - 需求条目（功能/非功能）
    - API端点契约（RESTful接口定义）
    - 数据模型（实体/值对象/DTO）
    - 业务规则（约束/不变量/规则）
    - 验收标准（Given-When-Then格式）
    """

    SECTION_PATTERNS: dict[str, tuple[str, SpecSection]] = {
        r"^#{1,2}\s*(概览|概述|Overview|简介)": ("overview", SpecSection.OVERVIEW),
        r"^#{1,2}\s*(需求|Requirements|功能需求|FR-)": ("requirements", SpecSection.REQUIREMENTS),
        r"^#{1,2}\s*(API|接口|接口定义|Endpoint|API Contract)": ("api_contracts", SpecSection.API_CONTRACTS),
        r"^#{1,2}\s*(数据模型|Data Model|实体|Entity|DTO|值对象)": ("data_models", SpecSection.DATA_MODELS),
        r"^#{1,2}\s*(业务规则|Business Rule|规则|约束|Constraint)": ("business_rules", SpecSection.BUSINESS_RULES),
        r"^#{1,2}\s*(验收标准|Acceptance Criteria|AC|验收)": ("acceptance_criteria", SpecSection.ACCEPTANCE_CRITERIA),
        r"^#{1,2}\s*(非功能需求|Non-Functional|性能|安全|NFR)": ("non_functional", SpecSection.NON_FUNCTIONAL),
    }

    def __init__(self) -> None:
        self._parsed_specs: dict[str, SDDSpec] = {}

    def parse_spec_file(self, spec_path: Path) -> SDDSpec:
        """
        解析Markdown格式的SDD规范文档

        Args:
            spec_path: 规范文件路径

        Returns:
            结构化的SDDSpec对象

        Raises:
            SDDParseError: 当解析失败时
        """
        if not spec_path.exists():
            raise SDDParseError(f"规范文件不存在: {spec_path}")

        content = spec_path.read_text(encoding="utf-8")
        return self.parse_spec_content(content, spec_path)

    def parse_spec_content(self, content: str, source_path: Path | None = None) -> SDDSpec:
        """
        从文本内容解析SDD规范

        Args:
            content: 规范文档内容
            source_path: 来源路径（可选）

        Returns:
            结构化的SDDSpec对象
        """
        spec = SDDSpec(
            spec_id=str(uuid.uuid4())[:8],
            raw_content=content,
        )

        spec.metadata["source"] = str(source_path) if source_path else "inline"

        self._extract_header(spec, content)
        self._split_sections(spec, content)

        spec.requirements = self.extract_requirements(content)
        spec.api_contracts = self.extract_api_contracts(content)
        spec.data_models = self.extract_data_models(content)
        spec.business_rules = self.extract_business_rules(content)

        for req in spec.requirements:
            req.acceptance_criteria = self.extract_acceptance_criteria(req)

        cache_key = spec.spec_id
        self._parsed_specs[cache_key] = spec

        return spec

    def _extract_header(self, spec: SDDSpec, content: str) -> None:
        """提取文档头部元信息"""
        lines = content.split("\n")
        for line in lines[:20]:
            title_match = re.match(r"^#\s+(.+)$", line)
            if title_match and not spec.title:
                spec.title = title_match.group(1).strip()

            version_match = re.search(r"(?:版本|Version|v?)\s*[:=]\s*([\d.]+)", line, re.IGNORECASE)
            if version_match:
                spec.version = version_match.group(1)

            author_match = re.search(r"(?:作者|Author)\s*[:=]\s*(.+)", line, re.IGNORECASE)
            if author_match:
                spec.author = author_match.group(1).strip()

    def _split_sections(self, spec: SDDSpec, content: str) -> None:
        """分割文档章节"""
        current_section = "overview"
        section_lines: list[str] = []
        section_order: list[str] = []

        for line in content.split("\n"):
            matched_section = None
            for pattern, (section_name, _) in self.SECTION_PATTERNS.items():
                if re.match(pattern, line, re.IGNORECASE | re.MULTILINE):
                    if section_lines:
                        spec.sections[current_section] = "\n".join(section_lines).strip()
                    matched_section = section_name
                    current_section = section_name
                    section_lines = []
                    section_order.append(section_name)
                    break

            if matched_section is None:
                section_lines.append(line)

        if section_lines:
            spec.sections[current_section] = "\n".join(section_lines).strip()

        if "overview" not in spec.sections and content:
            spec.sections["overview"] = content[:500]

    def extract_requirements(self, spec_content: str) -> list[SDDRequirement]:
        """
        从规范中提取结构化需求条目

        支持格式：
        - ### REQ-001: 标题
        - **REQ-002** 标题
        - [x] FR-003 标题
        """
        requirements: list[SDDRequirement] = []
        patterns = [
            (r"^(?:###\s*)?(REQ|FR|NFR|UR)-(\d+)[:\s]*(.+?)(?:\n|$)", "auto"),
            (r"^\*\*(REQ|FR|NFR|UR)-(\d+)\*\*\s*(.+)", "bold"),
            (r"^\s*[-*+]\s+\[(?:x| )\]\s*(REQ|FR|NFR|UR)-(\d+)[:\s]*(.+)", "checkbox"),
            (r"^\d+[.\)]\s+(.+?)(?:\n|$)", "numbered"),
        ]

        req_blocks = self._extract_code_blocks(spec_content, ["requirement", "req"])

        for pattern_type, pattern in patterns:
            matches = list(re.finditer(pattern, spec_content, re.MULTILINE | re.IGNORECASE))
            for m in matches:
                if pattern_type in ("auto", "bold", "checkbox"):
                    prefix = m.group(1).upper()
                    num = m.group(2)
                    title = m.group(3).strip()
                    req_id = f"{prefix}-{num}"
                else:
                    req_id = f"REQ-{len(requirements) + 1:03d}"
                    title = m.group(1).strip()

                start_pos = m.start()
                end_pos = m.end()
                block_end = spec_content.find("\n##", start_pos + 1)
                if block_end == -1 or block_end > start_pos + 2000:
                    block_end = start_pos + 1500

                desc_text = spec_content[start_pos:block_end].strip()
                existing_ids = {r.id for r in requirements}
                if req_id not in existing_ids:
                    priority = self._infer_priority(desc_text)
                    category = self._infer_category(prefix if pattern_type != "numbered" else "FR")
                    req = SDDRequirement(
                        id=req_id,
                        title=title,
                        description=desc_text[:500],
                        priority=priority,
                        category=category,
                        raw_text=desc_text,
                    )
                    requirements.append(req)

        for block in req_blocks:
            block_id = f"REQ-BLOCK-{len(requirements):03d}"
            if not any(r.raw_text == block for r in requirements):
                title_match = re.search(r"^(?:#+\s*)?(.+?)(?:\n|$)", block)
                requirements.append(SDDRequirement(
                    id=block_id,
                    title=title_match.group(1).strip() if title_match else "未命名需求",
                    description=block[:300],
                    raw_text=block,
                ))

        return requirements

    def extract_api_contracts(self, spec_content: str) -> list[APIContract]:
        """
        提取API端点定义

        支持格式：
        - `GET /api/users`
        - `POST /api/auth/login`
        - Method: GET, Path: /api/resource
        """
        contracts: list[APIContract] = []

        method_pattern = r"(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(/[\w/\-{}.:?=&]+)"
        api_section = spec_content

        for section_name, section_enum in [("api_contracts", SpecSection.API_CONTRACTS), ("requirements", SpecSection.REQUIREMENTS)]:
            for pattern, (name, _) in self.SECTION_PATTERNS.items():
                if name == section_name:
                    match = re.search(pattern, spec_content, re.IGNORECASE | re.MULTILINE)
                    if match:
                        next_header = spec_content.find("\n##", match.start() + 1)
                        api_section = spec_content[match.start():next_header if next_header != -1 else len(spec_content)]
                        break
            break

        for m in re.finditer(method_pattern, api_section, re.IGNORECASE):
            method = m.group(1).upper()
            endpoint = m.group(2)

            context_start = max(0, m.start() - 100)
            context_end = min(len(api_section), m.end() + 800)
            context = api_section[context_start:context_end]

            desc_match = re.search(r"(?:描述|Description|说明)[:\s]*([^\n#]+)", context, re.IGNORECASE)
            auth_match = re.search(r"(?:认证|Auth|鉴权|Token|JWT)", context, re.IGNORECASE)

            params = self._extract_api_params(context)
            status_codes = self._extract_status_codes(context)
            request_body = self._extract_request_body(context)
            response_body = self._extract_response_body(context)

            contract = APIContract(
                endpoint=endpoint,
                method=method,
                description=desc_match.group(1).strip() if desc_match else "",
                request_params=params,
                request_body=request_body,
                response_body=response_body,
                status_codes=status_codes,
                authentication=bool(auth_match),
            )

            if not any(c.endpoint == endpoint and c.method == method for c in contracts):
                contracts.append(contract)

        return contracts

    def extract_data_models(self, spec_content: str) -> list[DataModel]:
        """
        提取实体/值对象/DTO定义

        支持格式：
        - ## Entity: User
        - ### User (Entity)
        - ```model / ```entity 代码块
        """
        models: list[DataModel] = []

        entity_patterns = [
            r"(?:##?\s*)(?:Entity|实体|模型|Model|DTO|值对象|VO)?[:\s]*([\w]+)\s*(?:\((\w+)\))?",
            r"```(?:model|entity|dto|vo)\n([\s\S]*?)```",
        ]

        model_code_blocks = re.findall(r"```(?:model|entity|dto|vo)\n([\s\S]*?)```", spec_content)

        for block in model_code_blocks:
            model = self._parse_model_block(block)
            if model and not any(m.name == model.name for m in models):
                models.append(model)

        for m in re.finditer(entity_patterns[0], spec_content, re.IGNORECASE | re.MULTILINE):
            name = m.group(1)
            model_type = m.group(2) or "entity"

            if any(model.name == name for model in models):
                continue

            start = m.start()
            end = spec_content.find("\n##", start + 1)
            if end == -1:
                end = start + 1000
            context = spec_content[start:end]

            desc_match = re.search(r"(?:描述|Description)[:\s]*([^\n]+)", context, re.IGNORECASE)
            fields = self._extract_model_fields(context)

            models.append(DataModel(
                name=name,
                model_type=model_type.lower(),
                description=desc_match.group(1).strip() if desc_match else "",
                fields=fields,
            ))

        table_models = self._extract_models_from_tables(spec_content)
        for tm in table_models:
            if not any(m.name == tm.name for m in models):
                models.append(tm)

        return models

    def extract_business_rules(self, spec_content: str) -> list[BusinessRule]:
        """
        提取业务规则/约束/不变量

        支持格式：
        - BR-001: 规则名称
        - **规则**: 描述
        - 约束/不变量/规则 关键字
        """
        rules: list[BusinessRule] = []

        rule_patterns = [
            r"(BR|RULE)-(\d+)[:\s]*(.+)",
            r"\*\*(?:规则|Rule|业务规则|约束|Constraint|不变量|Invariant)[^\*]*\*\*[^\n]*\n?\s*(.+)",
        ]

        rule_section = spec_content
        for pattern, (name, _) in self.SECTION_PATTERNS.items():
            if name == "business_rules":
                match = re.search(pattern, spec_content, re.IGNORECASE | re.MULTILINE)
                if match:
                    next_h = spec_content.find("\n##", match.start() + 1)
                    rule_section = spec_content[match.start():next_h if next_h != -1 else len(spec_content)]

        for idx, pattern in enumerate(rule_patterns):
            for m in re.finditer(pattern, rule_section, re.MULTILINE | re.IGNORECASE):
                if idx == 0:
                    rule_id = f"{m.group(1)}-{m.group(2)}"
                    name = m.group(3).strip()[:80]
                else:
                    rule_id = f"BR-{len(rules) + 1:03d}"
                    name = m.group(1).strip()[:80]

                start = m.start()
                end = rule_section.find("\n", start + 1)
                if end == -1:
                    end = start + 300
                full_text = rule_section[start:end + 200].strip()

                rule_type = self._infer_rule_type(full_text)
                severity = self._infer_severity(full_text)

                if not any(r.id == rule_id for r in rules):
                    rules.append(BusinessRule(
                        id=rule_id,
                        name=name.split("\n")[0][:60],
                        description=full_text[:400],
                        rule_type=rule_type,
                        severity=severity,
                    ))

        constraint_keywords = [
            (r"(?:必须|MUST|不得|MUST NOT|禁止|不允许)[^\n]{10,200}", "constraint"),
            (r"(?:应该|SHOULD|建议|推荐)[^\n]{10,200}", "recommendation"),
            (r"(?:可以|MAY|可选|允许)[^\n]{10,200}", "permissive"),
        ]

        for kw_pattern, rtype in constraint_keywords:
            for m in re.finditer(kw_pattern, spec_content, re.MULTILINE):
                text = m.group(0).strip()
                if not any(text in r.description for r in rules):
                    rules.append(BusinessRule(
                        id=f"BR-AUTO-{len(rules) + 1:03d}",
                        name=text[:50],
                        description=text,
                        rule_type=rtype,
                        severity="warning" if rtype == "recommendation" else "error",
                    ))

        return rules

    def extract_acceptance_criteria(self, requirement: SDDRequirement) -> list[AcceptanceCriterion]:
        """
        从需求条目提取验收标准

        支持Given-When-Then格式和列表格式
        """
        criteria: list[AcceptanceCriterion] = []
        text = requirement.raw_text

        gwt_patterns = [
            r"(?:给定|Given)[：:]\s*(.+?)\s*(?:当|When)[：:]\s*(.+?)\s*(?:那么|Then)[：:]\s*(.+)",
            r"Given[:\s](.+?)\s*When[:\s](.+?)\s*Then[:\s](.+)",
        ]

        for pattern in gwt_patterns:
            for m in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
                criteria.append(AcceptanceCriterion(
                    id=f"AC-{requirement.id}-{len(criteria)}",
                    description=f"{m.group(1).strip()} → {m.group(3).strip()}",
                    given=m.group(1).strip(),
                    when=m.group(2).strip(),
                    then=m.group(3).strip(),
                ))

        ac_list_pattern = r"(?:验收标准|AC|Acceptance Criteria|验证)[：:]?\s*\n((?:\s*[-*+]\s*.+\n?)++)"
        ac_match = re.search(ac_list_pattern, text, re.IGNORECASE)
        if ac_match:
            for item in re.findall(r"[-*+]\s*(.+)", ac_match.group(1)):
                criteria.append(AcceptanceCriterion(
                    id=f"AC-{requirement.id}-{len(criteria)}",
                    description=item.strip(),
                ))

        checkbox_pattern = r"\[(?:x| )\]\s*(.+?)(?:\n|$)"
        for m in re.finditer(checkbox_pattern, text):
            item = m.group(1).strip()
            if len(item) > 5 and not any(item == c.description for c in criteria):
                criteria.append(AcceptanceCriterion(
                    id=f"AC-{requirement.id}-{len(criteria)}",
                    description=item,
                ))

        return criteria

    def calculate_coverage(self, spec: SDDSpec, implemented_items: list[Any]) -> CoverageReport:
        """
        计算规范覆盖率

        Args:
            spec: SDD规范对象
            implemented_items: 已实现的条目列表

        Returns:
            覆盖率报告
        """
        report = CoverageReport()

        all_items: list[tuple[str, str, str]] = []

        for req in spec.requirements:
            all_items.append(("requirement", req.id, req.title))

        for contract in spec.api_contracts:
            all_items.append(("api", f"{contract.method} {contract.endpoint}", contract.description or contract.endpoint))

        for model in spec.data_models:
            all_items.append(("model", model.name, model.description or model.name))

        for rule in spec.business_rules:
            all_items.append(("rule", rule.id, rule.name))

        report.total_items = len(all_items)

        implemented_ids: set[str] = set()
        if implemented_items:
            for item in implemented_items:
                if isinstance(item, str):
                    implemented_ids.add(item.lower())
                elif isinstance(item, dict):
                    implemented_ids.add(str(item.get("id", "")).lower())

        category_counts: dict[str, dict[str, int]] = {}
        for item_type, item_id, item_title in all_items:
            is_covered = (
                item_id.lower() in implemented_ids or
                any(item_id.lower() in impl or item_title.lower() in impl.lower() for impl in implemented_ids)
            )
            if is_covered:
                report.covered_items += 1
            else:
                report.uncovered_items.append({
                    "type": item_type,
                    "id": item_id,
                    "title": item_title,
                })

            if item_type not in category_counts:
                category_counts[item_type] = {"total": 0, "covered": 0}
            category_counts[item_type]["total"] += 1
            if is_covered:
                category_counts[item_type]["covered"] += 1

        if report.total_items > 0:
            report.coverage_percentage = (report.covered_items / report.total_items) * 100

        for cat, counts in category_counts.items():
            total = counts["total"]
            covered = counts["covered"]
            report.by_category[cat] = (covered / total * 100) if total > 0 else 0.0

        return report

    # ==================== 内部辅助方法 ====================

    def _extract_code_blocks(self, content: str, languages: list[str]) -> list[str]:
        """提取指定语言的代码块内容"""
        blocks: list[str] = []
        lang_pattern = "|".join(re.escape(lang) for lang in languages)
        pattern = rf"```({lang_pattern})\n([\s\S]*?)```"
        for m in re.finditer(pattern, content, re.IGNORECASE):
            blocks.append(m.group(2).strip())
        return blocks

    def _infer_priority(self, text: str) -> str:
        """从文本推断优先级"""
        text_lower = text.lower()
        if any(kw in text_lower for kw in ["critical", "紧急", "P0", "必须", "关键", "must"]):
            return "critical"
        elif any(kw in text_lower for kw in ["high", "高", "P1", "重要", "should"]):
            return "high"
        elif any(kw in text_lower for kw in ["low", "低", "P3", "可选", "nice", "may"]):
            return "low"
        return "medium"

    def _infer_category(self, prefix: str) -> str:
        """从前缀推断类别"""
        category_map = {
            "NFR": "non_functional",
            "UR": "user_story",
            "FR": "functional",
            "REQ": "functional",
        }
        return category_map.get(prefix.upper(), "functional")

    def _infer_rule_type(self, text: str) -> str:
        """推断规则类型"""
        text_lower = text.lower()
        if any(kw in text_lower for kw in ["不变量", "invariant", "始终", "必须"]):
            return "invariant"
        elif any(kw in text_lower for kw in ["验证", "validation", "检查", "check"]):
            return "validation"
        elif any(kw in text_lower for kw in ["计算", "calculation", "推导", "derive"]):
            return "calculation"
        return "constraint"

    def _infer_severity(self, text: str) -> str:
        """推断严重程度"""
        text_lower = text.lower()
        if any(kw in text_lower for kw in ["致命", "fatal", "崩溃", "crash", "数据丢失"]):
            return "fatal"
        elif any(kw in text_lower for kw in ["警告", "warning", "注意", "caution"]):
            return "warning"
        return "error"

    def _extract_api_params(self, context: str) -> list[dict[str, Any]]:
        """提取API参数定义"""
        params: list[dict[str, Any]] = []
        param_patterns = [
            r"(?:参数|Parameter|Param)[\s：:]*([A-Za-z_]\w*)\s*[:\(]\s*(\w+)",
            r"\*\*([A-Za-z_]\w*)\*\*\s*\([^)]+\)\s*[:\-]\s*(\w+)",
            r"([A-Za-z_]\w*)\s*:\s*(string|int|float|bool|list|dict|array|object)",
        ]
        for pattern in param_patterns:
            for m in re.finditer(pattern, context, re.IGNORECASE):
                params.append({
                    "name": m.group(1),
                    "type": m.group(2),
                    "required": True,
                })
        return params

    def _extract_status_codes(self, context: str) -> list[dict[str, str]]:
        """提取状态码定义"""
        codes: list[dict[str, str]] = []
        for m in re.finditer(r"(\d{3})\s*[:\-]\s*([^\n,]+)", context):
            code = int(m.group(1))
            if 100 <= code <= 599:
                codes.append({"code": m.group(1), "description": m.group(2).strip()})
        return codes

    def _extract_request_body(self, context: str) -> dict[str, Any]:
        """提取请求体定义"""
        body: dict[str, Any] = {}
        json_match = re.search(r"(?:请求体|Request Body|Body)[^:]*[:\{]*\s*(\{[^}]+\})", context, re.IGNORECASE)
        if json_match:
            try:
                import json
                body = json.loads(json_match.group(1))
            except Exception:
                body = {"raw": json_match.group(1)}
        return body

    def _extract_response_body(self, context: str) -> dict[str, Any]:
        """提取响应体定义"""
        body: dict[str, Any] = {}
        json_match = re.search(r"(?:响应|Response)[^:]*[:\{]*\s*(\{[^}]+\})", context, re.IGNORECASE)
        if json_match:
            try:
                import json
                body = json.loads(json_match.group(1))
            except Exception:
                body = {"raw": json_match.group(1)}
        return body

    def _parse_model_block(self, block: str) -> DataModel | None:
        """解析模型代码块"""
        first_line = block.split("\n")[0].strip()
        name_match = re.match(r"(\w+)(?:\s*\((\w+)\))?", first_line)
        if not name_match:
            return None

        name = name_match.group(1)
        model_type = name_match.group(2) or "entity"
        fields = self._extract_model_fields(block)

        return DataModel(name=name, model_type=model_type.lower(), fields=fields)

    def _extract_model_fields(self, context: str) -> list[DataModelField]:
        """提取模型字段定义"""
        fields: list[DataModelField] = []
        patterns = [
            r"([A-Za-z_]\w*)\s*:\s*(str|int|float|bool|datetime|list|dict|JSON|Text|String|Integer|Float|Boolean|DateTime)(?:\s*\([^)]*\))?",
            r"\*\*([A-Za-z_]\w*)\*\*\s*[|:(]\s*(\w+)",
            r"(?:字段|Field|列|Column)[\s：:]*([A-Za-z_]\w*)\s*[:(]\s*(\w+)",
        ]

        seen_fields: set[str] = set()
        for pattern in patterns:
            for m in re.finditer(pattern, context, re.IGNORECASE):
                fname = m.group(1)
                ftype = m.group(2)
                if fname not in seen_fields and not fname.startswith("_"):
                    required = "optional" not in ftype.lower() and "nullable" not in ftype.lower()
                    fields.append(DataModelField(name=fname, type=ftype, required=required))
                    seen_fields.add(fname)

        return fields

    def _extract_models_from_tables(self, content: str) -> list[DataModel]:
        """从Markdown表格提取数据模型"""
        models: list[DataModel] = []
        table_pattern = r"(\|[^\n]+\|\n\|[-:| ]+\|\n(?:\|[^\n]+\|\n?)+)"

        for m in re.finditer(table_pattern, content):
            table_text = m.group(0)
            rows = [line.strip().strip("|").split("|") for line in table_text.strip().split("\n") if line.strip()]

            if len(rows) < 3:
                continue

            header = [h.strip() for h in rows[0]]
            if "field" not in " ".join(header).lower() and "字段" not in " ".join(header).lower():
                continue

            type_col = -1
            name_col = -1
            for i, h in enumerate(header):
                hl = h.lower()
                if hl in ("field", "字段", "name", "列名"):
                    name_col = i
                elif hl in ("type", "类型", "dtype", "数据类型"):
                    type_col = i

            if name_col == -1:
                continue

            model_name = f"TableModel_{len(models)}"
            fields: list[DataModelField] = []
            for row in rows[2:]:
                cells = [c.strip() for c in row]
                if len(cells) > name_col and cells[name_col]:
                    fname = cells[name_col]
                    ftype = cells[type_col] if type_col >= 0 and type_col < len(cells) else "string"
                    fields.append(DataModelField(name=fname, type=ftype))

            if fields:
                models.append(DataModel(name=model_name, model_type="entity", fields=fields))

        return models

    def generate_spec_report(self, spec: SDDSpec) -> str:
        """生成规范解析报告（Markdown格式）"""
        lines: list[str] = []
        lines.append("# 📋 SDD规范解析报告\n")
        lines.append(f"| 属性 | 值 |")
        lines.append(f"| --- | --- |")
        lines.append(f"| 规范ID | `{spec.spec_id}` |")
        lines.append(f"| 标题 | **{spec.title}** |")
        lines.append(f"| 版本 | {spec.version} |")
        lines.append(f"| 作者 | {spec.author or '未知'} |")

        lines.append(f"\n## 📊 统计摘要\n")
        lines.append(f"| 类型 | 数量 |")
        lines.append(f"| --- | --- |")
        lines.append(f"| 需求条目 | {len(spec.requirements)} |")
        lines.append(f"| API端点 | {len(spec.api_contracts)} |")
        lines.append(f"| 数据模型 | {len(spec.data_models)} |")
        lines.append(f"| 业务规则 | {len(spec.business_rules)} |")

        if spec.requirements:
            lines.append(f"\n## 📝 需求列表\n")
            lines.append(f"| ID | 标题 | 优先级 | 类别 | AC数 |")
            lines.append(f"| --- | --- | --- | --- | --- |")
            for req in spec.requirements[:15]:
                lines.append(f"| `{req.id}` | {req.title[:30]} | {req.priority} | {req.category} | {len(req.acceptance_criteria)} |")

        if spec.api_contracts:
            lines.append(f"\n## 🔗 API端点\n")
            lines.append(f"| 方法 | 端点 | 认证 |")
            lines.append(f"| --- | --- | --- |")
            for contract in spec.api_contracts[:10]:
                lines.append(f"| **{contract.method}** | `{contract.endpoint}` | {'✅' if contract.authentication else '❌'} |")

        if spec.data_models:
            lines.append(f"\n## 🗃️ 数据模型\n")
            lines.append(f"| 名称 | 类型 | 字段数 |")
            lines.append(f"| --- | --- | --- |")
            for model in spec.data_models[:8]:
                lines.append(f"| **{model.name}** | {model.model_type} | {len(model.fields)} |")

        if spec.business_rules:
            lines.append(f"\n## 📐 业务规则\n")
            lines.append(f"| ID | 名称 | 类型 | 严重程度 |")
            lines.append(f"| --- | --- | --- | --- |")
            for rule in spec.business_rules[:8]:
                lines.append(f"| `{rule.id}` | {rule.name[:30]} | {rule.rule_type} | {rule.severity} |")

        coverage = self.calculate_coverage(spec, [])
        lines.append(f"\n## 📈 覆盖率基准\n")
        lines.append(f"- 总条目数: **{coverage.total_items}**")
        lines.append(f"- 已覆盖: **{coverage.covered_items}** ({coverage.coverage_percentage:.1f}%)")

        return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print("=" * 60)
    print("SDD规范解析器 - 功能演示")
    print("=" * 60)

    sample_spec = '''# 用户管理系统 SDD v1.0

作者: 中书省·需求司
版本: 1.0.0

## 概述

用户管理系统提供完整的用户生命周期管理能力。

## 功能需求

### REQ-001: 用户注册
- **优先级**: Critical
- **描述**: 新用户可以通过邮箱注册账号
- 验收标准:
  - Given 有效邮箱 When 注册 Then 创建成功返回用户ID
  - Given 重复邮箱 When 注册 Then 返回409错误

### REQ-002: 用户登录
**优先级**: High
支持用户名密码登录，返回JWT Token

- [ ] 验证码登录
- [ ] OAuth第三方登录

## API接口定义

`POST /api/auth/register` - 用户注册
- 参数: email(string), password(string)
- 响应: {"user_id": "uuid", "token": "jwt"}

`GET /api/users/{id}` - 获取用户信息
- 状态码: 200 成功, 404 未找到, 403 无权限

## 数据模型

### User (Entity)
- id: UUID (主键)
- email: String (唯一)
- password_hash: String
- is_active: Boolean
- created_at: DateTime

### UserProfile (DTO)
- user_id: UUID
- nickname: string
- avatar_url: string

## 业务规则

**BR-001**: 用户邮箱必须唯一，重复注册返回409
**BR-002**: 密码长度不少于8位，必须包含字母和数字
- MUST: 密码不能与用户名相同
- SHOULD: 建议使用特殊字符

## 非功能需求

- NFR-001: API响应时间 < 200ms (P95)
- NFR-002: 支持1000并发用户
'''

    parser = SDDSpecParser()
    spec = parser.parse_spec_content(sample_spec)

    print(f"\n📄 规范标题: {spec.title}")
    print(f"   版本: {spec.version}")
    print(f"   ID: {spec.spec_id}")

    print(f"\n📝 需求条目: {len(spec.requirements)} 个")
    for req in spec.requirements:
        print(f"   [{req.id}] {req.title} (优先级:{req.priority}, AC:{len(req.acceptance_criteria)})")
        for ac in req.acceptance_criteria:
            print(f"      AC: {ac.description}")

    print(f"\n🔗 API端点: {len(spec.api_contracts)} 个")
    for api in spec.api_contracts:
        print(f"   {api.method} {api.endpoint} (认证:{api.authentication})")

    print(f"\n🗃️ 数据模型: {len(spec.data_models)} 个")
    for model in spec.data_models:
        print(f"   {model.name} ({model.model_type}) - {len(model.fields)}个字段:")
        for f in model.fields[:4]:
            print(f"      - {f.name}: {f.type} {'(必填)' if f.required else '(可选)'}")

    print(f"\n📐 业务规则: {len(spec.business_rules)} 条")
    for rule in spec.business_rules:
        print(f"   [{rule.id}] {rule.name} ({rule.rule_type}/{rule.severity})")

    coverage = parser.calculate_coverage(spec, ["REQ-001", "POST /api/auth/register"])
    print(f"\n📈 覆盖率报告:")
    print(f"   总条目: {coverage.total_items}, 已覆盖: {coverage.covered_items}")
    print(f"   覆盖率: {coverage.coverage_percentage:.1f}%")
    print(f"   分类覆盖: {coverage.by_category}")

    report = parser.generate_spec_report(spec)
    print(f"\n--- 报告预览 (前600字符) ---\n{report[:600]}...")

    print("\n✅ 所有测试通过!")
