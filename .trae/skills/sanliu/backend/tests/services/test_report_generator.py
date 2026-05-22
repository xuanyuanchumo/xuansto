import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock


class TestReportGenerator:
    
    def test_generate_empty_report(self, db_session):
        from app.services.report.generator import ReportGenerator
        from app.services.report.statistics_collector import TaskStatistics, MilestoneStatistics
        
        project = Mock()
        project.name = "测试项目"
        project.status = "REQUIREMENT"
        project.description = "测试描述"
        project.tech_stack = ["Python"]
        project.created_at = datetime.now()
        
        generator = ReportGenerator(project)
        
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
        
        from app.services.report.risk_analyzer import Risk, Suggestion
        
        content = generator.generate(
            task_stats=task_stats,
            milestone_stats=milestone_stats,
            milestones=[],
            risks=[],
            suggestions=[Suggestion(description="继续保持当前进度")]
        )
        
        assert "测试项目" in content
        assert "项目进度报告" in content

    def test_generate_report_with_tasks(self, db_session):
        from app.services.report.generator import ReportGenerator
        from app.services.report.statistics_collector import TaskStatistics, MilestoneStatistics
        
        project = Mock()
        project.name = "测试项目"
        project.status = "DEVELOPMENT"
        project.description = None
        project.tech_stack = None
        project.created_at = datetime.now()
        
        generator = ReportGenerator(project)
        
        task_stats = TaskStatistics(
            total=10,
            completed=5,
            in_progress=2,
            pending=2,
            review=1,
            high_priority=2,
            medium_priority=5,
            low_priority=3,
            completion_rate=50.0
        )
        
        milestone_stats = MilestoneStatistics(
            total=0,
            completed=0,
            in_progress=0,
            overdue=0
        )
        
        content = generator.generate(
            task_stats=task_stats,
            milestone_stats=milestone_stats,
            milestones=[],
            risks=[],
            suggestions=[]
        )
        
        assert "总任务数: 10" in content
        assert "已完成: 5" in content
        assert "50%" in content

    def test_generate_report_with_milestones(self, db_session):
        from app.services.report.generator import ReportGenerator
        from app.services.report.statistics_collector import TaskStatistics, MilestoneStatistics
        
        project = Mock()
        project.name = "测试项目"
        project.status = "DEVELOPMENT"
        project.description = None
        project.tech_stack = None
        project.created_at = datetime.now()
        
        generator = ReportGenerator(project)
        
        milestone = Mock()
        milestone.name = "里程碑1"
        milestone.status = "completed"
        milestone.planned_date = datetime.now()
        milestone.completed_date = datetime.now()
        
        task_stats = TaskStatistics(
            total=5,
            completed=5,
            in_progress=0,
            pending=0,
            review=0,
            high_priority=0,
            medium_priority=0,
            low_priority=0,
            completion_rate=100.0
        )
        
        milestone_stats = MilestoneStatistics(
            total=1,
            completed=1,
            in_progress=0,
            overdue=0
        )
        
        content = generator.generate(
            task_stats=task_stats,
            milestone_stats=milestone_stats,
            milestones=[milestone],
            risks=[],
            suggestions=[]
        )
        
        assert "里程碑1" in content


class TestStatisticsCollector:
    
    def test_collect_tasks_empty(self, db_session):
        from app.services.report.statistics_collector import StatisticsCollector
        
        from tests.conftest import create_test_project
        project = create_test_project(db_session, name="测试项目")
        
        collector = StatisticsCollector(db_session, project.id)
        tasks = collector.collect_tasks()
        
        assert tasks == []

    def test_collect_tasks_with_data(self, db_session):
        from app.services.report.statistics_collector import StatisticsCollector
        from tests.conftest import create_test_project, create_test_task
        
        project = create_test_project(db_session, name="测试项目")
        create_test_task(db_session, project_id=project.id, title="任务1")
        create_test_task(db_session, project_id=project.id, title="任务2")
        
        collector = StatisticsCollector(db_session, project.id)
        tasks = collector.collect_tasks()
        
        assert len(tasks) == 2

    def test_get_task_statistics(self, db_session):
        from app.services.report.statistics_collector import StatisticsCollector
        from app.models.task import TaskStatus
        from tests.conftest import create_test_project, create_test_task
        
        project = create_test_project(db_session, name="测试项目")
        create_test_task(db_session, project_id=project.id, title="任务1", status=TaskStatus.COMPLETED.value)
        create_test_task(db_session, project_id=project.id, title="任务2", status=TaskStatus.PENDING.value)
        create_test_task(db_session, project_id=project.id, title="任务3", status=TaskStatus.IN_PROGRESS.value)
        
        collector = StatisticsCollector(db_session, project.id)
        stats = collector.get_task_statistics()
        
        assert stats.total == 3
        assert stats.completed == 1
        assert stats.pending == 1
        assert stats.in_progress == 1
        assert stats.completion_rate == 33.33

    def test_get_milestone_statistics(self, db_session):
        from app.services.report.statistics_collector import StatisticsCollector
        from app.models.milestone import Milestone
        from tests.conftest import create_test_project
        
        project = create_test_project(db_session, name="测试项目")
        
        m1 = Milestone(project_id=project.id, name="里程碑1", status="completed")
        m2 = Milestone(project_id=project.id, name="里程碑2", status="in_progress")
        m3 = Milestone(
            project_id=project.id, 
            name="里程碑3", 
            status="pending",
            planned_date=datetime.utcnow() - timedelta(days=1)
        )
        db_session.add_all([m1, m2, m3])
        db_session.commit()
        
        collector = StatisticsCollector(db_session, project.id)
        stats = collector.get_milestone_statistics()
        
        assert stats.total == 3
        assert stats.completed == 1
        assert stats.in_progress == 1
        assert stats.overdue == 1


