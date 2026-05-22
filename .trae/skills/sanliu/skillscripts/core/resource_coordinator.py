#!/usr/bin/env python3
"""
多Agent资源协调器（MARC-Lite）- Multi-Agent Resource Coordinator Lite

功能：
1. 资源类型管理：支持5种资源类型（FILE/API/COMPUTE/TERMINAL/SECRET）
2. 资源注册中心：资源的注册、注销和查询
3. 锁管理器：共享读锁、独占写锁、超时自动释放
4. 调度队列：优先级队列、公平调度、抢占式调度、批处理合并
5. 死锁预防：资源排序分配、等待图检测、超时回退、受害者选择
6. 配额管理：per-agent配额、全局限制、使用率监控
7. 状态报告：资源使用率、锁持有情况、告警信息面板
"""

import threading
import time
import uuid
import heapq
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict, deque
from datetime import datetime, timedelta
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    FILE = "file"
    API = "api"
    COMPUTE = "compute"
    TERMINAL = "terminal"
    SECRET = "secret"


class LockType(Enum):
    SHARED = "shared"
    EXCLUSIVE = "exclusive"


class Priority(Enum):
    HIGH = 0
    MEDIUM = 1
    LOW = 2


@dataclass
class ResourceInfo:
    resource_id: str
    type: ResourceType
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True


@dataclass
class LockToken:
    token_id: str
    resource_id: str
    agent_id: str
    lock_type: LockType
    acquired_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


@dataclass
class ScheduledTask:
    task_id: str
    agent_id: str
    resource_ids: List[str]
    priority: Priority
    created_at: datetime = field(default_factory=datetime.now)
    preemptive: bool = False

    def __lt__(self, other):
        if self.preemptive and not other.preemptive:
            return True
        if not self.preemptive and other.preemptive:
            return False
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.created_at < other.created_at


@dataclass
class AgentQuota:
    agent_id: str
    max_files_locked: int = 10
    max_concurrent_api_calls: int = 5
    cpu_quota: float = 100.0
    memory_quota: float = 512.0
    current_files_locked: int = 0
    current_api_calls: int = 0
    current_cpu_usage: float = 0.0
    current_memory_usage: float = 0.0


@dataclass
class GlobalLimits:
    total_active_agents: int = 50
    total_file_locks: int = 200
    total_api_calls: int = 100
    total_cpu_quota: float = 5000.0
    total_memory_quota: float = 25600.0
    current_active_agents: int = 0
    current_file_locks: int = 0
    current_api_calls: int = 0
    current_cpu_usage: float = 0.0
    current_memory_usage: float = 0.0


