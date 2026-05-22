"""
Universal DevOps v6.0 - Multi-Agent Resource Coordinator (MARC)

多Agent资源共享协调系统，解决并发执行时的资源抢占、竞态条件和死锁问题。

核心模块:
- ResourceRegistry: 资源注册表，管理四类资源的元数据和状态
- LockManager: 锁管理器，提供互斥锁/读写锁/乐观锁
- SchedulerQueue: 调度队列，支持优先级/FIFO/Fair-share策略
- DeadlockDetector: 死锁检测器，基于Wait-for-Graph的周期性检测
- QuotaManager: 配额管理器，内存/CPU/网络资源配额控制
"""

from .resource_registry import (
    ResourceType,
    ResourceMetadata,
    ResourceRegistry,
    ResourceStats,
)
from .lock_manager import (
    LockType,
    LockRequest,
    LockEntry,
    LockManager,
    LockAcquireResult,
)
from .scheduler_queue import (
    SchedulingStrategy,
    ScheduledTask,
    TaskStatus,
    SchedulerQueue,
)
from .deadlock_detector import (
    WaitForGraphNode,
    DeadlockCycle,
    DeadlockDetector,
    DeadlockResolution,
)
from .quota_manager import (
    MemoryQuota,
    NetworkQuota,
    CPUQuota,
    QuotaManager,
    QuotaUsage,
    TokenBucket,
)

__version__ = "6.0.0"
__author__ = "Universal DevOps Team"

__all__ = [
    "ResourceType",
    "ResourceMetadata",
    "ResourceRegistry",
    "ResourceStats",
    "LockType",
    "LockRequest",
    "LockEntry",
    "LockManager",
    "LockAcquireResult",
    "SchedulingStrategy",
    "ScheduledTask",
    "TaskStatus",
    "SchedulerQueue",
    "WaitForGraphNode",
    "DeadlockCycle",
    "DeadlockDetector",
    "DeadlockResolution",
    "MemoryQuota",
    "NetworkQuota",
    "CPUQuota",
    "QuotaManager",
    "QuotaUsage",
    "TokenBucket",
]
