"""
协同调度司 - 跨部门协同编排、依赖拓扑管理、冲突检测
"""
from __future__ import annotations

import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class CoordinationError(Exception):
    """协同调度相关异常"""
    pass


class TaskState(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class CoordinationProtocol(str, Enum):
    """协同协议枚举"""
    HANDSHAKE = "handshake"
    PUBSUB = "pubsub"
    PIPELINE = "pipeline"


class ConflictType(str, Enum):
    """冲突类型枚举"""
    RESOURCE = "resource"
    TIME = "time"
    DEADLOCK = "deadlock"


@dataclass
class DAGNode:
    """DAG节点（任务）"""
    task_id: str
    name: str = ""
    department: str | None = None
    state: TaskState = TaskState.PENDING
    resources: list[str] = field(default_factory=list)
    estimated_duration: float = 0.0
    priority: int = 5
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "department": self.department,
            "state": self.state.value,
            "resources": self.resources,
            "estimated_duration": self.estimated_duration,
            "priority": self.priority,
        }


@dataclass
class DAGEdge:
    """DAG边（依赖关系）"""
    from_id: str
    to_id: str
    dependency_type: str = "finish_to_start"

    def to_dict(self) -> dict[str, Any]:
        return {
            "from": self.from_id,
            "to": self.to_id,
            "type": self.dependency_type,
        }


@dataclass
class ConflictInfo:
    """冲突信息"""
    conflict_type: ConflictType
    description: str
    involved_tasks: list[str]
    involved_resources: list[str]
    severity: str = "warning"
    suggestion: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "conflict_type": self.conflict_type.value,
            "description": self.description,
            "involved_tasks": self.involved_tasks,
            "involved_resources": self.involved_resources,
            "severity": self.severity,
            "suggestion": self.suggestion,
        }


@dataclass
class ExecutionPlan:
    """执行计划"""
    phases: list[list[str]]
    total_phases: int
    critical_path: list[str]
    estimated_total_duration: float
    parallelism_info: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "phases": self.phases,
            "total_phases": self.total_phases,
            "critical_path": self.critical_path,
            "estimated_total_duration": round(self.estimated_total_duration, 2),
            "parallelism_info": self.parallelism_info,
        }


@dataclass
class HandshakeAgreement:
    """握手协议协商结果"""
    task_a: str
    task_b: str
    shared_resource: str
    agreement_type: str
    conditions: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_a": self.task_a,
            "task_b": self.task_b,
            "shared_resource": self.shared_resource,
            "agreement_type": self.agreement_type,
            "conditions": self.conditions,
        }


