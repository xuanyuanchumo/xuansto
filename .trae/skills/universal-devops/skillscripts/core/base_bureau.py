"""
局基类 - 中书省和门下省各局的抽象基础
中书省4局：需求分析局、架构设计局、规范制定局、方案审议局
门下省4局：代码审查局、测试验证局、质量监控局、合规审计局
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


class BureauType(Enum):
    """局类型枚举 - 中书省（决策层）"""
    REQUIREMENTS_BUREAU = "requirements_bureau"
    ARCHITECTURE_BUREAU = "architecture_bureau"
    STANDARDS_BUREAU = "standards_bureau"
    REVIEW_BUREAU = "review_bureau"


class AuditBureauType(Enum):
    """局类型枚举 - 门下省（审核层）"""
    CODE_REVIEW_BUREAU = "code_review_bureau"
    TESTING_BUREAU = "testing_bureau"
    QUALITY_MONITOR_BUREAU = "quality_monitor_bureau"
    COMPLIANCE_AUDIT_BUREAU = "compliance_audit_bureau"


class BureauStatus(Enum):
    """局状态枚举"""
    IDLE = "idle"
    PROCESSING = "processing"
    REVIEWING = "reviewing"
    VALIDATING = "validating"
    ERROR = "error"
    COMPLETED = "completed"


@dataclass
class BureauInput:
    """局输入数据"""
    task_id: str = ""
    input_type: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    priority: str = "medium"
    requirements: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BureauOutput:
    """局输出数据"""
    success: bool = False
    bureau_name: str = ""
    task_id: str = ""
    output_type: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: float = 0.0
    quality_score: float = 100.0


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    score: float = 0.0
    checked_items: int = 0
    total_items: int = 0


class BaseBureau(ABC):
    """
    局级抽象基类

    中书省4局（决策层）：
    - requirements_bureau: 需求分析局
    - architecture_bureau: 架构设计局
    - standards_bureau: 规范制定局
    - review_bureau: 方案审议局

    门下省4局（审核层）：
    - code_review_bureau: 代码审查局
    - testing_bureau: 测试验证局
    - quality_monitor_bureau: 质量监控局
    - compliance_audit_bureau: 合规审计局
    """

    def __init__(self, name: str, bureau_type: Any):
        self.name = name
        self.bureau_type = bureau_type
        self.status = BureauStatus.IDLE
        self._history: List[BureauOutput] = []
        self._validators: List[Callable[[BureauOutput], ValidationResult]] = []
        self._config: Dict[str, Any] = {}
        self._start_time: Optional[float] = None

    @abstractmethod
    def execute(self, input_data: BureauInput) -> BureauOutput:
        """
        执行局的核心功能

        Args:
            input_data: 输入数据

        Returns:
            BureauOutput: 执行结果
        """
        pass

    @abstractmethod
    def validate_output(self, output: BureauOutput) -> ValidationResult:
        """
        验证输出结果的质量

        Args:
            output: 待验证的输出

        Returns:
            ValidationResult: 验证结果
        """
        pass

    def process(self, input_data: BureauInput) -> BureauOutput:
        """
        处理输入并返回结果（带计时和错误处理）

        Args:
            input_data: 输入数据

        Returns:
            BureauOutput: 处理结果
        """
        self.status = BureauStatus.PROCESSING
        self._start_time = time.time()

        if not input_data.task_id:
            input_data.task_id = str(uuid.uuid4())

        try:
            output = self.execute(input_data)
            output.bureau_name = self.name
            output.task_id = input_data.task_id

            validation = self.validate_output(output)
            if not validation.is_valid:
                output.validation_errors.extend(validation.errors)
                output.warnings.extend(validation.warnings)
                output.quality_score = validation.score

            output.processing_time_ms = (time.time() - self._start_time) * 1000

            self._history.append(output)
            self.status = BureauStatus.COMPLETED
            logger.info(f"[{self.name}] 处理完成: {input_data.task_id} ({output.processing_time_ms:.2f}ms)")
            return output

        except Exception as e:
            self.status = BureauStatus.ERROR
            logger.error(f"[{self.name}] 处理异常: {e}")
            return BureauOutput(
                success=False,
                bureau_name=self.name,
                task_id=input_data.task_id,
                validation_errors=[str(e)],
                processing_time_ms=(time.time() - self._start_time) * 1000 if self._start_time else 0.0
            )

    def add_validator(self, validator: Callable[[BureauOutput], ValidationResult]) -> None:
        """
        添加自定义验证器

        Args:
            validator: 验证函数
        """
        self._validators.append(validator)

    def get_history(self, limit: int = 10) -> List[BureauOutput]:
        """
        获取处理历史

        Args:
            limit: 返回的最大数量

        Returns:
            List[BureauOutput]: 历史记录列表
        """
        return self._history[-limit:]

    def configure(self, config: Dict[str, Any]) -> None:
        """
        配置局参数

        Args:
            config: 配置字典
        """
        self._config.update(config)

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键
            default: 默认值

        Returns:
            Any: 配置值
        """
        return self._config.get(key, default)

    @property
    def execution_count(self) -> int:
        """已执行次数"""
        return len(self._history)

    @property
    def average_processing_time(self) -> float:
        """平均处理时间(ms)"""
        if not self._history:
            return 0.0
        times = [h.processing_time_ms for h in self._history]
        return sum(times) / len(times)
