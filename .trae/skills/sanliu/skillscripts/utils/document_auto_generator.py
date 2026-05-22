#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档自动生成器 - Sanliu 技能

功能：
1. 演化报告自动生成 - 日报、周报、月报生成，支持多种输出格式
2. API文档自动生成 - 从代码提取API信息，支持OpenAPI/Swagger格式
3. 知识库文档生成 - 知识条目文档化，支持知识图谱可视化
4. 变更日志自动生成 - 从Git历史生成变更日志，支持语义化版本

使用方法：
    from document_auto_generator import (
        EvolutionReportGenerator,
        APIDocGenerator,
        KnowledgeDocGenerator,
        ChangelogGenerator
    )
    
    # 演化报告生成
    report_gen = EvolutionReportGenerator()
    report = report_gen.generate_daily_report()
    report_gen.save_report(report, format="html")
    
    # API文档生成
    api_gen = APIDocGenerator()
    api_doc = api_gen.generate_from_code("src/api/")
    api_gen.export_openapi(api_doc, "openapi.json")
    
    # 知识库文档生成
    kb_gen = KnowledgeDocGenerator()
    kb_doc = kb_gen.generate_knowledge_doc(knowledge_items)
    kb_gen.export_with_graph(kb_doc, "knowledge.html")
    
    # 变更日志生成
    changelog_gen = ChangelogGenerator()
    changelog = changelog_gen.generate_from_git()
    changelog_gen.save_changelog(changelog, "CHANGELOG.md")
"""

import ast
import json
import logging
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from path_config_manager import PathConfigManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ReportFormat(Enum):
    """报告输出格式枚举"""
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"


class ReportPeriod(Enum):
    """报告周期枚举"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ChangeCategory(Enum):
    """变更类别枚举"""
    ADDED = "added"
    CHANGED = "changed"
    DEPRECATED = "deprecated"
    REMOVED = "removed"
    FIXED = "fixed"
    SECURITY = "security"


class APIType(Enum):
    """API类型枚举"""
    REST = "rest"
    GRAPHQL = "graphql"
    GRPC = "grpc"
    WEBSOCKET = "websocket"


class KnowledgeType(Enum):
    """知识类型枚举"""
    CONCEPT = "concept"
    PATTERN = "pattern"
    BEST_PRACTICE = "best_practice"
    ANTI_PATTERN = "anti_pattern"
    SOLUTION = "solution"
    FAQ = "faq"


@dataclass
class ReportTemplate:
    """报告模板数据类"""
    template_id: str
    name: str
    description: str
    sections: List[Dict[str, Any]]
    format_hints: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReportSection:
    """报告章节"""
    title: str
    content: str
    order: int
    subsections: List['ReportSection'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "order": self.order,
            "subsections": [s.to_dict() for s in self.subsections],
            "metadata": self.metadata
        }


@dataclass
class EvolutionMetrics:
    """演化指标数据类"""
    total_changes: int = 0
    successful_changes: int = 0
    failed_changes: int = 0
    rollback_count: int = 0
    avg_duration_ms: float = 0.0
    coverage_before: float = 0.0
    coverage_after: float = 0.0
    quality_score_before: float = 0.0
    quality_score_after: float = 0.0
    issues_found: int = 0
    issues_fixed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def success_rate(self) -> float:
        if self.total_changes == 0:
            return 0.0
        return round((self.successful_changes / self.total_changes) * 100, 2)

    @property
    def coverage_improvement(self) -> float:
        return round(self.coverage_after - self.coverage_before, 2)

    @property
    def quality_improvement(self) -> float:
        return round(self.quality_score_after - self.quality_score_before, 2)


@dataclass
class APIEndpoint:
    """API端点数据类"""
    path: str
    method: str
    description: str = ""
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    deprecated: bool = False
    version_added: str = ""
    version_deprecated: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class APISchema:
    """API模式数据类"""
    api_type: APIType
    title: str
    version: str
    description: str = ""
    endpoints: List[APIEndpoint] = field(default_factory=list)
    models: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    base_url: str = ""
    auth_schemes: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "api_type": self.api_type.value,
            "title": self.title,
            "version": self.version,
            "description": self.description,
            "endpoints": [e.to_dict() for e in self.endpoints],
            "models": self.models,
            "base_url": self.base_url,
            "auth_schemes": self.auth_schemes
        }


@dataclass
class APIChange:
    """API变更数据类"""
    endpoint_path: str
    method: str
    change_type: ChangeCategory
    description: str
    version: str
    timestamp: str
    breaking: bool = False
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KnowledgeItem:
    """知识条目数据类"""
    item_id: str
    title: str
    knowledge_type: KnowledgeType
    content: str
    tags: List[str] = field(default_factory=list)
    related_items: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KnowledgeGraph:
    """知识图谱数据类"""
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    clusters: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KnowledgeIndex:
    """知识索引数据类"""
    categories: Dict[str, List[str]] = field(default_factory=dict)
    tag_index: Dict[str, List[str]] = field(default_factory=dict)
    search_index: Dict[str, List[str]] = field(default_factory=dict)
    last_updated: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ChangelogEntry:
    """变更日志条目数据类"""
    version: str
    release_date: str
    changes: Dict[ChangeCategory, List[Dict[str, Any]]] = field(default_factory=dict)
    breaking_changes: List[str] = field(default_factory=list)
    migration_guide: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "release_date": self.release_date,
            "changes": {k.value: v for k, v in self.changes.items()},
            "breaking_changes": self.breaking_changes,
            "migration_guide": self.migration_guide
        }


