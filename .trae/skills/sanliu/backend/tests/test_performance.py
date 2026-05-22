"""
性能测试

测试 API 和数据库的性能指标
"""

import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tests.conftest import create_test_project, create_test_task, create_test_agent


@pytest.mark.performance
@pytest.mark.integration
class TestAPIPerformance:
    """测试 API 性能"""

    def test_list_projects_response_time(self, client, db_session, mock_redis):
        """测试项目列表响应时间"""
        # 创建测试数据
        for i in range(50):
            create_test_project(db_session, name=f"性能测试项目{i}")

        mock_redis.get_json.return_value = None

        # 测量响应时间
        start_time = time.time()
        response = client.get("/api/projects/")
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 1.0  # 响应时间应小于 1 秒

    def test_list_tasks_response_time(self, client, db_session, mock_redis):
        """测试任务列表响应时间"""
        project = create_test_project(db_session, name="性能测试项目")

        for i in range(100):
            create_test_task(db_session, project_id=project.id, title=f"性能测试任务{i}")

        mock_redis.get_json.return_value = None

        start_time = time.time()
        response = client.get("/api/tasks/")
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 1.5  # 响应时间应小于 1.5 秒

    def test_dashboard_stats_response_time(self, client, db_session, mock_redis):
        """测试仪表盘统计响应时间"""
        # 创建测试数据
        for i in range(30):
            create_test_project(db_session, name=f"项目{i}")
            create_test_agent(db_session, name=f"代理{i}")

        mock_redis.get_json.return_value = None

        start_time = time.time()
        response = client.get("/api/dashboard/stats")
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 1.0  # 响应时间应小于 1 秒

    def test_concurrent_requests_performance(self, client, db_session, mock_redis):
        """测试并发请求性能"""
        # 创建测试数据
        for i in range(20):
            create_test_project(db_session, name=f"并发项目{i}")

        mock_redis.get_json.return_value = None

        def make_request():
            start = time.time()
            response = client.get("/api/projects/")
            end = time.time()
            return response.status_code == 200, end - start

        # 并发发送 10 个请求
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in as_completed(futures)]

        success_count = sum(1 for success, _ in results if success)
        avg_response_time = sum(t for _, t in results) / len(results)

        assert success_count == 10  # 所有请求都应成功
        assert avg_response_time < 2.0  # 平均响应时间应小于 2 秒

    def test_large_dataset_pagination_performance(self, client, db_session, mock_redis):
        """测试大数据集分页性能"""
        # 创建大量数据
        for i in range(200):
            create_test_project(db_session, name=f"分页项目{i}")

        mock_redis.get_json.return_value = None

        # 测试不同页面的加载时间
        for page in [1, 5, 10]:
            start_time = time.time()
            response = client.get(f"/api/projects/?page={page}&page_size=20")
            end_time = time.time()

            assert response.status_code == 200
            assert end_time - start_time < 1.0  # 每页加载时间应小于 1 秒


@pytest.mark.performance
@pytest.mark.integration
class TestDatabasePerformance:
    """测试数据库性能"""

    def test_bulk_insert_performance(self, db_session):
        """测试批量插入性能"""
        start_time = time.time()

        # 批量插入项目
        projects = []
        for i in range(100):
            from app.models.project import Project
            projects.append(Project(name=f"批量项目{i}"))

        db_session.add_all(projects)
        db_session.commit()

        end_time = time.time()
        insert_time = end_time - start_time

        assert insert_time < 5.0  # 批量插入应在 5 秒内完成

    def test_query_performance_with_index(self, db_session):
        """测试带索引的查询性能"""
        # 创建测试数据
        for i in range(100):
            create_test_project(db_session, name=f"查询项目{i}")

        start_time = time.time()

        # 执行多次查询
        for i in range(50):
            db_session.query(create_test_project.__wrapped__.__globals__['Project']).filter_by(
                name=f"查询项目{i}"
            ).first()

        end_time = time.time()
        query_time = end_time - start_time

        assert query_time < 3.0  # 查询应在 3 秒内完成

    def test_complex_query_performance(self, db_session):
        """测试复杂查询性能"""
        from app.models.project import Project
        from app.models.task import Task

        # 创建测试数据
        for i in range(20):
            project = create_test_project(db_session, name=f"复杂查询项目{i}")
            for j in range(10):
                create_test_task(db_session, project_id=project.id, title=f"任务{j}")

        start_time = time.time()

        # 执行复杂查询（JOIN）
        results = db_session.query(Project, Task).join(
            Task, Project.id == Task.project_id
        ).filter(
            Project.name.like("%复杂查询%")
        ).all()

        end_time = time.time()
        query_time = end_time - start_time

        assert query_time < 2.0  # 复杂查询应在 2 秒内完成
        assert len(results) > 0

    def test_transaction_performance(self, db_session):
        """测试事务性能"""
        start_time = time.time()

        # 执行多个事务
        for i in range(50):
            project = create_test_project(db_session, name=f"事务项目{i}")
            create_test_task(db_session, project_id=project.id, title=f"事务任务{i}")
            db_session.commit()

        end_time = time.time()
        transaction_time = end_time - start_time

        assert transaction_time < 10.0  # 事务应在 10 秒内完成


