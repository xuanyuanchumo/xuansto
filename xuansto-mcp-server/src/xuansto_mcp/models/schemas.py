from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ConfigDict


class SkillAnalyzeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    skill_path: str = Field(description="技能根目录路径")
    include_scripts: bool = Field(default=True, description="是否分析scripts目录")
    include_agents: bool = Field(default=True, description="是否分析agents目录")
    depth: str = Field(default="basic", description="分析深度: basic 或 full")


class KnowledgeSearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str = Field(default="retrieve", description="操作类型: retrieve, inject, precipitate")
    query: str | None = Field(default=None, description="搜索查询文本")
    top_k: int = Field(default=5, ge=1, le=50, description="返回结果数量上限")
    search_type: str = Field(default="hybrid", description="搜索策略: hybrid, semantic_only, keyword_only")
    scope: str | None = Field(default=None, description="限定搜索范围: general, workspace, experience")
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="最低置信度阈值")
    content: str | None = Field(default=None, description="注入的知识内容(inject时使用)")
    knowledge_type: str = Field(default="general", description="知识类型(inject时使用): general, workspace, experience")
    metadata: dict[str, Any] | None = Field(default=None, description="附加元数据(inject时使用)")
    pattern_ids: list[str] | None = Field(default=None, description="模式ID列表(precipitate时使用)")


class QualityGateCheckInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gate_ids: list[str] | None = Field(default=None, description="要检查的门禁ID列表，为空则检查全部")
    phase: str | None = Field(default=None, description="按阶段过滤门禁(0-8)")
    project_path: str = Field(default=".", description="项目根目录路径")
    severity_filter: str = Field(default="all", description="严重级别过滤: all, BLOCK, WARN")
    force_refresh: bool = Field(default=False, description="强制刷新缓存，忽略文件哈希缓存")


class SpecDriftDetectInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    spec_dir: str = Field(default=".trae/specs", description="规格文档目录")
    src_dir: str = Field(default=".", description="源代码目录")


class SecurityScanInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target: str = Field(default=".", description="目标扫描目录")
    severity_threshold: str = Field(default="medium", description="最低报告严重级别: critical, high, medium, low")
    include_agentic: bool = Field(default=True, description="是否包含OWASP Agentic Top 10检查")
    include_dependency: bool = Field(default=True, description="是否包含依赖漏洞扫描")


class CodeSimplifyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target: str = Field(description="目标文件或目录路径")
    scope: str = Field(default="recent", description="扫描范围: file, dir, recent")
    include_dedup: bool = Field(default=True, description="是否包含重复代码检测")


class SessionManageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str = Field(description="操作类型: save, load, list, detect, verify, track, restore")
    completed_tasks: list[str] | None = Field(default=None, description="已完成任务列表(save时使用)")
    pending_tasks: list[str] | None = Field(default=None, description="未完成任务列表(save/track时使用)")
    decisions: list[str] | None = Field(default=None, description="关键决策列表(save/track时使用)")
    experience: list[str] | None = Field(default=None, description="经验沉淀列表(save时使用)")
    error_log: list[str] | None = Field(default=None, description="错误日志(detect时使用)")
    pattern_path: str | None = Field(default=None, description="模式文件路径(verify时使用)")
    success: bool = Field(default=True, description="验证是否成功(verify时使用)")
    current_phase: int | None = Field(default=None, description="当前阶段编号(track时使用)")
    current_task: str | None = Field(default=None, description="当前任务描述(track时使用)")


class WorkflowDispatchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str = Field(description="操作类型: start, status, abort, phase, recover, snapshots")
    workflow: str | None = Field(default=None, description="工作流名称(start时使用): sdd-tdd-full, sdd-tdd-medium, sdd-tdd-fast等")
    project_path: str = Field(default=".", description="项目根目录路径(start时使用)")
    workflow_id: str | None = Field(default=None, description="工作流实例ID(status/abort/phase/recover/snapshots时使用)")
    phase_action: str | None = Field(default=None, description="阶段操作(phase时使用): advance, current")
    snapshot_phase: int | None = Field(default=None, description="恢复到指定阶段的快照(recover时使用)")


class AgentStatusInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str = Field(description="操作类型: list, by_phase, detail, create, match, assign, release, instance_status, destroy, schedule")
    phase: int | None = Field(default=None, ge=0, le=8, description="按阶段查询Agent(by_phase时使用, 0-8)")
    agent_name: str | None = Field(default=None, description="Agent名称(detail时使用)")
    agent_type: str | None = Field(default=None)
    capabilities: list[str] | None = Field(default=None)
    agent_id: str | None = Field(default=None)
    task: str | None = Field(default=None)


class HookManageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str = Field(description="操作类型: list, execute")
    profile: str = Field(default="standard", description="Hook配置级别: minimal, standard, strict")
    hook_name: str | None = Field(default=None, description="Hook名称(execute时使用)")
    context: dict[str, Any] | None = Field(default=None, description="执行上下文(execute时使用)")


class ResourceLoadStatusInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str = Field(description="操作类型: status, preload, cache, clear_cache, loading_progress")
    phase: int | None = Field(default=None, ge=0, le=8, description="目标阶段(0-8)")
    resource_ids: list[str] | None = Field(default=None, description="指定资源ID列表")
    resource_uris: list[str] | None = Field(default=None, description="资源URI列表(preload时使用)")
    priority: str = Field(default="normal", description="预加载优先级(preload时使用): critical, normal, background")
    batch_mode: bool = Field(default=False, description="是否批量预加载模式(preload时使用)，批量模式并发加载多个资源")


class ContextCompressInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str = Field(description="待压缩的文本内容")
    strategy: str = Field(default="semantic", description="压缩策略: semantic, selective, lossless")
    target_tokens: int = Field(default=2000, ge=100, le=50000, description="目标Token数量")
    preserve_sections: list[str] | None = Field(default=None, description="必须保留的章节标题列表")
