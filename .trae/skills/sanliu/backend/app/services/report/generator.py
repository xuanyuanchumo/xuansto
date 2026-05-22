from datetime import datetime
from typing import List

from .statistics_collector import TaskStatistics, MilestoneStatistics
from .risk_analyzer import Risk, Suggestion
from .formatters import ProgressBarGenerator, MarkdownFormatter
from ...models.project import Project
from ...models.task import Task
from ...models.milestone import Milestone


class ReportGenerator:
    def __init__(self, project: Project):
        self.project = project
        self.lines: List[str] = []
        self.formatter = MarkdownFormatter()
        self.progress_bar = ProgressBarGenerator()

    def generate(
        self,
        task_stats: TaskStatistics,
        milestone_stats: MilestoneStatistics,
        milestones: List[Milestone],
        risks: List[Risk],
        suggestions: List[Suggestion]
    ) -> str:
        self.lines = []
        
        self._add_header()
        self._add_project_overview(task_stats.completion_rate)
        self._add_progress_summary(task_stats)
        self._add_milestones_section(milestones, milestone_stats)
        self._add_task_statistics(task_stats)
        self._add_risks_and_suggestions(risks, suggestions)
        self._add_footer()
        
        return "\n".join(self.lines)

    def _add_header(self) -> None:
        self.lines.append(self.formatter.heading("项目进度报告"))
        self.lines.append("")
        self.lines.append(
            self.formatter.bold("生成时间") + 
            f": {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.lines.append("")

    def _add_project_overview(self, completion_rate: float) -> None:
        self.lines.append(self.formatter.heading("项目概述", level=2))
        self.lines.append("")
        self.lines.append(self.formatter.list_item(f"**项目名称**: {self.project.name}"))
        self.lines.append(self.formatter.list_item(f"**项目状态**: {self.project.status}"))
        self.lines.append(self.formatter.list_item(f"**整体进度**: {completion_rate}%"))
        
        if self.project.description:
            self.lines.append(self.formatter.list_item(f"**项目描述**: {self.project.description}"))
        
        if self.project.tech_stack:
            tech_stack = ", ".join(self.project.tech_stack) if isinstance(self.project.tech_stack, list) else str(self.project.tech_stack)
            self.lines.append(self.formatter.list_item(f"**技术栈**: {tech_stack}"))
        
        created_at = self.project.created_at.strftime('%Y-%m-%d') if self.project.created_at else '-'
        self.lines.append(self.formatter.list_item(f"**创建时间**: {created_at}"))
        self.lines.append("")

    def _add_progress_summary(self, stats: TaskStatistics) -> None:
        self.lines.append(self.formatter.heading("进度摘要", level=2))
        self.lines.append("")
        self.lines.append(self.formatter.list_item(f"总任务数: {stats.total}"))
        self.lines.append(self.formatter.list_item(f"已完成: {stats.completed}"))
        self.lines.append(self.formatter.list_item(f"进行中: {stats.in_progress}"))
        self.lines.append(self.formatter.list_item(f"待处理: {stats.pending}"))
        self.lines.append(self.formatter.list_item(f"审核中: {stats.review}"))
        self.lines.append("")
        
        progress_bar = self.progress_bar.generate(stats.completion_rate)
        self.lines.append(f"**完成进度**: {progress_bar} {stats.completion_rate}%")
        self.lines.append("")

    def _add_milestones_section(self, milestones: List[Milestone], stats: MilestoneStatistics) -> None:
        self.lines.append(self.formatter.heading("里程碑完成情况", level=2))
        self.lines.append("")
        
        if milestones:
            self._add_milestones_table(milestones)
            self._add_milestones_summary(stats)
        else:
            self.lines.append("暂无里程碑")
        
        self.lines.append("")

    def _add_milestones_table(self, milestones: List[Milestone]) -> None:
        self.lines.append(self.formatter.table_header(["里程碑", "状态", "计划日期", "完成日期"]))
        self.lines.append(self.formatter.table_separator(4))
        
        status_map = {"pending": "待处理", "in_progress": "进行中", "completed": "已完成"}
        
        for m in milestones:
            planned = m.planned_date.strftime('%Y-%m-%d') if m.planned_date else '-'
            completed = m.completed_date.strftime('%Y-%m-%d') if m.completed_date else '-'
            status_display = status_map.get(m.status, m.status)
            self.lines.append(self.formatter.table_row([m.name, status_display, planned, completed]))
        
        self.lines.append("")

    def _add_milestones_summary(self, stats: MilestoneStatistics) -> None:
        self.lines.append(self.formatter.list_item(f"总里程碑数: {stats.total}"))
        self.lines.append(self.formatter.list_item(f"已完成: {stats.completed}"))
        self.lines.append(self.formatter.list_item(f"进行中: {stats.in_progress}"))

    def _add_task_statistics(self, stats: TaskStatistics) -> None:
        self.lines.append(self.formatter.heading("任务统计", level=2))
        self.lines.append("")
        
        if stats.total > 0:
            self._add_task_status_distribution(stats)
            self._add_task_priority_distribution(stats)
        else:
            self.lines.append("暂无任务")
        
        self.lines.append("")

    def _add_task_status_distribution(self, stats: TaskStatistics) -> None:
        self.lines.append(self.formatter.heading("按状态分布", level=3))
        self.lines.append("")
        
        total = stats.total
        self.lines.append(self.formatter.list_item(
            f"已完成: {stats.completed} ({self._percentage(stats.completed, total)}%)"
        ))
        self.lines.append(self.formatter.list_item(
            f"进行中: {stats.in_progress} ({self._percentage(stats.in_progress, total)}%)"
        ))
        self.lines.append(self.formatter.list_item(
            f"待处理: {stats.pending} ({self._percentage(stats.pending, total)}%)"
        ))
        self.lines.append(self.formatter.list_item(
            f"审核中: {stats.review} ({self._percentage(stats.review, total)}%)"
        ))
        self.lines.append("")

    def _add_task_priority_distribution(self, stats: TaskStatistics) -> None:
        self.lines.append(self.formatter.heading("按优先级分布", level=3))
        self.lines.append("")
        self.lines.append(self.formatter.list_item(f"高优先级: {stats.high_priority}"))
        self.lines.append(self.formatter.list_item(f"中优先级: {stats.medium_priority}"))
        self.lines.append(self.formatter.list_item(f"低优先级: {stats.low_priority}"))

    def _add_risks_and_suggestions(self, risks: List[Risk], suggestions: List[Suggestion]) -> None:
        self.lines.append(self.formatter.heading("风险和建议", level=2))
        self.lines.append("")
        
        self._add_risks(risks)
        self._add_suggestions(suggestions)

    def _add_risks(self, risks: List[Risk]) -> None:
        if risks:
            for i, risk in enumerate(risks, 1):
                self.lines.append(self.formatter.numbered_item(i, risk.description))
        else:
            self.lines.append("暂无明显风险")
        self.lines.append("")

    def _add_suggestions(self, suggestions: List[Suggestion]) -> None:
        self.lines.append(self.formatter.heading("建议", level=3))
        self.lines.append("")
        
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                self.lines.append(self.formatter.numbered_item(i, suggestion.description))
        else:
            self.lines.append("继续保持当前进度")
        self.lines.append("")

    def _add_footer(self) -> None:
        self.lines.append(self.formatter.horizontal_rule())
        self.lines.append("*报告由三省六部协同开发系统自动生成*")

    @staticmethod
    def _percentage(value: int, total: int) -> float:
        return round(value / total * 100, 1) if total > 0 else 0.0
