"""
数据库高级性能测试

测试数据库操作的高级性能特性，包括查询响应时间、并发操作等
"""

import pytest
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from sqlalchemy.orm import joinedload, selectinload

from app.models.project import Project, ProjectStatus
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.agent import Agent
from app.models.department import Department
from app.models.skill_call import SkillCall
from app.models.assignment import Assignment
from app.models.milestone import Milestone


PERFORMANCE_THRESHOLDS = {
    "single_insert": 0.05,
    "bulk_insert_100": 1.0,
    "bulk_insert_1000": 5.0,
    "single_query": 0.02,
    "complex_query": 0.5,
    "join_query": 0.3,
    "aggregation_query": 0.2,
    "pagination_query": 0.1,
}


@pytest.mark.database
@pytest.mark.performance
class TestQueryResponseTime:
    """测试查询响应时间"""

    def test_single_record_insert_time(self, db_session: Session):
        """测试单条记录插入时间"""
        start_time = time.time()
        project = Project(name="性能测试项目")
        db_session.add(project)
        db_session.commit()
        elapsed = time.time() - start_time

        assert elapsed < PERFORMANCE_THRESHOLDS["single_insert"], \
            f"单条插入耗时 {elapsed:.3f}s，超过阈值 {PERFORMANCE_THRESHOLDS['single_insert']}s"

    def test_single_record_query_time(self, db_session: Session):
        """测试单条记录查询时间"""
        project = Project(name="查询测试项目")
        db_session.add(project)
        db_session.commit()

        start_time = time.time()
        found = db_session.query(Project).filter_by(id=project.id).first()
        elapsed = time.time() - start_time

        assert elapsed < PERFORMANCE_THRESHOLDS["single_query"], \
            f"单条查询耗时 {elapsed:.3f}s，超过阈值 {PERFORMANCE_THRESHOLDS['single_query']}s"
        assert found is not None

    def test_bulk_insert_100_time(self, db_session: Session):
        """测试100条记录批量插入时间"""
        projects = [Project(name=f"批量项目{i:04d}") for i in range(100)]

        start_time = time.time()
        db_session.add_all(projects)
        db_session.commit()
        elapsed = time.time() - start_time

        assert elapsed < PERFORMANCE_THRESHOLDS["bulk_insert_100"], \
            f"批量插入100条耗时 {elapsed:.3f}s，超过阈值 {PERFORMANCE_THRESHOLDS['bulk_insert_100']}s"

    def test_bulk_insert_1000_time(self, db_session: Session):
        """测试1000条记录批量插入时间"""
        projects = [Project(name=f"大批量项目{i:05d}") for i in range(1000)]

        start_time = time.time()
        db_session.add_all(projects)
        db_session.commit()
        elapsed = time.time() - start_time

        assert elapsed < PERFORMANCE_THRESHOLDS["bulk_insert_1000"], \
            f"批量插入1000条耗时 {elapsed:.3f}s，超过阈值 {PERFORMANCE_THRESHOLDS['bulk_insert_1000']}s"

    def test_complex_filter_query_time(self, db_session: Session):
        """测试复杂过滤查询时间"""
        for i in range(100):
            project = Project(
                name=f"过滤项目{i:04d}",
                status=ProjectStatus.DEVELOPMENT.value if i % 3 == 0 else ProjectStatus.COMPLETED.value
            )
            db_session.add(project)
        db_session.commit()

        start_time = time.time()
        results = db_session.query(Project).filter(
            Project.status == ProjectStatus.DEVELOPMENT.value,
            Project.name.like("过滤项目%")
        ).all()
        elapsed = time.time() - start_time

        assert elapsed < PERFORMANCE_THRESHOLDS["complex_query"], \
            f"复杂查询耗时 {elapsed:.3f}s，超过阈值 {PERFORMANCE_THRESHOLDS['complex_query']}s"
        assert len(results) == 34

    def test_join_query_time(self, db_session: Session):
        """测试连接查询时间"""
        project = Project(name="连接测试项目")
        agent = Agent(name="连接测试代理")
        db_session.add_all([project, agent])
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

        assert elapsed < PERFORMANCE_THRESHOLDS["join_query"], \
            f"连接查询耗时 {elapsed:.3f}s，超过阈值 {PERFORMANCE_THRESHOLDS['join_query']}s"
        assert len(results) == 50

    def test_aggregation_query_time(self, db_session: Session):
        """测试聚合查询时间"""
        project = Project(name="聚合测试项目")
        db_session.add(project)
        db_session.commit()

        for i in range(100):
            task = Task(
                title=f"聚合任务{i}",
                project_id=project.id,
                status=TaskStatus.COMPLETED.value if i < 60 else TaskStatus.PENDING.value,
                priority=TaskPriority.HIGH.value if i % 2 == 0 else TaskPriority.LOW.value
            )
            db_session.add(task)
        db_session.commit()

        start_time = time.time()
        result = db_session.query(
            Task.status,
            Task.priority,
            func.count(Task.id)
        ).filter(
            Task.project_id == project.id
        ).group_by(Task.status, Task.priority).all()
        elapsed = time.time() - start_time

        assert elapsed < PERFORMANCE_THRESHOLDS["aggregation_query"], \
            f"聚合查询耗时 {elapsed:.3f}s，超过阈值 {PERFORMANCE_THRESHOLDS['aggregation_query']}s"
        assert len(result) > 0

    def test_pagination_query_time(self, db_session: Session):
        """测试分页查询时间"""
        for i in range(500):
            project = Project(name=f"分页项目{i:05d}")
            db_session.add(project)
        db_session.commit()

        page_size = 20
        page_times = []

        for page in range(5):
            offset = page * page_size
            start_time = time.time()
            results = db_session.query(Project).order_by(
                Project.created_at.desc()
            ).offset(offset).limit(page_size).all()
            elapsed = time.time() - start_time
            page_times.append(elapsed)

            assert len(results) == page_size

        avg_time = sum(page_times) / len(page_times)
        assert avg_time < PERFORMANCE_THRESHOLDS["pagination_query"], \
            f"平均分页查询耗时 {avg_time:.3f}s，超过阈值 {PERFORMANCE_THRESHOLDS['pagination_query']}s"


