#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Decision Log 系统 - OpenCode透明化理念内化

功能：
1. 决策记录生成与管理（DEC-YYYYMMDD-NNN编号体系）
2. 历史决策查询与过滤
3. 决策后评估（效果追踪）
4. 决策归档与检索
5. 与尚书省各部的集成接口
"""

import json
import os
import re
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """风险等级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DecisionStatus(Enum):
    """决策状态枚举"""
    DRAFT = "draft"
    RECORDED = "recorded"
    EVALUATED = "evaluated"
    SUPERSEDED = "superseded"


@dataclass
class DecisionRecord:
    """决策记录数据类"""
    decision_id: str                           # DEC-YYYYMMDD-NNN
    decision_time: datetime                    # 决策时间
    maker: str                                 # 决策者（如"中书省-架构设计局"）
    decision_content: str                      # 决策内容
    rationale: str                             # 决策依据
    alternatives: Dict[str, float] = field(default_factory=dict)   # 备选方案及评分
    selected_option: str = ""                  # 选中的方案
    impact_scope: List[str] = field(default_factory=list)          # 影响范围
    risk_assessment: str = "low"               # 风险等级 (low/medium/high)
    evaluation_plan: str = ""                  # 后评估计划
    status: str = "recorded"                   # 决策状态
    actual_outcome: Optional[str] = None       # 实际结果（后评估填写）
    outcome_evaluation: Optional[str] = None   # 效果评价
    outcome_score: Optional[float] = None      # 效果评分(0-1)
    outcome_evaluated_at: Optional[datetime] = None  # 后评估时间
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["decision_time"] = self.decision_time.isoformat()
        if self.outcome_evaluated_at:
            result["outcome_evaluated_at"] = self.outcome_evaluated_at.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionRecord":
        if isinstance(data.get("decision_time"), str):
            data["decision_time"] = datetime.fromisoformat(data["decision_time"])
        if isinstance(data.get("outcome_evaluated_at"), str):
            data["outcome_evaluated_at"] = datetime.fromisoformat(data["outcome_evaluated_at"])
        return cls(**data)


@dataclass
class EvaluationResult:
    """后评估结果"""
    decision_id: str
    evaluated_at: datetime
    actual_outcome: str
    effectiveness_score: float              # 0-1
    evaluation_summary: str
    lessons_learned: List[str] = field(default_factory=list)
    recommendation: str = ""
    would_repeat: bool = True

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["evaluated_at"] = self.evaluated_at.isoformat()
        return result


