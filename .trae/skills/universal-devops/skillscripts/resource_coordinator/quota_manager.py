"""
配额管理器模块 - 多维度资源配额控制系统

支持的配额类型:
- MemoryQuota: 内存配额（单Agent限制、全局阈值）
- NetworkQuota: 网络配额（API频率、连接数、带宽）
- CPUQuota: CPU配额（时间片、公平分配）

核心特性:
- 令牌桶算法实现平滑限流
- 动态阈值告警与自动恢复
- 按权重的公平资源分配
- 完整的使用统计与报告
"""

from __future__ import annotations

import gc
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple


class QuotaExceededAction(Enum):
    """配额超限处理动作"""
    REJECT = "reject"
    QUEUE = "queue"
    DEGRADE = "degrade"
    WARNING_ONLY = "warning_only"


@dataclass
class MemoryQuota:
    """内存配额配置"""
    per_agent_max_mb: int = 512
    global_warning_threshold: float = 0.8  # 80%
    global_critical_threshold: float = 0.95  # 95%


@dataclass
class NetworkQuota:
    """网络配额配置"""
    api_calls_per_minute: int = 60
    max_concurrent_connections: int = 10
    download_bandwidth_mbps: int = 0  # 0=不限制


@dataclass
class CPUQuota:
    """CPU配额配置"""
    fair_share_enabled: bool = True
    time_slice_ms: int = 100
    max_cpu_percent_per_agent: float = 25.0


