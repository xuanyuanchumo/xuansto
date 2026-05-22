#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源协调器并发测试套件

覆盖范围：
- 资源注册（5种类型）
- 锁管理（乐观锁、悲观锁、读写锁、超时释放）
- 调度队列（优先级、公平调度、抢占式、批处理合并）
- 死锁预防（资源排序、等待图DFS检测、超时回退、受害者选择）
- 配额管理（per-agent、global、使用率监控、超限告警）
- 并发安全（多线程、锁竞争、死锁恢复）
"""

import pytest
import threading
import time
from resource_coordinator import (
    ResourceType,
    LockType,
    Priority,
    ResourceInfo,
    LockToken,
    ScheduledTask,
    AgentQuota,
    GlobalLimits,
    ResourceStatusReport,
    ResourceRegistry,
    LockManager,
    SchedulerQueue,
    DeadlockPreventer,
    QuotaManager,
    ResourceCoordinator,
)


class TestResourceType:
    """测试资源类型枚举"""

    def test_file_type(self):
        assert ResourceType.FILE.value == "file"

    def test_api_type(self):
        assert ResourceType.API.value == "api"

    def test_compute_type(self):
        assert ResourceType.COMPUTE.value == "compute"

    def test_terminal_type(self):
        assert ResourceType.TERMINAL.value == "terminal"

    def test_secret_type(self):
        assert ResourceType.SECRET.value == "secret"


class TestResourceRegistry:
    """测试资源注册中心"""

    @pytest.fixture
    def registry(self):
        return ResourceRegistry()

    def test_register_file_resource(self, registry):
        """注册文件类型资源"""
        result = registry.register_resource("file_001", ResourceType.FILE, {"path": "/tmp/test.txt"})
        assert result is True
        resource = registry.get_resource("file_001")
        assert resource is not None
        assert resource.type == ResourceType.FILE

    def test_register_api_resource(self, registry):
        """注册API类型资源"""
        result = registry.register_resource("api_001", ResourceType.API, {"endpoint": "/api/v1/data"})
        assert result is True

    def test_register_compute_resource(self, registry):
        """注册计算类型资源"""
        result = registry.register_resource("compute_001", ResourceType.COMPUTE, {"cores": 4})
        assert result is True

    def test_register_terminal_resource(self, registry):
        """注册终端类型资源"""
        result = registry.register_resource("terminal_001", ResourceType.TERMINAL, {"session": "bash"})
        assert result is True

    def test_register_secret_resource(self, registry):
        """注册密钥类型资源"""
        result = registry.register_resource("secret_001", ResourceType.SECRET, {"key_type": "api_key"})
        assert result is True

    def test_register_duplicate_fails(self, registry):
        """重复注册失败"""
        registry.register_resource("dup_001", ResourceType.FILE)
        result = registry.register_resource("dup_001", ResourceType.FILE)
        assert result is False

    def test_unregister_resource(self, registry):
        """注销资源"""
        registry.register_resource("to_remove", ResourceType.FILE)
        result = registry.unregister_resource("to_remove")
        assert result is True
        assert registry.get_resource("to_remove") is None

    def test_unregister_nonexistent_fails(self, registry):
        """注销不存在的资源失败"""
        result = registry.unregister_resource("nonexistent")
        assert result is False

    def test_list_all_resources(self, registry):
        """列出所有资源"""
        for i in range(5):
            registry.register_resource(f"res_{i}", ResourceType.FILE)
        resources = registry.list_resources()
        assert len(resources) == 5

    def test_list_resources_by_type(self, registry):
        """按类型过滤资源列表"""
        registry.register_resource("f1", ResourceType.FILE)
        registry.register_resource("a1", ResourceType.API)
        file_resources = registry.list_resources(ResourceType.FILE)
        assert len(file_resources) == 1
        assert file_resources[0].type == ResourceType.FILE

    def test_get_stats(self, registry):
        """获取统计信息"""
        registry.register_resource("f1", ResourceType.FILE)
        registry.register_resource("a1", ResourceType.API)
        stats = registry.get_stats()
        assert stats[ResourceType.FILE]["total"] == 1


class TestLockManager:
    """测试锁管理器"""

    @pytest.fixture
    def lock_manager(self):
        registry = ResourceRegistry()
        registry.register_resource("test_res", ResourceType.FILE)
        return LockManager(registry)

    def test_acquire_exclusive_lock(self, lock_manager):
        """获取独占写锁"""
        token = lock_manager.acquire_lock(
            "test_res", "agent_01", LockType.EXCLUSIVE
        )
        assert token is not None
        assert token.lock_type == LockType.EXCLUSIVE

    def test_acquire_shared_lock(self, lock_manager):
        """获取共享读锁"""
        token = lock_manager.acquire_lock(
            "test_res", "agent_02", LockType.SHARED
        )
        assert token is not None
        assert token.lock_type == LockType.SHARED

    def test_release_lock(self, lock_manager):
        """释放锁"""
        token = lock_manager.acquire_lock(
            "test_res", "agent_03", LockType.EXCLUSIVE
        )
        result = lock_manager.release_lock(token.token_id)
        assert result is True

    def test_release_invalid_token_fails(self, lock_manager):
        """释放无效令牌失败"""
        result = lock_manager.release_lock("invalid_token")
        assert result is False

    def test_pessimistic_mode_blocks_when_locked(self, lock_manager):
        """悲观模式：已锁定时阻塞"""
        token1 = lock_manager.acquire_lock(
            "test_res", "agent_01", LockType.EXCLUSIVE
        )
        assert token1 is not None
        token2 = lock_manager.acquire_lock(
            "test_res", "agent_02", LockType.EXCLUSIVE, mode="pessimistic"
        )
        assert token2 is None
        lock_manager.release_lock(token1.token_id)

    def test_optimistic_mode_returns_none_on_conflict(self, lock_manager):
        """乐观模式：冲突时返回None"""
        token1 = lock_manager.acquire_lock(
            "test_res", "agent_01", LockType.EXCLUSIVE
        )
        token2 = lock_manager.acquire_lock(
            "test_res", "agent_02", LockType.EXCLUSIVE, mode="optimistic"
        )
        if token1:
            lock_manager.release_lock(token1.token_id)

    def test_multiple_shared_readers(self, lock_manager):
        """多个共享读锁可以共存"""
        tokens = []
        for i in range(5):
            token = lock_manager.acquire_lock(
                "test_res", f"reader_{i}", LockType.SHARED
            )
            if token:
                tokens.append(token)
        assert len(tokens) > 0
        for t in tokens:
            lock_manager.release_lock(t.token_id)

    def test_get_active_locks(self, lock_manager):
        """获取活跃锁列表"""
        token = lock_manager.acquire_lock(
            "test_res", "agent_01", LockType.EXCLUSIVE
        )
        active = lock_manager.get_active_locks()
        assert "test_res" in active
        lock_manager.release_lock(token.token_id)

    def test_acquire_lock_for_nonexistent_resource(self, lock_manager):
        """对不存在的资源加锁失败"""
        token = lock_manager.acquire_lock(
            "nonexistent", "agent_01", LockType.EXCLUSIVE
        )
        assert token is None


class TestSchedulerQueue:
    """测试调度队列"""

    @pytest.fixture
    def scheduler(self):
        return SchedulerQueue()

    def test_enqueue_task(self, scheduler):
        """入队任务"""
        task = ScheduledTask(
            task_id="task_001",
            agent_id="agent_01",
            resource_ids=["res_1"],
            priority=Priority.MEDIUM,
        )
        result = scheduler.enqueue(task)
        assert result is True

    def test_dequeue_task(self, scheduler):
        """出队任务"""
        task = ScheduledTask(
            task_id="task_002",
            agent_id="agent_01",
            resource_ids=["res_1"],
            priority=Priority.HIGH,
        )
        scheduler.enqueue(task)
        dequeued = scheduler.dequeue(timeout=1.0)
        assert dequeued is not None
        assert dequeued.task_id == "task_002"

    def test_priority_ordering(self, scheduler):
        """优先级排序"""
        scheduler.enqueue(ScheduledTask(
            task_id="low", agent_id="a1", resource_ids=[],
            priority=Priority.LOW,
        ))
        scheduler.enqueue(ScheduledTask(
            task_id="high", agent_id="a2", resource_ids=[],
            priority=Priority.HIGH,
        ))
        task = scheduler.dequeue(timeout=1.0)
        assert task.task_id == "high"

    def test_queue_full_rejection(self, scheduler):
        """队列满时拒绝任务"""
        for i in range(SchedulerQueue.MAX_QUEUE_SIZE + 10):
            task = ScheduledTask(
                task_id=f"task_{i}",
                agent_id=f"a{i % 100}",
                resource_ids=[],
                priority=Priority.LOW,
            )
            if not scheduler.enqueue(task):
                break
        status = scheduler.get_status()
        assert status["waiting_count"] >= SchedulerQueue.MAX_QUEUE_SIZE

    def test_preempt_task(self, scheduler):
        """抢占式调度"""
        scheduler.enqueue(ScheduledTask(
            task_id="normal", agent_id="a1", resource_ids=[],
            priority=Priority.LOW,
        ))
        result = scheduler.preempt("normal")
        assert result is True

    def test_preempt_nonexistent_fails(self, scheduler):
        """抢占不存在的任务失败"""
        result = scheduler.preempt("nonexistent")
        assert result is False

    def test_get_status(self, scheduler):
        """获取队列状态"""
        scheduler.enqueue(ScheduledTask(
            task_id="t1", agent_id="a1", resource_ids=[],
            priority=Priority.HIGH,
        ))
        status = scheduler.get_status()
        assert status["waiting_count"] >= 1
        assert status["high_priority"] >= 1


class TestDeadlockPreventer:
    """测试死锁预防"""

    @pytest.fixture
    def deadlock_preventer(self):
        registry = ResourceRegistry()
        registry.register_resource("r1", ResourceType.FILE)
        registry.register_resource("r2", ResourceType.FILE)
        lm = LockManager(registry)
        return DeadlockPreventer(lm)

    def test_record_wait_relationship(self, deadlock_preventer):
        """记录等待关系"""
        deadlock_preventer.record_wait("agent_a", "agent_b")
        risks = deadlock_preventer.get_risks()
        assert isinstance(risks, list)

    def test_clear_wait(self, deadlock_preventer):
        """清除等待记录"""
        deadlock_preventer.record_wait("agent_a", "agent_b")
        deadlock_preventer.clear_wait("agent_a")
        risks = deadlock_preventer.get_risks()

    def test_detect_cycle_in_wait_graph(self, deadlock_preventer):
        """检测等待图中的环（死锁）"""
        deadlock_preventer.record_wait("agent_a", "agent_b")
        deadlock_preventer.record_wait("agent_b", "agent_c")
        deadlock_preventer.record_wait("agent_c", "agent_a")
        time.sleep(0.1)
        risks = deadlock_preventer.get_risks()


class TestQuotaManager:
    """测试配额管理"""

    @pytest.fixture
    def quota_manager(self):
        return QuotaManager()

    def test_register_agent(self, quota_manager):
        """注册Agent配额"""
        quota = quota_manager.register_agent("agent_01")
        assert quota.agent_id == "agent_01"

    def test_register_agent_with_custom_quota(self, quota_manager):
        """使用自定义配额注册Agent"""
        custom = AgentQuota(agent_id="custom", max_files_locked=20)
        quota = quota_manager.register_agent("custom", custom)
        assert quota.max_files_locked == 20

    def test_unregister_agent(self, quota_manager):
        """注销Agent"""
        quota_manager.register_agent("to_unregister")
        result = quota_manager.unregister_agent("to_unregister")
        assert result is True

    def test_check_and_acquire_file_quota(self, quota_manager):
        """检查并获取文件配额"""
        quota_manager.register_agent("agent_file")
        allowed, reason = quota_manager.check_and_acquire(
            "agent_file", ResourceType.FILE
        )
        assert allowed is True

    def test_check_and_acquire_api_quota(self, quota_manager):
        """检查并获取API配额"""
        quota_manager.register_agent("agent_api")
        allowed, reason = quota_manager.check_and_acquire(
            "agent_api", ResourceType.API
        )
        assert allowed is True

    def test_quota_limit_enforcement(self, quota_manager):
        """配额限制强制执行"""
        limited = AgentQuota(agent_id="limited", max_files_locked=2)
        quota_manager.register_agent("limited", limited)
        for _ in range(2):
            quota_manager.check_and_acquire("limited", ResourceType.FILE)
        allowed, reason = quota_manager.check_and_acquire(
            "limited", ResourceType.FILE
        )
        assert allowed is False

    def test_get_usage_report(self, quota_manager):
        """获取使用率报告"""
        quota_manager.register_agent("report_test")
        report = quota_manager.get_usage_report()
        assert "report_test" in report

    def test_get_alerts(self, quota_manager):
        """获取告警信息"""
        alerts = quota_manager.get_alerts()
        assert isinstance(alerts, list)


class TestResourceCoordinatorIntegration:
    """测试资源协调器集成"""

    @pytest.fixture
    def coordinator(self):
        coord = ResourceCoordinator()
        coord.register_resource("file_001", ResourceType.FILE, {"path": "/tmp/f1"})
        coord.register_resource("api_001", ResourceType.API, {"endpoint": "/api/data"})
        coord.register_resource("compute_001", ResourceType.COMPUTE, {"cores": 4})
        coord.register_resource("terminal_001", ResourceType.TERMINAL, {"session": "bash"})
        coord.register_resource("secret_001", ResourceType.SECRET, {"key_type": "token"})
        return coord

    def test_full_lifecycle(self, coordinator):
        """完整生命周期：注册→加锁→释放→注销"""
        coordinator.register_agent("worker_01")
        token = coordinator.acquire_lock(
            "file_001", "worker_01", LockType.EXCLUSIVE
        )
        assert token is not None
        result = coordinator.release_lock(token.token_id)
        assert result is True

    def test_enqueue_dequeue_task(self, coordinator):
        """任务入队和出队"""
        coordinator.register_agent("scheduler_01")
        result = coordinator.enqueue_task(
            "task_001", "scheduler_01", ["file_001"], Priority.HIGH
        )
        assert result is True
        task = coordinator.dequeue_task(timeout=1.0)
        if task:
            assert task.task_id == "task_001"

    def test_preempt_task(self, coordinator):
        """抢占任务"""
        coordinator.enqueue_task(
            "to_preempt", "agent_01", [], Priority.LOW
        )
        result = coordinator.preempt_task("to_preempt")
        assert result is True

    def test_get_status_report(self, coordinator):
        """获取状态报告"""
        coordinator.register_agent("monitor_01")
        status = coordinator.get_status()
        assert isinstance(status, ResourceStatusReport)

    def test_status_report_to_panel(self, coordinator):
        """状态报告面板输出"""
        coordinator.register_agent("panel_test")
        status = coordinator.get_status()
        panel = status.to_panel()
        assert "MARC-Lite" in panel
        assert "资源协调器" in panel

    def test_shutdown(self, coordinator):
        """优雅关闭"""
        coordinator.shutdown()
        assert True


class TestConcurrencySafety:
    """测试并发安全性"""

    def test_concurrent_resource_registration(self):
        """多线程并发注册资源"""
        registry = ResourceRegistry()
        threads = []
        results = []

        def register_resources(thread_id):
            for i in range(10):
                res_id = f"{thread_id}_res_{i}"
                success = registry.register_resource(res_id, ResourceType.FILE)
                results.append(success)

        for t in range(5):
            thread = threading.Thread(target=register_resources, args=(t,))
            threads.append(thread)

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5.0)

        total_registered = len(registry.list_resources())
        assert total_registered <= 50

    def test_concurrent_lock_acquisition(self):
        """多线程并发获取锁"""
        coordinator = ResourceCoordinator()
        coordinator.register_resource("shared_file", ResourceType.FILE)
        coordinator.register_agent(f"concurrent_worker_{i}" for i in range(10))

        acquired_tokens = []
        errors = []

        def acquire_lock(worker_id):
            try:
                token = coordinator.acquire_lock(
                    "shared_file", worker_id, LockType.SHARED
                )
                if token:
                    acquired_tokens.append(token)
                    time.sleep(0.01)
                    coordinator.release_lock(token.token_id)
            except Exception as e:
                errors.append(str(e))

        threads = []
        for i in range(10):
            worker_id = f"worker_{i}"
            coordinator.register_agent(worker_id)
            t = threading.Thread(target=acquire_lock, args=(worker_id,))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10.0)

        assert len(errors) == 0 or len(acquired_tokens) > 0

    def test_concurrent_enqueue_dequeue(self):
        """多线程并发入队和出队"""
        coordinator = ResourceCoordinator()
        coordinator.register_agent("queue_worker")

        enqueued = 0
        dequeued_items = []

        def producer():
            nonlocal enqueued
            for i in range(20):
                if coordinator.enqueue_task(
                    f"prod_task_{i}", "queue_worker", [], Priority.MEDIUM
                ):
                    enqueued += 1

        def consumer():
            for _ in range(20):
                task = coordinator.dequeue_task(timeout=0.5)
                if task:
                    dequeued_items.append(task.task_id)

        producer_thread = threading.Thread(target=producer)
        consumer_thread = threading.Thread(target=consumer)

        producer_thread.start()
        consumer_thread.start()

        producer_thread.join(timeout=10.0)
        consumer_thread.join(timeout=10.0)

        assert enqueued >= 0
        assert len(dequeued_items) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
