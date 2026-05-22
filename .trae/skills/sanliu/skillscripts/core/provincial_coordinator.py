#!/usr/bin/env python3
"""
省部司协同调用脚本 - 实现三省六部司三级协同调度

功能：
1. 三省协调逻辑：中书省（决策）、门下省（审议）、尚书省（执行）
2. 六部分发逻辑：吏户礼兵刑工六部各司其职
3. 司级细粒度协作：每部四司精细分工
4. 协同调用日志和状态追踪
5. 异步调用支持：支持异步任务执行和回调
6. 状态查询接口：提供实时状态查询能力
7. 进度跟踪功能：细粒度进度追踪和报告
8. 任务优先级队列：支持优先级调度和依赖管理
9. 批量状态查询：高效批量状态检索
10. 错误恢复机制：自动重试和故障恢复
11. 智能任务分发：基于能力匹配和负载均衡的任务分发
12. 执行结果分析：任务执行结果的分析和报告生成
13. 协同效果评估：三省六部协同效果评估和优化建议
14. 流水线管理：白盒化7阶段流水线协调管理
"""

import json
import argparse
import logging
import asyncio
import threading
import time
import queue
import heapq
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Awaitable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
import uuid
from concurrent.futures import ThreadPoolExecutor, Future
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class Province(Enum):
    ZHONGSHUSHENG = "zhongshusheng"
    MENXIASHENG = "menxiasheng"
    SHANGSHUSHENG = "shangshusheng"


class Ministry(Enum):
    LIBU = "libu"
    HUBU = "hubu"
    LIIBU = "liibu"
    BINGBU = "bingbu"
    XINGBU = "xingbu"
    GONGBU = "gongbu"


PROVINCE_CONFIG = {
    Province.ZHONGSHUSHENG: {
        "name": "中书省",
        "role": "决策制定",
        "responsibilities": ["需求分析", "SDD规范定义", "架构决策", "优先级排序"],
        "departments": [],
        "workflow": "decision_making"
    },
    Province.MENXIASHENG: {
        "name": "门下省",
        "role": "审议监督",
        "responsibilities": ["方案评审", "测试覆盖审查", "质量门禁", "合规检查"],
        "departments": [],
        "workflow": "review_supervision"
    },
    Province.SHANGSHUSHENG: {
        "name": "尚书省",
        "role": "执行统筹",
        "responsibilities": ["六部协调", "TDD循环管理", "任务分发", "进度追踪"],
        "departments": ["libu", "hubu", "liibu", "bingbu", "xingbu", "gongbu"],
        "workflow": "execution_coordination"
    }
}

MINISTRY_CONFIG = {
    Ministry.LIBU: {
        "name": "吏部",
        "role": "人员调度",
        "tdd_phase": None,
        "responsibilities": ["Agent分配", "技能匹配", "负载均衡", "绩效评估"],
        "departments": {
            "xuanbosi": {"name": "选补司", "role": "Agent选拔与配置"},
            "kaogongsi": {"name": "考功司", "role": "绩效评估与考核"},
            "jixunsi": {"name": "稽勋司", "role": "任务追踪与记录"},
            "yanfengsi": {"name": "验封司", "role": "权限验证与管理"}
        }
    },
    Ministry.HUBU: {
        "name": "户部",
        "role": "资源管理",
        "tdd_phase": None,
        "responsibilities": ["环境配置", "资源分配", "成本控制", "容量规划"],
        "departments": {
            "jihuasi": {"name": "计化司", "role": "资源规划与预算"},
            "dutousi": {"name": "度头司", "role": "环境度量与监控"},
            "cangkusi": {"name": "仓库司", "role": "依赖仓库管理"},
            "tunbusi": {"name": "屯布司", "role": "资源部署与分发"}
        }
    },
    Ministry.LIIBU: {
        "name": "礼部",
        "role": "规范制定",
        "tdd_phase": None,
        "responsibilities": ["代码审查", "规范制定", "文档管理", "知识沉淀"],
        "departments": {
            "yizhisi": {"name": "仪制司", "role": "编码规范制定"},
            "jiaoguansi": {"name": "教管司", "role": "文档与知识管理"},
            "zhukeji": {"name": "主客司", "role": "接口规范管理"},
            "jingshisi": {"name": "精饰司", "role": "代码美化与重构建议"}
        }
    },
    Ministry.BINGBU: {
        "name": "兵部",
        "role": "测试先行",
        "tdd_phase": "red",
        "responsibilities": ["测试用例设计", "测试先行", "边界测试", "回归测试"],
        "departments": {
            "wuxuansi": {"name": "武选司", "role": "测试策略选择"},
            "zhifangsi": {"name": "职方司", "role": "测试范围规划"},
            "chekesi": {"name": "车客司", "role": "测试执行与驱动"},
            "wubeisi": {"name": "武备司", "role": "测试工具与装备"}
        }
    },
    Ministry.XINGBU: {
        "name": "刑部",
        "role": "持续重构",
        "tdd_phase": "blue",
        "responsibilities": ["代码重构", "质量优化", "问题修复", "安全审计"],
        "departments": {
            "zhifasi": {"name": "执法司", "role": "代码违规检测"},
            "dugusi": {"name": "都古司", "role": "重构规划与执行"},
            "bibusi": {"name": "比部司", "role": "代码对比与分析"},
            "sixingsi": {"name": "司刑司", "role": "安全漏洞修复"}
        }
    },
    Ministry.GONGBU: {
        "name": "工部",
        "role": "代码实现",
        "tdd_phase": "green",
        "responsibilities": ["代码实现", "功能开发", "技术债务", "性能优化"],
        "departments": {
            "yingquansi": {"name": "营全司", "role": "功能规划与设计"},
            "yubusi": {"name": "虞部司", "role": "代码实现执行"},
            "shuibusi": {"name": "水部司", "role": "数据流处理"},
            "tuntianji": {"name": "屯田司", "role": "技术债务管理"}
        }
    }
}


@dataclass
class CoordinationTask:
    task_id: str
    task_type: str
    description: str
    priority: str = "medium"
    status: str = "pending"
    created_at: str = ""
    updated_at: str = ""
    province_path: List[str] = field(default_factory=list)
    ministry_path: List[str] = field(default_factory=list)
    department_path: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    result: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CoordinationLog:
    log_id: str
    task_id: str
    timestamp: str
    level: str
    province: Optional[str] = None
    ministry: Optional[str] = None
    department: Optional[str] = None
    action: str = ""
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


class TaskStatus(Enum):
    PENDING = "pending"
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    DISPATCHED = "dispatched"
    EXECUTING = "executing"


class ProgressPhase(Enum):
    INITIALIZATION = "initialization"
    REQUIREMENT_ANALYSIS = "requirement_analysis"
    SDD_SPECIFICATION = "sdd_specification"
    REVIEW = "review"
    TEST_FIRST = "test_first"
    IMPLEMENTATION = "implementation"
    REFACTORING = "refactoring"
    DEPLOYMENT = "deployment"
    VALIDATION = "validation"
    COMPLETED = "completed"


class TaskPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    BACKGROUND = 4


class RecoveryStrategy(Enum):
    RETRY = "retry"
    ROLLBACK = "rollback"
    ESCALATE = "escalate"
    ABORT = "abort"


@dataclass
class ProgressInfo:
    phase: str
    phase_progress: float
    overall_progress: float
    start_time: str
    estimated_end_time: Optional[str] = None
    current_action: str = ""
    completed_steps: List[str] = field(default_factory=list)
    pending_steps: List[str] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PriorityTask:
    task_id: str
    priority: TaskPriority
    score: float
    dependencies: List[str] = field(default_factory=list)
    created_at: str = ""
    scheduled_at: Optional[str] = None
    started_at: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY
    
    def __lt__(self, other):
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.score > other.score


@dataclass
class RecoveryContext:
    task_id: str
    error_type: str
    error_message: str
    failed_at: str
    retry_count: int
    max_retries: int
    strategy: RecoveryStrategy
    recovery_actions: List[Dict[str, Any]] = field(default_factory=list)
    rollback_data: Optional[Dict[str, Any]] = None


@dataclass
class BatchQueryResult:
    query_id: str
    timestamp: str
    total_tasks: int
    results: List[Dict[str, Any]]
    summary: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


@dataclass
class AsyncTask:
    task_id: str
    coroutine: Optional[Callable] = None
    future: Optional[Future] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    callback: Optional[Callable] = None
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: ProgressInfo = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.progress is None:
            self.progress = ProgressInfo(
                phase=ProgressPhase.INITIALIZATION.value,
                phase_progress=0.0,
                overall_progress=0.0,
                start_time=datetime.now().isoformat()
            )


class StatusQueryResult:
    def __init__(
        self,
        task_id: str,
        status: TaskStatus,
        progress: ProgressInfo,
        province_path: List[str],
        ministry_path: List[str],
        department_path: List[str],
        created_at: str,
        updated_at: str,
        result: Optional[Dict] = None,
        error: Optional[str] = None
    ):
        self.task_id = task_id
        self.status = status
        self.progress = progress
        self.province_path = province_path
        self.ministry_path = ministry_path
        self.department_path = department_path
        self.created_at = created_at
        self.updated_at = updated_at
        self.result = result
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "progress": asdict(self.progress) if self.progress else None,
            "province_path": self.province_path,
            "ministry_path": self.ministry_path,
            "department_path": self.department_path,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "result": self.result,
            "error": self.error
        }


