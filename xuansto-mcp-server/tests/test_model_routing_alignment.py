import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

REGISTRY_PATH = Path(__file__).resolve().parent.parent.parent / ".trae" / "skills" / "xuansto-skill-v2" / "agents" / "registry.yaml"
MODEL_ROUTING_PATH = Path(__file__).resolve().parent.parent.parent / ".trae" / "skills" / "xuansto-skill-v2" / "references" / "model-routing.md"


def _parse_registry_yaml() -> dict[str, str]:
    import yaml
    content = REGISTRY_PATH.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    agent_routing: dict[str, str] = {}
    for layer in data.get("layers", []):
        for agent in layer.get("agents", []):
            name = agent.get("name", "")
            routing = agent.get("model_routing", "standard")
            agent_routing[name] = routing
    return agent_routing


def _parse_model_routing_md() -> dict[str, str]:
    content = MODEL_ROUTING_PATH.read_text(encoding="utf-8")
    agent_routing: dict[str, str] = {}
    pattern = re.compile(r"\|\s*([^|]+?)\s*\|\s*(fast|standard|deep)\s*\|")
    for line in content.splitlines():
        m = pattern.match(line.strip())
        if m:
            name = m.group(1).strip()
            if name.lower() in ("agent", ""):
                continue
            agent_routing[name] = m.group(2).strip()
    return agent_routing


class TestModelRoutingAlignment:
    @pytest.fixture(autouse=True)
    def _load_data(self):
        self.registry = _parse_registry_yaml()
        self.md = _parse_model_routing_md()

    def test_all_registry_agents_in_md(self):
        missing = []
        for name, routing in self.registry.items():
            if name not in self.md:
                missing.append(name)
        assert len(missing) == 0, f"Agents in registry.yaml but missing from model-routing.md: {missing}"

    def test_all_md_agents_in_registry(self):
        extra = []
        for name in self.md:
            if name not in self.registry:
                extra.append(name)
        assert len(extra) == 0, f"Agents in model-routing.md but not in registry.yaml: {extra}"

    def test_model_routing_values_match(self):
        mismatches = []
        for name, routing in self.registry.items():
            md_routing = self.md.get(name)
            if md_routing is not None and md_routing != routing:
                mismatches.append(f"{name}: registry={routing}, md={md_routing}")
        assert len(mismatches) == 0, f"Model routing mismatches: {mismatches}"

    def test_total_agent_count(self):
        assert len(self.registry) == 57, f"Expected 57 agents in registry.yaml, got {len(self.registry)}"

    def test_routing_group_counts(self):
        from collections import Counter
        counts = Counter(self.registry.values())
        assert counts.get("fast", 0) == 10, f"Expected 10 fast agents, got {counts.get('fast', 0)}"
        assert counts.get("standard", 0) == 37, f"Expected 37 standard agents, got {counts.get('standard', 0)}"
        assert counts.get("deep", 0) == 10, f"Expected 10 deep agents, got {counts.get('deep', 0)}"

    def test_md_routing_group_counts(self):
        from collections import Counter
        counts = Counter(self.md.values())
        assert counts.get("fast", 0) == 10, f"Expected 10 fast agents in md, got {counts.get('fast', 0)}"
        assert counts.get("standard", 0) == 37, f"Expected 37 standard agents in md, got {counts.get('standard', 0)}"
        assert counts.get("deep", 0) == 10, f"Expected 10 deep agents in md, got {counts.get('deep', 0)}"