@pytest.mark.database
@pytest.mark.performance
class TestIndexPerformance:
    """测试索引性能"""

    def test_index_on_status_column(self, db_session: Session):
        """测试状态列索引效果"""
        for i in range(200):
            status = [ProjectStatus.REQUIREMENT, ProjectStatus.DEVELOPMENT, 
                     ProjectStatus.TESTING, ProjectStatus.COMPLETED][i % 4]
            project = Project(
                name=f"索引状态项目{i:04d}",
                status=status.value
            )
            db_session.add(project)
        db_session.commit()

        start_time = time.time()
        results = db_session.query(Project).filter(
            Project.status == ProjectStatus.DEVELOPMENT.value
        ).all()
        elapsed = time.time() - start_time

        assert elapsed < 0.1, f"状态索引查询耗时 {elapsed:.3f}s"
        assert len(results) == 50

    def test_index_on_created_at_column(self, db_session: Session):
        """测试创建时间列索引效果"""
        now = datetime.utcnow()
        for i in range(200):
            project = Project(
                name=f"时间索引项目{i:04d}",
                created_at=now - timedelta(days=i)
            )
            db_session.add(project)
        db_session.commit()

        start_time = time.time()
        results = db_session.query(Project).filter(
            Project.created_at >= now - timedelta(days=30)
        ).all()
        elapsed = time.time() - start_time

        assert elapsed < 0.1, f"时间索引查询耗时 {elapsed:.3f}s"
        assert len(results) == 31

    def test_composite_index_performance(self, db_session: Session):
        """测试复合索引性能"""
        project = Project(name="复合索引项目")
        db_session.add(project)
        db_session.commit()

        for i in range(100):
            task = Task(
                title=f"复合索引任务{i}",
                project_id=project.id,
                status=TaskStatus.PENDING.value if i % 2 == 0 else TaskStatus.COMPLETED.value,
                priority=TaskPriority.HIGH.value if i % 3 == 0 else TaskPriority.MEDIUM.value
            )
            db_session.add(task)
        db_session.commit()

        start_time = time.time()
        results = db_session.query(Task).filter(
            Task.project_id == project.id,
            Task.status == TaskStatus.PENDING.value
        ).all()
        elapsed = time.time() - start_time

        assert elapsed < 0.1, f"复合索引查询耗时 {elapsed:.3f}s"