@dataclass
class GitCommit:
    """Git提交数据类"""
    commit_hash: str
    author: str
    date: str
    message: str
    files_changed: List[str] = field(default_factory=list)
    additions: int = 0
    deletions: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EvolutionReportGenerator:
    """
    演化报告自动生成器
    
    功能：
    - 生成日报、周报、月报
    - 支持报告模板
    - 支持多种输出格式（Markdown、HTML、JSON）
    - 与path_config_manager集成
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        初始化演化报告生成器
        
        Args:
            project_root: 项目根目录，默认使用PathConfigManager自动检测
        """
        self.path_manager = PathConfigManager(auto_detect=True) if project_root is None else None
        self.project_root = project_root or (self.path_manager.get_base_path() if self.path_manager else Path.cwd())
        self.reports_dir = self.project_root / "reports" / "evolution"
        self.templates_dir = self.project_root / "templates" / "reports"
        self.history_file = self.reports_dir / "evolution_history.json"
        
        self._ensure_directories()
        self.templates: Dict[str, ReportTemplate] = {}
        self.history: List[Dict[str, Any]] = []
        self._load_templates()
        self._load_history()
        
        logger.info(f"演化报告生成器初始化完成，项目根目录: {self.project_root}")
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_templates(self):
        """加载报告模板"""
        default_templates = self._get_default_templates()
        for template in default_templates:
            self.templates[template.template_id] = template
        
        template_files = list(self.templates_dir.glob("*.json"))
        for tf in template_files:
            try:
                with open(tf, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                template = ReportTemplate(**data)
                self.templates[template.template_id] = template
            except Exception as e:
                logger.warning(f"加载模板失败 {tf}: {e}")
    
    def _get_default_templates(self) -> List[ReportTemplate]:
        """获取默认报告模板"""
        return [
            ReportTemplate(
                template_id="daily_standard",
                name="标准日报模板",
                description="每日演化报告标准模板",
                sections=[
                    {"title": "概述", "type": "summary", "order": 1},
                    {"title": "演化统计", "type": "statistics", "order": 2},
                    {"title": "问题分析", "type": "issues", "order": 3},
                    {"title": "修复效果", "type": "fixes", "order": 4},
                    {"title": "建议", "type": "recommendations", "order": 5}
                ]
            ),
            ReportTemplate(
                template_id="weekly_standard",
                name="标准周报模板",
                description="每周演化报告标准模板",
                sections=[
                    {"title": "周概述", "type": "summary", "order": 1},
                    {"title": "演化趋势", "type": "trends", "order": 2},
                    {"title": "统计汇总", "type": "statistics", "order": 3},
                    {"title": "问题分析", "type": "issues", "order": 4},
                    {"title": "学习成果", "type": "learning", "order": 5},
                    {"title": "下周计划", "type": "planning", "order": 6}
                ]
            ),
            ReportTemplate(
                template_id="monthly_standard",
                name="标准月报模板",
                description="每月演化报告标准模板",
                sections=[
                    {"title": "月度概述", "type": "summary", "order": 1},
                    {"title": "整体趋势", "type": "trends", "order": 2},
                    {"title": "详细统计", "type": "statistics", "order": 3},
                    {"title": "问题深度分析", "type": "issues", "order": 4},
                    {"title": "知识积累", "type": "knowledge", "order": 5},
                    {"title": "改进建议", "type": "recommendations", "order": 6},
                    {"title": "下月规划", "type": "planning", "order": 7}
                ]
            )
        ]
    
    def _load_history(self):
        """加载演化历史"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history = data.get("records", [])
            except Exception as e:
                logger.warning(f"加载演化历史失败: {e}")
                self.history = []
    
    def _save_history(self):
        """保存演化历史"""
        data = {
            "records": self.history,
            "last_updated": datetime.now().isoformat(),
            "total_records": len(self.history)
        }
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def record_evolution(
        self,
        evolution_type: str,
        metrics: EvolutionMetrics,
        details: Dict[str, Any] = None
    ) -> str:
        """
        记录一次演化
        
        Args:
            evolution_type: 演化类型
            metrics: 演化指标
            details: 详细信息
            
        Returns:
            演化记录ID
        """
        record_id = f"EVO-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(self.history):04d}"
        
        record = {
            "record_id": record_id,
            "timestamp": datetime.now().isoformat(),
            "evolution_type": evolution_type,
            "metrics": metrics.to_dict(),
            "details": details or {}
        }
        
        self.history.append(record)
        self._save_history()
        
        logger.info(f"记录演化: {record_id}")
        return record_id
    
    def generate_report(
        self,
        period: ReportPeriod,
        template_id: str = None,
        custom_data: Dict[str, Any] = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """
        生成演化报告
        
        Args:
            period: 报告周期
            template_id: 模板ID
            custom_data: 自定义数据
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            报告数据字典
        """
        end_date = end_date or datetime.now()
        
        if period == ReportPeriod.DAILY:
            start_date = start_date or end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == ReportPeriod.WEEKLY:
            start_date = start_date or (end_date - timedelta(days=7))
        elif period == ReportPeriod.MONTHLY:
            start_date = start_date or (end_date - timedelta(days=30))
        elif period == ReportPeriod.QUARTERLY:
            start_date = start_date or (end_date - timedelta(days=90))
        else:
            start_date = start_date or (end_date - timedelta(days=365))
        
        template = self.templates.get(template_id or f"{period.value}_standard")
        if not template:
            template = self.templates.get("daily_standard")
        
        records = self._get_records_in_period(start_date, end_date)
        metrics = self._aggregate_metrics(records)
        sections = self._build_sections(template, records, metrics, custom_data)
        
        report = {
            "report_id": f"RPT-{period.value.upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "period": period.value,
            "generated_at": datetime.now().isoformat(),
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "template": template.template_id if template else "default",
            "sections": [s.to_dict() for s in sections],
            "metrics": metrics.to_dict(),
            "summary": self._generate_summary(metrics, period),
            "recommendations": self._generate_recommendations(metrics, records)
        }
        
        return report
    
    def generate_daily_report(self, date: datetime = None) -> Dict[str, Any]:
        """生成日报"""
        target_date = date or datetime.now()
        return self.generate_report(ReportPeriod.DAILY, start_date=target_date, end_date=target_date)
    
    def generate_weekly_report(self, end_date: datetime = None) -> Dict[str, Any]:
        """生成周报"""
        return self.generate_report(ReportPeriod.WEEKLY, end_date=end_date)
    
    def generate_monthly_report(self, end_date: datetime = None) -> Dict[str, Any]:
        """生成月报"""
        return self.generate_report(ReportPeriod.MONTHLY, end_date=end_date)
    
    def _get_records_in_period(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """获取指定时间范围内的记录"""
        records = []
        for record in self.history:
            try:
                record_time = datetime.fromisoformat(record["timestamp"])
                if start_date <= record_time <= end_date:
                    records.append(record)
            except Exception:
                continue
        return records
    
    def _aggregate_metrics(self, records: List[Dict[str, Any]]) -> EvolutionMetrics:
        """聚合演化指标"""
        if not records:
            return EvolutionMetrics()
        
        total = len(records)
        successful = sum(1 for r in records if r.get("metrics", {}).get("successful_changes", 0) > 0)
        failed = sum(1 for r in records if r.get("metrics", {}).get("failed_changes", 0) > 0)
        
        metrics_list = [r.get("metrics", {}) for r in records]
        
        return EvolutionMetrics(
            total_changes=total,
            successful_changes=successful,
            failed_changes=failed,
            rollback_count=sum(m.get("rollback_count", 0) for m in metrics_list),
            avg_duration_ms=sum(m.get("avg_duration_ms", 0) for m in metrics_list) / total if total > 0 else 0,
            coverage_before=sum(m.get("coverage_before", 0) for m in metrics_list) / total if total > 0 else 0,
            coverage_after=sum(m.get("coverage_after", 0) for m in metrics_list) / total if total > 0 else 0,
            quality_score_before=sum(m.get("quality_score_before", 0) for m in metrics_list) / total if total > 0 else 0,
            quality_score_after=sum(m.get("quality_score_after", 0) for m in metrics_list) / total if total > 0 else 0,
            issues_found=sum(m.get("issues_found", 0) for m in metrics_list),
            issues_fixed=sum(m.get("issues_fixed", 0) for m in metrics_list)
        )
    
    def _build_sections(
        self,
        template: ReportTemplate,
        records: List[Dict[str, Any]],
        metrics: EvolutionMetrics,
        custom_data: Dict[str, Any] = None
    ) -> List[ReportSection]:
        """构建报告章节"""
        sections = []
        
        for section_def in template.sections:
            section = self._build_section(section_def, records, metrics, custom_data)
            sections.append(section)
        
        return sorted(sections, key=lambda s: s.order)
    
    def _build_section(
        self,
        section_def: Dict[str, Any],
        records: List[Dict[str, Any]],
        metrics: EvolutionMetrics,
        custom_data: Dict[str, Any] = None
    ) -> ReportSection:
        """构建单个章节"""
        section_type = section_def.get("type", "custom")
        title = section_def.get("title", "")
        order = section_def.get("order", 0)
        
        content_map = {
            "summary": self._build_summary_content(metrics, records),
            "statistics": self._build_statistics_content(metrics),
            "issues": self._build_issues_content(records),
            "fixes": self._build_fixes_content(records),
            "trends": self._build_trends_content(records),
            "learning": self._build_learning_content(records),
            "knowledge": self._build_knowledge_content(records),
            "recommendations": self._build_recommendations_content(metrics, records),
            "planning": self._build_planning_content(metrics)
        }
        
        content = content_map.get(section_type, "")
        
        if custom_data and section_type == "custom":
            content = custom_data.get("content", "")
        
        return ReportSection(
            title=title,
            content=content,
            order=order
        )
    
    def _build_summary_content(self, metrics: EvolutionMetrics, records: List[Dict[str, Any]]) -> str:
        """构建概述内容"""
        return f"""
本周期内共执行 {metrics.total_changes} 次演化操作：
- 成功: {metrics.successful_changes} 次 ({metrics.success_rate}%)
- 失败: {metrics.failed_changes} 次
- 回滚: {metrics.rollback_count} 次

覆盖率变化: {metrics.coverage_before}% → {metrics.coverage_after}% ({metrics.coverage_improvement:+.2f}%)
质量分数变化: {metrics.quality_score_before} → {metrics.quality_score_after} ({metrics.quality_improvement:+.2f})
"""
    
    def _build_statistics_content(self, metrics: EvolutionMetrics) -> str:
        """构建统计内容"""
        return f"""
| 指标 | 数值 |
|------|------|
| 总演化次数 | {metrics.total_changes} |
| 成功次数 | {metrics.successful_changes} |
| 失败次数 | {metrics.failed_changes} |
| 成功率 | {metrics.success_rate}% |
| 平均耗时 | {metrics.avg_duration_ms:.2f}ms |
| 发现问题 | {metrics.issues_found} |
| 修复问题 | {metrics.issues_fixed} |
"""
    
    def _build_issues_content(self, records: List[Dict[str, Any]]) -> str:
        """构建问题分析内容"""
        issue_types: Dict[str, int] = defaultdict(int)
        
        for record in records:
            details = record.get("details", {})
            issues = details.get("issues", [])
            for issue in issues:
                issue_type = issue.get("type", "unknown")
                issue_types[issue_type] += 1
        
        if not issue_types:
            return "本周期内无重大问题记录。"
        
        lines = ["| 问题类型 | 数量 |", "|----------|------|"]
        for issue_type, count in sorted(issue_types.items(), key=lambda x: -x[1]):
            lines.append(f"| {issue_type} | {count} |")
        
        return "\n".join(lines)
    
    def _build_fixes_content(self, records: List[Dict[str, Any]]) -> str:
        """构建修复效果内容"""
        total_fixes = 0
        successful_fixes = 0
        side_effects = 0
        
        for record in records:
            details = record.get("details", {})
            fixes = details.get("fixes", [])
            total_fixes += len(fixes)
            successful_fixes += sum(1 for f in fixes if f.get("success", False))
            side_effects += len(details.get("side_effects", []))
        
        fix_rate = (successful_fixes / total_fixes * 100) if total_fixes > 0 else 0
        
        return f"""
| 指标 | 数值 |
|------|------|
| 总修复数 | {total_fixes} |
| 成功修复 | {successful_fixes} |
| 修复成功率 | {fix_rate:.2f}% |
| 副作用数量 | {side_effects} |
"""
    
    def _build_trends_content(self, records: List[Dict[str, Any]]) -> str:
        """构建趋势分析内容"""
        if len(records) < 2:
            return "数据不足，无法进行趋势分析。"
        
        sorted_records = sorted(records, key=lambda r: r["timestamp"])
        
        mid = len(sorted_records) // 2
        first_half = sorted_records[:mid]
        second_half = sorted_records[mid:]
        
        first_metrics = self._aggregate_metrics(first_half)
        second_metrics = self._aggregate_metrics(second_half)
        
        coverage_trend = second_metrics.coverage_after - first_metrics.coverage_after
        quality_trend = second_metrics.quality_score_after - first_metrics.quality_score_after
        
        return f"""
| 指标 | 前半周期 | 后半周期 | 变化 |
|------|----------|----------|------|
| 覆盖率 | {first_metrics.coverage_after:.2f}% | {second_metrics.coverage_after:.2f}% | {coverage_trend:+.2f}% |
| 质量分数 | {first_metrics.quality_score_after:.2f} | {second_metrics.quality_score_after:.2f} | {quality_trend:+.2f} |
| 成功率 | {first_metrics.success_rate}% | {second_metrics.success_rate}% | {second_metrics.success_rate - first_metrics.success_rate:+.2f}% |
"""
    
    def _build_learning_content(self, records: List[Dict[str, Any]]) -> str:
        """构建学习成果内容"""
        patterns_learned = []
        knowledge_updates = []
        
        for record in records:
            details = record.get("details", {})
            patterns_learned.extend(details.get("patterns_learned", []))
            knowledge_updates.extend(details.get("knowledge_updates", []))
        
        content = "### 学习新模式\n\n"
        if patterns_learned:
            for pattern in patterns_learned[:10]:
                content += f"- {pattern}\n"
        else:
            content += "本周期无新模式学习记录。\n"
        
        content += "\n### 知识库更新\n\n"
        if knowledge_updates:
            for update in knowledge_updates[:10]:
                content += f"- {update}\n"
        else:
            content += "本周期无知识库更新记录。\n"
        
        return content
    
    def _build_knowledge_content(self, records: List[Dict[str, Any]]) -> str:
        """构建知识积累内容"""
        return self._build_learning_content(records)
    
    def _build_recommendations_content(self, metrics: EvolutionMetrics, records: List[Dict[str, Any]]) -> str:
        """构建建议内容"""
        recommendations = self._generate_recommendations(metrics, records)
        
        content = ""
        for i, rec in enumerate(recommendations, 1):
            content += f"{i}. {rec}\n"
        
        return content
    
    def _build_planning_content(self, metrics: EvolutionMetrics) -> str:
        """构建规划内容"""
        plans = []
        
        if metrics.success_rate < 80:
            plans.append("提高演化成功率，优化演化策略")
        
        if metrics.coverage_improvement < 0:
            plans.append("增加测试覆盖率，补充缺失的测试用例")
        
        if metrics.quality_improvement < 0:
            plans.append("提升代码质量，进行代码审查和重构")
        
        if metrics.rollback_count > 0:
            plans.append("减少回滚次数，增强演化验证机制")
        
        if not plans:
            plans.append("保持当前演化策略，持续监控关键指标")
        
        content = "### 下周期计划\n\n"
        for i, plan in enumerate(plans, 1):
            content += f"{i}. {plan}\n"
        
        return content
    
    def _generate_summary(self, metrics: EvolutionMetrics, period: ReportPeriod) -> str:
        """生成报告摘要"""
        period_names = {
            ReportPeriod.DAILY: "日报",
            ReportPeriod.WEEKLY: "周报",
            ReportPeriod.MONTHLY: "月报",
            ReportPeriod.QUARTERLY: "季报",
            ReportPeriod.YEARLY: "年报"
        }
        
        return f"【{period_names.get(period, '报告')}摘要】共执行{metrics.total_changes}次演化，成功率{metrics.success_rate}%，覆盖率变化{metrics.coverage_improvement:+.2f}%。"
    
    def _generate_recommendations(self, metrics: EvolutionMetrics, records: List[Dict[str, Any]]) -> List[str]:
        """生成建议列表"""
        recommendations = []
        
        if metrics.success_rate < 80:
            recommendations.append(f"演化成功率较低({metrics.success_rate}%)，建议检查演化策略和测试覆盖率")
        
        if metrics.avg_duration_ms > 10000:
            recommendations.append(f"平均演化耗时较长({metrics.avg_duration_ms:.0f}ms)，建议优化演化流程")
        
        if metrics.rollback_count > 0:
            recommendations.append(f"发生{metrics.rollback_count}次回滚，建议改进演化验证流程")
        
        fix_rate = (metrics.issues_fixed / metrics.issues_found * 100) if metrics.issues_found > 0 else 100
        if fix_rate < 70:
            recommendations.append(f"问题修复率较低({fix_rate:.1f}%)，建议增强自动修复能力")
        
        if metrics.coverage_improvement < 0:
            recommendations.append("覆盖率呈下降趋势，建议补充测试用例")
        
        if not recommendations:
            recommendations.append("演化状态良好，继续保持当前策略")
        
        return recommendations
    
    def save_report(
        self,
        report: Dict[str, Any],
        format: ReportFormat = ReportFormat.JSON,
        output_path: Path = None
    ) -> Path:
        """
        保存报告
        
        Args:
            report: 报告数据
            format: 输出格式
            output_path: 输出路径
            
        Returns:
            保存的文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        period = report.get("period", "unknown")
        
        if format == ReportFormat.JSON:
            return self._save_json_report(report, output_path, timestamp, period)
        elif format == ReportFormat.MARKDOWN:
            return self._save_markdown_report(report, output_path, timestamp, period)
        elif format == ReportFormat.HTML:
            return self._save_html_report(report, output_path, timestamp, period)
        else:
            return self._save_json_report(report, output_path, timestamp, period)
    
    def _save_json_report(
        self,
        report: Dict[str, Any],
        output_path: Path,
        timestamp: str,
        period: str
    ) -> Path:
        output_path = output_path or self.reports_dir / f"evolution_report_{period}_{timestamp}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        latest_path = output_path.parent / f"latest_{period}_report.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"报告已保存: {output_path}")
        return output_path
    
    def _save_markdown_report(
        self,
        report: Dict[str, Any],
        output_path: Path,
        timestamp: str,
        period: str
    ) -> Path:
        output_path = output_path or self.reports_dir / f"evolution_report_{period}_{timestamp}.md"
        
        content = self._generate_markdown_content(report)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"报告已保存: {output_path}")
        return output_path
    
    def _generate_markdown_content(self, report: Dict[str, Any]) -> str:
        """生成Markdown格式内容"""
        lines = [
            f"# 演化报告 - {report['period'].upper()}",
            "",
            f"**报告ID**: {report['report_id']}",
            f"**生成时间**: {report['generated_at']}",
            f"**统计周期**: {report['period_start']} ~ {report['period_end']}",
            "",
            "## 摘要",
            "",
            report['summary'],
            ""
        ]
        
        for section in report.get('sections', []):
            lines.append(f"## {section['title']}")
            lines.append("")
            lines.append(section['content'])
            lines.append("")
        
        lines.extend([
            "## 建议",
            ""
        ])
        for i, rec in enumerate(report.get('recommendations', []), 1):
            lines.append(f"{i}. {rec}")
        
        return "\n".join(lines)
    
    def _save_html_report(
        self,
        report: Dict[str, Any],
        output_path: Path,
        timestamp: str,
        period: str
    ) -> Path:
        output_path = output_path or self.reports_dir / f"evolution_report_{period}_{timestamp}.html"
        
        content = self._generate_html_content(report)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"报告已保存: {output_path}")
        return output_path
    
    def _generate_html_content(self, report: Dict[str, Any]) -> str:
        """生成HTML格式内容"""
        metrics = report.get('metrics', {})
        
        sections_html = ""
        for section in report.get('sections', []):
            sections_html += f"""
        <div class="card">
            <h2>{section['title']}</h2>
            <div class="content">{section['content']}</div>
        </div>
"""
        
        recommendations_html = ""
        for rec in report.get('recommendations', []):
            recommendations_html += f"<li>{rec}</li>"
        
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>演化报告 - {report['period'].upper()}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .summary {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }}
        .stat-card {{ background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
        .stat-card h3 {{ color: #666; font-size: 14px; margin-bottom: 10px; }}
        .stat-card .value {{ font-size: 28px; font-weight: bold; color: #333; }}
        .card {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .card h2 {{ color: #333; margin-bottom: 15px; font-size: 18px; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        .content {{ white-space: pre-wrap; font-size: 14px; line-height: 1.6; }}
        .recommendations {{ background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 15px; margin-top: 15px; }}
        .recommendations h3 {{ color: #1e40af; margin-bottom: 10px; }}
        .recommendations ul {{ list-style: none; }}
        .recommendations li {{ padding: 5px 0; padding-left: 20px; position: relative; }}
        .recommendations li::before {{ content: "→"; position: absolute; left: 0; color: #3b82f6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 演化报告 - {report['period'].upper()}</h1>
            <p>报告ID: {report['report_id']} | 生成时间: {report['generated_at']}</p>
            <p>统计周期: {report['period_start']} ~ {report['period_end']}</p>
        </div>
        
        <div class="summary">
            <h2>摘要</h2>
            <p>{report['summary']}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>总演化次数</h3>
                <div class="value">{metrics.get('total_changes', 0)}</div>
            </div>
            <div class="stat-card">
                <h3>成功率</h3>
                <div class="value">{metrics.get('success_rate', 0)}%</div>
            </div>
            <div class="stat-card">
                <h3>覆盖率变化</h3>
                <div class="value">{metrics.get('coverage_improvement', 0):+.2f}%</div>
            </div>
            <div class="stat-card">
                <h3>质量分数变化</h3>
                <div class="value">{metrics.get('quality_improvement', 0):+.2f}</div>
            </div>
        </div>
        
        {sections_html}
        
        <div class="recommendations">
            <h3>建议</h3>
            <ul>
                {recommendations_html}
            </ul>
        </div>
    </div>
</body>
</html>"""


class APIDocGenerator:
    """
    API文档自动生成器
    
    功能：
    - 从代码提取API信息
    - 支持OpenAPI/Swagger格式
    - 支持API变更追踪
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        初始化API文档生成器
        
        Args:
            project_root: 项目根目录
        """
        self.path_manager = PathConfigManager(auto_detect=True) if project_root is None else None
        self.project_root = project_root or (self.path_manager.get_base_path() if self.path_manager else Path.cwd())
        self.output_dir = self.project_root / "docs" / "api"
        self.changes_dir = self.output_dir / "changes"
        self.changes_file = self.changes_dir / "api_changes.json"
        
        self._ensure_directories()
        self.api_changes: List[APIChange] = []
        self._load_changes()
        
        logger.info(f"API文档生成器初始化完成，项目根目录: {self.project_root}")
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.changes_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_changes(self):
        """加载API变更历史"""
        if self.changes_file.exists():
            try:
                with open(self.changes_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for change_data in data.get("changes", []):
                        change_data["change_type"] = ChangeCategory(change_data["change_type"])
                        self.api_changes.append(APIChange(**change_data))
            except Exception as e:
                logger.warning(f"加载API变更历史失败: {e}")
    
    def _save_changes(self):
        """保存API变更历史"""
        data = {
            "changes": [c.to_dict() for c in self.api_changes],
            "last_updated": datetime.now().isoformat()
        }
        with open(self.changes_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def generate_from_code(
        self,
        source_path: Path,
        api_type: APIType = APIType.REST,
        base_url: str = ""
    ) -> APISchema:
        """
        从代码生成API文档
        
        Args:
            source_path: 源代码路径
            api_type: API类型
            base_url: 基础URL
            
        Returns:
            API模式对象
        """
        endpoints: List[APIEndpoint] = []
        models: Dict[str, Dict[str, Any]] = {}
        
        source_path = Path(source_path)
        
        if source_path.is_file() and source_path.suffix == '.py':
            file_endpoints, file_models = self._parse_python_file(source_path)
            endpoints.extend(file_endpoints)
            models.update(file_models)
        elif source_path.is_dir():
            for py_file in source_path.rglob("*.py"):
                try:
                    file_endpoints, file_models = self._parse_python_file(py_file)
                    endpoints.extend(file_endpoints)
                    models.update(file_models)
                except Exception as e:
                    logger.warning(f"解析文件失败 {py_file}: {e}")
        
        schema = APISchema(
            api_type=api_type,
            title="API Documentation",
            version="1.0.0",
            description=f"自动生成的API文档，共{len(endpoints)}个端点",
            endpoints=endpoints,
            models=models,
            base_url=base_url
        )
        
        return schema
    
    def _parse_python_file(self, file_path: Path) -> Tuple[List[APIEndpoint], Dict[str, Dict[str, Any]]]:
        """解析Python文件提取API信息"""
        endpoints: List[APIEndpoint] = []
        models: Dict[str, Dict[str, Any]] = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    endpoint = self._extract_endpoint_from_function(node, file_path)
                    if endpoint:
                        endpoints.append(endpoint)
                
                if isinstance(node, ast.ClassDef):
                    model = self._extract_model_from_class(node)
                    if model:
                        models[node.name] = model
        
        except Exception as e:
            logger.warning(f"解析Python文件失败 {file_path}: {e}")
        
        return endpoints, models
    
    def _extract_endpoint_from_function(self, node: ast.FunctionDef, file_path: Path) -> Optional[APIEndpoint]:
        """从函数定义提取API端点信息"""
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                decorators.append(decorator.attr)
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    decorators.append(decorator.func.id)
                elif isinstance(decorator.func, ast.Attribute):
                    decorators.append(decorator.func.attr)
        
        route_decorators = ['route', 'get', 'post', 'put', 'delete', 'patch', 'head', 'options']
        http_methods = ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']
        
        route_path = ""
        method = "GET"
        
        for decorator in decorators:
            dec_lower = decorator.lower()
            if dec_lower in http_methods:
                method = dec_lower.upper()
            if dec_lower in route_decorators:
                route_path = f"/{node.name}"
        
        if not route_path:
            return None
        
        docstring = ast.get_docstring(node) or ""
        
        parameters = []
        for arg in node.args.args:
            if arg.arg != 'self':
                param_type = "string"
                if arg.annotation:
                    if isinstance(arg.annotation, ast.Name):
                        param_type = arg.annotation.id
                    elif isinstance(arg.annotation, ast.Constant):
                        param_type = str(arg.annotation.value)
                
                parameters.append({
                    "name": arg.arg,
                    "in": "query",
                    "required": True,
                    "type": param_type
                })
        
        return APIEndpoint(
            path=route_path,
            method=method,
            description=docstring.split('\n')[0] if docstring else f"{method} {route_path}",
            parameters=parameters,
            responses={
                "200": {"description": "成功响应"},
                "400": {"description": "请求参数错误"},
                "500": {"description": "服务器内部错误"}
            }
        )
    
    def _extract_model_from_class(self, node: ast.ClassDef) -> Optional[Dict[str, Any]]:
        """从类定义提取数据模型信息"""
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
        
        model_bases = ['BaseModel', 'Model', 'Schema', 'Dataclass']
        if not any(bc in base_classes for bc in model_bases):
            return None
        
        properties = {}
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                prop_name = item.target.id
                prop_type = "string"
                if item.annotation:
                    if isinstance(item.annotation, ast.Name):
                        prop_type = item.annotation.id
                    elif isinstance(item.annotation, ast.Constant):
                        prop_type = str(item.annotation.value)
                
                properties[prop_name] = {"type": prop_type}
        
        docstring = ast.get_docstring(node) or ""
        
        return {
            "type": "object",
            "properties": properties,
            "description": docstring.split('\n')[0] if docstring else f"数据模型: {node.name}"
        }
    
    def export_openapi(
        self,
        schema: APISchema,
        output_path: Path = None,
        version: str = "3.0.0"
    ) -> Path:
        """
        导出OpenAPI/Swagger格式文档
        
        Args:
            schema: API模式
            output_path: 输出路径
            version: OpenAPI版本
            
        Returns:
            输出文件路径
        """
        output_path = output_path or self.output_dir / "openapi.json"
        
        openapi_doc = {
            "openapi": version,
            "info": {
                "title": schema.title,
                "version": schema.version,
                "description": schema.description
            },
            "servers": [{"url": schema.base_url}] if schema.base_url else [],
            "paths": {},
            "components": {
                "schemas": schema.models,
                "securitySchemes": {s["name"]: s for s in schema.auth_schemes} if schema.auth_schemes else {}
            }
        }
        
        for endpoint in schema.endpoints:
            path = endpoint.path
            method = endpoint.method.lower()
            
            if path not in openapi_doc["paths"]:
                openapi_doc["paths"][path] = {}
            
            openapi_doc["paths"][path][method] = {
                "summary": endpoint.description,
                "deprecated": endpoint.deprecated,
                "parameters": endpoint.parameters,
                "requestBody": endpoint.request_body,
                "responses": endpoint.responses,
                "tags": endpoint.tags
            }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(openapi_doc, f, indent=2, ensure_ascii=False)
        
        logger.info(f"OpenAPI文档已导出: {output_path}")
        return output_path
    
    def track_change(
        self,
        endpoint_path: str,
        method: str,
        change_type: ChangeCategory,
        description: str,
        version: str,
        breaking: bool = False,
        details: Dict[str, Any] = None
    ) -> APIChange:
        """
        追踪API变更
        
        Args:
            endpoint_path: 端点路径
            method: HTTP方法
            change_type: 变更类型
            description: 变更描述
            version: 版本号
            breaking: 是否为破坏性变更
            details: 详细信息
            
        Returns:
            API变更对象
        """
        change = APIChange(
            endpoint_path=endpoint_path,
            method=method,
            change_type=change_type,
            description=description,
            version=version,
            timestamp=datetime.now().isoformat(),
            breaking=breaking,
            details=details or {}
        )
        
        self.api_changes.append(change)
        self._save_changes()
        
        logger.info(f"记录API变更: {method} {endpoint_path} - {change_type.value}")
        return change
    
    def get_changes_for_version(self, version: str) -> List[APIChange]:
        """获取指定版本的API变更"""
        return [c for c in self.api_changes if c.version == version]
    
    def get_breaking_changes(self) -> List[APIChange]:
        """获取所有破坏性变更"""
        return [c for c in self.api_changes if c.breaking]
    
    def generate_change_report(self, version: str = None) -> Dict[str, Any]:
        """生成API变更报告"""
        changes = self.get_changes_for_version(version) if version else self.api_changes
        
        by_type: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for change in changes:
            by_type[change.change_type.value].append(change.to_dict())
        
        return {
            "version": version or "all",
            "generated_at": datetime.now().isoformat(),
            "total_changes": len(changes),
            "breaking_changes": len(self.get_breaking_changes()),
            "changes_by_type": dict(by_type)
        }


class KnowledgeDocGenerator:
    """
    知识库文档生成器
    
    功能：
    - 知识条目文档化
    - 支持知识图谱可视化
    - 支持知识索引生成
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        初始化知识库文档生成器
        
        Args:
            project_root: 项目根目录
        """
        self.path_manager = PathConfigManager(auto_detect=True) if project_root is None else None
        self.project_root = project_root or (self.path_manager.get_base_path() if self.path_manager else Path.cwd())
        self.output_dir = self.project_root / "docs" / "knowledge"
        self.index_file = self.output_dir / "knowledge_index.json"
        self.graph_file = self.output_dir / "knowledge_graph.json"
        
        self._ensure_directories()
        self.knowledge_items: Dict[str, KnowledgeItem] = {}
        self.index: KnowledgeIndex = KnowledgeIndex()
        self.graph: KnowledgeGraph = KnowledgeGraph()
        
        self._load_index()
        
        logger.info(f"知识库文档生成器初始化完成，项目根目录: {self.project_root}")
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_index(self):
        """加载知识索引"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.index = KnowledgeIndex(
                        categories=data.get("categories", {}),
                        tag_index=data.get("tag_index", {}),
                        search_index=data.get("search_index", {}),
                        last_updated=data.get("last_updated", "")
                    )
            except Exception as e:
                logger.warning(f"加载知识索引失败: {e}")
    
    def _save_index(self):
        """保存知识索引"""
        self.index.last_updated = datetime.now().isoformat()
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index.to_dict(), f, indent=2, ensure_ascii=False)
    
    def add_knowledge_item(self, item: KnowledgeItem) -> str:
        """
        添加知识条目
        
        Args:
            item: 知识条目
            
        Returns:
            条目ID
        """
        if not item.created_at:
            item.created_at = datetime.now().isoformat()
        item.updated_at = datetime.now().isoformat()
        
        self.knowledge_items[item.item_id] = item
        
        self._update_index(item)
        self._update_graph(item)
        self._save_index()
        
        logger.info(f"添加知识条目: {item.item_id}")
        return item.item_id
    
    def _update_index(self, item: KnowledgeItem):
        """更新知识索引"""
        category = item.knowledge_type.value
        if category not in self.index.categories:
            self.index.categories[category] = []
        if item.item_id not in self.index.categories[category]:
            self.index.categories[category].append(item.item_id)
        
        for tag in item.tags:
            if tag not in self.index.tag_index:
                self.index.tag_index[tag] = []
            if item.item_id not in self.index.tag_index[tag]:
                self.index.tag_index[tag].append(item.item_id)
        
        words = re.findall(r'\w+', item.title.lower()) + re.findall(r'\w+', item.content.lower()[:500])
        for word in set(words):
            if len(word) >= 2:
                if word not in self.index.search_index:
                    self.index.search_index[word] = []
                if item.item_id not in self.index.search_index[word]:
                    self.index.search_index[word].append(item.item_id)
    
    def _update_graph(self, item: KnowledgeItem):
        """更新知识图谱"""
        existing_node = next((n for n in self.graph.nodes if n["id"] == item.item_id), None)
        
        node_data = {
            "id": item.item_id,
            "label": item.title,
            "type": item.knowledge_type.value,
            "tags": item.tags,
            "group": item.knowledge_type.value
        }
        
        if existing_node:
            existing_node.update(node_data)
        else:
            self.graph.nodes.append(node_data)
        
        for related_id in item.related_items:
            edge_exists = any(
                e["source"] == item.item_id and e["target"] == related_id
                for e in self.graph.edges
            )
            if not edge_exists:
                self.graph.edges.append({
                    "source": item.item_id,
                    "target": related_id,
                    "type": "related"
                })
    
    def generate_knowledge_doc(
        self,
        items: List[KnowledgeItem] = None,
        format: ReportFormat = ReportFormat.MARKDOWN
    ) -> str:
        """
        生成知识库文档
        
        Args:
            items: 知识条目列表，默认使用所有条目
            format: 输出格式
            
        Returns:
            文档内容
        """
        items = items or list(self.knowledge_items.values())
        
        if format == ReportFormat.MARKDOWN:
            return self._generate_markdown_doc(items)
        elif format == ReportFormat.HTML:
            return self._generate_html_doc(items)
        else:
            return json.dumps([i.to_dict() for i in items], indent=2, ensure_ascii=False)
    
    def _generate_markdown_doc(self, items: List[KnowledgeItem]) -> str:
        """生成Markdown格式知识文档"""
        lines = [
            "# 知识库文档",
            "",
            f"生成时间: {datetime.now().isoformat()}",
            f"条目数量: {len(items)}",
            "",
            "## 目录",
            ""
        ]
        
        by_type: Dict[str, List[KnowledgeItem]] = defaultdict(list)
        for item in items:
            by_type[item.knowledge_type.value].append(item)
        
        for ktype, type_items in by_type.items():
            lines.append(f"- [{ktype.upper()}](#{ktype}) ({len(type_items)})")
        
        lines.append("")
        
        for ktype, type_items in by_type.items():
            lines.append(f"## {ktype.upper()}")
            lines.append("")
            
            for item in sorted(type_items, key=lambda x: x.title):
                lines.append(f"### {item.title}")
                lines.append("")
                lines.append(f"**ID**: {item.item_id}")
                lines.append(f"**类型**: {item.knowledge_type.value}")
                lines.append(f"**标签**: {', '.join(item.tags) if item.tags else '无'}")
                lines.append("")
                lines.append(item.content)
                lines.append("")
                
                if item.related_items:
                    lines.append("**相关条目**:")
                    for related_id in item.related_items:
                        lines.append(f"  - {related_id}")
                    lines.append("")
                
                if item.references:
                    lines.append("**参考链接**:")
                    for ref in item.references:
                        lines.append(f"  - {ref}")
                    lines.append("")
                
                lines.append("---")
                lines.append("")
        
        return "\n".join(lines)
    
    def _generate_html_doc(self, items: List[KnowledgeItem]) -> str:
        """生成HTML格式知识文档"""
        items_html = ""
        
        by_type: Dict[str, List[KnowledgeItem]] = defaultdict(list)
        for item in items:
            by_type[item.knowledge_type.value].append(item)
        
        for ktype, type_items in by_type.items():
            items_html += f"<section><h2>{ktype.upper()}</h2>"
            
            for item in sorted(type_items, key=lambda x: x.title):
                tags_html = ", ".join(item.tags) if item.tags else "无"
                related_html = "".join(f"<li>{rid}</li>" for rid in item.related_items) if item.related_items else "<li>无</li>"
                
                items_html += f"""
                <article class="knowledge-item">
                    <h3>{item.title}</h3>
                    <div class="meta">
                        <span class="type">{item.knowledge_type.value}</span>
                        <span class="tags">标签: {tags_html}</span>
                    </div>
                    <div class="content">{item.content}</div>
                    <div class="related">
                        <h4>相关条目</h4>
                        <ul>{related_html}</ul>
                    </div>
                </article>
"""
            
            items_html += "</section>"
        
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>知识库文档</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        h2 {{ color: #667eea; margin-top: 30px; }}
        .knowledge-item {{ background: #f9f9f9; border-radius: 8px; padding: 20px; margin: 15px 0; }}
        .knowledge-item h3 {{ color: #333; margin-bottom: 10px; }}
        .meta {{ color: #666; font-size: 14px; margin-bottom: 15px; }}
        .meta span {{ margin-right: 15px; }}
        .content {{ line-height: 1.6; }}
        .related {{ margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee; }}
        .related h4 {{ color: #666; font-size: 14px; margin-bottom: 10px; }}
        .related ul {{ list-style: none; padding: 0; }}
        .related li {{ color: #667eea; }}
    </style>
</head>
<body>
    <h1>知识库文档</h1>
    <p>生成时间: {datetime.now().isoformat()} | 条目数量: {len(items)}</p>
    {items_html}
</body>
</html>"""
    
    def export_with_graph(
        self,
        items: List[KnowledgeItem] = None,
        output_path: Path = None,
        include_visualization: bool = True
    ) -> Path:
        """
        导出知识文档（包含知识图谱）
        
        Args:
            items: 知识条目列表
            output_path: 输出路径
            include_visualization: 是否包含可视化
            
        Returns:
            输出文件路径
        """
        items = items or list(self.knowledge_items.values())
        output_path = output_path or self.output_dir / "knowledge_with_graph.html"
        
        doc_content = self._generate_html_doc(items)
        
        if include_visualization:
            graph_json = json.dumps(self.graph.to_dict(), ensure_ascii=False)
            
            visualization_script = f"""
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script>
        const graphData = {graph_json};
        
        const svg = d3.select("body").append("svg")
            .attr("width", 800)
            .attr("height", 600)
            .style("border", "1px solid #ccc")
            .style("margin-top", "20px");
        
        const simulation = d3.forceSimulation(graphData.nodes)
            .force("link", d3.forceLink(graphData.edges).id(d => d.id))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(400, 300));
        
        const link = svg.append("g")
            .selectAll("line")
            .data(graphData.edges)
            .enter().append("line")
            .attr("stroke", "#999");
        
        const node = svg.append("g")
            .selectAll("circle")
            .data(graphData.nodes)
            .enter().append("circle")
            .attr("r", 10)
            .attr("fill", d => {{
                const colors = {{"concept": "#667eea", "pattern": "#10b981", "best_practice": "#f59e0b", "anti_pattern": "#ef4444", "solution": "#3b82f6", "faq": "#8b5cf6"}};
                return colors[d.type] || "#666";
            }})
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));
        
        node.append("title").text(d => d.label);
        
        simulation.on("tick", () => {{
            link.attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            node.attr("cx", d => d.x)
                .attr("cy", d => d.y);
        }});
        
        function dragstarted(event) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }}
        
        function dragged(event) {{
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }}
        
        function dragended(event) {{
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }}
    </script>
"""
            
            doc_content = doc_content.replace("</body>", visualization_script + "</body>")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(doc_content)
        
        logger.info(f"知识文档已导出: {output_path}")
        return output_path
    
    def generate_index(self) -> KnowledgeIndex:
        """生成知识索引"""
        return self.index
    
    def search(self, query: str) -> List[KnowledgeItem]:
        """
        搜索知识条目
        
        Args:
            query: 搜索关键词
            
        Returns:
            匹配的知识条目列表
        """
        words = re.findall(r'\w+', query.lower())
        item_scores: Dict[str, int] = defaultdict(int)
        
        for word in words:
            if len(word) >= 2:
                matching_ids = self.index.search_index.get(word, [])
                for item_id in matching_ids:
                    item_scores[item_id] += 1
        
        sorted_ids = sorted(item_scores.keys(), key=lambda x: item_scores[x], reverse=True)
        
        return [self.knowledge_items[iid] for iid in sorted_ids if iid in self.knowledge_items]
    
    def get_by_category(self, category: KnowledgeType) -> List[KnowledgeItem]:
        """按类别获取知识条目"""
        ids = self.index.categories.get(category.value, [])
        return [self.knowledge_items[iid] for iid in ids if iid in self.knowledge_items]
    
    def get_by_tag(self, tag: str) -> List[KnowledgeItem]:
        """按标签获取知识条目"""
        ids = self.index.tag_index.get(tag, [])
        return [self.knowledge_items[iid] for iid in ids if iid in self.knowledge_items]


class ChangelogGenerator:
    """
    变更日志自动生成器
    
    功能：
    - 从Git历史生成变更日志
    - 支持语义化版本
    - 支持变更分类
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        初始化变更日志生成器
        
        Args:
            project_root: 项目根目录
        """
        self.path_manager = PathConfigManager(auto_detect=True) if project_root is None else None
        self.project_root = project_root or (self.path_manager.get_base_path() if self.path_manager else Path.cwd())
        self.output_dir = self.project_root / "docs"
        self.changelog_file = self.output_dir / "CHANGELOG.md"
        self.history_file = self.output_dir / "changelog_history.json"
        
        self._ensure_directories()
        self.entries: List[ChangelogEntry] = []
        self._load_history()
        
        logger.info(f"变更日志生成器初始化完成，项目根目录: {self.project_root}")
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_history(self):
        """加载变更日志历史"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for entry_data in data.get("entries", []):
                        changes = {}
                        for cat, items in entry_data.get("changes", {}).items():
                            try:
                                changes[ChangeCategory(cat)] = items
                            except ValueError:
                                changes[ChangeCategory.CHANGED] = items
                        
                        self.entries.append(ChangelogEntry(
                            version=entry_data["version"],
                            release_date=entry_data["release_date"],
                            changes=changes,
                            breaking_changes=entry_data.get("breaking_changes", []),
                            migration_guide=entry_data.get("migration_guide", "")
                        ))
            except Exception as e:
                logger.warning(f"加载变更日志历史失败: {e}")
    
    def _save_history(self):
        """保存变更日志历史"""
        data = {
            "entries": [e.to_dict() for e in self.entries],
            "last_updated": datetime.now().isoformat()
        }
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_git_commits(
        self,
        since_tag: str = None,
        until_tag: str = None,
        max_count: int = 100
    ) -> List[GitCommit]:
        """
        获取Git提交历史
        
        Args:
            since_tag: 起始标签
            until_tag: 结束标签
            max_count: 最大数量
            
        Returns:
            Git提交列表
        """
        commits: List[GitCommit] = []
        
        try:
            cmd = ["git", "log", f"--max-count={max_count}", "--pretty=format:%H|%an|%ad|%s", "--date=iso"]
            
            if since_tag:
                cmd.append(f"{since_tag}..HEAD")
            if until_tag:
                cmd.extend(["--tags", until_tag])
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    
                    parts = line.split('|', 3)
                    if len(parts) >= 4:
                        commits.append(GitCommit(
                            commit_hash=parts[0][:8],
                            author=parts[1],
                            date=parts[2],
                            message=parts[3]
                        ))
        except Exception as e:
            logger.warning(f"获取Git提交历史失败: {e}")
        
        return commits
    
    def classify_commit(self, commit: GitCommit) -> ChangeCategory:
        """
        分类提交
        
        Args:
            commit: Git提交
            
        Returns:
            变更类别
        """
        message = commit.message.lower()
        
        if any(kw in message for kw in ['add', '新增', 'create', 'implement', 'feat']):
            return ChangeCategory.ADDED
        elif any(kw in message for kw in ['fix', '修复', 'bugfix']):
            return ChangeCategory.FIXED
        elif any(kw in message for kw in ['remove', '删除', 'delete']):
            return ChangeCategory.REMOVED
        elif any(kw in message for kw in ['deprecate', '废弃', 'deprecated']):
            return ChangeCategory.DEPRECATED
        elif any(kw in message for kw in ['security', '安全', 'cve']):
            return ChangeCategory.SECURITY
        else:
            return ChangeCategory.CHANGED
    
    def generate_from_git(
        self,
        version: str,
        since_tag: str = None,
        release_date: str = None
    ) -> ChangelogEntry:
        """
        从Git历史生成变更日志
        
        Args:
            version: 版本号
            since_tag: 起始标签
            release_date: 发布日期
            
        Returns:
            变更日志条目
        """
        commits = self.get_git_commits(since_tag=since_tag)
        
        changes: Dict[ChangeCategory, List[Dict[str, Any]]] = defaultdict(list)
        breaking_changes: List[str] = []
        
        for commit in commits:
            category = self.classify_commit(commit)
            
            change_item = {
                "message": commit.message,
                "hash": commit.commit_hash,
                "author": commit.author,
                "date": commit.date
            }
            
            changes[category].append(change_item)
            
            if 'breaking' in commit.message.lower() or 'break' in commit.message.lower():
                breaking_changes.append(commit.message)
        
        entry = ChangelogEntry(
            version=version,
            release_date=release_date or datetime.now().strftime("%Y-%m-%d"),
            changes=dict(changes),
            breaking_changes=breaking_changes
        )
        
        self.entries.append(entry)
        self._save_history()
        
        logger.info(f"生成变更日志: {version}")
        return entry
    
    def add_entry(
        self,
        version: str,
        changes: Dict[ChangeCategory, List[str]],
        release_date: str = None,
        breaking_changes: List[str] = None,
        migration_guide: str = ""
    ) -> ChangelogEntry:
        """
        手动添加变更日志条目
        
        Args:
            version: 版本号
            changes: 变更内容
            release_date: 发布日期
            breaking_changes: 破坏性变更列表
            migration_guide: 迁移指南
            
        Returns:
            变更日志条目
        """
        formatted_changes = {
            cat: [{"message": msg} for msg in items]
            for cat, items in changes.items()
        }
        
        entry = ChangelogEntry(
            version=version,
            release_date=release_date or datetime.now().strftime("%Y-%m-%d"),
            changes=formatted_changes,
            breaking_changes=breaking_changes or [],
            migration_guide=migration_guide
        )
        
        self.entries.append(entry)
        self._save_history()
        
        logger.info(f"添加变更日志条目: {version}")
        return entry
    
    def generate_changelog_doc(self, format: ReportFormat = ReportFormat.MARKDOWN) -> str:
        """
        生成变更日志文档
        
        Args:
            format: 输出格式
            
        Returns:
            文档内容
        """
        if format == ReportFormat.MARKDOWN:
            return self._generate_markdown_changelog()
        elif format == ReportFormat.HTML:
            return self._generate_html_changelog()
        else:
            return json.dumps([e.to_dict() for e in self.entries], indent=2, ensure_ascii=False)
    
    def _generate_markdown_changelog(self) -> str:
        """生成Markdown格式变更日志"""
        lines = [
            "# 变更日志 (Changelog)",
            "",
            "本文件记录项目的所有重要变更。",
            "",
            "格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，",
            "版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。",
            ""
        ]
        
        sorted_entries = sorted(self.entries, key=lambda e: e.release_date, reverse=True)
        
        for entry in sorted_entries:
            lines.append(f"## [{entry.version}] - {entry.release_date}")
            lines.append("")
            
            if entry.breaking_changes:
                lines.append("### ⚠️ 破坏性变更")
                lines.append("")
                for bc in entry.breaking_changes:
                    lines.append(f"- {bc}")
                lines.append("")
            
            category_order = [
                (ChangeCategory.ADDED, "新增"),
                (ChangeCategory.CHANGED, "变更"),
                (ChangeCategory.DEPRECATED, "废弃"),
                (ChangeCategory.REMOVED, "移除"),
                (ChangeCategory.FIXED, "修复"),
                (ChangeCategory.SECURITY, "安全")
            ]
            
            for category, title in category_order:
                items = entry.changes.get(category, [])
                if items:
                    lines.append(f"### {title}")
                    lines.append("")
                    for item in items:
                        msg = item.get("message", str(item))
                        lines.append(f"- {msg}")
                    lines.append("")
            
            if entry.migration_guide:
                lines.append("### 迁移指南")
                lines.append("")
                lines.append(entry.migration_guide)
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_html_changelog(self) -> str:
        """生成HTML格式变更日志"""
        entries_html = ""
        
        sorted_entries = sorted(self.entries, key=lambda e: e.release_date, reverse=True)
        
        for entry in sorted_entries:
            breaking_html = ""
            if entry.breaking_changes:
                breaking_html = '<div class="breaking-changes"><h4>⚠️ 破坏性变更</h4><ul>'
                for bc in entry.breaking_changes:
                    breaking_html += f"<li>{bc}</li>"
                breaking_html += "</ul></div>"
            
            changes_html = ""
            category_titles = {
                ChangeCategory.ADDED: "新增",
                ChangeCategory.CHANGED: "变更",
                ChangeCategory.DEPRECATED: "废弃",
                ChangeCategory.REMOVED: "移除",
                ChangeCategory.FIXED: "修复",
                ChangeCategory.SECURITY: "安全"
            }
            
            for category, title in category_titles.items():
                items = entry.changes.get(category, [])
                if items:
                    changes_html += f"<div class='change-section'><h4>{title}</h4><ul>"
                    for item in items:
                        msg = item.get("message", str(item))
                        changes_html += f"<li>{msg}</li>"
                    changes_html += "</ul></div>"
            
            entries_html += f"""
        <article class="version-entry">
            <h3>版本 {entry.version} <span class="date">{entry.release_date}</span></h3>
            {breaking_html}
            {changes_html}
        </article>
"""
        
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>变更日志</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        .version-entry {{ background: #f9f9f9; border-radius: 8px; padding: 20px; margin: 20px 0; }}
        .version-entry h3 {{ color: #667eea; margin-bottom: 15px; }}
        .version-entry .date {{ color: #666; font-size: 14px; font-weight: normal; }}
        .breaking-changes {{ background: #fef2f2; border-left: 4px solid #ef4444; padding: 15px; margin: 15px 0; }}
        .breaking-changes h4 {{ color: #dc2626; margin-bottom: 10px; }}
        .change-section {{ margin: 15px 0; }}
        .change-section h4 {{ color: #333; margin-bottom: 10px; }}
        .change-section ul {{ list-style: disc; padding-left: 20px; }}
        .change-section li {{ margin: 5px 0; }}
    </style>
</head>
<body>
    <h1>变更日志 (Changelog)</h1>
    <p>本页面记录项目的所有重要变更。</p>
    {entries_html}
</body>
</html>"""
    
    def save_changelog(
        self,
        content: str = None,
        output_path: Path = None,
        format: ReportFormat = ReportFormat.MARKDOWN
    ) -> Path:
        """
        保存变更日志
        
        Args:
            content: 内容，默认自动生成
            output_path: 输出路径
            format: 输出格式
            
        Returns:
            输出文件路径
        """
        output_path = output_path or self.changelog_file
        content = content or self.generate_changelog_doc(format)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"变更日志已保存: {output_path}")
        return output_path
    
    def get_latest_version(self) -> Optional[str]:
        """获取最新版本号"""
        if not self.entries:
            return None
        return sorted(self.entries, key=lambda e: e.release_date, reverse=True)[0].version
    
    def get_entry(self, version: str) -> Optional[ChangelogEntry]:
        """获取指定版本的变更日志"""
        return next((e for e in self.entries if e.version == version), None)


class DocumentAutoGenerator:
    """
    文档自动生成器统一入口
    
    功能：
    - 整合所有文档生成器
    - 提供统一的文档生成接口
    - 支持多种文档格式
    """
    
    def __init__(self, project_root: Optional[Path] = None, output_dir: Optional[Path] = None):
        """
        初始化文档自动生成器
        
        Args:
            project_root: 项目根目录
            output_dir: 输出目录（可选，如果提供则覆盖默认输出目录）
        """
        self.path_manager = PathConfigManager(auto_detect=True) if project_root is None else None
        self.project_root = project_root or (self.path_manager.get_base_path() if self.path_manager else Path.cwd())
        self.output_dir = output_dir or self.project_root / "docs" / "generated"
        
        self._ensure_directories()
        
        self.evolution_report_gen = EvolutionReportGenerator(self.project_root)
        self.api_doc_gen = APIDocGenerator(self.project_root)
        self.knowledge_doc_gen = KnowledgeDocGenerator(self.project_root)
        self.changelog_gen = ChangelogGenerator(self.project_root)
        
        logger.info(f"文档自动生成器初始化完成，项目根目录: {self.project_root}")
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self, data: Dict[str, Any], output_name: str, format: str = "markdown") -> Path:
        """
        生成文档
        
        Args:
            data: 文档数据
            output_name: 输出文件名
            format: 输出格式（markdown, html, json）
            
        Returns:
            输出文件路径
        """
        if format == "markdown":
            return self.format_markdown(data, output_name)
        elif format == "html":
            return self.format_html(data, output_name)
        else:
            return self._save_json(data, output_name)
    
    def format_markdown(self, content: Dict[str, Any], output_name: str = None) -> Path:
        """
        格式化为Markdown
        
        Args:
            content: 文档内容
            output_name: 输出文件名
            
        Returns:
            输出文件路径
        """
        lines = []
        
        if "title" in content:
            lines.append(f"# {content['title']}")
            lines.append("")
        
        if "body" in content:
            lines.append(content['body'])
            lines.append("")
        
        if "code_blocks" in content:
            for block in content['code_blocks']:
                lines.append(f"```{block.get('language', '')}")
                lines.append(block.get('code', ''))
                lines.append("```")
                lines.append("")
        
        if "tables" in content:
            for table in content['tables']:
                headers = table.get('headers', [])
                rows = table.get('rows', [])
                
                lines.append("| " + " | ".join(headers) + " |")
                lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                
                for row in rows:
                    lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
                lines.append("")
        
        if "sections" in content:
            for section in content['sections']:
                lines.append(f"## {section.get('title', '')}")
                lines.append("")
                lines.append(section.get('content', ''))
                lines.append("")
        
        markdown_content = "\n".join(lines)
        
        if output_name:
            output_path = self.output_dir / f"{output_name}.md"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            logger.info(f"Markdown文档已生成: {output_path}")
            return output_path
        
        return markdown_content
    
    def format_html(self, content: Dict[str, Any], output_name: str = None) -> Path:
        """
        格式化为HTML
        
        Args:
            content: 文档内容
            output_name: 输出文件名
            
        Returns:
            输出文件路径
        """
        html_parts = [
            "<!DOCTYPE html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="UTF-8">',
            f"<title>{content.get('title', '文档')}</title>",
            "<style>",
            "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }",
            "h1 { color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }",
            "h2 { color: #667eea; margin-top: 30px; }",
            "pre { background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }",
            "table { border-collapse: collapse; width: 100%; margin: 20px 0; }",
            "th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }",
            "th { background: #f8f9fa; }",
            "</style>",
            "</head>",
            "<body>"
        ]
        
        if "title" in content:
            html_parts.append(f"<h1>{content['title']}</h1>")
        
        if "body" in content:
            html_parts.append(f"<p>{content['body']}</p>")
        
        if "code_blocks" in content:
            for block in content['code_blocks']:
                html_parts.append(f"<pre><code class=\"{block.get('language', '')}\">{block.get('code', '')}</code></pre>")
        
        if "tables" in content:
            for table in content['tables']:
                headers = table.get('headers', [])
                rows = table.get('rows', [])
                
                html_parts.append("<table>")
                html_parts.append("<thead><tr>")
                for header in headers:
                    html_parts.append(f"<th>{header}</th>")
                html_parts.append("</tr></thead>")
                html_parts.append("<tbody>")
                for row in rows:
                    html_parts.append("<tr>")
                    for cell in row:
                        html_parts.append(f"<td>{cell}</td>")
                    html_parts.append("</tr>")
                html_parts.append("</tbody></table>")
        
        if "sections" in content:
            for section in content['sections']:
                html_parts.append(f"<h2>{section.get('title', '')}</h2>")
                html_parts.append(f"<p>{section.get('content', '')}</p>")
        
        html_parts.extend(["</body>", "</html>"])
        
        html_content = "\n".join(html_parts)
        
        if output_name:
            output_path = self.output_dir / f"{output_name}.html"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"HTML文档已生成: {output_path}")
            return output_path
        
        return html_content
    
    def render_template(self, template: str, data: Dict[str, Any]) -> str:
        """
        渲染模板
        
        Args:
            template: 模板字符串
            data: 模板数据
            
        Returns:
            渲染后的内容
        """
        content = template
        
        for key, value in data.items():
            placeholder = "{{ " + key + " }}"
            content = content.replace(placeholder, str(value))
        
        if "{% for" in template:
            import re
            for_pattern = r'{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%}(.*?){%\s*endfor\s*%}'
            
            def replace_for(match):
                item_name = match.group(1)
                list_name = match.group(2)
                item_template = match.group(3)
                
                items = data.get(list_name, [])
                result = []
                for item in items:
                    item_content = item_template
                    if isinstance(item, dict):
                        for k, v in item.items():
                            item_content = item_content.replace("{{ " + k + " }}", str(v))
                    else:
                        item_content = item_content.replace("{{ " + item_name + " }}", str(item))
                    result.append(item_content)
                
                return "".join(result)
            
            content = re.sub(for_pattern, replace_for, content, flags=re.DOTALL)
        
        return content
    
    def export_document(self, content: str, filename: str, format: str = "markdown") -> Path:
        """
        导出文档
        
        Args:
            content: 文档内容
            filename: 文件名
            format: 格式
            
        Returns:
            输出文件路径
        """
        ext_map = {
            "markdown": ".md",
            "html": ".html",
            "json": ".json"
        }
        
        ext = ext_map.get(format, ".txt")
        output_path = self.output_dir / f"{filename}{ext}"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"文档已导出: {output_path}")
        return output_path
    
    def _save_json(self, data: Dict[str, Any], output_name: str) -> Path:
        """保存JSON格式"""
        output_path = self.output_dir / f"{output_name}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return output_path


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="文档自动生成器")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    parser_report = subparsers.add_parser("report", help="生成演化报告")
    parser_report.add_argument("--daily", action="store_true", help="生成日报")
    parser_report.add_argument("--weekly", action="store_true", help="生成周报")
    parser_report.add_argument("--monthly", action="store_true", help="生成月报")
    parser_report.add_argument("--format", choices=["json", "markdown", "html"], default="json", help="输出格式")
    
    parser_api = subparsers.add_parser("api", help="生成API文档")
    parser_api.add_argument("source", help="源代码路径")
    parser_api.add_argument("--output", help="输出文件路径")
    parser_api.add_argument("--format", choices=["openapi"], default="openapi", help="输出格式")
    
    parser_knowledge = subparsers.add_parser("knowledge", help="生成知识库文档")
    parser_knowledge.add_argument("--output", help="输出文件路径")
    parser_knowledge.add_argument("--with-graph", action="store_true", help="包含知识图谱")
    
    parser_changelog = subparsers.add_parser("changelog", help="生成变更日志")
    parser_changelog.add_argument("--version", help="版本号")
    parser_changelog.add_argument("--since-tag", help="起始标签")
    parser_changelog.add_argument("--output", help="输出文件路径")
    parser_changelog.add_argument("--format", choices=["markdown", "html", "json"], default="markdown", help="输出格式")
    
    args = parser.parse_args()
    
    format_map = {
        "json": ReportFormat.JSON,
        "markdown": ReportFormat.MARKDOWN,
        "html": ReportFormat.HTML
    }
    
    if args.command == "report":
        generator = EvolutionReportGenerator()
        
        if args.daily:
            report = generator.generate_daily_report()
        elif args.weekly:
            report = generator.generate_weekly_report()
        elif args.monthly:
            report = generator.generate_monthly_report()
        else:
            report = generator.generate_daily_report()
        
        path = generator.save_report(report, format=format_map[args.format])
        print(f"报告已生成: {path}")
    
    elif args.command == "api":
        generator = APIDocGenerator()
        schema = generator.generate_from_code(Path(args.source))
        
        output_path = Path(args.output) if args.output else None
        path = generator.export_openapi(schema, output_path)
        print(f"API文档已生成: {path}")
    
    elif args.command == "knowledge":
        generator = KnowledgeDocGenerator()
        
        output_path = Path(args.output) if args.output else None
        
        if args.with_graph:
            path = generator.export_with_graph(output_path=output_path)
        else:
            doc = generator.generate_knowledge_doc(format=ReportFormat.HTML)
            path = output_path or generator.output_dir / "knowledge.html"
            with open(path, 'w', encoding='utf-8') as f:
                f.write(doc)
        
        print(f"知识库文档已生成: {path}")
    
    elif args.command == "changelog":
        generator = ChangelogGenerator()
        
        if args.version:
            generator.generate_from_git(args.version, args.since_tag)
        
        content = generator.generate_changelog_doc(format=format_map[args.format])
        output_path = Path(args.output) if args.output else None
        path = generator.save_changelog(content, output_path, format_map[args.format])
        print(f"变更日志已生成: {path}")
    
    else:
        parser.print_help()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