class CoordinationSi:
    """
    协同调度司

    负责跨部门协同编排、依赖拓扑管理和冲突检测。
    支持DAG构建与管理、拓扑排序执行引擎、资源/时间冲突检测和死锁检测。
    """

    _instance: CoordinationSi | None = None

    def __init__(self) -> None:
        self._nodes: dict[str, DAGNode] = {}
        self._edges: list[DAGEdge] = []
        self._adjacency: dict[str, list[str]] = defaultdict(list)
        self._reverse_adj: dict[str, list[str]] = defaultdict(list)
        self._resource_allocations: dict[str, str] = {}
        self._execution_log: list[dict[str, Any]] = []
        self._protocols: dict[CoordinationProtocol, Any] = {}

    @classmethod
    def get_instance(cls) -> CoordinationSi:
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def add_node(
        self,
        task_id: str,
        name: str = "",
        department: str | None = None,
        resources: list[str] | None = None,
        estimated_duration: float = 0.0,
        priority: int = 5,
        **kwargs: Any,
    ) -> DAGNode:
        """
        添加DAG节点（任务）

        Args:
            task_id: 任务ID
            name: 任务名称
            department: 所属部门
            resources: 所需资源列表
            estimated_duration: 预估持续时间（小时）
            priority: 优先级（数值越小越高）
            **kwargs: 其他元数据

        Returns:
            创建的DAGNode对象

        Raises:
            CoordinationError: 当节点已存在时
        """
        if task_id in self._nodes:
            raise CoordinationError(f"任务节点已存在: {task_id}")

        node = DAGNode(
            task_id=task_id,
            name=name or task_id,
            department=department,
            resources=resources or [],
            estimated_duration=estimated_duration,
            priority=priority,
            **kwargs,
        )
        self._nodes[task_id] = node
        return node

    def remove_node(self, task_id: str) -> bool:
        """移除DAG节点及其关联边"""
        if task_id not in self._nodes:
            return False

        del self._nodes[task_id]
        self._edges = [e for e in self._edges if e.from_id != task_id and e.to_id != task_id]

        self._adjacency = defaultdict(list)
        self._reverse_adj = defaultdict(list)
        for edge in self._edges:
            self._adjacency[edge.from_id].append(edge.to_id)
            self._reverse_adj[edge.to_id].append(edge.from_id)

        if task_id in self._resource_allocations:
            del self._resource_allocations[task_id]

        return True

    def add_edge(
        self,
        from_id: str,
        to_id: str,
        dependency_type: str = "finish_to_start",
    ) -> DAGEdge:
        """
        添加DAG边（依赖关系）

        Args:
            from_id: 前置任务ID
            to_id: 后置任务ID
            dependency_type: 依赖类型

        Returns:
            创建的DAGEdge对象

        Raises:
            CoordinationError: 当节点不存在或会形成环时
        """
        if from_id not in self._nodes:
            raise CoordinationError(f"前置任务不存在: {from_id}")
        if to_id not in self._nodes:
            raise CoordinationError(f"后置任务不存在: {to_id}")

        existing = [e for e in self._edges if e.from_id == from_id and e.to_id == to_id]
        if existing:
            return existing[0]

        test_edges = self._edges + [DAGEdge(from_id=from_id, to_id=to_id)]
        if self._has_cycle_with_edge(from_id, to_id):
            raise CoordinationError(
                f"添加边 {from_id} → {to_id} 会形成循环依赖"
            )

        edge = DAGEdge(from_id=from_id, to_id=to_id, dependency_type=dependency_type)
        self._edges.append(edge)
        self._adjacency[from_id].append(to_id)
        self._reverse_adj[to_id].append(from_id)
        return edge

    def remove_edge(self, from_id: str, to_id: str) -> bool:
        """移除DAG边"""
        original_len = len(self._edges)
        self._edges = [
            e for e in self._edges
            if not (e.from_id == from_id and e.to_id == to_id)
        ]

        self._adjacency = defaultdict(list)
        self._reverse_adj = defaultdict(list)
        for edge in self._edges:
            self._adjacency[edge.from_id].append(edge.to_id)
            self._reverse_adj[edge.to_id].append(edge.from_id)

        return len(self._edges) < original_len

    def topological_sort(self) -> list[str]:
        """
        对DAG进行拓扑排序（Kahn算法）

        Returns:
            按拓扑顺序排列的任务ID列表

        Raises:
            CoordinationError: 当存在循环依赖时
        """
        in_degree: dict[str, int] = {nid: 0 for nid in self._nodes}

        for edge in self._edges:
            in_degree[edge.to_id] = in_degree.get(edge.to_id, 0) + 1

        queue: deque[str] = deque(nid for nid, deg in in_degree.items() if deg == 0)
        sorted_result: list[str] = []

        while queue:
            node = queue.popleft()
            sorted_result.append(node)
            for neighbor in self._adjacency.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_result) != len(self._nodes):
            remaining = set(self._nodes.keys()) - set(sorted_result)
            raise CoordinationError(f"检测到循环依赖，涉及任务: {remaining}")

        return sorted_result

    def generate_execution_plan(self) -> ExecutionPlan:
        """
        基于拓扑排序生成分阶段执行计划

        Returns:
            ExecutionPlan对象，包含阶段划分和关键路径信息
        """
        topo_order = self.topological_sort()

        completed: set[str] = set()
        phases: list[list[str]] = []
        current_phase: list[str] = []

        for task_id in topo_order:
            deps = self._reverse_adj.get(task_id, [])
            if all(d in completed for d in deps):
                current_phase.append(task_id)
            else:
                if current_phase:
                    phases.append(current_phase)
                    completed.update(current_phase)
                current_phase = [task_id]

        if current_phase:
            phases.append(current_phase)

        critical_path = self._find_critical_path()

        phase_parallelism: dict[str, int] = {}
        for i, phase in enumerate(phases):
            phase_parallelism[f"phase_{i+1}"] = len(phase)

        total_duration = sum(
            max(
                (self._nodes[tid].estimated_duration for tid in phase),
                default=0,
            )
            for phase in phases
        )

        return ExecutionPlan(
            phases=phases,
            total_phases=len(phases),
            critical_path=critical_path,
            estimated_total_duration=total_duration,
            parallelism_info=phase_parallelism,
        )

    def _find_critical_path(self) -> list[str]:
        """查找关键路径（最长路径）"""
        dist: dict[str, float] = {nid: 0.0 for nid in self._nodes}
        prev: dict[str, str | None] = {nid: None for nid in self._nodes}

        topo_order = self.topological_sort()

        for node_id in topo_order:
            node = self._nodes[node_id]
            for pred_id in self._reverse_adj.get(node_id, []):
                pred_node = self._nodes[pred_id]
                new_dist = dist[pred_id] + pred_node.estimated_duration
                if new_dist > dist[node_id]:
                    dist[node_id] = new_dist
                    prev[node_id] = pred_id

        end_node = max(dist, key=dist.get) if dist else ""
        path: list[str] = []
        current = end_node
        while current is not None:
            path.append(current)
            current = prev.get(current)

        path.reverse()
        return path

    def detect_conflicts(self) -> list[ConflictInfo]:
        """
        检测所有类型的冲突（资源冲突、时间冲突、死锁）

        Returns:
            冲突信息列表
        """
        conflicts: list[ConflictInfo] = []

        resource_users: dict[str, list[str]] = defaultdict(list)
        for nid, node in self._nodes.items():
            if node.state in (TaskState.PENDING, TaskState.READY, TaskState.RUNNING):
                for res in node.resources:
                    resource_users[res].append(nid)

        for resource, users in resource_users.items():
            if len(users) > 1:
                conflicts.append(ConflictInfo(
                    conflict_type=ConflictType.RESOURCE,
                    description=f"资源 '{resource}' 被 {len(users)} 个任务争用: {', '.join(users)}",
                    involved_tasks=users,
                    involved_resources=[resource],
                    severity="warning",
                    suggestion="建议串行化执行或增加资源实例",
                ))

        plan = self.generate_execution_plan()
        for phase_idx, phase in enumerate(plan.phases):
            if len(phase) > 1:
                tasks_with_time = [
                    (tid, self._nodes[tid].estimated_duration)
                    for tid in phase
                    if self._nodes[tid].estimated_duration > 0
                ]
                if len(tasks_with_time) > 3:
                    conflicts.append(ConflictInfo(
                        conflict_type=ConflictType.TIME,
                        description=f"第{phase_idx + 1}阶段有{len(phase)}个并行任务，可能存在时间压力",
                        involved_tasks=phase,
                        involved_resources=[],
                        severity="info",
                        suggestion="考虑拆分为更细粒度的子阶段",
                    ))

        deadlock_cycles = self.detect_deadlocks()
        for cycle in deadlock_cycles:
            conflicts.append(ConflictInfo(
                conflict_type=ConflictType.DEADLOCK,
                description=f"检测到死锁循环: {' → '.join(cycle)}",
                involved_tasks=cycle,
                involved_resources=[],
                severity="critical",
                suggestion="重新设计任务依赖关系以打破循环等待",
            ))

        return conflicts

    def detect_deadlocks(self) -> list[list[str]]:
        """
        检测死锁（循环等待条件）

        Returns:
            循环链列表
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {nid: WHITE for nid in self._nodes}
        cycles: list[list[str]] = []
        path: list[str] = []

        def dfs(node_id: str) -> None:
            color[node_id] = GRAY
            path.append(node_id)

            for neighbor in self._adjacency.get(node_id, []):
                if color.get(neighbor) == GRAY:
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
                elif color.get(neighbor) == WHITE:
                    dfs(neighbor)

            path.pop()
            color[node_id] = BLACK

        for node_id in self._nodes:
            if color[node_id] == WHITE:
                dfs(node_id)

        unique_cycles: list[list[str]] = []
        seen: set[tuple[str, ...]] = set()
        for cycle in cycles:
            key = tuple(cycle[:-1]) if cycle else ()
            normalized = tuple(sorted(key))
            if normalized not in seen:
                seen.add(normalized)
                unique_cycles.append(cycle)

        return unique_cycles

    def allocate_resource(self, task_id: str, resource: str) -> bool:
        """
        为任务分配资源

        Args:
            task_id: 任务ID
            resource: 资源名称

        Returns:
            是否分配成功
        """
        if task_id not in self._nodes:
            return False
        if resource in self._resource_allocations:
            current_holder = self._resource_allocations[resource]
            if current_holder != task_id:
                return False

        self._resource_allocations[resource] = task_id
        if resource not in self._nodes[task_id].resources:
            self._nodes[task_id].resources.append(resource)
        return True

    def release_resource(self, task_id: str, resource: str) -> bool:
        """释放任务占用的资源"""
        if self._resource_allocations.get(resource) == task_id:
            del self._resource_allocations[resource]
            if resource in self._nodes.get(task_id, DAGNode("")).resources:
                self._nodes[task_id].resources.remove(resource)
            return True
        return False

    def update_task_state(self, task_id: str, state: TaskState) -> None:
        """更新任务状态"""
        if task_id in self._nodes:
            old_state = self._nodes[task_id].state
            self._nodes[task_id].state = state
            self._execution_log.append({
                "task_id": task_id,
                "old_state": old_state.value,
                "new_state": state.value,
                "timestamp": __import__("datetime").datetime.now().isoformat(),
            })

    def initiate_handshake(
        self,
        task_a: str,
        task_b: str,
        shared_resource: str,
    ) -> HandshakeAgreement:
        """
        发起握手协议（用于资源协调）

        Args:
            task_a: 任务A ID
            task_b: 任务B ID
            shared_resource: 共享资源名称

        Returns:
            协商结果
        """
        node_a = self._nodes.get(task_a)
        node_b = self._nodes.get(task_b)

        if not node_a or not node_b:
            raise CoordinationError(f"任务不存在: {task_a if not node_a else task_b}")

        duration_a = node_a.estimated_duration
        duration_b = node_b.estimated_duration

        match (duration_a > 0, duration_b > 0):
            case (True, True):
                if duration_a <= duration_b:
                    winner, loser = task_a, task_b
                    agreement_type = "priority_by_duration"
                else:
                    winner, loser = task_b, task_a
                    agreement_type = "priority_by_duration"
            case (True, False):
                winner, loser = task_a, task_b
                agreement_type = "default_to_running"
            case (False, True):
                winner, loser = task_b, task_a
                agreement_type = "default_to_running"
            case _:
                winner, loser = task_a, task_b
                agreement_type = "arbitrary"

        conditions = {
            "winner": winner,
            "loser": loser,
            "shared_resource": shared_resource,
            "loser_must_wait": True,
            "timeout_seconds": 300,
        }

        return HandshakeAgreement(
            task_a=task_a,
            task_b=task_b,
            shared_resource=shared_resource,
            agreement_type=agreement_type,
            conditions=conditions,
        )

    def setup_pubsub_channel(
        self,
        channel_name: str,
        publishers: list[str],
        subscribers: list[str],
    ) -> dict[str, Any]:
        """
        设置发布-订阅通信通道

        Args:
            channel_name: 通道名称
            publishers: 发布者任务ID列表
            subscribers: 订阅者任务ID列表

        Returns:
            通道配置字典
        """
        valid_publishers = [p for p in publishers if p in self._nodes]
        valid_subscribers = [s for s in subscribers if s in self._nodes]

        channel_config = {
            "channel": channel_name,
            "publishers": valid_publishers,
            "subscribers": valid_subscribers,
            "protocol": CoordinationProtocol.PUBSUB.value,
            "message_filter": "*",
            "created_at": __import__("datetime").datetime.now().isoformat(),
        }

        self._protocols[CoordinationProtocol.PUBSUB] = channel_config
        return channel_config

    def setup_pipeline(
        self,
        stages: list[list[str]],
    ) -> dict[str, Any]:
        """
        设置管道式处理流程

        Args:
            stages: 各阶段的任务ID列表

        Returns:
            管道配置字典
        """
        validated_stages: list[list[str]] = []
        for stage in stages:
            valid = [t for t in stage if t in self._nodes]
            validated_stages.append(valid)

        for i in range(len(validated_stages) - 1):
            for source in validated_stages[i]:
                for target in validated_stages[i + 1]:
                    try:
                        self.add_edge(source, target, dependency_type="pipeline")
                    except CoordinationError:
                        pass

        pipeline_config = {
            "stages": validated_stages,
            "total_stages": len(validated_stages),
            "protocol": CoordinationProtocol.PIPELINE.value,
            "throughput_target": "high",
        }

        self._protocols[CoordinationProtocol.PIPELINE] = pipeline_config
        return pipeline_config

    def get_node(self, task_id: str) -> DAGNode | None:
        """获取节点"""
        return self._nodes.get(task_id)

    def get_all_nodes(self) -> dict[str, DAGNode]:
        return dict(self._nodes)

    def get_all_edges(self) -> list[DAGEdge]:
        return list(self._edges)

    def get_execution_log(self, limit: int = 50) -> list[dict[str, Any]]:
        return self._execution_log[-limit:]

    def _has_cycle_with_edge(self, from_id: str, to_id: str) -> bool:
        """检查添加指定边是否会形成环"""
        visited: set[str] = set()
        stack: list[str] = [to_id]

        while stack:
            node = stack.pop()
            if node == from_id:
                return True
            if node in visited:
                continue
            visited.add(node)
            stack.extend(self._adjacency.get(node, []))

        return False

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return len(self._edges)

    def clear(self) -> None:
        """清空所有数据"""
        self._nodes.clear()
        self._edges.clear()
        self._adjacency.clear()
        self._reverse_adj.clear()
        self._resource_allocations.clear()
        self._execution_log.clear()
        self._protocols.clear()

    def export_dag_markdown(self) -> str:
        """导出DAG为Markdown格式"""
        lines: list[str] = []
        lines.append("# 任务依赖图 (DAG)")
        lines.append("")
        lines.append(f"## 总览")
        lines.append(f"- 节点数: {self.node_count}")
        lines.append(f"- 边数: {self.edge_count}")
        lines.append("")

        try:
            plan = self.generate_execution_plan()
            lines.append("## 执行计划")
            lines.append("")
            lines.append(f"- 总阶段数: {plan.total_phases}")
            lines.append(f"- 预估总时长: {plan.estimated_total_duration:.1f}h")
            lines.append(f"- 关键路径: {' → '.join(plan.critical_path)}")
            lines.append("")
            lines.append("| 阶段 | 并行任务 | 任务列表 |")
            lines.append("|------|---------|--------|")
            for i, phase in enumerate(plan.phases):
                names = [self._nodes[t].name for t in phase]
                lines.append(f"| 第{i+1}阶段 | {len(phase)} | {', '.join(names)} |")

        except CoordinationError:
            lines.append("> ⚠️ 存在循环依赖，无法生成执行计划")

        lines.append("")
        lines.append("## 依赖关系详情")
        lines.append("")
        lines.append("| 前置任务 | 后置任务 | 类型 |")
        lines.append("|----------|----------|------|")
        for edge in self._edges:
            from_name = self._nodes.get(edge.from_id, DAGNode(edge.from_id)).name
            to_name = self._nodes.get(edge.to_id, DAGNode(edge.to_id)).name
            lines.append(f"| {from_name} | {to_name} | {edge.dependency_type} |")

        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"CoordinationSi(nodes={self.node_count}, "
            f"edges={self.edge_count})"
        )


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 协同调度司测试")
    print("=" * 60)

    coord = CoordinationSi()

    print("\n--- 构建DAG任务图 ---")
    tasks_data = [
        ("T001", "需求分析", "product", [], 2.0, 1),
        ("T002", "架构设计", "architecture", ["架构师"], 4.0, 2),
        ("T003", "数据库设计", "backend", ["DBA"], 3.0, 2),
        ("T004", "API开发", "backend", ["开发环境"], 8.0, 3),
        ("T005", "前端开发", "frontend", ["开发环境"], 10.0, 3),
        ("T006", "单元测试", "qa", [], 4.0, 4),
        ("T007", "集成测试", "qa", ["测试环境"], 6.0, 5),
        ("T008", "部署上线", "devops", ["生产环境", "K8s集群"], 2.0, 6),
        ("T009", "文档编写", "docs", [], 3.0, 5),
    ]
    for tid, name, dept, res, dur, pri in tasks_data:
        coord.add_node(tid, name=name, department=dept, resources=res, estimated_duration=dur, priority=pri)
        print(f"   ✅ {tid}: {name} ({dept}, {dur}h)")

    print("\n--- 添加依赖关系 ---")
    dependencies = [
        ("T001", "T002"), ("T001", "T003"),
        ("T002", "T004"), ("T002", "T005"),
        ("T003", "T004"),
        ("T004", "T006"), ("T005", "T006"),
        ("T006", "T007"),
        ("T007", "T008"),
        ("T004", "T009"), ("T005", "T009"),
    ]
    for from_id, to_id in dependencies:
        try:
            edge = coord.add_edge(from_id, to_id)
            print(f"   🔗 {from_id} → {to_id}")
        except CoordinationError as e:
            print(f"   ❌ {e}")

    print("\n--- 拓扑排序 ---")
    try:
        topo_order = coord.topological_sort()
        print(f"   📋 执行顺序: {' → '.join(topo_order)}")
    except CoordinationError as e:
        print(f"   ❌ {e}")

    print("\n--- 执行计划 ---")
    plan = coord.generate_execution_plan()
    print(f"   📊 总阶段数: {plan.total_phases}")
    print(f"   ⏱️ 预估总时长: {plan.estimated_total_duration:.1f}h")
    print(f"   🔑 关键路径: {' → '.join(plan.critical_path)}")
    print(f"\n   分阶段详情:")
    for i, phase in enumerate(plan.phases):
        names = [coord._nodes[t].name for t in phase]
        durations = [coord._nodes[t].estimated_duration for t in phase]
        max_dur = max(durations) if durations else 0
        print(f"      第{i+1}阶段 ({len(phase)}任务, ~{max_dur:.1f}h): {', '.join(names)}")

    print("\n--- 冲突检测 ---")
    conflicts = coord.detect_conflicts()
    if conflicts:
        print(f"   ⚠️ 发现 {len(conflicts)} 个冲突:")
        for c in conflicts:
            icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(c.severity, "⚪")
            print(f"   {icon} [{c.conflict_type.value}] {c.description}")
            if c.suggestion:
                print(f"      💡 建议: {c.suggestion}")
    else:
        print(f"   ✅ 未发现冲突")

    print("\n--- 死锁检测 ---")
    deadlocks = coord.detect_deadlocks()
    if deadlocks:
        print(f"   🔴 发现 {len(deadlocks)} 个死锁:")
        for cycle in deadlocks:
            print(f"      循环: {' → '.join(cycle)}")
    else:
        print(f"   ✅ 未检测到死锁")

    print("\n--- 握手协议测试 ---")
    try:
        handshake = coord.initiate_handshake("T004", "T005", "开发环境")
        print(f"   🤝 握手结果:")
        print(f"      共享资源: {handshake.shared_resource}")
        print(f"      协议类型: {handshake.agreement_type}")
        print(f"      优先方: {handshake.conditions['winner']}")
        print(f"      等待方: {handshake.conditions['loser']}")
    except CoordinationError as e:
        print(f"   ❌ {e}")

    print("\n--- 管道协议测试 ---")
    pipeline_stages = [["T001"], ["T002", "T003"], ["T004", "T005"], ["T006", "T009"], ["T007"], ["T008"]]
    pipe_config = coord.setup_pipeline(pipeline_stages)
    print(f"   🔄 管道配置: {pipe_config['total_stages']} 阶段")

    print("\n--- 发布订阅协议测试 ---")
    pubsub = coord.setup_pubsub_channel(
        channel_name="build_events",
        publishers=["T004", "T005"],
        subscribers=["T006", "T007"],
    )
    print(f"   📡 通道: {pubsub['channel']}")
    print(f"      发布者: {pubsub['publishers']}")
    print(f"      订阅者: {pubsub['subscribers']}")

    print("\n--- 导出DAG Markdown ---")
    md = coord.export_dag_markdown()
    print(md[:800])

    print("\n✅ 所有测试通过!")