@pytest.mark.database
@pytest.mark.performance
class TestRelationshipLoading:
    """测试关系加载性能"""

    def test_eager_loading_performance(self, db_session: Session):
        """测试预加载性能"""
        project = Project(name="预加载项目")
        agent = Agent(name="预加载代理")
        db_session.add_all([project, agent])
        db_session.commit()

        for i in range(50):
            task = Task(
                title=f"预加载任务{i}",
                project_id=project.id,
                agent_id=agent.id
            )
            db_session.add(task)
        db_session.commit()

        start_time = time.time()
        tasks = db_session.query(Task).options(
            joinedload(Task.project),
            joinedload(Task.agent)
        ).filter(Task.project_id == project.id).all()
        elapsed = time.time() - start_time

        assert elapsed < 0.3, f"预加载耗时 {elapsed:.3f}s"
        assert len(tasks) == 50

        for task in tasks:
            assert task.project is not None
            assert task.agent is not None

    def test_lazy_loading_overhead(self, db_session: Session):
        """测试延迟加载开销"""
        project = Project(name="延迟加载项目")
        agent = Agent(name="延迟加载代理")
        db_session.add_all([project, agent])
        db_session.commit()

        for i in range(20):
            task = Task(
                title=f"延迟加载任务{i}",
                project_id=project.id,
                agent_id=agent.id
            )
            db_session.add(task)
        db_session.commit()

        start_time = time.time()
        tasks = db_session.query(Task).filter(Task.project_id == project.id).all()
        query_time = time.time() - start_time

        start_time = time.time()
        for task in tasks:
            _ = task.project.name
            _ = task.agent.name
        access_time = time.time() - start_time

        assert query_time < 0.1, f"延迟加载查询耗时 {query_time:.3f}s"
        assert access_time < 0.5, f"延迟加载访问耗时 {access_time:.3f}s"


@pytest.mark.database
@pytest.mark.performance
class TestBulkOperations:
    """测试批量操作性能"""

    def test_bulk_update_performance(self, db_session: Session):
        """测试批量更新性能"""
        for i in range(100):
            project = Project(
                name=f"更新项目{i:04d}",
                status=ProjectStatus.REQUIREMENT.value
            )
            db_session.add(project)
        db_session.commit()

        start_time = time.time()
        db_session.query(Project).filter(
            Project.name.like("更新项目%")
        ).update(
            {"status": ProjectStatus.DEVELOPMENT.value},
            synchronize_session=False
        )
        db_session.commit()
        elapsed = time.time() - start_time

        assert elapsed < 1.0, f"批量更新耗时 {elapsed:.3f}s"

        updated_count = db_session.query(Project).filter(
            Project.status == ProjectStatus.DEVELOPMENT.value
        ).count()
        assert updated_count == 100

    def test_bulk_delete_performance(self, db_session: Session):
        """测试批量删除性能"""
        for i in range(100):
            project = Project(name=f"删除项目{i:04d}")
            db_session.add(project)
        db_session.commit()

        start_time = time.time()
        deleted = db_session.query(Project).filter(
            Project.name.like("删除项目%")
        ).delete(synchronize_session=False)
        db_session.commit()
        elapsed = time.time() - start_time

        assert elapsed < 1.0, f"批量删除耗时 {elapsed:.3f}s"
        assert deleted == 100

    def test_bulk_insert_with_relationships(self, db_session: Session):
        """测试带关系的批量插入"""
        project = Project(name="批量关系项目")
        db_session.add(project)
        db_session.commit()

        tasks = [
            Task(
                title=f"批量关系任务{i}",
                project_id=project.id,
                status=TaskStatus.PENDING.value
            )
            for i in range(100)
        ]

        start_time = time.time()
        db_session.add_all(tasks)
        db_session.commit()
        elapsed = time.time() - start_time

        assert elapsed < 1.0, f"带关系批量插入耗时 {elapsed:.3f}s"


@pytest.mark.database
@pytest.mark.performance
class TestTransactionPerformance:
    """测试事务性能"""

    def test_single_transaction_performance(self, db_session: Session):
        """测试单事务性能"""
        start_time = time.time()

        for i in range(50):
            project = Project(name=f"事务项目{i:04d}")
            db_session.add(project)
        db_session.commit()

        elapsed = time.time() - start_time
        assert elapsed < 1.0, f"单事务插入50条耗时 {elapsed:.3f}s"

    def test_rollback_performance(self, db_session: Session):
        """测试回滚性能"""
        for i in range(50):
            project = Project(name=f"回滚前项目{i:04d}")
            db_session.add(project)
        db_session.commit()

        start_time = time.time()

        for i in range(50):
            project = Project(name=f"回滚项目{i:04d}")
            db_session.add(project)

        db_session.rollback()
        elapsed = time.time() - start_time

        assert elapsed < 0.5, f"回滚耗时 {elapsed:.3f}s"

        count = db_session.query(Project).filter(
            Project.name.like("回滚项目%")
        ).count()
        assert count == 0


