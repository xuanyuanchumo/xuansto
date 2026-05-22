"""
核心模块 - 基础框架和公共组件
三省六部二十四司的抽象基类体系
"""
from .base_province import (
    BaseProvince,
    ProvinceType,
    ProvinceStatus,
    Task,
    CoordinationResult,
    ProvinceStatusReport,
)
from .base_bureau import (
    BaseBureau,
    BureauType,
    AuditBureauType,
    BureauStatus,
    BureauInput,
    BureauOutput,
    ValidationResult,
)
from .base_department import (
    BaseDepartment,
    DepartmentType,
    DepartmentStatus,
    SiContext,
    SiResult,
    DepartmentOutput,
    DispatchTicket,
)
from .base_si import (
    BaseSi,
    HealthStatus,
    SiStatus,
    HealthCheckResult,
    SiOutput,
    SiConfig,
)

__all__ = [
    "BaseProvince",
    "ProvinceType",
    "ProvinceStatus",
    "Task",
    "CoordinationResult",
    "ProvinceStatusReport",
    "BaseBureau",
    "BureauType",
    "AuditBureauType",
    "BureauStatus",
    "BureauInput",
    "BureauOutput",
    "ValidationResult",
    "BaseDepartment",
    "DepartmentType",
    "DepartmentStatus",
    "SiContext",
    "SiResult",
    "DepartmentOutput",
    "DispatchTicket",
    "BaseSi",
    "HealthStatus",
    "SiStatus",
    "HealthCheckResult",
    "SiOutput",
    "SiConfig",
]
