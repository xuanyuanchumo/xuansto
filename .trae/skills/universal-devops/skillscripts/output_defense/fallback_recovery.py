"""
兜底恢复机制（第四维防线）- Fallback Recovery

提供四级输出降级策略、指数退避自动重试、
状态回滚（快照）、人工介入请求触发等最终保障能力。
"""

from __future__ import annotations

import copy
import json
import re
import shutil
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class FallbackLevel(Enum):
    """四级输出降级策略枚举"""

    FULL = auto()
    SIMPLIFIED = auto()
    SKELETON = auto()
    ERROR = auto()

    @property
    def priority(self) -> int:
        _order = {FallbackLevel.FULL: 0, FallbackLevel.SIMPLIFIED: 1, FallbackLevel.SKELETON: 2, FallbackLevel.ERROR: 3}
        return _order[self]

    def next_lower(self) -> "FallbackLevel":
        order = [FallbackLevel.FULL, FallbackLevel.SIMPLIFIED, FallbackLevel.SKELETON, FallbackLevel.ERROR]
        idx = order.index(self)
        return order[idx + 1] if idx < len(order) - 1 else FallbackLevel.ERROR


@dataclass
class FallbackStrategy:
    """降级策略配置数据类"""

    level: FallbackLevel = FallbackLevel.FULL
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    compression_ratio: float = 0.2
    enable_rollback: bool = True
    enable_human_intervention: bool = True
    snapshot_dir: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Snapshot:
    """状态快照数据类"""

    snapshot_id: str
    timestamp: str
    level: FallbackLevel
    content: Any
    context_snapshot: dict[str, Any]
    error_log: list[str] = field(default_factory=list)
    retry_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "level": self.level.name,
            "content": str(self.content) if not isinstance(self.content, (dict, list)) else self.content,
            "context_snapshot": self.context_snapshot,
            "error_log": self.error_log,
            "retry_count": self.retry_count,
        }


@dataclass
class HumanInterventionRequest:
    """
    人工介入请求数据结构

    当自动恢复全部失败时，生成结构化的人工介入请求文档。
    """

    request_id: str
    timestamp: str
    task_description: str
    failure_summary: str
    attempted_levels: list[FallbackLevel] = field(default_factory=list)
    error_history: list[dict[str, Any]] = field(default_factory=list)
    last_working_snapshot: Snapshot | None = None
    suggested_actions: list[str] = field(default_factory=list)
    urgency: str = "medium"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        lines = [
            "# Human Intervention Request",
            f"",
            f"**Request ID:** {self.request_id}",
            f"**Timestamp:** {self.timestamp}",
            f"**Urgency:** {self.urgency.upper()}",
            f"",
            f"## Task Description",
            f"{self.task_description}",
            f"",
            f"## Failure Summary",
            f"{self.failure_summary}",
            f"",
            f"## Attempted Recovery Levels",
        ]
        for level in self.attempted_levels:
            lines.append(f"- {level.name} ({'FAILED' if level != self.attempted_levels[-1] or True else 'OK'})")
        lines.extend([
            "",
            "## Error History",
        ])
        for i, err in enumerate(self.error_history, 1):
            lines.append(f"{i}. **{err.get('timestamp', 'N/A')}** [{err.get('level', 'N/A')}] {err.get('message', 'No message')}")
        if self.last_working_snapshot:
            lines.extend([
                "",
                "## Last Working State",
                f"- Snapshot ID: {self.last_working_snapshot.snapshot_id}",
                f"- Timestamp: {self.last_working_snapshot.timestamp}",
                f"- Level: {self.last_working_snapshot.level.name}",
            ])
        if self.suggested_actions:
            lines.extend(["", "## Suggested Actions"])
            for action in self.suggested_actions:
                lines.append(f"- [ ] {action}")
        return "\n".join(lines)


