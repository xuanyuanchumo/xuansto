"""
工作流执行器服务测试

测试工作流执行相关功能
"""

import pytest
from unittest.mock import Mock, MagicMock
from app.services.workflow.executor import WorkflowExecutor
from app.models.task import Task, TaskStatus


@pytest.mark.unit
class TestWorkflowExecutor:
    """测试 WorkflowExecutor 服务"""

    def test_build_dependency_detail(self):
        """测试构建依赖详情"""
        task = Mock(spec=Task)
        task.id = 1
        task.title = "测试任务"
        task.status = "COMPLETED"
        
        result = WorkflowExecutor._build_dependency_detail(task)
        
        assert result["id"] == 1
        assert result["title"] == "测试任务"
        assert result["status"] == "COMPLETED"

    def test_build_not_found_detail(self):
        """测试构建未找到详情"""
        result = WorkflowExecutor._build_not_found_detail(999)
        
        assert result["id"] == 999
        assert result["title"] == "Unknown"
        assert result["status"] == WorkflowExecutor.STATUS_NOT_FOUND

    def test_process_dependency_found_completed(self):
        """测试处理已完成的依赖"""
        dep_task = Mock(spec=Task)
        dep_task.id = 1
        dep_task.title = "依赖任务"
        dep_task.status = TaskStatus.COMPLETED.value
        
        dependency_map = {1: dep_task}
        
        is_pending, detail = WorkflowExecutor._process_dependency(1, dependency_map)
        
        assert is_pending is False
        assert detail["id"] == 1
        assert detail["status"] == TaskStatus.COMPLETED.value

    def test_process_dependency_found_pending(self):
        """测试处理待处理的依赖"""
        dep_task = Mock(spec=Task)
        dep_task.id = 1
        dep_task.title = "依赖任务"
        dep_task.status = TaskStatus.PENDING.value
        
        dependency_map = {1: dep_task}
        
        is_pending, detail = WorkflowExecutor._process_dependency(1, dependency_map)
        
        assert is_pending is True
        assert detail["status"] == TaskStatus.PENDING.value

    def test_process_dependency_not_found(self):
        """测试处理未找到的依赖"""
        dependency_map = {}
        
        is_pending, detail = WorkflowExecutor._process_dependency(999, dependency_map)
        
        assert is_pending is True
        assert detail["status"] == WorkflowExecutor.STATUS_NOT_FOUND

    def test_check_dependencies_no_dependencies(self):
        """测试无依赖的任务"""
        task = Mock(spec=Task)
        task.dependencies = None
        
        db = Mock()
        
        result = WorkflowExecutor.check_dependencies(task, db)
        
        assert result["all_dependencies_completed"] is True
        assert result["pending_dependencies"] == []
        assert result["dependency_details"] == []

    def test_check_dependencies_empty_dependencies(self):
        """测试空依赖列表"""
        task = Mock(spec=Task)
        task.dependencies = []
        
        db = Mock()
        
        result = WorkflowExecutor.check_dependencies(task, db)
        
        assert result["all_dependencies_completed"] is True

    def test_check_dependencies_all_completed(self):
        """测试所有依赖已完成"""
        task = Mock(spec=Task)
        task.dependencies = [1, 2, 3]
        
        dep_tasks = [
            Mock(id=1, title="任务1", status=TaskStatus.COMPLETED.value),
            Mock(id=2, title="任务2", status=TaskStatus.COMPLETED.value),
            Mock(id=3, title="任务3", status=TaskStatus.COMPLETED.value)
        ]
        
        db = Mock()
        db.query.return_value.filter.return_value.all.return_value = dep_tasks
        
        result = WorkflowExecutor.check_dependencies(task, db)
        
        assert result["all_dependencies_completed"] is True
        assert result["pending_dependencies"] == []

    def test_check_dependencies_some_pending(self):
        """测试部分依赖待处理"""
        task = Mock(spec=Task)
        task.dependencies = [1, 2, 3]
        
        dep_tasks = [
            Mock(id=1, title="任务1", status=TaskStatus.COMPLETED.value),
            Mock(id=2, title="任务2", status=TaskStatus.PENDING.value),
            Mock(id=3, title="任务3", status=TaskStatus.IN_PROGRESS.value)
        ]
        
        db = Mock()
        db.query.return_value.filter.return_value.all.return_value = dep_tasks
        
        result = WorkflowExecutor.check_dependencies(task, db)
        
        assert result["all_dependencies_completed"] is False
        assert 2 in result["pending_dependencies"]
        assert 3 in result["pending_dependencies"]

    def test_check_dependencies_missing_task(self):
        """测试依赖任务不存在"""
        task = Mock(spec=Task)
        task.dependencies = [1, 999]
        
        dep_tasks = [
            Mock(id=1, title="任务1", status=TaskStatus.COMPLETED.value)
        ]
        
        db = Mock()
        db.query.return_value.filter.return_value.all.return_value = dep_tasks
        
        result = WorkflowExecutor.check_dependencies(task, db)
        
        assert result["all_dependencies_completed"] is False
        assert 999 in result["pending_dependencies"]

    def test_get_task_or_raise_found(self):
        """测试获取存在的任务"""
        task = Mock(spec=Task)
        task.id = 1
        
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = task
        
        result = WorkflowExecutor.get_task_or_raise(1, db)
        
        assert result.id == 1

    def test_get_task_or_raise_not_found(self):
        """测试获取不存在的任务"""
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(Exception) as exc_info:
            WorkflowExecutor.get_task_or_raise(999, db)
        
        assert exc_info.value.status_code == 404

    def test_check_circular_dependencies_no_deps(self):
        """测试无依赖时无循环"""
        db = Mock()
        
        result = WorkflowExecutor.check_circular_dependencies(1, [], db)
        
        assert result is False

    def test_check_circular_dependencies_self_reference(self):
        """测试自引用循环"""
        db = Mock()
        
        result = WorkflowExecutor.check_circular_dependencies(1, [1], db)
        
        assert result is True

    def test_check_circular_dependencies_no_cycle(self):
        """测试无循环依赖"""
        db = Mock()
        
        task1 = Mock(id=1, dependencies=[2])
        task2 = Mock(id=2, dependencies=[])
        
        def mock_query_side_effect(model):
            mock_query = Mock()
            def mock_filter(condition):
                mock_filter = Mock()
                def mock_first():
                    if hasattr(condition, 'right'):
                        task_id = condition.right.value
                        if task_id == 1:
                            return task1
                        elif task_id == 2:
                            return task2
                    return None
                mock_filter.first = mock_first
                return mock_filter
            mock_query.filter = mock_filter
            return mock_query
        
        db.query.side_effect = mock_query_side_effect
        
        result = WorkflowExecutor.check_circular_dependencies(3, [1], db)
        
        assert result is False

    def test_get_ready_tasks(self):
        """测试获取就绪任务"""
        task1 = Mock(spec=Task)
        task1.id = 1
        task1.dependencies = []
        task1.status = TaskStatus.PENDING.value
        
        task2 = Mock(spec=Task)
        task2.id = 2
        task2.dependencies = [1]
        task2.status = TaskStatus.PENDING.value
        
        db = Mock()
        db.query.return_value.filter.return_value.all.return_value = [task1, task2]
        
        result = WorkflowExecutor.get_ready_tasks(1, db)
        
        assert len(result) == 1
        assert result[0].id == 1


