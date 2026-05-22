"""
结果收集器

收集、合并、冲突检测与解决多 Agent 执行结果，
提供指标聚合、统一格式化和持久化存储功能。
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ConflictResolutionStrategy(str, Enum):
    """冲突解决策略枚举"""
    MERGE = "merge"
    PREFER_PRIMARY = "prefer_primary"
    PREFER_SECONDARY = "prefer_secondary"
    ESCALATE = "escalate"


class ResultStatus(str, Enum):
    """结果状态枚举"""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class AgentResult:
    """单个 Agent 执行结果"""

    agent_id: str
    status: ResultStatus = ResultStatus.SUCCESS
    output: str = ""
    artifacts: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, float] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "output_length": len(self.output),
            "artifacts": list(self.artifacts.keys()),
            "metrics": self.metrics,
            "timestamp": self.timestamp,
            "errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
        }


@dataclass
class CollectedResult:
    """合并后的收集结果"""

    collection_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    primary_result: AgentResult | None = None
    secondary_results: list[AgentResult] = field(default_factory=list)
    merged_output: str = ""
    merged_artifacts: dict[str, Any] = field(default_factory=dict)
    conflicts_detected: list[dict[str, Any]] = field(default_factory=list)
    resolution_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.MERGE
    aggregated_metrics: dict[str, float] = field(default_factory=dict)
    collected_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "collection_id": self.collection_id,
            "primary_agent": self.primary_result.agent_id if self.primary_result else None,
            "secondary_count": len(self.secondary_results),
            "merged_output_length": len(self.merged_output),
            "artifacts_count": len(self.merged_artifacts),
            "conflicts_count": len(self.conflicts_detected),
            "resolution_strategy": self.resolution_strategy.value,
            "aggregated_metrics": self.aggregated_metrics,
            "collected_at": self.collected_at,
        }


class AgentResultCollector:
    """
    结果收集器

    负责多 Agent 执行结果的收集、合并、冲突解决和持久化。
    """

    def __init__(self, output_dir: Path | str | None = None) -> None:
        self._output_dir = Path(output_dir) if output_dir else Path.cwd() / "logs"
        self._collections: dict[str, CollectedResult] = {}

    def collect_result(
        self,
        agent_id: str,
        output: str = "",
        status: ResultStatus = ResultStatus.SUCCESS,
        artifacts: dict[str, Any] | None = None,
        metrics: dict[str, float] | None = None,
        errors: list[str] | None = None,
    ) -> AgentResult:
        """
        收集单个 agent 结果

        Args:
            agent_id: agent 标识符
            output: 输出内容
            status: 执行状态
            artifacts: 产物字典
            metrics: 指标字典
            errors: 错误列表

        Returns:
            AgentResult 对象
        """
        result = AgentResult(
            agent_id=agent_id,
            status=status,
            output=output,
            artifacts=artifacts or {},
            metrics=metrics or {},
            errors=errors or [],
        )

        if status == ResultStatus.FAILURE and not result.errors:
            result.errors.append("Execution failed without specific error message")

        return result

    def merge_results(
        self,
        primary: AgentResult,
        secondaries: list[AgentResult],
        strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.MERGE,
    ) -> CollectedResult:
        """
        合并多个 agent 结果

        Args:
            primary: 主结果
            secondaries: 辅助结果列表
            strategy: 冲突解决策略

        Returns:
            CollectedResult 合并结果对象
        """
        collected = CollectedResult(
            primary_result=primary,
            secondary_results=secondaries,
            resolution_strategy=strategy,
        )

        all_results = [primary] + secondaries

        if strategy == ConflictResolutionStrategy.PREFER_PRIMARY:
            collected.merged_output = primary.output
            collected.merged_artifacts = dict(primary.artifacts)
        elif strategy == ConflictResolutionStrategy.PREFER_SECONDARY and secondaries:
            best_secondary = max(secondaries, key=lambda r: len(r.output))
            collected.merged_output = best_secondary.output
            collected.merged_artifacts = dict(best_secondary.artifacts)
        elif strategy == ConflictResolutionStrategy.MERGE:
            output_parts: list[str] = []
            if primary.output:
                output_parts.append(f"## 主Agent [{primary.agent_id}] 输出\n\n{primary.output}")
            for idx, secondary in enumerate(secondaries, 1):
                if secondary.output:
                    output_parts.append(f"\n## 辅助Agent #{idx} [{secondary.agent_id}] 补充\n\n{secondary.output}")
            collected.merged_output = "\n".join(output_parts)

            merged_artifacts: dict[str, Any] = {}
            for result in all_results:
                for art_key, art_value in result.artifacts.items():
                    if art_key not in merged_artifacts:
                        merged_artifacts[art_key] = art_value
            collected.merged_artifacts = merged_artifacts
        else:
            collected.merged_output = primary.output
            collected.merged_artifacts = dict(primary.artifacts)
            collected.conflicts_detected.append({
                "type": "escalation_required",
                "message": "需要人工介入解决冲突",
                "agents_involved": [r.agent_id for r in all_results],
            })

        conflicts = self.detect_conflicts(primary, secondaries)
        collected.conflicts_detected = conflicts

        if conflicts and strategy != ConflictResolutionStrategy.ESCALATE:
            collected = self.resolve_conflicts(collected, strategy)

        collected.aggregated_metrics = self.aggregate_metrics(all_results)
        self._collections[collected.collection_id] = collected

        return collected

    def detect_conflicts(
        self,
        primary: AgentResult,
        secondaries: list[AgentResult],
    ) -> list[dict[str, Any]]:
        """
        检测结果冲突（意见不一致、重叠建议等）

        Args:
            primary: 主结果
            secondaries: 辅助结果列表

        Returns:
            冲突详情列表
        """
        conflicts: list[dict[str, Any]] = []

        primary_keywords = set(self._extract_keywords(primary.output))
        for secondary in secondaries:
            secondary_keywords = set(self._extract_keywords(secondary.output))

            disagreement_indicators = [
                ("但是", "but"), ("然而", "however"), ("不建议", "not recommend"),
                ("相反", "conversely"), ("应该避免", "should avoid"),
                ("better not", "avoid"), ("instead", ""),
            ]

            for cn_hint, en_hint in disagreement_indicators:
                if cn_hint in secondary.output or en_hint in secondary.output.lower():
                    overlap = primary_keywords & secondary_keywords
                    if len(overlap) > 3:
                        conflicts.append({
                            "type": "opinion_divergence",
                            "primary_agent": primary.agent_id,
                            "secondary_agent": secondary.agent_id,
                            "shared_topics": list(overlap)[:5],
                            "severity": "medium",
                            "hint": cn_hint or en_hint,
                        })

            for art_key in primary.artifacts:
                if art_key in secondary.artifacts:
                    if primary.artifacts[art_key] != secondary.artifacts[art_key]:
                        conflicts.append({
                            "type": "artifact_conflict",
                            "artifact": art_key,
                            "primary_value": str(primary.artifacts[art_key])[:100],
                            "secondary_value": str(secondary.artifacts[art_key])[:100],
                            "severity": "high",
                        })

        if primary.status != ResultStatus.SUCCESS:
            for secondary in secondaries:
                if secondary.status == ResultStatus.SUCCESS:
                    conflicts.append({
                        "type": "status_inconsistency",
                        "primary_status": primary.status.value,
                        "secondary_status": secondary.status.value,
                        "severity": "low",
                    })

        return conflicts

    def resolve_conflicts(
        self,
        collected: CollectedResult,
        strategy: ConflictResolutionStrategy,
    ) -> CollectedResult:
        """
        冲突解决（按策略处理）

        Args:
            collected: 收集结果
            strategy: 解决策略

        Returns:
            处理后的 CollectedResult
        """
        resolved_conflicts: list[dict[str, Any]] = []

        for conflict in collected.conflicts_detected:
            conflict_type = conflict.get("type", "")

            if conflict_type == "opinion_divergence":
                if strategy == ConflictResolutionStrategy.MERGE:
                    resolved_conflicts.append({**conflict, "resolution": "merged_with_annotation"})
                elif strategy == ConflictResolutionStrategy.PREFER_PRIMARY:
                    resolved_conflicts.append({**conflict, "resolution": "accepted_primary_view"})
                elif strategy == ConflictResolutionStrategy.PREFER_SECONDARY:
                    resolved_conflicts.append({**conflict, "resolution": "accepted_secondary_view"})
                else:
                    resolved_conflicts.append({**conflict, "resolution": "escalated_for_review"})

            elif conflict_type == "artifact_conflict":
                artifact = conflict.get("artifact", "")
                if strategy in (ConflictResolutionStrategy.PREFER_PRIMARY, ConflictResolutionStrategy.MERGE):
                    if collected.primary_result and artifact in collected.primary_result.artifacts:
                        collected.merged_artifacts[artifact] = collected.primary_result.artifacts[artifact]
                    resolved_conflicts.append({**conflict, "resolution": "kept_primary_version"})
                else:
                    resolved_conflicts.append({**conflict, "resolution": "flagged_for_review"})

            else:
                resolved_conflicts.append({**conflict, "resolution": "acknowledged"})

        collected.conflicts_detected = resolved_conflicts
        return collected

    def aggregate_metrics(self, results: list[AgentResult]) -> dict[str, float]:
        """
        聚合指标（成功率、平均耗时、质量评分等）

        Args:
            results: AgentResult 列表

        Returns:
            聚合后的指标字典
        """
        if not results:
            return {}

        total = len(results)
        success_count = sum(1 for r in results if r.status == ResultStatus.SUCCESS)
        partial_count = sum(1 for r in results if r.status == ResultStatus.PARTIAL)

        all_metric_values: dict[str, list[float]] = {}
        for result in results:
            for metric_key, metric_value in result.metrics.items():
                all_metric_values.setdefault(metric_key, []).append(float(metric_value))

        aggregated: dict[str, float] = {
            "total_agents": float(total),
            "success_rate": round(success_count / total, 3),
            "partial_rate": round(partial_count / total, 3),
            "failure_rate": round((total - success_count - partial_count) / total, 3),
        }

        for metric_key, values in all_metric_values.items():
            aggregated[f"{metric_key}_avg"] = round(sum(values) / len(values), 3)
            aggregated[f"{metric_key}_min"] = round(min(values), 3)
            aggregated[f"{metric_key}_max"] = round(max(values), 3)

        avg_output_len = sum(len(r.output) for r in results) / total
        aggregated["avg_output_length"] = round(avg_output_len, 1)

        return aggregated

    def format_unified_output(self, collected: CollectedResult, format_type: str = "markdown") -> str:
        """
        格式化统一输出

        Args:
            collected: 收集结果
            format_type: 输出格式 ('markdown', 'json')

        Returns:
            格式化后的字符串
        """
        if format_type == "json":
            return json.dumps(collected.to_dict(), ensure_ascii=False, indent=2)

        lines: list[str] = [
            "# 📦 Agent 结果汇总报告",
            f"\n> **收集ID**: `{collected.collection_id}`",
            f"> **主Agent**: {collected.primary_result.agent_id if collected.primary_result else 'N/A'}",
            f"> **辅助Agent数**: {len(collected.secondary_results)}",
            f"> **解决策略**: {collected.resolution_strategy.value}",
            f"> **收集时间**: {collected.collected_at}\n",
        ]

        metrics = collected.aggregated_metrics
        if metrics:
            lines.extend([
                "## 📊 聚合指标\n",
                "| 指标 | 值 |",
                "|------|-----|",
            ])
            for metric_key, metric_value in sorted(metrics.items()):
                lines.append(f"| {metric_key} | {metric_value} |")

        if collected.merged_output:
            output_preview = collected.merged_output[:1000]
            lines.extend([
                f"\n## 📝 合并输出\n",
                f"```",
                output_preview,
                "```",
            ])
            if len(collected.merged_output) > 1000:
                lines.append(f"\n*... 输出已截断, 完整长度: {len(collected.merged_output)} 字符*")

        if collected.merged_artifacts:
            lines.append("\n## 🎁 合并产物\n")
            for art_key, art_value in collected.merged_artifacts.items():
                value_str = str(art_value)[:100]
                lines.append(f"- **{art_key}**: {value_str}")

        if collected.conflicts_detected:
            lines.append(f"\n## ⚠️ 冲突记录 ({len(collected.conflicts_detected)})\n")
            for conflict in collected.conflicts_detected[:5]:
                resolution = conflict.get("resolution", "pending")
                lines.append(f"- [{conflict.get('type')}] {resolution}")

        return "\n".join(lines)

    def generate_summary_report(self, collections: list[CollectedResult] | None = None) -> str:
        """
        生成汇总报告

        Args:
            collections: CollectedResult 列表（默认使用全部已收集的结果）

        Returns:
            Markdown 格式的汇总报告
        """
        target_collections = collections or list(self._collections.values())

        if not target_collections:
            return "# 📋 结果汇总报告\n\n暂无收集数据。\n"

        total_collections = len(target_collections)
        total_agents = sum(len(c.secondary_results) + (1 if c.primary_result else 0) for c in target_collections)
        total_conflicts = sum(len(c.conflicts_detected) for c in target_collections)

        strategy_counts: dict[str, int] = {}
        status_counts: dict[str, int] = {}
        all_metrics: list[dict[str, float]] = [c.aggregated_metrics for c in target_collections if c.aggregated_metrics]

        for col in target_collections:
            strat = col.resolution_strategy.value
            strategy_counts[strat] = strategy_counts.get(strat, 0) + 1
            if col.primary_result:
                status = col.primary_result.status.value
                status_counts[status] = status_counts.get(status, 0) + 1

        avg_success_rate = 0.0
        if all_metrics:
            rates = [m.get("success_rate", 0) for m in all_metrics]
            avg_success_rate = sum(rates) / len(rates)

        lines: list[str] = [
            "# 📋 Agent 结果汇总报告",
            f"\n> **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"> **收集批次**: {total_collections}",
            f"> **涉及Agent**: {total_agents}\n",
            "## 总览统计\n",
            "| 指标 | 数值 |",
            "|------|------|",
            f"| 总收集批次 | {total_collections} |",
            f"| 涉及Agent总数 | {total_agents} |",
            f"| 检测到冲突 | {total_conflicts} |",
            f"| 平均成功率 | {avg_success_rate:.1%} |\n",
        ]

        if strategy_counts:
            lines.extend(["## 解决策略分布\n", "| 策略 | 使用次数 |", "|------|----------|"])
            for strat, count in sorted(strategy_counts.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"| {strat} | {count} |")

        if status_counts:
            lines.extend(["\n## 主Agent状态分布\n", "| 状态 | 数量 |", "|------|------|"])
            for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"| {status} | {count} |")

        recent = target_collections[-3:] if len(target_collections) >= 3 else target_collections
        if recent:
            lines.append("\n## 最近收集\n")
            for col in recent:
                primary_name = col.primary_result.agent_id if col.primary_result else "?"
                agent_count = 1 + len(col.secondary_results) if col.primary_result else len(col.secondary_results)
                lines.append(
                    f"- `{col.collection_id}`: **{primary_name}** + {agent_count} agents | "
                    f"{len(col.conflicts_detected)} conflicts"
                )

        return "\n".join(lines)

    def persist_results(self, collected: CollectedResult | None = None) -> Path:
        """
        持久化结果到日志目录

        Args:
            collected: 要保存的收集结果（默认保存全部）

        Returns:
            保存的文件路径
        """
        targets = [collected] if collected else list(self._collections.values())

        try:
            self._output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise RuntimeError(f"无法创建输出目录 [{self._output_dir}]: {e}") from e

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if len(targets) == 1 and targets[0]:
            col = targets[0]
            filename = f"agent_result_{col.collection_id}_{timestamp}.json"
            filepath = self._output_dir / filename
            data = col.to_dict()
        else:
            filename = f"agent_results_batch_{timestamp}.json"
            filepath = self._output_dir / filename
            data = {
                "batch_timestamp": timestamp,
                "total_collections": len(targets),
                "collections": [c.to_dict() for c in targets],
            }

        try:
            filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as e:
            raise RuntimeError(f"写入结果文件失败 [{filepath}]: {e}") from e

        return filepath

    def get_collection(self, collection_id: str) -> CollectedResult | None:
        """获取指定收集结果"""
        return self._collections.get(collection_id)

    def get_all_collections(self) -> list[CollectedResult]:
        """获取所有收集结果"""
        return list(self._collections.values())

    @staticmethod
    def _extract_keywords(text: str) -> list[str]:
        """从文本中提取关键词"""
        words = text.lower().split()
        meaningful = [w for w in words if len(w) > 3 and w.isalpha()]
        return meaningful[:20]


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 结果收集器测试")
    print("=" * 60)

    collector = AgentResultCollector()

    print("\n--- 单个结果收集 ---")
    r1 = collector.collect_result(
        agent_id="engineering_frontend_developer",
        output="完成了React组件的开发，使用了TypeScript和Hooks模式。组件支持响应式设计。",
        status=ResultStatus.SUCCESS,
        artifacts={"component.jsx": "// React component code...", "styles.css": "/* styles */"},
        metrics={"quality_score": 8.5, "speed": 9.0},
    )
    print(f"✅ Agent: {r1.agent_id}, Status: {r1.status.value}")
    print(f"   Output length: {len(r1.output)}, Artifacts: {list(r1.artifacts.keys())}")

    r2 = collector.collect_result(
        agent_id="design_ui_designer",
        output="建议使用更现代的设计系统，但要注意保持与现有品牌一致性。颜色方案应该重新考虑。",
        status=ResultStatus.SUCCESS,
        artifacts={"design_spec.md": "# Design specifications..."},
        metrics={"quality_score": 7.8, "creativity": 9.2},
    )
    print(f"✅ Agent: {r2.agent_id}, Status: {r2.status.value}")

    r3 = collector.collect_result(
        agent_id="testing_evidence_collector",
        output="测试用例编写完成，覆盖了主要用户场景。但是边界情况还需要补充。",
        status=ResultStatus.PARTIAL,
        metrics={"coverage": 78.0},
        warnings=["部分边界情况未覆盖"],
    )
    print(f"✅ Agent: {r3.agent_id}, Status: {r3.status.value}, Warnings: {len(r3.warnings)}")

    print("\n--- 结果合并 ---")
    merged = collector.merge_results(r1, [r2, r3], ConflictResolutionStrategy.MERGE)
    print(f"✅ Collection ID: {merged.collection_id}")
    print(f"✅ Strategy: {merged.resolution_strategy.value}")
    print(f"✅ Merged output length: {len(merged.merged_output)}")
    print(f"✅ Artifacts: {list(merged.merged_artifacts.keys())}")
    print(f"✅ Conflicts: {len(merged.conflicts_detected)}")

    if merged.conflicts_detected:
        for c in merged.conflicts_detected[:2]:
            print(f"   ⚠️  {c.get('type')}: {c.get('resolution')}")

    print("\n--- 指标聚合 ---")
    metrics = merged.aggregated_metrics
    print(f"✅ Success rate: {metrics.get('success_rate')}")
    print(f"✅ Avg quality: {metrics.get('quality_score_avg')}")
    print(f"✅ Total agents: {metrics.get('total_agents')}")

    print("\n--- 统一输出格式化 ---")
    formatted = collector.format_unified_output(merged, "markdown")
    print(formatted[:600])

    print("\n--- 汇总报告 ---")
    report = collector.generate_summary_report()
    print(report[:400])

    print("\n✅ 结果收集器测试通过!")
