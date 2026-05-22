"""
提示词工程层（第一维防线）- Prompt Engineering Layer

提供结构化Prompt模板库、Few-shot示例动态注入、
上下文窗口智能裁剪、角色人格一致性校验等核心能力。
"""

from __future__ import annotations

import re
import json
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class ReasoningChain(Enum):
    """推理链类型枚举"""

    COT = auto()
    REACT = auto()
    TOT = auto()


@dataclass(frozen=True)
class PromptTemplate:
    """结构化Prompt模板数据类"""

    name: str
    template_id: str
    reasoning_chain: ReasoningChain
    system_prompt: str
    task_description: str
    output_format: str
    constraints: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    metadata: dict[str, Any] = field(default_factory=dict)

    def render(self, **kwargs: Any) -> str:
        parts = [
            f"# System Prompt\n{self.system_prompt}",
            f"\n# Task\n{self.task_description.format(**kwargs)}",
            f"\n# Output Format\n{self.output_format}",
        ]
        if self.constraints:
            constraint_str = "\n".join(f"- {c}" for c in self.constraints)
            parts.append(f"\n# Constraints\n{constraint_str}")
        return "\n".join(parts)

    def fingerprint(self) -> str:
        raw = f"{self.name}:{self.template_id}:{self.version}:{self.system_prompt}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


@dataclass(frozen=True)
class FewShotExample:
    """Few-shot示例数据类"""

    example_id: str
    task_type: str
    input_text: str
    expected_output: str
    reasoning_trace: str = ""
    tags: list[str] = field(default_factory=list)
    difficulty: float = 0.5

    def relevance_score(self, query_task_type: str) -> float:
        if self.task_type == query_task_type:
            return 1.0 - self.difficulty * 0.3
        return max(0.0, 1.0 - self.difficulty)

    def to_prompt_block(self) -> str:
        block = f"## Example {self.example_id}\n"
        block += f"**Input:**\n{self.input_text}\n\n"
        if self.reasoning_trace:
            block += f"**Reasoning:**\n{self.reasoning_trace}\n\n"
        block += f"**Expected Output:**\n{self.expected_output}\n"
        return block


@dataclass
class ContextWindow:
    """上下文窗口管理器"""

    max_tokens: int = 128000
    reserved_tokens: int = 4096
    content: list[dict[str, Any]] = field(default_factory=list)
    token_counts: dict[str, int] = field(default_factory=dict)

    @property
    def used_tokens(self) -> int:
        return sum(self.token_counts.values())

    @property
    def available_tokens(self) -> int:
        return self.max_tokens - self.reserved_tokens - self.used_tokens

    def estimate_tokens(self, text: str) -> int:
        return len(text.split()) + len(text) // 4

    def add_content(self, role: str, text: str, priority: int = 5) -> bool:
        token_count = self.estimate_tokens(text)
        if token_count > self.available_tokens:
            return False
        entry_id = f"{role}_{len(self.content)}"
        self.content.append({"role": role, "text": text, "priority": priority, "id": entry_id})
        self.token_counts[entry_id] = token_count
        return True

    def trim_to_fit(self, target_tokens: int | None = None) -> list[dict[str, Any]]:
        limit = target_tokens or (self.max_tokens - self.reserved_tokens)
        sorted_content = sorted(self.content, key=lambda x: x.get("priority", 5), reverse=True)
        result = []
        current_tokens = 0
        for entry in sorted_content:
            entry_id = entry["id"]
            entry_tokens = self.token_counts.get(entry_id, 0)
            if current_tokens + entry_tokens <= limit:
                result.append({"role": entry["role"], "text": entry["text"]})
                current_tokens += entry_tokens
        return result

    def clear(self) -> None:
        self.content.clear()
        self.token_counts.clear()


@dataclass(frozen=True)
class RoleProfile:
    """角色人格配置数据类"""

    role_name: str
    description: str
    style_guidelines: list[str]
    forbidden_patterns: list[str] = field(default_factory=list)
    tone_keywords: set[str] = field(default_factory=set)
    response_length_range: tuple[int, int] = (50, 2000)


