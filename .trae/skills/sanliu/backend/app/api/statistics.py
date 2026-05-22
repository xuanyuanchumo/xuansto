from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.base import get_db
from ..models.project import Project
from ..models.task import Task
from ..models.skill_call import SkillCall
from ..models.agent import Agent
from ..services.cache import cache_service, CacheKeys

router = APIRouter()

@router.get("")
def get_statistics_overview(db: Session = Depends(get_db)):
    cache_key = "statistics:overview"
    cached = cache_service.get_json(cache_key)
    if cached:
        return cached
    
    total_projects = db.query(func.count(Project.id)).scalar()
    total_tasks = db.query(func.count(Task.id)).scalar()
    total_skill_calls = db.query(func.count(SkillCall.id)).scalar()
    total_agents = db.query(func.count(Agent.id)).scalar()
    
    completed_tasks = db.query(func.count(Task.id)).filter(
        Task.status == "COMPLETED"
    ).scalar()
    
    successful_calls = db.query(func.count(SkillCall.id)).filter(
        SkillCall.status == "completed"
    ).scalar()
    
    task_completion_rate = 0
    if total_tasks > 0:
        task_completion_rate = round((completed_tasks / total_tasks) * 100, 2)
    
    call_success_rate = 0
    if total_skill_calls > 0:
        call_success_rate = round((successful_calls / total_skill_calls) * 100, 2)
    
    result = {
        "total_projects": total_projects,
        "total_tasks": total_tasks,
        "total_skill_calls": total_skill_calls,
        "total_agents": total_agents,
        "task_completion_rate": task_completion_rate,
        "call_success_rate": call_success_rate,
        "completed_tasks": completed_tasks,
        "successful_calls": successful_calls
    }
    
    cache_service.set_json(cache_key, result, ttl=120)
    
    return result

@router.get("/projects")
def get_project_statistics(db: Session = Depends(get_db)):
    cache_key = "statistics:projects"
    cached = cache_service.get_json(cache_key)
    if cached:
        return cached
    
    status_counts = db.query(
        Project.status,
        func.count(Project.id)
    ).group_by(Project.status).all()
    
    total_projects = db.query(func.count(Project.id)).scalar()
    
    status_distribution = {}
    for status, count in status_counts:
        status_distribution[status] = count
    
    result = {
        "total": total_projects,
        "status_distribution": status_distribution
    }
    
    cache_service.set_json(cache_key, result, ttl=120)
    
    return result

@router.get("/tasks")
def get_task_statistics(db: Session = Depends(get_db)):
    cache_key = "statistics:tasks"
    cached = cache_service.get_json(cache_key)
    if cached:
        return cached
    
    status_counts = db.query(
        Task.status,
        func.count(Task.id)
    ).group_by(Task.status).all()
    
    total_tasks = db.query(func.count(Task.id)).scalar()
    completed_tasks = db.query(func.count(Task.id)).filter(
        Task.status == "COMPLETED"
    ).scalar()
    
    status_distribution = {}
    for status, count in status_counts:
        status_distribution[status] = count
    
    completion_rate = 0
    if total_tasks > 0:
        completion_rate = round((completed_tasks / total_tasks) * 100, 2)
    
    result = {
        "total": total_tasks,
        "completed": completed_tasks,
        "completion_rate": completion_rate,
        "status_distribution": status_distribution
    }
    
    cache_service.set_json(cache_key, result, ttl=120)
    
    return result

@router.get("/skill-calls")
def get_skill_call_statistics(db: Session = Depends(get_db)):
    cache_key = "statistics:skill_calls"
    cached = cache_service.get_json(cache_key)
    if cached:
        return cached
    
    status_counts = db.query(
        SkillCall.status,
        func.count(SkillCall.id)
    ).group_by(SkillCall.status).all()
    
    total_calls = db.query(func.count(SkillCall.id)).scalar()
    successful_calls = db.query(func.count(SkillCall.id)).filter(
        SkillCall.status == "completed"
    ).scalar()
    
    skill_call_counts = db.query(
        SkillCall.skill_name,
        func.count(SkillCall.id)
    ).group_by(SkillCall.skill_name).all()
    
    status_distribution = {}
    for status, count in status_counts:
        status_distribution[status] = count
    
    success_rate = 0
    if total_calls > 0:
        success_rate = round((successful_calls / total_calls) * 100, 2)
    
    skill_distribution = {}
    for skill_name, count in skill_call_counts:
        skill_distribution[skill_name] = count
    
    result = {
        "total": total_calls,
        "successful": successful_calls,
        "success_rate": success_rate,
        "status_distribution": status_distribution,
        "skill_distribution": skill_distribution
    }
    
    cache_service.set_json(cache_key, result, ttl=120)
    
    return result

@router.get("/agents")
def get_agent_statistics(db: Session = Depends(get_db)):
    cache_key = "statistics:agents"
    cached = cache_service.get_json(cache_key)
    if cached:
        return cached
    
    status_counts = db.query(
        Agent.status,
        func.count(Agent.id)
    ).group_by(Agent.status).all()
    
    total_agents = db.query(func.count(Agent.id)).scalar()
    active_agents = db.query(func.count(Agent.id)).filter(
        Agent.status == "busy"
    ).scalar()
    
    agent_workload = db.query(
        Agent.name,
        Agent.current_load,
        Agent.max_load
    ).all()
    
    status_distribution = {}
    for status, count in status_counts:
        status_distribution[status] = count
    
    workload_info = []
    for name, current_load, max_load in agent_workload:
        workload_info.append({
            "name": name,
            "current_load": current_load,
            "max_load": max_load,
            "utilization": round((current_load / max_load) * 100, 2) if max_load > 0 else 0
        })
    
    result = {
        "total": total_agents,
        "active": active_agents,
        "status_distribution": status_distribution,
        "workload": workload_info
    }
    
    cache_service.set_json(cache_key, result, ttl=120)
    
    return result
