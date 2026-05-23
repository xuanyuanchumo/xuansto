from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, ConfigDict


class DisclosureTransition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    from_phase: str = Field(description="源阶段名称")
    to_phase: str = Field(description="目标阶段名称")
    started_at: str | None = Field(default=None, description="转换开始时间(ISO8601)")
    completed_at: str | None = Field(default=None, description="转换完成时间(ISO8601)")
    resources_affected: list[str] = Field(default_factory=list, description="受影响的资源ID列表")
    status: Literal["pending", "in_progress", "completed", "failed"] = Field(default="pending", description="转换状态: pending/in_progress/completed/failed")


class SkillAnalyzeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    skill_path: str = Field(description="技能根目录路径")
    include_scripts: bool = Field(default=True, description="是否分析scripts目录")
    include_agents: bool = Field(default=True, description="是否分析agents目录")
    depth: Literal["basic", "full"] = Field(default="basic", description="分析深度: basic 或 full")


class KnowledgeSearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["retrieve", "inject", "precipitate"] = Field(default="retrieve", description="操作类型: retrieve, inject, precipitate")
    query: str | None = Field(default=None, description="搜索查询文本")
    top_k: int = Field(default=5, ge=1, le=50, description="返回结果数量上限")
    search_type: Literal["hybrid", "semantic_only", "keyword_only"] = Field(default="hybrid", description="搜索策略: hybrid, semantic_only, keyword_only")
    scope: Literal["general", "workspace", "experience"] | None = Field(default=None, description="限定搜索范围: general, workspace, experience")
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="最低置信度阈值")
    content: str | None = Field(default=None, description="注入的知识内容(inject时使用)")
    knowledge_type: Literal["general", "workspace", "experience"] = Field(default="general", description="知识类型(inject时使用): general, workspace, experience")
    metadata: dict[str, Any] | None = Field(default=None, description="附加元数据(inject时使用)")
    pattern_ids: list[str] | None = Field(default=None, description="模式ID列表(precipitate时使用)")


class QualityGateCheckInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gate_ids: list[str] | None = Field(default=None, description="要检查的门禁ID列表，为空则检查全部")
    phase: str | None = Field(default=None, description="按阶段过滤门禁(0-8)")
    project_path: str = Field(default=".", description="项目根目录路径")
    severity_filter: Literal["all", "BLOCK", "WARN"] = Field(default="all", description="严重级别过滤: all, BLOCK, WARN")
    force_refresh: bool = Field(default=False, description="强制刷新缓存，忽略文件哈希缓存")


class SpecDriftDetectInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    spec_dir: str = Field(default=".trae/specs", description="规格文档目录")
    src_dir: str = Field(default=".", description="源代码目录")


class SecurityScanInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target: str = Field(default=".", description="目标扫描目录")
    severity_threshold: Literal["critical", "high", "medium", "low"] = Field(default="medium", description="最低报告严重级别: critical, high, medium, low")
    include_agentic: bool = Field(default=True, description="是否包含OWASP Agentic Top 10检查")
    include_dependency: bool = Field(default=True, description="是否包含依赖漏洞扫描")


class CodeSimplifyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target: str = Field(description="目标文件或目录路径")
    scope: Literal["file", "dir", "recent"] = Field(default="recent", description="扫描范围: file, dir, recent")
    include_dedup: bool = Field(default=True, description="是否包含重复代码检测")


class SessionManageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["save", "load", "list", "detect", "verify", "track", "restore"] = Field(description="操作类型: save, load, list, detect, verify, track, restore")
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
    action: Literal["start", "status", "abort", "phase", "recover", "snapshots"] = Field(description="操作类型: start, status, abort, phase, recover, snapshots")
    workflow: str | None = Field(default=None, description="工作流名称(start时使用): sdd-tdd-full, sdd-tdd-medium, sdd-tdd-fast等")
    project_path: str = Field(default=".", description="项目根目录路径(start时使用)")
    workflow_id: str | None = Field(default=None, description="工作流实例ID(status/abort/phase/recover/snapshots时使用)")
    phase_action: Literal["advance", "current"] | None = Field(default=None, description="阶段操作(phase时使用): advance, current")
    snapshot_phase: int | None = Field(default=None, description="恢复到指定阶段的快照(recover时使用)")


class AgentStatusInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["list", "by_phase", "detail", "create", "match", "assign", "release", "instance_status", "destroy", "schedule"] = Field(description="操作类型: list, by_phase, detail, create, match, assign, release, instance_status, destroy, schedule")
    phase: int | None = Field(default=None, ge=0, le=8, description="按阶段查询Agent(by_phase时使用, 0-8)")
    agent_name: str | None = Field(default=None, description="Agent名称(detail时使用)")
    agent_type: str | None = Field(default=None, description="Agent类型(create时使用)，如: developer, reviewer, tester")
    capabilities: list[str] | None = Field(default=None, description="Agent能力列表(create/match时使用)，如: ['code_review', 'testing']")
    agent_id: str | None = Field(default=None, description="Agent实例ID(assign/release/instance_status/destroy时使用)")
    task: str | None = Field(default=None, description="分配的任务描述(assign时使用)")


class HookManageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["list", "execute"] = Field(description="操作类型: list, execute")
    profile: Literal["minimal", "standard", "strict"] = Field(default="standard", description="Hook配置级别: minimal, standard, strict")
    hook_name: str | None = Field(default=None, description="Hook名称(execute时使用)")
    context: dict[str, Any] | None = Field(default=None, description="执行上下文(execute时使用)")


class ResourceLoadStatusInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["status", "preload", "cache", "clear_cache", "loading_progress", "token_report"] = Field(description="操作类型: status, preload, cache, clear_cache, loading_progress, token_report")
    phase: int | None = Field(default=None, ge=0, le=3, description="目标加载阶段(0-3): 0=骨架, 1=功能, 2=增强, 3=完整")
    resource_ids: list[str] | None = Field(default=None, description="指定资源ID列表")
    resource_uris: list[str] | None = Field(default=None, description="资源URI列表(preload时使用)")
    priority: Literal["critical", "normal", "background"] = Field(default="normal", description="预加载优先级(preload时使用): critical, normal, background")
    batch_mode: bool = Field(default=False, description="是否批量预加载模式(preload时使用)，批量模式并发加载多个资源")
    auto_upgrade: bool = Field(default=False, description="自动升级阶段(preload时使用)，当Token预算超限时自动推进到下一阶段")


class ServerHealthInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["check", "negotiate_version"] = Field(default="check", description="操作类型: check, negotiate_version")
    client_version: str | None = Field(default=None, description="客户端API版本(negotiate_version时使用)")


class ContextCompressInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str = Field(description="待压缩的文本内容")
    strategy: Literal["semantic", "selective", "lossless"] = Field(default="semantic", description="压缩策略: semantic, selective, lossless")
    target_tokens: int = Field(default=2000, ge=100, le=50000, description="目标Token数量")
    preserve_sections: list[str] | None = Field(default=None, description="必须保留的章节标题列表")


class DecisionLogInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["log", "list", "query", "update", "export", "stats"] = Field(description="操作类型: log, list, query, update, export, stats")
    title: str | None = Field(default=None, description="决策标题(log时使用)")
    description: str | None = Field(default=None, description="决策描述(log时使用)")
    context: str | None = Field(default=None, description="决策上下文(log/query时使用)")
    alternatives: list[str] | None = Field(default=None, description="备选方案列表(log时使用)")
    decision: str | None = Field(default=None, description="最终决策(log时使用)")
    rationale: str | None = Field(default=None, description="决策理由(log时使用)")
    impact: str | None = Field(default=None, description="影响范围(log时使用)")
    decided_by: str | None = Field(default=None, description="决策者(log时使用)")
    keyword: str | None = Field(default=None, description="搜索关键词(query时使用)")
    tag: str | None = Field(default=None, description="标签过滤(query时使用)")
    date_from: str | None = Field(default=None, description="起始日期(ISO8601, query/export/stats时使用)")
    date_to: str | None = Field(default=None, description="截止日期(ISO8601, query/export/stats时使用)")
    limit: int = Field(default=20, ge=1, le=100, description="返回数量上限(list/query时使用)")
    offset: int = Field(default=0, ge=0, le=10000, description="偏移量(list/query时使用)")
    format: Literal["json", "markdown"] = Field(default="json", description="导出格式(export时使用): json, markdown")
    decision_id: str | None = Field(default=None, description="决策ID(update时使用)")
    status: Literal["proposed", "accepted", "deprecated", "superseded"] | None = Field(default=None, description="决策状态(log/update时使用): proposed, accepted, deprecated, superseded")


class TokenBudgetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["status", "set_budget", "recommend", "report"] = Field(description="操作类型: status, set_budget, recommend, report")
    total_budget: int | None = Field(default=None, ge=1000, description="总Token预算(set_budget时使用)")
    phase_allocations: dict[str, int] | None = Field(default=None, description="阶段分配(set_budget时使用)")
    project_size: Literal["small", "medium", "large"] | None = Field(default=None, description="项目规模(recommend时使用): small, medium, large")
    complexity: Literal["low", "medium", "high"] | None = Field(default=None, description="复杂度(recommend时使用): low, medium, high")
    team_size: int | None = Field(default=None, ge=1, le=50, description="团队人数(recommend时使用)")
    period: Literal["daily", "weekly", "session"] = Field(default="session", description="报告周期(report时使用): daily, weekly, session")


class ProjectInitInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["create", "validate", "detect_stack"] = Field(description="操作类型: create, validate, detect_stack")
    name: str | None = Field(default=None, description="项目名称(create时使用)")
    description: str | None = Field(default=None, description="项目描述(create时使用)")
    stack: list[str] | None = Field(default=None, description="技术栈列表(create时使用)")
    template: str | None = Field(default=None, description="项目模板(create时使用)")
    directory: str | None = Field(default=None, description="项目目录(create时使用)")
    project_path: str | None = Field(default=None, description="项目路径(validate/detect_stack时使用)")


class KnowledgeInjectInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["inject", "list_available", "precipitate"] = Field(default="inject", description="操作类型: inject, list_available, precipitate")
    topics: list[str] | None = Field(default=None, description="知识主题列表(inject时使用)")
    scope: Literal["general", "workspace", "experience"] = Field(default="general", description="知识范围: general, workspace, experience")
    max_tokens: int = Field(default=5000, ge=100, le=50000, description="最大注入Token数量(inject时使用)")
    relevance_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="相关性阈值(inject时使用)")
    category: str | None = Field(default=None, description="经验分类(precipitate时使用)")
    title: str | None = Field(default=None, description="经验标题(precipitate时使用)")
    content: str | None = Field(default=None, description="经验内容(precipitate时使用)")
    tags: list[str] | None = Field(default=None, description="标签列表(precipitate时使用)")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="置信度(precipitate时使用)")
