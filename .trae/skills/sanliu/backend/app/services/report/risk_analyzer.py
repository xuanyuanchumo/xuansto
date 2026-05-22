from dataclasses import dataclass
from typing import List


@dataclass
class Risk:
    description: str
    severity: str = "medium"


@dataclass
class Suggestion:
    description: str


class RiskAnalyzer:
    def __init__(
        self,
        completion_rate: float,
        project_status: str,
        pending_tasks: int,
        completed_tasks: int,
        overdue_milestones: int
    ):
        self.completion_rate = completion_rate
        self.project_status = project_status
        self.pending_tasks = pending_tasks
        self.completed_tasks = completed_tasks
        self.overdue_milestones = overdue_milestones

    def analyze(self) -> tuple[List[Risk], List[Suggestion]]:
        risks = []
        suggestions = []
        
        self._check_progress_risk(risks, suggestions)
        self._check_pending_tasks_risk(risks, suggestions)
        self._check_overdue_milestones_risk(risks, suggestions)
        
        return risks, suggestions

    def _check_progress_risk(self, risks: List[Risk], suggestions: List[Suggestion]) -> None:
        if self.completion_rate < 50 and self.project_status in ["DEVELOPMENT", "TESTING"]:
            risks.append(Risk(
                description="项目进度较慢，可能无法按时完成",
                severity="high"
            ))
            suggestions.append(Suggestion(
                description="建议评估是否需要增加资源或调整计划"
            ))

    def _check_pending_tasks_risk(self, risks: List[Risk], suggestions: List[Suggestion]) -> None:
        if self.pending_tasks > self.completed_tasks and self.project_status in ["DEVELOPMENT", "TESTING"]:
            risks.append(Risk(
                description="待处理任务数量较多",
                severity="medium"
            ))
            suggestions.append(Suggestion(
                description="建议优先处理高优先级任务"
            ))

    def _check_overdue_milestones_risk(self, risks: List[Risk], suggestions: List[Suggestion]) -> None:
        if self.overdue_milestones > 0:
            risks.append(Risk(
                description=f"有 {self.overdue_milestones} 个里程碑已逾期",
                severity="high"
            ))
            suggestions.append(Suggestion(
                description="建议重新评估里程碑计划或加快进度"
            ))
