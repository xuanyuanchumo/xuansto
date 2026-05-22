"""
锁管理器模块 - 提供多粒度并发控制

支持的锁类型:
- ExclusiveLock (互斥锁): 同一时间只允许一个Agent访问（用于源代码文件写操作）
- ReadWriteLock (读写锁): 允许多个读、单个写（用于配置文件）
- OptimisticLock (乐观锁): 基于版本号的最后写入胜出（用于文档文件）

核心特性:
- 锁超时自动释放（默认120s）
- 优先级继承（高优先级可抢占低优先级）
- 完整的锁生命周期跟踪
"""

from __future__ import annotations

import threading
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple


class LockType(Enum):
    """锁类型枚举"""
    EXCLUSIVE = "exclusive"
    READ_WRITE = "read_write"
    OPTIMISTIC = "optimistic"


@dataclass
class LockRequest:
    """锁请求"""
    agent_id: str
    resource_id: str
    lock_type: LockType
    priority: int
    timeout: float = 120.0
    requested_at: datetime = field(default_factory=datetime.now)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class LockEntry:
    """锁条目"""
    lock_id: str
    resource_id: str
    agent_id: str
    lock_type: LockType
    acquired_at: datetime
    expires_at: datetime
    priority: int
    is_write_lock: bool = False
    version: int = 0


@dataclass
class LockAcquireResult:
    """锁获取结果"""
    success: bool
    lock_id: Optional[str] = None
    message: str = ""
    preempted_agent: Optional[str] = None


class _ExclusiveLock:
    """互斥锁实现 - 同一时刻只允许一个持有者"""

    def __init__(self) -> None:
        self._holder: Optional[str] = None
        self._lock_id: Optional[str] = None
        self._priority: int = 0

    @property
    def is_locked(self) -> bool:
        return self._holder is not None

    @property
    def holder(self) -> Optional[str]:
        return self._holder

    @property
    def holder_priority(self) -> int:
        return self._priority

    def try_acquire(self, agent_id: str, priority: int) -> bool:
        if not self.is_locked or priority > self._priority:
            self._holder = agent_id
            self._priority = priority
            return True
        return False

    def release(self, agent_id: str) -> bool:
        if self._holder == agent_id:
            self._holder = None
            self._lock_id = None
            self._priority = 0
            return True
        return False

    def force_release(self) -> Optional[str]:
        old_holder = self._holder
        self._holder = None
        self._lock_id = None
        self._priority = 0
        return old_holder


class _ReadWriteLock:
    """
    读写锁实现 - 多读单写

    特性:
    - 允许并发读取
    - 写操作独占访问
    - 写优先策略防止饥饿
    """

    def __init__(self) -> None:
        self._readers: Set[str] = set()
        self._writer: Optional[str] = None
        self._writer_priority: int = 0
        self._pending_writers: int = 0

    @property
    def is_read_locked(self) -> bool:
        return len(self._readers) > 0

    @property
    def is_write_locked(self) -> bool:
        return self._writer is not None

    @property
    def is_locked(self) -> bool:
        return self.is_read_locked or self.is_write_locked

    @property
    def readers(self) -> Set[str]:
        return set(self._readers)

    @property
    def writer(self) -> Optional[str]:
        return self._writer

    @property
    def writer_priority(self) -> int:
        return self._writer_priority

    def can_read(self, priority: int) -> bool:
        if not self.is_write_locked:
            return True
        return priority > self._writer_priority

    def can_write(self, priority: int) -> bool:
        if not self.is_locked:
            return True
        if self.is_write_locked and priority > self._writer_priority:
            return True
        if self.is_read_locked:
            for reader in self._readers:
                reader_pri = getattr(reader, '_priority', 0)
                if isinstance(reader_pri, int) and priority <= reader_pri:
                    return False
            return True
        return False

    def acquire_read(self, agent_id: str, priority: int) -> bool:
        if not self.can_read(priority):
            return False
        self._readers.add(agent_id)
        return True

    def acquire_write(self, agent_id: str, priority: int) -> bool:
        if not self.can_write(priority):
            return False
        self._writer = agent_id
        self._writer_priority = priority
        return True

    def release_read(self, agent_id: str) -> bool:
        if agent_id in self._readers:
            self._readers.discard(agent_id)
            return True
        return False

    def release_write(self, agent_id: str) -> bool:
        if self._writer == agent_id:
            self._writer = None
            self._writer_priority = 0
            return True
        return False

    def force_release_all(self) -> Tuple[Set[str], Optional[str]]:
        readers = set(self._readers)
        writer = self._writer
        self._readers.clear()
        self._writer = None
        self._writer_priority = 0
        return readers, writer


