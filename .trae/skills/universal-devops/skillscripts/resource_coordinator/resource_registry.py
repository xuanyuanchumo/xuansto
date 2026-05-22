"""
资源注册表模块 - 管理四类资源的元数据和状态

支持的资源类型:
- FILE: 文件资源（源代码、配置文件、文档等）
- TERMINAL: 终端资源（命令行会话、Shell进程等）
- NETWORK: 网络资源（API连接、HTTP请求、WebSocket等）
- SYSTEM: 系统资源（内存、CPU、磁盘IO等）
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional


class ResourceType(Enum):
    """资源类型枚举（v7.0 新增 AGENT 和 CONTEXT）"""
    FILE = auto()
    TERMINAL = auto()
    NETWORK = auto()
    SYSTEM = auto()
    SECRET = auto()
    AGENT = auto()  # v7.0 新增: Agent身份资源
    CONTEXT = auto()  # v7.0 新增: 上下文资源


class AccessPolicy(Enum):
    EXCLUSIVE = "exclusive"
    READ_WRITE = "read_write"
    OPTIMISTIC = "optimistic"
    READ_ONCE = "read_once"


@dataclass
class ResourceMetadata:
    """资源元数据

    SECRET 类型资源具有特殊行为：
    - 访问策略默认为 READ_ONCE（一次性读取后自动失效）
    - 不支持并发访问，max_concurrent 强制为 1
    - 使用后自动标记为已消耗状态
    """
    resource_type: ResourceType
    name: str
    default_quota: int | float
    priority: int  # 1-10, 10最高
    description: str
    max_concurrent: int
    current_usage: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        if not 1 <= self.priority <= 10:
            raise ValueError(f"Priority must be between 1 and 10, got {self.priority}")
        if self.max_concurrent < 1:
            raise ValueError(f"max_concurrent must be >= 1, got {self.max_concurrent}")


@dataclass
class ResourceStats:
    """资源统计信息"""
    resource_id: str
    resource_type: ResourceType
    total_quota: int | float
    used: int | float
    available: int | float
    waiting_count: int
    utilization_percent: float
    last_updated: datetime = field(default_factory=datetime.now)


class ResourceRegistry:
    """
    资源注册表 - 核心资源管理组件

    功能:
    - 资源的注册/注销/查询
    - 资源状态实时跟踪（已用/可用/等待中）
    - 按类型的资源分组统计
    - 线程安全的并发访问控制

    使用示例:
        >>> registry = ResourceRegistry()
        >>> registry.register("file_source", ResourceMetadata(
        ...     ResourceType.FILE, "Source Code Files", 100, 8,
        ...     "Python source code files", max_concurrent=5
        ... ))
        >>> stats = registry.get_stats("file_source")
    """

    def __init__(self) -> None:
        self._resources: Dict[str, ResourceMetadata] = {}
        self._lock = threading.RLock()
        self._waiting_queues: Dict[str, List[str]] = {}  # resource_id -> [agent_ids]

    def register(self, resource_id: str, metadata: ResourceMetadata) -> bool:
        """
        注册新资源

        Args:
            resource_id: 唯一资源标识符
            metadata: 资源元数据

        Returns:
            注册成功返回True，已存在返回False

        Raises:
            ValueError: 参数校验失败时抛出
        """
        if not resource_id or not resource_id.strip():
            raise ValueError("resource_id cannot be empty")

        with self._lock:
            if resource_id in self._resources:
                return False

            self._resources[resource_id] = metadata
            self._waiting_queues[resource_id] = []
            return True

    def unregister(self, resource_id: str) -> bool:
        """
        注销资源

        Args:
            resource_id: 要注销的资源ID

        Returns:
            注销成功返回True，不存在返回False
        """
        with self._lock:
            if resource_id not in self._resources:
                return False

            del self._resources[resource_id]
            if resource_id in self._waiting_queues:
                del self._waiting_queues[resource_id]
            return True

    def get_metadata(self, resource_id: str) -> Optional[ResourceMetadata]:
        """获取资源元数据"""
        with self._lock:
            return self._resources.get(resource_id)

    def get_all_resources(self) -> Dict[str, ResourceMetadata]:
        """获取所有注册资源的副本"""
        with self._lock:
            return dict(self._resources)

    def get_resources_by_type(self, resource_type: ResourceType) -> Dict[str, ResourceMetadata]:
        """按类型获取资源"""
        with self._lock:
            return {
                rid: meta for rid, meta in self._resources.items()
                if meta.resource_type == resource_type
            }

    def acquire(self, resource_id: str, amount: int = 1) -> bool:
        """
        尝试获取资源配额

        Args:
            resource_id: 资源ID
            amount: 请求数量

        Returns:
            获取成功返回True
        """
        with self._lock:
            if resource_id not in self._resources:
                return False

            meta = self._resources[resource_id]
            if meta.current_usage + amount > meta.max_concurrent:
                return False

            meta.current_usage += amount
            meta.last_updated = datetime.now()
            return True

    def release(self, resource_id: str, amount: int = 1) -> bool:
        """
        释放资源配额

        Args:
            resource_id: 资源ID
            amount: 释放数量

        Returns:
            释放成功返回True
        """
        with self._lock:
            if resource_id not in self._resources:
                return False

            meta = self._resources[resource_id]
            meta.current_usage = max(0, meta.current_usage - amount)
            meta.last_updated = datetime.now()
            return True

    def add_to_waiting(self, resource_id: str, agent_id: str) -> None:
        """将Agent加入等待队列"""
        with self._lock:
            if resource_id in self._waiting_queues and agent_id not in self._waiting_queues[resource_id]:
                self._waiting_queues[resource_id].append(agent_id)

    def remove_from_waiting(self, resource_id: str, agent_id: str) -> None:
        """从等待队列移除Agent"""
        with self._lock:
            if resource_id in self._waiting_queues and agent_id in self._waiting_queues[resource_id]:
                self._waiting_queues[resource_id].remove(agent_id)

    def get_waiting_count(self, resource_id: str) -> int:
        """获取等待队列长度"""
        with self._lock:
            return len(self._waiting_queues.get(resource_id, []))

    def get_stats(self, resource_id: str) -> Optional[ResourceStats]:
        """
        获取资源实时统计

        Returns:
            ResourceStats对象或None（如果资源不存在）
        """
        with self._lock:
            if resource_id not in self._resources:
                return None

            meta = self._resources[resource_id]
            available = meta.max_concurrent - meta.current_usage
            utilization = (meta.current_usage / meta.max_concurrent * 100) if meta.max_concurrent > 0 else 0.0

            return ResourceStats(
                resource_id=resource_id,
                resource_type=meta.resource_type,
                total_quota=meta.default_quota,
                used=meta.current_usage,
                available=available,
                waiting_count=len(self._waiting_queues.get(resource_id, [])),
                utilization_percent=round(utilization, 2),
                last_updated=meta.last_updated,
            )

    def get_global_stats(self) -> Dict[str, any]:
        """
        获取全局资源统计摘要

        Returns:
            包含各类资源汇总信息的字典
        """
        with self._lock:
            stats = {
                "total_resources": len(self._resources),
                "by_type": {},
                "total_utilization": 0.0,
                "high_utilization_resources": [],
            }

            type_counts: Dict[ResourceType, int] = {}
            total_util = 0.0
            count = 0

            for rid, meta in self._resources.items():
                rtype = meta.resource_type
                type_counts[rtype] = type_counts.get(rtype, 0) + 1

                util = (meta.current_usage / meta.max_concurrent * 100) if meta.max_concurrent > 0 else 0.0
                total_util += util
                count += 1

                if util > 80:
                    stats["high_utilization_resources"].append({
                        "resource_id": rid,
                        "utilization": round(util, 2),
                    })

            stats["by_type"] = {
                rt.name: cnt for rt, cnt in type_counts.items()
            }
            stats["total_utilization"] = round(total_util / max(count, 1), 2)

            return stats

    def reset_usage(self, resource_id: str) -> bool:
        """重置资源使用计数（用于测试或紧急恢复）"""
        with self._lock:
            if resource_id not in self._resources:
                return False

            self._resources[resource_id].current_usage = 0
            self._resources[resource_id].last_updated = datetime.now()
            return True

    def __len__(self) -> int:
        with self._lock:
            return len(self._resources)

    def __contains__(self, resource_id: str) -> bool:
        with self._lock:
            return resource_id in self._resources
