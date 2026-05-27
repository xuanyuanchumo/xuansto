import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# NOTE: _inject_knowledge and _precipitate_experience were removed during refactoring.
# The new knowledge_inject.py has _action_inject and _action_precipitate with completely
# different signatures, so these tests cannot be simply re-imported.
# from xuansto_mcp.tools.knowledge_search import _inject_knowledge, _precipitate_experience


@pytest.fixture
def tmp_knowledge_dirs(tmp_path):
    general_dir = tmp_path / "knowledge" / "general"
    workspace_dir = tmp_path / "knowledge" / "workspace"
    experience_dir = tmp_path / "knowledge" / "experience"
    patterns_dir = tmp_path / "patterns"
    db_path = tmp_path / "knowledge" / "index" / "knowledge.db"

    general_dir.mkdir(parents=True)
    workspace_dir.mkdir(parents=True)
    experience_dir.mkdir(parents=True)
    patterns_dir.mkdir(parents=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    return {
        "general": general_dir,
        "workspace": workspace_dir,
        "experience": experience_dir,
        "patterns": patterns_dir,
        "db": db_path,
        "root": tmp_path,
    }


@pytest.fixture(autouse=True)
def patch_config(tmp_knowledge_dirs):
    with patch("xuansto_mcp.tools.knowledge_inject.KNOWLEDGE_GENERAL_DIR", tmp_knowledge_dirs["general"]), \
         patch("xuansto_mcp.tools.knowledge_inject.KNOWLEDGE_WORKSPACE_DIR", tmp_knowledge_dirs["workspace"]), \
         patch("xuansto_mcp.tools.knowledge_inject.KNOWLEDGE_EXPERIENCE_DIR", tmp_knowledge_dirs["experience"]), \
         patch("xuansto_mcp.tools.knowledge_inject.PATTERNS_DIR", tmp_knowledge_dirs["patterns"]), \
         patch("xuansto_mcp.tools.knowledge_inject.KNOWLEDGE_DB_PATH", tmp_knowledge_dirs["db"]):
        yield


# NOTE: TestInjectKnowledge class commented out - _inject_knowledge was completely removed.
# The replacement _action_inject in knowledge_inject.py has a different signature:
#   _action_inject(topics, scope, max_tokens, relevance_threshold)
# vs the old:
#   _inject_knowledge(content, knowledge_type, metadata)
# class TestInjectKnowledge:
#     def test_inject_creates_file_in_general_dir(self, tmp_knowledge_dirs):
#         ...
#     def test_inject_creates_file_in_workspace_dir(self, tmp_knowledge_dirs):
#         ...
#     def test_inject_creates_file_in_experience_dir(self, tmp_knowledge_dirs):
#         ...
#     def test_inject_writes_yaml_frontmatter(self, tmp_knowledge_dirs):
#         ...
#     def test_inject_with_none_metadata(self, tmp_knowledge_dirs):
#         ...
#     def test_inject_with_metadata(self, tmp_knowledge_dirs):
#         ...


# NOTE: TestPrecipitateExperience class commented out - _precipitate_experience was completely removed.
# The replacement _action_precipitate in knowledge_inject.py has a different signature:
#   _action_precipitate(category, title, content, tags, confidence)
# vs the old:
#   _precipitate_experience(pattern_ids)
# class TestPrecipitateExperience:
#     def test_precipitate_reads_patterns_and_generates_doc(self, tmp_knowledge_dirs):
#         ...
#     def test_precipitate_with_multiple_patterns(self, tmp_knowledge_dirs):
#         ...
#     def test_precipitate_with_nonexistent_patterns(self, tmp_knowledge_dirs):
#         ...
#     def test_precipitate_mixed_found_and_not_found(self, tmp_knowledge_dirs):
#         ...
#     def test_precipitate_uses_type_fallback(self, tmp_knowledge_dirs):
#         ...
