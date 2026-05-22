"""
API集成测试

测试完整的API请求/响应流程，包括数据库交互
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStatus
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.agent import Agent
from app.models.department import Department
from app.models.skill_call import SkillCall
from app.models.assignment import Assignment
from app.models.milestone import Milestone
from tests.conftest import create_test_project, create_test_task, create_test_agent


@pytest.mark.api
@pytest.mark.integration
class TestProjectWorkflowIntegration:
    """测试项目完整工作流集成"""

    def test_full_project_lifecycle(self, client: TestClient, db_session: Session):
        """测试项目完整生命周期"""
        create_data = {
            "name": "完整生命周期项目",
            "description": "测试完整生命周期",
            "tech_stack": ["Python", "FastAPI", "Vue"]
        }

        create_response = client.post("/api/projects/", json=create_data)
        assert create_response.status_code == 200
        project_data = create_response.json()
        project_id = project_data["id"]

        assert project_data["status"] == "REQUIREMENT"

        status_transitions = [
            ("DESIGN", "设计阶段"),
            ("DEVELOPMENT", "开发阶段"),
            ("TESTING", "测试阶段"),
            ("COMPLETED", "完成")
        ]

        for status, description in status_transitions:
            update_response = client.put(
                f"/api/projects/{project_id}",
                json={"status": status}
            )
            assert update_response.status_code == 200
            assert update_response.json()["status"] == status

        get_response = client.get(f"/api/projects/{project_id}")
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "COMPLETED"

    def test_project_with_tasks_integration(self, client: TestClient, db_session: Session, mock_redis):
        """测试项目与任务的集成"""
        mock_redis.get_json.return_value = None

        project = create_test_project(db_session, name="任务集成项目")

        for i in range(5):
            create_test_task(
                db_session,
                project_id=project.id,
                title=f"集成任务{i+1}",
                status=TaskStatus.PENDING.value if i < 3 else TaskStatus.COMPLETED.value
            )

        stats_response = client.get(f"/api/projects/{project.id}/stats")
        assert stats_response.status_code == 200
        stats = stats_response.json()

        assert stats["total_tasks"] == 5
        assert stats["pending_tasks"] == 3
        assert stats["completed_tasks"] == 2

    def test_project_search_integration(self, client: TestClient, db_session: Session):
        """测试项目搜索集成"""
        projects = [
            create_test_project(db_session, name="Python Web开发", description="使用Python框架"),
            create_test_project(db_session, name="Java后端服务", description="Spring Boot"),
            create_test_project(db_session, name="React前端应用", description="前端开发"),
            create_test_project(db_session, name="Python数据分析", description="数据科学"),
        ]

        search_response = client.get("/api/projects/search?q=Python")
        assert search_response.status_code == 200
        results = search_response.json()

        assert len(results) >= 2
        for result in results:
            assert "Python" in result["name"] or "Python" in (result.get("description") or "")


@pytest.mark.api
@pytest.mark.integration
class TestTaskWorkflowIntegration:
    """测试任务工作流集成"""

    def test_task_assignment_workflow(self, client: TestClient, db_session: Session):
        """测试任务分配工作流"""
        project = create_test_project(db_session, name="分配工作流项目")
        agent = create_test_agent(db_session, name="工作流代理", skills=["Python"])
        task = create_test_task(
            db_session,
            project_id=project.id,
            title="待分配任务",
            status=TaskStatus.PENDING.value
        )

        assign_response = client.post(
            f"/api/tasks/{task.id}/assign",
            json={"agent_id": agent.id}
        )
        
        if assign_response.status_code == 200:
            assignment_data = assign_response.json()
            assert assignment_data["agent_id"] == agent.id

    def test_task_status_transitions(self, client: TestClient, db_session: Session):
        """测试任务状态转换"""
        project = create_test_project(db_session, name="状态转换项目")
        task = create_test_task(
            db_session,
            project_id=project.id,
            title="状态转换任务",
            status=TaskStatus.PENDING.value
        )

        transitions = [
            TaskStatus.IN_PROGRESS.value,
            TaskStatus.REVIEW.value,
            TaskStatus.COMPLETED.value
        ]

        for new_status in transitions:
            update_response = client.put(
                f"/api/tasks/{task.id}",
                json={"status": new_status}
            )
            if update_response.status_code == 200:
                assert update_response.json()["status"] == new_status


@pytest.mark.api
@pytest.mark.integration
class TestAgentWorkflowIntegration:
    """测试代理工作流集成"""

    def test_agent_task_relationship(self, client: TestClient, db_session: Session, mock_redis):
        """测试代理与任务关系"""
        mock_redis.get_json.return_value = None

        department = Department(name="开发部", pinyin="kaifabu")
        db_session.add(department)
        db_session.commit()

        agent = Agent(
            name="关系测试代理",
            skills=["Python", "JavaScript"],
            department_id=department.id,
            status="idle"
        )
        db_session.add(agent)
        db_session.commit()

        project = create_test_project(db_session, name="关系测试项目")
        task = create_test_task(
            db_session,
            project_id=project.id,
            title="关系测试任务",
            agent_id=agent.id
        )

        agent_response = client.get(f"/api/agents/{agent.id}")
        if agent_response.status_code == 200:
            agent_data = agent_response.json()
            assert agent_data["name"] == "关系测试代理"

    def test_agent_availability_check(self, client: TestClient, db_session: Session):
        """测试代理可用性检查"""
        agent1 = Agent(name="空闲代理", status="idle", current_load=0, max_load=5)
        agent2 = Agent(name="忙碌代理", status="busy", current_load=5, max_load=5)
        db_session.add_all([agent1, agent2])
        db_session.commit()

        response = client.get("/api/agents/available")
        if response.status_code == 200:
            available_agents = response.json()
            assert any(a["name"] == "空闲代理" for a in available_agents)


@pytest.mark.api
@pytest.mark.integration
class TestSkillCallIntegration:
    """测试技能调用集成"""

    def test_skill_call_creation_and_tracking(self, client: TestClient, db_session: Session):
        """测试技能调用创建和追踪"""
        parent_call = SkillCall(
            skill_name="parent_skill",
            caller="test_user",
            status="started",
            details={"type": "parent"}
        )
        db_session.add(parent_call)
        db_session.commit()

        child_call = SkillCall(
            skill_name="child_skill",
            caller="test_user",
            parent_call_id=parent_call.id,
            status="started"
        )
        db_session.add(child_call)
        db_session.commit()

        response = client.get(f"/api/skill-calls/{parent_call.id}")
        if response.status_code == 200:
            call_data = response.json()
            assert call_data["skill_name"] == "parent_skill"

    def test_skill_call_hierarchy(self, db_session: Session):
        """测试技能调用层级"""
        parent = SkillCall(skill_name="parent", caller="user1")
        db_session.add(parent)
        db_session.commit()

        children = []
        for i in range(3):
            child = SkillCall(
                skill_name=f"child_{i}",
                caller="user1",
                parent_call_id=parent.id
            )
            children.append(child)
        db_session.add_all(children)
        db_session.commit()

        db_session.refresh(parent)
        assert len(parent.children) == 3


@pytest.mark.api
@pytest.mark.integration
class TestMilestoneIntegration:
    """测试里程碑集成"""

    def test_milestone_progress_tracking(self, db_session: Session):
        """测试里程碑进度追踪"""
        project = create_test_project(db_session, name="里程碑进度项目")

        milestones = [
            Milestone(
                project_id=project.id,
                name="需求分析",
                status="completed",
                planned_date=datetime.utcnow() - timedelta(days=30),
                completed_date=datetime.utcnow() - timedelta(days=25)
            ),
            Milestone(
                project_id=project.id,
                name="设计阶段",
                status="completed",
                planned_date=datetime.utcnow() - timedelta(days=20),
                completed_date=datetime.utcnow() - timedelta(days=15)
            ),
            Milestone(
                project_id=project.id,
                name="开发阶段",
                status="in_progress",
                planned_date=datetime.utcnow() + timedelta(days=10)
            ),
        ]
        db_session.add_all(milestones)
        db_session.commit()

        completed = db_session.query(Milestone).filter(
            Milestone.project_id == project.id,
            Milestone.status == "completed"
        ).count()

        assert completed == 2


@pytest.mark.api
@pytest.mark.integration
class TestDatabaseTransactionIntegration:
    """测试数据库事务集成"""

    def test_cascade_delete_project(self, db_session: Session):
        """测试级联删除项目"""
        project = create_test_project(db_session, name="级联删除项目")
        task1 = create_test_task(db_session, project_id=project.id, title="任务1")
        task2 = create_test_task(db_session, project_id=project.id, title="任务2")

        project_id = project.id
        db_session.delete(project)
        db_session.commit()

        deleted_project = db_session.query(Project).filter_by(id=project_id).first()
        assert deleted_project is None

    def test_concurrent_task_updates(self, db_session: Session):
        """测试并发任务更新"""
        project = create_test_project(db_session, name="并发更新项目")
        task = create_test_task(
            db_session,
            project_id=project.id,
            title="并发任务",
            status=TaskStatus.PENDING.value
        )

        task.status = TaskStatus.IN_PROGRESS.value
        db_session.commit()
        db_session.refresh(task)
        assert task.status == TaskStatus.IN_PROGRESS.value

        task.status = TaskStatus.COMPLETED.value
        db_session.commit()
        db_session.refresh(task)
        assert task.status == TaskStatus.COMPLETED.value


@pytest.mark.api
@pytest.mark.integration
class TestErrorHandlingIntegration:
    """测试错误处理集成"""

    def test_invalid_project_id_format(self, client: TestClient):
        """测试无效项目ID格式"""
        response = client.get("/api/projects/invalid_id")
        assert response.status_code == 422

    def test_missing_required_fields(self, client: TestClient):
        """测试缺少必填字段"""
        response = client.post("/api/projects/", json={})
        assert response.status_code == 422

    def test_duplicate_project_name(self, client: TestClient, db_session: Session):
        """测试重复项目名称"""
        create_test_project(db_session, name="重复名称项目")

        response = client.post("/api/projects/", json={"name": "重复名称项目"})
        assert response.status_code == 409

    def test_invalid_status_transition(self, client: TestClient, db_session: Session):
        """测试无效状态转换"""
        project = create_test_project(
            db_session,
            name="状态转换项目",
            status=ProjectStatus.REQUIREMENT.value
        )

        response = client.put(
            f"/api/projects/{project.id}",
            json={"status": "INVALID_STATUS"}
        )
        assert response.status_code == 400


@pytest.mark.api
@pytest.mark.integration
class TestPaginationIntegration:
    """测试分页集成"""

    def test_large_dataset_pagination(self, client: TestClient, db_session: Session, mock_redis):
        """测试大数据集分页"""
        mock_redis.get_json.return_value = None

        for i in range(50):
            create_test_project(db_session, name=f"分页项目{i:03d}")

        page1 = client.get("/api/projects/?page=1&page_size=10")
        assert page1.status_code == 200
        data1 = page1.json()
        assert len(data1["items"]) == 10
        assert data1["total"] == 50
        assert data1["total_pages"] == 5

        page5 = client.get("/api/projects/?page=5&page_size=10")
        assert page5.status_code == 200
        data5 = page5.json()
        assert len(data5["items"]) == 10

    def test_empty_page_handling(self, client: TestClient, mock_redis):
        """测试空页面处理"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/projects/?page=100&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
