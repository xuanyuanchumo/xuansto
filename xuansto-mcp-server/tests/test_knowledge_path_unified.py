from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


class TestKnowledgePathConfig:
    def test_knowledge_dir_under_data_dir(self):
        from xuansto_mcp.core.config import DATA_DIR, KNOWLEDGE_DIR
        assert KNOWLEDGE_DIR == DATA_DIR / "knowledge"

    def test_knowledge_general_dir_under_knowledge_dir(self):
        from xuansto_mcp.core.config import KNOWLEDGE_DIR, KNOWLEDGE_GENERAL_DIR
        assert KNOWLEDGE_GENERAL_DIR == KNOWLEDGE_DIR / "general"

    def test_knowledge_workspace_dir_under_knowledge_dir(self):
        from xuansto_mcp.core.config import KNOWLEDGE_DIR, KNOWLEDGE_WORKSPACE_DIR
        assert KNOWLEDGE_WORKSPACE_DIR == KNOWLEDGE_DIR / "workspace"

    def test_knowledge_experience_dir_under_knowledge_dir(self):
        from xuansto_mcp.core.config import KNOWLEDGE_DIR, KNOWLEDGE_EXPERIENCE_DIR
        assert KNOWLEDGE_EXPERIENCE_DIR == KNOWLEDGE_DIR / "experience"

    def test_knowledge_references_dir_under_knowledge_dir(self):
        from xuansto_mcp.core.config import KNOWLEDGE_DIR, KNOWLEDGE_REFERENCES_DIR
        assert KNOWLEDGE_REFERENCES_DIR == KNOWLEDGE_DIR / "references"

    def test_all_knowledge_dirs_share_common_parent(self):
        from xuansto_mcp.core.config import (
            KNOWLEDGE_DIR,
            KNOWLEDGE_EXPERIENCE_DIR,
            KNOWLEDGE_GENERAL_DIR,
            KNOWLEDGE_REFERENCES_DIR,
            KNOWLEDGE_WORKSPACE_DIR,
        )
        for d in [KNOWLEDGE_GENERAL_DIR, KNOWLEDGE_WORKSPACE_DIR,
                  KNOWLEDGE_EXPERIENCE_DIR, KNOWLEDGE_REFERENCES_DIR]:
            assert d.parent == KNOWLEDGE_DIR


class TestKnowledgeSearchUsesUnifiedPath:
    def test_keyword_fallback_uses_knowledge_references_dir(self):
        from xuansto_mcp.tools.knowledge_search import _keyword_fallback_search
        import inspect
        source = inspect.getsource(_keyword_fallback_search)
        assert "KNOWLEDGE_REFERENCES_DIR" in source
        import re
        standalone_refs = re.findall(r'(?<!KNOWLEDGE_)REFERENCES_DIR', source)
        assert len(standalone_refs) == 0

    def test_knowledge_search_imports_knowledge_references_dir(self):
        import xuansto_mcp.tools.knowledge_search as ks_mod
        assert hasattr(ks_mod, "KNOWLEDGE_REFERENCES_DIR")

    def test_search_engine_uses_knowledge_references_dir(self):
        from xuansto_mcp.core.search_engine import SimpleSearchEngine
        engine = SimpleSearchEngine()
        from xuansto_mcp.core.config import KNOWLEDGE_REFERENCES_DIR
        assert KNOWLEDGE_REFERENCES_DIR in engine._search_dirs


class TestConstraintsKnowledgeDir:
    def test_constraints_yaml_knowledge_search_has_knowledge_dir(self):
        import yaml
        from xuansto_mcp.core.config import _resolve_skill_file
        constraints_path = _resolve_skill_file("constraints.yaml")
        if not constraints_path.exists():
            pytest.skip("constraints.yaml not found")
        raw = yaml.safe_load(constraints_path.read_text(encoding="utf-8"))
        fallbacks = raw.get("degradation", {}).get("tool_fallbacks", {})
        ks_entry = fallbacks.get("knowledge_search", {})
        assert ks_entry.get("knowledge_dir") == "data/knowledge"

    def test_constraints_yaml_knowledge_inject_has_knowledge_dir(self):
        import yaml
        from xuansto_mcp.core.config import _resolve_skill_file
        constraints_path = _resolve_skill_file("constraints.yaml")
        if not constraints_path.exists():
            pytest.skip("constraints.yaml not found")
        raw = yaml.safe_load(constraints_path.read_text(encoding="utf-8"))
        fallbacks = raw.get("degradation", {}).get("tool_fallbacks", {})
        ki_entry = fallbacks.get("knowledge_inject", {})
        assert ki_entry.get("knowledge_dir") == "data/knowledge"
