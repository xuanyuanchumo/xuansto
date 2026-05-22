"""
调度队列模块 - 多策略任务调度系统

支持的调度策略:
- PRIORITY: 优先级队列，按Agent优先级调度
- FIFO: 先进先出，先到先服务
- FAIR_SHARE: 公平调度，按权重比例分配时间片

核心功能:
- DAG依赖关系解析与拓扑排序
- 任务生命周期管理
- 多队列并发支持
"""

from __future__ import annotations

import heapq
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple


class SchedulingStrategy(Enum):
    """调度策略枚举"""
    PRIORITY = "priority"
    FIFO = "fifo"
    FAIR_SHARE = "fair_share"


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = auto()
    READY = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass(order=True)
class ScheduledTask:
    """调度任务"""
    task_id: str = field(compare=False)
    agent_id: str = field(compare=False)
    priority: int  # 用于排序
    resources_required: List[str] = field(compare=False, default_factory=list)
    dependencies: List[str] = field(compare=False, default_factory=list)
    strategy: SchedulingStrategy = field(default=SchedulingStrategy.PRIORITY, compare=False)
    weight: float = 1.0  # Fair-share权重
    created_at: datetime = field(default_factory=datetime.now, compare=False)
    status: TaskStatus = field(default=TaskStatus.PENDING, compare=False)
    started_at: Optional[datetime] = field(default=None, compare=False)
    completed_at: Optional[datetime] = field(default=None, compare=False)
    error_message: Optional[str] = field(default=None, compare=False)
    retry_count: int = field(default=0, compare=False)
    max_retries: int = field(default=3, compare=False)


@dataclass
class DependencyEdge:
    """依赖边"""
    from_task: str
    to_task: str


