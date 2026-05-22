from fastapi import HTTPException
from typing import Union
from enum import Enum

from ...models.project import ProjectStatus
from ...models.task import TaskStatus


class StatusValidator:
    @staticmethod
    def validate_status(status_value: str, status_enum: type) -> Enum:
        try:
            return status_enum(status_value)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status_value}"
            )

    @staticmethod
    def validate_transition(
        current_status: Enum,
        new_status: Enum,
        allowed_transitions: dict
    ) -> None:
        allowed = allowed_transitions.get(current_status, [])
        if new_status not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot transition from {current_status.value} to {new_status.value}"
            )

    @staticmethod
    def validate_entity_type(entity_type: str) -> None:
        if entity_type not in ["project", "task"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid entity type. Use 'project' or 'task'"
            )

    @staticmethod
    def validate_project_status(status: str) -> ProjectStatus:
        return StatusValidator.validate_status(status, ProjectStatus)

    @staticmethod
    def validate_task_status(status: str) -> TaskStatus:
        return StatusValidator.validate_status(status, TaskStatus)
