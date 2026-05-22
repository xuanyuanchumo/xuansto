"""
事件总线 - 跨部门异步通信机制
支持发布/订阅模式、事件过滤、优先级队列
"""
from __future__ import annotations

import asyncio
import inspect
import uuid
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Awaitable


class EventBusError(Exception):
    """事件总线相关异常"""
    pass


class EventPriority(int, Enum):
    """事件优先级"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Event:
    """事件数据类"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    source: str | None = None
    target: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    priority: EventPriority = EventPriority.NORMAL
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "target": self.target,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "priority": self.priority.name,
            "metadata": self.metadata,
        }


EventHandler = Callable[[Event], Awaitable[None]] | Callable[[Event], None]


@dataclass
class Subscription:
    """订阅信息"""
    handler: EventHandler
    filter_fn: Callable[[Event], bool] | None = None
    priority: int = 0
    subscribed_at: str = field(default_factory=lambda: datetime.now().isoformat())


class EventType:
    """预定义事件类型常量"""

    TASK_CREATED = "task.created"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"

    QUALITY_ALERT = "quality.alert"
    QUALITY_METRIC_UPDATE = "quality.metric_update"

    EVOLUTION_CYCLE_STARTED = "evolution.cycle_started"
    EVOLUTION_CYCLE_COMPLETED = "evolution.cycle_completed"

    PROVINCE_HANDOFF = "province.handoff"
    DEPARTMENT_HANDOFF = "department.handoff"

    DOCUMENT_GENERATED = "document.generated"
    SCRIPT_EXECUTED = "script.executed"

    AGENT_SELECTED = "agent.selected"
    SKILL_CALLED = "skill.called"
    ERROR_OCCURRED = "error.occurred"

    ALL_EVENTS = "*"


