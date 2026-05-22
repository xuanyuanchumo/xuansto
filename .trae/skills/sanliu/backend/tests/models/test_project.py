"""
项目模型测试

测试 Project 模型的创建、属性、关系和行为
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStatus, PROJECT_STATUS_TRANSITIONS
from app.models.base import Base


@pytest.mark.model
@pytest.mark.unit
class TestProjectModel:
    """测试 Project 模型的基本功能"""

    def test_project_creation(self, db_session: Session):
        """测试创建项目实例"""
        project = Project(
            name="测试项目",
            description="这是一个测试项目",
            tech_stack=["Python", "FastAPI"]
        )

        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert project.id is not None
        assert project.name == "测试项目"
        assert project.description == "这是一个测试项目"
        assert project.tech_stack == ["Python", "FastAPI"]
        assert project.status == ProjectStatus.REQUIREMENT.value
        assert project.created_at is not None

    def test_project_default_status(self, db_session: Session):
        """测试项目默认状态为 REQUIREMENT"""
        project = Project(name="默认状态项目")

        db_session.add(project)
        db_session.commit()

        assert project.status == ProjectStatus.REQUIREMENT.value

    def test_project_status_history_default(self, db_session: Session):
        """测试项目状态历史默认为空列表"""
        project = Project(name="历史测试项目")

        db_session.add(project)
        db_session.commit()

        assert project.status_history == []
        assert project.milestones == []

    def test_project_name_constraint(self, db_session: Session):
        """测试项目名称约束"""
        # 创建第一个项目
        project1 = Project(name="唯一名称")
        db_session.add(project1)
        db_session.commit()

        # 创建同名项目（在数据库层面应该允许，但在应用层面应该阻止）
        project2 = Project(name="唯一名称")
        db_session.add(project2)
        db_session.commit()

        # 验证两个项目都存在于数据库中
        projects = db_session.query(Project).filter_by(name="唯一名称").all()
        assert len(projects) == 2

    def test_project_tech_stack_json(self, db_session: Session):
        """测试技术栈 JSON 存储"""
        tech_stack = ["Python", "FastAPI", "SQLAlchemy", "PostgreSQL"]
        project = Project(
            name="技术栈测试项目",
            tech_stack=tech_stack
        )

        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert project.tech_stack == tech_stack
        assert isinstance(project.tech_stack, list)

    def test_project_update(self, db_session: Session):
        """测试更新项目"""
        project = Project(name="更新前名称")
        db_session.add(project)
        db_session.commit()

        # 更新项目
        project.name = "更新后名称"
        project.description = "更新后的描述"
        db_session.commit()
        db_session.refresh(project)

        assert project.name == "更新后名称"
        assert project.description == "更新后的描述"
        assert project.updated_at is not None

    def test_project_with_long_name(self, db_session: Session):
        """测试使用长名称创建项目"""
        project = Project(name="A" * 200)
        db_session.add(project)
        db_session.commit()

        assert project.name == "A" * 200

    def test_project_with_unicode_name(self, db_session: Session):
        """测试使用 Unicode 名称创建项目"""
        project = Project(name="🚀 项目 日本語 한국어")
        db_session.add(project)
        db_session.commit()

        assert project.name == "🚀 项目 日本語 한국어"


@pytest.mark.model
@pytest.mark.unit
class TestProjectStatusEnum:
    """测试项目状态枚举"""

    def test_status_enum_values(self):
        """测试状态枚举值"""
        assert ProjectStatus.REQUIREMENT.value == "REQUIREMENT"
        assert ProjectStatus.DESIGN.value == "DESIGN"
        assert ProjectStatus.DEVELOPMENT.value == "DEVELOPMENT"
        assert ProjectStatus.TESTING.value == "TESTING"
        assert ProjectStatus.DEPLOYMENT.value == "DEPLOYMENT"
        assert ProjectStatus.COMPLETED.value == "COMPLETED"

    def test_status_enum_members(self):
        """测试状态枚举成员"""
        statuses = list(ProjectStatus)
        assert len(statuses) == 6
        assert ProjectStatus.REQUIREMENT in statuses
        assert ProjectStatus.COMPLETED in statuses

    def test_status_transitions(self):
        """测试状态转换规则"""
        # REQUIREMENT 可以转换到 DESIGN
        assert ProjectStatus.DESIGN in PROJECT_STATUS_TRANSITIONS[ProjectStatus.REQUIREMENT]

        # DESIGN 可以转换到 DEVELOPMENT
        assert ProjectStatus.DEVELOPMENT in PROJECT_STATUS_TRANSITIONS[ProjectStatus.DESIGN]

        # DEVELOPMENT 可以转换到 TESTING
        assert ProjectStatus.TESTING in PROJECT_STATUS_TRANSITIONS[ProjectStatus.DEVELOPMENT]

        # TESTING 可以转换到 DEVELOPMENT 或 DEPLOYMENT
        assert ProjectStatus.DEVELOPMENT in PROJECT_STATUS_TRANSITIONS[ProjectStatus.TESTING]
        assert ProjectStatus.DEPLOYMENT in PROJECT_STATUS_TRANSITIONS[ProjectStatus.TESTING]

        # DEPLOYMENT 可以转换到 TESTING 或 COMPLETED
        assert ProjectStatus.TESTING in PROJECT_STATUS_TRANSITIONS[ProjectStatus.DEPLOYMENT]
        assert ProjectStatus.COMPLETED in PROJECT_STATUS_TRANSITIONS[ProjectStatus.DEPLOYMENT]

        # COMPLETED 不能转换到任何状态
        assert PROJECT_STATUS_TRANSITIONS[ProjectStatus.COMPLETED] == []

    def test_invalid_status_transition(self):
        """测试无效的状态转换"""
        # REQUIREMENT 不能直接转换到 DEVELOPMENT
        assert ProjectStatus.DEVELOPMENT not in PROJECT_STATUS_TRANSITIONS[ProjectStatus.REQUIREMENT]

        # REQUIREMENT 不能直接转换到 COMPLETED
        assert ProjectStatus.COMPLETED not in PROJECT_STATUS_TRANSITIONS[ProjectStatus.REQUIREMENT]

    def test_all_statuses_have_transitions_defined(self):
        """测试所有状态都有定义的转换规则"""
        for status in ProjectStatus:
            assert status in PROJECT_STATUS_TRANSITIONS


@pytest.mark.model
@pytest.mark.unit
class TestProjectStatusHistory:
    """测试项目状态历史"""

    def test_status_history_storage(self, db_session: Session):
        """测试状态历史存储"""
        project = Project(
            name="状态历史测试",
            status_history=[
                {
                    "status": "DESIGN",
                    "previous_status": "REQUIREMENT",
                    "timestamp": datetime.utcnow().isoformat(),
                    "comment": "需求分析完成"
                }
            ]
        )

        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert len(project.status_history) == 1
        assert project.status_history[0]["status"] == "DESIGN"
        assert project.status_history[0]["previous_status"] == "REQUIREMENT"

    def test_status_history_append(self, db_session: Session):
        """测试追加状态历史"""
        project = Project(name="追加历史测试")
        db_session.add(project)
        db_session.commit()

        # 添加状态历史
        project.status_history = [
            {
                "status": "DESIGN",
                "previous_status": "REQUIREMENT",
                "timestamp": datetime.utcnow().isoformat(),
                "comment": "开始设计"
            }
        ]
        db_session.commit()
        db_session.refresh(project)

        assert len(project.status_history) == 1

    def test_status_history_multiple_entries(self, db_session: Session):
        """测试多个状态历史条目"""
        project = Project(
            name="多历史测试",
            status_history=[
                {
                    "status": "DESIGN",
                    "previous_status": "REQUIREMENT",
                    "timestamp": datetime.utcnow().isoformat(),
                    "comment": "需求完成"
                },
                {
                    "status": "DEVELOPMENT",
                    "previous_status": "DESIGN",
                    "timestamp": datetime.utcnow().isoformat(),
                    "comment": "设计完成"
                }
            ]
        )

        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert len(project.status_history) == 2


@pytest.mark.model
@pytest.mark.unit
class TestProjectMilestones:
    """测试项目里程碑"""

    def test_milestones_storage(self, db_session: Session):
        """测试里程碑存储"""
        project = Project(
            name="里程碑测试",
            milestones=[
                {
                    "name": "第一阶段",
                    "description": "需求分析完成",
                    "completed": True,
                    "completed_at": datetime.utcnow().isoformat()
                },
                {
                    "name": "第二阶段",
                    "description": "设计完成",
                    "completed": False
                }
            ]
        )

        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert len(project.milestones) == 2
        assert project.milestones[0]["name"] == "第一阶段"
        assert project.milestones[0]["completed"] is True
        assert project.milestones[1]["completed"] is False

    def test_milestones_empty_list(self, db_session: Session):
        """测试空里程碑列表"""
        project = Project(name="无里程碑项目", milestones=[])
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert project.milestones == []

    def test_milestones_with_metadata(self, db_session: Session):
        """测试带元数据的里程碑"""
        project = Project(
            name="元数据里程碑测试",
            milestones=[
                {
                    "name": "里程碑1",
                    "description": "描述",
                    "completed": True,
                    "completed_at": datetime.utcnow().isoformat(),
                    "metadata": {
                        "owner": "张三",
                        "priority": "high"
                    }
                }
            ]
        )

        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert project.milestones[0]["metadata"]["owner"] == "张三"


@pytest.mark.model
@pytest.mark.unit
class TestProjectQuery:
    """测试项目查询"""

    def test_query_by_status(self, db_session: Session):
        """测试按状态查询"""
        # 创建不同状态的项目
        project1 = Project(name="项目1", status=ProjectStatus.REQUIREMENT.value)
        project2 = Project(name="项目2", status=ProjectStatus.DEVELOPMENT.value)
        project3 = Project(name="项目3", status=ProjectStatus.REQUIREMENT.value)

        db_session.add_all([project1, project2, project3])
        db_session.commit()

        # 查询 REQUIREMENT 状态的项目
        requirement_projects = db_session.query(Project).filter_by(
            status=ProjectStatus.REQUIREMENT.value
        ).all()

        assert len(requirement_projects) == 2
        for p in requirement_projects:
            assert p.status == ProjectStatus.REQUIREMENT.value

    def test_query_by_name(self, db_session: Session):
        """测试按名称查询"""
        project = Project(name="精确查询名称")
        db_session.add(project)
        db_session.commit()

        found = db_session.query(Project).filter_by(name="精确查询名称").first()

        assert found is not None
        assert found.name == "精确查询名称"

    def test_query_order_by_created_at(self, db_session: Session):
        """测试按创建时间排序"""
        from sqlalchemy import desc

        # 创建多个项目
        for i in range(5):
            project = Project(name=f"排序项目{i}")
            db_session.add(project)
        db_session.commit()

        # 按创建时间降序查询
        projects = db_session.query(Project).order_by(desc(Project.created_at)).all()

        # 验证排序
        for i in range(len(projects) - 1):
            assert projects[i].created_at >= projects[i + 1].created_at

    def test_query_like_name(self, db_session: Session):
        """测试模糊查询名称"""
        project1 = Project(name="Python Web 项目")
        project2 = Project(name="Python Data 项目")
        project3 = Project(name="Java 项目")

        db_session.add_all([project1, project2, project3])
        db_session.commit()

        # 模糊查询
        results = db_session.query(Project).filter(Project.name.like("%Python%")).all()

        assert len(results) == 2


@pytest.mark.model
@pytest.mark.unit
class TestProjectDeletion:
    """测试项目删除"""

    def test_delete_project(self, db_session: Session):
        """测试删除项目"""
        project = Project(name="待删除项目")
        db_session.add(project)
        db_session.commit()

        project_id = project.id

        # 删除项目
        db_session.delete(project)
        db_session.commit()

        # 验证项目已被删除
        deleted = db_session.query(Project).filter_by(id=project_id).first()
        assert deleted is None

    def test_delete_project_cascade(self, db_session: Session):
        """测试级联删除（如果配置了外键关系）"""
        # 注意：这里假设没有配置级联删除，只是测试项目本身的删除
        project = Project(name="级联测试项目")
        db_session.add(project)
        db_session.commit()

        project_id = project.id

        # 删除项目
        db_session.delete(project)
        db_session.commit()

        # 验证项目已被删除
        assert db_session.query(Project).filter_by(id=project_id).first() is None


@pytest.mark.model
@pytest.mark.unit
class TestProjectStringRepresentation:
    """测试项目的字符串表示"""

    def test_project_attributes(self, db_session: Session):
        """测试项目属性访问"""
        project = Project(
            name="属性测试项目",
            description="测试描述",
            status=ProjectStatus.DEVELOPMENT.value
        )
        db_session.add(project)
        db_session.commit()

        # 验证所有属性都可以访问
        assert isinstance(project.id, int)
        assert isinstance(project.name, str)
        assert isinstance(project.description, str)
        assert isinstance(project.status, str)
        assert isinstance(project.created_at, datetime)


@pytest.mark.model
@pytest.mark.unit
class TestProjectEdgeCases:
    """测试项目边界情况"""

    def test_project_with_empty_tech_stack(self, db_session: Session):
        """测试使用空技术栈创建项目"""
        project = Project(name="空技术栈项目", tech_stack=[])
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert project.tech_stack == []

    def test_project_with_none_tech_stack(self, db_session: Session):
        """测试使用 None 技术栈创建项目"""
        project = Project(name="None技术栈项目", tech_stack=None)
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert project.tech_stack is None

    def test_project_with_long_description(self, db_session: Session):
        """测试使用长描述创建项目"""
        long_description = "A" * 1000
        project = Project(name="长描述项目", description=long_description)
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert project.description == long_description

    def test_concurrent_project_updates(self, db_session: Session):
        """测试并发更新项目"""
        project = Project(name="并发测试项目")
        db_session.add(project)
        db_session.commit()

        # 模拟并发更新
        project1 = db_session.query(Project).filter_by(id=project.id).first()
        project1.name = "更新1"

        project2 = db_session.query(Project).filter_by(id=project.id).first()
        project2.name = "更新2"

        db_session.commit()

        # 验证最后一次更新生效
        updated = db_session.query(Project).filter_by(id=project.id).first()
        assert updated.name in ["更新1", "更新2"]


@pytest.mark.model
@pytest.mark.unit
class TestProjectPerformance:
    """测试项目模型性能"""

    def test_bulk_insert_projects(self, db_session: Session):
        """测试批量插入项目"""
        projects = []
        for i in range(100):
            projects.append(Project(name=f"批量项目{i}"))

        db_session.add_all(projects)
        db_session.commit()

        count = db_session.query(Project).count()
        assert count >= 100

    def test_query_performance(self, db_session: Session):
        """测试查询性能"""
        # 创建大量项目
        for i in range(100):
            project = Project(name=f"性能测试项目{i}")
            db_session.add(project)
        db_session.commit()

        import time
        start_time = time.time()
        projects = db_session.query(Project).all()
        end_time = time.time()

        assert len(projects) >= 100
        assert end_time - start_time < 5.0  # 应该在 5 秒内完成
