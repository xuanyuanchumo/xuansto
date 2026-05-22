"""
脚本注册机制模块
提供脚本注册、发现、依赖解析和生命周期管理功能
"""

import ast
import importlib.util
import inspect
import json
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union


class ScriptCategory(Enum):
    CORE = "core"
    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"
    TEST = "test"
    UTILITY = "utility"
    PIPELINE = "pipeline"
    REQUIREMENTS = "requirements"
    MONITORING = "monitoring"
    SUBSKILL = "subskill"


class ScriptState(Enum):
    UNREGISTERED = auto()
    REGISTERED = auto()
    ACTIVE = auto()
    INACTIVE = auto()
    ERROR = auto()
    UNLOADED = auto()


class ScriptPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class CallStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class CallerType(Enum):
    SCRIPT = "script"
    SUBSKILL = "subskill"
    EXTERNAL = "external"
    SYSTEM = "system"


@dataclass
class CallChainNode:
    caller_type: str
    caller_name: str
    callee_type: str
    callee_name: str
    timestamp: datetime
    duration_ms: int
    status: CallStatus
    error: Optional[str] = None
    args: Optional[tuple] = None
    kwargs: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    call_id: Optional[str] = None

    def __post_init__(self):
        if self.call_id is None:
            import uuid
            self.call_id = str(uuid.uuid4())[:8]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "call_id": self.call_id,
            "caller_type": self.caller_type,
            "caller_name": self.caller_name,
            "callee_type": self.callee_type,
            "callee_name": self.callee_name,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "error": self.error,
            "args": str(self.args) if self.args else None,
            "kwargs": str(self.kwargs) if self.kwargs else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CallChainNode':
        return cls(
            call_id=data.get('call_id'),
            caller_type=data['caller_type'],
            caller_name=data['caller_name'],
            callee_type=data['callee_type'],
            callee_name=data['callee_name'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            duration_ms=data['duration_ms'],
            status=CallStatus(data['status']),
            error=data.get('error'),
            args=data.get('args'),
            kwargs=data.get('kwargs')
        )


@dataclass
class CallState:
    call_id: str
    caller: str
    callee: str
    status: CallStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    caller_type: str = "script"
    callee_type: str = "script"
    duration_ms: int = 0
    retry_count: int = 0
    max_retries: int = 3

    def __post_init__(self):
        import uuid
        if not self.call_id:
            self.call_id = str(uuid.uuid4())[:8]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "call_id": self.call_id,
            "caller": self.caller,
            "callee": self.callee,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": str(self.result) if self.result else None,
            "error": self.error,
            "caller_type": self.caller_type,
            "callee_type": self.callee_type,
            "duration_ms": self.duration_ms,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CallState':
        return cls(
            call_id=data['call_id'],
            caller=data['caller'],
            callee=data['callee'],
            status=CallStatus(data['status']),
            started_at=datetime.fromisoformat(data['started_at']),
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            result=data.get('result'),
            error=data.get('error'),
            caller_type=data.get('caller_type', 'script'),
            callee_type=data.get('callee_type', 'script'),
            duration_ms=data.get('duration_ms', 0),
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3)
        )


@dataclass
class ScriptMetadata:
    name: str
    version: str
    description: str
    category: ScriptCategory
    dependencies: List[str] = field(default_factory=list)
    entry_point: str = "main"
    config_schema: Dict[str, Any] = field(default_factory=dict)
    author: str = ""
    tags: List[str] = field(default_factory=list)
    priority: ScriptPriority = ScriptPriority.NORMAL
    enabled: bool = True
    auto_activate: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "category": self.category.value,
            "dependencies": self.dependencies,
            "entry_point": self.entry_point,
            "config_schema": self.config_schema,
            "author": self.author,
            "tags": self.tags,
            "priority": self.priority.value,
            "enabled": self.enabled,
            "auto_activate": self.auto_activate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScriptMetadata':
        return cls(
            name=data['name'],
            version=data['version'],
            description=data['description'],
            category=ScriptCategory(data['category']),
            dependencies=data.get('dependencies', []),
            entry_point=data.get('entry_point', 'main'),
            config_schema=data.get('config_schema', {}),
            author=data.get('author', ''),
            tags=data.get('tags', []),
            priority=ScriptPriority(data.get('priority', 2)),
            enabled=data.get('enabled', True),
            auto_activate=data.get('auto_activate', True),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )


@dataclass
class ScriptInfo:
    metadata: ScriptMetadata
    path: Path
    state: ScriptState = ScriptState.UNREGISTERED
    module: Optional[Any] = None
    instance: Optional[Any] = None
    error_message: Optional[str] = None
    load_time: Optional[datetime] = None
    last_execution: Optional[datetime] = None
    execution_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict(),
            "path": str(self.path),
            "state": self.state.name,
            "error_message": self.error_message,
            "load_time": self.load_time.isoformat() if self.load_time else None,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "execution_count": self.execution_count
        }


@dataclass
class DependencyNode:
    name: str
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    depth: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "dependencies": list(self.dependencies),
            "dependents": list(self.dependents),
            "depth": self.depth
        }


