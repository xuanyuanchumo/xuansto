"""
司基类 - 二十四司的抽象基础
每司是具体的功能执行单元
"""
from __future__ import annotations

import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional


logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class SiStatus(Enum):
    """司状态枚举"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    status: HealthStatus = HealthStatus.UNKNOWN
    si_name: str = ""
    checks_passed: int = 0
    checks_total: int = 0
    details: Dict[str, Any] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    last_check_time: float = 0.0
    next_check_time: Optional[float] = None


@dataclass
class SiOutput:
    """司输出"""
    si_name: str = ""
    task_id: str = ""
    success: bool = False
    output_data: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    next_steps: List[str] = field(default_factory=list)


@dataclass
class SiConfig:
    """司配置"""
    timeout_seconds: float = 300.0
    max_retries: int = 3
    retry_delay: float = 1.0
    enable_caching: bool = True
    cache_ttl: float = 3600.0
    log_level: str = "INFO"
    required_dependencies: List[str] = field(default_factory=list)
    custom_params: Dict[str, Any] = field(default_factory=dict)


class BaseSi(ABC):
    """
    司级抽象基类 - 二十四司的基础

    每司是一个独立的功能执行单元，负责具体的开发任务。
    二十四司分布在六部之下：
    - 吏部4司: Agent调度、角色管理、技能匹配、协调
    - 户部4司: 环境配置、依赖管理、资源优化、基础设施
    - 礼部4司: 文档管理、模板管理、知识库、标准化
    - 兵部4司: TDD执行、测试框架、覆盖率分析、回归测试
    - 工部4司: 代码生成、UI/UX设计、数据库设计、API设计
    - 刑部4司: Bug修复、重构、自演化、版本控制
    """

    SI_NAME: str = "base_si"
    SI_DESCRIPTION: str = "基础司"
    DEPARTMENT: str = ""

    def __init__(self, config: Optional[SiConfig] = None):
        self.config = config or SiConfig()
        self.status = SiStatus.IDLE
        self._execution_count = 0
        self._success_count = 0
        self._failure_count = 0
        self._last_execution_time: Optional[float] = None
        self._health_history: List[HealthCheckResult] = []
        self._pre_hooks: List[Callable[[SiContext], None]] = []
        self._post_hooks: List[[SiOutput], None] = []
        self._cache: Dict[str, tuple] = {}

    @abstractmethod
    def run(self, context: SiContext) -> SiOutput:
        """
        执行司的核心功能

        Args:
            context: 执行上下文

        Returns:
            SiOutput: 执行结果
        """
        pass

    @abstractmethod
    def self_check(self) -> HealthCheckResult:
        """
        自检健康状况

        Returns:
            HealthCheckResult: 健康检查结果
        """
        pass

    def execute(self, context: SiContext) -> SiOutput:
        """
        完整执行流程（带钩子、重试、超时控制）

        Args:
            context: 执行上下文

        Returns:
            SiOutput: 执行结果
        """
        self.status = SiStatus.INITIALIZING
        start_time = time.time()

        if not context.task_id:
            context.task_id = str(uuid.uuid4())
        context.si_name = self.SI_NAME

        for hook in self._pre_hooks:
            try:
                hook(context)
            except Exception as e:
                logger.warning(f"[{self.SI_NAME}] 前置钩子异常: {e}")

        self.status = SiStatus.RUNNING
        output = self._execute_with_retry(context)

        for hook in self._post_hooks:
            try:
                hook(output)
            except Exception as e:
                logger.warning(f"[{self.SI_NAME}] 后置钩子异常: {e}")

        output.execution_time_ms = (time.time() - start_time) * 1000
        output.si_name = self.SI_NAME
        output.task_id = context.task_id

        self._update_stats(output)
        self.status = SiStatus.COMPLETED if output.success else SiStatus.FAILED
        self._last_execution_time = time.time()

        logger.info(
            f"[{self.SI_NAME}] 执行{'成功' if output.success else '失败'}: "
            f"{context.task_id} ({output.execution_time_ms:.2f}ms)"
        )

        return output

    def _execute_with_retry(self, context: SiContext) -> SiOutput:
        """
        带重试机制的执行

        Args:
            context: 执行上下文

        Returns:
            SiOutput: 执行结果
        """
        last_error = None
        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"[{self.SI_NAME}] 重试第 {attempt} 次...")
                    time.sleep(self.config.retry_delay * attempt)
                return self.run(context)
            except TimeoutError:
                logger.error(f"[{self.SI_NAME}] 执行超时")
                return SiOutput(
                    success=False,
                    errors=[f"执行超时 ({self.config.timeout_seconds}s)"],
                    task_id=context.task_id
                )
            except Exception as e:
                last_error = e
                logger.warning(f"[{self.SI_NAME}] 第 {attempt + 1} 次尝试失败: {e}")

        return SiOutput(
            success=False,
            errors=[f"全部 {self.config.max_retries + 1} 次尝试均失败: {last_error}"],
            task_id=context.task_id
        )

    def add_pre_hook(self, hook: Callable[[SiContext], None]) -> None:
        """
        添加前置钩子

        Args:
            hook: 前置钩子函数
        """
        self._pre_hooks.append(hook)

    def add_post_hook(self, hook: Callable) -> None:
        """
        添加后置钩子

        Args:
            hook: 后置钩子函数
        """
        self._post_hooks.append(hook)

    def _update_stats(self, output: SiOutput) -> None:
        """
        更新统计信息

        Args:
            output: 执行结果
        """
        self._execution_count += 1
        if output.success:
            self._success_count += 1
        else:
            self._failure_count += 1

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict[str, Any]: 统计信息字典
        """
        success_rate = (self._success_count / self._execution_count * 100
                       if self._execution_count > 0 else 0.0)
        return {
            "si_name": self.SI_NAME,
            "total_executions": self._execution_count,
            "success_count": self._success_count,
            "failure_count": self._failure_count,
            "success_rate_pct": round(success_rate, 2),
            "last_execution": self._last_execution_time,
            "current_status": self.status.value
        }

    def cached_execute(self, context: SiContext) -> SiOutput:
        """
        带缓存的执行

        Args:
            context: 执行上下文

        Returns:
            SiOutput: 执行结果
        """
        cache_key = f"{context.task_id}_{hash(str(context.input_data))}"
        if self.config.enable_caching and cache_key in self._cache:
            cached_result, cached_time = self._cache[cache_key]
            if time.time() - cached_time < self.config.cache_ttl:
                logger.debug(f"[{self.SI_NAME}] 使用缓存结果: {cache_key}")
                return cached_result

        result = self.execute(context)
        if self.config.enable_caching:
            self._cache[cache_key] = (result, time.time())
        return result

    def clear_cache(self) -> None:
        """清除缓存"""
        self._cache.clear()

    @classmethod
    def get_info(cls) -> Dict[str, str]:
        """
        获取司的基本信息

        Returns:
            Dict[str, str]: 信息字典
        """
        return {
            "name": cls.SI_NAME,
            "description": cls.SI_DESCRIPTION,
            "department": cls.DEPARTMENT
        }