class EventBus:
    """
    事件总线

    跨部门异步通信机制，支持发布/订阅模式、事件过滤、优先级队列。
    提供同步/异步发布、装饰器订阅、事件历史记录等功能。
    """

    _instance: EventBus | None = None

    def __init__(self, max_history: int = 1000) -> None:
        self._subscribers: dict[str, list[Subscription]] = {}
        self._history: list[Event] = []
        self._max_history: int = max_history
        self._lock: threading.RLock = threading.RLock()
        self._waiters: dict[str, list[asyncio.Future]] = {}
        self._publish_count: int = 0
        self._subscribe_count: int = 0

    @classmethod
    def get_instance(cls, max_history: int = 1000) -> EventBus:
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls(max_history=max_history)
        return cls._instance

    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
        filter_fn: Callable[[Event], bool] | None = None,
        priority: int = 0,
    ) -> None:
        """
        订阅事件

        Args:
            event_type: 事件类型（使用 '*' 订阅所有事件）
            handler: 事件处理函数（支持同步和异步）
            filter_fn: 可选的过滤函数，返回True时才调用handler
            priority: 优先级，数值越大越先执行

        Raises:
            EventBusError: 当参数无效时
        """
        if not event_type:
            raise EventBusError("事件类型不能为空")
        if not callable(handler):
            raise EventBusError("handler必须是可调用的")

        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []

            subscription = Subscription(
                handler=handler,
                filter_fn=filter_fn,
                priority=priority,
            )

            self._subscribers[event_type].append(subscription)
            self._subscribers[event_type].sort(
                key=lambda s: s.priority, reverse=True
            )
            self._subscribe_count += 1

    def unsubscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> bool:
        """
        取消订阅

        Args:
            event_type: 事件类型
            handler: 要取消的事件处理函数

        Returns:
            是否成功取消订阅
        """
        with self._lock:
            if event_type not in self._subscribers:
                return False

            original_count: int = len(self._subscribers[event_type])
            self._subscribers[event_type] = [
                sub for sub in self._subscribers[event_type]
                if sub.handler is not handler
            ]

            removed: bool = len(self._subscribers[event_type]) < original_count

            if not self._subscribers[event_type]:
                del self._subscribers[event_type]

            return removed

    def publish(self, event: Event) -> int:
        """
        发布事件（同步方式）

        Args:
            event: 要发布的Event对象

        Returns:
            成功通知的订阅者数量
        """
        with self._lock:
            self._add_to_history(event)
            self._publish_count += 1

        notified_count: int = 0
        target_types: list[str] = [event.event_type, EventType.ALL_EVENTS]

        for etype in target_types:
            subscribers: list[Subscription] | None = None
            with self._lock:
                subscribers = self._subscribers.get(etype, [])

            for subscription in subscribers:
                try:
                    if subscription.filter_fn is not None:
                        if not subscription.filter_fn(event):
                            continue

                    handler: EventHandler = subscription.handler
                    if inspect.iscoroutinefunction(handler):
                        asyncio.ensure_future(handler(event))
                    else:
                        handler(event)

                    notified_count += 1

                except Exception as e:
                    error_event = Event(
                        event_type=EventType.ERROR_OCCURRED,
                        source="EventBus",
                        payload={
                            "original_event_id": event.event_id,
                            "error": str(e),
                            "handler": getattr(handler, "__name__", str(handler)),
                        },
                        priority=EventPriority.LOW,
                    )
                    self.publish(error_event)

        self._notify_waiters(event)

        return notified_count

    async def publish_async(self, event: Event) -> asyncio.Task:
        """
        异步发布事件

        Args:
            event: 要发布的Event对象

        Returns:
            asyncio.Task对象
        """
        async def _async_publish() -> int:
            with self._lock:
                self._add_to_history(event)
                self._publish_count += 1

            notified_count: int = 0
            target_types: list[str] = [event.event_type, EventType.ALL_EVENTS]

            for etype in target_types:
                subscribers: list[Subscription]
                with self._lock:
                    subscribers = list(self._subscribers.get(etype, []))

                for subscription in subscribers:
                    try:
                        if subscription.filter_fn is not None:
                            if not subscription.filter_fn(event):
                                continue

                        handler: EventHandler = subscription.handler
                        if inspect.iscoroutinefunction(handler):
                            await handler(event)
                        else:
                            handler(event)

                        notified_count += 1

                    except Exception as e:
                        pass

            self._notify_waiters(event)
            return notified_count

        task: asyncio.Task = asyncio.create_task(_async_publish())
        return task

    def on(
        self,
        event_type: str,
        filter_fn: Callable[[Event], bool] | None = None,
        priority: int = 0,
    ) -> Callable:
        """
        装饰器风格的订阅方式

        Args:
            event_type: 事件类型
            filter_fn: 可选的过滤函数
            priority: 优先级

        使用示例::

            @bus.on("task.completed")
            def handle_task_complete(event):
                print(f"任务完成: {event.payload}")
        """

        def decorator(func: EventHandler) -> EventHandler:
            self.subscribe(event_type, func, filter_fn=filter_fn, priority=priority)
            return func

        return decorator

    def get_event_history(
        self,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[Event]:
        """
        获取事件历史

        Args:
            event_type: 可选，按事件类型过滤
            limit: 返回的最大条数

        Returns:
            Event列表（按时间倒序）
        """
        with self._lock:
            history: list[Event] = list(self._history)

        if event_type:
            history = [e for e in history if e.event_type == event_type]

        return history[-limit:]

    def clear_history(self) -> None:
        """清空事件历史"""
        with self._lock:
            self._history.clear()

    async def wait_for(
        self,
        event_type: str,
        timeout: float | None = None,
        filter_fn: Callable[[Event], bool] | None = None,
    ) -> Event:
        """
        等待特定类型的事件

        Args:
            event_type: 等待的事件类型
            timeout: 超时时间（秒），None表示无限等待
            filter_fn: 可选的过滤函数

        Returns:
            匹配的Event对象

        Raises:
            asyncio.TimeoutError: 当超时时
        """
        loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        future: asyncio.Future[Event] = loop.create_future()

        waiter_entry: dict[str, Any] = {
            "future": future,
            "filter_fn": filter_fn,
        }

        with self._lock:
            if event_type not in self._waiters:
                self._waiters[event_type] = []
            self._waiters[event_type].append(waiter_entry)

        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            with self._lock:
                if event_type in self._waiters:
                    self._waiters[event_type] = [
                        w for w in self._waiters[event_type]
                        if w["future"] is not future
                    ]
            raise
        finally:
            pass

    def _notify_waiters(self, event: Event) -> None:
        """通知等待者"""
        target_types: list[str] = [event.event_type, EventType.ALL_EVENTS]

        for etype in target_types:
            waiters: list[dict[str, Any]] | None = None
            with self._lock:
                waiters = self._waiters.get(etype, [])

            for waiter in list(waiters):
                future: asyncio.Future = waiter["future"]
                if future.done():
                    continue

                filter_fn: Callable[[Event], bool] | None = waiter.get("filter_fn")
                if filter_fn is not None and not filter_fn(event):
                    continue

                try:
                    future.set_result(event)
                except asyncio.InvalidStateError:
                    pass

    def _add_to_history(self, event: Event) -> None:
        """添加事件到历史记录"""
        self._history.append(event)

        while len(self._history) > self._max_history:
            self._history.pop(0)

    @property
    def total_subscriptions(self) -> int:
        total: int = 0
        with self._lock:
            for subs in self._subscribers.values():
                total += len(subs)
        return total

    @property
    def registered_event_types(self) -> list[str]:
        with self._lock:
            return sorted(self._subscribers.keys())

    @property
    def history_size(self) -> int:
        with self._lock:
            return len(self._history)

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "total_publishes": self._publish_count,
            "total_subscribes": self._subscribe_count,
            "current_subscriptions": self.total_subscriptions,
            "registered_types": len(self.registered_event_types),
            "history_size": self.history_size,
            "max_history": self._max_history,
        }

    def create_event(
        self,
        event_type: str,
        source: str | None = None,
        target: str | None = None,
        payload: dict[str, Any] | None = None,
        priority: EventPriority | int = EventPriority.NORMAL,
        **metadata: Any,
    ) -> Event:
        """
        工厂方法：创建新事件

        Args:
            event_type: 事件类型
            source: 事件来源
            target: 事件目标
            payload: 事件负载数据
            priority: 优先级
            **metadata: 额外的元数据

        Returns:
            新创建的Event对象
        """
        if isinstance(priority, int):
            try:
                priority = EventPriority(priority)
            except ValueError:
                priority = EventPriority.NORMAL

        meta_dict: dict[str, Any] = dict(metadata)

        return Event(
            event_type=event_type,
            source=source,
            target=target,
            payload=payload or {},
            priority=priority,
            metadata=meta_dict,
        )

    def emit(
        self,
        event_type: str,
        payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> int:
        """
        快捷发布事件的便捷方法

        Args:
            event_type: 事件类型
            payload: 事件负载
            **kwargs: 传递给create_event的其他参数

        Returns:
            通知的订阅者数量
        """
        event: Event = self.create_event(event_type, payload=payload, **kwargs)
        return self.publish(event)

    def __repr__(self) -> str:
        return (
            f"EventBus(subscriptions={self.total_subscriptions}, "
            f"types={len(self.registered_event_types)}, "
            f"history={self.history_size})"
        )


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 事件总线测试")
    print("=" * 60)

    bus = EventBus()

    received_events: list[Event] = []

    def sync_handler(event: Event) -> None:
        received_events.append(event)
        print(f"   📨 同步处理器收到: {event.event_type} (来自 {event.source})")

    async def async_handler(event: Event) -> None:
        print(f"   📨 异步处理器收到: {event.event_type} (ID: {event.event_id[:8]}...)")

    print("\n--- 测试订阅与发布 ---")

    bus.subscribe(EventType.TASK_CREATED, sync_handler)
    bus.subscribe(EventType.TASK_CREATED, async_handler)

    event1 = bus.create_event(
        event_type=EventType.TASK_CREATED,
        source="TestRunner",
        payload={"task_id": "T001", "name": "测试任务"},
        priority=EventPriority.HIGH,
    )

    count = bus.publish(event1)
    print(f"✅ 已发布事件，通知了 {count} 个订阅者")

    print("\n--- 测试装饰器风格订阅 ---")

    @bus.on(EventType.TASK_COMPLETED, priority=10)
    def handle_completion(event: Event) -> None:
        print(f"   ✅ 任务完成! payload: {event.payload}")

    bus.emit(
        EventType.TASK_COMPLETED,
        payload={"task_id": "T001", "duration_ms": 1500},
        source="Worker",
    )

    print("\n--- 测试通配符订阅 ---")

    @bus.on(EventType.ALL_EVENTS)
    def catch_all(event: Event) -> None:
        print(f"   🔔 捕获所有事件: {event.event_type}")

    bus.emit(
        EventType.SCRIPT_EXECUTED,
        payload={"script": "test_script.py"},
        source="ScriptRunner",
    )

    print("\n--- 测试事件过滤 ---")

    def only_high_priority(event: Event) -> bool:
        return event.priority == EventPriority.CRITICAL

    bus.subscribe(
        EventType.QUALITY_ALERT,
        lambda e: print(f"   ⚠️ 仅CRITICAL级别: {e.payload}"),
        filter_fn=only_high_priority,
    )

    normal_alert = bus.create_event(
        EventType.QUALITY_ALERT,
        payload={"metric": "coverage", "value": 45},
        priority=EventPriority.NORMAL,
    )
    bus.publish(normal_alert)

    critical_alert = bus.create_event(
        EventType.QUALITY_ALERT,
        payload={"metric": "security", "issue": "SQL注入"},
        priority=EventPriority.CRITICAL,
    )
    bus.publish(critical_alert)

    print("\n--- 测试事件历史 ---")
    history = bus.get_event_history(limit=5)
    print(f"最近 {len(history)} 条事件:")
    for evt in reversed(history[-3:]):
        print(f"   [{evt.priority.name}] {evt.event_type} @ {evt.timestamp[:19]}")

    task_history = bus.get_event_history(event_type=EventType.TASK_CREATED)
    print(f"\ntask.created 类型事件数: {len(task_history)}")

    print("\n--- 统计信息 ---")
    stats = bus.stats
    print(f"总发布次数: {stats['total_publishes']}")
    print(f"总订阅次数: {stats['total_subscribes']}")
    print(f"当前活跃订阅: {stats['current_subscriptions']}")
    print(f"已注册事件类型: {stats['registered_types']}")
    print(f"历史记录大小: {stats['history_size']}/{stats['max_history']}")

    print("\n--- 测试取消订阅 ---")
    removed = bus.unsubscribe(EventType.TASK_CREATED, sync_handler)
    print(f"取消订阅结果: {'✅ 成功' if removed else '❌ 失败'}")

    print("\n--- 列出所有注册的事件类型 ---")
    for etype in bus.registered_event_types:
        subs_count = len(bus._subscribers.get(etype, []))
        print(f"   📋 {etype} ({subs_count} 个订阅者)")

    print("\n--- 测试预定义事件类型 ---")
    predefined = [
        EventType.TASK_CREATED,
        EventType.TASK_STARTED,
        EventType.TASK_COMPLETED,
        EventType.TASK_FAILED,
        EventType.QUALITY_ALERT,
        EventType.QUALITY_METRIC_UPDATE,
        EventType.EVOLUTION_CYCLE_STARTED,
        EventType.EVOLUTION_CYCLE_COMPLETED,
        EventType.PROVINCE_HANDOFF,
        EventType.DEPARTMENT_HANDOFF,
        EventType.DOCUMENT_GENERATED,
        EventType.SCRIPT_EXECUTED,
    ]
    print(f"预定义事件类型 ({len(predefined)}个):")
    for et in predefined:
        print(f"   • {et}")

    print("\n✅ 所有测试通过!")