class SchedulerQueue:
    """
    调度队列 - 任务编排与执行控制中心

    功能:
    - 支持多种调度策略的统一接口
    - 基于DAG的依赖管理
    - 任务状态跟踪与监控
    - 线程安全的并发操作

    使用示例:
        >>> scheduler = SchedulerQueue(strategy=SchedulingStrategy.PRIORITY)
        >>> task = scheduler.enqueue(
        ...     task_id="task_1",
        ...     agent_id="agent_1",
        ...     priority=8,
        ...     resources_required=["file_src", "terminal"],
        ... )
        >>> ready_tasks = scheduler.get_ready_tasks()
        >>> scheduler.start_task(task.task_id)
        >>> scheduler.complete_task(task.task_id)
    """

    def __init__(self, default_strategy: SchedulingStrategy = SchedulingStrategy.PRIORITY) -> None:
        self._default_strategy = default_strategy
        self._tasks: Dict[str, ScheduledTask] = {}
        self._dependency_graph: Dict[str, Set[str]] = defaultdict(set)  # task -> dependents
        self._reverse_deps: Dict[str, Set[str]] = defaultdict(set)  # task -> dependencies
        self._queues: Dict[SchedulingStrategy, any] = {
            SchedulingStrategy.PRIORITY: [],
            SchedulingStrategy.FIFO: deque(),
            SchedulingStrategy.FAIR_SHARE: [],
        }
        self._agent_weights: Dict[str, float] = defaultdict(lambda: 1.0)
        self._agent_usage: Dict[str, float] = defaultdict(float)
        self._lock = threading.RLock()
        self._task_counter: int = 0

    def enqueue(
        self,
        task_id: str,
        agent_id: str,
        priority: int = 5,
        resources_required: List[str] | None = None,
        dependencies: List[str] | None = None,
        strategy: SchedulingStrategy | None = None,
        weight: float = 1.0,
        max_retries: int = 3,
    ) -> Optional[ScheduledTask]:
        """
        入队新任务

        Args:
            task_id: 任务唯一标识
            agent_id: 执行任务的Agent ID
            priority: 优先级(1-10)，默认5
            resources_required: 所需资源ID列表
            dependencies: 依赖的任务ID列表
            strategy: 调度策略，None使用默认策略
            weight: Fair-share权重
            max_retries: 最大重试次数

        Returns:
            创建的ScheduledTask对象，如果参数无效返回None
        """
        if not task_id or not agent_id:
            return None

        if strategy is None:
            strategy = self._default_strategy

        task = ScheduledTask(
            task_id=task_id,
            agent_id=agent_id,
            priority=priority,
            resources_required=resources_required or [],
            dependencies=dependencies or [],
            strategy=strategy,
            weight=max(0.1, weight),
            max_retries=max_retries,
        )

        with self._lock:
            if task_id in self._tasks:
                return None

            for dep in task.dependencies:
                if dep not in self._tasks and dep != task_id:
                    self._dependency_graph[dep].add(task_id)
                    self._reverse_deps[task_id].add(dep)

            self._tasks[task_id] = task
            self._agent_weights[agent_id] = weight

            if not task.dependencies or all(d in self._tasks and self._tasks[d].status == TaskStatus.COMPLETED for d in task.dependencies):
                task.status = TaskStatus.READY
                self._add_to_queue(task)

            return task

    def dequeue(self) -> Optional[ScheduledTask]:
        """
        出队下一个就绪任务

        Returns:
            下一个可执行的任务或None
        """
        with self._lock:
            for strategy in [self._default_strategy, *SchedulingStrategy]:
                queue = self._queues.get(strategy)
                if queue is None:
                    continue

                task = self._get_from_queue(queue, strategy)
                if task and task.status == TaskStatus.READY:
                    return task

            return None

    def get_ready_tasks(self, limit: int = 10) -> List[ScheduledTask]:
        """
        获取所有就绪任务（不改变队列状态）

        Args:
            limit: 最大返回数量

        Returns:
            就绪任务列表（按优先级排序）
        """
        with self._lock:
            ready = []
            seen = set()

            for strategy in SchedulingStrategy:
                queue = self._queues.get(strategy)
                if queue is None:
                    continue

                tasks = self._peek_queue(queue, strategy)
                for task in tasks:
                    if task.task_id not in seen and task.status == TaskStatus.READY:
                        seen.add(task.task_id)
                        ready.append(task)

            ready.sort(key=lambda t: (-t.priority, t.created_at))
            return ready[:limit]

    def start_task(self, task_id: str) -> bool:
        """
        标记任务开始执行

        Args:
            task_id: 任务ID

        Returns:
            操作成功返回True
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or task.status != TaskStatus.READY:
                return False

            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            self._remove_from_all_queues(task_id)
            return True

    def complete_task(self, task_id: str, success: bool = True, error_message: str | None = None) -> bool:
        """
        标记任务完成/失败

        Args:
            task_id: 任务ID
            success: 是否成功完成
            error_message: 失败时的错误信息

        Returns:
            操作成功返回True
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or task.status != TaskStatus.RUNNING:
                return False

            task.completed_at = datetime.now()
            task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
            task.error_message = error_message

            if success:
                self._update_dependents(task_id)

            return True

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            取消成功返回True
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                return False

            old_status = task.status
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()

            self._remove_from_all_queues(task_id)

            if old_status == TaskStatus.RUNNING:
                self._cancel_dependents(task_id)

            return True

    def retry_task(self, task_id: str) -> bool:
        """
        重试失败的任务

        Args:
            task_id: 任务ID

        Returns:
            重试成功返回True
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or task.status != TaskStatus.FAILED:
                return False

            if task.retry_count >= task.max_retries:
                return False

            task.retry_count += 1
            task.error_message = None
            task.status = TaskStatus.READY
            task.started_at = None
            task.completed_at = None

            deps_met = all(
                dep not in self._tasks or self._tasks[dep].status == TaskStatus.COMPLETED
                for dep in task.dependencies
            )

            if deps_met:
                self._add_to_queue(task)

            return True

    def topological_sort(self) -> List[str]:
        """
        Kahn算法进行拓扑排序

        Returns:
            按依赖顺序排列的任务ID列表
        """
        with self._lock:
            in_degree: Dict[str, int] = {tid: 0 for tid in self._tasks}
            for tid, deps in self._reverse_deps.items():
                if tid in in_degree:
                    in_degree[tid] = len(deps)

            queue = deque([tid for tid, deg in in_degree.items() if deg == 0])
            result = []

            while queue:
                tid = queue.popleft()
                result.append(tid)

                for dependent in self._dependency_graph[tid]:
                    if dependent in in_degree:
                        in_degree[dependent] -= 1
                        if in_degree[dependent] == 0:
                            queue.append(dependent)

            if len(result) != len(self._tasks):
                remaining = set(self._tasks.keys()) - set(result)
                raise ValueError(f"Circular dependency detected among tasks: {remaining}")

            return result

    def has_cycle(self) -> bool:
        """检测是否存在循环依赖"""
        try:
            self.topological_sort()
            return False
        except ValueError:
            return True

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """获取任务详情"""
        with self._lock:
            return self._tasks.get(task_id)

    def get_tasks_by_agent(self, agent_id: str) -> List[ScheduledTask]:
        """获取Agent的所有任务"""
        with self._lock:
            return [t for t in self._tasks.values() if t.agent_id == agent_id]

    def get_tasks_by_status(self, status: TaskStatus) -> List[ScheduledTask]:
        """按状态获取任务"""
        with self._lock:
            return [t for t in self._tasks.values() if t.status == status]

    def get_statistics(self) -> Dict[str, any]:
        """获取调度器统计信息"""
        with self._lock:
            status_counts = defaultdict(int)
            for task in self._tasks.values():
                status_counts[task.status.name] += 1

            queue_sizes = {}
            for strategy, queue in self._queues.items():
                if strategy == SchedulingStrategy.PRIORITY:
                    queue_sizes[strategy.value] = len(queue)
                elif strategy == SchedulingStrategy.FIFO:
                    queue_sizes[strategy.value] = len(queue)
                elif strategy == SchedulingStrategy.FAIR_SHARE:
                    queue_sizes[strategy.value] = len(queue)

            return {
                "total_tasks": len(self._tasks),
                "by_status": dict(status_counts),
                "queue_sizes": queue_sizes,
                "agents_count": len(self._agent_weights),
                "has_cycles": self.has_cycle(),
            }

    def _add_to_queue(self, task: ScheduledTask) -> None:
        """将任务添加到对应策略队列"""
        queue = self._queues.get(task.strategy)
        if queue is None:
            return

        if task.strategy == SchedulingStrategy.PRIORITY:
            heapq.heappush(queue, (-task.priority, self._task_counter, task))
            self._task_counter += 1
        elif task.strategy == SchedulingStrategy.FIFO:
            queue.append(task)
        elif task.strategy == SchedulingStrategy.FAIR_SHARE:
            queue.append((task.weight, task.created_at, task))

    def _get_from_queue(self, queue: any, strategy: SchedulingStrategy) -> Optional[ScheduledTask]:
        """从队列中取出任务"""
        if strategy == SchedulingStrategy.PRIORITY:
            if queue:
                _, _, task = heapq.heappop(queue)
                return task
        elif strategy == SchedulingStrategy.FIFO:
            if queue:
                return queue.popleft()
        elif strategy == SchedulingStrategy.FAIR_SHARE:
            if queue:
                queue.sort(key=lambda x: (x[0], x[1]))
                _, _, task = queue.pop(0)
                return task
        return None

    def _peek_queue(self, queue: any, strategy: SchedulingStrategy) -> List[ScheduledTask]:
        """查看队列内容但不取出"""
        if strategy == SchedulingStrategy.PRIORITY:
            return [item[2] for item in queue]
        elif strategy == SchedulingStrategy.FIFO:
            return list(queue)
        elif strategy == SchedulingStrategy.FAIR_SHARE:
            return [item[2] for item in queue]
        return []

    def _remove_from_all_queues(self, task_id: str) -> None:
        """从所有队列中移除任务"""
        for strategy, queue in self._queues.items():
            if strategy == SchedulingStrategy.PRIORITY:
                self._queues[strategy] = [
                    item for item in queue if item[2].task_id != task_id
                ]
                heapq.heapify(self._queues[strategy])
            elif strategy == SchedulingStrategy.FIFO:
                new_deque = deque()
                for task in queue:
                    if task.task_id != task_id:
                        new_deque.append(task)
                self._queues[strategy] = new_deque
            elif strategy == SchedulingStrategy.FAIR_SHARE:
                self._queues[strategy] = [
                    item for item in queue if item[2].task_id != task_id
                ]

    def _update_dependents(self, completed_task_id: str) -> None:
        """更新依赖已完成任务的后继任务"""
        for dependent_id in self._dependency_graph[completed_task_id]:
            task = self._tasks.get(dependent_id)
            if task and task.status == TaskStatus.PENDING:
                deps_met = all(
                    dep not in self._tasks or self._tasks[dep].status == TaskStatus.COMPLETED
                    for dep in task.dependencies
                )
                if deps_met:
                    task.status = TaskStatus.READY
                    self._add_to_queue(task)

    def _cancel_dependents(self, cancelled_task_id: str) -> None:
        """取消依赖被取消任务的后继任务"""
        for dependent_id in self._dependency_graph[cancelled_task_id]:
            task = self._tasks.get(dependent_id)
            if task and task.status in (TaskStatus.PENDING, TaskStatus.READY):
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now()
                self._remove_from_all_queues(dependent_id)

    def __len__(self) -> int:
        with self._lock:
            return len(self._tasks)

    def __contains__(self, task_id: str) -> bool:
        with self._lock:
            return task_id in self._tasks