@pytest.mark.performance
@pytest.mark.integration
class TestCachePerformance:
    """测试缓存性能"""

    def test_cache_hit_performance(self, client, db_session, mock_redis):
        """测试缓存命中性能"""
        # 设置缓存数据
        cached_data = {
            "items": [{"id": i, "name": f"项目{i}"} for i in range(50)],
            "total": 50
        }
        mock_redis.get_json.return_value = cached_data

        start_time = time.time()
        response = client.get("/api/projects/")
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 0.1  # 缓存命中应在 100ms 内完成

    def test_cache_miss_performance(self, client, db_session, mock_redis):
        """测试缓存未命中性能"""
        # 创建测试数据
        for i in range(50):
            create_test_project(db_session, name=f"缓存项目{i}")

        mock_redis.get_json.return_value = None

        start_time = time.time()
        response = client.get("/api/projects/")
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 2.0  # 缓存未命中应在 2 秒内完成
        mock_redis.set_json.assert_called_once()  # 验证缓存被设置


@pytest.mark.performance
@pytest.mark.integration
class TestMemoryPerformance:
    """测试内存性能"""

    def test_large_response_memory_usage(self, client, db_session, mock_redis):
        """测试大响应内存使用"""
        import psutil
        import os

        # 获取当前进程
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 创建大量数据
        for i in range(100):
            create_test_project(db_session, name=f"内存测试项目{i}")

        mock_redis.get_json.return_value = None

        # 请求大数据集
        response = client.get("/api/projects/?page_size=100")

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        assert response.status_code == 200
        assert memory_increase < 100  # 内存增加应小于 100MB


@pytest.mark.performance
@pytest.mark.integration
class TestLoadTesting:
    """负载测试"""

    @pytest.mark.slow
    def test_sustained_load(self, client, db_session, mock_redis):
        """测试持续负载"""
        # 创建测试数据
        for i in range(50):
            create_test_project(db_session, name=f"负载项目{i}")

        mock_redis.get_json.return_value = None

        # 持续发送请求 10 秒
        start_time = time.time()
        request_count = 0
        error_count = 0

        while time.time() - start_time < 10:
            try:
                response = client.get("/api/projects/")
                if response.status_code == 200:
                    request_count += 1
                else:
                    error_count += 1
            except Exception:
                error_count += 1

        # 验证性能指标
        assert request_count > 50  # 10 秒内应处理超过 50 个请求
        assert error_count / (request_count + error_count) < 0.1  # 错误率应小于 10%

    @pytest.mark.slow
    def test_burst_load(self, client, db_session, mock_redis):
        """测试突发负载"""
        # 创建测试数据
        for i in range(30):
            create_test_project(db_session, name=f"突发项目{i}")

        mock_redis.get_json.return_value = None

        def make_request():
            try:
                response = client.get("/api/projects/")
                return response.status_code == 200
            except Exception:
                return False

        # 突发 50 个并发请求
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [future.result() for future in as_completed(futures)]

        success_count = sum(results)
        success_rate = success_count / len(results)

        assert success_rate > 0.95  # 成功率应大于 95%