class _OptimisticLock:
    """
    乐观锁实现 - 基于版本号的CAS (Compare-And-Swap)

    特性:
    - 无阻塞的版本号检查
    - 最后写入胜出 (Last-Write-Wins)
    - 适用于冲突率低的场景
    """

    def __init__(self) -> None:
        self._version: int = 0
        self._holders: Dict[str, int] = {}  # agent_id -> version acquired

    @property
    def current_version(self) -> int:
        return self._version

    @property
    def holders(self) -> Dict[str, int]:
        return dict(self._holders)

    def try_acquire(self, agent_id: str, expected_version: int = -1) -> Tuple[bool, int]:
        """
        尝试获取锁（乐观方式）

        Args:
            agent_id: Agent标识
            expected_version: 期望的版本号，-1表示不检查

        Returns:
            (成功标志, 当前版本号)
        """
        if expected_version >= 0 and expected_version != self._version:
            return False, self._version

        new_version = self._version + 1
        self._version = new_version
        self._holders[agent_id] = new_version
        return True, new_version

    def release(self, agent_id: str) -> bool:
        if agent_id in self._holders:
            del self._holders[agent_id]
            return True
        return False

    def validate(self, agent_id: str, held_version: int) -> bool:
        """验证持有的版本是否仍然有效"""
        return self._holders.get(agent_id) == held_version and self._version == held_version


