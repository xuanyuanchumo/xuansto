from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class IssueSeverity(Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class ValidationIssue:
    severity: IssueSeverity
    field: str
    message: str
    suggestion: str | None = None


@dataclass
class FieldCheckResult:
    is_valid: bool
    present_fields: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    issues: list[ValidationIssue] = field(default_factory=list)


@dataclass
class DescriptionQualityScore:
    length_score: int
    keyword_score: int
    clarity_score: int
    trigger_score: int

    @property
    def overall_score(self) -> float:
        weights = (0.15, 0.25, 0.30, 0.30)
        scores = (
            self.length_score,
            self.keyword_score,
            self.clarity_score,
            self.trigger_score,
        )
        return round(sum(w * s for w, s in zip(weights, scores)), 2)

    @property
    def grade(self) -> str:
        s = self.overall_score
        if s >= 4.5:
            return "A+"
        if s >= 4.0:
            return "A"
        if s >= 3.5:
            return "B+"
        if s >= 3.0:
            return "B"
        if s >= 2.5:
            return "C+"
        if s >= 2.0:
            return "C"
        if s >= 1.5:
            return "D"
        return "F"


@dataclass
class ValidationResult:
    is_valid: bool
    required_fields_result: FieldCheckResult
    recommended_fields_result: FieldCheckResult
    description_score: DescriptionQualityScore
    issues: list[ValidationIssue] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    validated_at: datetime = field(default_factory=datetime.now)


REQUIRED_FIELDS = {"name", "version", "description"}
RECOMMENDED_FIELDS = {
    "compatibility",
    "triggers",
    "eval_metrics",
}
COMPATIBILITY_SUBFIELDS = {
    "python",
    "terminal",
    "ide",
    "skills",
}
TRIGGER_KEYWORDS = {
    "三省六部",
    "全生命周期",
    "DevOps",
    "CI/CD",
    "自动化部署",
    "持续集成",
    "持续交付",
    "架构设计",
    "需求分析",
    "TDD",
    "测试驱动",
    "代码审查",
    "Code Review",
    "性能优化",
    "容器化",
    "Docker",
    "Kubernetes",
    "K8s",
    "微服务",
    "监控告警",
    "日志分析",
}
DESCRIPTION_MIN_LENGTH = 30
DESCRIPTION_MAX_LENGTH = 500
IDEAL_DESCRIPTION_LENGTH = 150


class MetadataValidator:
    def __init__(self, skill_md_path: Path | None = None):
        self._skill_md_path = skill_md_path

    def validate_frontmatter(self, skill_md_path: Path | None = None) -> ValidationResult:
        path = skill_md_path or self._skill_md_path
        if path is None:
            raise ValueError("skill_md_path must be provided")
        if not path.exists():
            raise FileNotFoundError(f"SKILL.md not found at {path}")
        content = path.read_text(encoding="utf-8")
        metadata = self._parse_frontmatter(content)
        if metadata is None:
            raise ValueError(f"No frontmatter found in {path}")
        req_result = self.check_required_fields(metadata)
        rec_result = self.check_recommended_fields(metadata)
        desc_score = self.validate_description_quality(
            metadata.get("description", "")
        )
        compat = metadata.get("compatibility")
        if compat is not None:
            compat_ok, compat_issues = self.check_compatibility_declaration(compat)
            if not compat_ok:
                rec_result.issues.extend(
                    ValidationIssue(
                        severity=IssueSeverity.WARNING,
                        field="compatibility",
                        message=i,
                    )
                    for i in compat_issues
                )
        all_issues = [
            *req_result.issues,
            *rec_result.issues,
        ]
        is_valid = req_result.is_valid and desc_score.overall_score >= 2.0
        suggestions = self._generate_suggestions(metadata, req_result, rec_result, desc_score)
        return ValidationResult(
            is_valid=is_valid,
            required_fields_result=req_result,
            recommended_fields_result=rec_result,
            description_score=desc_score,
            issues=all_issues,
            suggestions=suggestions,
        )

    def check_required_fields(self, metadata: dict[str, Any]) -> tuple[bool, list[str]]:
        missing = [f for f in REQUIRED_FIELDS if f not in metadata]
        present = [f for f in REQUIRED_FIELDS if f in metadata]
        issues: list[ValidationIssue] = []
        for f in missing:
            issues.append(
                ValidationIssue(
                    severity=IssueSeverity.ERROR,
                    field=f,
                    message=f"Required field '{f}' is missing",
                    suggestion=f"Add '{f}' to the SKILL.md frontmatter",
                )
            )
        for f in present:
            val = metadata.get(f)
            if isinstance(val, str) and not val.strip():
                issues.append(
                    ValidationIssue(
                        severity=IssueSeverity.ERROR,
                        field=f,
                        message=f"Field '{f}' is empty",
                        suggestion=f"Provide a value for '{f}'",
                    )
                )
        result = FieldCheckResult(
            is_valid=len(missing) == 0,
            present_fields=present,
            missing_fields=missing,
            issues=issues,
        )
        return result.is_valid, result.missing_fields

    def check_recommended_fields(self, metadata: dict[str, Any]) -> FieldCheckResult:
        present = [f for f in RECOMMENDED_FIELDS if f in metadata]
        missing = [f for f in RECOMMENDED_FIELDS if f not in metadata]
        issues: list[ValidationIssue] = []
        for f in missing:
            issues.append(
                ValidationIssue(
                    severity=IssueSeverity.INFO,
                    field=f,
                    message=f"Recommended field '{f}' is missing",
                    suggestion=f"Consider adding '{f}' for better compatibility",
                )
            )
        return FieldCheckResult(
            is_valid=len(missing) == 0,
            present_fields=present,
            missing_fields=missing,
            issues=issues,
        )

    def check_compatibility_declaration(
        self, compat: dict[Any, Any] | None
    ) -> tuple[bool, list[str]]:
        if compat is None:
            return True, []
        issues: list[str] = []
        if not isinstance(compat, dict):
            return False, ["compatibility must be a dictionary"]
        for subfield in COMPATIBILITY_SUBFIELDS:
            if subfield in compat:
                val = compat[subfield]
                if subfield == "python":
                    if not isinstance(val, str) or not re.match(r"^3\.\d+", str(val)):
                        issues.append(
                            f"compatibility.python should be a version string like '3.10', got {val!r}"
                        )
                elif subfield in ("terminal", "ide", "skills"):
                    if not isinstance(val, list):
                        issues.append(
                            f"compatibility.{subfield} should be a list, got {type(val).__name__}"
                        )
        return len(issues) == 0, issues

    def validate_description_quality(self, description: str) -> DescriptionQualityScore:
        length_score = self._score_description_length(description)
        keyword_score = self._score_keyword_coverage(description)
        clarity_score = self._score_clarity(description)
        trigger_score = self._score_trigger_clarity(description)
        return DescriptionQualityScore(
            length_score=length_score,
            keyword_score=keyword_score,
            clarity_score=clarity_score,
            trigger_score=trigger_score,
        )

    def _score_description_length(self, description: str) -> int:
        length = len(description.strip())
        if DESCRIPTION_MIN_LENGTH <= length <= DESCRIPTION_MAX_LENGTH:
            diff = abs(length - IDEAL_DESCRIPTION_LENGTH)
            if diff <= 50:
                return 5
            if diff <= 100:
                return 4
            return 3
        if length < DESCRIPTION_MIN_LENGTH:
            return max(1, 3 - (DESCRIPTION_MIN_LENGTH - length) // 20)
        return max(1, 3 - (length - DESCRIPTION_MAX_LENGTH) // 100)

    def _score_keyword_coverage(self, description: str) -> int:
        desc_lower = description.lower()
        matches = sum(1 for kw in TRIGGER_KEYWORDS if kw.lower() in desc_lower)
        if matches >= 6:
            return 5
        if matches >= 4:
            return 4
        if matches >= 2:
            return 3
        if matches >= 1:
            return 2
        return 1

    def _score_clarity(self, description: str) -> int:
        score = 3
        sentences = re.split(r"[。！？.!?\n]", description)
        non_empty = [s.strip() for s in sentences if s.strip()]
        if len(non_empty) >= 2:
            score += 1
        if any(len(s) > 20 for s in non_empty):
            score += 1
        has_structure = bool(re.search(r"[：:]|[-—–]|（|[\d.]", description))
        if has_structure:
            score = min(5, score + 1)
        return min(5, max(1, score))

    def _score_trigger_clarity(self, description: str) -> int:
        score = 2
        trigger_patterns = [
            r"(当|如果|当用户|适用于|支持|用于|可以|能够)",
            r"(触发|调用|激活|启动|使用|执行)",
            r"(开发|部署|运维|构建|测试|监控)",
        ]
        for pattern in trigger_patterns:
            if re.search(pattern, description):
                score += 1
        return min(5, score)

    @staticmethod
    def _parse_frontmatter(content: str) -> dict[str, Any] | None:
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if not match:
            return None
        raw = match.group(1)
        metadata: dict[str, Any] = {}
        current_key: str | None = None
        current_value: Any = None
        in_list = False
        list_items: list[str] = []
        indent_stack: list[tuple[str, Any]] = []
        for line in raw.split("\n"):
            stripped = line.rstrip()
            top_match = re.match(r"^(\w[\w-]*)\s*:\s*(.*)", stripped)
            if top_match and not stripped.startswith(" ") and not stripped.startswith("\t"):
                if current_key is not None:
                    if in_list:
                        metadata[current_key] = list_items
                    else:
                        metadata[current_key] = current_value
                current_key = top_match.group(1)
                rest = top_match.group(2).strip()
                if rest.startswith("[") and "]" in rest:
                    items_str = rest[1 : rest.index("]")]
                    metadata[current_key] = [
                        item.strip().strip("'\"")
                        for item in items_str.split(",")
                        if item.strip()
                    ]
                    current_key = None
                    current_value = None
                    in_list = False
                    list_items = []
                elif rest:
                    current_value = rest.strip("'\"")
                    in_list = False
                    list_items = []
                else:
                    current_value = None
                    in_list = False
                    list_items = []
            elif stripped.startswith("  - ") or stripped.startswith("\t- "):
                in_list = True
                item = stripped.split("-", 1)[1].strip().strip("'\"")
                list_items.append(item)
            elif stripped.startswith("    ") and current_key and in_list:
                pass
            else:
                if current_key and not in_list and current_value is None:
                    current_value = ""
        if current_key is not None:
            if in_list:
                metadata[current_key] = list_items
            elif current_value is not None:
                metadata[current_key] = current_value
        return metadata

    def _generate_suggestions(
        self,
        metadata: dict[str, Any],
        req_result: FieldCheckResult,
        rec_result: FieldCheckResult,
        desc_score: DescriptionQualityScore,
    ) -> list[str]:
        suggestions: list[str] = []
        for f in req_result.missing_fields:
            suggestions.append(f"添加必填字段 `{f}` 以符合skill-creator标准")
        for f in rec_result.missing_fields:
            suggestions.append(f"建议添加推荐字段 `{f}` 以提升兼容性")
        if desc_score.length_score < 3:
            suggestions.append(
                f"描述长度应为{DESCRIPTION_MIN_LENGTH}-{DESCRIPTION_MAX_LENGTH}字符，当前可能过短或过长"
            )
        if desc_score.keyword_score < 3:
            suggestions.append(
                "描述中应包含更多技能关键词以提升可发现性"
            )
        if desc_score.trigger_score < 3:
            suggestions.append(
                "建议明确说明触发条件和使用场景"
            )
        if desc_score.overall_score < 3.0:
            suggestions.append(
                f"描述质量评分较低({desc_score.overall_score:.1f}/{desc_score.grade})，建议重写"
            )
        triggers = metadata.get("triggers")
        if not triggers:
            suggestions.append("建议配置triggers字段以优化触发准确率")
        eval_metrics = metadata.get("eval_metrics")
        if not eval_metrics:
            suggestions.append("建议配置eval_metrics字段以设定评估基准")
        return suggestions

    def generate_validation_report(self, skill_md_path: Path | None = None) -> str:
        result = self.validate_frontmatter(skill_md_path)
        lines: list[str] = []
        lines.append("# Skill元数据验证报告")
        lines.append("")
        lines.append(f"> 验证时间: {result.validated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        status_icon = "✅ 通过" if result.is_valid else "❌ 未通过"
        lines.append(f"> 验证状态: **{status_icon}**")
        lines.append("")
        lines.append("## 总体评分")
        lines.append("")
        ds = result.description_score
        lines.append(f"| 维度 | 得分 |")
        lines.append(f"|------|------|")
        lines.append(f"| 描述长度 | {ds.length_score}/5 |")
        lines.append(f"| 关键词覆盖 | {ds.keyword_score}/5 |")
        lines.append(f"| 清晰度 | {ds.clarity_score}/5 |")
        lines.append(f"| 触发条件明确性 | {ds.trigger_score}/5 |")
        lines.append(f"| **综合评分** | **{ds.overall_score:.2f}/5 ({ds.grade})** |")
        lines.append("")
        lines.append("## 必填字段检查")
        lines.append("")
        req = result.required_fields_result
        req_status = "✅ 全部通过" if req.is_valid else f"⚠️ 缺失 {len(req.missing_fields)} 个字段"
        lines.append(f"- 状态: {req_status}")
        lines.append(f"- 已包含: {', '.join(req.present_fields) or '(无)'}")
        if req.missing_fields:
            lines.append(f"- 缺失: {', '.join(req.missing_fields)}")
        lines.append("")
        lines.append("## 推荐字段检查")
        lines.append("")
        rec = result.recommended_fields_result
        rec_status = "✅ 全部包含" if rec.is_valid else f"ℹ️ 缺少 {len(rec.missing_fields)} 个"
        lines.append(f"- 状态: {rec_status}")
        lines.append(f"- 已包含: {', '.join(rec.present_fields) or '(无)'}")
        if rec.missing_fields:
            lines.append(f"- 缺少: {', '.join(rec.missing_fields)}")
        lines.append("")
        if result.issues:
            lines.append("## 问题详情")
            lines.append("")
            severity_icons = {
                IssueSeverity.ERROR: "🔴",
                IssueSeverity.WARNING: "🟡",
                IssueSeverity.INFO: "🔵",
            }
            for issue in result.issues:
                icon = severity_icons.get(issue.severity, "•")
                lines.append(f"- {icon} **[{issue.severity.value}]** `{issue.field}`: {issue.message}")
                if issue.suggestion:
                    lines.append(f"  - 💡 建议: {issue.suggestion}")
            lines.append("")
        if result.suggestions:
            lines.append("## 改进建议")
            lines.append("")
            for i, suggestion in enumerate(result.suggestions, 1):
                lines.append(f"{i}. {suggestion}")
            lines.append("")
        lines.append("---")
        lines.append("*报告由 Universal DevOps v6.0 Skill Standardization 模块生成*")
        return "\n".join(lines)
