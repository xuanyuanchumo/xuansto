from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DegradationConfigModel(BaseModel):
    model_config = ConfigDict(extra="allow")
    health_check_interval: float = Field(default=30.0, ge=1.0, le=3600.0)


class SkillConfigModel(BaseModel):
    model_config = ConfigDict(extra="allow")
    gate_scripts: dict[str, str | None] = Field(default_factory=dict)
    gates_by_phase: dict[str, list[str]] = Field(default_factory=dict)
    hook_scripts: dict[str, str | None] = Field(default_factory=dict)
    max_snapshots_per_workflow: int = Field(default=20, ge=1, le=1000)
    snapshot_ttl_days: int = Field(default=30, ge=1, le=365)
    degradation: DegradationConfigModel = Field(default_factory=DegradationConfigModel)


class FallbackEntryModel(BaseModel):
    model_config = ConfigDict(extra="allow")
    component: str = Field(default="")
    fallback_action: str = Field(default="disable")
    timeout_ms: int = Field(default=5000, ge=100, le=60000)
    retry_count: int = Field(default=3, ge=0, le=10)
    degradation_level: str = Field(default="none")


class FallbackConfigModel(BaseModel):
    model_config = ConfigDict(extra="allow")
    fallbacks: list[FallbackEntryModel] = Field(default_factory=list)
    default_timeout_ms: int = Field(default=5000, ge=100, le=60000)
    default_retry_count: int = Field(default=3, ge=0, le=10)


class ConstraintsModel(BaseModel):
    model_config = ConfigDict(extra="allow")
    max_file_size_kb: int = Field(default=500, ge=1, le=100000)
    max_line_length: int = Field(default=120, ge=40, le=1000)
    max_function_lines: int = Field(default=50, ge=5, le=500)
    max_complexity: int = Field(default=10, ge=1, le=100)
    forbidden_patterns: list[str] = Field(default_factory=list)
    required_patterns: list[str] = Field(default_factory=list)
    encoding: str = Field(default="utf-8")
    comment_language: str = Field(default="any")