class DecisionLog:
    """Decision Log 系统 - OpenCode透明化理念内化"""

    DEFAULT_OUTPUT_DIR = "docs/logs/decision_logs"

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or self.DEFAULT_OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._counter_cache: Dict[str, int] = {}
        self._load_counters()

    def _load_counters(self):
        counter_file = self.output_dir / ".counters.json"
        if counter_file.exists():
            try:
                with open(counter_file, "r", encoding="utf-8") as f:
                    self._counter_cache = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("加载计数器文件失败: %s", e)
                self._counter_cache = {}

    def _save_counters(self):
        counter_file = self.output_dir / ".counters.json"
        with open(counter_file, "w", encoding="utf-8") as f:
            json.dump(self._counter_cache, f, ensure_ascii=False, indent=2)

    def _generate_decision_id(self) -> str:
        date_str = datetime.now().strftime("%Y%m%d")
        if date_str not in self._counter_cache:
            self._counter_cache[date_str] = 0
        self._counter_cache[date_str] += 1
        self._save_counters()
        return f"DEC-{date_str}-{self._counter_cache[date_str]:03d}"

    def generate(
        self,
        decision: str,
        maker: str,
        rationale: str,
        alternatives: Optional[List[str]] = None,
        impact_scope: Optional[List[str]] = None,
        risk_assessment: str = "low",
        output_dir: Optional[str] = None,
        selected_option: str = "",
        evaluation_plan: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        生成决策日志

        参数:
            decision: 决策内容
            maker: 决策者（如"中书省-架构设计局"）
            rationale: 决策依据
            alternatives: 备选方案列表
            impact_scope: 影响范围（前端/后端/数据库/运维等）
            risk_assessment: 风险等级 (low/medium/high)
            output_dir: 输出目录（默认 docs/logs/decision_logs/）
            selected_option: 选中的方案
            evaluation_plan: 后评估计划
            metadata: 额外元数据

        返回:
            生成的文件路径
        """
        decision_id = self._generate_decision_id()

        alt_dict = {}
        if alternatives:
            for i, alt in enumerate(alternatives):
                alt_dict[f"option_{i+1}_{alt[:30]}"] = 0.0
            if selected_option:
                for key in alt_dict:
                    if selected_option in key:
                        alt_dict[key] = 1.0

        record = DecisionRecord(
            decision_id=decision_id,
            decision_time=datetime.now(),
            maker=maker,
            decision_content=decision,
            rationale=rationale,
            alternatives=alt_dict,
            selected_option=selected_option or (alternatives[0] if alternatives else ""),
            impact_scope=impact_scope or [],
            risk_assessment=risk_assessment.lower(),
            evaluation_plan=evaluation_plan,
            status="recorded",
            metadata=metadata or {},
        )

        target_dir = Path(output_dir) if output_dir else self.output_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / f"{decision_id}.md"

        content = self._format_record_as_markdown(record)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        json_path = target_dir / f"{decision_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, ensure_ascii=False, indent=2, default=str)

        logger.info("决策日志已生成: %s (%s)", decision_id, file_path)
        return str(file_path)

    def _format_record_as_markdown(self, record: DecisionRecord) -> str:
        lines = [
            f"# {record.decision_id}",
            "",
            "**决策者**: " + record.maker,
            "**决策时间**: " + record.decision_time.strftime("%Y-%m-%d %H:%M:%S"),
            "**风险等级**: " + record.risk_assessment.upper(),
            "**状态**: " + record.status.upper(),
            "",
            "---",
            "",
            "## 决策内容",
            "",
            record.decision_content,
            "",
            "## 决策依据",
            "",
            record.rationale,
            "",
        ]

        if record.alternatives:
            lines.extend([
                "## 备选方案",
                "",
            ])
            for key, score in record.alternatives.items():
                marker = " ✅" if score > 0 else ""
                lines.append(f"- **{key}** (评分: {score}){marker}")
            lines.append("")

        if record.selected_option:
            lines.extend([
                "## 最终选择",
                "",
                f"> **{record.selected_option}**",
                "",
            ])

        if record.impact_scope:
            scope_str = ", ".join(record.impact_scope)
            lines.extend([
                "## 影响范围",
                "",
                f"`{scope_str}`",
                "",
            ])

        if record.evaluation_plan:
            lines.extend([
                "## 后评估计划",
                "",
                record.evaluation_plan,
                "",
            ])

        if record.actual_outcome is not None:
            lines.extend([
                "---",
                "",
                "## 后评估结果",
                "",
                "**实际结果**: " + record.actual_outcome,
            ])
            if record.outcome_score is not None:
                lines.append(f"**效果评分**: {record.outcome_score:.2f}/1.00")
            if record.outcome_evaluation:
                lines.append(f"\n**评价**: {record.outcome_evaluation}")
            if record.outcome_evaluated_at:
                lines.append(f"**评估时间**: {record.outcome_evaluated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("")

        if record.metadata:
            lines.extend([
                "---",
                "",
                "## 元数据",
                "",
                "```json",
                json.dumps(record.metadata, ensure_ascii=False, indent=2),
                "```",
                "",
            ])

        return "\n".join(lines)

    def list_decisions(
        self,
        date_filter: Optional[str] = None,
        maker_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        列出历史决策

        参数:
            date_filter: 日期过滤器，格式 YYYYMMDD 或 YYYYMM
            maker_filter: 按决策者过滤
            status_filter: 按状态过滤
            keyword: 关键词搜索

        返回:
            决策摘要列表
        """
        decisions = []

        for json_file in sorted(self.output_dir.glob("DEC-*.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if date_filter:
                    decision_date = data.get("decision_time", "")[:10].replace("-", "")
                    if not decision_date.startswith(date_filter):
                        continue

                if maker_filter:
                    if maker_filter.lower() not in data.get("maker", "").lower():
                        continue

                if status_filter:
                    if data.get("status", "") != status_filter:
                        continue

                if keyword:
                    search_text = (
                        data.get("decision_content", "") +
                        data.get("rationale", "") +
                        data.get("maker", "")
                    ).lower()
                    if keyword.lower() not in search_text:
                        continue

                decisions.append({
                    "decision_id": data.get("decision_id"),
                    "decision_time": data.get("decision_time"),
                    "maker": data.get("maker"),
                    "decision_content": data.get("decision_content", "")[:100],
                    "risk_assessment": data.get("risk_assessment"),
                    "status": data.get("status"),
                    "impact_scope": data.get("impact_scope", []),
                    "file_path": str(json_file),
                })
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("读取决策文件失败 %s: %s", json_file, e)

        return decisions

    def get_decision(self, decision_id: str) -> Optional[DecisionRecord]:
        """获取单个决策详情"""
        json_path = self.output_dir / f"{decision_id}.json"
        if not json_path.exists():
            md_path = self.output_dir / f"{decision_id}.md"
            if not md_path.exists():
                return None
            return self._parse_md_to_record(md_path)

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return DecisionRecord.from_dict(data)

    def _parse_md_to_record(self, md_path: Path) -> Optional[DecisionRecord]:
        content = md_path.read_text(encoding="utf-8")
        record_data = {
            "decision_id": md_path.stem,
            "decision_time": datetime.fromtimestamp(md_path.stat().st_ctime),
            "maker": "",
            "decision_content": "",
            "rationale": "",
            "alternatives": {},
            "selected_option": "",
            "impact_scope": [],
            "risk_assessment": "low",
            "evaluation_plan": "",
            "status": "recorded",
        }

        sections = re.split(r"^## ", content, flags=re.MULTILINE)
        for section in sections:
            if section.startswith("决策内容"):
                record_data["decision_content"] = section.replace("决策内容\n\n", "").strip()
            elif section.startswith("决策依据"):
                record_data["rationale"] = section.replace("决策依据\n\n", "").strip()
            elif section.startswith("备选方案"):
                alts = re.findall(r"- \*\*(.+?)\*\*.*?评分:\s*([\d.]+)", section)
                record_data["alternatives"] = {k: float(v) for k, v in alts}

        return DecisionRecord(**record_data)

    def evaluate_outcome(
        self,
        decision_id: str,
        actual_outcome: str,
        effectiveness_score: Optional[float] = None,
        evaluation_summary: str = "",
        lessons_learned: Optional[List[str]] = None,
        recommendation: str = "",
        would_repeat: bool = True,
    ) -> EvaluationResult:
        """
        评估决策效果（后评估）

        参数:
            decision_id: 决策ID
            actual_outcome: 实际执行结果描述
            effectiveness_score: 效果评分 (0.0-1.0)
            evaluation_summary: 评价总结
            lessons_learned: 经验教训列表
            recommendation: 后续建议
            would_repeat: 是否会再次做同样的决策

        返回:
            EvaluationResult 对象
        """
        record = self.get_decision(decision_id)
        if record is None:
            raise ValueError(f"决策不存在: {decision_id}")

        now = datetime.now()

        if effectiveness_score is None:
            effectiveness_score = 0.5

        result = EvaluationResult(
            decision_id=decision_id,
            evaluated_at=now,
            actual_outcome=actual_outcome,
            effectiveness_score=max(0.0, min(1.0, effectiveness_score)),
            evaluation_summary=evaluation_summary,
            lessons_learned=lessons_learned or [],
            recommendation=recommendation,
            would_repeat=would_repeat,
        )

        record.actual_outcome = actual_outcome
        record.outcome_evaluation = evaluation_summary
        record.outcome_score = result.effectiveness_score
        record.outcome_evaluated_at = now
        record.status = "evaluated"

        self._update_record(record)

        logger.info("决策后评估完成: %s (评分: %.2f)", decision_id, result.effectiveness_score)
        return result

    def _update_record(self, record: DecisionRecord):
        json_path = self.output_dir / f"{record.decision_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, ensure_ascii=False, indent=2, default=str)

        md_path = self.output_dir / f"{record.decision_id}.md"
        content = self._format_record_as_markdown(record)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(content)

    def get_statistics(self) -> Dict[str, Any]:
        """获取决策统计信息"""
        decisions = self.list_decisions()
        total = len(decisions)

        if total == 0:
            return {
                "total_decisions": 0,
                "by_maker": {},
                "by_risk": {},
                "by_status": {},
                "evaluated_count": 0,
                "avg_effectiveness": None,
            }

        by_maker: Dict[str, int] = {}
        by_risk: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        effectiveness_scores = []
        evaluated_count = 0

        for d in decisions:
            maker = d.get("maker", "unknown")
            by_maker[maker] = by_maker.get(maker, 0) + 1

            risk = d.get("risk_assessment", "unknown")
            by_risk[risk] = by_risk.get(risk, 0) + 1

            status = d.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1

            full_record = self.get_decision(d["decision_id"])
            if full_record and full_record.outcome_score is not None:
                effectiveness_scores.append(full_record.outcome_score)
                evaluated_count += 1

        avg_effectiveness = (
            sum(effectiveness_scores) / len(effectiveness_scores)
            if effectiveness_scores else None
        )

        return {
            "total_decisions": total,
            "by_maker": dict(sorted(by_maker.items(), key=lambda x: x[1], reverse=True)),
            "by_risk": by_risk,
            "by_status": by_status,
            "evaluated_count": evaluated_count,
            "avg_effectiveness": round(avg_effectiveness, 3) if avg_effectiveness else None,
        }


def main():
    demo = DecisionLog()

    path = demo.generate(
        decision="扩展尚书省六部为24司SKILL.md体系",
        maker="刑部-自演化司",
        rationale="为提升三省六部协同系统的精细化管理能力，将每部从原有4司扩展为新的职能化24司架构",
        alternatives=[
            "保持原有架构不变，通过增强现有司的能力来扩展",
            "扩展为24司，每个司职责明确、接口清晰",
            "采用动态司制，按需创建和销毁司",
        ],
        impact_scope=["吏部", "户部", "礼部", "兵部", "工部", "刑部", "skillscripts/core"],
        risk_assessment="medium",
        selected_option="扩展为24司，每个司职责明确、接口清晰",
        evaluation_plan="在v4.0版本发布后30天进行效果评估",
        metadata={"version": "4.0", "task_type": "architecture"},
    )
    print(f"生成决策日志: {path}")

    decisions = demo.list_decisions()
    print(f"\n共 {len(decisions)} 条决策:")
    for d in decisions[:5]:
        print(f"  [{d['decision_id']}] {d['maker']}: {d['decision_content']}...")

    stats = demo.get_statistics()
    print(f"\n统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
