"""
省基类 - 三省（中书省/门下省/尚书省）的抽象基础
基于三省六部二十四司治理架构
"""
from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


class ProvinceType(Enum):
    """省类型枚举"""
    ZHONGSHUSHENG = "zhongshusheng"
    MENXIASHENG = "menxiasheng"
    SHANGSHUSHENG = "shangshusheng"


class ProvinceStatus(Enum):
    """省状态枚举"""
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class Task:
    """任务数据结构"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    task_type: str = ""
    priority: str = "medium"
    source_province: Optional[str] = None
    target_province: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: "")
    status: str = "pending"


@dataclass
class CoordinationResult:
    """协调结果"""
    success: bool = False
    task_id: str = ""
    province_name: str = ""
    output_data: Dict[str, Any] = field(default_factory=dict)
    next_actions: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProvinceStatusReport:
    """省状态报告"""
    province_type: ProvinceType
    province_name: str
    current_status: ProvinceStatus
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    queued_tasks: int = 0
    bureaus_status: Dict[str, str] = field(default_factory=dict)
    health_score: float = 100.0
    last_activity: str = ""
    error_log: List[Dict[str, Any]] = field(default_factory=list)


class BaseProvince(ABC):
    """
    省级抽象基类

    三省架构：
    - 中书省(Zhongshusheng): 决策层 - 需求分析、架构设计、规范制定、方案审议
    - 门下省(Menxiasheng): 审核层 - 代码审查、测试验证、质量监控、合规审计
    - 尚书省(Shangshusheng): 执行层 - 六部×四司=二十四司具体执行
    """

    def __init__(self, name: str, province_type: ProvinceType):
        self.name = name
        self.province_type = province_type
        self.status = ProvinceStatus.IDLE
        self._task_queue: List[Task] = []
        self._active_task: Optional[Task] = None
        self._completed_tasks: List[Task] = []
        self._failed_tasks: List[Task] = []
        self._bureaus: Dict[str, Any] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}

    @abstractmethod
    def coordinate(self, task: Task) -> CoordinationResult:
        """
        协调任务执行

        Args:
            task: 待执行的任务

        Returns:
            CoordinationResult: 协调结果，包含输出数据和后续动作
        """
        pass

    @abstractmethod
    def report_status(self) -> ProvinceStatusReport:
        """
        报告当前省的状态

        Returns:
            ProvinceStatusReport: 详细的状态报告
        """
        pass

    def receive_task(self, task: Task) -> bool:
        """
        接收任务到队列

        Args:
            task: 待接收的任务

        Returns:
            bool: 是否成功接收
        """
        if not task.id:
            task.id = str(uuid.uuid4())
        task.target_province = self.province_type.value
        self._task_queue.append(task)
        logger.info(f"[{self.name}] 任务已接收: {task.id} ({task.name})")
        return True

    def get_next_task(self) -> Optional[Task]:
        """
        获取队列中的下一个任务

        Returns:
            Optional[Task]: 下一个待处理任务
        """
        if self._task_queue:
            return self._task_queue.pop(0)
        return None

    def complete_task(self, task: Task, result: CoordinationResult) -> None:
        """
        标记任务完成

        Args:
            task: 已完成的任务
            result: 执行结果
        """
        task.status = "completed" if result.success else "failed"
        if result.success:
            self._completed_tasks.append(task)
        else:
            self._failed_tasks.append(task)
        self._active_task = None
        logger.info(f"[{self.name}] 任务{'完成' if result.success else '失败'}: {task.id}")

    def register_bureau(self, bureau_name: str, bureau_instance: Any) -> None:
        """
        注册局到省

        Args:
            bureau_name: 局名称
            bureau_instance: 局实例
        """
        self._bureaus[bureau_name] = bureau_instance
        logger.debug(f"[{self.name}] 局已注册: {bureau_name}")

    def get_bureau(self, bureau_name: str) -> Optional[Any]:
        """
        获取指定局的实例

        Args:
            bureau_name: 局名称

        Returns:
            Optional[Any]: 局实例或None
        """
        return self._bureaus.get(bureau_name)

    def on_event(self, event_type: str, handler: Callable) -> None:
        """
        注册事件处理器

        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        触发事件

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                logger.error(f"[{self.name}] 事件处理器错误 ({event_type}): {e}")

    def list_bureaus(self) -> List[str]:
        """
        列出所有已注册的局

        Returns:
            List[str]: 局名称列表
        """
        return list(self._bureaus.keys())

    @property
    def queue_length(self) -> int:
        """队列中待处理任务数"""
        return len(self._task_queue)

    @property
    def is_busy(self) -> bool:
        """是否正在处理任务"""
        return self._active_task is not None