class BaseReasoningTemplate(ABC):
    """推理链模板基类"""

    @abstractmethod
    def build(self, template: PromptTemplate, examples: list[FewShotExample], context: dict[str, Any]) -> str:
        ...


class ChainOfThoughtTemplate(BaseReasoningTemplate):
    """CoT（思维链）推理模板"""

    def build(
        self,
        template: PromptTemplate,
        examples: list[FewShotExample],
        context: dict[str, Any],
    ) -> str:
        cot_header = (
            "Please think step by step and show your reasoning process clearly.\n"
            "Follow this structure:\n"
            "1. **Analysis**: Break down the problem\n"
            "2. **Reasoning**: Step-by-step logical deduction\n"
            "3. **Conclusion**: Final answer with confidence level"
        )
        parts = [template.render(**context), f"\n# Reasoning Method\n{cot_header}"]
        if examples:
            parts.append("\n# Examples")
            for ex in examples[:3]:
                parts.append(f"\n{ex.to_prompt_block()}")
        parts.append("\n# Your Response (follow the CoT structure above)")
        return "\n".join(parts)


class ReActTemplate(BaseReasoningTemplate):
    """ReAct（推理+行动）模板"""

    def build(
        self,
        template: PromptTemplate,
        examples: list[FewShotExample],
        context: dict[str, Any],
    ) -> str:
        react_header = (
            "Follow the ReAct pattern:\n"
            "- **Thought**: Analyze the current situation\n"
            "- **Action**: Decide what tool/action to use\n"
            "- **Observation**: Record the result\n"
            "- Repeat until you reach a final answer"
        )
        parts = [template.render(**context), f"\n# Reasoning Method\n{react_header}"]
        if examples:
            parts.append("\n# Examples")
            for ex in examples[:3]:
                parts.append(f"\n{ex.to_prompt_block()}")
        parts.append("\n# Your Response (follow Thought/Action/Observation loop)")
        return "\n".join(parts)


class TreeOfThoughtsTemplate(BaseReasoningTemplate):
    """ToT（思维树）推理模板"""

    def build(
        self,
        template: PromptTemplate,
        examples: list[FewShotExample],
        context: dict[str, Any],
    ) -> str:
        tot_header = (
            "Explore multiple reasoning paths using Tree of Thoughts:\n"
            "1. **Generate** 3-5 possible approaches\n"
            "2. **Evaluate** each approach pros/cons\n"
            "3. **Select** the best path and elaborate"
        )
        parts = [template.render(**context), f"\n# Reasoning Method\n{tot_header}"]
        if examples:
            parts.append("\n# Examples")
            for ex in examples[:3]:
                parts.append(f"\n{ex.to_prompt_block()}")
        parts.append("\n# Your Response (explore multiple paths systematically)")
        return "\n".join(parts)


