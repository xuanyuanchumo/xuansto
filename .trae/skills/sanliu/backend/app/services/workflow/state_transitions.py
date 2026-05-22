from typing import List, Type
from enum import Enum

from ...models.project import ProjectStatus, PROJECT_STATUS_TRANSITIONS
from ...models.task import TaskStatus, TASK_STATUS_TRANSITIONS


class StateTransitionManager:
    @staticmethod
    def get_allowed_transitions(
        current_status: Enum,
        transitions_map: dict
    ) -> List[Enum]:
        return transitions_map.get(current_status, [])

    @staticmethod
    def get_project_transitions(project_status: ProjectStatus) -> List[ProjectStatus]:
        return StateTransitionManager.get_allowed_transitions(
            project_status,
            PROJECT_STATUS_TRANSITIONS
        )

    @staticmethod
    def get_task_transitions(task_status: TaskStatus) -> List[TaskStatus]:
        return StateTransitionManager.get_allowed_transitions(
            task_status,
            TASK_STATUS_TRANSITIONS
        )

    @staticmethod
    def format_transitions_response(
        current_status: Enum,
        allowed_transitions: List[Enum]
    ) -> dict:
        return {
            "current_status": current_status.value,
            "allowed_transitions": [s.value for s in allowed_transitions]
        }
