from typing import List, Dict, Any, Set
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ...models.task import Task, TaskStatus


class WorkflowExecutor:
    STATUS_NOT_FOUND = "not_found"
    
    @staticmethod
    def _build_dependency_detail(dep_task: Task) -> Dict[str, Any]:
        return {
            "id": dep_task.id,
            "title": dep_task.title,
            "status": dep_task.status
        }

    @staticmethod
    def _build_not_found_detail(dep_id: int) -> Dict[str, Any]:
        return {
            "id": dep_id,
            "title": "Unknown",
            "status": WorkflowExecutor.STATUS_NOT_FOUND
        }

    @staticmethod
    def _process_dependency(
        dep_id: int,
        dependency_map: Dict[int, Task]
    ) -> tuple[bool, Dict[str, Any]]:
        dep_task = dependency_map.get(dep_id)
        
        if not dep_task:
            return True, WorkflowExecutor._build_not_found_detail(dep_id)
        
        detail = WorkflowExecutor._build_dependency_detail(dep_task)
        is_pending = dep_task.status != TaskStatus.COMPLETED.value
        
        return is_pending, detail

    @staticmethod
    def check_dependencies(
        task: Task,
        db: Session
    ) -> Dict[str, Any]:
        dependencies = task.dependencies or []
        
        if not dependencies:
            return {
                "all_dependencies_completed": True,
                "pending_dependencies": [],
                "dependency_details": []
            }
        
        dependency_tasks = db.query(Task).filter(Task.id.in_(dependencies)).all()
        dependency_map = {t.id: t for t in dependency_tasks}
        
        pending_dependencies: List[int] = []
        dependency_details: List[Dict[str, Any]] = []
        
        for dep_id in dependencies:
            is_pending, detail = WorkflowExecutor._process_dependency(dep_id, dependency_map)
            dependency_details.append(detail)
            if is_pending:
                pending_dependencies.append(dep_id)
        
        return {
            "all_dependencies_completed": len(pending_dependencies) == 0,
            "pending_dependencies": pending_dependencies,
            "dependency_details": dependency_details
        }

    @staticmethod
    def get_task_or_raise(task_id: int, db: Session) -> Task:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    @staticmethod
    def check_circular_dependencies(
        task_id: int,
        new_dependencies: List[int],
        db: Session
    ) -> bool:
        if not new_dependencies:
            return False
        
        visited: Set[int] = set()
        stack: Set[int] = set()
        
        def has_cycle(current_id: int) -> bool:
            if current_id in stack:
                return True
            if current_id in visited:
                return False
            
            visited.add(current_id)
            stack.add(current_id)
            
            task = db.query(Task).filter(Task.id == current_id).first()
            if task and task.dependencies:
                for dep_id in task.dependencies:
                    if has_cycle(dep_id):
                        return True
            
            stack.remove(current_id)
            return False
        
        for dep_id in new_dependencies:
            if dep_id == task_id:
                return True
            if has_cycle(dep_id):
                return True
        
        return False

    @staticmethod
    def get_ready_tasks(project_id: int, db: Session) -> List[Task]:
        tasks = db.query(Task).filter(
            Task.project_id == project_id,
            Task.status == TaskStatus.PENDING.value
        ).all()
        
        ready_tasks = []
        for task in tasks:
            result = WorkflowExecutor.check_dependencies(task, db)
            if result["all_dependencies_completed"]:
                ready_tasks.append(task)
        
        return ready_tasks
