from dataclasses import dataclass
from typing import List, Callable
from sqlalchemy.orm import Session

from ...models.task import Task
from ...models.milestone import Milestone


@dataclass
class TaskStatistics:
    total: int
    completed: int
    in_progress: int
    pending: int
    review: int
    high_priority: int
    medium_priority: int
    low_priority: int
    completion_rate: float


@dataclass
class MilestoneStatistics:
    total: int
    completed: int
    in_progress: int
    overdue: int


class StatisticsCollector:
    def __init__(self, db: Session, project_id: int):
        self.db = db
        self.project_id = project_id
        self._tasks: List[Task] = []
        self._milestones: List[Milestone] = []

    def collect_tasks(self) -> List[Task]:
        if not self._tasks:
            self._tasks = self.db.query(Task).filter(
                Task.project_id == self.project_id
            ).all()
        return self._tasks

    def collect_milestones(self) -> List[Milestone]:
        if not self._milestones:
            self._milestones = self.db.query(Milestone).filter(
                Milestone.project_id == self.project_id
            ).all()
        return self._milestones

    def get_task_statistics(self) -> TaskStatistics:
        tasks = self.collect_tasks()
        total = len(tasks)
        
        completed = self._count_by_status(tasks, "COMPLETED")
        in_progress = self._count_by_status(tasks, "IN_PROGRESS")
        pending = self._count_by_status(tasks, "PENDING")
        review = self._count_by_status(tasks, "REVIEW")
        
        high_priority = self._count_by_priority(tasks, "high")
        medium_priority = self._count_by_priority(tasks, "medium")
        low_priority = self._count_by_priority(tasks, "low")
        
        completion_rate = round((completed / total) * 100, 2) if total > 0 else 0.0
        
        return TaskStatistics(
            total=total,
            completed=completed,
            in_progress=in_progress,
            pending=pending,
            review=review,
            high_priority=high_priority,
            medium_priority=medium_priority,
            low_priority=low_priority,
            completion_rate=completion_rate
        )

    def get_milestone_statistics(self) -> MilestoneStatistics:
        from datetime import datetime
        
        milestones = self.collect_milestones()
        total = len(milestones)
        
        completed = self._count_milestone_by_status(milestones, "completed")
        in_progress = self._count_milestone_by_status(milestones, "in_progress")
        
        overdue = sum(
            1 for m in milestones
            if m.planned_date and m.planned_date < datetime.now() and m.status != "completed"
        )
        
        return MilestoneStatistics(
            total=total,
            completed=completed,
            in_progress=in_progress,
            overdue=overdue
        )

    @staticmethod
    def _count_by_status(tasks: List[Task], status: str) -> int:
        return sum(1 for t in tasks if t.status == status)

    @staticmethod
    def _count_by_priority(tasks: List[Task], priority: str) -> int:
        return sum(1 for t in tasks if t.priority == priority)

    @staticmethod
    def _count_milestone_by_status(milestones: List[Milestone], status: str) -> int:
        return sum(1 for m in milestones if m.status == status)