class ProvincialCoordinator:
    """省部司协同调度器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.sanliu_root = Path(__file__).parent.parent
        self.logs_dir = self.sanliu_root / "coordination_logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        self.tasks_file = self.logs_dir / "tasks.json"
        self.logs_file = self.logs_dir / "coordination_logs.json"
        self.status_file = self.logs_dir / "status.json"
        self.progress_file = self.logs_dir / "progress.json"
        
        self.tasks: Dict[str, CoordinationTask] = {}
        self.logs: List[CoordinationLog] = []
        self.status_cache: Dict[str, Any] = {}
        self.async_tasks: Dict[str, AsyncTask] = {}
        self.progress_tracking: Dict[str, ProgressInfo] = {}
        
        self._load_data()
        
        self.province_config = PROVINCE_CONFIG
        self.ministry_config = MINISTRY_CONFIG
        
        self._build_coordination_graph()
        
        self._executor = ThreadPoolExecutor(max_workers=10)
        self._event_loop = None
        self._lock = threading.Lock()
        self._progress_callbacks: Dict[str, List[Callable]] = {}
        self._status_subscribers: Dict[str, List[Callable]] = {}
        
        self._priority_queue: List[PriorityTask] = []
        self._queue_lock = threading.Lock()
        self._dependency_graph: Dict[str, List[str]] = {}
        self._recovery_contexts: Dict[str, RecoveryContext] = {}
        self._rollback_snapshots: Dict[str, Dict[str, Any]] = {}
        self._batch_query_cache: Dict[str, BatchQueryResult] = {}
        self._cache_ttl_seconds: int = 60
        self._last_cache_cleanup: float = time.time()
    
    def __del__(self):
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)
    
    def _load_data(self):
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tasks = {
                        k: CoordinationTask(**v) for k, v in data.get("tasks", {}).items()
                    }
            except Exception as e:
                logger.warning(f"Failed to load tasks: {e}")
        
        if self.logs_file.exists():
            try:
                with open(self.logs_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.logs = [CoordinationLog(**log) for log in data.get("logs", [])]
            except Exception as e:
                logger.warning(f"Failed to load logs: {e}")
    
    def _save_data(self):
        tasks_data = {
            "tasks": {k: asdict(v) for k, v in self.tasks.items()},
            "last_updated": datetime.now().isoformat()
        }
        with open(self.tasks_file, 'w', encoding='utf-8') as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)
        
        logs_data = {
            "logs": [asdict(log) for log in self.logs[-1000:]],
            "last_updated": datetime.now().isoformat()
        }
        with open(self.logs_file, 'w', encoding='utf-8') as f:
            json.dump(logs_data, f, ensure_ascii=False, indent=2)
    
    def _build_coordination_graph(self):
        self.coordination_graph = {
            "provinces": {},
            "ministries": {},
            "departments": {}
        }
        
        for province, config in self.province_config.items():
            self.coordination_graph["provinces"][province.value] = {
                "name": config["name"],
                "role": config["role"],
                "workflow": config["workflow"],
                "ministries": config["departments"]
            }
        
        for ministry, config in self.ministry_config.items():
            self.coordination_graph["ministries"][ministry.value] = {
                "name": config["name"],
                "role": config["role"],
                "tdd_phase": config["tdd_phase"],
                "departments": list(config["departments"].keys())
            }
            
            for dept_id, dept_config in config["departments"].items():
                self.coordination_graph["departments"][dept_id] = {
                    "name": dept_config["name"],
                    "role": dept_config["role"],
                    "ministry": ministry.value,
                    "ministry_name": config["name"]
                }
    
    def _log_action(
        self,
        task_id: str,
        level: str,
        action: str,
        message: str,
        province: Optional[str] = None,
        ministry: Optional[str] = None,
        department: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> CoordinationLog:
        log = CoordinationLog(
            log_id=f"LOG-{uuid.uuid4().hex[:8]}",
            task_id=task_id,
            timestamp=datetime.now().isoformat(),
            level=level,
            province=province,
            ministry=ministry,
            department=department,
            action=action,
            message=message,
            details=details or {}
        )
        
        self.logs.append(log)
        self._save_data()
        
        return log
    
    def create_task(
        self,
        task_type: str,
        description: str,
        priority: str = "medium",
        context: Optional[Dict] = None
    ) -> CoordinationTask:
        task_id = f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        
        task = CoordinationTask(
            task_id=task_id,
            task_type=task_type,
            description=description,
            priority=priority,
            status="created",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            context=context or {}
        )
        
        self.tasks[task_id] = task
        self._save_data()
        
        self._log_action(
            task_id=task_id,
            level="INFO",
            action="task_created",
            message=f"创建任务: {description}",
            details={"task_type": task_type, "priority": priority}
        )
        
        return task
    
    def coordinate_provinces(
        self,
        task: CoordinationTask,
        workflow: str = "standard"
    ) -> Dict[str, Any]:
        """
        三省协调逻辑
        
        工作流程：
        1. 中书省：决策制定、需求分析、SDD规范定义
        2. 门下省：审议监督、方案评审、测试覆盖审查
        3. 尚书省：执行统筹、六部协调、TDD循环管理
        """
        self._log_action(
            task_id=task.task_id,
            level="INFO",
            action="province_coordination_start",
            message="开始三省协调",
            province="zhongshusheng",
            details={"workflow": workflow}
        )
        
        result = {
            "task_id": task.task_id,
            "workflow": workflow,
            "provinces": {},
            "coordination_chain": [],
            "status": "in_progress"
        }
        
        zhongshu_result = self._zhongshusheng_process(task)
        result["provinces"]["zhongshusheng"] = zhongshu_result
        result["coordination_chain"].append({
            "province": "中书省",
            "action": "decision_making",
            "status": zhongshu_result["status"],
            "timestamp": datetime.now().isoformat()
        })
        
        if zhongshu_result["status"] == "approved":
            menxia_result = self._menxiasheng_process(task, zhongshu_result)
            result["provinces"]["menxiasheng"] = menxia_result
            result["coordination_chain"].append({
                "province": "门下省",
                "action": "review_supervision",
                "status": menxia_result["status"],
                "timestamp": datetime.now().isoformat()
            })
            
            if menxia_result["status"] == "approved":
                shangshu_result = self._shangshusheng_process(task, menxia_result)
                result["provinces"]["shangshusheng"] = shangshu_result
                result["coordination_chain"].append({
                    "province": "尚书省",
                    "action": "execution_coordination",
                    "status": shangshu_result["status"],
                    "timestamp": datetime.now().isoformat()
                })
                
                result["status"] = "dispatched"
                result["ministry_dispatch"] = shangshu_result.get("ministry_dispatch", {})
            else:
                result["status"] = "review_rejected"
        else:
            result["status"] = "decision_rejected"
        
        task.province_path = [step["province"] for step in result["coordination_chain"]]
        task.status = result["status"]
        task.updated_at = datetime.now().isoformat()
        self._save_data()
        
        self._log_action(
            task_id=task.task_id,
            level="INFO",
            action="province_coordination_complete",
            message=f"三省协调完成: {result['status']}",
            details=result
        )
        
        return result
    
    def _zhongshusheng_process(self, task: CoordinationTask) -> Dict[str, Any]:
        """中书省处理：决策制定、需求分析、SDD规范定义"""
        self._log_action(
            task_id=task.task_id,
            level="DEBUG",
            action="zhongshusheng_processing",
            message="中书省开始处理",
            province="zhongshusheng"
        )
        
        result = {
            "province": "中书省",
            "status": "approved",
            "decisions": [],
            "sdd_specs": {},
            "requirements": {}
        }
        
        result["requirements"] = {
            "analysis": self._analyze_requirements(task.description),
            "priority": task.priority,
            "type": task.task_type,
            "context": task.context
        }
        
        result["sdd_specs"] = {
            "spec_id": f"SDD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "spec_type": self._determine_spec_type(task.task_type),
            "constraints": self._extract_constraints(task.context),
            "quality_attributes": self._define_quality_attributes(task.task_type)
        }
        
        result["decisions"] = [
            {"decision": "task_classification", "value": task.task_type},
            {"decision": "priority_level", "value": task.priority},
            {"decision": "spec_defined", "value": True}
        ]
        
        return result
    
    def _menxiasheng_process(
        self,
        task: CoordinationTask,
        zhongshu_result: Dict
    ) -> Dict[str, Any]:
        """门下省处理：审议监督、方案评审、测试覆盖审查"""
        self._log_action(
            task_id=task.task_id,
            level="DEBUG",
            action="menxiasheng_processing",
            message="门下省开始审议",
            province="menxiasheng"
        )
        
        result = {
            "province": "门下省",
            "status": "approved",
            "reviews": [],
            "coverage_requirements": {},
            "quality_gates": {}
        }
        
        result["reviews"] = [
            {"aspect": "requirement_clarity", "passed": True, "score": 0.9},
            {"aspect": "spec_completeness", "passed": True, "score": 0.85},
            {"aspect": "feasibility", "passed": True, "score": 0.88}
        ]
        
        result["coverage_requirements"] = {
            "minimum_coverage": 80,
            "critical_paths": self._identify_critical_paths(task),
            "test_types": ["unit", "integration", "e2e"]
        }
        
        result["quality_gates"] = {
            "code_quality": {"threshold": 0.8, "metrics": ["complexity", "duplication"]},
            "security": {"threshold": 0.9, "checks": ["vulnerability_scan", "dependency_audit"]},
            "performance": {"threshold": 0.85, "benchmarks": ["response_time", "throughput"]}
        }
        
        return result
    
    def _shangshusheng_process(
        self,
        task: CoordinationTask,
        menxia_result: Dict
    ) -> Dict[str, Any]:
        """尚书省处理：执行统筹、六部协调、TDD循环管理"""
        self._log_action(
            task_id=task.task_id,
            level="DEBUG",
            action="shangshusheng_processing",
            message="尚书省开始执行统筹",
            province="shangshusheng"
        )
        
        result = {
            "province": "尚书省",
            "status": "dispatched",
            "ministry_dispatch": {},
            "tdd_cycle": {},
            "execution_plan": {},
            "fusion_engine_report": None
        }
        
        ministry_dispatch = self._plan_ministry_dispatch(task, menxia_result)
        result["ministry_dispatch"] = ministry_dispatch
        
        result["tdd_cycle"] = {
            "current_phase": "red",
            "phases": [
                {"phase": "red", "ministry": "bingbu", "status": "pending"},
                {"phase": "green", "ministry": "gongbu", "status": "pending"},
                {"phase": "blue", "ministry": "xingbu", "status": "pending"}
            ]
        }
        
        result["execution_plan"] = {
            "stages": self._create_execution_stages(task, ministry_dispatch),
            "dependencies": self._identify_dependencies(task),
            "estimated_effort": self._estimate_effort(task)
        }
        
        fusion_enabled = task.context.get("enable_sdd_tdd_fusion", False)
        if fusion_enabled:
            fusion_report = self.integrate_with_sdd_tdd_fusion(
                task.context.get("spec_path")
            )
            result["fusion_engine_report"] = fusion_report
            if fusion_report:
                self._log_action(
                    task_id=task.task_id,
                    level="INFO",
                    action="sdd_tdd_fusion_completed",
                    message="SDD-TDD融合循环已完成",
                    details={"report_id": getattr(fusion_report, 'cycle_id', None)}
                )
        
        return result
    
    def integrate_with_sdd_tdd_fusion(self, task_spec_path=None):
        """集成 SDD-TDD 融合循环
        
        Args:
            task_spec_path: 任务规范文件路径 (可选)
            
        Returns:
            融合报告或 None
        """
        try:
            from skillscripts.pipeline.sdd_tdd_fusion_engine import SDDTDDFusionEngine
            from skillscripts.core.path_config_center import get_path_config
            
            engine = SDDTDDFusionEngine()
            
            spec_path = Path(task_spec_path) if task_spec_path else None
            
            if spec_path and spec_path.exists():
                report = engine.execute_cycle(spec_path)
                return report
            
            pcc = get_path_config()
            default_specs_dir = pcc.DOCS_DIR / "specs"
            if default_specs_dir.exists():
                spec_files = list(default_specs_dir.glob("*.md"))
                if spec_files:
                    latest_spec = max(spec_files, key=lambda f: f.stat().st_mtime)
                    report = engine.execute_cycle(latest_spec)
                    return report
            
            return None
            
        except ImportError as e:
            self._log_action(
                task_id="",
                level="WARNING",
                action="sdd_tdd_fusion_import_error",
                message=f"SDD-TDD融合引擎导入失败: {e}"
            )
            return None
        except Exception as e:
            self._log_action(
                task_id="",
                level="ERROR",
                action="sdd_tdd_fusion_error",
                message=f"SDD-TDD融合循环执行失败: {e}"
            )
            return None
    
    def dispatch_to_ministries(
        self,
        task: CoordinationTask,
        dispatch_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        六部分发逻辑
        
        分发策略：
        - 吏部：人员调度、Agent分配
        - 户部：资源管理、环境配置
        - 礼部：规范制定、代码审查
        - 兵部：测试先行、红阶段
        - 刑部：持续重构、蓝阶段
        - 工部：代码实现、绿阶段
        """
        self._log_action(
            task_id=task.task_id,
            level="INFO",
            action="ministry_dispatch_start",
            message="开始六部分发"
        )
        
        result = {
            "task_id": task.task_id,
            "dispatches": {},
            "execution_order": [],
            "status": "dispatched"
        }
        
        execution_order = self._determine_execution_order(task, dispatch_plan)
        result["execution_order"] = execution_order
        
        for ministry_key in execution_order:
            ministry = Ministry(ministry_key)
            ministry_config = self.ministry_config.get(ministry, {})
            
            dispatch_result = self._dispatch_to_ministry(
                task, ministry, ministry_config, dispatch_plan
            )
            result["dispatches"][ministry_key] = dispatch_result
            
            task.ministry_path.append(ministry_key)
            
            self._log_action(
                task_id=task.task_id,
                level="INFO",
                action="ministry_dispatched",
                message=f"任务已分发至{ministry_config.get('name', ministry_key)}",
                ministry=ministry_key,
                details=dispatch_result
            )
        
        task.status = "executing"
        task.updated_at = datetime.now().isoformat()
        self._save_data()
        
        return result
    
    def _dispatch_to_ministry(
        self,
        task: CoordinationTask,
        ministry: Ministry,
        config: Dict,
        dispatch_plan: Dict
    ) -> Dict[str, Any]:
        """分发任务到具体部门"""
        result = {
            "ministry": ministry.value,
            "name": config.get("name", ""),
            "role": config.get("role", ""),
            "tdd_phase": config.get("tdd_phase"),
            "departments": {},
            "status": "pending"
        }
        
        departments = config.get("departments", {})
        for dept_id, dept_config in departments.items():
            dept_result = self._dispatch_to_department(
                task, ministry, dept_id, dept_config, dispatch_plan
            )
            result["departments"][dept_id] = dept_result
        
        result["status"] = "dispatched"
        return result
    
    def _dispatch_to_department(
        self,
        task: CoordinationTask,
        ministry: Ministry,
        dept_id: str,
        dept_config: Dict,
        dispatch_plan: Dict
    ) -> Dict[str, Any]:
        """分发任务到具体司"""
        return {
            "department_id": dept_id,
            "name": dept_config.get("name", ""),
            "role": dept_config.get("role", ""),
            "task_assignment": {
                "type": self._map_task_to_department(task.task_type, dept_id),
                "priority": task.priority,
                "context": task.context
            },
            "status": "assigned"
        }
    
    def coordinate_departments(
        self,
        task: CoordinationTask,
        ministry: Ministry,
        department_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        司级细粒度协作
        
        每个部下属4个司，支持细粒度任务分发和协作
        """
        ministry_config = self.ministry_config.get(ministry, {})
        all_departments = ministry_config.get("departments", {})
        
        target_departments = department_ids or list(all_departments.keys())
        
        self._log_action(
            task_id=task.task_id,
            level="INFO",
            action="department_coordination_start",
            message=f"开始司级协作: {ministry_config.get('name', ministry.value)}",
            ministry=ministry.value
        )
        
        result = {
            "task_id": task.task_id,
            "ministry": ministry.value,
            "ministry_name": ministry_config.get("name", ""),
            "departments": {},
            "coordination_flow": [],
            "status": "coordinating"
        }
        
        for dept_id in target_departments:
            if dept_id not in all_departments:
                continue
            
            dept_config = all_departments[dept_id]
            
            coord_result = self._coordinate_single_department(
                task, ministry, dept_id, dept_config
            )
            result["departments"][dept_id] = coord_result
            
            task.department_path.append(dept_id)
            
            result["coordination_flow"].append({
                "department": dept_config.get("name", dept_id),
                "role": dept_config.get("role", ""),
                "status": coord_result.get("status", "pending"),
                "timestamp": datetime.now().isoformat()
            })
        
        result["status"] = "coordinated"
        task.updated_at = datetime.now().isoformat()
        self._save_data()
        
        self._log_action(
            task_id=task.task_id,
            level="INFO",
            action="department_coordination_complete",
            message="司级协作完成",
            ministry=ministry.value,
            details={"departments": list(result["departments"].keys())}
        )
        
        return result
    
    def _coordinate_single_department(
        self,
        task: CoordinationTask,
        ministry: Ministry,
        dept_id: str,
        dept_config: Dict
    ) -> Dict[str, Any]:
        """单个司的协作处理"""
        return {
            "department_id": dept_id,
            "name": dept_config.get("name", ""),
            "role": dept_config.get("role", ""),
            "actions": self._generate_department_actions(task, dept_id),
            "deliverables": self._define_deliverables(task, dept_id),
            "dependencies": self._identify_department_dependencies(dept_id),
            "status": "ready"
        }
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """查询任务状态"""
        task = self.tasks.get(task_id)
        if not task:
            return {"error": f"Task not found: {task_id}"}
        
        return {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "description": task.description,
            "priority": task.priority,
            "status": task.status,
            "province_path": task.province_path,
            "ministry_path": task.ministry_path,
            "department_path": task.department_path,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "result": task.result
        }
    
    def get_coordination_logs(
        self,
        task_id: Optional[str] = None,
        province: Optional[str] = None,
        ministry: Optional[str] = None,
        department: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取协同调用日志"""
        filtered_logs = self.logs
        
        if task_id:
            filtered_logs = [log for log in filtered_logs if log.task_id == task_id]
        if province:
            filtered_logs = [log for log in filtered_logs if log.province == province]
        if ministry:
            filtered_logs = [log for log in filtered_logs if log.ministry == ministry]
        if department:
            filtered_logs = [log for log in filtered_logs if log.department == department]
        
        return [asdict(log) for log in filtered_logs[-limit:]]
    
    def get_coordination_chain(self, task_id: str) -> Dict[str, Any]:
        """获取任务完整协同链路"""
        task = self.tasks.get(task_id)
        if not task:
            return {"error": f"Task not found: {task_id}"}
        
        task_logs = [log for log in self.logs if log.task_id == task_id]
        
        return {
            "task_id": task_id,
            "chain": {
                "provinces": task.province_path,
                "ministries": task.ministry_path,
                "departments": task.department_path
            },
            "timeline": [
                {
                    "timestamp": log.timestamp,
                    "level": log.level,
                    "province": log.province,
                    "ministry": log.ministry,
                    "department": log.department,
                    "action": log.action,
                    "message": log.message
                }
                for log in sorted(task_logs, key=lambda x: x.timestamp)
            ],
            "current_status": task.status
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取协同统计信息"""
        total_tasks = len(self.tasks)
        status_counts = defaultdict(int)
        province_usage = defaultdict(int)
        ministry_usage = defaultdict(int)
        
        for task in self.tasks.values():
            status_counts[task.status] += 1
            for province in task.province_path:
                province_usage[province] += 1
            for ministry in task.ministry_path:
                ministry_usage[ministry] += 1
        
        return {
            "total_tasks": total_tasks,
            "status_distribution": dict(status_counts),
            "province_usage": dict(province_usage),
            "ministry_usage": dict(ministry_usage),
            "total_logs": len(self.logs)
        }
    
    def _analyze_requirements(self, description: str) -> Dict[str, Any]:
        return {
            "summary": description[:100] if len(description) > 100 else description,
            "keywords": description.lower().split()[:10],
            "complexity": "medium"
        }
    
    def _determine_spec_type(self, task_type: str) -> str:
        spec_map = {
            "feature": "functional_spec",
            "bugfix": "defect_spec",
            "refactor": "improvement_spec",
            "test": "test_spec",
            "docs": "documentation_spec"
        }
        return spec_map.get(task_type, "general_spec")
    
    def _extract_constraints(self, context: Dict) -> List[str]:
        constraints = []
        if context.get("deadline"):
            constraints.append(f"time_constraint: {context['deadline']}")
        if context.get("budget"):
            constraints.append(f"resource_constraint: {context['budget']}")
        if context.get("tech_stack"):
            constraints.append(f"tech_constraint: {context['tech_stack']}")
        return constraints
    
    def _define_quality_attributes(self, task_type: str) -> List[str]:
        base_attributes = ["maintainability", "testability", "readability"]
        if task_type == "feature":
            base_attributes.extend(["scalability", "performance"])
        elif task_type == "bugfix":
            base_attributes.extend(["reliability", "stability"])
        elif task_type == "refactor":
            base_attributes.extend(["extensibility", "modularity"])
        return base_attributes
    
    def _identify_critical_paths(self, task: CoordinationTask) -> List[str]:
        paths = ["main_flow"]
        if "api" in task.description.lower():
            paths.append("api_endpoints")
        if "ui" in task.description.lower():
            paths.append("user_interface")
        return paths
    
    def _plan_ministry_dispatch(
        self,
        task: CoordinationTask,
        menxia_result: Dict
    ) -> Dict[str, Any]:
        dispatch = {
            "libu": {"priority": 1, "agents": [], "resources": {}},
            "hubu": {"priority": 2, "environments": [], "configurations": {}},
            "liibu": {"priority": 3, "standards": [], "reviews": []},
            "bingbu": {"priority": 4, "tests": [], "coverage_target": 80},
            "gongbu": {"priority": 5, "implementations": [], "features": []},
            "xingbu": {"priority": 6, "refactors": [], "optimizations": []}
        }
        return dispatch
    
    def _create_execution_stages(
        self,
        task: CoordinationTask,
        dispatch: Dict
    ) -> List[Dict[str, Any]]:
        return [
            {"stage": "preparation", "ministries": ["libu", "hubu"], "status": "pending"},
            {"stage": "planning", "ministries": ["liibu"], "status": "pending"},
            {"stage": "tdd_red", "ministries": ["bingbu"], "status": "pending"},
            {"stage": "tdd_green", "ministries": ["gongbu"], "status": "pending"},
            {"stage": "tdd_blue", "ministries": ["xingbu"], "status": "pending"}
        ]
    
    def _identify_dependencies(self, task: CoordinationTask) -> List[Dict[str, str]]:
        return [
            {"from": "libu", "to": "gongbu", "type": "resource"},
            {"from": "hubu", "to": "gongbu", "type": "environment"},
            {"from": "bingbu", "to": "gongbu", "type": "test"},
            {"from": "gongbu", "to": "xingbu", "type": "code"}
        ]
    
    def _estimate_effort(self, task: CoordinationTask) -> Dict[str, float]:
        base_effort = {
            "feature": 8.0,
            "bugfix": 4.0,
            "refactor": 6.0,
            "test": 3.0,
            "docs": 2.0
        }
        return {
            "estimated_hours": base_effort.get(task.task_type, 5.0),
            "confidence": 0.8
        }
    
    def _determine_execution_order(
        self,
        task: CoordinationTask,
        dispatch_plan: Dict
    ) -> List[str]:
        order = ["libu", "hubu", "liibu"]
        
        if task.task_type in ["feature", "bugfix"]:
            order.extend(["bingbu", "gongbu", "xingbu"])
        elif task.task_type == "refactor":
            order.extend(["xingbu", "gongbu", "bingbu"])
        elif task.task_type == "test":
            order.extend(["bingbu"])
        else:
            order.extend(["gongbu", "bingbu", "xingbu"])
        
        return order
    
    def _map_task_to_department(self, task_type: str, dept_id: str) -> str:
        return f"{task_type}_{dept_id}_task"
    
    def _generate_department_actions(
        self,
        task: CoordinationTask,
        dept_id: str
    ) -> List[str]:
        return [
            f"analyze_{task.task_type}_requirements",
            f"prepare_{dept_id}_resources",
            f"execute_{task.task_type}_task"
        ]
    
    def _define_deliverables(
        self,
        task: CoordinationTask,
        dept_id: str
    ) -> List[str]:
        return [
            f"{dept_id}_output_document",
            f"{dept_id}_quality_report"
        ]
    
    def _identify_department_dependencies(self, dept_id: str) -> List[str]:
        dept_deps = {
            "xuanbosi": [],
            "kaogongsi": ["xuanbosi"],
            "jixunsi": ["xuanbosi"],
            "yanfengsi": ["xuanbosi"],
            "jihuasi": [],
            "dutousi": ["jihuasi"],
            "cangkusi": ["jihuasi"],
            "tunbusi": ["dutousi", "cangkusi"]
        }
        return dept_deps.get(dept_id, [])
    
    def create_async_task(
        self,
        task_type: str,
        description: str,
        priority: str = "medium",
        context: Optional[Dict] = None,
        callback: Optional[Callable] = None
    ) -> AsyncTask:
        task = self.create_task(task_type, description, priority, context)
        
        async_task = AsyncTask(
            task_id=task.task_id,
            callback=callback,
            status=TaskStatus.CREATED
        )
        
        with self._lock:
            self.async_tasks[task.task_id] = async_task
            self.progress_tracking[task.task_id] = async_task.progress
        
        self._log_action(
            task_id=task.task_id,
            level="INFO",
            action="async_task_created",
            message=f"创建异步任务: {description}"
        )
        
        return async_task
    
    def execute_async(
        self,
        task_id: str,
        coordination_func: Callable,
        *args,
        **kwargs
    ) -> Future:
        async_task = self.async_tasks.get(task_id)
        if not async_task:
            raise ValueError(f"Async task not found: {task_id}")
        
        def wrapper():
            try:
                async_task.status = TaskStatus.RUNNING
                async_task.started_at = datetime.now().isoformat()
                self._update_progress(task_id, ProgressPhase.INITIALIZATION, 0.1, "开始执行")
                
                result = coordination_func(*args, **kwargs)
                
                async_task.result = result
                async_task.status = TaskStatus.COMPLETED
                async_task.completed_at = datetime.now().isoformat()
                self._update_progress(task_id, ProgressPhase.COMPLETED, 1.0, "执行完成")
                
                if async_task.callback:
                    async_task.callback(task_id, result, None)
                
                self._notify_status_subscribers(task_id, async_task.status)
                
                return result
            except Exception as e:
                async_task.error = str(e)
                async_task.status = TaskStatus.FAILED
                async_task.completed_at = datetime.now().isoformat()
                self._update_progress(
                    task_id, 
                    ProgressPhase.COMPLETED, 
                    0.0, 
                    f"执行失败: {str(e)}",
                    error={"message": str(e), "type": type(e).__name__}
                )
                
                if async_task.callback:
                    async_task.callback(task_id, None, str(e))
                
                self._notify_status_subscribers(task_id, async_task.status)
                raise
        
        async_task.future = self._executor.submit(wrapper)
        return async_task.future
    
    def execute_async_coordination(
        self,
        task_id: str,
        workflow: str = "standard",
        callback: Optional[Callable] = None
    ) -> Future:
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        async_task = self.create_async_task(
            task.task_type,
            task.description,
            task.priority,
            task.context,
            callback
        )
        async_task.task_id = task_id
        
        return self.execute_async(
            task_id,
            self.coordinate_provinces,
            task,
            workflow
        )
    
    def get_async_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        async_task = self.async_tasks.get(task_id)
        if not async_task:
            return None
        
        return {
            "task_id": task_id,
            "status": async_task.status.value,
            "created_at": async_task.created_at,
            "started_at": async_task.started_at,
            "completed_at": async_task.completed_at,
            "progress": asdict(async_task.progress) if async_task.progress else None,
            "result": async_task.result,
            "error": async_task.error,
            "is_running": async_task.status == TaskStatus.RUNNING,
            "is_completed": async_task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
        }
    
    def cancel_async_task(self, task_id: str) -> bool:
        async_task = self.async_tasks.get(task_id)
        if not async_task:
            return False
        
        if async_task.future and async_task.future.running():
            async_task.future.cancel()
            async_task.status = TaskStatus.CANCELLED
            async_task.completed_at = datetime.now().isoformat()
            self._update_progress(task_id, ProgressPhase.COMPLETED, 0.0, "任务已取消")
            self._notify_status_subscribers(task_id, TaskStatus.CANCELLED)
            return True
        
        return False
    
    def _update_progress(
        self,
        task_id: str,
        phase: ProgressPhase,
        progress: float,
        action: str = "",
        error: Optional[Dict] = None
    ):
        with self._lock:
            progress_info = self.progress_tracking.get(task_id)
            if not progress_info:
                progress_info = ProgressInfo(
                    phase=phase.value,
                    phase_progress=progress,
                    overall_progress=self._calculate_overall_progress(phase, progress),
                    start_time=datetime.now().isoformat(),
                    current_action=action
                )
                self.progress_tracking[task_id] = progress_info
            else:
                progress_info.phase = phase.value
                progress_info.phase_progress = progress
                progress_info.overall_progress = self._calculate_overall_progress(phase, progress)
                progress_info.current_action = action
                if action:
                    progress_info.completed_steps.append(action)
                
                if error:
                    progress_info.errors.append(error)
        
        self._notify_progress_callbacks(task_id, progress_info)
        self._save_progress()
    
    def _calculate_overall_progress(self, phase: ProgressPhase, phase_progress: float) -> float:
        phase_weights = {
            ProgressPhase.INITIALIZATION: 0.05,
            ProgressPhase.REQUIREMENT_ANALYSIS: 0.15,
            ProgressPhase.SDD_SPECIFICATION: 0.15,
            ProgressPhase.REVIEW: 0.10,
            ProgressPhase.TEST_FIRST: 0.15,
            ProgressPhase.IMPLEMENTATION: 0.20,
            ProgressPhase.REFACTORING: 0.10,
            ProgressPhase.DEPLOYMENT: 0.05,
            ProgressPhase.VALIDATION: 0.03,
            ProgressPhase.COMPLETED: 0.02
        }
        
        weight = phase_weights.get(phase, 0.1)
        completed_weight = sum(
            phase_weights.get(p, 0) 
            for p in ProgressPhase 
            if list(ProgressPhase).index(p) < list(ProgressPhase).index(phase)
        )
        
        return completed_weight + (weight * phase_progress)
    
    def _save_progress(self):
        progress_data = {
            task_id: asdict(progress) 
            for task_id, progress in self.progress_tracking.items()
        }
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
    
    def get_task_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        progress = self.progress_tracking.get(task_id)
        if not progress:
            return None
        
        return asdict(progress)
    
    def get_detailed_status(self, task_id: str) -> StatusQueryResult:
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        async_task = self.async_tasks.get(task_id)
        progress = self.progress_tracking.get(task_id)
        
        status = TaskStatus.PENDING
        if async_task:
            status = async_task.status
        elif task.status == "created":
            status = TaskStatus.CREATED
        elif task.status == "executing":
            status = TaskStatus.EXECUTING
        elif task.status == "dispatched":
            status = TaskStatus.DISPATCHED
        elif task.status == "completed":
            status = TaskStatus.COMPLETED
        
        if not progress:
            progress = ProgressInfo(
                phase=ProgressPhase.INITIALIZATION.value,
                phase_progress=0.0,
                overall_progress=0.0,
                start_time=task.created_at
            )
        
        return StatusQueryResult(
            task_id=task_id,
            status=status,
            progress=progress,
            province_path=task.province_path,
            ministry_path=task.ministry_path,
            department_path=task.department_path,
            created_at=task.created_at,
            updated_at=task.updated_at,
            result=task.result,
            error=async_task.error if async_task else None
        )
    
    def query_status_batch(
        self, 
        task_ids: Optional[List[str]] = None,
        status_filter: Optional[List[TaskStatus]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        results = []
        
        target_tasks = task_ids if task_ids else list(self.tasks.keys())
        
        for task_id in target_tasks[:limit]:
            try:
                status_result = self.get_detailed_status(task_id)
                
                if status_filter and status_result.status not in status_filter:
                    continue
                
                results.append(status_result.to_dict())
            except ValueError:
                continue
        
        return results
    
    def subscribe_status_changes(
        self,
        task_id: str,
        callback: Callable[[str, TaskStatus], None]
    ):
        with self._lock:
            if task_id not in self._status_subscribers:
                self._status_subscribers[task_id] = []
            self._status_subscribers[task_id].append(callback)
    
    def subscribe_progress_updates(
        self,
        task_id: str,
        callback: Callable[[str, ProgressInfo], None]
    ):
        with self._lock:
            if task_id not in self._progress_callbacks:
                self._progress_callbacks[task_id] = []
            self._progress_callbacks[task_id].append(callback)
    
    def _notify_status_subscribers(self, task_id: str, status: TaskStatus):
        callbacks = self._status_subscribers.get(task_id, [])
        for callback in callbacks:
            try:
                callback(task_id, status)
            except Exception as e:
                logger.warning(f"Status callback failed: {e}")
    
    def _notify_progress_callbacks(self, task_id: str, progress: ProgressInfo):
        callbacks = self._progress_callbacks.get(task_id, [])
        for callback in callbacks:
            try:
                callback(task_id, progress)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")
    
    def get_progress_summary(self, task_id: str) -> Dict[str, Any]:
        progress = self.progress_tracking.get(task_id)
        task = self.tasks.get(task_id)
        
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        if not progress:
            return {
                "task_id": task_id,
                "overall_progress": 0.0,
                "current_phase": "not_started",
                "elapsed_time_seconds": 0,
                "estimated_remaining_seconds": None
            }
        
        start_time = datetime.fromisoformat(progress.start_time)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        estimated_remaining = None
        if progress.overall_progress > 0:
            total_estimated = elapsed / progress.overall_progress
            estimated_remaining = total_estimated - elapsed
        
        return {
            "task_id": task_id,
            "overall_progress": progress.overall_progress,
            "current_phase": progress.phase,
            "phase_progress": progress.phase_progress,
            "current_action": progress.current_action,
            "completed_steps": len(progress.completed_steps),
            "pending_steps": len(progress.pending_steps),
            "error_count": len(progress.errors),
            "elapsed_time_seconds": elapsed,
            "estimated_remaining_seconds": estimated_remaining,
            "metrics": progress.metrics
        }
    
    def get_execution_timeline(self, task_id: str) -> List[Dict[str, Any]]:
        task_logs = [log for log in self.logs if log.task_id == task_id]
        task_logs.sort(key=lambda x: x.timestamp)
        
        timeline = []
        for log in task_logs:
            timeline.append({
                "timestamp": log.timestamp,
                "level": log.level,
                "province": log.province,
                "ministry": log.ministry,
                "department": log.department,
                "action": log.action,
                "message": log.message,
                "details": log.details
            })
        
        return timeline
    
    def add_priority_task(
        self,
        task_id: str,
        priority: TaskPriority,
        score: float = 0.0,
        dependencies: Optional[List[str]] = None,
        max_retries: int = 3,
        recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY
    ) -> PriorityTask:
        priority_task = PriorityTask(
            task_id=task_id,
            priority=priority,
            score=score,
            dependencies=dependencies or [],
            created_at=datetime.now().isoformat(),
            max_retries=max_retries,
            recovery_strategy=recovery_strategy
        )
        
        with self._queue_lock:
            heapq.heappush(self._priority_queue, priority_task)
            self._dependency_graph[task_id] = priority_task.dependencies
        
        self._log_action(
            task_id=task_id,
            level="INFO",
            action="priority_task_added",
            message=f"添加优先级任务: {priority.name}, 分数: {score}"
        )
        
        return priority_task
    
    def get_next_priority_task(self) -> Optional[PriorityTask]:
        with self._queue_lock:
            while self._priority_queue:
                task = heapq.heappop(self._priority_queue)
                
                dependencies_met = all(
                    dep_id not in self._dependency_graph or 
                    self.tasks.get(dep_id, CoordinationTask("", "", "", "", "", [], [], [])).status == "completed"
                    for dep_id in task.dependencies
                )
                
                if dependencies_met:
                    task.scheduled_at = datetime.now().isoformat()
                    return task
                
                heapq.heappush(self._priority_queue, task)
                break
        
        return None
    
    def create_rollback_snapshot(self, task_id: str) -> Dict[str, Any]:
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        snapshot = {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "task_state": asdict(task),
            "province_path": task.province_path.copy(),
            "ministry_path": task.ministry_path.copy(),
            "department_path": task.department_path.copy(),
            "result": task.result
        }
        
        with self._lock:
            self._rollback_snapshots[task_id] = snapshot
        
        self._log_action(
            task_id=task_id,
            level="INFO",
            action="rollback_snapshot_created",
            message="创建回滚快照"
        )
        
        return snapshot
    
    def rollback_task(self, task_id: str) -> bool:
        snapshot = self._rollback_snapshots.get(task_id)
        if not snapshot:
            self._log_action(
                task_id=task_id,
                level="ERROR",
                action="rollback_failed",
                message="未找到回滚快照"
            )
            return False
        
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        task.province_path = snapshot["province_path"]
        task.ministry_path = snapshot["ministry_path"]
        task.department_path = snapshot["department_path"]
        task.result = snapshot["result"]
        task.status = "rolled_back"
        task.updated_at = datetime.now().isoformat()
        
        self._save_data()
        
        self._log_action(
            task_id=task_id,
            level="INFO",
            action="rollback_completed",
            message="任务已回滚到快照状态"
        )
        
        return True
    
    def handle_task_failure(
        self,
        task_id: str,
        error_type: str,
        error_message: str,
        recovery_strategy: Optional[RecoveryStrategy] = None
    ) -> RecoveryContext:
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        priority_task = next(
            (pt for pt in self._priority_queue if pt.task_id == task_id),
            None
        )
        
        strategy = recovery_strategy or (priority_task.recovery_strategy if priority_task else RecoveryStrategy.RETRY)
        max_retries = priority_task.max_retries if priority_task else 3
        retry_count = priority_task.retry_count if priority_task else 0
        
        recovery_context = RecoveryContext(
            task_id=task_id,
            error_type=error_type,
            error_message=error_message,
            failed_at=datetime.now().isoformat(),
            retry_count=retry_count,
            max_retries=max_retries,
            strategy=strategy,
            recovery_actions=[]
        )
        
        if strategy == RecoveryStrategy.RETRY and retry_count < max_retries:
            recovery_context.recovery_actions.append({
                "action": "retry",
                "timestamp": datetime.now().isoformat(),
                "attempt": retry_count + 1
            })
            if priority_task:
                priority_task.retry_count += 1
                with self._queue_lock:
                    heapq.heappush(self._priority_queue, priority_task)
        
        elif strategy == RecoveryStrategy.ROLLBACK:
            self.rollback_task(task_id)
            recovery_context.recovery_actions.append({
                "action": "rollback",
                "timestamp": datetime.now().isoformat()
            })
        
        elif strategy == RecoveryStrategy.ESCALATE:
            recovery_context.recovery_actions.append({
                "action": "escalate",
                "timestamp": datetime.now().isoformat(),
                "reason": "Max retries exceeded or manual escalation required"
            })
        
        elif strategy == RecoveryStrategy.ABORT:
            task.status = "aborted"
            task.updated_at = datetime.now().isoformat()
            self._save_data()
            recovery_context.recovery_actions.append({
                "action": "abort",
                "timestamp": datetime.now().isoformat()
            })
        
        with self._lock:
            self._recovery_contexts[task_id] = recovery_context
        
        self._log_action(
            task_id=task_id,
            level="ERROR",
            action="task_failure_handled",
            message=f"任务失败处理: {strategy.value}",
            details={
                "error_type": error_type,
                "error_message": error_message,
                "recovery_actions": recovery_context.recovery_actions
            }
        )
        
        return recovery_context
    
    def get_recovery_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        context = self._recovery_contexts.get(task_id)
        if not context:
            return None
        return asdict(context)
    
    def batch_query_status(
        self,
        task_ids: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        include_progress: bool = True,
        include_logs: bool = False
    ) -> BatchQueryResult:
        query_id = f"BQ-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        target_ids = task_ids if task_ids else list(self.tasks.keys())
        results = []
        errors = []
        summary = {
            "total": len(target_ids),
            "found": 0,
            "not_found": 0,
            "by_status": defaultdict(int),
            "by_priority": defaultdict(int)
        }
        
        for task_id in target_ids:
            task = self.tasks.get(task_id)
            if not task:
                summary["not_found"] += 1
                errors.append(f"Task not found: {task_id}")
                continue
            
            if filters:
                if filters.get("status") and task.status != filters["status"]:
                    continue
                if filters.get("priority") and task.priority != filters["priority"]:
                    continue
                if filters.get("task_type") and task.task_type != filters["task_type"]:
                    continue
            
            result = {
                "task_id": task_id,
                "task_type": task.task_type,
                "description": task.description[:100] if len(task.description) > 100 else task.description,
                "priority": task.priority,
                "status": task.status,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
                "province_path": task.province_path,
                "ministry_path": task.ministry_path
            }
            
            if include_progress:
                progress = self.progress_tracking.get(task_id)
                result["progress"] = asdict(progress) if progress else None
            
            if include_logs:
                task_logs = [log for log in self.logs if log.task_id == task_id]
                result["log_count"] = len(task_logs)
            
            results.append(result)
            summary["found"] += 1
            summary["by_status"][task.status] += 1
            summary["by_priority"][task.priority] += 1
        
        summary["by_status"] = dict(summary["by_status"])
        summary["by_priority"] = dict(summary["by_priority"])
        
        batch_result = BatchQueryResult(
            query_id=query_id,
            timestamp=datetime.now().isoformat(),
            total_tasks=len(results),
            results=results,
            summary=summary,
            errors=errors
        )
        
        with self._lock:
            self._batch_query_cache[query_id] = batch_result
            self._cleanup_cache()
        
        return batch_result
    
    def _cleanup_cache(self):
        current_time = time.time()
        if current_time - self._last_cache_cleanup > self._cache_ttl_seconds:
            expired_keys = [
                key for key, value in self._batch_query_cache.items()
                if current_time - datetime.fromisoformat(value.timestamp).timestamp() > self._cache_ttl_seconds
            ]
            for key in expired_keys:
                del self._batch_query_cache[key]
            self._last_cache_cleanup = current_time
    
    def get_cached_query(self, query_id: str) -> Optional[BatchQueryResult]:
        return self._batch_query_cache.get(query_id)
    
    def get_queue_statistics(self) -> Dict[str, Any]:
        with self._queue_lock:
            queue_size = len(self._priority_queue)
            by_priority = defaultdict(int)
            for task in self._priority_queue:
                by_priority[task.priority.name] += 1
            
            pending_dependencies = sum(
                1 for task in self._priority_queue
                if any(dep_id in self._dependency_graph for dep_id in task.dependencies)
            )
        
        return {
            "queue_size": queue_size,
            "by_priority": dict(by_priority),
            "pending_dependencies": pending_dependencies,
            "total_recovery_contexts": len(self._recovery_contexts),
            "total_rollback_snapshots": len(self._rollback_snapshots)
        }
    
    def execute_with_priority(
        self,
        coordination_func: Callable,
        *args,
        **kwargs
    ) -> Future:
        priority_task = self.get_next_priority_task()
        if not priority_task:
            raise ValueError("No available priority task in queue")
        
        self.create_rollback_snapshot(priority_task.task_id)
        
        return self.execute_async(
            priority_task.task_id,
            coordination_func,
            *args,
            **kwargs
        )


class CapabilityProfile:
    def __init__(
        self,
        entity_id: str,
        entity_type: str,
        capabilities: Dict[str, float],
        max_concurrent_tasks: int = 5,
        specializations: Optional[List[str]] = None
    ):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.capabilities = capabilities
        self.max_concurrent_tasks = max_concurrent_tasks
        self.specializations = specializations or []
        self.current_load = 0
        self.task_history: List[str] = []
        self.performance_metrics: Dict[str, float] = {
            "success_rate": 1.0,
            "avg_completion_time": 0.0,
            "quality_score": 1.0
        }
    
    def get_capability_score(self, capability: str) -> float:
        return self.capabilities.get(capability, 0.0)
    
    def get_load_factor(self) -> float:
        return self.current_load / self.max_concurrent_tasks if self.max_concurrent_tasks > 0 else 1.0
    
    def is_available(self) -> bool:
        return self.current_load < self.max_concurrent_tasks
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "capabilities": self.capabilities,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "specializations": self.specializations,
            "current_load": self.current_load,
            "performance_metrics": self.performance_metrics
        }


class TaskRequirement:
    def __init__(
        self,
        task_id: str,
        required_capabilities: Dict[str, float],
        preferred_specializations: Optional[List[str]] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        estimated_complexity: float = 1.0,
        dependencies: Optional[List[str]] = None
    ):
        self.task_id = task_id
        self.required_capabilities = required_capabilities
        self.preferred_specializations = preferred_specializations or []
        self.priority = priority
        self.estimated_complexity = estimated_complexity
        self.dependencies = dependencies or []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "required_capabilities": self.required_capabilities,
            "preferred_specializations": self.preferred_specializations,
            "priority": self.priority.value,
            "estimated_complexity": self.estimated_complexity,
            "dependencies": self.dependencies
        }


@dataclass
class DispatchDecision:
    task_id: str
    assigned_entity: str
    entity_type: str
    capability_match_score: float
    load_balance_score: float
    overall_score: float
    reasoning: List[str] = field(default_factory=list)
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class SmartDispatcher:
    def __init__(self):
        self.capability_registry: Dict[str, CapabilityProfile] = {}
        self.dispatch_history: List[DispatchDecision] = []
        self._lock = threading.Lock()
        
        self._initialize_default_capabilities()
    
    def _initialize_default_capabilities(self):
        ministry_capabilities = {
            "libu": {
                "agent_allocation": 0.95,
                "skill_matching": 0.90,
                "load_balancing": 0.85,
                "performance_evaluation": 0.88,
                "resource_planning": 0.80
            },
            "hubu": {
                "environment_config": 0.92,
                "resource_allocation": 0.90,
                "cost_control": 0.85,
                "capacity_planning": 0.88,
                "dependency_management": 0.82
            },
            "liibu": {
                "code_review": 0.95,
                "standard_definition": 0.92,
                "documentation": 0.88,
                "knowledge_management": 0.85,
                "compliance_check": 0.90
            },
            "bingbu": {
                "test_design": 0.95,
                "test_first": 0.92,
                "boundary_testing": 0.88,
                "regression_testing": 0.85,
                "security_testing": 0.80
            },
            "xingbu": {
                "code_refactoring": 0.95,
                "quality_optimization": 0.92,
                "bug_fixing": 0.90,
                "security_audit": 0.85,
                "performance_optimization": 0.88
            },
            "gongbu": {
                "code_implementation": 0.95,
                "feature_development": 0.92,
                "technical_debt": 0.80,
                "performance_optimization": 0.85,
                "deployment": 0.88
            }
        }
        
        for ministry_id, capabilities in ministry_capabilities.items():
            profile = CapabilityProfile(
                entity_id=ministry_id,
                entity_type="ministry",
                capabilities=capabilities,
                max_concurrent_tasks=10,
                specializations=[ministry_id]
            )
            self.capability_registry[ministry_id] = profile
        
        province_capabilities = {
            "zhongshusheng": {
                "decision_making": 0.95,
                "requirement_analysis": 0.92,
                "sdd_specification": 0.90,
                "architecture_decision": 0.88,
                "priority_ranking": 0.85
            },
            "menxiasheng": {
                "review_supervision": 0.95,
                "plan_review": 0.92,
                "test_coverage_review": 0.90,
                "quality_gate": 0.88,
                "compliance_check": 0.85
            },
            "shangshusheng": {
                "execution_coordination": 0.95,
                "ministry_coordination": 0.92,
                "tdd_management": 0.90,
                "task_dispatch": 0.88,
                "progress_tracking": 0.85
            }
        }
        
        for province_id, capabilities in province_capabilities.items():
            profile = CapabilityProfile(
                entity_id=province_id,
                entity_type="province",
                capabilities=capabilities,
                max_concurrent_tasks=20,
                specializations=[province_id]
            )
            self.capability_registry[province_id] = profile
    
    def register_capability(self, profile: CapabilityProfile):
        with self._lock:
            self.capability_registry[profile.entity_id] = profile
    
    def calculate_capability_match(
        self,
        profile: CapabilityProfile,
        requirement: TaskRequirement
    ) -> float:
        if not requirement.required_capabilities:
            return 1.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for capability, required_level in requirement.required_capabilities.items():
            available_level = profile.get_capability_score(capability)
            if available_level >= required_level:
                score = 1.0 - (available_level - required_level) * 0.1
            else:
                score = available_level / required_level * 0.8
            
            weight = required_level
            total_score += score * weight
            total_weight += weight
        
        base_score = total_score / total_weight if total_weight > 0 else 0.0
        
        specialization_bonus = 0.0
        for spec in requirement.preferred_specializations:
            if spec in profile.specializations:
                specialization_bonus += 0.05
        
        return min(1.0, base_score + specialization_bonus)
    
    def calculate_load_balance_score(self, profile: CapabilityProfile) -> float:
        load_factor = profile.get_load_factor()
        return 1.0 - load_factor
    
    def calculate_overall_score(
        self,
        profile: CapabilityProfile,
        requirement: TaskRequirement,
        capability_weight: float = 0.6,
        load_weight: float = 0.4
    ) -> float:
        capability_score = self.calculate_capability_match(profile, requirement)
        load_score = self.calculate_load_balance_score(profile)
        
        performance_factor = (
            profile.performance_metrics.get("success_rate", 1.0) * 0.5 +
            profile.performance_metrics.get("quality_score", 1.0) * 0.3 +
            (1.0 - min(1.0, profile.performance_metrics.get("avg_completion_time", 0.0) / 3600)) * 0.2
        )
        
        return (
            capability_score * capability_weight +
            load_score * load_weight
        ) * performance_factor
    
    def find_best_match(
        self,
        requirement: TaskRequirement,
        entity_type: Optional[str] = None
    ) -> DispatchDecision:
        candidates = []
        reasoning = []
        
        for entity_id, profile in self.capability_registry.items():
            if entity_type and profile.entity_type != entity_type:
                continue
            
            if not profile.is_available():
                reasoning.append(f"{entity_id} 不可用（负载已满）")
                continue
            
            capability_match = self.calculate_capability_match(profile, requirement)
            load_balance = self.calculate_load_balance_score(profile)
            overall_score = self.calculate_overall_score(profile, requirement)
            
            candidates.append({
                "entity_id": entity_id,
                "profile": profile,
                "capability_match": capability_match,
                "load_balance": load_balance,
                "overall_score": overall_score
            })
            
            reasoning.append(
                f"{entity_id}: 能力匹配={capability_match:.2f}, "
                f"负载均衡={load_balance:.2f}, 综合得分={overall_score:.2f}"
            )
        
        if not candidates:
            return DispatchDecision(
                task_id=requirement.task_id,
                assigned_entity="",
                entity_type=entity_type or "unknown",
                capability_match_score=0.0,
                load_balance_score=0.0,
                overall_score=0.0,
                reasoning=["无可用候选实体"],
                alternatives=[]
            )
        
        candidates.sort(key=lambda x: x["overall_score"], reverse=True)
        
        best = candidates[0]
        alternatives = [
            {
                "entity_id": c["entity_id"],
                "overall_score": c["overall_score"]
            }
            for c in candidates[1:4]
        ]
        
        decision = DispatchDecision(
            task_id=requirement.task_id,
            assigned_entity=best["entity_id"],
            entity_type=best["profile"].entity_type,
            capability_match_score=best["capability_match"],
            load_balance_score=best["load_balance"],
            overall_score=best["overall_score"],
            reasoning=reasoning,
            alternatives=alternatives
        )
        
        with self._lock:
            self.dispatch_history.append(decision)
            if best["entity_id"] in self.capability_registry:
                self.capability_registry[best["entity_id"]].current_load += 1
                self.capability_registry[best["entity_id"]].task_history.append(requirement.task_id)
        
        return decision
    
    def release_load(self, entity_id: str, task_id: str, success: bool = True, completion_time: float = 0.0):
        with self._lock:
            if entity_id in self.capability_registry:
                profile = self.capability_registry[entity_id]
                if profile.current_load > 0:
                    profile.current_load -= 1
                
                if task_id in profile.task_history:
                    profile.task_history.remove(task_id)
                
                current_success_rate = profile.performance_metrics["success_rate"]
                alpha = 0.1
                profile.performance_metrics["success_rate"] = (
                    current_success_rate * (1 - alpha) + (1.0 if success else 0.0) * alpha
                )
                
                if completion_time > 0:
                    current_avg = profile.performance_metrics["avg_completion_time"]
                    profile.performance_metrics["avg_completion_time"] = (
                        current_avg * 0.8 + completion_time * 0.2
                    )
    
    def get_dispatcher_statistics(self) -> Dict[str, Any]:
        with self._lock:
            entity_stats = {}
            for entity_id, profile in self.capability_registry.items():
                entity_stats[entity_id] = {
                    "current_load": profile.current_load,
                    "max_concurrent_tasks": profile.max_concurrent_tasks,
                    "load_factor": profile.get_load_factor(),
                    "performance_metrics": profile.performance_metrics,
                    "task_history_count": len(profile.task_history)
                }
            
            return {
                "total_entities": len(self.capability_registry),
                "total_dispatches": len(self.dispatch_history),
                "entity_statistics": entity_stats,
                "recent_dispatches": [
                    {
                        "task_id": d.task_id,
                        "assigned_entity": d.assigned_entity,
                        "overall_score": d.overall_score,
                        "timestamp": d.timestamp
                    }
                    for d in self.dispatch_history[-10:]
                ]
            }


@dataclass
class ExecutionResult:
    task_id: str
    status: str
    start_time: str
    end_time: str
    duration_seconds: float
    province_path: List[str] = field(default_factory=list)
    ministry_path: List[str] = field(default_factory=list)
    department_path: List[str] = field(default_factory=list)
    outputs: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    quality_score: float = 0.0
    efficiency_score: float = 0.0


@dataclass
class AnalysisReport:
    report_id: str
    task_id: str
    generated_at: str
    execution_summary: Dict[str, Any] = field(default_factory=dict)
    performance_analysis: Dict[str, Any] = field(default_factory=dict)
    quality_analysis: Dict[str, Any] = field(default_factory=dict)
    coordination_analysis: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    issues_identified: List[Dict[str, Any]] = field(default_factory=list)
    best_practices: List[str] = field(default_factory=list)


class ExecutionAnalyzer:
    def __init__(self):
        self.results: Dict[str, ExecutionResult] = {}
        self.reports: Dict[str, AnalysisReport] = {}
        self._lock = threading.Lock()
    
    def record_result(self, result: ExecutionResult):
        with self._lock:
            self.results[result.task_id] = result
    
    def analyze_execution(self, task_id: str) -> AnalysisReport:
        result = self.results.get(task_id)
        if not result:
            raise ValueError(f"No execution result found for task: {task_id}")
        
        report_id = f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        
        execution_summary = self._analyze_execution_summary(result)
        performance_analysis = self._analyze_performance(result)
        quality_analysis = self._analyze_quality(result)
        coordination_analysis = self._analyze_coordination(result)
        recommendations = self._generate_recommendations(
            result, execution_summary, performance_analysis, quality_analysis
        )
        issues_identified = self._identify_issues(result)
        best_practices = self._extract_best_practices(result)
        
        report = AnalysisReport(
            report_id=report_id,
            task_id=task_id,
            generated_at=datetime.now().isoformat(),
            execution_summary=execution_summary,
            performance_analysis=performance_analysis,
            quality_analysis=quality_analysis,
            coordination_analysis=coordination_analysis,
            recommendations=recommendations,
            issues_identified=issues_identified,
            best_practices=best_practices
        )
        
        with self._lock:
            self.reports[report_id] = report
        
        return report
    
    def _analyze_execution_summary(self, result: ExecutionResult) -> Dict[str, Any]:
        return {
            "status": result.status,
            "duration_seconds": result.duration_seconds,
            "province_count": len(result.province_path),
            "ministry_count": len(result.ministry_path),
            "department_count": len(result.department_path),
            "output_count": len(result.outputs),
            "error_count": len(result.errors),
            "warning_count": len(result.warnings),
            "quality_score": result.quality_score,
            "efficiency_score": result.efficiency_score
        }
    
    def _analyze_performance(self, result: ExecutionResult) -> Dict[str, Any]:
        metrics = result.metrics
        
        performance_level = "good"
        if result.duration_seconds > 3600:
            performance_level = "slow"
        elif result.duration_seconds < 300:
            performance_level = "fast"
        
        bottleneck_analysis = []
        if result.duration_seconds > 1800:
            bottleneck_analysis.append({
                "type": "long_duration",
                "description": "任务执行时间过长",
                "suggestion": "检查是否有阻塞操作或优化执行路径"
            })
        
        return {
            "performance_level": performance_level,
            "duration_seconds": result.duration_seconds,
            "metrics": metrics,
            "bottleneck_analysis": bottleneck_analysis,
            "throughput": 1.0 / result.duration_seconds if result.duration_seconds > 0 else 0
        }
    
    def _analyze_quality(self, result: ExecutionResult) -> Dict[str, Any]:
        quality_issues = []
        
        if result.errors:
            for error in result.errors:
                quality_issues.append({
                    "type": "error",
                    "severity": error.get("severity", "high"),
                    "message": error.get("message", str(error))
                })
        
        if result.warnings:
            for warning in result.warnings:
                quality_issues.append({
                    "type": "warning",
                    "severity": "medium",
                    "message": warning.get("message", str(warning))
                })
        
        quality_score = result.quality_score
        if not quality_score:
            error_penalty = len(result.errors) * 0.1
            warning_penalty = len(result.warnings) * 0.05
            quality_score = max(0.0, 1.0 - error_penalty - warning_penalty)
        
        return {
            "quality_score": quality_score,
            "issues": quality_issues,
            "error_count": len(result.errors),
            "warning_count": len(result.warnings),
            "quality_level": "high" if quality_score >= 0.8 else "medium" if quality_score >= 0.6 else "low"
        }
    
    def _analyze_coordination(self, result: ExecutionResult) -> Dict[str, Any]:
        coordination_efficiency = 1.0
        
        if len(result.province_path) > 3:
            coordination_efficiency -= 0.1
        
        if len(result.ministry_path) > 6:
            coordination_efficiency -= 0.1
        
        coordination_path = []
        for i, province in enumerate(result.province_path):
            coordination_path.append({
                "step": i + 1,
                "entity": province,
                "type": "province"
            })
        
        for i, ministry in enumerate(result.ministry_path):
            coordination_path.append({
                "step": len(result.province_path) + i + 1,
                "entity": ministry,
                "type": "ministry"
            })
        
        return {
            "coordination_efficiency": coordination_efficiency,
            "coordination_path": coordination_path,
            "province_involvement": result.province_path,
            "ministry_involvement": result.ministry_path,
            "department_involvement": result.department_path,
            "coordination_complexity": len(coordination_path)
        }
    
    def _generate_recommendations(
        self,
        result: ExecutionResult,
        execution_summary: Dict[str, Any],
        performance_analysis: Dict[str, Any],
        quality_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        recommendations = []
        
        if performance_analysis["performance_level"] == "slow":
            recommendations.append({
                "category": "performance",
                "priority": "high",
                "recommendation": "优化任务执行流程，减少不必要的等待时间",
                "expected_impact": "预计可减少30%执行时间"
            })
        
        if quality_analysis["error_count"] > 0:
            recommendations.append({
                "category": "quality",
                "priority": "critical",
                "recommendation": "修复执行过程中的错误，提高任务成功率",
                "expected_impact": "提高任务质量和成功率"
            })
        
        if len(result.ministry_path) > 4:
            recommendations.append({
                "category": "coordination",
                "priority": "medium",
                "recommendation": "简化协调路径，减少不必要的部门参与",
                "expected_impact": "提高协调效率，减少沟通成本"
            })
        
        return recommendations
    
    def _identify_issues(self, result: ExecutionResult) -> List[Dict[str, Any]]:
        issues = []
        
        for i, error in enumerate(result.errors):
            issues.append({
                "id": f"ISSUE-{result.task_id}-E{i}",
                "type": "error",
                "severity": "high",
                "description": error.get("message", str(error)),
                "location": error.get("location", "unknown"),
                "suggested_fix": error.get("suggested_fix", "需要进一步分析")
            })
        
        for i, warning in enumerate(result.warnings):
            issues.append({
                "id": f"ISSUE-{result.task_id}-W{i}",
                "type": "warning",
                "severity": "medium",
                "description": warning.get("message", str(warning)),
                "location": warning.get("location", "unknown"),
                "suggested_fix": warning.get("suggested_fix", "建议优化")
            })
        
        return issues
    
    def _extract_best_practices(self, result: ExecutionResult) -> List[str]:
        practices = []
        
        if result.status == "completed" and not result.errors:
            practices.append("任务执行完整，无错误发生")
        
        if result.duration_seconds < 600 and result.status == "completed":
            practices.append("任务执行高效，在合理时间内完成")
        
        if result.quality_score >= 0.9:
            practices.append("输出质量优秀，达到高标准")
        
        return practices
    
    def get_aggregate_statistics(self) -> Dict[str, Any]:
        with self._lock:
            if not self.results:
                return {"message": "No execution results available"}
            
            total_tasks = len(self.results)
            completed_tasks = sum(1 for r in self.results.values() if r.status == "completed")
            failed_tasks = sum(1 for r in self.results.values() if r.status == "failed")
            
            durations = [r.duration_seconds for r in self.results.values()]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            quality_scores = [r.quality_score for r in self.results.values() if r.quality_score > 0]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            total_errors = sum(len(r.errors) for r in self.results.values())
            total_warnings = sum(len(r.warnings) for r in self.results.values())
            
            return {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "success_rate": completed_tasks / total_tasks if total_tasks > 0 else 0,
                "avg_duration_seconds": avg_duration,
                "avg_quality_score": avg_quality,
                "total_errors": total_errors,
                "total_warnings": total_warnings,
                "reports_generated": len(self.reports)
            }


class PipelineStage(Enum):
    REQUIREMENT_ANALYSIS = "requirement_analysis"
    SDD_SPECIFICATION = "sdd_specification"
    REVIEW_APPROVAL = "review_approval"
    TEST_FIRST = "test_first"
    IMPLEMENTATION = "implementation"
    REFACTORING = "refactoring"
    DEPLOYMENT = "deployment"


@dataclass
class StageResult:
    stage: PipelineStage
    status: str
    start_time: str
    end_time: Optional[str] = None
    duration_seconds: float = 0.0
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    responsible_entity: str = ""


@dataclass
class PipelineExecution:
    pipeline_id: str
    task_id: str
    stages: List[StageResult] = field(default_factory=list)
    current_stage_index: int = 0
    status: str = "initialized"
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    total_duration_seconds: float = 0.0
    overall_quality_score: float = 0.0
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class PipelineManager:
    def __init__(self):
        self.pipelines: Dict[str, PipelineExecution] = {}
        self.stage_templates: Dict[PipelineStage, Dict[str, Any]] = self._initialize_stage_templates()
        self._lock = threading.Lock()
    
    def _initialize_stage_templates(self) -> Dict[PipelineStage, Dict[str, Any]]:
        return {
            PipelineStage.REQUIREMENT_ANALYSIS: {
                "name": "需求分析",
                "responsible_province": "zhongshusheng",
                "expected_outputs": ["requirement_document", "priority_assessment", "risk_analysis"],
                "quality_criteria": {
                    "completeness": 0.9,
                    "clarity": 0.85,
                    "feasibility": 0.8
                },
                "estimated_duration_seconds": 300
            },
            PipelineStage.SDD_SPECIFICATION: {
                "name": "SDD规范定义",
                "responsible_province": "zhongshusheng",
                "expected_outputs": ["sdd_document", "entity_definitions", "interface_contracts", "business_rules"],
                "quality_criteria": {
                    "spec_completeness": 0.9,
                    "constraint_coverage": 0.85,
                    "traceability": 0.8
                },
                "estimated_duration_seconds": 600
            },
            PipelineStage.REVIEW_APPROVAL: {
                "name": "审议批准",
                "responsible_province": "menxiasheng",
                "expected_outputs": ["review_report", "approval_decision", "quality_gates"],
                "quality_criteria": {
                    "review_coverage": 0.95,
                    "compliance_score": 0.9,
                    "risk_assessment": 0.85
                },
                "estimated_duration_seconds": 300
            },
            PipelineStage.TEST_FIRST: {
                "name": "测试先行",
                "responsible_province": "shangshusheng",
                "responsible_ministry": "bingbu",
                "expected_outputs": ["test_cases", "test_coverage_report", "test_strategy"],
                "quality_criteria": {
                    "coverage": 0.8,
                    "test_quality": 0.85,
                    "boundary_coverage": 0.75
                },
                "estimated_duration_seconds": 900
            },
            PipelineStage.IMPLEMENTATION: {
                "name": "代码实现",
                "responsible_province": "shangshusheng",
                "responsible_ministry": "gongbu",
                "expected_outputs": ["source_code", "build_artifacts", "integration_report"],
                "quality_criteria": {
                    "code_quality": 0.85,
                    "test_pass_rate": 1.0,
                    "spec_compliance": 0.9
                },
                "estimated_duration_seconds": 1800
            },
            PipelineStage.REFACTORING: {
                "name": "持续重构",
                "responsible_province": "shangshusheng",
                "responsible_ministry": "xingbu",
                "expected_outputs": ["refactored_code", "quality_improvement_report", "technical_debt_reduction"],
                "quality_criteria": {
                    "complexity_reduction": 0.8,
                    "duplication_reduction": 0.9,
                    "maintainability_improvement": 0.85
                },
                "estimated_duration_seconds": 600
            },
            PipelineStage.DEPLOYMENT: {
                "name": "部署发布",
                "responsible_province": "shangshusheng",
                "responsible_ministry": "gongbu",
                "expected_outputs": ["deployment_package", "deployment_report", "monitoring_config"],
                "quality_criteria": {
                    "deployment_success": 1.0,
                    "rollback_readiness": 1.0,
                    "monitoring_coverage": 0.9
                },
                "estimated_duration_seconds": 300
            }
        }
    
    def create_pipeline(self, task_id: str) -> PipelineExecution:
        pipeline_id = f"PIPE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        
        stages = []
        for stage in PipelineStage:
            template = self.stage_templates[stage]
            stage_result = StageResult(
                stage=stage,
                status="pending",
                start_time="",
                responsible_entity=template.get("responsible_ministry", template.get("responsible_province", ""))
            )
            stages.append(stage_result)
        
        pipeline = PipelineExecution(
            pipeline_id=pipeline_id,
            task_id=task_id,
            stages=stages,
            status="created"
        )
        
        with self._lock:
            self.pipelines[pipeline_id] = pipeline
        
        return pipeline
    
    def start_pipeline(self, pipeline_id: str) -> bool:
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            return False
        
        pipeline.status = "running"
        pipeline.started_at = datetime.now().isoformat()
        
        if pipeline.stages:
            pipeline.stages[0].status = "running"
            pipeline.stages[0].start_time = datetime.now().isoformat()
        
        return True
    
    def advance_stage(
        self,
        pipeline_id: str,
        outputs: Dict[str, Any],
        quality_metrics: Dict[str, float],
        issues: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            return {"error": f"Pipeline not found: {pipeline_id}"}
        
        if pipeline.current_stage_index >= len(pipeline.stages):
            return {"error": "Pipeline already completed"}
        
        current_stage = pipeline.stages[pipeline.current_stage_index]
        current_stage.status = "completed"
        current_stage.end_time = datetime.now().isoformat()
        current_stage.outputs = outputs
        current_stage.quality_metrics = quality_metrics
        current_stage.issues = issues or []
        
        if current_stage.start_time:
            start = datetime.fromisoformat(current_stage.start_time)
            end = datetime.fromisoformat(current_stage.end_time)
            current_stage.duration_seconds = (end - start).total_seconds()
        
        pipeline.current_stage_index += 1
        
        if pipeline.current_stage_index < len(pipeline.stages):
            next_stage = pipeline.stages[pipeline.current_stage_index]
            next_stage.status = "running"
            next_stage.start_time = datetime.now().isoformat()
            
            return {
                "status": "advanced",
                "completed_stage": current_stage.stage.value,
                "next_stage": next_stage.stage.value,
                "progress": pipeline.current_stage_index / len(pipeline.stages)
            }
        else:
            pipeline.status = "completed"
            pipeline.completed_at = datetime.now().isoformat()
            
            if pipeline.started_at:
                start = datetime.fromisoformat(pipeline.started_at)
                end = datetime.fromisoformat(pipeline.completed_at)
                pipeline.total_duration_seconds = (end - start).total_seconds()
            
            quality_scores = [
                s.quality_metrics for s in pipeline.stages 
                if s.quality_metrics
            ]
            if quality_scores:
                avg_scores = {}
                for metrics in quality_scores:
                    for key, value in metrics.items():
                        if key not in avg_scores:
                            avg_scores[key] = []
                        avg_scores[key].append(value)
                
                pipeline.overall_quality_score = sum(
                    sum(scores) / len(scores) for scores in avg_scores.values()
                ) / len(avg_scores) if avg_scores else 0.0
            
            return {
                "status": "completed",
                "pipeline_id": pipeline_id,
                "total_duration_seconds": pipeline.total_duration_seconds,
                "overall_quality_score": pipeline.overall_quality_score
            }
    
    def fail_stage(
        self,
        pipeline_id: str,
        error: Dict[str, Any],
        rollback: bool = False
    ) -> Dict[str, Any]:
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            return {"error": f"Pipeline not found: {pipeline_id}"}
        
        if pipeline.current_stage_index >= len(pipeline.stages):
            return {"error": "Pipeline already completed"}
        
        current_stage = pipeline.stages[pipeline.current_stage_index]
        current_stage.status = "failed"
        current_stage.end_time = datetime.now().isoformat()
        current_stage.issues.append(error)
        
        if rollback:
            pipeline.status = "rolled_back"
            return {
                "status": "rolled_back",
                "failed_stage": current_stage.stage.value,
                "error": error
            }
        else:
            pipeline.status = "failed"
            return {
                "status": "failed",
                "failed_stage": current_stage.stage.value,
                "error": error
            }
    
    def get_pipeline_status(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            return None
        
        stages_status = []
        for i, stage in enumerate(pipeline.stages):
            template = self.stage_templates[stage.stage]
            stages_status.append({
                "stage": stage.stage.value,
                "name": template["name"],
                "status": stage.status,
                "responsible_entity": stage.responsible_entity,
                "duration_seconds": stage.duration_seconds,
                "quality_metrics": stage.quality_metrics,
                "issues_count": len(stage.issues)
            })
        
        return {
            "pipeline_id": pipeline_id,
            "task_id": pipeline.task_id,
            "status": pipeline.status,
            "current_stage_index": pipeline.current_stage_index,
            "total_stages": len(pipeline.stages),
            "progress": pipeline.current_stage_index / len(pipeline.stages) if pipeline.stages else 0,
            "created_at": pipeline.created_at,
            "started_at": pipeline.started_at,
            "completed_at": pipeline.completed_at,
            "total_duration_seconds": pipeline.total_duration_seconds,
            "overall_quality_score": pipeline.overall_quality_score,
            "stages": stages_status
        }
    
    def get_pipeline_visualization(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            return None
        
        visualization = {
            "pipeline_id": pipeline_id,
            "task_id": pipeline.task_id,
            "status": pipeline.status,
            "flow": []
        }
        
        for i, stage in enumerate(pipeline.stages):
            template = self.stage_templates[stage.stage]
            node = {
                "id": f"stage_{i}",
                "name": template["name"],
                "stage": stage.stage.value,
                "status": stage.status,
                "responsible": stage.responsible_entity,
                "is_current": i == pipeline.current_stage_index,
                "quality_score": sum(stage.quality_metrics.values()) / len(stage.quality_metrics) if stage.quality_metrics else 0
            }
            visualization["flow"].append(node)
        
        return visualization
    
    def get_pipeline_statistics(self) -> Dict[str, Any]:
        with self._lock:
            total_pipelines = len(self.pipelines)
            status_counts = defaultdict(int)
            stage_performance = defaultdict(list)
            
            for pipeline in self.pipelines.values():
                status_counts[pipeline.status] += 1
                
                for stage in pipeline.stages:
                    if stage.duration_seconds > 0:
                        stage_performance[stage.stage.value].append(stage.duration_seconds)
            
            avg_stage_durations = {}
            for stage, durations in stage_performance.items():
                avg_stage_durations[stage] = sum(durations) / len(durations) if durations else 0
            
            return {
                "total_pipelines": total_pipelines,
                "status_distribution": dict(status_counts),
                "average_stage_durations": avg_stage_durations,
                "stage_templates": {
                    stage.value: {
                        "name": template["name"],
                        "estimated_duration": template["estimated_duration_seconds"]
                    }
                    for stage, template in self.stage_templates.items()
                }
            }


@dataclass
class CoordinationMetrics:
    timestamp: str
    province_efficiency: Dict[str, float] = field(default_factory=dict)
    ministry_efficiency: Dict[str, float] = field(default_factory=dict)
    cross_province_coordination: float = 0.0
    cross_ministry_coordination: float = 0.0
    task_success_rate: float = 0.0
    avg_task_duration: float = 0.0
    resource_utilization: float = 0.0
    quality_score: float = 0.0


@dataclass
class OptimizationSuggestion:
    suggestion_id: str
    category: str
    priority: str
    description: str
    current_state: str
    suggested_improvement: str
    expected_impact: str
    implementation_effort: str
    affected_entities: List[str] = field(default_factory=list)


class CoordinationEvaluator:
    def __init__(self):
        self.metrics_history: List[CoordinationMetrics] = []
        self.suggestions: List[OptimizationSuggestion] = []
        self._lock = threading.Lock()
    
    def record_metrics(self, metrics: CoordinationMetrics):
        with self._lock:
            self.metrics_history.append(metrics)
    
    def evaluate_coordination(
        self,
        tasks: List[CoordinationTask],
        execution_results: List[ExecutionResult]
    ) -> Dict[str, Any]:
        if not tasks:
            return {"error": "No tasks to evaluate"}
        
        province_stats = self._analyze_province_performance(tasks)
        ministry_stats = self._analyze_ministry_performance(tasks)
        coordination_efficiency = self._calculate_coordination_efficiency(tasks)
        quality_assessment = self._assess_quality(execution_results)
        
        metrics = CoordinationMetrics(
            timestamp=datetime.now().isoformat(),
            province_efficiency=province_stats["efficiency"],
            ministry_efficiency=ministry_stats["efficiency"],
            cross_province_coordination=coordination_efficiency["cross_province"],
            cross_ministry_coordination=coordination_efficiency["cross_ministry"],
            task_success_rate=quality_assessment["success_rate"],
            avg_task_duration=quality_assessment["avg_duration"],
            resource_utilization=coordination_efficiency["resource_utilization"],
            quality_score=quality_assessment["avg_quality"]
        )
        
        self.record_metrics(metrics)
        
        suggestions = self._generate_optimization_suggestions(
            province_stats, ministry_stats, coordination_efficiency, quality_assessment
        )
        
        return {
            "evaluation_id": f"EVAL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp": metrics.timestamp,
            "province_performance": province_stats,
            "ministry_performance": ministry_stats,
            "coordination_efficiency": coordination_efficiency,
            "quality_assessment": quality_assessment,
            "overall_score": self._calculate_overall_score(metrics),
            "optimization_suggestions": suggestions
        }
    
    def _analyze_province_performance(self, tasks: List[CoordinationTask]) -> Dict[str, Any]:
        province_counts = defaultdict(int)
        province_success = defaultdict(int)
        
        for task in tasks:
            for province in task.province_path:
                province_counts[province] += 1
                if task.status == "completed":
                    province_success[province] += 1
        
        efficiency = {}
        for province, count in province_counts.items():
            efficiency[province] = province_success[province] / count if count > 0 else 0
        
        return {
            "counts": dict(province_counts),
            "success_counts": dict(province_success),
            "efficiency": efficiency,
            "most_active": max(province_counts.items(), key=lambda x: x[1])[0] if province_counts else None
        }
    
    def _analyze_ministry_performance(self, tasks: List[CoordinationTask]) -> Dict[str, Any]:
        ministry_counts = defaultdict(int)
        ministry_success = defaultdict(int)
        
        for task in tasks:
            for ministry in task.ministry_path:
                ministry_counts[ministry] += 1
                if task.status == "completed":
                    ministry_success[ministry] += 1
        
        efficiency = {}
        for ministry, count in ministry_counts.items():
            efficiency[ministry] = ministry_success[ministry] / count if count > 0 else 0
        
        return {
            "counts": dict(ministry_counts),
            "success_counts": dict(ministry_success),
            "efficiency": efficiency,
            "most_active": max(ministry_counts.items(), key=lambda x: x[1])[0] if ministry_counts else None
        }
    
    def _calculate_coordination_efficiency(self, tasks: List[CoordinationTask]) -> Dict[str, Any]:
        if not tasks:
            return {
                "cross_province": 0.0,
                "cross_ministry": 0.0,
                "resource_utilization": 0.0
            }
        
        cross_province_score = 0.0
        cross_ministry_score = 0.0
        
        for task in tasks:
            if len(task.province_path) == 3:
                cross_province_score += 1.0
            elif len(task.province_path) > 0:
                cross_province_score += len(task.province_path) / 3.0
            
            if len(task.ministry_path) >= 4:
                cross_ministry_score += 1.0
            elif len(task.ministry_path) > 0:
                cross_ministry_score += len(task.ministry_path) / 4.0
        
        cross_province = cross_province_score / len(tasks)
        cross_ministry = cross_ministry_score / len(tasks)
        
        resource_utilization = (cross_province + cross_ministry) / 2
        
        return {
            "cross_province": cross_province,
            "cross_ministry": cross_ministry,
            "resource_utilization": resource_utilization
        }
    
    def _assess_quality(self, execution_results: List[ExecutionResult]) -> Dict[str, Any]:
        if not execution_results:
            return {
                "success_rate": 0.0,
                "avg_duration": 0.0,
                "avg_quality": 0.0,
                "total_errors": 0
            }
        
        success_count = sum(1 for r in execution_results if r.status == "completed")
        durations = [r.duration_seconds for r in execution_results]
        quality_scores = [r.quality_score for r in execution_results if r.quality_score > 0]
        total_errors = sum(len(r.errors) for r in execution_results)
        
        return {
            "success_rate": success_count / len(execution_results),
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "avg_quality": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            "total_errors": total_errors
        }
    
    def _calculate_overall_score(self, metrics: CoordinationMetrics) -> float:
        weights = {
            "task_success_rate": 0.3,
            "quality_score": 0.25,
            "coordination": 0.2,
            "resource_utilization": 0.15,
            "efficiency": 0.1
        }
        
        province_avg = sum(metrics.province_efficiency.values()) / len(metrics.province_efficiency) if metrics.province_efficiency else 0
        ministry_avg = sum(metrics.ministry_efficiency.values()) / len(metrics.ministry_efficiency) if metrics.ministry_efficiency else 0
        efficiency_avg = (province_avg + ministry_avg) / 2
        
        coordination_avg = (metrics.cross_province_coordination + metrics.cross_ministry_coordination) / 2
        
        return (
            metrics.task_success_rate * weights["task_success_rate"] +
            metrics.quality_score * weights["quality_score"] +
            coordination_avg * weights["coordination"] +
            metrics.resource_utilization * weights["resource_utilization"] +
            efficiency_avg * weights["efficiency"]
        )
    
    def _generate_optimization_suggestions(
        self,
        province_stats: Dict[str, Any],
        ministry_stats: Dict[str, Any],
        coordination_efficiency: Dict[str, Any],
        quality_assessment: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        suggestions = []
        
        for province, efficiency in province_stats["efficiency"].items():
            if efficiency < 0.8:
                suggestions.append({
                    "suggestion_id": f"SUG-{uuid.uuid4().hex[:8]}",
                    "category": "province_efficiency",
                    "priority": "high" if efficiency < 0.6 else "medium",
                    "description": f"提高{province}的执行效率",
                    "current_state": f"当前效率: {efficiency:.2%}",
                    "suggested_improvement": "优化工作流程，减少不必要的等待时间",
                    "expected_impact": "预计效率提升15-20%",
                    "implementation_effort": "中等",
                    "affected_entities": [province]
                })
        
        for ministry, efficiency in ministry_stats["efficiency"].items():
            if efficiency < 0.8:
                suggestions.append({
                    "suggestion_id": f"SUG-{uuid.uuid4().hex[:8]}",
                    "category": "ministry_efficiency",
                    "priority": "high" if efficiency < 0.6 else "medium",
                    "description": f"提高{ministry}的执行效率",
                    "current_state": f"当前效率: {efficiency:.2%}",
                    "suggested_improvement": "优化任务分配和执行流程",
                    "expected_impact": "预计效率提升10-15%",
                    "implementation_effort": "中等",
                    "affected_entities": [ministry]
                })
        
        if coordination_efficiency["cross_province"] < 0.7:
            suggestions.append({
                "suggestion_id": f"SUG-{uuid.uuid4().hex[:8]}",
                "category": "coordination",
                "priority": "high",
                "description": "改善三省协调流程",
                "current_state": f"当前协调效率: {coordination_efficiency['cross_province']:.2%}",
                "suggested_improvement": "简化协调路径，建立更高效的沟通机制",
                "expected_impact": "预计协调效率提升20-25%",
                "implementation_effort": "高",
                "affected_entities": ["zhongshusheng", "menxiasheng", "shangshusheng"]
            })
        
        if quality_assessment["success_rate"] < 0.9:
            suggestions.append({
                "suggestion_id": f"SUG-{uuid.uuid4().hex[:8]}",
                "category": "quality",
                "priority": "critical",
                "description": "提高任务成功率",
                "current_state": f"当前成功率: {quality_assessment['success_rate']:.2%}",
                "suggested_improvement": "加强质量门禁，优化测试覆盖",
                "expected_impact": "预计成功率提升至95%以上",
                "implementation_effort": "高",
                "affected_entities": ["all"]
            })
        
        return suggestions
    
    def get_historical_trends(self, days: int = 7) -> Dict[str, Any]:
        cutoff = datetime.now() - timedelta(days=days)
        
        recent_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m.timestamp) >= cutoff
        ]
        
        if not recent_metrics:
            return {"message": "No historical data available"}
        
        trends = {
            "success_rate_trend": [],
            "quality_score_trend": [],
            "coordination_efficiency_trend": [],
            "resource_utilization_trend": []
        }
        
        for metrics in sorted(recent_metrics, key=lambda x: x.timestamp):
            trends["success_rate_trend"].append({
                "timestamp": metrics.timestamp,
                "value": metrics.task_success_rate
            })
            trends["quality_score_trend"].append({
                "timestamp": metrics.timestamp,
                "value": metrics.quality_score
            })
            trends["coordination_efficiency_trend"].append({
                "timestamp": metrics.timestamp,
                "value": (metrics.cross_province_coordination + metrics.cross_ministry_coordination) / 2
            })
            trends["resource_utilization_trend"].append({
                "timestamp": metrics.timestamp,
                "value": metrics.resource_utilization
            })
        
        return {
            "period_days": days,
            "data_points": len(recent_metrics),
            "trends": trends
        }


def main():
    parser = argparse.ArgumentParser(
        description="省部司协同调用脚本 - 实现三省六部司三级协同调度",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 创建新任务
  python provincial_coordinator.py --create-task --type feature --description "实现用户登录功能" --priority high
  
  # 执行三省协调
  python provincial_coordinator.py --coordinate --task-id TASK-20240101120000-abc123
  
  # 异步执行三省协调
  python provincial_coordinator.py --async-coordinate --task-id TASK-20240101120000-abc123
  
  # 分发到六部
  python provincial_coordinator.py --dispatch --task-id TASK-20240101120000-abc123
  
  # 司级协作
  python provincial_coordinator.py --coordinate-departments --task-id TASK-20240101120000-abc123 --ministry gongbu
  
  # 查询任务状态
  python provincial_coordinator.py --status --task-id TASK-20240101120000-abc123
  
  # 查询异步任务状态
  python provincial_coordinator.py --async-status --task-id TASK-20240101120000-abc123
  
  # 查询任务进度
  python provincial_coordinator.py --progress --task-id TASK-20240101120000-abc123
  
  # 批量查询状态
  python provincial_coordinator.py --batch-status --status-filter running,executing
  
  # 查看协同链路
  python provincial_coordinator.py --chain --task-id TASK-20240101120000-abc123
  
  # 查看执行时间线
  python provincial_coordinator.py --timeline --task-id TASK-20240101120000-abc123
  
  # 查看统计信息
  python provincial_coordinator.py --stats
  
  # 查看协调日志
  python provincial_coordinator.py --logs --task-id TASK-20240101120000-abc123
  
  # 取消异步任务
  python provincial_coordinator.py --cancel --task-id TASK-20240101120000-abc123
  
  # 添加优先级任务
  python provincial_coordinator.py --add-priority --task-id TASK-20240101120000-abc123 --priority-level high --score 10
  
  # 创建回滚快照
  python provincial_coordinator.py --create-snapshot --task-id TASK-20240101120000-abc123
  
  # 回滚任务
  python provincial_coordinator.py --rollback --task-id TASK-20240101120000-abc123
  
  # 查看恢复状态
  python provincial_coordinator.py --recovery-status --task-id TASK-20240101120000-abc123
  
  # 批量查询（增强版）
  python provincial_coordinator.py --batch-query --task-ids TASK-001 TASK-002 TASK-003
  
  # 查看队列统计
  python provincial_coordinator.py --queue-stats
        """
    )
    
    parser.add_argument("--create-task", action="store_true", help="创建新任务")
    parser.add_argument("--coordinate", action="store_true", help="执行三省协调")
    parser.add_argument("--async-coordinate", action="store_true", help="异步执行三省协调")
    parser.add_argument("--dispatch", action="store_true", help="分发到六部")
    parser.add_argument("--coordinate-departments", action="store_true", help="司级协作")
    parser.add_argument("--status", action="store_true", help="查询任务状态")
    parser.add_argument("--async-status", action="store_true", help="查询异步任务状态")
    parser.add_argument("--progress", action="store_true", help="查询任务进度")
    parser.add_argument("--progress-summary", action="store_true", help="查询进度摘要")
    parser.add_argument("--batch-status", action="store_true", help="批量查询状态")
    parser.add_argument("--chain", action="store_true", help="查看协同链路")
    parser.add_argument("--timeline", action="store_true", help="查看执行时间线")
    parser.add_argument("--stats", action="store_true", help="查看统计信息")
    parser.add_argument("--logs", action="store_true", help="查看协调日志")
    parser.add_argument("--cancel", action="store_true", help="取消异步任务")
    parser.add_argument("--add-priority", action="store_true", help="添加优先级任务")
    parser.add_argument("--create-snapshot", action="store_true", help="创建回滚快照")
    parser.add_argument("--rollback", action="store_true", help="回滚任务")
    parser.add_argument("--recovery-status", action="store_true", help="查看恢复状态")
    parser.add_argument("--batch-query", action="store_true", help="批量查询（增强版）")
    parser.add_argument("--queue-stats", action="store_true", help="查看队列统计")
    parser.add_argument("--handle-failure", action="store_true", help="处理任务失败")
    
    parser.add_argument("--smart-dispatch", action="store_true", help="智能任务分发")
    parser.add_argument("--analyze-execution", action="store_true", help="分析执行结果")
    parser.add_argument("--evaluate-coordination", action="store_true", help="评估协同效果")
    parser.add_argument("--create-pipeline", action="store_true", help="创建流水线")
    parser.add_argument("--start-pipeline", action="store_true", help="启动流水线")
    parser.add_argument("--advance-pipeline", action="store_true", help="推进流水线阶段")
    parser.add_argument("--pipeline-status", action="store_true", help="查看流水线状态")
    parser.add_argument("--pipeline-visualize", action="store_true", help="可视化流水线")
    parser.add_argument("--pipeline-stats", action="store_true", help="流水线统计")
    parser.add_argument("--dispatcher-stats", action="store_true", help="分发器统计")
    parser.add_argument("--analyzer-stats", action="store_true", help="分析器统计")
    parser.add_argument("--historical-trends", action="store_true", help="历史趋势")
    
    parser.add_argument("--task-id", help="任务ID")
    parser.add_argument("--task-ids", nargs="+", help="多个任务ID")
    parser.add_argument("--type", choices=["feature", "bugfix", "refactor", "test", "docs"], help="任务类型")
    parser.add_argument("--description", help="任务描述")
    parser.add_argument("--priority", choices=["low", "medium", "high", "critical"], default="medium", help="优先级")
    parser.add_argument("--priority-level", choices=["critical", "high", "medium", "low", "background"], help="优先级级别")
    parser.add_argument("--score", type=float, default=0.0, help="优先级分数")
    parser.add_argument("--dependencies", nargs="+", help="任务依赖")
    parser.add_argument("--max-retries", type=int, default=3, help="最大重试次数")
    parser.add_argument("--recovery-strategy", choices=["retry", "rollback", "escalate", "abort"], help="恢复策略")
    parser.add_argument("--error-type", help="错误类型")
    parser.add_argument("--error-message", help="错误消息")
    parser.add_argument("--ministry", help="指定部门")
    parser.add_argument("--departments", nargs="+", help="指定司")
    parser.add_argument("--context", help="任务上下文(JSON格式)")
    parser.add_argument("--status-filter", help="状态过滤(逗号分隔)")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--limit", type=int, default=100, help="日志条数限制")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--wait", action="store_true", help="等待异步任务完成")
    parser.add_argument("--timeout", type=int, default=300, help="等待超时时间(秒)")
    parser.add_argument("--include-progress", action="store_true", default=True, help="包含进度信息")
    parser.add_argument("--include-logs", action="store_true", help="包含日志信息")
    parser.add_argument("--required-capabilities", help="所需能力(JSON格式)")
    parser.add_argument("--preferred-specializations", nargs="+", help="偏好专业化")
    parser.add_argument("--entity-type", choices=["province", "ministry"], help="实体类型")
    parser.add_argument("--pipeline-id", help="流水线ID")
    parser.add_argument("--stage-outputs", help="阶段输出(JSON格式)")
    parser.add_argument("--quality-metrics", help="质量指标(JSON格式)")
    parser.add_argument("--days", type=int, default=7, help="历史数据天数")
    
    args = parser.parse_args()
    
    coordinator = ProvincialCoordinator()
    dispatcher = SmartDispatcher()
    analyzer = ExecutionAnalyzer()
    pipeline_manager = PipelineManager()
    evaluator = CoordinationEvaluator()
    result = {}
    
    if args.create_task:
        if not args.type or not args.description:
            parser.error("--create-task requires --type and --description")
        
        context = {}
        if args.context:
            try:
                context = json.loads(args.context)
            except json.JSONDecodeError:
                parser.error("Invalid JSON in --context")
        
        task = coordinator.create_task(
            task_type=args.type,
            description=args.description,
            priority=args.priority,
            context=context
        )
        result = asdict(task)
        
    elif args.async_coordinate:
        if not args.task_id:
            parser.error("--async-coordinate requires --task-id")
        
        task = coordinator.tasks.get(args.task_id)
        if not task:
            result = {"error": f"Task not found: {args.task_id}"}
        else:
            future = coordinator.execute_async_coordination(args.task_id)
            result = {
                "task_id": args.task_id,
                "status": "submitted",
                "message": "异步任务已提交"
            }
            
            if args.wait:
                try:
                    future.result(timeout=args.timeout)
                    result = coordinator.get_async_task_status(args.task_id)
                except Exception as e:
                    result["error"] = str(e)
        
    elif args.coordinate:
        if not args.task_id:
            parser.error("--coordinate requires --task-id")
        
        task = coordinator.tasks.get(args.task_id)
        if not task:
            result = {"error": f"Task not found: {args.task_id}"}
        else:
            result = coordinator.coordinate_provinces(task)
            
    elif args.dispatch:
        if not args.task_id:
            parser.error("--dispatch requires --task-id")
        
        task = coordinator.tasks.get(args.task_id)
        if not task:
            result = {"error": f"Task not found: {args.task_id}"}
        else:
            result = coordinator.dispatch_to_ministries(task, {})
            
    elif args.coordinate_departments:
        if not args.task_id or not args.ministry:
            parser.error("--coordinate-departments requires --task-id and --ministry")
        
        task = coordinator.tasks.get(args.task_id)
        if not task:
            result = {"error": f"Task not found: {args.task_id}"}
        else:
            try:
                ministry = Ministry(args.ministry)
                result = coordinator.coordinate_departments(
                    task, ministry, args.departments
                )
            except ValueError:
                result = {"error": f"Invalid ministry: {args.ministry}"}
                
    elif args.async_status:
        if not args.task_id:
            parser.error("--async-status requires --task-id")
        result = coordinator.get_async_task_status(args.task_id)
        
    elif args.progress:
        if not args.task_id:
            parser.error("--progress requires --task-id")
        result = coordinator.get_task_progress(args.task_id)
        
    elif args.progress_summary:
        if not args.task_id:
            parser.error("--progress-summary requires --task-id")
        result = coordinator.get_progress_summary(args.task_id)
        
    elif args.batch_status:
        status_filter = None
        if args.status_filter:
            status_filter = [TaskStatus(s.strip()) for s in args.status_filter.split(",")]
        result = coordinator.query_status_batch(
            task_ids=args.task_ids,
            status_filter=status_filter,
            limit=args.limit
        )
        
    elif args.timeline:
        if not args.task_id:
            parser.error("--timeline requires --task-id")
        result = {"timeline": coordinator.get_execution_timeline(args.task_id)}
        
    elif args.cancel:
        if not args.task_id:
            parser.error("--cancel requires --task-id")
        success = coordinator.cancel_async_task(args.task_id)
        result = {"task_id": args.task_id, "cancelled": success}
                
    elif args.status:
        if not args.task_id:
            parser.error("--status requires --task-id")
        result = coordinator.get_task_status(args.task_id)
        
    elif args.chain:
        if not args.task_id:
            parser.error("--chain requires --task-id")
        result = coordinator.get_coordination_chain(args.task_id)
        
    elif args.stats:
        result = coordinator.get_statistics()
        
    elif args.logs:
        result = {
            "logs": coordinator.get_coordination_logs(
                task_id=args.task_id,
                ministry=args.ministry,
                department=args.departments[0] if args.departments else None,
                limit=args.limit
            )
        }
    
    elif args.add_priority:
        if not args.task_id:
            parser.error("--add-priority requires --task-id")
        
        priority_map = {
            "critical": TaskPriority.CRITICAL,
            "high": TaskPriority.HIGH,
            "medium": TaskPriority.MEDIUM,
            "low": TaskPriority.LOW,
            "background": TaskPriority.BACKGROUND
        }
        priority = priority_map.get(args.priority_level or "medium", TaskPriority.MEDIUM)
        
        strategy_map = {
            "retry": RecoveryStrategy.RETRY,
            "rollback": RecoveryStrategy.ROLLBACK,
            "escalate": RecoveryStrategy.ESCALATE,
            "abort": RecoveryStrategy.ABORT
        }
        strategy = strategy_map.get(args.recovery_strategy, RecoveryStrategy.RETRY) if args.recovery_strategy else RecoveryStrategy.RETRY
        
        priority_task = coordinator.add_priority_task(
            task_id=args.task_id,
            priority=priority,
            score=args.score,
            dependencies=args.dependencies,
            max_retries=args.max_retries,
            recovery_strategy=strategy
        )
        result = asdict(priority_task)
    
    elif args.create_snapshot:
        if not args.task_id:
            parser.error("--create-snapshot requires --task-id")
        result = coordinator.create_rollback_snapshot(args.task_id)
    
    elif args.rollback:
        if not args.task_id:
            parser.error("--rollback requires --task-id")
        success = coordinator.rollback_task(args.task_id)
        result = {"task_id": args.task_id, "rolled_back": success}
    
    elif args.recovery_status:
        if not args.task_id:
            parser.error("--recovery-status requires --task-id")
        result = coordinator.get_recovery_status(args.task_id)
    
    elif args.batch_query:
        result = coordinator.batch_query_status(
            task_ids=args.task_ids,
            include_progress=args.include_progress,
            include_logs=args.include_logs
        )
    
    elif args.queue_stats:
        result = coordinator.get_queue_statistics()
    
    elif args.handle_failure:
        if not args.task_id or not args.error_type or not args.error_message:
            parser.error("--handle-failure requires --task-id, --error-type, and --error-message")
        
        strategy_map = {
            "retry": RecoveryStrategy.RETRY,
            "rollback": RecoveryStrategy.ROLLBACK,
            "escalate": RecoveryStrategy.ESCALATE,
            "abort": RecoveryStrategy.ABORT
        }
        strategy = strategy_map.get(args.recovery_strategy) if args.recovery_strategy else None
        
        result = asdict(coordinator.handle_task_failure(
            task_id=args.task_id,
            error_type=args.error_type,
            error_message=args.error_message,
            recovery_strategy=strategy
        ))
    
    elif args.smart_dispatch:
        if not args.task_id:
            parser.error("--smart-dispatch requires --task-id")
        
        required_capabilities = {}
        if args.required_capabilities:
            try:
                required_capabilities = json.loads(args.required_capabilities)
            except json.JSONDecodeError:
                parser.error("Invalid JSON in --required-capabilities")
        
        requirement = TaskRequirement(
            task_id=args.task_id,
            required_capabilities=required_capabilities,
            preferred_specializations=args.preferred_specializations or [],
            priority=TaskPriority.HIGH
        )
        
        decision = dispatcher.find_best_match(requirement, args.entity_type)
        result = asdict(decision)
    
    elif args.analyze_execution:
        if not args.task_id:
            parser.error("--analyze-execution requires --task-id")
        
        try:
            report = analyzer.analyze_execution(args.task_id)
            result = asdict(report)
        except ValueError as e:
            result = {"error": str(e)}
    
    elif args.evaluate_coordination:
        tasks = list(coordinator.tasks.values())
        execution_results = list(analyzer.results.values())
        
        evaluation = evaluator.evaluate_coordination(tasks, execution_results)
        result = evaluation
    
    elif args.create_pipeline:
        if not args.task_id:
            parser.error("--create-pipeline requires --task-id")
        
        pipeline = pipeline_manager.create_pipeline(args.task_id)
        result = asdict(pipeline)
    
    elif args.start_pipeline:
        if not args.pipeline_id:
            parser.error("--start-pipeline requires --pipeline-id")
        
        success = pipeline_manager.start_pipeline(args.pipeline_id)
        result = {"pipeline_id": args.pipeline_id, "started": success}
    
    elif args.advance_pipeline:
        if not args.pipeline_id:
            parser.error("--advance-pipeline requires --pipeline-id")
        
        outputs = {}
        if args.stage_outputs:
            try:
                outputs = json.loads(args.stage_outputs)
            except json.JSONDecodeError:
                parser.error("Invalid JSON in --stage-outputs")
        
        quality_metrics = {}
        if args.quality_metrics:
            try:
                quality_metrics = json.loads(args.quality_metrics)
            except json.JSONDecodeError:
                parser.error("Invalid JSON in --quality-metrics")
        
        advance_result = pipeline_manager.advance_stage(
            args.pipeline_id,
            outputs,
            quality_metrics
        )
        result = advance_result
    
    elif args.pipeline_status:
        if not args.pipeline_id:
            parser.error("--pipeline-status requires --pipeline-id")
        
        status = pipeline_manager.get_pipeline_status(args.pipeline_id)
        result = status if status else {"error": f"Pipeline not found: {args.pipeline_id}"}
    
    elif args.pipeline_visualize:
        if not args.pipeline_id:
            parser.error("--pipeline-visualize requires --pipeline-id")
        
        visualization = pipeline_manager.get_pipeline_visualization(args.pipeline_id)
        result = visualization if visualization else {"error": f"Pipeline not found: {args.pipeline_id}"}
    
    elif args.pipeline_stats:
        result = pipeline_manager.get_pipeline_statistics()
    
    elif args.dispatcher_stats:
        result = dispatcher.get_dispatcher_statistics()
    
    elif args.analyzer_stats:
        result = analyzer.get_aggregate_statistics()
    
    elif args.historical_trends:
        result = evaluator.get_historical_trends(args.days)
        
    else:
        parser.print_help()
        return
    
    output_json = json.dumps(result, ensure_ascii=False, indent=2, default=str)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_json)
        print(f"结果已保存到: {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