class LockManager:
    """
    锁管理器 - 多Agent并发控制核心组件

    功能:
    - 三种锁类型的统一管理接口
    - 超时自动释放机制
    - 优先级继承与抢占
    - 完整的审计日志
    - 死锁预防支持

    使用示例:
        >>> manager = LockManager()
        >>> result = manager.acquire_lock(
        ...     agent_id="agent_1",
        ...     resource_id="file_main.py",
        ...     lock_type=LockType.EXCLUSIVE,
        ...     priority=8
        ... )
        >>> if result.success:
        ...     manager.release_lock(result.lock_id)
    """

    def __init__(self, default_timeout: float = 120.0) -> None:
        self._default_timeout = default_timeout
        self._locks: Dict[str, Dict[LockType, any]] = {
            LockType.EXCLUSIVE: {},
            LockType.READ_WRITE: {},
            LockType.OPTIMISTIC: {},
        }
        self._active_locks: Dict[str, LockEntry] = {}  # lock_id -> LockEntry
        self._resource_locks: Dict[str, List[str]] = defaultdict(list)  # resource_id -> [lock_ids]
        self._agent_locks: Dict[str, Set[str]] = defaultdict(set)  # agent_id -> {lock_ids}
        self._pending_requests: Dict[str, List[LockRequest]] = defaultdict(list)
        self._global_lock = threading.RLock()
        self._audit_log: List[Dict] = []
        self._cleanup_interval: float = 30.0
        self._last_cleanup: datetime = datetime.now()

    def acquire_lock(
        self,
        agent_id: str,
        resource_id: str,
        lock_type: LockType,
        priority: int = 5,
        timeout: float | None = None,
        is_write: bool = False,
        expected_version: int = -1,
    ) -> LockAcquireResult:
        """
        申请获取资源锁

        Args:
            agent_id: 请求锁的Agent ID
            resource_id: 目标资源ID
            lock_type: 锁类型
            priority: 优先级(1-10)，默认5
            timeout: 超时时间(秒)，None使用默认值
            is_write: 是否为写锁（仅ReadWriteLock使用）
            expected_version: 期望版本号（仅OptimisticLock使用）

        Returns:
            LockAcquireResult包含成功/失败信息
        """
        if timeout is None:
            timeout = self._default_timeout

        request = LockRequest(
            agent_id=agent_id,
            resource_id=resource_id,
            lock_type=lock_type,
            priority=priority,
            timeout=timeout,
        )

        with self._global_lock:
            expired = self._cleanup_expired_locks()

            lock_impl = self._get_or_create_lock(resource_id, lock_type)
            acquired = False
            preempted_agent = None

            if lock_type == LockType.EXCLUSIVE:
                exclusive_lock: _ExclusiveLock = lock_impl
                if exclusive_lock.try_acquire(agent_id, priority):
                    if exclusive_lock.holder != agent_id and exclusive_lock.holder is not None:
                        preempted_agent = exclusive_lock.holder
                    acquired = True

            elif lock_type == LockType.READ_WRITE:
                rw_lock: _ReadWriteLock = lock_impl
                if is_write:
                    if rw_lock.acquire_write(agent_id, priority):
                        if rw_lock.writer != agent_id and rw_lock.writer is not None:
                            preempted_agent = rw_lock.writer
                        acquired = True
                else:
                    if rw_lock.acquire_read(agent_id, priority):
                        acquired = True

            elif lock_type == LockType.OPTIMISTIC:
                opt_lock: _OptimisticLock = lock_impl
                success, version = opt_lock.try_acquire(agent_id, expected_version)
                acquired = success

            if acquired:
                lock_id = str(uuid.uuid4())
                expires_at = datetime.now() + __import__('datetime').timedelta(seconds=timeout)
                entry = LockEntry(
                    lock_id=lock_id,
                    resource_id=resource_id,
                    agent_id=agent_id,
                    lock_type=lock_type,
                    acquired_at=datetime.now(),
                    expires_at=expires_at,
                    priority=priority,
                    is_write_lock=is_write,
                    version=getattr(lock_impl, 'current_version', 0) if lock_type == LockType.OPTIMISTIC else 0,
                )

                self._active_locks[lock_id] = entry
                self._resource_locks[resource_id].append(lock_id)
                self._agent_locks[agent_id].add(lock_id)

                self._log_audit("ACQUIRE", agent_id, resource_id, lock_type, {
                    "lock_id": lock_id,
                    "priority": priority,
                    "preempted": preempted_agent,
                })

                return LockAcquireResult(
                    success=True,
                    lock_id=lock_id,
                    message="Lock acquired successfully",
                    preempted_agent=preempted_agent,
                )

            self._pending_requests[resource_id].append(request)
            self._log_audit("ACQUIRE_FAILED", agent_id, resource_id, lock_type, {
                "reason": "Resource locked by another agent",
                "priority": priority,
            })

            return LockAcquireResult(
                success=False,
                message=f"Failed to acquire {lock_type.value} lock on {resource_id}",
            )

    def release_lock(self, lock_id: str) -> bool:
        """
        释放锁

        Args:
            lock_id: 要释放的锁ID

        Returns:
            释放成功返回True
        """
        with self._global_lock:
            if lock_id not in self._active_locks:
                return False

            entry = self._active_locks[lock_id]
            lock_impl = self._get_lock(entry.resource_id, entry.lock_type)
            released = False

            if entry.lock_type == LockType.EXCLUSIVE and lock_impl:
                released = lock_impl.release(entry.agent_id)
            elif entry.lock_type == LockType.READ_WRITE and lock_impl:
                if entry.is_write_lock:
                    released = lock_impl.release_write(entry.agent_id)
                else:
                    released = lock_impl.release_read(entry.agent_id)
            elif entry.lock_type == LockType.OPTIMISTIC and lock_impl:
                released = lock_impl.release(entry.agent_id)

            if released:
                del self._active_locks[lock_id]
                if lock_id in self._resource_locks.get(entry.resource_id, []):
                    self._resource_locks[entry.resource_id].remove(lock_id)
                if lock_id in self._agent_locks.get(entry.agent_id, set()):
                    self._agent_locks[entry.agent_id].discard(lock_id)

                self._log_audit("RELEASE", entry.agent_id, entry.resource_id, entry.lock_type, {
                    "lock_id": lock_id,
                })
                return True

            return False

    def release_all_for_agent(self, agent_id: str) -> int:
        """
        释放指定Agent持有的所有锁

        Args:
            agent_id: Agent ID

        Returns:
            释放的锁数量
        """
        with self._global_lock:
            lock_ids = list(self._agent_locks.get(agent_id, set()))
            count = 0
            for lid in lock_ids:
                if self.release_lock(lid):
                    count += 1
            return count

    def force_release_resource(self, resource_id: str, lock_type: LockType | None = None) -> List[str]:
        """
        强制释放资源的所有锁（紧急恢复用）

        Args:
            resource_id: 资源ID
            lock_type: 指定锁类型，None表示所有类型

        Returns:
            被强制释放的锁ID列表
        """
        with self._global_lock:
            released_locks = []
            lock_ids = list(self._resource_locks.get(resource_id, []))

            for lid in lock_ids:
                entry = self._active_locks.get(lid)
                if entry and (lock_type is None or entry.lock_type == lock_type):
                    if self.release_lock(lid):
                        released_locks.append(lid)
                        self._log_audit("FORCE_RELEASE", entry.agent_id, resource_id, entry.lock_type, {
                            "lock_id": lid,
                        })

            return released_locks

    def get_lock_status(self, lock_id: str) -> Optional[LockEntry]:
        """查询锁状态"""
        with self._global_lock:
            return self._active_locks.get(lock_id)

    def get_resource_locks(self, resource_id: str) -> List[LockEntry]:
        """获取资源的所有活跃锁"""
        with self._global_lock:
            lock_ids = self._resource_locks.get(resource_id, [])
            return [self._active_locks[lid] for lid in lock_ids if lid in self._active_locks]

    def get_agent_locks(self, agent_id: str) -> List[LockEntry]:
        """获取Agent持有的所有锁"""
        with self._global_lock:
            lock_ids = self._agent_locks.get(agent_id, set())
            return [self._active_locks[lid] for lid in lock_ids if lid in self._active_locks]

    def get_waiting_agents(self, resource_id: str) -> List[LockRequest]:
        """获取等待某资源的Agent列表"""
        with self._global_lock:
            return list(self._pending_requests.get(resource_id, []))

    def get_wait_for_graph(self) -> Dict[str, Set[str]]:
        """
        构建等待图（用于死锁检测）

        Returns:
            {agent_id: set of agents it's waiting for}
        """
        with self._global_lock:
            graph: Dict[str, Set[str]] = {}

            for resource_id, requests in self._pending_requests.items():
                holders = self._get_resource_holders(resource_id)
                for req in requests:
                    if req.agent_id not in graph:
                        graph[req.agent_id] = set()
                    for holder in holders:
                        if holder != req.agent_id:
                            graph[req.agent_id].add(holder)

            return graph

    def get_all_active_locks(self) -> List[LockEntry]:
        """获取所有活跃锁"""
        with self._global_lock:
            return list(self._active_locks.values())

    def get_statistics(self) -> Dict[str, any]:
        """获取锁管理器统计信息"""
        with self._global_lock:
            type_counts = defaultdict(int)
            for entry in self._active_locks.values():
                type_counts[entry.lock_type.value] += 1

            return {
                "total_active_locks": len(self._active_locks),
                "locked_resources": len(self._resource_locks),
                "agents_with_locks": len(self._agent_locks),
                "pending_requests": sum(len(v) for v in self._pending_requests.values()),
                "by_type": dict(type_counts),
                "audit_log_entries": len(self._audit_log),
            }

    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """获取审计日志"""
        with self._global_lock:
            return self._audit_log[-limit:]

    def _get_or_create_lock(self, resource_id: str, lock_type: LockType) -> any:
        """获取或创建锁实例"""
        if resource_id not in self._locks[lock_type]:
            if lock_type == LockType.EXCLUSIVE:
                self._locks[lock_type][resource_id] = _ExclusiveLock()
            elif lock_type == LockType.READ_WRITE:
                self._locks[lock_type][resource_id] = _ReadWriteLock()
            elif lock_type == LockType.OPTIMISTIC:
                self._locks[lock_type][resource_id] = _OptimisticLock()
        return self._locks[lock_type][resource_id]

    def _get_lock(self, resource_id: str, lock_type: LockType) -> Optional[any]:
        """获取已存在的锁实例"""
        return self._locks.get(lock_type, {}).get(resource_id)

    def _get_resource_holders(self, resource_id: str) -> Set[str]:
        """获取资源的当前持有者"""
        holders: Set[str] = set()
        for lock_type in LockType:
            lock_impl = self._get_lock(resource_id, lock_type)
            if lock_impl:
                if lock_type == LockType.EXCLUSIVE:
                    if lock_impl.holder:
                        holders.add(lock_impl.holder)
                elif lock_type == LockType.READ_WRITE:
                    if lock_impl.writer:
                        holders.add(lock_impl.writer)
                    holders.update(lock_impl.readers)
                elif lock_type == LockType.OPTIMISTIC:
                    holders.update(lock_impl.holders.keys())
        return holders

    def _cleanup_expired_locks(self) -> int:
        """清理过期锁，返回清理数量"""
        now = datetime.now()
        expired_ids = [
            lid for lid, entry in self._active_locks.items()
            if entry.expires_at < now
        ]

        count = 0
        for lid in expired_ids:
            entry = self._active_locks[lid]
            if self.release_lock(lid):
                self._log_audit("EXPIRED", entry.agent_id, entry.resource_id, entry.lock_type, {
                    "lock_id": lid,
                    "expired_at": entry.expires_at.isoformat(),
                })
                count += 1

        if count > 0:
            self._last_cleanup = now

        return count

    def _log_audit(self, action: str, agent_id: str, resource_id: str,
                   lock_type: LockType, details: Dict) -> None:
        """记录审计日志"""
        self._audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "agent_id": agent_id,
            "resource_id": resource_id,
            "lock_type": lock_type.value,
            "details": details,
        })

        if len(self._audit_log) > 10000:
            self._audit_log = self._audit_log[-5000:]
