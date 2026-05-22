"""
数据库性能测试

测试数据库操作的性能特性
"""

import pytest
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from app.models.project import Project, ProjectStatus
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.agent import Agent
from app.models.skill_call import SkillCall
from app.models.milestone import Milestone


@pytest.mark.database
@pytest.mark.performance
class TestDatabasePerformance:
    """测试数据库性能"""

    def test_bulk_insert_performance(self, db_session: Session):
        """测试批量插入性能"""
        projects = [
            Project(name=f"批量项目{i:04d}")
            for i in range(100)
        ]

        start_time = time.time()
        db_session.add_all(projects)
        db_session.commit()
        elapsed = time.time() - start_time

        assert elapsed < 2.0, f"批量插入100条记录耗时 {elapsed:.2f}s，超过预期"
        assert len(projects) == 100

    def test_bulk_query_performance(self, db_session: Session):
        """测试批量查询性能"""
        for i in range(100):
            project = Project(name=f"查询项目{i:04d}")
            db_session.add(project)
        db_session.commit()

        start_time = time.time()
        results = db_session.query(Project).filter(
            Project.name.like("查询项目%")
        ).limit(50).all()
        elapsed = time.time() - start_time

        assert elapsed < 0.5, f"查询50条记录耗时 {elapsed:.2f}s，超过预期"
        assert len(results) == 50

    def test_complex_join_performance(self, db_session: Session):
        """测试复杂连接查询性能"""
        project = Project(name="连接测试项目")
        db_session.add(project)
        db_session.commit()

        agent = Agent(name="连接测试代理")
        db_session.add(agent)
        db_session.commit()

        for i in range(50):
            task = Task(
                title=f"连接任务{i}",
                project_id=project.id,
                agent_id=agent.id
            )
            db_session.add(task)
        db_session.commit()

        start_time = time.time()
        results = db_session.query(Task).join(Project).join(Agent).filter(
            Project.id == project.id
        ).all()
        elapsed = time.time() - start_time

        assert elapsed < 1.0, f"复杂连接查询耗时 {elapsed:.2f}s，超过预期"
        assert len(results) == 50

    def test_index_usage(self, db_session: Session):
        """测试索引使用"""
        for i in range(100):
            project = Project(
                name=f"索引项目{i:04d}",
                status=ProjectStatus.DEVELOPMENT.value if i % 2 == 0 else ProjectStatus.COMPLETED.value
            )
            db_session.add(project)
        db_session.commit()

        start_time = time.time()
        results = db_session.query(Project).filter(
            Project.status == ProjectStatus.DEVELOPMENT.value
        ).all()
        elapsed = time.time() - start_time

        assert elapsed < 0.5, f"索引查询耗时 {elapsed:.2f}s，超过预期"
        assert len(results) == 50


@pytest.mark.database
@pytest.mark.performance
class TestDatabaseConcurrency:
    """测试数据库并发"""

    def test_concurrent_reads(self, db_session: Session):
        """测试并发读取"""
        for i in range(50):
            project = Project(name=f"并发读取项目{i}")
            db_session.add(project)
        db_session.commit()

        results = []
        for _ in range(10):
            items = db_session.query(Project).limit(10).all()
            results.append(len(items))

        assert all(r == 10 for r in results)

    def test_transaction_isolation(self, db_session: Session):
        """测试事务隔离"""
        project = Project(name="隔离测试项目")
        db_session.add(project)
        db_session.commit()

        project_id = project.id

        project.status = ProjectStatus.DEVELOPMENT.value
        db_session.flush()

        same_project = db_session.query(Project).filter_by(id=project_id).first()
        assert same_project.status == ProjectStatus.DEVELOPMENT.value