@dataclass
class FallbackContext:
    """
    降级上下文管理器

    支持with语句使用，自动管理降级过程和资源清理。
    """

    strategy: FallbackStrategy
    original_content: Any = None
    current_level: FallbackLevel = field(init=False)
    snapshots: list[Snapshot] = field(init=False, default_factory=list)
    errors: list[str] = field(init=False, default_factory=list)
    retry_count: int = field(init=False, default=0)
    _active: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        self.current_level = self.strategy.level

    def __enter__(self) -> "FallbackContext":
        self._active = True
        self._take_snapshot("initial")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> bool:
        self._active = False
        if exc_val is not None:
            self.errors.append(str(exc_val))
            return False
        return True

    @property
    def is_active(self) -> bool:
        return self._active

    def can_retry(self) -> bool:
        return self.retry_count < self.strategy.max_retries and self.current_level != FallbackLevel.ERROR

    def record_error(self, error: str) -> None:
        self.errors.append(error)

    def degrade(self) -> FallbackLevel:
        new_level = self.current_level.next_lower()
        self.current_level = new_level
        self.retry_count += 1
        return new_level

    def get_retry_delay(self) -> float:
        delay = self.strategy.base_delay * (2 ** (self.retry_count - 1))
        return min(delay, self.strategy.max_delay)

    def compress_context(self, context: dict[str, Any], ratio: float | None = None) -> dict[str, Any]:
        r = ratio or self.strategy.compression_ratio
        compressed: dict[str, Any] = {}
        for key, value in context.items():
            if isinstance(value, str):
                keep_len = max(50, int(len(value) * r))
                compressed[key] = value[:keep_len] + "... [TRUNCATED]" if len(value) > keep_len else value
            elif isinstance(value, (list, tuple)):
                keep_count = max(1, int(len(value) * r))
                compressed[key] = list(value[:keep_count])
            elif isinstance(value, dict):
                compressed[key] = self.compress_context(value, ratio)
            else:
                compressed[key] = value
        return compressed

    def _take_snapshot(self, label: str = "") -> None:
        from datetime import datetime, timezone
        snap = Snapshot(
            snapshot_id=f"snap_{len(self.snapshots):04d}_{label}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=self.current_level,
            content=copy.deepcopy(self.original_content),
            context_snapshot={},
            error_log=list(self.errors),
            retry_count=self.retry_count,
        )
        self.snapshots.append(snap)

    def get_last_stable_snapshot(self) -> Snapshot | None:
        stable = None
        for snap in reversed(self.snapshots):
            if len(snap.error_log) == 0 and snap.level.priority <= FallbackLevel.SIMPLIFIED.priority:
                stable = snap
                break
        return stable or (self.snapshots[0] if self.snapshots else None)