class TestRiskAnalyzer:
    
    def test_analyze_no_risks(self):
        from app.services.report.risk_analyzer import RiskAnalyzer
        
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
        from app.services.report.risk_analyzer import RiskAnalyzer
        
        analyzer = RiskAnalyzer(
            completion_rate=30.0,
            project_status="DEVELOPMENT",
            pending_tasks=5,
            completed_tasks=2,
            overdue_milestones=0
        )
        
        risks, suggestions = analyzer.analyze()
        
        assert len(risks) == 2
        assert any("进度较慢" in r.description for r in risks)

    def test_analyze_overdue_milestones_risk(self):
        from app.services.report.risk_analyzer import RiskAnalyzer
        
        analyzer = RiskAnalyzer(
            completion_rate=80.0,
            project_status="DEVELOPMENT",
            pending_tasks=2,
            completed_tasks=8,
            overdue_milestones=2
        )
        
        risks, suggestions = analyzer.analyze()
        
        assert len(risks) == 1
        assert "逾期" in risks[0].description
        assert risks[0].severity == "high"

    def test_analyze_pending_tasks_risk(self):
        from app.services.report.risk_analyzer import RiskAnalyzer
        
        analyzer = RiskAnalyzer(
            completion_rate=60.0,
            project_status="DEVELOPMENT",
            pending_tasks=10,
            completed_tasks=5,
            overdue_milestones=0
        )
        
        risks, suggestions = analyzer.analyze()
        
        assert any("待处理任务" in r.description for r in risks)


class TestFormatters:
    
    def test_progress_bar_generator(self):
        from app.services.report.formatters import ProgressBarGenerator
        
        bar = ProgressBarGenerator.generate(50, length=10)
        assert bar == "█████░░░░░"
        
        bar = ProgressBarGenerator.generate(100, length=10)
        assert bar == "██████████"
        
        bar = ProgressBarGenerator.generate(0, length=10)
        assert bar == "░░░░░░░░░░"

    def test_markdown_formatter_heading(self):
        from app.services.report.formatters import MarkdownFormatter
        
        assert MarkdownFormatter.heading("标题", level=1) == "# 标题"
        assert MarkdownFormatter.heading("标题", level=2) == "## 标题"
        assert MarkdownFormatter.heading("标题", level=3) == "### 标题"

    def test_markdown_formatter_bold(self):
        from app.services.report.formatters import MarkdownFormatter
        
        assert MarkdownFormatter.bold("文本") == "**文本**"

    def test_markdown_formatter_list_item(self):
        from app.services.report.formatters import MarkdownFormatter
        
        assert MarkdownFormatter.list_item("项目") == "- 项目"

    def test_markdown_formatter_numbered_item(self):
        from app.services.report.formatters import MarkdownFormatter
        
        assert MarkdownFormatter.numbered_item(1, "项目") == "1. 项目"

    def test_markdown_formatter_table(self):
        from app.services.report.formatters import MarkdownFormatter
        
        header = MarkdownFormatter.table_header(["列1", "列2", "列3"])
        assert header == "| 列1 | 列2 | 列3 |"
        
        separator = MarkdownFormatter.table_separator(3)
        assert separator == "|------|------|------|"
        
        row = MarkdownFormatter.table_row(["值1", "值2", "值3"])
        assert row == "| 值1 | 值2 | 值3 |"

    def test_markdown_formatter_horizontal_rule(self):
        from app.services.report.formatters import MarkdownFormatter
        
        assert MarkdownFormatter.horizontal_rule() == "---"