class DependencyGraph:
    def __init__(self):
        self._nodes: Dict[str, DependencyNode] = {}
    
    def add_script(self, name: str, dependencies: List[str] = None) -> None:
        if name not in self._nodes:
            self._nodes[name] = DependencyNode(name=name)
        
        if dependencies:
            for dep in dependencies:
                self._nodes[name].dependencies.add(dep)
                if dep not in self._nodes:
                    self._nodes[dep] = DependencyNode(name=dep)
                self._nodes[dep].dependents.add(name)
        
        self._update_depths()
    
    def remove_script(self, name: str) -> None:
        if name in self._nodes:
            node = self._nodes[name]
            for dep in node.dependencies:
                if dep in self._nodes:
                    self._nodes[dep].dependents.discard(name)
            for dependent in node.dependents:
                if dependent in self._nodes:
                    self._nodes[dependent].dependencies.discard(name)
            del self._nodes[name]
            self._update_depths()
    
    def _update_depths(self) -> None:
        visited = set()
        
        def calc_depth(name: str) -> int:
            if name not in self._nodes:
                return 0
            if name in visited:
                return self._nodes[name].depth
            visited.add(name)
            
            node = self._nodes[name]
            if not node.dependencies:
                node.depth = 0
            else:
                max_dep_depth = 0
                for dep in node.dependencies:
                    if dep in self._nodes:
                        max_dep_depth = max(max_dep_depth, calc_depth(dep) + 1)
                node.depth = max_dep_depth
            
            return node.depth
        
        for name in list(self._nodes.keys()):
            calc_depth(name)
    
    def get_load_order(self) -> List[str]:
        return sorted(
            self._nodes.keys(),
            key=lambda x: (self._nodes[x].depth, x)
        )
    
    def get_shutdown_order(self) -> List[str]:
        return list(reversed(self.get_load_order()))
    
    def detect_cycles(self) -> List[List[str]]:
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(name: str) -> bool:
            visited.add(name)
            rec_stack.add(name)
            path.append(name)
            
            if name in self._nodes:
                for dep in self._nodes[name].dependencies:
                    if dep not in visited:
                        if dfs(dep):
                            return True
                    elif dep in rec_stack:
                        cycle_start = path.index(dep)
                        cycles.append(path[cycle_start:] + [dep])
                        return True
            
            path.pop()
            rec_stack.remove(name)
            return False
        
        for name in self._nodes:
            if name not in visited:
                dfs(name)
        
        return cycles
    
    def get_dependencies(self, name: str, recursive: bool = True) -> Set[str]:
        if name not in self._nodes:
            return set()
        
        if not recursive:
            return self._nodes[name].dependencies.copy()
        
        all_deps = set()
        queue = list(self._nodes[name].dependencies)
        
        while queue:
            dep = queue.pop(0)
            if dep not in all_deps:
                all_deps.add(dep)
                if dep in self._nodes:
                    queue.extend(self._nodes[dep].dependencies)
        
        return all_deps
    
    def get_dependents(self, name: str, recursive: bool = True) -> Set[str]:
        if name not in self._nodes:
            return set()
        
        if not recursive:
            return self._nodes[name].dependents.copy()
        
        all_dependents = set()
        queue = list(self._nodes[name].dependents)
        
        while queue:
            dependent = queue.pop(0)
            if dependent not in all_dependents:
                all_dependents.add(dependent)
                if dependent in self._nodes:
                    queue.extend(self._nodes[dependent].dependents)
        
        return all_dependents
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": {name: node.to_dict() for name, node in self._nodes.items()},
            "load_order": self.get_load_order(),
            "cycles": self.detect_cycles()
        }


class CallChainTracker:
    def __init__(self, max_history: int = 1000):
        self._call_chain: List[CallChainNode] = []
        self._max_history = max_history
        self._call_graph: Dict[str, Set[str]] = {}
        self._active_calls: Dict[str, CallChainNode] = {}

    def start_call(
        self,
        caller_type: str,
        caller_name: str,
        callee_type: str,
        callee_name: str,
        args: tuple = None,
        kwargs: Dict[str, Any] = None
    ) -> str:
        import uuid
        call_id = str(uuid.uuid4())[:8]

        node = CallChainNode(
            call_id=call_id,
            caller_type=caller_type,
            caller_name=caller_name,
            callee_type=callee_type,
            callee_name=callee_name,
            timestamp=datetime.now(),
            duration_ms=0,
            status=CallStatus.RUNNING,
            args=args,
            kwargs=kwargs
        )

        self._active_calls[call_id] = node
        return call_id

    def end_call(
        self,
        call_id: str,
        status: CallStatus,
        result: Any = None,
        error: Optional[str] = None
    ) -> Optional[CallChainNode]:
        if call_id not in self._active_calls:
            return None

        node = self._active_calls.pop(call_id)
        node.status = status
        node.result = result
        node.error = error

        now = datetime.now()
        node.duration_ms = int((now - node.timestamp).total_seconds() * 1000)

        self._call_chain.append(node)
        self._update_call_graph(node)

        if len(self._call_chain) > self._max_history:
            self._call_chain = self._call_chain[-self._max_history:]

        return node

    def _update_call_graph(self, node: CallChainNode) -> None:
        edge_key = f"{node.caller_type}:{node.caller_name}"
        target_key = f"{node.callee_type}:{node.callee_name}"

        if edge_key not in self._call_graph:
            self._call_graph[edge_key] = set()
        self._call_graph[edge_key].add(target_key)

    def get_call_chain(self, limit: int = 100) -> List[CallChainNode]:
        return self._call_chain[-limit:]

    def get_call_chain_by_caller(self, caller_name: str) -> List[CallChainNode]:
        return [
            node for node in self._call_chain
            if node.caller_name == caller_name
        ]

    def get_call_chain_by_callee(self, callee_name: str) -> List[CallChainNode]:
        return [
            node for node in self._call_chain
            if node.callee_name == callee_name
        ]

    def get_call_chain_by_status(self, status: CallStatus) -> List[CallChainNode]:
        return [
            node for node in self._call_chain
            if node.status == status
        ]

    def get_call_graph(self) -> Dict[str, Set[str]]:
        return {
            key: set(values)
            for key, values in self._call_graph.items()
        }

    def generate_call_chain_graph(self) -> Dict[str, Any]:
        nodes = set()
        for node in self._call_chain:
            nodes.add(f"{node.caller_type}:{node.caller_name}")
            nodes.add(f"{node.callee_type}:{node.callee_name}")

        edges = []
        for source, targets in self._call_graph.items():
            for target in targets:
                call_count = sum(
                    1 for node in self._call_chain
                    if f"{node.caller_type}:{node.caller_name}" == source
                    and f"{node.callee_type}:{node.callee_name}" == target
                )
                edges.append({
                    "source": source,
                    "target": target,
                    "count": call_count
                })

        return {
            "nodes": list(nodes),
            "edges": edges,
            "total_calls": len(self._call_chain),
            "generated_at": datetime.now().isoformat()
        }

    def export_call_chain(self, format: str = "json") -> str:
        data = {
            "exported_at": datetime.now().isoformat(),
            "total_calls": len(self._call_chain),
            "call_chain": [node.to_dict() for node in self._call_chain],
            "call_graph": self.generate_call_chain_graph()
        }

        if format == "json":
            return json.dumps(data, indent=2, ensure_ascii=False)
        elif format == "mermaid":
            return self._generate_mermaid_diagram()
        else:
            return str(data)

    def _generate_mermaid_diagram(self) -> str:
        lines = ["graph TD"]
        added_nodes = set()

        for node in self._call_chain:
            caller_id = f"{node.caller_type}_{node.caller_name}".replace("-", "_")
            callee_id = f"{node.callee_type}_{node.callee_name}".replace("-", "_")

            if caller_id not in added_nodes:
                lines.append(f"    {caller_id}[{node.caller_name}]")
                added_nodes.add(caller_id)

            if callee_id not in added_nodes:
                lines.append(f"    {callee_id}[{node.callee_name}]")
                added_nodes.add(callee_id)

            style = ":::success" if node.status == CallStatus.SUCCESS else ":::failed"
            lines.append(f"    {caller_id} -->{style} {callee_id}")

        lines.append("    classDef success stroke:#0f0")
        lines.append("    classDef failed stroke:#f00")

        return "\n".join(lines)

    def get_statistics(self) -> Dict[str, Any]:
        if not self._call_chain:
            return {
                "total_calls": 0,
                "success_rate": 0,
                "average_duration_ms": 0,
                "by_caller_type": {},
                "by_callee_type": {},
                "by_status": {}
            }

        success_count = sum(1 for node in self._call_chain if node.status == CallStatus.SUCCESS)
        total_duration = sum(node.duration_ms for node in self._call_chain)

        by_caller_type: Dict[str, int] = {}
        by_callee_type: Dict[str, int] = {}
        by_status: Dict[str, int] = {}

        for node in self._call_chain:
            by_caller_type[node.caller_type] = by_caller_type.get(node.caller_type, 0) + 1
            by_callee_type[node.callee_type] = by_callee_type.get(node.callee_type, 0) + 1
            by_status[node.status.value] = by_status.get(node.status.value, 0) + 1

        return {
            "total_calls": len(self._call_chain),
            "success_rate": success_count / len(self._call_chain) * 100,
            "average_duration_ms": total_duration / len(self._call_chain),
            "by_caller_type": by_caller_type,
            "by_callee_type": by_callee_type,
            "by_status": by_status
        }

    def clear(self) -> None:
        self._call_chain.clear()
        self._call_graph.clear()
        self._active_calls.clear()