@dataclass
class FallbackRecovery:
    """
    兜底恢复机制 - 第四维输出防线

    职责：
      - 四级输出降级策略管理
      - 指数退避自动重试
      - 状态快照与回滚
      - 人工介入请求生成
    """

    default_strategy: FallbackStrategy = field(default_factory=FallbackStrategy)
    _context_stack: list[FallbackContext] = field(init=False, default_factory=list)
    _request_history: list[HumanInterventionRequest] = field(init=False, default_factory=list)

    def create_context(
        self,
        initial_content: Any = None,
        strategy: FallbackStrategy | None = None,
    ) -> FallbackContext:
        strat = strategy or self.default_strategy
        ctx = FallbackContext(strategy=strat, original_content=initial_content)
        return ctx

    @contextmanager
    def recovery_session(
        self,
        initial_content: Any = None,
        strategy: FallbackStrategy | None = None,
    ) -> Any:
        ctx = self.create_context(initial_content, strategy)
        self._context_stack.append(ctx)
        try:
            with ctx as session_ctx:
                yield session_ctx
        finally:
            self._context_stack.pop()

    def attempt_recovery(
        self,
        execute_func: Any,
        context: dict[str, Any] | None = None,
        strategy: FallbackStrategy | None = None,
    ) -> tuple[Any, FallbackLevel, HumanInterventionRequest | None]:
        ctx = self.create_context(strategy=strategy)
        self._context_stack.append(ctx)
        try:
            with ctx:
                ctx.original_content = context
                ctx._take_snapshot("before_execution")
                result = self._execute_with_retry(execute_func, context, ctx)
                return result, ctx.current_level, None
        except Exception as e:
            ctx.record_error(str(e))
            intervention = self._generate_intervention_request(ctx, str(e))
            self._request_history.append(intervention)
            return None, FallbackLevel.ERROR, intervention
        finally:
            if self._context_stack and self._context_stack[-1] is ctx:
                self._context_stack.pop()

    def _execute_with_retry(
        self,
        func: Any,
        context: dict[str, Any] | None,
        ctx: FallbackContext,
    ) -> Any:
        working_context = context or {}
        while ctx.can_retry():
            try:
                if ctx.retry_count > 0:
                    delay = ctx.get_retry_delay()
                    time.sleep(delay)
                    working_context = ctx.compress_context(working_context)
                result = func(working_context, ctx.current_level)
                ctx._take_snapshot(f"success_attempt_{ctx.retry_count}")
                return result
            except Exception as e:
                ctx.record_error(str(e))
                new_level = ctx.degrade()
                ctx._take_snapshot(f"degraded_to_{new_level.name}")
                if new_level == FallbackLevel.ERROR:
                    raise RuntimeError(
                        f"All recovery attempts exhausted after {ctx.retry_count} retries. "
                        f"Final errors: {ctx.errors}"
                    ) from e
        raise RuntimeError(f"Max retries ({ctx.strategy.max_retries}) exceeded")

    def _generate_intervention_request(
        self,
        ctx: FallbackContext,
        final_error: str,
    ) -> HumanInterventionRequest:
        from datetime import datetime, timezone
        from uuid import uuid4
        attempted = []
        if ctx.snapshots:
            levels_seen = set()
            for snap in ctx.snapshots:
                if snap.level not in levels_seen:
                    attempted.append(snap.level)
                    levels_seen.add(snap.level)
        suggested = [
            "Review the task description for ambiguous requirements",
            "Check if the input data format matches expectations",
            "Verify all required dependencies are available",
            "Consider simplifying the task scope",
            "Review system resource availability (memory/disk)",
        ]
        request = HumanInterventionRequest(
            request_id=f"HIR-{uuid4().hex[:8].upper()}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_description="Automated task execution failed",
            failure_summary=f"After {ctx.retry_count} attempts across {len(attempted)} degradation levels: {final_error}",
            attempted_levels=attempted,
            error_history=[
                {"timestamp": datetime.now(timezone.utc).isoformat(), "level": ctx.current_level.name, "message": err}
                for err in ctx.errors[-5:]
            ],
            last_working_snapshot=ctx.get_last_stable_snapshot(),
            suggested_actions=suggested,
            urgency="high" if ctx.current_level == FallbackLevel.ERROR else "medium",
        )
        return request

    def rollback_to_snapshot(self, snapshot: Snapshot) -> Any:
        return copy.deepcopy(snapshot.content)

    def rollback_to_last_stable(self, ctx: FallbackContext) -> tuple[Any, bool]:
        stable = ctx.get_last_stable_snapshot()
        if stable:
            return self.rollback_to_snapshot(stable), True
        return None, False

    def persist_snapshot(self, snapshot: Snapshot, directory: Path | str | None = None) -> Path | None:
        target_dir = Path(directory) if directory else (self.default_strategy.snapshot_dir or Path(".fallback_snapshots"))
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / f"{snapshot.snapshot_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(snapshot.to_dict(), f, ensure_ascii=False, indent=2, default=str)
        return file_path

    def load_snapshot(self, file_path: Path | str) -> Snapshot | None:
        path = Path(file_path)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        level_map = {name: lvl for name, lvl in FallbackLevel.__members__.items()}
        return Snapshot(
            snapshot_id=data["snapshot_id"],
            timestamp=data["timestamp"],
            level=level_map.get(data["level"], FallbackLevel.ERROR),
            content=data["content"],
            context_snapshot=data.get("context_snapshot", {}),
            error_log=data.get("error_log", []),
            retry_count=data.get("retry_count", 0),
        )

    def cleanup_old_snapshots(self, directory: Path | str | None = None, keep_recent: int = 10) -> int:
        target_dir = Path(directory) if directory else (self.default_strategy.snapshot_dir or Path(".fallback_snapshots"))
        if not target_dir.exists():
            return 0
        files = sorted(target_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        removed = 0
        for old_file in files[keep_recent:]:
            old_file.unlink()
            removed += 1
        return removed

    def generate_degraded_output(
        self,
        original_output: Any,
        level: FallbackLevel,
        error_message: str = "",
    ) -> str:
        if level == FallbackLevel.FULL:
            if isinstance(original_output, str):
                return original_output
            return json.dumps(original_output, ensure_ascii=False, indent=2, default=str)
        elif level == FallbackLevel.SIMPLIFIED:
            if isinstance(original_output, str):
                lines = original_output.splitlines()
                keep = max(5, len(lines) // 2)
                summary_lines = lines[:keep]
                if len(lines) > keep:
                    summary_lines.append(f"\n... [SIMPLIFIED: {len(lines) - keep} lines omitted]")
                return "\n".join(summary_lines)
            elif isinstance(original_output, dict):
                simplified = {"_degradation_note": "Simplified output", "_original_keys": list(original_output.keys())}
                top_keys = list(original_output.keys())[:5]
                for k in top_keys:
                    val = original_output[k]
                    if isinstance(val, str) and len(val) > 200:
                        simplified[k] = val[:200] + "..."
                    else:
                        simplified[k] = val
                return json.dumps(simplified, ensure_ascii=False, indent=2, default=str)
            return str(original_output)[:500]
        elif level == FallbackLevel.SKELETON:
            skeleton = (
                "# Output Skeleton (Degraded)\n\n"
                "## Structure Overview\n"
                "- Original output was too complex or generation failed\n"
                f"- Degradation Level: {level.name}\n"
            )
            if error_message:
                skeleton += f"- Last Error: {error_message}\n"
            if isinstance(original_output, dict):
                skeleton += "\n## Available Keys\n"
                for key in original_output.keys():
                    skeleton += f"- `{key}`\n"
            elif isinstance(original_output, str):
                headings = re.findall(r"^#{1,6}\s+(.+)$", original_output, re.MULTILINE)
                if headings:
                    skeleton += "\n## Document Structure\n"
                    for h in headings:
                        skeleton += f"- {h}\n"
                else:
                    preview = original_output[:300]
                    skeleton += f"\n## Content Preview\n```\n{preview}...\n```\n"
            else:
                skeleton += f"\n## Type Info\n- Type: {type(original_output).__name__}\n"
            return skeleton
        else:
            error_block = (
                "# ERROR: Output Generation Failed\n\n"
                "## Error Summary\n"
                "The system was unable to produce valid output after all recovery attempts.\n\n"
            )
            if error_message:
                error_block += f"**Last Error:** {error_message}\n\n"
            error_block += (
                "## Recommended Actions\n"
                "1. Review input parameters for correctness\n"
                "2. Check system resources and dependencies\n"
                "3. Simplify task requirements if possible\n"
                "4. Contact support with the error details above\n\n"
                "---\n"
                "*Generated by Universal DevOps v6.0 Fallback Recovery System*"
            )
            return error_block

    @property
    def active_context_count(self) -> int:
        return len(self._context_stack)

    @property
    def intervention_request_count(self) -> int:
        return len(self._request_history)

    def get_intervention_history(self, limit: int = 10) -> list[HumanInterventionRequest]:
        return self._request_history[-limit:]

    def clear_history(self) -> None:
        self._request_history.clear()
