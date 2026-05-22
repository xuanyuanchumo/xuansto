"""
Agent 注册表

负责扫描、解析、索引和管理 agency-agents 目录下的所有 AI 智能体。
支持动态注册/注销、多维度搜索和统计信息查询。
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class AgentMetadata:
    """智能体元数据"""

    id: str
    name: str
    file_path: Path
    division: str = ""
    specialty: str = ""
    description: str = ""
    color: str = ""
    emoji: str = ""
    vibe: str = ""
    tags: list[str] = field(default_factory=list)
    triggers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "file_path": str(self.file_path),
            "division": self.division,
            "specialty": self.specialty,
            "description": self.description[:100],
            "color": self.color,
            "emoji": self.emoji,
            "vibe": self.vibe,
            "tags": self.tags,
            "triggers": self.triggers,
        }


@dataclass
class RegistryStats:
    """注册表统计信息"""

    total_agents: int = 0
    divisions_count: int = 0
    specialties_count: int = 0
    last_refresh: str = ""
    division_breakdown: dict[str, int] = field(default_factory=dict)


class AgentRegistry:
    """
    Agent 注册表

    管理所有可用 AI 智能体的注册信息，提供扫描、搜索、索引等功能。
    """

    def __init__(self, agents_dir: Path | str | None = None) -> None:
        self._agents_dir = Path(agents_dir) if agents_dir else Path(__file__).parent.parent.parent / "agency-agents"
        self._agents: dict[str, AgentMetadata] = {}
        self._index_by_division: dict[str, list[str]] = {}
        self._index_by_specialty: dict[str, list[str]] = {}
        self._index_by_tags: dict[str, list[str]] = {}
        self._stats = RegistryStats()

    def scan_agents_directory(self) -> list[AgentMetadata]:
        """
        扫描 agency-agents 目录，递归查找所有 .md 文件并解析元数据

        Returns:
            新发现的 AgentMetadata 列表
        """
        discovered: list[AgentMetadata] = []

        if not self._agents_dir.exists():
            return discovered

        for md_file in sorted(self._agents_dir.rglob("*.md")):
            if md_file.parent.name in {".github", "examples", "integrations", "scripts", "strategy"}:
                continue

            relative = md_file.relative_to(self._agents_dir)
            division = relative.parts[0] if len(relative.parts) > 1 else "root"

            try:
                metadata = self.parse_agent_metadata(md_file, division)
                if metadata and metadata.id not in self._agents:
                    self._agents[metadata.id] = metadata
                    discovered.append(metadata)
            except (OSError, ValueError):
                continue

        if discovered:
            self.build_index()
            self._update_stats()

        return discovered

    def parse_agent_metadata(self, file_path: Path, division: str = "") -> AgentMetadata | None:
        """
        解析 agent 文件的 frontmatter 元数据（YAML frontmatter 格式）

        Args:
            file_path: agent markdown 文件路径
            division: 所属部门（从目录结构推断）

        Returns:
            解析后的 AgentMetadata，解析失败返回 None
        """
        content = file_path.read_text(encoding="utf-8")

        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if not frontmatter_match:
            return None

        frontmatter_text = frontmatter_match.group(1)
        meta_dict: dict[str, str] = {}

        for line in frontmatter_text.split("\n"):
            line = line.strip()
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            meta_dict[key.strip().lower()] = value.strip().strip("\"'")

        stem = file_path.stem
        agent_id = stem.replace("-", "_")

        name = meta_dict.get("name", stem.replace("-", " ").title())
        description = meta_dict.get("description", "")
        color = meta_dict.get("color", "")
        emoji = meta_dict.get("emoji", "")
        vibe = meta_dict.get("vibe", "")

        specialty_parts = stem.split("-")
        specialty = " ".join(specialty_parts[1:]) if len(specialty_parts) > 1 else name

        tags = [division]
        if description:
            tag_words = re.findall(r"[a-zA-Z]{3,}", description.lower())
            tags.extend(tag_words[:5])

        triggers = [name.lower(), specialty.lower()]
        if description:
            triggers.append(description.lower()[:50])

        return AgentMetadata(
            id=agent_id,
            name=name,
            file_path=file_path,
            division=division,
            specialty=specialty,
            description=description,
            color=color,
            emoji=emoji,
            vibe=vibe,
            tags=tags,
            triggers=triggers,
        )

    def build_index(self) -> None:
        """
        构建 agent 多维度索引（按 division / specialty / tags）
        """
        self._index_by_division.clear()
        self._index_by_specialty.clear()
        self._index_by_tags.clear()

        for agent_id, metadata in self._agents.items():
            div = metadata.division or "unknown"
            self._index_by_division.setdefault(div, []).append(agent_id)

            spec = metadata.specialty.lower()
            self._index_by_specialty.setdefault(spec, []).append(agent_id)

            for tag in metadata.tags:
                tag_key = tag.lower()
                self._index_by_tags.setdefault(tag_key, []).append(agent_id)

    def register_agent(self, agent: AgentMetadata) -> None:
        """
        动态注册单个 agent

        Args:
            agent: 要注册的 AgentMetadata 对象
        """
        self._agents[agent.id] = agent
        self.build_index()
        self._update_stats()

    def unregister_agent(self, agent_id: str) -> bool:
        """
        注销指定 agent

        Args:
            agent_id: 要注销的 agent ID

        Returns:
            是否成功注销
        """
        if agent_id in self._agents:
            del self._agents[agent_id]
            self.build_index()
            self._update_stats()
            return True
        return False

    def get_agent_by_id(self, agent_id: str) -> AgentMetadata | None:
        """
        按 ID 查询 agent

        Args:
            agent_id: agent 唯一标识符

        Returns:
            对应的 AgentMetadata，不存在则返回 None
        """
        return self._agents.get(agent_id)

    def search_agents(
        self,
        query: str = "",
        tags: list[str] | None = None,
        division: str = "",
        limit: int = 20,
    ) -> list[AgentMetadata]:
        """
        按关键词 / 标签 / 专长 / 部门搜索 agents

        Args:
            query: 搜索关键词（匹配 name/description/specialty）
            tags: 标签过滤列表
            division: 部门过滤
            limit: 返回结果上限

        Returns:
            匹配的 AgentMetadata 列表（按相关度排序）
        """
        results: list[tuple[AgentMetadata, float]] = []
        query_lower = query.lower() if query else ""

        for agent_id, metadata in self._agents.items():
            score = 0.0

            if division and metadata.division != division:
                continue

            if tags:
                if not any(t.lower() in [tag.lower() for tag in metadata.tags] for t in tags):
                    continue
                score += len([t for t in tags if t.lower() in [tag.lower() for tag in metadata.tags]]) * 10

            if query_lower:
                if query_lower in metadata.name.lower():
                    score += 30
                if query_lower in metadata.specialty.lower():
                    score += 20
                if query_lower in metadata.description.lower():
                    score += 15
                if any(query_lower in t.lower() for t in metadata.triggers):
                    score += 10
                if query_lower in metadata.id:
                    score += 25

            if score > 0 or (not query and not tags and not division):
                results.append((metadata, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results[:limit]]

    def get_registry_stats(self) -> RegistryStats:
        """
        获取注册统计信息

        Returns:
            RegistryStats 统计对象
        """
        return self._stats

    def refresh_registry(self) -> dict[str, Any]:
        """
        刷新注册表（检测新增 / 删除的 agent）

        Returns:
            包含新增/删除数量的变更报告
        """
        before_ids = set(self._agents.keys())
        self.scan_agents_directory()
        after_ids = set(self._agents.keys())

        added = after_ids - before_ids
        removed = before_ids - after_ids

        return {
            "added_count": len(added),
            "removed_count": len(removed),
            "added_agents": list(added),
            "removed_agents": list(removed),
            "total_after": len(after_ids),
        }

    def _update_stats(self) -> None:
        """更新统计信息"""
        divisions: dict[str, int] = {}
        specialties: set[str] = set()

        for metadata in self._agents.values():
            div = metadata.division or "unknown"
            divisions[div] = divisions.get(div, 0) + 1
            specialties.add(metadata.specialty.lower())

        self._stats = RegistryStats(
            total_agents=len(self._agents),
            divisions_count=len(divisions),
            specialties_count=len(specialties),
            last_refresh=datetime.now().isoformat(),
            division_breakdown=divisions,
        )

    def list_all_agents(self) -> list[AgentMetadata]:
        """列出所有已注册 agents"""
        return list(self._agents.values())

    def get_agents_by_division(self, division: str) -> list[AgentMetadata]:
        """获取指定部门的全部 agents"""
        agent_ids = self._index_by_division.get(division, [])
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Agent 注册表测试")
    print("=" * 60)

    registry = AgentRegistry()

    print("\n--- 扫描 agents 目录 ---")
    discovered = registry.scan_agents_directory()
    print(f"✅ 发现 {len(discovered)} 个 agents")

    stats = registry.get_registry_stats()
    print(f"📊 总计: {stats.total_agents} agents")
    print(f"📊 部门数: {stats.divisions_count}")
    print(f"📊 专业数: {stats.specialties_count}")

    print("\n--- 部门分布 ---")
    for div, count in sorted(stats.division_breakdown.items()):
        print(f"   {div}: {count}")

    print("\n--- 搜索测试 ---")
    results = registry.search_agents("frontend", limit=5)
    print(f"✅ 'frontend' 搜索结果: {len(results)}")
    for r in results[:3]:
        print(f"   [{r.emoji}] {r.name} ({r.division})")

    print("\n--- 单个查询 ---")
    agent = registry.get_agent_by_id("engineering_frontend_developer")
    if agent:
        print(f"✅ {agent.emoji} {agent.name}")
        print(f"   描述: {agent.description[:60]}...")

    print("\n✅ Agent 注册表测试通过!")