class CallStateRecorder:
    def __init__(self, max_history: int = 500):
        self._states: Dict[str, CallState] = {}
        self._history: List[CallState] = []
        self._max_history = max_history
        self._state_hooks: Dict[str, List[Callable]] = {
            'on_state_change': [],
            'on_success': [],
            'on_failure': [],
            'on_timeout': []
        }

    def start_call(
        self,
        caller: str,
        callee: str,
        caller_type: str = "script",
        callee_type: str = "script"
    ) -> str:
        import uuid
        call_id = str(uuid.uuid4())[:8]

        state = CallState(
            call_id=call_id,
            caller=caller,
            callee=callee,
            status=CallStatus.PENDING,
            started_at=datetime.now(),
            caller_type=caller_type,
            callee_type=callee_type
        )

        self._states[call_id] = state
        return call_id

    def update_status(
        self,
        call_id: str,
        status: CallStatus,
        error: Optional[str] = None
    ) -> Optional[CallState]:
        if call_id not in self._states:
            return None

        state = self._states[call_id]
        old_status = state.status
        state.status = status

        if error:
            state.error = error

        self._execute_hooks('on_state_change', call_id, old_status, status)

        if status == CallStatus.SUCCESS:
            self._execute_hooks('on_success', call_id)
        elif status == CallStatus.FAILED:
            self._execute_hooks('on_failure', call_id, error)
        elif status == CallStatus.TIMEOUT:
            self._execute_hooks('on_timeout', call_id)

        return state

    def complete_call(
        self,
        call_id: str,
        result: Any = None,
        error: Optional[str] = None
    ) -> Optional[CallState]:
        if call_id not in self._states:
            return None

        state = self._states.pop(call_id)
        state.completed_at = datetime.now()
        state.duration_ms = int(
            (state.completed_at - state.started_at).total_seconds() * 1000
        )
        state.result = result

        if error:
            state.status = CallStatus.FAILED
            state.error = error
        else:
            state.status = CallStatus.SUCCESS

        self._history.append(state)

        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        self._execute_hooks('on_state_change', call_id, CallStatus.RUNNING, state.status)

        return state

    def get_state(self, call_id: str) -> Optional[CallState]:
        return self._states.get(call_id)

    def get_active_calls(self) -> List[CallState]:
        return list(self._states.values())

    def get_history(self, limit: int = 100) -> List[CallState]:
        return self._history[-limit:]

    def get_history_by_caller(self, caller: str) -> List[CallState]:
        return [state for state in self._history if state.caller == caller]

    def get_history_by_callee(self, callee: str) -> List[CallState]:
        return [state for state in self._history if state.callee == callee]

    def get_history_by_status(self, status: CallStatus) -> List[CallState]:
        return [state for state in self._history if state.status == status]

    def get_failed_calls(self) -> List[CallState]:
        return self.get_history_by_status(CallStatus.FAILED)

    def get_successful_calls(self) -> List[CallState]:
        return self.get_history_by_status(CallStatus.SUCCESS)

    def get_statistics(self) -> Dict[str, Any]:
        if not self._history:
            return {
                "total_calls": 0,
                "active_calls": len(self._states),
                "success_count": 0,
                "failed_count": 0,
                "success_rate": 0,
                "average_duration_ms": 0
            }

        success_count = sum(1 for s in self._history if s.status == CallStatus.SUCCESS)
        failed_count = sum(1 for s in self._history if s.status == CallStatus.FAILED)
        total_duration = sum(s.duration_ms for s in self._history)

        return {
            "total_calls": len(self._history),
            "active_calls": len(self._states),
            "success_count": success_count,
            "failed_count": failed_count,
            "success_rate": success_count / len(self._history) * 100 if self._history else 0,
            "average_duration_ms": total_duration / len(self._history) if self._history else 0
        }

    def add_hook(self, event: str, callback: Callable) -> None:
        if event in self._state_hooks:
            self._state_hooks[event].append(callback)

    def remove_hook(self, event: str, callback: Callable) -> bool:
        if event in self._state_hooks and callback in self._state_hooks[event]:
            self._state_hooks[event].remove(callback)
            return True
        return False

    def _execute_hooks(self, event: str, *args, **kwargs) -> None:
        if event in self._state_hooks:
            for callback in self._state_hooks[event]:
                try:
                    callback(*args, **kwargs)
                except Exception:
                    pass

    def export_history(self, output_path: Path) -> bool:
        try:
            data = {
                "exported_at": datetime.now().isoformat(),
                "active_calls": [s.to_dict() for s in self._states.values()],
                "history": [s.to_dict() for s in self._history],
                "statistics": self.get_statistics()
            }

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        except Exception:
            return False

    def clear(self) -> None:
        self._states.clear()
        self._history.clear()