@pytest.mark.database
@pytest.mark.performance
class TestComplexQueryPerformance:
    """测试复杂查询性能"""

    def test_subquery_performance(self, db_session: Session):
        """测试子查询性能"""
        for i in range(50):
            project = Project(name=f"子查询项目{i:04d}")
            db_session.add(project)
        db_session.commit()

        projects = db_session.query(Project).filter(
            Project.name.like("子查询项目%")
        ).all()

        for project in projects:
            for j in range(5):
                task = Task(
                    title=f"子查询任务{project.id}_{j}",
                    project_id=project.id,
                    status=TaskStatus.COMPLETED.value if j % 2 == 0 else TaskStatus.PENDING.value
                )
                db_session.add(task)
        db_session.commit()

        start_time = time.time()
        subquery = db_session.query(Task.project_id).filter(
            Task.status == TaskStatus.COMPLETED.value
        ).distinct()

        results = db_session.query(Project).filter(
            Project.id.in_(subquery)
        ).all()
        elapsed = time.time() - start_time

        assert elapsed < 0.5, f"子查询耗时 {elapsed:.3f}s"
        assert len(results) == 50

    def test_union_query_performance(self, db_session: Session):
        """测试联合查询性能"""
        project = Project(name="联合查询项目")
        db_session.add(project)
        db_session.commit()

        for i in range(50):
            task = Task(
                title=f"联合任务{i}",
                project_id=project.id,
                status=TaskStatus.PENDING.value if i < 25 else TaskStatus.COMPLETED.value
            )
            db_session.add(task)
        db_session.commit()

        start_time = time.time()
        pending = db_session.query(Task).filter(
            Task.status == TaskStatus.PENDING.value
        )
        completed = db_session.query(Task).filter(
            Task.status == TaskStatus.COMPLETED.value
        )

        results = pending.union(completed).all()
        elapsed = time.time() - start_time

        assert elapsed < 0.3, f"联合查询耗时 {elapsed:.3f}s"
        assert len(results) == 50

    def test_window_function_performance(self, db_session: Session):
        """测试窗口函数性能"""
        project = Project(name="窗口函数项目")
        db_session.add(project)
        db_session.commit()

        for i in range(100):
            task = Task(
                title=f"窗口任务{i}",
                project_id=project.id,
                estimated_hours=float(i % 10 + 1)
            )
            db_session.add(task)
        db_session.commit()

        start_time = time.time()
        results = db_session.query(
            Task,
            func.row_number().over(
                order_by=Task.estimated_hours.desc()
            ).label("rank")
        ).filter(
            Task.project_id == project.id
        ).limit(10).all()
        elapsed = time.time() - start_time

        assert elapsed < 0.5, f"窗口函数查询耗时 {elapsed:.3f}s"
        assert len(results) == 10


@pytest.mark.database
@pytest.mark.performance
class TestDatabaseStats:
    """测试数据库统计"""

    def test_record_count_performance(self, db_session: Session):
        """测试记录计数性能"""
        for i in range(1000):
            project = Project(name=f"计数项目{i:05d}")
            db_session.add(project)
        db_session.commit()

        start_time = time.time()
        count = db_session.query(Project).filter(
            Project.name.like("计数项目%")
        ).count()
        elapsed = time.time() - start_time

        assert elapsed < 0.2, f"计数查询耗时 {elapsed:.3f}s"
        assert count == 1000

    def test_distinct_query_performance(self, db_session: Session):
        """测试去重查询性能"""
        for i in range(100):
            project = Project(
                name=f"去重项目{i:04d}",
                status=[ProjectStatus.REQUIREMENT, ProjectStatus.DEVELOPMENT, 
                       ProjectStatus.TESTING][i % 3].value
            )
            db_session.add(project)
        db_session.commit()

        start_time = time.time()
        statuses = db_session.query(Project.status).distinct().all()
        elapsed = time.time() - start_time

        assert elapsed < 0.1, f"去重查询耗时 {elapsed:.3f}s"
        assert len(statuses) == 3

    def test_exists_query_performance(self, db_session: Session):
        """测试存在性查询性能"""
        for i in range(100):
            project = Project(name=f"存在项目{i:04d}")
            db_session.add(project)
        db_session.commit()

        start_time = time.time()
        exists = db_session.query(Project).filter(
            Project.name == "存在项目0050"
        ).first() is not None
        elapsed = time.time() - start_time

        assert elapsed < 0.05, f"存在性查询耗时 {elapsed:.3f}s"
        assert exists is True
