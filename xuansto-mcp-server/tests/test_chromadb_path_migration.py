import shutil
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


@pytest.fixture
def knowledge_root(tmp_path):
    return tmp_path / "knowledge"


def _make_index_dir(knowledge_root: Path) -> Path:
    index_dir = knowledge_root / "index"
    index_dir.mkdir(parents=True, exist_ok=True)
    return index_dir


class TestConfigUsesChromaDbPath:
    def test_knowledge_chroma_path_ends_with_chroma_db(self):
        from xuansto_mcp.core.config import KNOWLEDGE_CHROMA_PATH
        assert KNOWLEDGE_CHROMA_PATH.name == "chroma_db"

    def test_knowledge_chroma_path_under_index(self):
        from xuansto_mcp.core.config import KNOWLEDGE_CHROMA_PATH
        assert KNOWLEDGE_CHROMA_PATH.parent.name == "index"

    def test_legacy_path_constant_exists(self):
        from xuansto_mcp.core.config import _CHROMA_LEGACY_PATH
        assert _CHROMA_LEGACY_PATH.name == "chroma"


class TestMigrationOldPathToNew:
    def test_old_path_migrated_when_new_absent(self, knowledge_root):
        index_dir = _make_index_dir(knowledge_root)
        legacy = index_dir / "chroma"
        current = index_dir / "chroma_db"

        legacy.mkdir(parents=True, exist_ok=True)
        (legacy / "data.bin").write_bytes(b"\x00\x01\x02")

        with patch("xuansto_mcp.core.config.KNOWLEDGE_DIR", knowledge_root), \
             patch("xuansto_mcp.core.config.KNOWLEDGE_CHROMA_PATH", current), \
             patch("xuansto_mcp.core.config._CHROMA_LEGACY_PATH", legacy):
            from xuansto_mcp.core.config import _migrate_chroma_path
            _migrate_chroma_path()

        assert current.exists()
        assert (current / "data.bin").exists()
        assert not legacy.exists()

    def test_old_empty_dir_not_migrated(self, knowledge_root):
        index_dir = _make_index_dir(knowledge_root)
        legacy = index_dir / "chroma"
        current = index_dir / "chroma_db"

        legacy.mkdir(parents=True, exist_ok=True)

        with patch("xuansto_mcp.core.config.KNOWLEDGE_DIR", knowledge_root), \
             patch("xuansto_mcp.core.config.KNOWLEDGE_CHROMA_PATH", current), \
             patch("xuansto_mcp.core.config._CHROMA_LEGACY_PATH", legacy):
            from xuansto_mcp.core.config import _migrate_chroma_path
            _migrate_chroma_path()

        assert not current.exists()

    def test_no_old_path_works_normally(self, knowledge_root):
        index_dir = _make_index_dir(knowledge_root)
        current = index_dir / "chroma_db"
        legacy = index_dir / "chroma"

        with patch("xuansto_mcp.core.config.KNOWLEDGE_DIR", knowledge_root), \
             patch("xuansto_mcp.core.config.KNOWLEDGE_CHROMA_PATH", current), \
             patch("xuansto_mcp.core.config._CHROMA_LEGACY_PATH", legacy):
            from xuansto_mcp.core.config import _migrate_chroma_path
            _migrate_chroma_path()

        assert not legacy.exists()
        assert not current.exists()


class TestBothPathsExistWarning:
    def test_both_paths_with_data_logs_warning(self, knowledge_root, caplog):
        import logging
        index_dir = _make_index_dir(knowledge_root)
        legacy = index_dir / "chroma"
        current = index_dir / "chroma_db"

        legacy.mkdir(parents=True, exist_ok=True)
        (legacy / "old_data.bin").write_bytes(b"\x00")

        current.mkdir(parents=True, exist_ok=True)
        (current / "new_data.bin").write_bytes(b"\x01")

        with patch("xuansto_mcp.core.config.KNOWLEDGE_DIR", knowledge_root), \
             patch("xuansto_mcp.core.config.KNOWLEDGE_CHROMA_PATH", current), \
             patch("xuansto_mcp.core.config._CHROMA_LEGACY_PATH", legacy), \
             caplog.at_level(logging.WARNING, logger="config"):
            from xuansto_mcp.core.config import _migrate_chroma_path
            _migrate_chroma_path()

        assert any("Both legacy ChromaDB path" in r.message for r in caplog.records)
        assert legacy.exists()
        assert current.exists()
        assert (current / "new_data.bin").exists()

    def test_both_exist_new_empty_migrates(self, knowledge_root):
        index_dir = _make_index_dir(knowledge_root)
        legacy = index_dir / "chroma"
        current = index_dir / "chroma_db"

        legacy.mkdir(parents=True, exist_ok=True)
        (legacy / "data.bin").write_bytes(b"\x00")

        current.mkdir(parents=True, exist_ok=True)

        with patch("xuansto_mcp.core.config.KNOWLEDGE_DIR", knowledge_root), \
             patch("xuansto_mcp.core.config.KNOWLEDGE_CHROMA_PATH", current), \
             patch("xuansto_mcp.core.config._CHROMA_LEGACY_PATH", legacy):
            from xuansto_mcp.core.config import _migrate_chroma_path
            _migrate_chroma_path()

        assert current.exists()
        assert (current / "data.bin").exists()
        assert not legacy.exists()


class TestKnowledgeSearchUsesChromaDb:
    def test_ensure_index_uses_knowledge_chroma_path_constant(self):
        import inspect
        from xuansto_mcp.tools import knowledge_search as ks

        source = inspect.getsource(ks._ensure_knowledge_index)
        assert "KNOWLEDGE_CHROMA_PATH" in source
        assert 'index_dir / "chroma"' not in source

    def test_chromadb_search_uses_knowledge_chroma_path_constant(self):
        import inspect
        from xuansto_mcp.tools import knowledge_search as ks

        source = inspect.getsource(ks._chromadb_search)
        assert "KNOWLEDGE_CHROMA_PATH" in source