class IScriptLifecycle(ABC):
    @abstractmethod
    def on_register(self) -> None:
        pass
    
    @abstractmethod
    def on_activate(self) -> None:
        pass
    
    @abstractmethod
    def on_deactivate(self) -> None:
        pass
    
    @abstractmethod
    def on_unload(self) -> None:
        pass
    
    @abstractmethod
    def on_error(self, error: Exception) -> None:
        pass


class SubskillScriptAdapter:
    def __init__(self, subskill_manager=None):
        self._subskill_manager = subskill_manager
        self._adapters: Dict[str, Callable] = {}
        self._metadata_cache: Dict[str, ScriptMetadata] = {}

    def _get_subskill_manager(self):
        if self._subskill_manager is None:
            try:
                from .subskill_manager import get_subskill_manager
                self._subskill_manager = get_subskill_manager()
            except ImportError:
                pass
        return self._subskill_manager

    def register_subskill_as_script(
        self,
        subskill_name: str,
        registry: 'ScriptRegistry' = None
    ) -> bool:
        manager = self._get_subskill_manager()
        if not manager:
            return False

        subskill_info = manager.get_subskill(subskill_name)
        if not subskill_info:
            return False

        metadata = self._convert_to_script_metadata(subskill_info)
        self._metadata_cache[subskill_name] = metadata

        if registry:
            script_info = ScriptInfo(
                metadata=metadata,
                path=subskill_info.path,
                state=ScriptState.REGISTERED
            )
            return registry.register_from_info(script_info)

        return True

    def _convert_to_script_metadata(self, subskill_info) -> ScriptMetadata:
        return ScriptMetadata(
            name=subskill_info.name,
            version=subskill_info.version,
            description=subskill_info.description,
            category=ScriptCategory.SUBSKILL,
            dependencies=subskill_info.dependencies,
            entry_point="execute",
            config_schema={},
            author=subskill_info.metadata.get('author', ''),
            tags=subskill_info.tags,
            priority=ScriptPriority.NORMAL,
            enabled=True,
            auto_activate=False,
            created_at=subskill_info.created_at,
            updated_at=subskill_info.updated_at
        )

    def execute_subskill(
        self,
        name: str,
        *args,
        **kwargs
    ) -> Any:
        manager = self._get_subskill_manager()
        if not manager:
            raise RuntimeError("子技能管理器未初始化")

        context = kwargs.get('context', {})
        if args:
            context['args'] = args
        context.update({k: v for k, v in kwargs.items() if k != 'context'})

        return manager.call_subskill(name, context)

    def get_subskill_guidance(
        self,
        name: str,
        topic: str
    ) -> Optional[str]:
        manager = self._get_subskill_manager()
        if not manager:
            return None

        return manager.get_guidance(name, topic)

    def create_adapter_function(
        self,
        subskill_name: str
    ) -> Callable:
        def adapter(*args, **kwargs):
            return self.execute_subskill(subskill_name, *args, **kwargs)

        adapter.__name__ = f"subskill_{subskill_name}"
        adapter.__doc__ = f"子技能 '{subskill_name}' 的适配器函数"
        return adapter

    def get_all_adapters(self) -> Dict[str, Callable]:
        manager = self._get_subskill_manager()
        if not manager:
            return {}

        adapters = {}
        for subskill in manager.list_subskills():
            adapters[subskill.name] = self.create_adapter_function(subskill.name)

        return adapters

    def get_metadata(self, subskill_name: str) -> Optional[ScriptMetadata]:
        if subskill_name in self._metadata_cache:
            return self._metadata_cache[subskill_name]

        manager = self._get_subskill_manager()
        if not manager:
            return None

        subskill_info = manager.get_subskill(subskill_name)
        if not subskill_info:
            return None

        metadata = self._convert_to_script_metadata(subskill_info)
        self._metadata_cache[subskill_name] = metadata
        return metadata

    def clear_cache(self) -> None:
        self._metadata_cache.clear()