@dataclass
class ResourceStatusReport:
    timestamp: datetime = field(default_factory=datetime.now)
    resources_by_type: Dict[ResourceType, Dict[str, Any]] = field(default_factory=dict)
    active_locks: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    queue_status: Dict[str, Any] = field(default_factory=dict)
    quota_usage: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    deadlock_risk: List[Dict[str, Any]] = field(default_factory=list)

    def to_panel(self) -> str:
        lines = []
        lines.append("=" * 80)
        lines.append("MARC-Lite 资源协调器状态报告")
        lines.append(f"生成时间: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)

        lines.append("\n📊 资源使用概览:")
        for rtype, info in self.resources_by_type.items():
            lines.append(f"  [{rtype.value.upper():10}] 总数: {info.get('total', 0):4} | "
                        f"活跃: {info.get('active', 0):4} | 锁定: {info.get('locked', 0):4}")

        lines.append("\n🔒 当前锁持有情况:")
        for resource_id, locks in self.active_locks.items():
            for lock in locks[:3]:
                lines.append(f"  [{resource_id[:20]:20}] Agent: {lock.get('agent_id', '?')[:15]:15} "
                            f"类型: {lock.get('lock_type', '?'):10} "
                            f"剩余: {lock.get('remaining_time', 'N/A')}")

        lines.append("\n⏱️ 调度队列状态:")
        queue_info = self.queue_status
        lines.append(f"  等待任务数: {queue_info.get('waiting_count', 0)}")
        lines.append(f"  高优先级:   {queue_info.get('high_priority', 0)}")
        lines.append(f"  中优先级:   {queue_info.get('medium_priority', 0)}")
        lines.append(f"  低优先级:   {queue_info.get('low_priority', 0)}")

        lines.append("\n💾 配额使用情况:")
        for agent_id, usage in list(self.quota_usage.items())[:5]:
            cpu_pct = usage.get('cpu_percent', 0)
            mem_pct = usage.get('memory_percent', 0)
            files_pct = usage.get('files_percent', 0)
            api_pct = usage.get('api_percent', 0)
            lines.append(f"  [{agent_id[:18]:18}] CPU:{cpu_pct:5.1f}% MEM:{mem_pct:5.1f}% "
                        f"文件:{files_pct:5.1f}% API:{api_pct:5.1f}%")

        if self.alerts:
            lines.append("\n⚠️ 告警信息:")
            for alert in self.alerts[:5]:
                level = alert.get('level', 'INFO')
                msg = alert.get('message', '')[:60]
                lines.append(f"  [{level:7}] {msg}")

        if self.deadlock_risk:
            lines.append("\n🔄 死锁风险检测:")
            for risk in self.deadlock_risk[:3]:
                agents = risk.get('agents', [])
                lines.append(f"  风险等级: {risk.get('level', '?')} 涉及Agent: {agents}")

        lines.append("\n" + "=" * 80)
        return "\n".join(lines)


class ResourceRegistry:
    def __init__(self):
        self._resources: Dict[str, ResourceInfo] = {}
        self._type_index: Dict[ResourceType, Set[str]] = defaultdict(set)
        self._lock = threading.Lock()

    def register_resource(self, resource_id: str, resource_type: ResourceType,
                         metadata: Optional[Dict[str, Any]] = None) -> bool:
        with self._lock:
            if resource_id in self._resources:
                logger.warning(f"Resource {resource_id} already registered")
                return False

            resource = ResourceInfo(
                resource_id=resource_id,
                type=resource_type,
                metadata=metadata or {}
            )
            self._resources[resource_id] = resource
            self._type_index[resource_type].add(resource_id)
            logger.info(f"Registered resource: {resource_id} (type={resource_type.value})")
            return True

    def unregister_resource(self, resource_id: str) -> bool:
        with self._lock:
            if resource_id not in self._resources:
                logger.warning(f"Resource {resource_id} not found")
                return False

            resource = self._resources.pop(resource_id)
            self._type_index[resource.type].discard(resource_id)
            logger.info(f"Unregistered resource: {resource_id}")
            return True

    def get_resource(self, resource_id: str) -> Optional[ResourceInfo]:
        with self._lock:
            return self._resources.get(resource_id)

    def list_resources(self, type_filter: Optional[ResourceType] = None) -> List[ResourceInfo]:
        with self._lock:
            if type_filter:
                return [self._resources[rid] for rid in self._type_index.get(type_filter, set())
                       if rid in self._resources]
            return list(self._resources.values())

    def get_stats(self) -> Dict[ResourceType, Dict[str, int]]:
        with self._lock:
            stats = {}
            for rtype in ResourceType:
                all_resources = self._type_index.get(rtype, set())
                active = sum(1 for rid in all_resources
                           if rid in self._resources and self._resources[rid].is_active)
                stats[rtype] = {
                    "total": len(all_resources),
                    "active": active
                }
            return stats


class LockManager:
    DEFAULT_TIMEOUT = 30.0

    def __init__(self, registry: ResourceRegistry):
        self._registry = registry
        self._locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)
        self._resource_locks: Dict[str, Dict[str, Any]] = {}
        self._agent_holds: Dict[str, Set[str]] = defaultdict(set)
        self._global_lock = threading.Lock()
        self._cleanup_thread: Optional[threading.Thread] = None
        self._running = True
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        self._cleanup_thread = threading.Thread(target=self._cleanup_expired_locks,
                                               daemon=True)
        self._cleanup_thread.start()

    def _cleanup_expired_locks(self):
        while self._running:
            time.sleep(5.0)
            now = datetime.now()
            expired_tokens = []

            with self._global_lock:
                for resource_id, lock_info in self._resource_locks.items():
                    for token_id, token in lock_info.get("tokens", {}).items():
                        if token.expires_at and now > token.expires_at:
                            expired_tokens.append((resource_id, token_id))

            for resource_id, token_id in expired_tokens:
                logger.warning(f"Auto-releasing expired lock: {token_id} on {resource_id}")
                try:
                    self.release_lock(token_id)
                except Exception as e:
                    logger.error(f"Failed to release lock {token_id}: {e}")

    def acquire_lock(self, resource_id: str, agent_id: str, lock_type: LockType,
                    mode: str = "optimistic", timeout: Optional[float] = None) -> Optional[LockToken]:
        timeout = timeout or self.DEFAULT_TIMEOUT
        resource = self._registry.get_resource(resource_id)
        if not resource:
            logger.error(f"Resource {resource_id} not registered")
            return None

        token_id = str(uuid.uuid4())[:8]
        expires_at = datetime.now() + timedelta(seconds=timeout)

        with self._locks[resource_id]:
            with self._global_lock:
                if resource_id not in self._resource_locks:
                    self._resource_locks[resource_id] = {
                        "readers": set(),
                        "writer": None,
                        "tokens": {},
                        "wait_queue": deque()
                    }

                lock_info = self._resource_locks[resource_id]

                if lock_type == LockType.SHARED:
                    if lock_info["writer"] is not None:
                        if mode == "pessimistic":
                            return None
                        wait_entry = {
                            "agent_id": agent_id,
                            "lock_type": lock_type,
                            "token_id": token_id
                        }
                        lock_info["wait_queue"].append(wait_entry)
                        return None

                    lock_info["readers"].add(agent_id)

                elif lock_type == LockType.EXCLUSIVE:
                    if lock_info["writer"] is not None or len(lock_info["readers"]) > 0:
                        if mode == "pessimistic":
                            return None
                        wait_entry = {
                            "agent_id": agent_id,
                            "lock_type": lock_type,
                            "token_id": token_id
                        }
                        lock_info["wait_queue"].append(wait_entry)
                        return None

                    lock_info["writer"] = agent_id

                token = LockToken(
                    token_id=token_id,
                    resource_id=resource_id,
                    agent_id=agent_id,
                    lock_type=lock_type,
                    acquired_at=datetime.now(),
                    expires_at=expires_at
                )
                lock_info["tokens"][token_id] = token
                self._agent_holds[agent_id].add(token_id)

                logger.info(f"Lock acquired: {token_id} by {agent_id} on {resource_id} "
                           f"({lock_type.value}, mode={mode})")
                return token

    def release_lock(self, token_id: str) -> bool:
        with self._global_lock:
            for resource_id, lock_info in self._resource_locks.items():
                if token_id in lock_info["tokens"]:
                    token = lock_info["tokens"].pop(token_id)
                    agent_id = token.agent_id

                    if token.lock_type == LockType.SHARED:
                        lock_info["readers"].discard(agent_id)
                    elif token.lock_type == LockType.EXCLUSIVE:
                        if lock_info["writer"] == agent_id:
                            lock_info["writer"] = None

                    self._agent_holds[agent_id].discard(token_id)
                    logger.info(f"Lock released: {token_id} by {agent_id}")
                    return True

            logger.warning(f"Lock token {token_id} not found")
            return False

    def get_active_locks(self) -> Dict[str, List[Dict[str, Any]]]:
        result = {}
        now = datetime.now()
        with self._global_lock:
            for resource_id, lock_info in self._resource_locks.items():
                locks = []
                for token in lock_info["tokens"].values():
                    remaining = (token.expires_at - now).total_seconds() if token.expires_at else None
                    locks.append({
                        "token_id": token.token_id,
                        "agent_id": token.agent_id,
                        "lock_type": token.lock_type.value,
                        "acquired_at": token.acquired_at.isoformat(),
                        "remaining_time": f"{remaining:.1f}s" if remaining else "N/A"
                    })
                if locks:
                    result[resource_id] = locks
        return result

    def shutdown(self):
        self._running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=2.0)


