"""
部基类 - 尚书省六部的抽象基础
吏部、户部、礼部、兵部、工部、刑部
每部下辖四司
"""
from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


class DepartmentType(Enum):
    """部类型枚举 - 尚书省六部"""
    LIBU = "libu"
    HUBU = "hubu"
    LIBU2 = "libu2"
    BINGBU = "bingbu"
    GONGBU = "gongbu"
    XINGBU = "xingbu"


class DepartmentStatus(Enum):
    """部状态枚举"""
    IDLE = "idle"
    DISPATCHING = "dispatching"
    EXECUTING = "executing"
    AGGREGATING = "aggregating"
    ERROR = "error"
    COMPLETED = "completed"


@dataclass
class SiContext:
    """司执行上下文"""
    task_id: str = ""
    si_name: str = ""
    department: str = ""
    input_data: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SiResult:
    """司执行结果"""
    si_name: str = ""
    task_id: str = ""
    success: bool = False
    output_data: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    health_status: str = "healthy"


@dataclass
class DepartmentOutput:
    """部聚合输出"""
    department_name: str = ""
    task_id: str = ""
    success: bool = False
    aggregated_results: Dict[str, SiResult] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    overall_quality_score: float = 100.0
    failed_sis: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class DispatchTicket:
    """调度工单"""
    ticket_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target_si: str = ""
    task_data: Dict[str, Any] = field(default_factory=dict)
    priority: str = "medium"
    deadline: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)
    created_at: float = 0.0
    status: str = "pending"


class BaseDepartment(ABC):
    """
    部级抽象基类 - 尚书省六部

    六部及其四司：
    - 吏部(Libu): agent_dispatch_si, role_management_si, skill_matching_si, coordination_si
    - 户部(Hubu): environment_config_si, dependency_mgmt_si, resource_optimization_si, infrastructure_si
    - 礼部(Libu2): documentation_si, template_management_si, knowledge_base_si, standardization_si
    - 兵部(Bingbu): tdd_execution_si, test_framework_si, coverage_analysis_si, regression_testing_si
    - 工部(Gongbu): code_generation_si, uiux_design_si, database_design_si, api_design_si
    - 刑部(Xingbu): bug_fixing_si, refactoring_si, self_evolution_si, version_control_si
    """

    DEPARTMENT_SIS: List[str] = []

    def __init__(self, name: str, department_type: DepartmentType):
        self.name = name
        self.department_type = department_type
        self.status = DepartmentStatus.IDLE
        self._sis: Dict[str, Any] = {}
        self._active_dispatches: Dict[str, DispatchTicket] = {}
        self._results_cache: Dict[str, SiResult] = {}
        self._dispatch_history: List[DispatchTicket] = []

    @abstractmethod
    def dispatch_to_si(self, task: Task, target_si: str) -> SiResult:
        """
        将任务分发到指定的司

        Args:
            task: 待分发的任务
            target_si: 目标司名称

        Returns:
            SiResult: 司执行结果
        """
        pass

    @abstractmethod
    def aggregate_results(self, results: List[SiResult]) -> DepartmentOutput:
        """
        聚合多个司的结果

        Args:
            results: 司结果列表

        Returns:
            DepartmentOutput: 部级聚合输出
        """
        pass

    def register_si(self, si_name: str, si_instance: Any) -> None:
        """
        注册司到部

        Args:
            si_name: 司名称
            si_instance: 司实例
        """
        self._sis[si_name] = si_instance
        logger.debug(f"[{self.name}] 司已注册: {si_name}")

    def get_si(self, si_name: str) -> Optional[Any]:
        """
        获取指定司的实例

        Args:
            si_name: 司名称

        Returns:
            Optional[Any]: 司实例或None
        """
        return self._sis.get(si_name)

    def list_sis(self) -> List[str]:
        """
        列出所有已注册的司

        Returns:
            List[str]: 司名称列表
        """
        return list(self._sis.keys())

    def create_dispatch_ticket(self, target_si: str, task_data: Dict[str, Any],
                                priority: str = "medium") -> DispatchTicket:
        """
        创建调度工单

        Args:
            target_si: 目标司
            task_data: 任务数据
            priority: 优先级

        Returns:
            DispatchTicket: 调度工单
        """
        import time
        ticket = DispatchTicket(
            target_si=target_si,
            task_data=task_data,
            priority=priority,
            created_at=time.time()
        )
        self._active_dispatches[ticket.ticket_id] = ticket
        self._dispatch_history.append(ticket)
        return ticket

    def complete_dispatch(self, ticket_id: str, result: SiResult) -> None:
        """
        完成调度并缓存结果

        Args:
            ticket_id: 工单ID
            result: 执行结果
        """
        if ticket_id in self._active_dispatches:
            del self._active_dispatches[ticket_id]
        self._results_cache[f"{ticket_id}_{result.si_name}"] = result

    def get_cached_result(self, key: str) -> Optional[SiResult]:
        """
        获取缓存的结果

        Args:
            key: 结果键

        Returns:
            Optional[SiResult]: 缓存的结果
        """
        return self._results_cache.get(key)

    def parallel_dispatch(self, task: Task, target_sis: List[str]) -> Dict[str, SiResult]:
        """
        并行分发任务到多个司

        Args:
            task: 待分发任务
            target_sis: 目标司列表

        Returns:
            Dict[str, SiResult]: 各司的结果映射
        """
        results = {}
        for si_name in target_sis:
            results[si_name] = self.dispatch_to_si(task, si_name)
        return results

    def sequential_dispatch(self, task: Task, target_sis: List[str]) -> Dict[str, SiResult]:
        """
        串行分发任务到多个司（前一个成功才继续下一个）

        Args:
            task: 待分发任务
            target_sis: 目标司列表（按顺序）

        Returns:
            Dict[str, SiResult]: 各司的结果映射
        """
        results = {}
        for si_name in target_sis:
            result = self.dispatch_to_si(task, si_name)
            results[si_name] = result
            if not result.success:
                logger.warning(f"[{self.name}] {si_name} 执行失败，停止串行分发")
                break
        return results

    @property
    def active_dispatch_count(self) -> int:
        """活跃调度数"""
        return len(self._active_dispatches)

    @property
    def registered_si_count(self) -> int:
        """已注册司数"""
        return len(self._sis)