class ScriptDiscovery:
    CATEGORY_DIRS = {
        ScriptCategory.CORE: "core",
        ScriptCategory.ANALYSIS: "analysis",
        ScriptCategory.OPTIMIZATION: "optimization",
        ScriptCategory.TEST: "test",
        ScriptCategory.UTILITY: "utils",
        ScriptCategory.PIPELINE: "pipeline",
        ScriptCategory.REQUIREMENTS: "requirements",
        ScriptCategory.MONITORING: "monitoring",
        ScriptCategory.SUBSKILL: "subskills"
    }
    
    METADATA_PATTERNS = [
        "SCRIPT_META",
        "SCRIPT_METADATA",
        "METADATA",
        "__meta__"
    ]
    
    def __init__(self, base_path: Path = None):
        self.base_path = base_path or get_path_config().SKILL_ROOT
        self._discovered: Dict[str, ScriptInfo] = {}
    
    def discover_all(self) -> Dict[str, ScriptInfo]:
        self._discovered.clear()
        
        for category, dir_name in self.CATEGORY_DIRS.items():
            category_path = self.base_path / dir_name
            if category_path.exists() and category_path.is_dir():
                self._discover_category(category_path, category)
        
        return self._discovered
    
    def _discover_category(self, category_path: Path, category: ScriptCategory) -> None:
        for script_file in category_path.glob("*.py"):
            if script_file.name.startswith("_"):
                continue
            
            script_info = self._analyze_script(script_file, category)
            if script_info:
                self._discovered[script_info.metadata.name] = script_info
    
    def _analyze_script(self, script_path: Path, category: ScriptCategory) -> Optional[ScriptInfo]:
        try:
            metadata = self._extract_metadata(script_path, category)
            if metadata:
                return ScriptInfo(
                    metadata=metadata,
                    path=script_path,
                    state=ScriptState.UNREGISTERED
                )
        except Exception as e:
            pass
        
        return None
    
    def _extract_metadata(self, script_path: Path, category: ScriptCategory) -> Optional[ScriptMetadata]:
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for pattern in self.METADATA_PATTERNS:
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id == pattern:
                                metadata = self._parse_metadata_node(node.value, script_path, category)
                                if metadata:
                                    return metadata
            
            docstring = ast.get_docstring(tree)
            if docstring:
                return self._create_metadata_from_docstring(script_path, category, docstring)
            
            return self._create_default_metadata(script_path, category)
            
        except Exception:
            return self._create_default_metadata(script_path, category)
    
    def _parse_metadata_node(self, node: ast.AST, script_path: Path, category: ScriptCategory) -> Optional[ScriptMetadata]:
        try:
            if isinstance(node, ast.Dict):
                metadata_dict = {}
                for key, value in zip(node.keys, node.values):
                    if isinstance(key, ast.Constant):
                        key_str = key.value
                    elif isinstance(key, ast.Str):
                        key_str = key.s
                    else:
                        continue
                    
                    if isinstance(value, ast.Constant):
                        metadata_dict[key_str] = value.value
                    elif isinstance(value, ast.Str):
                        metadata_dict[key_str] = value.s
                    elif isinstance(value, ast.List):
                        metadata_dict[key_str] = [
                            elt.value if isinstance(elt, ast.Constant) else elt.s
                            for elt in value.elts
                            if isinstance(elt, (ast.Constant, ast.Str))
                        ]
                    elif isinstance(value, ast.Dict):
                        metadata_dict[key_str] = {}
                        for k, v in zip(value.keys, value.values):
                            if isinstance(k, (ast.Constant, ast.Str)):
                                k_val = k.value if isinstance(k, ast.Constant) else k.s
                                v_val = v.value if isinstance(v, ast.Constant) else v.s
                                metadata_dict[key_str][k_val] = v_val
                
                return ScriptMetadata(
                    name=metadata_dict.get('name', script_path.stem),
                    version=metadata_dict.get('version', '1.0.0'),
                    description=metadata_dict.get('description', ''),
                    category=category,
                    dependencies=metadata_dict.get('dependencies', []),
                    entry_point=metadata_dict.get('entry_point', 'main'),
                    config_schema=metadata_dict.get('config_schema', {}),
                    author=metadata_dict.get('author', ''),
                    tags=metadata_dict.get('tags', [])
                )
        except Exception:
            pass
        
        return None
    
    def _create_metadata_from_docstring(self, script_path: Path, category: ScriptCategory, docstring: str) -> ScriptMetadata:
        lines = docstring.strip().split('\n')
        name = script_path.stem
        description = lines[0] if lines else ""
        
        return ScriptMetadata(
            name=name,
            version='1.0.0',
            description=description,
            category=category
        )
    
    def _create_default_metadata(self, script_path: Path, category: ScriptCategory) -> ScriptMetadata:
        return ScriptMetadata(
            name=script_path.stem,
            version='1.0.0',
            description=f"脚本: {script_path.stem}",
            category=category
        )
    
    def get_discovered(self) -> Dict[str, ScriptInfo]:
        return self._discovered.copy()
    
    def refresh(self) -> Dict[str, ScriptInfo]:
        return self.discover_all()