class PromptEngineeringLayer:
    """
    提示词工程层 - 第一维输出防线

    职责：
      - 管理结构化Prompt模板库（CoT / ReAct / ToT）
      - Few-shot示例动态注入与检索
      - 上下文窗口智能裁剪与token计数
      - 角色人格一致性校验（风格漂移检测）
    """

    _TEMPLATE_REGISTRY: dict[ReasoningChain, type[BaseReasoningTemplate]] = {
        ReasoningChain.COT: ChainOfThoughtTemplate,
        ReasoningChain.REACT: ReActTemplate,
        ReasoningChain.TOT: TreeOfThoughtsTemplate,
    }

    def __init__(
        self,
        max_context_tokens: int = 128000,
        reserved_tokens: int = 4096,
    ) -> None:
        self._templates: dict[str, PromptTemplate] = {}
        self._examples: list[FewShotExample] = []
        self._context_window = ContextWindow(max_tokens=max_context_tokens, reserved_tokens=reserved_tokens)
        self._active_role: RoleProfile | None = None
        self._style_history: list[str] = []
        self._max_history_size: int = 20

    def register_template(self, template: PromptTemplate) -> None:
        self._templates[template.template_id] = template

    def unregister_template(self, template_id: str) -> None:
        self._templates.pop(template_id, None)

    def add_example(self, example: FewShotExample) -> None:
        self._examples.append(example)

    def remove_example(self, example_id: str) -> None:
        self._examples = [e for e in self._examples if e.example_id != example_id]

    def set_active_role(self, profile: RoleProfile) -> None:
        self._active_role = profile
        self._style_history.clear()

    def clear_active_role(self) -> None:
        self._active_role = None
        self._style_history.clear()

    def select_examples(self, task_type: str, top_k: int = 3) -> list[FewShotExample]:
        scored = [(ex, ex.relevance_score(task_type)) for ex in self._examples]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [ex for ex, _ in scored[:top_k]]

    def build_prompt(
        self,
        template_id: str,
        context: dict[str, Any],
        task_type: str = "",
        top_k_examples: int = 3,
    ) -> str:
        template = self._templates.get(template_id)
        if template is None:
            raise ValueError(f"Template '{template_id}' not found")
        examples = self.select_examples(task_type, top_k_examples) if task_type else []
        builder_cls = self._TEMPLATE_REGISTRY.get(template.reasoning_chain)
        if builder_cls is None:
            raise ValueError(f"No builder for reasoning chain: {template.reasoning_chain}")
        builder = builder_cls()
        prompt = builder.build(template, examples, context)
        if self._active_role:
            prompt = self._inject_role_instructions(prompt)
        return prompt

    def _inject_role_instructions(self, prompt: str) -> str:
        if not self._active_role:
            return prompt
        role_section = (
            f"\n# Role: {self._active_role.role_name}\n"
            f"{self._active_role.description}\n\n"
            f"Style Guidelines:\n"
        )
        for guideline in self._active_role.style_guidelines:
            role_section += f"- {guideline}\n"
        return prompt + role_section

    def add_to_context(self, role: str, text: str, priority: int = 5) -> bool:
        return self._context_window.add_content(role, text, priority)

    def get_trimmed_context(self, target_tokens: int | None = None) -> list[dict[str, Any]]:
        return self._context_window.trim_to_fit(target_tokens)

    def clear_context(self) -> None:
        self._context_window.clear()

    def validate_style_consistency(self, output_text: str) -> tuple[bool, list[str]]:
        if not self._active_role:
            return True, []
        issues: list[str] = []
        for pattern in self._active_role.forbidden_patterns:
            if re.search(pattern, output_text, re.IGNORECASE):
                issues.append(f"Forbidden pattern detected: {pattern}")
        words = output_text.split()
        if self._active_role.tone_keywords:
            keyword_matches = sum(1 for w in words if w.lower() in self._active_role.tone_keywords)
            if len(words) > 50 and keyword_matches == 0:
                issues.append("No tone keywords found; style may have drifted")
        lo, hi = self._active_role.response_length_range
        if len(words) < lo:
            issues.append(f"Response too short ({len(words)} words, minimum {lo})")
        elif len(words) > hi:
            issues.append(f"Response too long ({len(words)} words, maximum {hi})")
        self._style_history.append(output_text)
        if len(self._style_history) > self._max_history_size:
            self._style_history = self._style_history[-self._max_history_size :]
        return len(issues) == 0, issues

    @property
    def context_stats(self) -> dict[str, int]:
        return {
            "used_tokens": self._context_window.used_tokens,
            "available_tokens": self._context_window.available_tokens,
            "max_tokens": self._context_window.max_tokens,
            "content_entries": len(self._context_window.content),
        }

    @property
    def registered_template_ids(self) -> list[str]:
        return list(self._templates.keys())

    @property
    def example_count(self) -> int:
        return len(self._examples)
