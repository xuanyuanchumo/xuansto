"""
报告生成功能回归测试套件

验证报告生成的核心功能，包括：
- 统计数据收集
- 风险分析
- 报告生成
- 格式化输出
- 数据可视化
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock

from tests.conftest import create_test_project, create_test_task
from app.models.task import TaskStatus
from app.models.milestone import Milestone


@pytest.mark.regression
@pytest.mark.services
class TestReportGenerationRegression:
    """报告生成回归测试套件"""

    def test_statistics_collection_basic(self, db_session):
        """测试基础统计数据收集"""
        from app.services.report.statistics_collector import StatisticsCollector
        
        project = create_test_project(db_session, name="统计测试项目")
        
        for i in range(5):
            create_test_task(
                db_session,
                project_id=project.id,
                title=f"任务{i+1}",
                status=TaskStatus.COMPLETED.value if i < 3 else TaskStatus.PENDING.value
            )
        
        collector = StatisticsCollector(db_session, project.id)
        stats = collector.get_task_statistics()
        
        assert stats.total == 5
        assert stats.completed == 3
        assert stats.pending == 2
        assert stats.completion_rate == 60.0

    def test_statistics_collection_with_priorities(self, db_session):
        """测试带优先级的统计收集"""
        from app.services.report.statistics_collector import StatisticsCollector
        
        project = create_test_project(db_session, name="优先级统计项目")
        
        priorities = ["high", "high", "medium", "low", "low", "low"]
        for i, priority in enumerate(priorities):
            create_test_task(
                db_session,
                project_id=project.id,
                title=f"优先级任务{i+1}",
                priority=priority
            )
        
        collector = StatisticsCollector(db_session, project.id)
        stats = collector.get_task_statistics()
        
        assert stats.high_priority == 2
        assert stats.medium_priority == 1
        assert stats.low_priority == 3

    def test_milestone_statistics_collection(self, db_session):
        """测试里程碑统计收集"""
        from app.services.report.statistics_collector import StatisticsCollector
        
        project = create_test_project(db_session, name="里程碑统计项目")
        
        past_date = datetime.utcnow() - timedelta(days=5)
        future_date = datetime.utcnow() + timedelta(days=5)
        
        milestones = [
            Milestone(name="已完成里程碑", project_id=project.id, status="completed", planned_date=past_date),
            Milestone(name="逾期里程碑", project_id=project.id, status="in_progress", planned_date=past_date),
            Milestone(name="正常里程碑", project_id=project.id, status="pending", planned_date=future_date),
        ]
        db_session.add_all(milestones)
        db_session.commit()
        
        collector = StatisticsCollector(db_session, project.id)
        stats = collector.get_milestone_statistics()
        
        assert stats.total == 3
        assert stats.completed == 1
        assert stats.overdue == 1

    def test_risk_analysis_progress(self):
        """测试进度风险分析"""
        from app.services.report.risk_analyzer import RiskAnalyzer
        
        analyzer = RiskAnalyzer(
            completion_rate=25.0,
            project_status="DEVELOPMENT",
            pending_tasks=15,
            completed_tasks=5,
            overdue_milestones=0
        )
        
        risks, suggestions = analyzer.analyze()
        
        progress_risk = next((r for r in risks if "进度" in r.description), None)
        assert progress_risk is not None
        assert progress_risk.severity == "high"

    def test_risk_analysis_overdue_milestones(self):
        """测试逾期里程碑风险分析"""
        from app.services.report.risk_analyzer import RiskAnalyzer
        
        analyzer = RiskAnalyzer(
            completion_rate=70.0,
            project_status="DEVELOPMENT",
            pending_tasks=3,
            completed_tasks=7,
            overdue_milestones=3
        )
        
        risks, suggestions = analyzer.analyze()
        
        overdue_risk = next((r for r in risks if "逾期" in r.description), None)
        assert overdue_risk is not None
        assert overdue_risk.severity == "high"

    def test_risk_analysis_no_risks(self):
        """测试无风险情况"""
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

    def test_risk_analysis_multiple_risks(self):
        """测试多风险情况"""
        from app.services.report.risk_analyzer import RiskAnalyzer
        
        analyzer = RiskAnalyzer(
            completion_rate=20.0,
            project_status="TESTING",
            pending_tasks=20,
            completed_tasks=5,
            overdue_milestones=2
        )
        
        risks, suggestions = analyzer.analyze()
        
        assert len(risks) >= 2
        assert len(suggestions) >= 2

    def test_report_generation_full(self, db_session):
        """测试完整报告生成"""
        from app.services.report.generator import ReportGenerator
        from app.services.report.statistics_collector import TaskStatistics, MilestoneStatistics
        from app.services.report.risk_analyzer import Risk, Suggestion
        
        project = create_test_project(
            db_session,
            name="报告生成项目",
            description="测试报告生成功能",
            tech_stack=["Python", "FastAPI"],
            status="DEVELOPMENT"
        )
        
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
        
        risks = [Risk(description="进度风险", severity="high")]
        suggestions = [Suggestion(description="增加资源投入")]
        
        generator = ReportGenerator(project)
        report = generator.generate(task_stats, milestone_stats, milestones, risks, suggestions)
        
        assert "项目进度报告" in report
        assert project.name in report
        assert "60.0%" in report
        assert "进度风险" in report
        assert "增加资源投入" in report

    def test_report_generation_empty_project(self, db_session):
        """测试空项目报告生成"""
        from app.services.report.generator import ReportGenerator
        from app.services.report.statistics_collector import TaskStatistics, MilestoneStatistics
        
        project = create_test_project(db_session, name="空项目")
        
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
        report = generator.generate(task_stats, milestone_stats, [], [], [])
        
        assert "暂无任务" in report or "总任务数: 0" in report

    def test_markdown_formatter(self):
        """测试Markdown格式化器"""
        from app.services.report.formatters import MarkdownFormatter
        
        formatter = MarkdownFormatter()
        
        assert formatter.heading("标题") == "# 标题"
        assert formatter.heading("二级标题", level=2) == "## 二级标题"
        assert formatter.bold("粗体") == "**粗体**"
        assert formatter.list_item("列表项") == "- 列表项"
        assert formatter.numbered_item(1, "第一项") == "1. 第一项"
        assert formatter.table_header(["列1", "列2"]) == "| 列1 | 列2 |"
        assert formatter.table_separator(2) == "|-----|-----|"
        assert formatter.table_row(["值1", "值2"]) == "| 值1 | 值2 |"

    def test_progress_bar_generator(self):
        """测试进度条生成器"""
        from app.services.report.formatters import ProgressBarGenerator
        
        generator = ProgressBarGenerator()
        
        bar_0 = generator.generate(0)
        assert "0%" in bar_0
        
        bar_50 = generator.generate(50)
        assert "50%" in bar_50
        
        bar_100 = generator.generate(100)
        assert "100%" in bar_100

    def test_report_with_chinese_content(self, db_session):
        """测试中文内容报告"""
        from app.services.report.generator import ReportGenerator
        from app.services.report.statistics_collector import TaskStatistics, MilestoneStatistics
        
        project = create_test_project(
            db_session,
            name="中文项目名称",
            description="这是中文描述",
            status="DEVELOPMENT"
        )
        
        task_stats = TaskStatistics(
            total=5,
            completed=3,
            in_progress=1,
            pending=1,
            review=0,
            high_priority=1,
            medium_priority=2,
            low_priority=2,
            completion_rate=60.0
        )
        
        milestone_stats = MilestoneStatistics(
            total=1,
            completed=1,
            in_progress=0,
            overdue=0
        )
        
        generator = ReportGenerator(project)
        report = generator.generate(task_stats, milestone_stats, [], [], [])
        
        assert "中文项目名称" in report

    def test_report_with_special_characters(self, db_session):
        """测试特殊字符报告"""
        from app.services.report.generator import ReportGenerator
        from app.services.report.statistics_collector import TaskStatistics, MilestoneStatistics
        
        project = create_test_project(
            db_session,
            name="特殊字符项目<>&\"'",
            description="描述包含特殊字符: <>&\"'",
            status="DEVELOPMENT"
        )
        
        task_stats = TaskStatistics(
            total=1,
            completed=1,
            in_progress=0,
            pending=0,
            review=0,
            high_priority=0,
            medium_priority=1,
            low_priority=0,
            completion_rate=100.0
        )
        
        milestone_stats = MilestoneStatistics(
            total=0,
            completed=0,
            in_progress=0,
            overdue=0
        )
        
        generator = ReportGenerator(project)
        report = generator.generate(task_stats, milestone_stats, [], [], [])
        
        assert project.name in report


@pytest.mark.regression
@pytest.mark.services
class TestReportEdgeCases:
    """报告生成边界条件测试"""

    def test_statistics_with_large_numbers(self, db_session):
        """测试大数据量统计"""
        from app.services.report.statistics_collector import StatisticsCollector
        
        project = create_test_project(db_session, name="大数据项目")
        
        for i in range(100):
            create_test_task(
                db_session,
                project_id=project.id,
                title=f"任务{i+1}",
                status=TaskStatus.COMPLETED.value if i % 3 == 0 else TaskStatus.PENDING.value
            )
        
        collector = StatisticsCollector(db_session, project.id)
        stats = collector.get_task_statistics()
        
        assert stats.total == 100
        assert stats.completion_rate > 0

    def test_risk_analyzer_edge_cases(self):
        """测试风险分析边界条件"""
        from app.services.report.risk_analyzer import RiskAnalyzer
        
        edge_cases = [
            {"completion_rate": 0.0, "project_status": "REQUIREMENT", "pending_tasks": 0, "completed_tasks": 0, "overdue_milestones": 0},
            {"completion_rate": 100.0, "project_status": "COMPLETED", "pending_tasks": 0, "completed_tasks": 10, "overdue_milestones": 0},
            {"completion_rate": 50.0, "project_status": "DEVELOPMENT", "pending_tasks": 0, "completed_tasks": 5, "overdue_milestones": 0},
        ]
        
        for case in edge_cases:
            analyzer = RiskAnalyzer(**case)
            risks, suggestions = analyzer.analyze()
            assert isinstance(risks, list)
            assert isinstance(suggestions, list)

    def test_report_with_null_values(self, db_session):
        """测试空值报告"""
        from app.services.report.generator import ReportGenerator
        from app.services.report.statistics_collector import TaskStatistics, MilestoneStatistics
        
        project = create_test_project(
            db_session,
            name="空值测试项目",
            description=None,
            tech_stack=None
        )
        
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
        report = generator.generate(task_stats, milestone_stats, [], [], [])
        
        assert report is not None
        assert len(report) > 0


@pytest.mark.regression
@pytest.mark.performance
class TestReportPerformance:
    """报告生成性能测试"""

    def test_statistics_collection_performance(self, db_session):
        """测试统计收集性能"""
        import time
        from app.services.report.statistics_collector import StatisticsCollector
        
        project = create_test_project(db_session, name="性能测试项目")
        
        for i in range(50):
            create_test_task(db_session, project_id=project.id, title=f"性能任务{i}")
        
        start = time.time()
        collector = StatisticsCollector(db_session, project.id)
        stats = collector.get_task_statistics()
        duration = time.time() - start
        
        assert duration < 2.0
        assert stats.total == 50

    def test_report_generation_performance(self, db_session):
        """测试报告生成性能"""
        import time
        from app.services.report.generator import ReportGenerator
        from app.services.report.statistics_collector import TaskStatistics, MilestoneStatistics
        
        project = create_test_project(db_session, name="报告性能项目")
        
        task_stats = TaskStatistics(
            total=100,
            completed=60,
            in_progress=20,
            pending=20,
            review=0,
            high_priority=30,
            medium_priority=40,
            low_priority=30,
            completion_rate=60.0
        )
        
        milestone_stats = MilestoneStatistics(
            total=10,
            completed=5,
            in_progress=3,
            overdue=2
        )
        
        generator = ReportGenerator(project)
        
        start = time.time()
        report = generator.generate(task_stats, milestone_stats, [], [], [])
        duration = time.time() - start
        
        assert duration < 1.0
        assert len(report) > 0

    def test_risk_analysis_performance(self):
        """测试风险分析性能"""
        import time
        from app.services.report.risk_analyzer import RiskAnalyzer
        
        analyzer = RiskAnalyzer(
            completion_rate=50.0,
            project_status="DEVELOPMENT",
            pending_tasks=10,
            completed_tasks=10,
            overdue_milestones=1
        )
        
        start = time.time()
        for _ in range(100):
            analyzer.analyze()
        duration = time.time() - start
        
        assert duration < 2.0