class SchedulerQueue:
    MAX_QUEUE_SIZE = 1000
    FAIRNESS_THRESHOLD = 10
    BATCH_SIZE = 5

    def __init__(self):
        self._queue: List[ScheduledTask] = []
        self._agent_task_count: Dict[str, int] = defaultdict(int)
        self._task_history: deque = deque(maxlen=1000)
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._batch_buffer: List[ScheduledTask] = []
        self._last_batch_time = time.time()

    def enqueue(self, task: ScheduledTask) -> bool:
        with self._condition:
            if len(self._queue) >= self.MAX_QUEUE_SIZE:
                logger.warning("Queue full, rejecting task")
                return False

            heapq.heappush(self._queue, task)
            self._agent_task_count[task.agent_id] += 1
            self._condition.notify()
            logger.info(f"Task enqueued: {task.task_id} (priority={task.priority.name})")
            return True

    def dequeue(self, timeout: Optional[float] = None) -> Optional[ScheduledTask]:
        with self._condition:
            if self._try_batch_process():
                if self._batch_buffer:
                    task = self._batch_buffer.pop(0)
                    self._record_task(task)
                    return task

            deadline = time.time() + (timeout or 0.1)
            while True:
                while self._queue:
                    task = heapq.heappop(self._queue)
                    if self._check_fairness(task):
                        self._record_task(task)
                        return task
                    else:
                        self._requeue_with_boost(task)

                remaining = deadline - time.time()
                if remaining <= 0:
                    break
                self._condition.wait(timeout=min(remaining, 0.1))

            return None

    def _try_batch_process(self) -> bool:
        now = time.time()
        if now - self._last_batch_time < 1.0:
            return False
        if len(self._queue) < self.BATCH_SIZE:
            return False

        self._batch_buffer = []
        for _ in range(min(self.BATCH_SIZE, len(self._queue))):
            if self._queue:
                task = heapq.heappop(self._queue)
                self._batch_buffer.append(task)

        self._last_batch_time = now
        return True

    def _check_fairness(self, task: ScheduledTask) -> bool:
        count = self._agent_task_count.get(task.agent_id, 0)
        if task.priority == Priority.HIGH:
            return True
        return count < self.FAIRNESS_THRESHOLD

    def _requeue_with_boost(self, task: ScheduledTask):
        boosted = ScheduledTask(
            task_id=task.task_id,
            agent_id=task.agent_id,
            resource_ids=task.resource_ids,
            priority=Priority(max(0, task.priority.value - 1)),
            created_at=task.created_at,
            preemptive=task.preemptive
        )
        heapq.heappush(self._queue, boosted)
        logger.debug(f"Task requeued with boost: {task.task_id}")

    def _record_task(self, task: ScheduledTask):
        self._agent_task_count[task.agent_id] += 1
        self._task_history.append({
            "task_id": task.task_id,
            "agent_id": task.agent_id,
            "completed_at": datetime.now().isoformat()
        })

    def preempt(self, task_id: str) -> bool:
        with self._lock:
            for i, task in enumerate(self._queue):
                if task.task_id == task_id:
                    preemptive_task = ScheduledTask(
                        task_id=task.task_id,
                        agent_id=task.agent_id,
                        resource_ids=task.resource_ids,
                        priority=task.priority,
                        created_at=task.created_at,
                        preemptive=True
                    )
                    self._queue[i] = preemptive_task
                    heapq.heapify(self._queue)
                    logger.info(f"Task preempted: {task_id}")
                    return True
            return False

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            priority_counts = {p: 0 for p in Priority}
            for task in self._queue:
                priority_counts[task.priority] += 1

            return {
                "waiting_count": len(self._queue),
                "high_priority": priority_counts[Priority.HIGH],
                "medium_priority": priority_counts[Priority.MEDIUM],
                "low_priority": priority_counts[Priority.LOW],
                "buffered_tasks": len(self._batch_buffer),
                "recently_completed": len(self._task_history)
            }