class ScriptRegistry:
    def __init__(self, base_path: Path = None):
        self._scripts: Dict[str, ScriptInfo] = {}
        self._dependency_graph = DependencyGraph()
        self._discovery = ScriptDiscovery(base_path)
        self._hooks: Dict[str, List[Callable]] = {
            'pre_register': [],
            'post_register': [],
            'pre_activate': [],
            'post_activate': [],
            'pre_deactivate': [],
            'post_deactivate': [],
            'pre_unload': [],
            'post_unload': [],
            'on_error': [],
            'pre_execute': [],
            'post_execute': []
        }
        self._config: Dict[str, Any] = {}
        self._call_chain_tracker = CallChainTracker()
        self._call_state_recorder = CallStateRecorder()
        self._subskill_adapter = SubskillScriptAdapter()
        self._current_caller: Optional[str] = None
        self._current_caller_type: str = "system"
    
    def register(
        self,
        name: str,
        version: str = "1.0.0",
        description: str = "",
        category: ScriptCategory = ScriptCategory.UTILITY,
        dependencies: List[str] = None,
        entry_point: str = "main",
        config_schema: Dict[str, Any] = None,
        path: Path = None,
        **kwargs
    ) -> bool:
        self._execute_hooks('pre_register', name)
        
        if name in self._scripts:
            return False
        
        metadata = ScriptMetadata(
            name=name,
            version=version,
            description=description,
            category=category,
            dependencies=dependencies or [],
            entry_point=entry_point,
            config_schema=config_schema or {},
            **kwargs
        )
        
        script_info = ScriptInfo(
            metadata=metadata,
            path=path or Path.cwd() / f"{name}.py",
            state=ScriptState.REGISTERED
        )
        
        self._scripts[name] = script_info
        self._dependency_graph.add_script(name, dependencies)
        
        cycles = self._dependency_graph.detect_cycles()
        if cycles:
            self._dependency_graph.remove_script(name)
            del self._scripts[name]
            return False
        
        self._execute_hooks('post_register', name)
        
        return True
    
    def register_from_info(self, script_info: ScriptInfo) -> bool:
        self._execute_hooks('pre_register', script_info.metadata.name)
        
        name = script_info.metadata.name
        if name in self._scripts:
            return False
        
        self._scripts[name] = script_info
        script_info.state = ScriptState.REGISTERED
        
        self._dependency_graph.add_script(
            name,
            script_info.metadata.dependencies
        )
        
        cycles = self._dependency_graph.detect_cycles()
        if cycles:
            self._dependency_graph.remove_script(name)
            del self._scripts[name]
            return False
        
        self._execute_hooks('post_register', name)
        
        return True
    
    def unregister(self, name: str) -> bool:
        if name not in self._scripts:
            return False
        
        script_info = self._scripts[name]
        
        if script_info.state == ScriptState.ACTIVE:
            self.deactivate(name)
        
        self._execute_hooks('pre_unload', name)
        
        self._dependency_graph.remove_script(name)
        del self._scripts[name]
        
        self._execute_hooks('post_unload', name)
        
        return True
    
    def discover_and_register(self) -> Dict[str, bool]:
        discovered = self._discovery.discover_all()
        results = {}
        
        for name, script_info in discovered.items():
            results[name] = self.register_from_info(script_info)
        
        return results
    
    def activate(self, name: str) -> bool:
        if name not in self._scripts:
            return False
        
        script_info = self._scripts[name]
        
        if script_info.state == ScriptState.ACTIVE:
            return True
        
        if not script_info.metadata.enabled:
            return False
        
        self._execute_hooks('pre_activate', name)
        
        try:
            for dep in script_info.metadata.dependencies:
                if dep in self._scripts:
                    dep_info = self._scripts[dep]
                    if dep_info.state != ScriptState.ACTIVE:
                        if not self.activate(dep):
                            raise RuntimeError(f"无法激活依赖脚本: {dep}")
            
            if script_info.path and script_info.path.exists():
                module = self._load_module(script_info)
                if module:
                    script_info.module = module
                    script_info.state = ScriptState.ACTIVE
                    script_info.load_time = datetime.now()
                    script_info.error_message = None
                else:
                    raise RuntimeError("无法加载模块")
            else:
                script_info.state = ScriptState.ACTIVE
                script_info.load_time = datetime.now()
            
            self._execute_hooks('post_activate', name)
            return True
            
        except Exception as e:
            script_info.state = ScriptState.ERROR
            script_info.error_message = str(e)
            self._execute_hooks('on_error', name, e)
            return False
    
    def deactivate(self, name: str) -> bool:
        if name not in self._scripts:
            return False
        
        script_info = self._scripts[name]
        
        if script_info.state != ScriptState.ACTIVE:
            return True
        
        dependents = self._dependency_graph.get_dependents(name)
        for dependent in dependents:
            if dependent in self._scripts:
                dep_info = self._scripts[dependent]
                if dep_info.state == ScriptState.ACTIVE:
                    self.deactivate(dependent)
        
        self._execute_hooks('pre_deactivate', name)
        
        try:
            if script_info.instance and hasattr(script_info.instance, 'cleanup'):
                script_info.instance.cleanup()
            
            script_info.module = None
            script_info.instance = None
            script_info.state = ScriptState.INACTIVE
            
            self._execute_hooks('post_deactivate', name)
            return True
            
        except Exception as e:
            script_info.state = ScriptState.ERROR
            script_info.error_message = str(e)
            self._execute_hooks('on_error', name, e)
            return False
    
    def _load_module(self, script_info: ScriptInfo) -> Optional[Any]:
        try:
            spec = importlib.util.spec_from_file_location(
                script_info.metadata.name,
                script_info.path
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[script_info.metadata.name] = module
                spec.loader.exec_module(module)
                return module
        except Exception:
            pass
        
        return None
    
    def get_script(self, name: str) -> Optional[ScriptInfo]:
        return self._scripts.get(name)
    
    def get_metadata(self, name: str) -> Optional[ScriptMetadata]:
        script_info = self._scripts.get(name)
        return script_info.metadata if script_info else None
    
    def get_all_scripts(self) -> Dict[str, ScriptInfo]:
        return self._scripts.copy()
    
    def get_scripts_by_category(self, category: ScriptCategory) -> List[ScriptInfo]:
        return [
            info for info in self._scripts.values()
            if info.metadata.category == category
        ]
    
    def get_scripts_by_state(self, state: ScriptState) -> List[ScriptInfo]:
        return [
            info for info in self._scripts.values()
            if info.state == state
        ]
    
    def get_active_scripts(self) -> List[ScriptInfo]:
        return self.get_scripts_by_state(ScriptState.ACTIVE)
    
    def resolve_dependencies(self, name: str) -> List[str]:
        if name not in self._scripts:
            return []
        
        all_deps = self._dependency_graph.get_dependencies(name, recursive=True)
        load_order = self._dependency_graph.get_load_order()
        
        return [n for n in load_order if n in all_deps]
    
    def get_load_order(self) -> List[str]:
        return self._dependency_graph.get_load_order()
    
    def get_shutdown_order(self) -> List[str]:
        return self._dependency_graph.get_shutdown_order()
    
    def activate_all(self) -> Dict[str, bool]:
        results = {}
        load_order = self.get_load_order()
        
        for name in load_order:
            if name in self._scripts:
                script_info = self._scripts[name]
                if script_info.metadata.auto_activate:
                    results[name] = self.activate(name)
        
        return results
    
    def deactivate_all(self) -> Dict[str, bool]:
        results = {}
        shutdown_order = self.get_shutdown_order()
        
        for name in shutdown_order:
            if name in self._scripts:
                results[name] = self.deactivate(name)
        
        return results
    
    def execute(
        self,
        name: str,
        *args,
        **kwargs
    ) -> Any:
        script_info = self._scripts.get(name)
        if not script_info:
            raise ValueError(f"脚本未注册: {name}")

        caller_name = self._current_caller or "system"
        caller_type = self._current_caller_type

        call_id = self._call_chain_tracker.start_call(
            caller_type=caller_type,
            caller_name=caller_name,
            callee_type="script",
            callee_name=name,
            args=args,
            kwargs=kwargs
        )

        state_id = self._call_state_recorder.start_call(
            caller=caller_name,
            callee=name,
            caller_type=caller_type,
            callee_type="script"
        )

        self._execute_hooks('pre_execute', name, args, kwargs)

        try:
            if script_info.state != ScriptState.ACTIVE:
                if not self.activate(name):
                    raise RuntimeError(f"无法激活脚本: {name}")

            module = script_info.module
            if not module:
                raise RuntimeError(f"脚本模块未加载: {name}")

            entry_point = script_info.metadata.entry_point
            if not hasattr(module, entry_point):
                raise AttributeError(f"脚本缺少入口点: {entry_point}")

            func = getattr(module, entry_point)

            old_caller = self._current_caller
            old_caller_type = self._current_caller_type
            self._current_caller = name
            self._current_caller_type = "script"

            try:
                result = func(*args, **kwargs)
                script_info.last_execution = datetime.now()
                script_info.execution_count += 1

                self._call_chain_tracker.end_call(call_id, CallStatus.SUCCESS, result)
                self._call_state_recorder.complete_call(state_id, result)

                self._execute_hooks('post_execute', name, result)

                return result
            finally:
                self._current_caller = old_caller
                self._current_caller_type = old_caller_type

        except Exception as e:
            script_info.error_message = str(e)
            self._call_chain_tracker.end_call(call_id, CallStatus.FAILED, error=str(e))
            self._call_state_recorder.complete_call(state_id, error=str(e))
            self._execute_hooks('on_error', name, e)
            raise

    def execute_subskill(
        self,
        name: str,
        *args,
        **kwargs
    ) -> Any:
        caller_name = self._current_caller or "system"
        caller_type = self._current_caller_type

        call_id = self._call_chain_tracker.start_call(
            caller_type=caller_type,
            caller_name=caller_name,
            callee_type="subskill",
            callee_name=name,
            args=args,
            kwargs=kwargs
        )

        state_id = self._call_state_recorder.start_call(
            caller=caller_name,
            callee=name,
            caller_type=caller_type,
            callee_type="subskill"
        )

        try:
            old_caller = self._current_caller
            old_caller_type = self._current_caller_type
            self._current_caller = name
            self._current_caller_type = "subskill"

            try:
                result = self._subskill_adapter.execute_subskill(name, *args, **kwargs)
                self._call_chain_tracker.end_call(call_id, CallStatus.SUCCESS, result)
                self._call_state_recorder.complete_call(state_id, result)
                return result
            finally:
                self._current_caller = old_caller
                self._current_caller_type = old_caller_type

        except Exception as e:
            self._call_chain_tracker.end_call(call_id, CallStatus.FAILED, error=str(e))
            self._call_state_recorder.complete_call(state_id, error=str(e))
            raise

    def execute_unified(
        self,
        name: str,
        entity_type: str = "auto",
        *args,
        **kwargs
    ) -> Any:
        if entity_type == "auto":
            if name in self._scripts:
                entity_type = "script"
            else:
                entity_type = "subskill"

        if entity_type == "script":
            return self.execute(name, *args, **kwargs)
        elif entity_type == "subskill":
            return self.execute_subskill(name, *args, **kwargs)
        else:
            raise ValueError(f"未知的实体类型: {entity_type}")

    def get_subskill_guidance(
        self,
        subskill_name: str,
        topic: str
    ) -> Optional[str]:
        return self._subskill_adapter.get_subskill_guidance(subskill_name, topic)

    def register_subskill(
        self,
        subskill_name: str
    ) -> bool:
        return self._subskill_adapter.register_subskill_as_script(
            subskill_name,
            registry=self
        )

    def get_call_chain_tracker(self) -> CallChainTracker:
        return self._call_chain_tracker

    def get_call_state_recorder(self) -> CallStateRecorder:
        return self._call_state_recorder

    def get_call_chain(self, limit: int = 100) -> List[CallChainNode]:
        return self._call_chain_tracker.get_call_chain(limit)

    def get_call_statistics(self) -> Dict[str, Any]:
        return {
            "call_chain": self._call_chain_tracker.get_statistics(),
            "call_state": self._call_state_recorder.get_statistics()
        }

    def export_call_chain(self, format: str = "json") -> str:
        return self._call_chain_tracker.export_call_chain(format)

    def get_active_calls(self) -> List[CallState]:
        return self._call_state_recorder.get_active_calls()

    def get_call_history(self, limit: int = 100) -> List[CallState]:
        return self._call_state_recorder.get_history(limit)
    
    def add_hook(self, event: str, callback: Callable) -> None:
        if event in self._hooks:
            self._hooks[event].append(callback)
    
    def remove_hook(self, event: str, callback: Callable) -> bool:
        if event in self._hooks and callback in self._hooks[event]:
            self._hooks[event].remove(callback)
            return True
        return False
    
    def _execute_hooks(self, event: str, *args, **kwargs) -> None:
        if event in self._hooks:
            for callback in self._hooks[event]:
                try:
                    callback(*args, **kwargs)
                except Exception:
                    pass
    
    def set_config(self, name: str, config: Dict[str, Any]) -> bool:
        if name not in self._scripts:
            return False
        
        self._config[name] = config
        return True
    
    def get_config(self, name: str) -> Dict[str, Any]:
        return self._config.get(name, {})
    
    def validate_config(self, name: str, config: Dict[str, Any]) -> bool:
        script_info = self._scripts.get(name)
        if not script_info:
            return False
        
        schema = script_info.metadata.config_schema
        if not schema:
            return True
        
        return self._validate_against_schema(config, schema)
    
    def _validate_against_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        if not schema:
            return True
        
        required = schema.get('required', [])
        properties = schema.get('properties', {})
        
        for field in required:
            if field not in data:
                return False
        
        for key, value in data.items():
            if key in properties:
                prop_schema = properties[key]
                prop_type = prop_schema.get('type')
                
                if prop_type == 'string' and not isinstance(value, str):
                    return False
                elif prop_type == 'number' and not isinstance(value, (int, float)):
                    return False
                elif prop_type == 'boolean' and not isinstance(value, bool):
                    return False
                elif prop_type == 'array' and not isinstance(value, list):
                    return False
                elif prop_type == 'object' and not isinstance(value, dict):
                    return False
        
        return True
    
    def export_registry(self, output_path: Path) -> bool:
        try:
            data = {
                "exported_at": datetime.now().isoformat(),
                "scripts": {
                    name: info.to_dict()
                    for name, info in self._scripts.items()
                },
                "dependency_graph": self._dependency_graph.to_dict(),
                "config": self._config
            }
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception:
            return False
    
    def import_registry(self, input_path: Path) -> bool:
        try:
            input_path = Path(input_path)
            
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for name, script_data in data.get('scripts', {}).items():
                metadata = ScriptMetadata.from_dict(script_data['metadata'])
                script_info = ScriptInfo(
                    metadata=metadata,
                    path=Path(script_data['path']),
                    state=ScriptState[script_data['state']]
                )
                self._scripts[name] = script_info
                self._dependency_graph.add_script(
                    name,
                    metadata.dependencies
                )
            
            self._config = data.get('config', {})
            
            return True
        except Exception:
            return False
    
    def get_status_report(self) -> Dict[str, Any]:
        state_counts = {}
        for state in ScriptState:
            state_counts[state.name] = len(self.get_scripts_by_state(state))
        
        category_counts = {}
        for category in ScriptCategory:
            category_counts[category.value] = len(self.get_scripts_by_category(category))
        
        cycles = self._dependency_graph.detect_cycles()
        
        return {
            "generated_at": datetime.now().isoformat(),
            "total_scripts": len(self._scripts),
            "state_summary": state_counts,
            "category_summary": category_counts,
            "dependency_cycles": cycles,
            "load_order": self.get_load_order(),
            "active_scripts": [name for name, info in self._scripts.items() if info.state == ScriptState.ACTIVE]
        }


_global_registry: Optional[ScriptRegistry] = None


def get_registry(base_path: Path = None) -> ScriptRegistry:
    global _global_registry
    if _global_registry is None:
        _global_registry = ScriptRegistry(base_path)
    return _global_registry


def register_script(
    name: str,
    version: str = "1.0.0",
    description: str = "",
    category: ScriptCategory = ScriptCategory.UTILITY,
    dependencies: List[str] = None,
    **kwargs
) -> bool:
    return get_registry().register(
        name=name,
        version=version,
        description=description,
        category=category,
        dependencies=dependencies,
        **kwargs
    )


def script_decorator(
    name: str = None,
    version: str = "1.0.0",
    description: str = "",
    category: ScriptCategory = ScriptCategory.UTILITY,
    dependencies: List[str] = None
):
    def decorator(cls):
        script_name = name or cls.__name__
        registry = get_registry()
        registry.register(
            name=script_name,
            version=version,
            description=description or cls.__doc__ or "",
            category=category,
            dependencies=dependencies
        )
        return cls
    return decorator


def execute_script(name: str, *args, **kwargs) -> Any:
    return get_registry().execute(name, *args, **kwargs)


def execute_subskill(name: str, *args, **kwargs) -> Any:
    return get_registry().execute_subskill(name, *args, **kwargs)


def execute_unified(name: str, entity_type: str = "auto", *args, **kwargs) -> Any:
    return get_registry().execute_unified(name, entity_type, *args, **kwargs)


def get_subskill_guidance(subskill_name: str, topic: str) -> Optional[str]:
    return get_registry().get_subskill_guidance(subskill_name, topic)


def register_subskill_as_script(subskill_name: str) -> bool:
    return get_registry().register_subskill(subskill_name)


def get_call_chain(limit: int = 100) -> List[CallChainNode]:
    return get_registry().get_call_chain(limit)


def get_call_statistics() -> Dict[str, Any]:
    return get_registry().get_call_statistics()


def export_call_chain(format: str = "json") -> str:
    return get_registry().export_call_chain(format)


def get_active_calls() -> List[CallState]:
    return get_registry().get_active_calls()


def get_call_history(limit: int = 100) -> List[CallState]:
    return get_registry().get_call_history(limit)


def create_call_chain_tracker(max_history: int = 1000) -> CallChainTracker:
    return CallChainTracker(max_history)


def create_call_state_recorder(max_history: int = 500) -> CallStateRecorder:
    return CallStateRecorder(max_history)