@dataclass
class QuotaUsage:
    """配额使用记录"""
    agent_id: str
    memory_used_mb: float
    memory_limit_mb: int
    api_calls_this_minute: int
    api_calls_limit: int
    cpu_time_ms: float
    cpu_percent: float
    active_connections: int
    connection_limit: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TokenBucket:
    """
    令牌桶 - 平滑请求限流算法

    特性:
    - 允许突发流量（桶容量）
    - 平均速率控制（填充速率）
    - 无状态设计（适合分布式场景）
    """
    capacity: int
    refill_rate: float  # tokens per second
    tokens: float = field(init=False)
    last_refill: float = field(init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    def __post_init__(self) -> None:
        self.tokens = float(self.capacity)
        self.last_refill = time.monotonic()

    def consume(self, tokens: int = 1) -> bool:
        """
        尝试消费令牌

        Args:
            tokens: 需要的令牌数量

        Returns:
            成功返回True，令牌不足返回False
        """
        with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def available_tokens(self) -> float:
        """获取当前可用令牌数"""
        with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now
            return self.tokens

    def reset(self) -> None:
        """重置令牌桶"""
        with self._lock:
            self.tokens = float(self.capacity)
            self.last_refill = time.monotonic()


class QuotaManager:
    """
    配额管理器 - 资源使用守门员

    功能:
    - 内存/CPU/网络多维配额控制
    - 基于令牌桶的API限流
    - 动态阈值告警与自动恢复
    - 公平的资源分配策略
    - 详细的使用统计报告

    使用示例:
        >>> manager = QuotaManager()
        >>> manager.register_agent("agent_1", weight=2.0)
        >>> if manager.check_memory_quota("agent_1", 256):
        ...     manager.allocate_memory("agent_1", 256)
        >>> if manager.allow_api_call("agent_1"):
        ...     pass  # 执行API调用
        >>> usage = manager.get_usage("agent_1")
    """

    def __init__(
        self,
        memory_config: MemoryQuota | None = None,
        network_config: NetworkQuota | None = None,
        cpu_config: CPUQuota | None = None,
    ) -> None:
        self._memory_config = memory_config or MemoryQuota()
        self._network_config = network_config or NetworkQuota()
        self._cpu_config = cpu_config or CPUQuota()

        self._agent_memory: Dict[str, float] = {}  # agent_id -> MB used
        self._agent_api_buckets: Dict[str, TokenBucket] = {}
        self._agent_connections: Dict[str, int] = {}
        self._agent_cpu_time: Dict[str, float] = {}
        self._agent_weights: Dict[str, float] = {}

        self._global_memory_used: float = 0.0
        self._total_memory_limit_mb: float = 4096.0  # 默认全局4GB
        self._api_call_log: List[Tuple[str, float]] = []  # (agent_id, timestamp)

        self._lock = threading.RLock()
        self._warning_state: bool = False
        self._critical_state: bool = False
        self._rejected_count: int = 0
        self._degraded_count: int = 0

    def register_agent(
        self,
        agent_id: str,
        weight: float = 1.0,
        memory_limit_mb: int | None = None,
    ) -> bool:
        """
        注册Agent并初始化配额

        Args:
            agent_id: Agent唯一标识
            weight: 权重系数（用于公平分配）
            memory_limit_mb: 自定义内存限制，None使用默认值

        Returns:
            注册成功返回True
        """
        with self._lock:
            if agent_id in self._agent_memory:
                return False

            limit = memory_limit_mb or self._memory_config.per_agent_max_mb
            self._agent_memory[agent_id] = 0.0
            self._agent_weights[agent_id] = max(0.1, weight)
            self._agent_connections[agent_id] = 0
            self._agent_cpu_time[agent_id] = 0.0

            refill_rate = self._network_config.api_calls_per_minute / 60.0
            burst = min(self._network_config.api_calls_per_minute, 10)
            self._agent_api_buckets[agent_id] = TokenBucket(
                capacity=burst,
                refill_rate=refill_rate,
            )

            return True

    def unregister_agent(self, agent_id: str) -> bool:
        """注销Agent并释放其资源"""
        with self._lock:
            if agent_id not in self._agent_memory:
                return False

            used = self._agent_memory.pop(agent_id, 0.0)
            self._global_memory_used = max(0.0, self._global_memory_used - used)

            self._agent_api_buckets.pop(agent_id, None)
            self._agent_connections.pop(agent_id, None)
            self._agent_cpu_time.pop(agent_id, None)
            self._agent_weights.pop(agent_id, None)

            return True

    def check_memory_quota(self, agent_id: str, requested_mb: float) -> Tuple[bool, str]:
        """
        检查内存配额是否允许分配

        Args:
            agent_id: Agent ID
            requested_mb: 请求的内存量(MB)

        Returns:
            (是否允许, 原因说明)
        """
        with self._lock:
            global_utilization = self._global_memory_used / self._total_memory_limit_mb

            if global_utilization >= self._memory_config.global_critical_threshold:
                self._critical_state = True
                self._rejected_count += 1
                self._force_garbage_collection()
                return False, f"Global memory critical ({global_utilization:.1%}), GC triggered"

            if global_utilization >= self._memory_config.global_warning_threshold:
                self._warning_state = True
                if requested_mb > 50:
                    self._degraded_count += 1
                    return False, f"Global memory warning ({global_utilization:.1%}), large allocation rejected"

            current = self._agent_memory.get(agent_id, 0.0)
            limit = self._memory_config.per_agent_max_mb

            if current + requested_mb > limit:
                return False, f"Agent {agent_id} would exceed per-agent limit ({current + requested_mb:.1f}/{limit}MB)"

            remaining_global = self._total_memory_limit_mb - self._global_memory_used
            if requested_mb > remaining_global:
                return False, f"Insufficient global memory ({remaining_global:.1f}MB available)"

            return True, "OK"

    def allocate_memory(self, agent_id: str, amount_mb: float) -> bool:
        """
        分配内存给Agent

        Args:
            agent_id: Agent ID
            amount_mb: 分配量(MB)

        Returns:
            分配成功返回True
        """
        allowed, reason = self.check_memory_quota(agent_id, amount_mb)
        if not allowed:
            return False

        with self._lock:
            self._agent_memory[agent_id] = self._agent_memory.get(agent_id, 0.0) + amount_mb
            self._global_memory_used += amount_mb
            return True

    def release_memory(self, agent_id: str, amount_mb: float) -> bool:
        """释放Agent占用的内存"""
        with self._lock:
            if agent_id not in self._agent_memory:
                return False

            current = self._agent_memory[agent_id]
            released = min(amount_mb, current)
            self._agent_memory[agent_id] -= released
            self._global_memory_used = max(0.0, self._global_memory_used - released)

            if self._global_memory_used < self._total_memory_limit_mb * 0.7:
                self._warning_state = False
                self._critical_state = False

            return True

    def allow_api_call(self, agent_id: str) -> Tuple[bool, str]:
        """
        检查是否允许API调用（令牌桶限流）

        Returns:
            (是否允许, 信息)
        """
        with self._lock:
            bucket = self._agent_api_buckets.get(agent_id)
            if not bucket:
                return False, "Agent not registered"

            if bucket.consume(1):
                self._api_call_log.append((agent_id, time.time()))
                return True, "API call allowed"

            retry_after = (1 - bucket.available_tokens()) / bucket.refill_rate
            return False, f"Rate limited, retry after {retry_after:.1f}s"

    def check_connection_quota(self, agent_id: str) -> Tuple[bool, str]:
        """检查连接数配额"""
        with self._lock:
            current = self._agent_connections.get(agent_id, 0)
            limit = self._network_config.max_concurrent_connections

            total_connections = sum(self._agent_connections.values())
            if total_connections >= limit * 2:
                return False, "Global connection limit reached"

            if current >= limit:
                return False, f"Agent {agent_id} connection limit reached ({current}/{limit})"

            return True, "Connection allowed"

    def add_connection(self, agent_id: str) -> bool:
        """增加Agent的活跃连接数"""
        allowed, _ = self.check_connection_quota(agent_id)
        if allowed:
            with self._lock:
                self._agent_connections[agent_id] = self._agent_connections.get(agent_id, 0) + 1
            return True
        return False

    def remove_connection(self, agent_id: str) -> bool:
        """减少Agent的活跃连接数"""
        with self._lock:
            if agent_id in self._agent_connections and self._agent_connections[agent_id] > 0:
                self._agent_connections[agent_id] -= 1
                return True
            return False

    def record_cpu_time(self, agent_id: str, time_ms: float) -> None:
        """记录CPU使用时间"""
        with self._lock:
            self._agent_cpu_time[agent_id] = self._agent_cpu_time.get(agent_id, 0.0) + time_ms

    def get_cpu_allocation(self, agent_id: str) -> float:
        """
        获取Agent的CPU时间片分配（毫秒）

        基于权重公平分配
        """
        with self._lock:
            if not self._cpu_config.fair_share_enabled:
                return float(self._cpu_config.time_slice_ms)

            total_weight = sum(self._agent_weights.values()) or 1.0
            agent_weight = self._agent_weights.get(agent_id, 1.0)
            share = (agent_weight / total_weight) * self._cpu_config.time_slice_ms
            return min(share, self._cpu_config.time_slice_ms * 0.8)

    def get_usage(self, agent_id: str) -> Optional[QuotaUsage]:
        """获取Agent的详细配额使用情况"""
        with self._lock:
            if agent_id not in self._agent_memory:
                return None

            one_minute_ago = time.time() - 60
            recent_calls = sum(1 for _, ts in self._api_call_log if ts > one_minute_ago and _ == agent_id)

            return QuotaUsage(
                agent_id=agent_id,
                memory_used_mb=self._agent_memory.get(agent_id, 0.0),
                memory_limit_mb=self._memory_config.per_agent_max_mb,
                api_calls_this_minute=recent_calls,
                api_calls_limit=self._network_config.api_calls_per_minute,
                cpu_time_ms=self._agent_cpu_time.get(agent_id, 0.0),
                cpu_percent=min(100.0, (self._agent_cpu_time.get(agent_id, 0.0) / 1000.0) * 10),
                active_connections=self._agent_connections.get(agent_id, 0),
                connection_limit=self._network_config.max_concurrent_connections,
            )

    def get_global_status(self) -> Dict[str, any]:
        """获取全局配额状态"""
        with self._lock:
            global_mem_util = self._global_memory_used / self._total_memory_limit_mb
            total_active_conns = sum(self._agent_connections.values())

            return {
                "global_memory": {
                    "used_mb": round(self._global_memory_used, 2),
                    "limit_mb": self._total_memory_limit_mb,
                    "utilization_percent": round(global_mem_util * 100, 2),
                    "is_warning": self._warning_state,
                    "is_critical": self._critical_state,
                },
                "agents": {
                    "registered": len(self._agent_memory),
                    "with_memory_usage": len([a for a, m in self._agent_memory.items() if m > 0]),
                },
                "connections": {
                    "active": total_active_conns,
                    "limit": self._network_config.max_concurrent_connections * 2,
                },
                "statistics": {
                    "total_rejected": self._rejected_count,
                    "total_degraded": self._degraded_count,
                    "registered_agents": len(self._agent_memory),
                },
            }

    def get_all_usages(self) -> List[QuotaUsage]:
        """获取所有Agent的使用情况"""
        with self._lock:
            return [self.get_usage(aid) for aid in list(self._agent_memory.keys()) if self.get_usage(aid)]

    def reset_agent_quota(self, agent_id: str) -> bool:
        """重置指定Agent的所有配额计数器"""
        with self._lock:
            if agent_id not in self._agent_memory:
                return False

            used = self._agent_memory[agent_id]
            self._agent_memory[agent_id] = 0.0
            self._global_memory_used = max(0.0, self._global_memory_used - used)
            self._agent_connections[agent_id] = 0
            self._agent_cpu_time[agent_id] = 0.0

            bucket = self._agent_api_buckets.get(agent_id)
            if bucket:
                bucket.reset()

            return True

    def set_global_memory_limit(self, limit_mb: float) -> None:
        """设置全局内存上限"""
        with self._lock:
            self._total_memory_limit_mb = max(512.0, limit_mb)

    def _force_garbage_collection(self) -> Dict[str, any]:
        """强制垃圾回收"""
        before = self._global_memory_used
        collected = gc.collect()
        after = self._global_memory_used

        return {
            "collected_objects": collected,
            "memory_before_mb": round(before, 2),
            "memory_after_mb": round(after, 2),
            "freed_mb": round(before - after, 2),
            "timestamp": datetime.now().isoformat(),
        }

    def cleanup_old_logs(self, max_age_seconds: float = 3600.0) -> int:
        """清理过期的API调用日志"""
        with self._lock:
            cutoff = time.time() - max_age_seconds
            original_len = len(self._api_call_log)
            self._api_call_log = [(aid, ts) for aid, ts in self._api_call_log if ts > cutoff]
            return original_len - len(self._api_call_log)

    @property
    def is_warning_state(self) -> bool:
        return self._warning_state

    @property
    def is_critical_state(self) -> bool:
        return self._critical_state

    def __len__(self) -> int:
        with self._lock:
            return len(self._agent_memory)

    def __contains__(self, agent_id: str) -> bool:
        with self._lock:
            return agent_id in self._agent_memory