class DeadlockPreventer:
    DETECTION_INTERVAL = 5.0
    WAIT_TIMEOUT = 20.0

    def __init__(self, lock_manager: LockManager):
        self._lock_manager = lock_manager
        self._wait_graph: Dict[str, Set[str]] = defaultdict(set)
        self._resource_order: List[str] = []
        self._agent_wait_start: Dict[str, datetime] = {}
        self._detection_thread: Optional[threading.Thread] = None
        self._running = True
        self._lock = threading.Lock()
        self._start_detection()

    def _start_detection(self):
        self._detection_thread = threading.Thread(target=self._detect_deadloops,
                                                 daemon=True)
        self._detection_thread.start()

    def _detect_deadloops(self):
        while self._running:
            time.sleep(self.DETECTION_INTERVAL)
            risks = self._analyze_wait_graph()
            if risks:
                for risk in risks:
                    logger.warning(f"Deadlock risk detected: {risk}")
                    victim = self._select_victim(risk["agents"])
                    if victim:
                        self._rollback_agent(victim)

    def _analyze_wait_graph(self) -> List[Dict[str, Any]]:
        risks = []
        visited = set()
        rec_stack = set()

        def dfs(agent: str, path: List[str]) -> bool:
            visited.add(agent)
            rec_stack.add(agent)
            path.append(agent)

            for waiting_for in self._wait_graph.get(agent, set()):
                if waiting_for not in visited:
                    if dfs(waiting_for, path):
                        return True
                elif waiting_for in rec_stack:
                    cycle = path[path.index(waiting_for):] + [waiting_for]
                    risks.append({
                        "level": "HIGH",
                        "agents": cycle.copy(),
                        "cycle_length": len(cycle)
                    })
                    return True

            path.pop()
            rec_stack.discard(agent)
            return False

        with self._lock:
            for agent in list(self._wait_graph.keys()):
                if agent not in visited:
                    dfs(agent, [])

        return risks

    def _select_victim(self, agents: List[str]) -> Optional[str]:
        best_victim = None
        min_cost = float('inf')

        for agent_id in agents:
            cost = self._calculate_rollback_cost(agent_id)
            if cost < min_cost:
                min_cost = cost
                best_victim = agent_id

        return best_victim

    def _calculate_rollback_cost(self, agent_id: str) -> float:
        active_locks = self._lock_manager.get_active_locks()
        hold_count = sum(1 for locks in active_locks.values()
                        for lock in locks if lock["agent_id"] == agent_id)
        wait_time = (datetime.now() - self._agent_wait_start.get(agent_id,
                     datetime.now())).total_seconds()
        return hold_count * 10 + wait_time

    def _rollback_agent(self, agent_id: str):
        logger.warning(f"Rolling back agent to prevent deadlock: {agent_id}")
        active_locks = self._lock_manager.get_active_locks()
        released = 0

        for resource_id, locks in active_locks.items():
            for lock in locks:
                if lock["agent_id"] == agent_id:
                    try:
                        self._lock_manager.release_lock(lock["token_id"])
                        released += 1
                    except Exception as e:
                        logger.error(f"Failed to release lock during rollback: {e}")

        with self._lock:
            self._wait_graph.pop(agent_id, None)
            self._agent_wait_start.pop(agent_id, None)

        logger.info(f"Agent rollback completed: {agent_id}, released {released} locks")

    def record_wait(self, agent_id: str, blocking_agent_id: str):
        with self._lock:
            self._wait_graph[agent_id].add(blocking_agent_id)
            self._agent_wait_start[agent_id] = datetime.now()

    def clear_wait(self, agent_id: str):
        with self._lock:
            self._wait_graph.pop(agent_id, None)
            self._agent_wait_start.pop(agent_id, None)

    def get_risks(self) -> List[Dict[str, Any]]:
        return self._analyze_wait_graph()

    def shutdown(self):
        self._running = False
        if self._detection_thread:
            self._detection_thread.join(timeout=2.0)