@pytest.mark.unit
class TestWorkflowExecutorIntegration:
    """测试 WorkflowExecutor 集成场景"""

    def test_complex_dependency_chain(self):
        """测试复杂依赖链"""
        task = Mock(spec=Task)
        task.dependencies = [1, 2, 3, 4, 5]
        
        dep_tasks = [
            Mock(id=1, title="任务1", status=TaskStatus.COMPLETED.value),
            Mock(id=2, title="任务2", status=TaskStatus.COMPLETED.value),
            Mock(id=3, title="任务3", status=TaskStatus.IN_PROGRESS.value),
            Mock(id=4, title="任务4", status=TaskStatus.PENDING.value),
            Mock(id=5, title="任务5", status=TaskStatus.COMPLETED.value)
        ]
        
        db = Mock()
        db.query.return_value.filter.return_value.all.return_value = dep_tasks
        
        result = WorkflowExecutor.check_dependencies(task, db)
        
        assert result["all_dependencies_completed"] is False
        assert len(result["pending_dependencies"]) == 2
        assert 3 in result["pending_dependencies"]
        assert 4 in result["pending_dependencies"]
        assert len(result["dependency_details"]) == 5

    def test_performance_with_many_dependencies(self):
        """测试大量依赖的性能"""
        task = Mock(spec=Task)
        task.dependencies = list(range(1, 101))
        
        dep_tasks = [
            Mock(id=i, title=f"任务{i}", status=TaskStatus.COMPLETED.value)
            for i in range(1, 101)
        ]
        
        db = Mock()
        db.query.return_value.filter.return_value.all.return_value = dep_tasks
        
        import time
        start = time.time()
        result = WorkflowExecutor.check_dependencies(task, db)
        end = time.time()
        
        assert end - start < 0.1
        assert result["all_dependencies_completed"] is True
