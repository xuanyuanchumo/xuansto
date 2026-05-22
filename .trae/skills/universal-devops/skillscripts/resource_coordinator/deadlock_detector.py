"""
死锁检测器模块 - 基于Wait-for-Graph的死锁检测与恢复系统

核心算法:
- Wait-for-Graph (WFG) 构建: 将资源等待关系建模为有向图
- DFS循环检测: 深度优先搜索识别图中的环
- 优先级恢复策略: 选择环中最低优先级Agent进行牺牲

特性:
- 周期性自动检测（默认10s间隔）
- 可配置的检测阈值和恢复策略
- 完整的审计日志与预防建议
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple


class ResolutionStrategy(Enum):
    """死锁恢复策略"""
    FORCE_RELEASE_LOWEST_PRIORITY = "force_release_lowest_priority"
    FORCE_RELEASE_OLDEST = "force_release_oldest"
    FORCE_RELEASE_MOST_HOLDER = "force_release_most_holder"


@dataclass
class WaitForGraphNode:
    """等待图节点"""
    agent_id: str
    waiting_for: str = ""
    holding: List[str] = field(default_factory=list)
    priority: int = 5

    def __hash__(self) -> int:
        return hash(self.agent_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WaitForGraphNode):
            return False
        return self.agent_id == other.agent_id


@dataclass
class DeadlockCycle:
    """检测到的死锁环"""
    cycle_agents: List[str]
    cycle_resources: List[str]
    detected_at: datetime = field(default_factory=datetime.now)
    resolution_strategy: str = ResolutionStrategy.FORCE_RELEASE_LOWEST_PRIORITY.value
    victim_agent: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_success: bool = False


@dataclass
class DeadlockResolution:
    """死锁恢复操作记录"""
    cycle: DeadlockCycle
    action_taken: str
    released_locks: List[str]
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PreventionSuggestion:
    """预防建议"""
    suggestion_id: str
    category: str
    title: str
    description: str
    severity: str  # low/medium/high/critical
    confidence: float  # 0.0 - 1.0
    created_at: datetime = field(default_factory=datetime.now)


class DeadlockDetector:
    """
    死锁检测器 - 并发安全守护者

    功能:
    - 实时构建Wait-for-Graph
    - DFS算法检测环路
    - 自动或手动的死锁恢复
    - 历史数据分析与预防建议
    - 完整审计追踪

    使用示例:
        >>> detector = DeadlockDetector(detection_interval=10.0)
        >>> detector.start_background_detection()
        >>> cycles = detector.detect_deadlocks()
        >>> if cycles:
        ...     resolution = detector.resolve_deadlock(cycles[0])
        >>> detector.stop_background_detection()
    """

    def __init__(
        self,
        detection_interval: float = 10.0,
        default_resolution: ResolutionStrategy = ResolutionStrategy.FORCE_RELEASE_LOWEST_PRIORITY,
        max_history: int = 1000,
    ) -> None:
        self._detection_interval = detection_interval
        self._default_resolution = default_resolution
        self._max_history = max_history

        self._wfg_nodes: Dict[str, WaitForGraphNode] = {}
        self._wfg_edges: Dict[str, Set[str]] = defaultdict(set)  # agent -> set of agents it waits for
        self._resource_holders: Dict[str, Set[str]] = defaultdict(set)  # resource -> agents holding it
        self._agent_priorities: Dict[str, int] = {}

        self._detected_cycles: List[DeadlockCycle] = []
        self._resolution_history: List[DeadlockResolution] = []
        self._prevention_suggestions: List[PreventionSuggestion] = []

        self._lock = threading.RLock()
        self._detection_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._is_running = False
        self._detection_count = 0
        self._total_cycles_found = 0

    def update_wait_for_graph(
        self,
        agent_id: str,
        waiting_for_resource: str | None = None,
        holding_resources: List[str] | None = None,
        priority: int = 5,
    ) -> None:
        """
        更新等待图节点信息

        Args:
            agent_id: Agent标识
            waiting_for_resource: 正在等待的资源ID，None表示不等待
            holding_resources: 当前持有的资源列表
            priority: Agent优先级(1-10)
        """
        with self._lock:
            node = WaitForGraphNode(
                agent_id=agent_id,
                waiting_for=waiting_for_resource or "",
                holding=holding_resources or [],
                priority=priority,
            )
            self._wfg_nodes[agent_id] = node
            self._agent_priorities[agent_id] = priority

            old_edges = self._wfg_edges.get(agent_id, set())
            self._wfg_edges[agent_id] = set()

            if waiting_for_resource:
                holders = self._resource_holders.get(waiting_for_resource, set())
                for holder in holders:
                    if holder != agent_id:
                        self._wfg_edges[agent_id].add(holder)

            for res in (holding_resources or []):
                self._resource_holders[res].add(agent_id)

            removed_holds = old_holding - set(holding_resources or [])
            for res in removed_holds:
                if res in self._resource_holders:
                    self._resource_holders[res].discard(agent_id)
                    if not self._resource_holders[res]:
                        del self._resource_holders[res]

    def remove_agent(self, agent_id: str) -> None:
        """从等待图中移除Agent"""
        with self._lock:
            if agent_id in self._wfg_nodes:
                node = self._wfg_nodes[agent_id]
                for res in node.holding:
                    if res in self._resource_holders:
                        self._resource_holders[res].discard(agent_id)
                        if not self._resource_holders[res]:
                            del self._resource_holders[res]

                del self._wfg_nodes[agent_id]
                if agent_id in self._wfg_edges:
                    del self._wfg_edges[agent_id]
                if agent_id in self._agent_priorities:
                    del self._agent_priorities[agent_id]

                for other_agent in list(self._wfg_edges.keys()):
                    self._wfg_edges[other_agent].discard(agent_id)

    def detect_deadlocks(self) -> List[DeadlockCycle]:
        """
        执行死锁检测

        Returns:
            检测到的所有死锁环列表
        """
        with self._lock:
            self._detection_count += 1
            cycles = self._find_all_cycles()

            new_cycles = []
            for cycle_agents in cycles:
                resources = self._get_cycle_resources(cycle_agents)
                existing = any(
                    set(c.cycle_agents) == set(cycle_agents)
                    for c in self._detected_cycles[-50:]
                )
                if not existing:
                    cycle = DeadlockCycle(
                        cycle_agents=list(cycle_agents),
                        cycle_resources=resources,
                        resolution_strategy=self._default_resolution.value,
                    )
                    self._detected_cycles.append(cycle)
                    new_cycles.append(cycle)
                    self._total_cycles_found += 1

            if len(self._detected_cycles) > self._max_history:
                self._detected_cycles = self._detected_cycles[-self._max_history // 2:]

            return new_cycles

    def _find_all_cycles(self) -> List[List[str]]:
        """
        使用DFS查找所有环路（核心算法）

        算法说明:
        1. 对每个未访问节点启动DFS
        2. 维护当前路径上的节点栈
        3. 当遇到已在路径中的节点时，发现环
        4. 回溯收集完整环路

        Returns:
            所有发现的环路列表（每个环路是Agent ID列表）
        """
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []
        all_cycles: List[List[str]] = []

        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self._wfg_edges.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    if len(cycle) > 2:
                        normalized_cycle = self._normalize_cycle(cycle[:-1])
                        if not any(set(nc) == set(normalized_cycle) for nc in all_cycles):
                            all_cycles.append(normalized_cycle)

            path.pop()
            rec_stack.discard(node)

        for node in list(self._wfg_nodes.keys()):
            if node not in visited:
                dfs(node)

        return all_cycles

    @staticmethod
    def _normalize_cycle(cycle: List[str]) -> List[str:
        """规范化环路：以最小元素为起点，保持方向一致"""
        if not cycle:
            return cycle

        min_idx = cycle.index(min(cycle))
        normalized = cycle[min_idx:] + cycle[:min_idx]
        return normalized

    def _get_cycle_resources(self, cycle_agents: List[str]) -> List[str]:
        """获取环路中涉及的所有资源"""
        resources: Set[str] = set()
        for agent_id in cycle_agents:
            node = self._wfg_nodes.get(agent_id)
            if node:
                resources.update(node.holding)
                if node.waiting_for:
                    resources.add(node.waiting_for)
        return list(resources)

    def resolve_deadlock(
        self,
        cycle: DeadlockCycle,
        strategy: ResolutionStrategy | None = None,
        get_agent_priority_callback=None,
        force_release_callback=None,
    ) -> DeadlockResolution:
        """
        执行死锁恢复

        Args:
            cycle: 要解决的死锁环
            strategy: 恢复策略，None使用默认策略
            get_agent_priority_callback: 获取Agent优先级的回调函数
            force_release_callback: 强制释放锁的回调函数

        Returns:
            DeadlockResolution包含恢复详情
        """
        if strategy is None:
            strategy = self._default_resolution

        victim = self._select_victim(cycle, strategy, get_agent_priority_callback)
        cycle.victim_agent = victim

        released_locks: List[str] = []
        success = False
        action = f"Selected victim: {victim} using {strategy.value}"

        if victim and force_release_callback:
            try:
                released_locks = force_release_callback(victim)
                success = True
                action += f" | Released {len(released_locks)} locks"
            except Exception as e:
                action += f" | Error: {str(e)}"
                success = False

        cycle.resolved_at = datetime.now()
        cycle.resolution_success = success

        resolution = DeadlockResolution(
            cycle=cycle,
            action_taken=action,
            released_locks=released_locks,
            success=success,
        )

        with self._lock:
            self._resolution_history.append(resolution)
            if len(self._resolution_history) > self._max_history:
                self._resolution_history = self._resolution_history[-self._max_history // 2:]

        return resolution

    def _select_victim(
        self,
        cycle: DeadlockCycle,
        strategy: ResolutionStrategy,
        priority_callback=None,
    ) -> Optional[str]:
        """
        选择牺牲者（根据策略）

        Args:
            cycle: 死锁环
            strategy: 选择策略
            priority_callback: 获取优先级的回调

        Returns:
            被选中的Agent ID
        """
        if strategy == ResolutionStrategy.FORCE_RELEASE_LOWEST_PRIORITY:
            priorities = {}
            for agent_id in cycle.cycle_agents:
                if priority_callback:
                    try:
                        priorities[agent_id] = priority_callback(agent_id)
                    except Exception:
                        priorities[agent_id] = self._agent_priorities.get(agent_id, 5)
                else:
                    priorities[agent_id] = self._agent_priorities.get(agent_id, 5)

            return min(priorities.keys(), key=lambda a: priorities[a])

        elif strategy == ResolutionStrategy.FORCE_RELEASE_OLDEST:
            oldest = None
            oldest_time = None
            for agent_id in cycle.cycle_agents:
                node = self._wfg_nodes.get(agent_id)
                if node and (oldest_time is None):
                    oldest = agent_id
            return oldest or (cycle.cycle_agents[0] if cycle.cycle_agents else None)

        elif strategy == ResolutionStrategy.FORCE_RELEASE_MOST_HOLDER:
            max_holds = -1
            victim = None
            for agent_id in cycle.cycle_agents:
                node = self._wfg_nodes.get(agent_id)
                hold_count = len(node.holding) if node else 0
                if hold_count > max_holds:
                    max_holds = hold_count
                    victim = agent_id
            return victim

        return cycle.cycle_agents[0] if cycle.cycle_agents else None

    def start_background_detection(self) -> None:
        """启动后台周期性检测线程"""
        if self._is_running:
            return

        self._stop_event.clear()
        self._is_running = True
        self._detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
        self._detection_thread.start()

    def stop_background_detection(self) -> None:
        """停止后台检测线程"""
        self._stop_event.set()
        self._is_running = False
        if self._detection_thread and self._detection_thread.is_alive():
            self._detection_thread.join(timeout=5.0)

    def _detection_loop(self) -> None:
        """后台检测主循环"""
        while not self._stop_event.is_set():
            try:
                cycles = self.detect_deadlocks()
                if cycles:
                    self._generate_prevention_suggestions(cycles)
            except Exception:
                pass

            self._stop_event.wait(timeout=self._detection_interval)

    def generate_prevention_advice(self) -> List[PreventionSuggestion]:
        """
        基于历史数据生成预防建议

        Returns:
            预防建议列表
        """
        suggestions = []

        with self._lock:
            recent_cycles = self._detected_cycles[-20:]
            recent_resolutions = self._resolution_history[-20:]

        if len(recent_cycles) >= 5:
            suggestions.append(PreventionSuggestion(
                suggestion_id=f"prev_{len(suggestions)}",
                category="frequency",
                title="高频死锁警告",
                description=f"最近检测到{len(recent_cycles)}次死锁，建议审查资源获取顺序",
                severity="high",
                confidence=min(1.0, len(recent_cycles) / 10.0),
            ))

        failed_resolutions = [r for r in recent_resolutions if not r.success]
        if len(failed_resolutions) >= 3:
            suggestions.append(PreventionSuggestion(
                suggestion_id=f"prev_{len(suggestions)}",
                category="recovery",
                title="恢复失败率过高",
                description=f"最近{len(failed_resolutions)}次恢复失败，建议检查强制释放回调",
                severity="critical",
                confidence=min(1.0, len(failed_resolutions) / 5.0),
            ))

        involved_agents: Dict[str, int] = defaultdict(int)
        for cycle in recent_cycles:
            for agent_id in cycle.cycle_agents:
                involved_agents[agent_id] += 1

        top_offenders = sorted(involved_agents.items(), key=lambda x: -x[1])[:3]
        if top_offenders and top_offenders[0][1] >= 3:
            offender_ids = ", ".join(a[0] for a in top_offenders)
            suggestions.append(PreventionSuggestion(
                suggestion_id=f"prev_{len(suggestions)}",
                category="agents",
                title="高风险Agent识别",
                description=f"以下Agent频繁参与死锁: {offender_ids}，建议优化其资源请求模式",
                severity="medium",
                confidence=0.8,
            ))

        with self._lock:
            self._prevention_suggestions.extend(suggestions)
            if len(self._prevention_suggestions) > 200:
                self._prevention_suggestions = self._prevention_suggestions[-100:]

        return suggestions

    def _generate_prevention_suggestions(self, cycles: List[DeadlockCycle]) -> None:
        """为新检测到的死锁生成即时建议"""
        for cycle in cycles:
            if len(cycle.cycle_agents) >= 4:
                suggestion = PreventionSuggestion(
                    suggestion_id=f"auto_{datetime.now().timestamp()}",
                    category="complexity",
                    title="复杂死锁环检测",
                    description=f"发现包含{len(cycle.cycle_agents)}个Agent的大型死锁环，建议拆分任务粒度",
                    severity="high",
                    confidence=0.9,
                )
                with self._lock:
                    self._prevention_suggestions.append(suggestion)

    def get_wait_for_graph(self) -> Dict[str, any]:
        """获取当前等待图的快照"""
        with self._lock:
            return {
                "nodes": {
                    aid: {
                        "waiting_for": n.waiting_for,
                        "holding": n.holding,
                        "priority": n.priority,
                    }
                    for aid, n in self._wfg_nodes.items()
                },
                "edges": {
                    aid: list(waiting_for)
                    for aid, waiting_for in self._wfg_edges.items()
                },
                "node_count": len(self._wfg_nodes),
                "edge_count": sum(len(v) for v in self._wfg_edges.values()),
            }

    def get_detected_cycles(self, limit: int = 50) -> List[DeadlockCycle]:
        """获取历史检测到的死锁环"""
        with self._lock:
            return list(self._detected_cycles[-limit:])

    def get_resolution_history(self, limit: int = 50) -> List[DeadlockResolution]:
        """获取恢复历史"""
        with self._lock:
            return list(self._resolution_history[-limit:])

    def get_statistics(self) -> Dict[str, any]:
        """获取检测器统计信息"""
        with self._lock:
            successful_resolutions = sum(1 for r in self._resolution_history if r.success)
            total_resolutions = len(self._resolution_history)

            return {
                "detection_count": self._detection_count,
                "total_cycles_found": self._total_cycles_found,
                "active_agents": len(self._wfg_nodes),
                "active_resources": len(self._resource_holders),
                "total_resolutions": total_resolutions,
                "successful_resolutions": successful_resolutions,
                "success_rate": round(successful_resolutions / max(total_resolutions, 1), 2),
                "is_running": self._is_running,
                "detection_interval": self._detection_interval,
                "pending_suggestions": len(self._prevention_suggestions),
            }

    def clear_history(self) -> None:
        """清除所有历史记录（用于测试）"""
        with self._lock:
            self._detected_cycles.clear()
            self._resolution_history.clear()
            self._prevention_suggestions.clear()
            self._detection_count = 0
            self._total_cycles_found = 0

    def __del__(self) -> None:
        self.stop_background_detection()
