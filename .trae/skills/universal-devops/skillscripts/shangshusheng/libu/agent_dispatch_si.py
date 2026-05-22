"""
Agent调度司 - 智能Agent分配、任务队列管理、负载均衡
"""
from __future__ import annotations

import hashlib
import heapq
import random
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class AgentDispatchError(Exception):
    """Agent调度相关异常"""
    pass


class AgentStatus(str, Enum):
    """Agent状态枚举"""
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class QueueStrategy(str, Enum):
    """队列策略枚举"""
    PRIORITY = "priority"
    FIFO = "fifo"
    LIFO = "lifo"


class BalanceStrategy(str, Enum):
    """负载均衡策略枚举"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_RANDOM = "weighted_random"
    CONSISTENT_HASH = "consistent_hash"


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


@dataclass(order=True)
class PriorityTask:
    """优先级任务（用于堆排序）"""
    priority: int
    task_id: str = field(compare=False)
    payload: dict[str, Any] = field(compare=False)
    created_at: float = field(compare=False, default_factory=time.time)
    retries: int = field(compare=False, default=0)
    max_retries: int = field(compare=False, default=3)
    timeout: float = field(compare=False, default=300.0)
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    """任务执行结果"""
    task_id: str
    status: TaskStatus
    agent_name: str | None = None
    result: Any = None
    error: str | None = None
    started_at: float | None = None
    completed_at: float | None = None
    duration_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "agent_name": self.agent_name,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
        }


@dataclass
class AgentNode:
    """Agent节点信息"""
    name: str
    status: AgentStatus = AgentStatus.IDLE
    max_concurrent: int = 5
    current_tasks: int = 0
    weight: int = 1
    total_completed: int = 0
    total_failed: int = 0
    last_heartbeat: float = field(default_factory=time.time)
    capabilities: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_available(self) -> bool:
        return (
            self.status == AgentStatus.IDLE
            and self.current_tasks < self.max_concurrent
        )

    @property
    def load_ratio(self) -> float:
        if self.max_concurrent == 0:
            return 1.0
        return self.current_tasks / self.max_concurrent

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "max_concurrent": self.max_concurrent,
            "current_tasks": self.current_tasks,
            "weight": self.weight,
            "is_available": self.is_available,
            "load_ratio": round(self.load_ratio, 4),
            "total_completed": self.total_completed,
            "total_failed": self.total_failed,
            "capabilities": self.capabilities,
        }


class AgentDispatchSi:
    """
    Agent调度司

    负责智能Agent分配、任务队列管理、负载均衡。
    支持多种队列策略、负载均衡算法和任务依赖拓扑排序执行。
    """

    _instance: AgentDispatchSi | None = None

    def __init__(
        self,
        queue_strategy: QueueStrategy = QueueStrategy.PRIORITY,
        balance_strategy: BalanceStrategy = BalanceStrategy.LEAST_CONNECTIONS,
        max_concurrent_agents: int = 50,
    ) -> None:
        self._queue_strategy = queue_strategy
        self._balance_strategy = balance_strategy
        self._max_concurrent_agents = max_concurrent_agents

        self._agents: dict[str, AgentNode] = {}
        self._task_queue: deque[PriorityTask] = deque()
        self._priority_heap: list[PriorityTask] = []
        self._running_tasks: dict[str, PriorityTask] = {}
        self._task_results: dict[str, TaskResult] = {}
        self._task_dependencies: dict[str, list[str]] = {}

        self._round_robin_index: int = 0
        self._lock: threading.RLock = threading.RLock()
        self._hash_ring: dict[int, str] = {}
        self._virtual_nodes: int = 150

        self._stats: dict[str, Any] = {
            "tasks_submitted": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_timeout": 0,
            "avg_dispatch_time_ms": 0.0,
        }

    @classmethod
    def get_instance(cls) -> AgentDispatchSi:
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_agent(
        self,
        name: str,
        capabilities: list[str] | None = None,
        max_concurrent: int = 5,
        weight: int = 1,
        **kwargs: Any,
    ) -> AgentNode:
        """
        注册Agent节点

        Args:
            name: Agent名称
            capabilities: 能力列表
            max_concurrent: 最大并发数
            weight: 权重（用于加权随机）
            **kwargs: 其他属性

        Returns:
            注册的AgentNode对象

        Raises:
            AgentDispatchError: 当Agent名称已存在时
        """
        with self._lock:
            if name in self._agents:
                raise AgentDispatchError(f"Agent已注册: {name}")

            node = AgentNode(
                name=name,
                capabilities=capabilities or [],
                max_concurrent=max_concurrent,
                weight=weight,
                **kwargs,
            )
            self._agents[name] = node
            self._rebuild_hash_ring()
            return node

    def unregister_agent(self, name: str) -> bool:
        """
        注销Agent节点

        Args:
            name: Agent名称

        Returns:
            是否成功注销
        """
        with self._lock:
            if name not in self._agents:
                return False
            if self._agents[name].current_tasks > 0:
                raise AgentDispatchError(f"Agent {name} 仍有运行中的任务，无法注销")
            del self._agents[name]
            self._rebuild_hash_ring()
            return True

    def update_agent_status(self, name: str, status: AgentStatus) -> None:
        """
        更新Agent状态

        Args:
            name: Agent名称
            status: 新状态

        Raises:
            AgentDispatchError: 当Agent不存在时
        """
        with self._lock:
            if name not in self._agents:
                raise AgentDispatchError(f"Agent不存在: {name}")
            self._agents[name].status = status
            if status == AgentStatus.IDLE:
                self._agents[name].last_heartbeat = time.time()

    def submit_task(
        self,
        payload: dict[str, Any],
        priority: int = 5,
        task_id: str | None = None,
        dependencies: list[str] | None = None,
        timeout: float = 300.0,
        max_retries: int = 3,
        **metadata: Any,
    ) -> str:
        """
        提交任务到队列

        Args:
            payload: 任务负载数据
            priority: 优先级（数值越小优先级越高）
            task_id: 可选的任务ID，自动生成如果未提供
            dependencies: 任务依赖列表
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
            **metadata: 额外元数据

        Returns:
            任务ID
        """
        tid = task_id or f"task_{uuid.uuid4().hex[:12]}"

        task = PriorityTask(
            priority=priority,
            task_id=tid,
            payload=payload,
            timeout=timeout,
            max_retries=max_retries,
            dependencies=dependencies or [],
            metadata=dict(metadata),
        )

        with self._lock:
            match self._queue_strategy:
                case QueueStrategy.PRIORITY:
                    heapq.heappush(self._priority_heap, task)
                case QueueStrategy.FIFO:
                    self._task_queue.append(task)
                case QueueStrategy.LIFO:
                    self._task_queue.appendleft(task)

            if dependencies:
                self._task_dependencies[tid] = dependencies

            self._stats["tasks_submitted"] += 1

        return tid

    def dispatch(self, task_key: str | None = None) -> TaskResult | None:
        """
        分派任务给可用Agent

        Args:
            task_key: 可选的任务ID或自动选择下一个就绪任务

        Returns:
            TaskResult对象，如果没有可分派的任务则返回None
        """
        with self._lock:
            task = self._pick_next_task(task_key)
            if task is None:
                return None

            agent = self._select_agent(task)
            if agent is None:
                match self._queue_strategy:
                    case QueueStrategy.PRIORITY:
                        heapq.heappush(self._priority_heap, task)
                    case _:
                        self._task_queue.append(task)
                return None

            agent.current_tasks += 1
            agent.status = AgentStatus.BUSY
            self._running_tasks[task.task_id] = task

        result = TaskResult(
            task_id=task.task_id,
            status=TaskStatus.RUNNING,
            agent_name=agent.name,
            started_at=time.time(),
        )

        self._task_results[task.task_id] = result
        return result

    def complete_task(
        self,
        task_id: str,
        success: bool = True,
        result: Any = None,
        error: str | None = None,
    ) -> TaskResult:
        """
        标记任务完成

        Args:
            task_id: 任务ID
            success: 是否成功
            result: 执行结果
            error: 错误信息

        Returns:
            更新后的TaskResult对象

        Raises:
            AgentDispatchError: 当任务不存在时
        """
        with self._lock:
            if task_id not in self._task_results:
                raise AgentDispatchError(f"任务不存在: {task_id}")

            existing_result = self._task_results[task_id]
            task = self._running_tasks.pop(task_id, None)

            if task and existing_result.agent_name:
                agent = self._agents.get(existing_result.agent_name)
                if agent:
                    agent.current_tasks -= 1
                    if agent.current_tasks == 0:
                        agent.status = AgentStatus.IDLE
                    if success:
                        agent.total_completed += 1
                    else:
                        agent.total_failed += 1

            now = time.time()
            duration = None
            if existing_result.started_at:
                duration = (now - existing_result.started_at) * 1000

            if success:
                final_status = TaskStatus.COMPLETED
                self._stats["tasks_completed"] += 1
            else:
                if task and task.retries < task.max_retries:
                    final_status = TaskStatus.RETRYING
                    task.retries += 1
                    match self._queue_strategy:
                        case QueueStrategy.PRIORITY:
                            heapq.heappush(self._priority_heap, task)
                        case _:
                            self._task_queue.append(task)
                else:
                    final_status = TaskStatus.FAILED
                    self._stats["tasks_failed"] += 1

            updated = TaskResult(
                task_id=task_id,
                status=final_status,
                agent_name=existing_result.agent_name,
                result=result,
                error=error,
                started_at=existing_result.started_at,
                completed_at=now,
                duration_ms=round(duration, 2) if duration else None,
            )
            self._task_results[task_id] = updated
            return updated

    def check_timeouts(self) -> list[TaskResult]:
        """
        检查并处理超时任务

        Returns:
            超时的TaskResult列表
        """
        now = time.time()
        timed_out: list[TaskResult] = []

        with self._lock:
            for task_id, task in list(self._running_tasks.items()):
                elapsed = now - (self._task_results[task_id].started_at or now)
                if elapsed > task.timeout:
                    result = self.complete_task(
                        task_id, success=False, error=f"任务超时 ({elapsed:.1f}s > {task.timeout}s)"
                    )
                    if result.status == TaskStatus.TIMEOUT:
                        pass
                    timed_out.append(result)
                    self._stats["tasks_timeout"] += 1

        return timed_out

    def get_ready_tasks(self) -> list[str]:
        """
        获取所有依赖已满足的待处理任务ID列表

        Returns:
            就绪任务ID列表
        """
        completed_ids: set[str] = {
            tid for tid, r in self._task_results.items()
            if r.status == TaskStatus.COMPLETED
        }

        ready: list[str] = []
        all_pending: list[PriorityTask] = list(self._priority_heap) + list(self._task_queue)

        for task in all_pending:
            if task.task_id in self._running_tasks:
                continue
            if all(dep in completed_ids for dep in task.dependencies):
                ready.append(task.task_id)

        return ready

    def topological_sort(self) -> list[str]:
        """
        对带依赖关系的任务进行拓扑排序

        Returns:
            按依赖顺序排列的任务ID列表

        Raises:
            AgentDispatchError: 当检测到循环依赖时
        """
        in_degree: dict[str, int] = {tid: 0 for tid in self._task_dependencies}
        graph: dict[str, list[str]] = defaultdict(list)

        for tid, deps in self._task_dependencies.items():
            in_degree.setdefault(tid, 0)
            for dep in deps:
                graph[dep].append(tid)
                in_degree[tid] = in_degree.get(tid, 0) + 1

        queue: deque[str] = deque(tid for tid, deg in in_degree.items() if deg == 0)
        sorted_order: list[str] = []

        while queue:
            node = queue.popleft()
            sorted_order.append(node)
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_order) != len(in_degree):
            remaining = set(in_degree.keys()) - set(sorted_order)
            raise AgentDispatchError(f"检测到循环依赖，涉及任务: {remaining}")

        return sorted_order

    def detect_deadlock(self) -> list[list[str]]:
        """
        检测死锁（循环等待）

        Returns:
            循环依赖链列表
        """
        cycles: list[list[str]] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self._task_dependencies.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])

            path.pop()
            rec_stack.remove(node)

        for tid in self._task_dependencies:
            if tid not in visited:
                dfs(tid)

        return cycles

    def _pick_next_task(self, task_key: str | None = None) -> PriorityTask | None:
        """选择下一个要执行的任务"""
        if task_key:
            match self._queue_strategy:
                case QueueStrategy.PRIORITY:
                    for i, t in enumerate(self._priority_heap):
                        if t.task_id == task_key:
                            self._priority_heap.pop(i)
                            heapq.heapify(self._priority_heap)
                            return t
                case QueueStrategy.FIFO:
                    for i, t in enumerate(self._task_queue):
                        if t.task_id == task_key:
                            return self._task_queue.pop(i)
                case QueueStrategy.LIFO:
                    for i, t in enumerate(self._task_queue):
                        if t.task_id == task_key:
                            return self._task_queue.pop(i)
            return None

        ready = set(self.get_ready_tasks())

        match self._queue_strategy:
            case QueueStrategy.PRIORITY:
                temp: list[PriorityTask] = []
                selected = None
                while self._priority_heap:
                    t = heapq.heappop(self._priority_heap)
                    if t.task_id in ready and t.task_id not in self._running_tasks:
                        selected = t
                        break
                    temp.append(t)
                for t in temp:
                    heapq.heappush(self._priority_heap, t)
                return selected
            case QueueStrategy.FIFO:
                for t in self._task_queue:
                    if t.task_id in ready and t.task_id not in self._running_tasks:
                        self._task_queue.remove(t)
                        return t
                return None
            case QueueStrategy.LIFO:
                for t in reversed(self._task_queue):
                    if t.task_id in ready and t.task_id not in self._running_tasks:
                        self._task_queue.remove(t)
                        return t
                return None
            case _:
                return None

    def _select_agent(self, task: PriorityTask) -> AgentNode | None:
        """根据负载均衡策略选择Agent"""
        available = [
            a for a in self._agents.values()
            if a.is_available
        ]

        if not available:
            return None

        match self._balance_strategy:
            case BalanceStrategy.ROUND_ROBIN:
                if not available:
                    return None
                agent = available[self._round_robin_index % len(available)]
                self._round_robin_index += 1
                return agent

            case BalanceStrategy.LEAST_CONNECTIONS:
                return min(available, key=lambda a: a.current_tasks)

            case BalanceStrategy.WEIGHTED_RANDOM:
                total_weight = sum(a.weight for a in available)
                if total_weight <= 0:
                    return random.choice(available)
                r = random.randint(1, total_weight)
                cumulative = 0
                for agent in available:
                    cumulative += agent.weight
                    if r <= cumulative:
                        return agent
                return available[-1]

            case BalanceStrategy.CONSISTENT_HASH:
                task_hash = hashlib.md5(task.task_id.encode()).hexdigest()
                hash_int = int(task_hash, 16) % (2**32)
                return self._get_hash_ring_node(hash_int)

            case _:
                return min(available, key=lambda a: a.load_ratio)

    def _rebuild_hash_ring(self) -> None:
        """重建一致性哈希环"""
        self._hash_ring.clear()
        for agent in self._agents.values():
            for i in range(self._virtual_nodes):
                key = f"{agent.name}:{i}"
                hash_int = int(hashlib.md5(key.encode()).hexdigest(), 16) % (2**32)
                self._hash_ring[hash_int] = agent.name

    def _get_hash_ring_node(self, hash_int: int) -> AgentNode | None:
        """在哈希环上查找最近的节点"""
        if not self._hash_ring:
            return None
        keys = sorted(self._hash_ring.keys())
        for k in keys:
            if k >= hash_int:
                return self._agents.get(self._hash_ring[k])
        return self._agents.get(self._hash_ring[keys[0]])

    @property
    def queue_size(self) -> int:
        return len(self._priority_heap) + len(self._task_queue)

    @property
    def running_count(self) -> int:
        return len(self._running_tasks)

    @property
    def agent_count(self) -> int:
        return len(self._agents)

    @property
    def available_agent_count(self) -> int:
        return sum(1 for a in self._agents.values() if a.is_available)

    def get_task_status(self, task_id: str) -> TaskResult | None:
        """获取任务状态"""
        return self._task_results.get(task_id)

    def get_all_agents(self) -> dict[str, AgentNode]:
        return dict(self._agents)

    def get_stats(self) -> dict[str, Any]:
        return {
            **self._stats,
            "queue_size": self.queue_size,
            "running_count": self.running_count,
            "agent_count": self.agent_count,
            "available_agents": self.available_agent_count,
            "queue_strategy": self._queue_strategy.value,
            "balance_strategy": self._balance_strategy.value,
        }

    def clear_queue(self) -> int:
        """清空待处理队列，返回清除的任务数"""
        count = self.queue_size
        self._priority_heap.clear()
        self._task_queue.clear()
        return count

    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            "tasks_submitted": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_timeout": 0,
            "avg_dispatch_time_ms": 0.0,
        }

    def __repr__(self) -> str:
        return (
            f"AgentDispatchSi(agents={self.agent_count}, "
            f"queue={self.queue_size}, running={self.running_count})"
        )


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Agent调度司测试")
    print("=" * 60)

    dispatch = AgentDispatchSi(
        queue_strategy=QueueStrategy.PRIORITY,
        balance_strategy=BalanceStrategy.LEAST_CONNECTIONS,
    )

    print("\n--- 注册Agent ---")
    agents_data = [
        ("Builder-Agent", ["code_generation", "build"], 5, 3),
        ("Tester-Agent", ["testing", "qa"], 8, 2),
        ("Deployer-Agent", ["deployment", "ops"], 3, 5),
        ("Reviewer-Agent", ["review", "analysis"], 6, 2),
    ]
    for name, caps, max_c, w in agents_data:
        agent = dispatch.register_agent(name=name, capabilities=caps, max_concurrent=max_c, weight=w)
        print(f"   ✅ 已注册: {name} (并发上限={max_c}, 权重={w})")

    print(f"\n--- 队列策略: {dispatch._queue_strategy.value} ---")
    print(f"--- 均衡策略: {dispatch._balance_strategy.value} ---")

    print("\n--- 提交任务 ---")
    task_ids: list[str] = []

    task_ids.append(dispatch.submit_task(
        payload={"action": "build", "target": "module-a"},
        priority=1,
        task_id="T001",
    ))
    print(f"   📥 T001 (优先级=1): 构建模块A")

    task_ids.append(dispatch.submit_task(
        payload={"action": "test", "target": "module-a"},
        priority=2,
        task_id="T002",
        dependencies=["T001"],
    ))
    print(f"   📥 T002 (优先级=2, 依赖=T001): 测试模块A")

    task_ids.append(dispatch.submit_task(
        payload={"action": "deploy", "target": "prod"},
        priority=3,
        task_id="T003",
        dependencies=["T002"],
    ))
    print(f"   📥 T003 (优先级=3, 依赖=[T002]): 部署生产环境")

    task_ids.append(dispatch.submit_task(
        payload={"action": "review", "target": "pr-42"},
        priority=1,
        task_id="T004",
    ))
    print(f"   📥 T004 (优先级=1): 审查PR#42")

    task_ids.append(dispatch.submit_task(
        payload={"action": "build", "target": "module-b"},
        priority=2,
        task_id="T005",
    ))
    print(f"   📥 T005 (优先级=2): 构建模块B")

    print(f"\n   📊 队列中任务数: {dispatch.queue_size}")

    print("\n--- 分派任务 ---")
    for _ in range(4):
        result = dispatch.dispatch()
        if result:
            print(f"   ✅ {result.task_id} → {result.agent_name}")
        else:
            print(f"   ⚠️ 无可用Agent或无就绪任务")

    print("\n--- 完成任务 ---")
    dispatch.complete_task("T001", success=True, result="构建成功")
    print(f"   ✅ T001 完成")

    result = dispatch.dispatch()
    if result:
        print(f"   ✅ 依赖满足后分派: {result.task_id} → {result.agent_name}")

    dispatch.complete_task("T002", success=True, result="测试通过")
    print(f"   ✅ T002 完成")

    dispatch.complete_task("T004", success=True, result="审查通过")
    print(f"   ✅ T004 完成")

    dispatch.complete_task("T003", success=False, error="部署失败: 配置错误")
    print(f"   ⚠️ T003 失败 (将重试)")

    print("\n--- Agent状态 ---")
    for name, agent in dispatch.get_all_agents().items():
        status_icon = {"idle": "🟢", "busy": "🔵", "offline": "⚫", "maintenance": "🟠"}
        icon = status_icon.get(agent.status.value, "❓")
        print(f"   {icon} {name}: 状态={agent.status.value}, "
              f"当前任务={agent.current_tasks}/{agent.max_concurrent}, "
              f"负载率={agent.load_ratio:.2%}")

    print("\n--- 拓扑排序 ---")
    try:
        order = dispatch.topological_sort()
        print(f"   🔗 执行顺序: {' → '.join(order)}")
    except AgentDispatchError as e:
        print(f"   ❌ {e}")

    print("\n--- 死锁检测 ---")
    cycles = dispatch.detect_deadlock()
    if cycles:
        print(f"   ⚠️ 发现 {len(cycles)} 个循环:")
        for c in cycles:
            print(f"      {' → '.join(c)}")
    else:
        print(f"   ✅ 未检测到死锁")

    print("\n--- 统计信息 ---")
    stats = dispatch.get_stats()
    for k, v in stats.items():
        print(f"   • {k}: {v}")

    print("\n--- 测试不同均衡策略 ---")
    for strategy in BalanceStrategy:
        test_dispatch = AgentDispatchSi(balance_strategy=strategy)
        test_dispatch.register_agent("A-1", weight=1)
        test_dispatch.register_agent("A-2", weight=3)
        test_dispatch.register_agent("A-3", weight=2)
        test_dispatch.submit_task(payload={}, task_id="test-task")
        result = test_dispatch.dispatch()
        agent_name = result.agent_name if result else "None"
        print(f"   {strategy.value:20s}: 选中 {agent_name}")

    print("\n✅ 所有测试通过!")