class QuotaManager:
    def __init__(self):
        self._agent_quotas: Dict[str, AgentQuota] = {}
        self._global_limits = GlobalLimits()
        self._lock = threading.Lock()
        self._alerts: List[Dict[str, Any]] = []

    def register_agent(self, agent_id: str,
                      quota: Optional[AgentQuota] = None) -> AgentQuota:
        with self._lock:
            if agent_id not in self._agent_quotas:
                self._agent_quotas[agent_id] = quota or AgentQuota(agent_id=agent_id)
                self._global_limits.current_active_agents += 1
            return self._agent_quotas[agent_id]

    def unregister_agent(self, agent_id: str) -> bool:
        with self._lock:
            if agent_id in self._agent_quotas:
                quota = self._agent_quotas.pop(agent_id)
                self._global_limits.current_file_locks -= quota.current_files_locked
                self._global_limits.current_api_calls -= quota.current_api_calls
                self._global_limits.current_cpu_usage -= quota.current_cpu_usage
                self._global_limits.current_memory_usage -= quota.current_memory_usage
                self._global_limits.current_active_agents -= 1
                return True
            return False

    def check_and_acquire(self, agent_id: str, resource_type: ResourceType,
                         amount: float = 1.0) -> Tuple[bool, str]:
        with self._lock:
            if agent_id not in self._agent_quotas:
                return False, f"Agent {agent_id} not registered"

            quota = self._agent_quotas[agent_id]
            reason = ""

            if resource_type == ResourceType.FILE:
                if quota.current_files_locked >= quota.max_files_locked:
                    reason = f"Agent file lock limit reached ({quota.current_files_locked}/{quota.max_files_locked})"
                    self._add_alert("WARNING", reason)
                    return False, reason
                if (self._global_limits.current_file_locks + amount >
                    self._global_limits.total_file_locks):
                    reason = "Global file lock limit reached"
                    self._add_alert("ERROR", reason)
                    return False, reason
                quota.current_files_locked += amount
                self._global_limits.current_file_locks += amount

            elif resource_type == ResourceType.API:
                if quota.current_api_calls >= quota.max_concurrent_api_calls:
                    reason = f"Agent API call limit reached ({quota.current_api_calls}/{quota.max_concurrent_api_calls})"
                    self._add_alert("WARNING", reason)
                    return False, reason
                if (self._global_limits.current_api_calls + amount >
                    self._global_limits.total_api_calls):
                    reason = "Global API call limit reached"
                    self._add_alert("ERROR", reason)
                    return False, reason
                quota.current_api_calls += amount
                self._global_limits.current_api_calls += amount

            elif resource_type == ResourceType.COMPUTE:
                if quota.current_cpu_usage + amount > quota.cpu_quota:
                    reason = f"Agent CPU quota exceeded ({quota.current_cpu_usage + amount:.1f}/{quota.cpu_quota:.1f})"
                    self._add_alert("WARNING", reason)
                    return False, reason
                if (self._global_limits.current_cpu_usage + amount >
                    self._global_limits.total_cpu_quota):
                    reason = "Global CPU quota exceeded"
                    self._add_alert("ERROR", reason)
                    return False, reason
                quota.current_cpu_usage += amount
                self._global_limits.current_cpu_usage += amount

            elif resource_type == ResourceType.TERMINAL:
                pass

            elif resource_type == ResourceType.SECRET:
                pass

            return True, "OK"

    def release(self, agent_id: str, resource_type: ResourceType,
               amount: float = 1.0):
        with self._lock:
            if agent_id not in self._agent_quotas:
                return

            quota = self._agent_quotas[agent_id]

            if resource_type == ResourceType.FILE:
                quota.current_files_locked = max(0, quota.current_files_locked - amount)
                self._global_limits.current_file_locks = max(0,
                    self._global_limits.current_file_locks - amount)
            elif resource_type == ResourceType.API:
                quota.current_api_calls = max(0, quota.current_api_calls - amount)
                self._global_limits.current_api_calls = max(0,
                    self._global_limits.current_api_calls - amount)
            elif resource_type == ResourceType.COMPUTE:
                quota.current_cpu_usage = max(0, quota.current_cpu_usage - amount)
                self._global_limits.current_cpu_usage = max(0,
                    self._global_limits.current_cpu_usage - amount)

    def get_usage_report(self) -> Dict[str, Dict[str, Any]]:
        report = {}
        with self._lock:
            for agent_id, quota in self._agent_quotas.items():
                report[agent_id] = {
                    "cpu_percent": (quota.current_cpu_usage / quota.cpu_quota * 100
                                   if quota.cpu_quota > 0 else 0),
                    "memory_percent": (quota.current_memory_usage / quota.memory_quota * 100
                                      if quota.memory_quota > 0 else 0),
                    "files_percent": (quota.current_files_locked / quota.max_files_locked * 100
                                     if quota.max_files_locked > 0 else 0),
                    "api_percent": (quota.current_api_calls / quota.max_concurrent_api_calls * 100
                                   if quota.max_concurrent_api_calls > 0 else 0)
                }
        return report

    def _add_alert(self, level: str, message: str):
        alert = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        self._alerts.append(alert)
        if len(self._alerts) > 100:
            self._alerts = self._alerts[-100:]

    def get_alerts(self) -> List[Dict[str, Any]]:
        with self._lock:
            return self._alerts.copy()


