"""
报告服务单元测试

测试 StatisticsCollector, RiskAnalyzer, ReportGenerator 等服务类
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from app.services.report.statistics_collector import (
    StatisticsCollector, TaskStatistics, MilestoneStatistics
)
from app.services.report.risk_analyzer import RiskAnalyzer, Risk, Suggestion
from app.services.report.generator import ReportGenerator
from app.services.report.formatters import MarkdownFormatter, ProgressBarGenerator
from app.models.project import Project
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.milestone import Milestone, MilestoneStatus


@pytest.mark.unit
@pytest.mark.services
class TestStatisticsCollector:
    """测试 StatisticsCollector 类"""

    def test_collect_tasks(self, db_session: Session):
        """测试收集任务"""
        project = Project(name="统计测试项目")
        db_session.add(project)
        db_session.commit()

        task1 = Task(title="任务1", project_id=project.id, status=TaskStatus.COMPLETED.value)
        task2 = Task(title="任务2", project_id=project.id, status=TaskStatus.PENDING.value)
        db_session.add_all([task1, task2])
        db_session.commit()

        collector = StatisticsCollector(db_session, project.id)
        tasks = collector.collect_tasks()

        assert len(tasks) == 2

    def test_collect_tasks_caching(self, db_session: Session):
        """测试任务收集缓存"""
        project = Project(name="缓存测试项目")
        db_session.add(project)
        db_session.commit()

        collector = StatisticsCollector(db_session, project.id)
        
        tasks1 = collector.collect_tasks()
        tasks2 = collector.collect_tasks()
        
        assert tasks1 is tasks2

    def test_collect_milestones(self, db_session: Session):
        """测试收集里程碑"""
        project = Project(name="里程碑测试项目")
        db_session.add(project)
        db_session.commit()

        milestone1 = Milestone(name="里程碑1", project_id=project.id)
        milestone2 = Milestone(name="里程碑2", project_id=project.id)
        db_session.add_all([milestone1, milestone2])
        db_session.commit()

        collector = StatisticsCollector(db_session, project.id)
        milestones = collector.collect_milestones()

        assert len(milestones) == 2

    def test_get_task_statistics_empty(self, db_session: Session):
        """测试空项目任务统计"""
        project = Project(name="空项目")
        db_session.add(project)
        db_session.commit()

        collector = StatisticsCollector(db_session, project.id)
        stats = collector.get_task_statistics()

        assert stats.total == 0
        assert stats.completed == 0
        assert stats.completion_rate == 0.0

    def test_get_task_statistics_with_tasks(self, db_session: Session):
        """测试有任务时的统计"""
        project = Project(name="统计项目")
        db_session.add(project)
        db_session.commit()

        tasks = [
            Task(title="完成", project_id=project.id, status=TaskStatus.COMPLETED.value, priority="high"),
            Task(title="进行中", project_id=project.id, status=TaskStatus.IN_PROGRESS.value, priority="medium"),
            Task(title="待处理", project_id=project.id, status=TaskStatus.PENDING.value, priority="low"),
            Task(title="审核中", project_id=project.id, status=TaskStatus.REVIEW.value, priority="high"),
        ]
        db_session.add_all(tasks)
        db_session.commit()

        collector = StatisticsCollector(db_session, project.id)
        stats = collector.get_task_statistics()

        assert stats.total == 4
        assert stats.completed == 1
        assert stats.in_progress == 1
        assert stats.pending == 1
        assert stats.review == 1
        assert stats.high_priority == 2
        assert stats.medium_priority == 1
        assert stats.low_priority == 1
        assert stats.completion_rate == 25.0

    def test_get_task_statistics_completion_rate(self, db_session: Session):
        """测试完成率计算"""
        project = Project(name="完成率项目")
        db_session.add(project)
        db_session.commit()

        for i in range(10):
            status = TaskStatus.COMPLETED.value if i < 7 else TaskStatus.PENDING.value
            task = Task(title=f"任务{i}", project_id=project.id, status=status)
            db_session.add(task)
        db_session.commit()

        collector = StatisticsCollector(db_session, project.id)
        stats = collector.get_task_statistics()

        assert stats.completion_rate == 70.0

    def test_get_milestone_statistics_empty(self, db_session: Session):
        """测试空里程碑统计"""
        project = Project(name="空里程碑项目")
        db_session.add(project)
        db_session.commit()

        collector = StatisticsCollector(db_session, project.id)
        stats = collector.get_milestone_statistics()

        assert stats.total == 0
        assert stats.completed == 0
        assert stats.overdue == 0

    def test_get_milestone_statistics_with_overdue(self, db_session: Session):
        """测试有逾期里程碑的统计"""
        project = Project(name="逾期里程碑项目")
        db_session.add(project)
        db_session.commit()

        past_date = datetime.utcnow() - timedelta(days=10)
        future_date = datetime.utcnow() + timedelta(days=10)

        milestones = [
            Milestone(name="已完成", project_id=project.id, status="completed", planned_date=past_date),
            Milestone(name="逾期未完成", project_id=project.id, status="in_progress", planned_date=past_date),
            Milestone(name="未逾期", project_id=project.id, status="pending", planned_date=future_date),
        ]
        db_session.add_all(milestones)
        db_session.commit()

        collector = StatisticsCollector(db_session, project.id)
        stats = collector.get_milestone_statistics()

        assert stats.total == 3
        assert stats.completed == 1
        assert stats.in_progress == 1
        assert stats.overdue == 1


@pytest.mark.unit
@pytest.mark.services
class TestRiskAnalyzer:
    """测试 RiskAnalyzer 类"""

    def test_analyze_no_risks(self):
        """测试无风险情况"""
        analyzer = RiskAnalyzer(
            completion_rate=80.0,
            project_status="DEVELOPMENT",
            pending_tasks=2,
            completed_tasks=8,
            overdue_milestones=0
        )
        
        risks, suggestions = analyzer.analyze()
        
        assert len(risks) == 0
        assert len(suggestions) == 0

    def test_analyze_progress_risk(self):
        """测试进度风险检测"""
        analyzer = RiskAnalyzer(
            completion_rate=30.0,
            project_status="DEVELOPMENT",
            pending_tasks=5,
            completed_tasks=2,
            overdue_milestones=0
        )
        
        risks, suggestions = analyzer.analyze()
        
        assert len(risks) == 1
        assert risks[0].severity == "high"
        assert "进度" in risks[0].description
        assert len(suggestions) == 1

    def test_analyze_pending_tasks_risk(self):
        """测试待处理任务风险"""
        analyzer = RiskAnalyzer(
            completion_rate=60.0,
            project_status="TESTING",
            pending_tasks=10,
            completed_tasks=5,
            overdue_milestones=0
        )
        
        risks, suggestions = analyzer.analyze()
        
        pending_risk = next((r for r in risks if "待处理" in r.description), None)
        assert pending_risk is not None
        assert pending_risk.severity == "medium"

    def test_analyze_overdue_milestones_risk(self):
        """测试逾期里程碑风险"""
        analyzer = RiskAnalyzer(
            completion_rate=70.0,
            project_status="DEVELOPMENT",
            pending_tasks=3,
            completed_tasks=7,
            overdue_milestones=2
        )
        
        risks, suggestions = analyzer.analyze()
        
        overdue_risk = next((r for r in risks if "逾期" in r.description), None)
        assert overdue_risk is not None
        assert overdue_risk.severity == "high"
        assert "2" in overdue_risk.description

    def test_analyze_multiple_risks(self):
        """测试多风险情况"""
        analyzer = RiskAnalyzer(
            completion_rate=20.0,
            project_status="TESTING",
            pending_tasks=15,
            completed_tasks=3,
            overdue_milestones=3
        )
        
        risks, suggestions = analyzer.analyze()
        
        assert len(risks) == 3
        assert len(suggestions) == 3

    def test_no_risk_in_early_stages(self):
        """测试早期阶段无风险"""
        analyzer = RiskAnalyzer(
            completion_rate=10.0,
            project_status="REQUIREMENT",
            pending_tasks=20,
            completed_tasks=2,
            overdue_milestones=0
        )
        
        risks, suggestions = analyzer.analyze()
        
        assert len(risks) == 0


@pytest.mark.unit
@pytest.mark.services
class TestReportGenerator:
    """测试 ReportGenerator 类"""

    def test_generate_report(self, db_session: Session):
        """测试生成报告"""
        project = Project(
            name="报告测试项目",
            description="测试描述",
            tech_stack=["Python", "FastAPI"],
            status="DEVELOPMENT"
        )
        db_session.add(project)
        db_session.commit()

        task_stats = TaskStatistics(
            total=10,
            completed=6,
            in_progress=2,
            pending=2,
            review=0,
            high_priority=3,
            medium_priority=4,
            low_priority=3,
            completion_rate=60.0
        )

        milestone_stats = MilestoneStatistics(
            total=3,
            completed=1,
            in_progress=1,
            overdue=1
        )

        milestones = [
            Milestone(name="里程碑1", project_id=project.id, status="completed"),
            Milestone(name="里程碑2", project_id=project.id, status="in_progress"),
        ]

        risks = [Risk(description="测试风险", severity="high")]
        suggestions = [Suggestion(description="测试建议")]

        generator = ReportGenerator(project)
        report = generator.generate(
            task_stats, milestone_stats, milestones, risks, suggestions
        )

        assert "项目进度报告" in report
        assert project.name in report
        assert "60.0%" in report
        assert "测试风险" in report
        assert "测试建议" in report

    def test_generate_report_empty_project(self, db_session: Session):
        """测试空项目报告"""
        project = Project(name="空项目")
        db_session.add(project)
        db_session.commit()

        task_stats = TaskStatistics(
            total=0,
            completed=0,
            in_progress=0,
            pending=0,
            review=0,
            high_priority=0,
            medium_priority=0,
            low_priority=0,
            completion_rate=0.0
        )

        milestone_stats = MilestoneStatistics(
            total=0,
            completed=0,
            in_progress=0,
            overdue=0
        )

        generator = ReportGenerator(project)
        report = generator.generate(
            task_stats, milestone_stats, [], [], []
        )

        assert "暂无任务" in report or "总任务数: 0" in report
        assert "暂无明显风险" in report


@pytest.mark.unit
@pytest.mark.services
class TestMarkdownFormatter:
    """测试 MarkdownFormatter 类"""

    def setup_method(self):
        self.formatter = MarkdownFormatter()

    def test_heading(self):
        """测试标题格式化"""
        result = self.formatter.heading("测试标题")
        assert result == "# 测试标题"

    def test_heading_with_level(self):
        """测试多级标题"""
        result = self.formatter.heading("二级标题", level=2)
        assert result == "## 二级标题"

    def test_bold(self):
        """测试粗体格式化"""
        result = self.formatter.bold("粗体文本")
        assert result == "**粗体文本**"

    def test_list_item(self):
        """测试列表项格式化"""
        result = self.formatter.list_item("列表项")
        assert result == "- 列表项"

    def test_numbered_item(self):
        """测试编号项格式化"""
        result = self.formatter.numbered_item(1, "第一项")
        assert result == "1. 第一项"

    def test_table_header(self):
        """测试表格头格式化"""
        result = self.formatter.table_header(["列1", "列2", "列3"])
        assert result == "| 列1 | 列2 | 列3 |"

    def test_table_separator(self):
        """测试表格分隔符"""
        result = self.formatter.table_separator(3)
        assert result == "|-----|-----|-----|"

    def test_table_row(self):
        """测试表格行格式化"""
        result = self.formatter.table_row(["值1", "值2", "值3"])
        assert result == "| 值1 | 值2 | 值3 |"

    def test_horizontal_rule(self):
        """测试水平线"""
        result = self.formatter.horizontal_rule()
        assert result == "---"


@pytest.mark.unit
@pytest.mark.services
class TestProgressBarGenerator:
    """测试 ProgressBarGenerator 类"""

    def setup_method(self):
        self.generator = ProgressBarGenerator()

    def test_generate_zero_progress(self):
        """测试零进度"""
        result = self.generator.generate(0)
        assert "0%" in result

    def test_generate_full_progress(self):
        """测试满进度"""
        result = self.generator.generate(100)
        assert "100%" in result

    def test_generate_partial_progress(self):
        """测试部分进度"""
        result = self.generator.generate(50)
        assert "50%" in result

    def test_generate_rounds_progress(self):
        """测试进度四舍五入"""
        result = self.generator.generate(33.33)
        assert "33" in result or "34" in result


@pytest.mark.unit
@pytest.mark.services
class TestRisk:
    """测试 Risk 数据类"""

    def test_risk_creation(self):
        """测试风险创建"""
        risk = Risk(description="测试风险", severity="high")
        
        assert risk.description == "测试风险"
        assert risk.severity == "high"

    def test_risk_default_severity(self):
        """测试风险默认严重程度"""
        risk = Risk(description="默认风险")
        
        assert risk.severity == "medium"


@pytest.mark.unit
@pytest.mark.services
class TestSuggestion:
    """测试 Suggestion 数据类"""

    def test_suggestion_creation(self):
        """测试建议创建"""
        suggestion = Suggestion(description="测试建议")
        
        assert suggestion.description == "测试建议"


@pytest.mark.unit
@pytest.mark.services
class TestTaskStatistics:
    """测试 TaskStatistics 数据类"""

    def test_task_statistics_creation(self):
        """测试任务统计创建"""
        stats = TaskStatistics(
            total=10,
            completed=5,
            in_progress=2,
            pending=3,
            review=0,
            high_priority=2,
            medium_priority=5,
            low_priority=3,
            completion_rate=50.0
        )
        
        assert stats.total == 10
        assert stats.completed == 5
        assert stats.completion_rate == 50.0


@pytest.mark.unit
@pytest.mark.services
class TestMilestoneStatistics:
    """测试 MilestoneStatistics 数据类"""

    def test_milestone_statistics_creation(self):
        """测试里程碑统计创建"""
        stats = MilestoneStatistics(
            total=5,
            completed=2,
            in_progress=2,
            overdue=1
        )
        
        assert stats.total == 5
        assert stats.overdue == 1
