import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools.knowledge_search import _inject_knowledge, _precipitate_experience


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
    with patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_GENERAL_DIR", tmp_knowledge_dirs["general"]), \
         patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_WORKSPACE_DIR", tmp_knowledge_dirs["workspace"]), \
         patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_EXPERIENCE_DIR", tmp_knowledge_dirs["experience"]), \
         patch("xuansto_mcp.tools.knowledge_search.PATTERNS_DIR", tmp_knowledge_dirs["patterns"]), \
         patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_DB_PATH", tmp_knowledge_dirs["db"]):
        yield


class TestInjectKnowledge:
    def test_inject_creates_file_in_general_dir(self, tmp_knowledge_dirs):
        result = _inject_knowledge("test knowledge content", "general", None)

        assert result["knowledge_type"] == "general"
        assert result["injected_id"].startswith("injected-")
        assert result["injected_id"].endswith(".md")
        assert result["indexed"] is False

        filepath = Path(result["path"])
        assert filepath.exists()
        assert filepath.parent == tmp_knowledge_dirs["general"]

    def test_inject_creates_file_in_workspace_dir(self, tmp_knowledge_dirs):
        result = _inject_knowledge("workspace content", "workspace", {"project": "test"})

        assert result["knowledge_type"] == "workspace"
        filepath = Path(result["path"])
        assert filepath.exists()
        assert filepath.parent == tmp_knowledge_dirs["workspace"]

    def test_inject_creates_file_in_experience_dir(self, tmp_knowledge_dirs):
        result = _inject_knowledge("experience content", "experience", None)

        assert result["knowledge_type"] == "experience"
        filepath = Path(result["path"])
        assert filepath.exists()
        assert filepath.parent == tmp_knowledge_dirs["experience"]

    def test_inject_writes_yaml_frontmatter(self, tmp_knowledge_dirs):
        result = _inject_knowledge("my knowledge body", "general", {"key": "value"})

        filepath = Path(result["path"])
        content = filepath.read_text(encoding="utf-8")

        assert content.startswith("---\n")
        assert "type: injected" in content
        assert "knowledge_type: general" in content
        assert "injected_at:" in content
        assert '"key": "value"' in content
        assert "---\n" in content
        body_after_frontmatter = content.split("---\n", 2)[2]
        assert body_after_frontmatter.startswith("my knowledge body")

    def test_inject_with_none_metadata(self, tmp_knowledge_dirs):
        result = _inject_knowledge("content", "general", None)

        filepath = Path(result["path"])
        content = filepath.read_text(encoding="utf-8")
        assert "metadata: {}" in content

    def test_inject_with_metadata(self, tmp_knowledge_dirs):
        meta = {"source": "test", "priority": 1}
        result = _inject_knowledge("content", "general", meta)

        filepath = Path(result["path"])
        content = filepath.read_text(encoding="utf-8")
        assert '"source": "test"' in content
        assert '"priority": 1' in content


class TestPrecipitateExperience:
    def test_precipitate_reads_patterns_and_generates_doc(self, tmp_knowledge_dirs):
        pattern_data = {
            "error_type": "ImportError",
            "description": "Module not found",
            "occurrences": 5,
        }
        pattern_file = tmp_knowledge_dirs["patterns"] / "pattern-001.json"
        pattern_file.write_text(json.dumps(pattern_data), encoding="utf-8")

        result = _precipitate_experience(["pattern-001"])

        assert result["patterns_analyzed"] == 1
        assert result["themes_found"] == 1
        assert result["precipitated_id"].startswith("precipitated-")
        assert result["precipitated_id"].endswith(".md")

        filepath = Path(result["path"])
        assert filepath.exists()
        assert filepath.parent == tmp_knowledge_dirs["experience"]

        doc = filepath.read_text(encoding="utf-8")
        assert "# 经验沉淀" in doc
        assert "## 模式来源" in doc
        assert "pattern-001" in doc
        assert "## 共性分析" in doc
        assert "ImportError" in doc
        assert "## 建议" in doc

    def test_precipitate_with_multiple_patterns(self, tmp_knowledge_dirs):
        for i, etype in enumerate(["TypeError", "ImportError", "TypeError"]):
            data = {"error_type": etype, "occurrences": i + 1}
            f = tmp_knowledge_dirs["patterns"] / f"pat-{i}.json"
            f.write_text(json.dumps(data), encoding="utf-8")

        result = _precipitate_experience(["pat-0", "pat-1", "pat-2"])

        assert result["patterns_analyzed"] == 3
        assert result["themes_found"] == 2

        doc = Path(result["path"]).read_text(encoding="utf-8")
        assert "TypeError" in doc
        assert "ImportError" in doc

    def test_precipitate_with_nonexistent_patterns(self, tmp_knowledge_dirs):
        result = _precipitate_experience(["nonexistent-1", "nonexistent-2"])

        assert result["patterns_analyzed"] == 0
        assert result["themes_found"] == 0

        doc = Path(result["path"]).read_text(encoding="utf-8")
        assert "## 模式来源" in doc
        assert "nonexistent-1" in doc
        assert "未找到" in doc

    def test_precipitate_mixed_found_and_not_found(self, tmp_knowledge_dirs):
        pattern_data = {"error_type": "ValueError", "occurrences": 2}
        pattern_file = tmp_knowledge_dirs["patterns"] / "exists.json"
        pattern_file.write_text(json.dumps(pattern_data), encoding="utf-8")

        result = _precipitate_experience(["exists", "missing"])

        assert result["patterns_analyzed"] == 1
        assert result["themes_found"] == 1

        doc = Path(result["path"]).read_text(encoding="utf-8")
        assert "ValueError" in doc
        assert "1 个模式文件未找到" in doc

    def test_precipitate_uses_type_fallback(self, tmp_knowledge_dirs):
        pattern_data = {"type": "RuntimeError", "occurrences": 3}
        pattern_file = tmp_knowledge_dirs["patterns"] / "fallback-type.json"
        pattern_file.write_text(json.dumps(pattern_data), encoding="utf-8")

        result = _precipitate_experience(["fallback-type"])

        assert result["patterns_analyzed"] == 1
        assert result["themes_found"] == 1

        doc = Path(result["path"]).read_text(encoding="utf-8")
        assert "RuntimeError" in doc