@pytest.mark.database
@pytest.mark.performance
class TestDatabaseMemory:
    """测试数据库内存使用"""

    def test_large_json_field(self, db_session: Session):
        """测试大型JSON字段"""
        large_tech_stack = [f"技术{i}" for i in range(100)]
        large_status_history = [
            {
                "status": f"STATUS_{i}",
                "timestamp": datetime.utcnow().isoformat(),
                "comment": "这是一个很长的注释" * 10
            }
            for i in range(50)
        ]

        project = Project(
            name="大型JSON项目",
            tech_stack=large_tech_stack,
            status_history=large_status_history
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert len(project.tech_stack) == 100
        assert len(project.status_history) == 50

    def test_many_relationships(self, db_session: Session):
        """测试多关系查询"""
        project = Project(name="多关系项目")
        db_session.add(project)
        db_session.commit()

        for i in range(100):
            task = Task(
                title=f"关系任务{i}",
                project_id=project.id
            )
            db_session.add(task)
        db_session.commit()

        db_session.refresh(project)
        task_count = db_session.query(Task).filter(
            Task.project_id == project.id
        ).count()

        assert task_count == 100


@pytest.mark.database
@pytest.mark.performance
class TestQueryOptimization:
    """测试查询优化"""

    def test_eager_loading(self, db_session: Session):
        """测试预加载"""
        from sqlalchemy.orm import joinedload

        project = Project(name="预加载项目")
        db_session.add(project)
        db_session.commit()

        for i in range(20):
            task = Task(title=f"预加载任务{i}", project_id=project.id)
            db_session.add(task)
        db_session.commit()

        start_time = time.time()
        results = db_session.query(Task).options(
            joinedload(Task.project)
        ).filter(Task.project_id == project.id).all()
        elapsed = time.time() - start_time

        assert elapsed < 0.5
        assert len(results) == 20

    def test_lazy_loading(self, db_session: Session):
        """测试延迟加载"""
        project = Project(name="延迟加载项目")
        db_session.add(project)
        db_session.commit()

        for i in range(20):
            task = Task(title=f"延迟加载任务{i}", project_id=project.id)
            db_session.add(task)
        db_session.commit()

        start_time = time.time()
        tasks = db_session.query(Task).filter(Task.project_id == project.id).all()
        elapsed = time.time() - start_time

        assert elapsed < 0.5
        assert len(tasks) == 20

    def test_pagination_efficiency(self, db_session: Session):
        """测试分页效率"""
        for i in range(1000):
            project = Project(name=f"分页项目{i:05d}")
            db_session.add(project)
        db_session.commit()

        page_size = 20
        total = db_session.query(Project).count()

        for page in range(5):
            offset = page * page_size
            start_time = time.time()
            results = db_session.query(Project).offset(offset).limit(page_size).all()
            elapsed = time.time() - start_time

            assert elapsed < 0.1, f"第{page+1}页查询耗时 {elapsed:.2f}s"
            assert len(results) == page_size


@pytest.mark.database
@pytest.mark.performance
class TestDatabaseCleanup:
    """测试数据库清理"""

    def test_delete_cascade_performance(self, db_session: Session):
        """测试级联删除性能"""
        project = Project(name="级联删除性能项目")
        db_session.add(project)
        db_session.commit()

        for i in range(100):
            task = Task(title=f"删除任务{i}", project_id=project.id)
            db_session.add(task)
        db_session.commit()

        start_time = time.time()
        db_session.delete(project)
        db_session.commit()
        elapsed = time.time() - start_time

        assert elapsed < 1.0, f"级联删除耗时 {elapsed:.2f}s"

        deleted = db_session.query(Project).filter_by(id=project.id).first()
        assert deleted is None

    def test_bulk_delete_performance(self, db_session: Session):
        """测试批量删除性能"""
        for i in range(100):
            project = Project(name=f"批量删除项目{i}")
            db_session.add(project)
        db_session.commit()

        start_time = time.time()
        deleted = db_session.query(Project).filter(
            Project.name.like("批量删除项目%")
        ).delete()
        db_session.commit()
        elapsed = time.time() - start_time

        assert elapsed < 1.0, f"批量删除耗时 {elapsed:.2f}s"
        assert deleted == 100


@pytest.mark.database
@pytest.mark.performance
class TestDatabaseAggregation:
    """测试数据库聚合"""

    def test_count_aggregation(self, db_session: Session):
        """测试计数聚合"""
        project = Project(name="计数聚合项目")
        db_session.add(project)
        db_session.commit()

        for i in range(50):
            status = TaskStatus.COMPLETED.value if i < 30 else TaskStatus.PENDING.value
            task = Task(title=f"计数任务{i}", project_id=project.id, status=status)
            db_session.add(task)
        db_session.commit()

        start_time = time.time()
        completed_count = db_session.query(Task).filter(
            Task.project_id == project.id,
            Task.status == TaskStatus.COMPLETED.value
        ).count()
        elapsed = time.time() - start_time

        assert elapsed < 0.1
        assert completed_count == 30

    def test_group_by_aggregation(self, db_session: Session):
        """测试分组聚合"""
        project = Project(name="分组聚合项目")
        db_session.add(project)
        db_session.commit()

        for i in range(30):
            priority = ["high", "medium", "low"][i % 3]
            task = Task(
                title=f"分组任务{i}",
                project_id=project.id,
                priority=priority
            )
            db_session.add(task)
        db_session.commit()

        start_time = time.time()
        from sqlalchemy import func
        results = db_session.query(
            Task.priority,
            func.count(Task.id)
        ).filter(
            Task.project_id == project.id
        ).group_by(Task.priority).all()
        elapsed = time.time() - start_time

        assert elapsed < 0.5
        assert len(results) == 3

        priority_counts = {r[0]: r[1] for r in results}
        assert priority_counts["high"] == 10
        assert priority_counts["medium"] == 10
        assert priority_counts["low"] == 10

    def test_date_aggregation(self, db_session: Session):
        """测试日期聚合"""
        now = datetime.utcnow()

        for i in range(30):
            days_ago = i
            project = Project(
                name=f"日期项目{i}",
                created_at=now - timedelta(days=days_ago)
            )
            db_session.add(project)
        db_session.commit()

        start_time = time.time()
        from sqlalchemy import func
        recent_count = db_session.query(Project).filter(
            Project.created_at >= now - timedelta(days=7)
        ).count()
        elapsed = time.time() - start_time

        assert elapsed < 0.1
        assert recent_count == 8