class ResourceCoordinator:
    def __init__(self):
        self._registry = ResourceRegistry()
        self._lock_manager = LockManager(self._registry)
        self._scheduler = SchedulerQueue()
        self._deadlock_preventer = DeadlockPreventer(self._lock_manager)
        self._quota_manager = QuotaManager()
        self._initialized = False
        self._init_lock = threading.Lock()
        logger.info("MARC-Lite ResourceCoordinator initialized")

    @contextmanager
    def acquire_context(self, resource_id: str, agent_id: str,
                       lock_type: LockType, mode: str = "optimistic",
                       timeout: float = 30.0):
        token = None
        try:
            token = self.acquire_lock(resource_id, agent_id, lock_type, mode, timeout)
            if token is None:
                raise RuntimeError(f"Failed to acquire lock on {resource_id}")
            yield token
        finally:
            if token:
                self.release_lock(token.token_id)

    def register_resource(self, resource_id: str, resource_type: ResourceType,
                         metadata: Optional[Dict[str, Any]] = None) -> bool:
        return self._registry.register_resource(resource_id, resource_type, metadata)

    def unregister_resource(self, resource_id: str) -> bool:
        return self._registry.unregister_resource(resource_id)

    def list_resources(self, type_filter: Optional[ResourceType] = None) -> List[ResourceInfo]:
        return self._registry.list_resources(type_filter)

    def acquire_lock(self, resource_id: str, agent_id: str, lock_type: LockType,
                    mode: str = "optimistic", timeout: float = 30.0) -> Optional[LockToken]:
        allowed, reason = self._quota_manager.check_and_acquire(agent_id,
                    self._registry.get_resource(resource_id).type
                    if self._registry.get_resource(resource_id) else ResourceType.FILE)
        if not allowed:
            logger.warning(f"Quota denied for {agent_id}: {reason}")
            return None

        token = self._lock_manager.acquire_lock(resource_id, agent_id, lock_type,
                                               mode, timeout)
        if token is None:
            blocking_agents = self._get_blocking_agents(resource_id)
            for blocker in blocking_agents:
                self._deadlock_preventer.record_wait(agent_id, blocker)
        else:
            self._deadlock_preventer.clear_wait(agent_id)

        return token

    def release_lock(self, token_id: str) -> bool:
        success = self._lock_manager.release_lock(token_id)
        if success:
            self._deadlock_preventer.clear_wait("")
        return success

    def enqueue_task(self, task_id: str, agent_id: str, resource_ids: List[str],
                    priority: Priority = Priority.MEDIUM) -> bool:
        task = ScheduledTask(
            task_id=task_id,
            agent_id=agent_id,
            resource_ids=resource_ids,
            priority=priority
        )
        return self._scheduler.enqueue(task)

    def dequeue_task(self, timeout: Optional[float] = None) -> Optional[ScheduledTask]:
        return self._scheduler.dequeue(timeout)

    def preempt_task(self, task_id: str) -> bool:
        return self._scheduler.preempt(task_id)

    def register_agent(self, agent_id: str,
                      quota: Optional[AgentQuota] = None) -> AgentQuota:
        return self._quota_manager.register_agent(agent_id, quota)

    def unregister_agent(self, agent_id: str) -> bool:
        return self._quota_manager.unregister_agent(agent_id)

    def _get_blocking_agents(self, resource_id: str) -> List[str]:
        blockers = []
        active_locks = self._lock_manager.get_active_locks()
        if resource_id in active_locks:
            for lock in active_locks[resource_id]:
                blockers.append(lock["agent_id"])
        return blockers

    def get_status(self) -> ResourceStatusReport:
        report = ResourceStatusReport()

        resource_stats = self._registry.get_stats()
        active_locks = self._lock_manager.get_active_locks()

        for rtype, stats in resource_stats.items():
            locked_count = sum(len(locks) for rid, locks in active_locks.items()
                             if self._registry.get_resource(rid) and
                             self._registry.get_resource(rid).type == rtype)
            report.resources_by_type[rtype] = {
                "total": stats["total"],
                "active": stats["active"],
                "locked": locked_count
            }

        report.active_locks = active_locks
        report.queue_status = self._scheduler.get_status()
        report.quota_usage = self._quota_manager.get_usage_report()
        report.alerts = self._quota_manager.get_alerts()
        report.deadlock_risk = self._deadlock_preventer.get_risks()

        return report

    def shutdown(self):
        logger.info("Shutting down MARC-Lite ResourceCoordinator...")
        self._deadlock_preventer.shutdown()
        self._lock_manager.shutdown()
        logger.info("MARC-Lite ResourceCoordinator shutdown complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    coordinator = ResourceCoordinator()

    coordinator.register_resource("file_001", ResourceType.FILE, {"path": "/tmp/test.txt"})
    coordinator.register_resource("api_001", ResourceType.API, {"endpoint": "/api/v1/data"})
    coordinator.register_resource("compute_001", ResourceType.COMPUTE, {"cores": 4})
    coordinator.register_resource("terminal_001", ResourceType.TERMINAL, {"session": "bash"})
    coordinator.register_resource("secret_001", ResourceType.SECRET, {"key_type": "api_key"})

    coordinator.register_agent("agent_01")
    coordinator.register_agent("agent_02")

    print("\n=== 测试锁获取 ===")
    token1 = coordinator.acquire_lock("file_001", "agent_01", LockType.EXCLUSIVE)
    print(f"agent_01 获取写锁: {'成功' if token1 else '失败'}")

    token2 = coordinator.acquire_lock("file_001", "agent_02", LockType.SHARED)
    print(f"agent_02 获取读锁: {'成功' if token2 else '失败 (预期)'}")

    if token1:
        coordinator.release_lock(token1.token_id)
        print("agent_01 释放写锁")

    token3 = coordinator.acquire_lock("file_001", "agent_02", LockType.SHARED)
    print(f"agent_02 再次获取读锁: {'成功' if token3 else '失败'}")

    print("\n=== 测试调度队列 ===")
    coordinator.enqueue_task("task_001", "agent_01", ["file_001"], Priority.HIGH)
    coordinator.enqueue_task("task_002", "agent_02", ["api_001"], Priority.LOW)
    coordinator.enqueue_task("task_003", "agent_01", ["compute_001"], Priority.MEDIUM)

    task = coordinator.dequeue_task(timeout=1.0)
    if task:
        print(f"出队任务: {task.task_id} (优先级: {task.priority.name})")

    print("\n=== 状态报告 ===")
    status = coordinator.get_status()
    print(status.to_panel())

    coordinator.shutdown()
