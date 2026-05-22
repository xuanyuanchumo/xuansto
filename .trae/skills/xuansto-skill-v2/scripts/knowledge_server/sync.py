import hashlib
import logging
from pathlib import Path
from typing import Optional

from .db_engine import SQLiteEngine
from .importer import FirstRunImporter
from .vector_engine import ChromaEngine

logger = logging.getLogger("knowledge-server")


class FileSyncDetector:
    def __init__(self, knowledge_root: Path, db_engine: SQLiteEngine, sync_config: Optional[dict] = None):
        self.knowledge_root = knowledge_root
        self.db = db_engine
        self._sync_config = sync_config or {}

    def detect_changes(self) -> dict:
        disk_files = self._scan_markdown_files()
        db_entries = self._get_db_source_paths()

        added = []
        modified = []
        deleted = []

        for rel_path, file_info in disk_files.items():
            if rel_path not in db_entries:
                added.append(rel_path)
            else:
                db_entry = db_entries[rel_path]
                filepath = self.knowledge_root / rel_path
                file_content = filepath.read_text(encoding="utf-8")
                current_hash = SQLiteEngine._compute_hash(file_content)
                if current_hash != db_entry.get("content_hash"):
                    modified.append({"source_path": rel_path, "id": db_entry["id"]})

        db_rel_paths = set(db_entries.keys())
        disk_rel_paths = set(disk_files.keys())
        for rel_path in db_rel_paths - disk_rel_paths:
            deleted.append({"source_path": rel_path, "id": db_entries[rel_path]["id"]})

        return {"added": added, "modified": modified, "deleted": deleted}

    def _compute_file_hash(self, filepath: Path) -> str:
        content = filepath.read_bytes()
        return hashlib.md5(content).hexdigest()

    def _scan_markdown_files(self) -> dict:
        result = {}
        file_patterns = self._sync_config.get("file_patterns", ["*.md"])
        md_patterns = [p for p in file_patterns if p.endswith(".md")]
        patterns = md_patterns if md_patterns else ["*.md"]

        for scope in ("general", "workspace", "experience"):
            scope_dir = self.knowledge_root / scope
            if not scope_dir.is_dir():
                continue
            for pattern in patterns:
                for md_file in scope_dir.rglob(pattern):
                    rel_path = str(md_file.relative_to(self.knowledge_root))
                    stat_info = md_file.stat()
                    result[rel_path] = {
                        "mtime": stat_info.st_mtime,
                        "hash": self._compute_file_hash(md_file),
                    }
        return result

    def _get_db_source_paths(self) -> dict:
        entries = self.db.get_all_entries()
        result = {}
        for entry in entries:
            source_path = entry.get("source_path")
            if source_path:
                result[source_path] = {
                    "id": entry["id"],
                    "content_hash": entry.get("content_hash"),
                }
        return result


class IncrementalSync:
    def __init__(self, knowledge_root: Path, db_engine: SQLiteEngine, importer: FirstRunImporter, chroma_engine: Optional[ChromaEngine] = None, sync_config: Optional[dict] = None):
        self.knowledge_root = knowledge_root
        self.db = db_engine
        self.importer = importer
        self.chroma = chroma_engine
        self._sync_config = sync_config or {}

    def sync(self) -> dict:
        detector = FileSyncDetector(self.knowledge_root, self.db, self._sync_config)
        changes = detector.detect_changes()

        report = {
            "added": 0,
            "modified": 0,
            "deleted": 0,
            "errors": 0,
            "details": changes,
        }

        if changes["added"]:
            report["added"] = self._sync_added(changes["added"])

        if changes["modified"]:
            report["modified"] = self._sync_modified(changes["modified"])

        if changes["deleted"]:
            report["deleted"] = self._sync_deleted(changes["deleted"])

        logger.info(
            "operation=incremental_sync, added=%d, modified=%d, deleted=%d",
            report["added"], report["modified"], report["deleted"],
        )

        return report

    def _sync_added(self, added_files: list) -> int:
        count = 0
        for rel_path in added_files:
            filepath = self.knowledge_root / rel_path
            scope = self._infer_scope(rel_path)
            try:
                entry = self.importer._parse_md_file(filepath, scope, self.knowledge_root)
                if entry:
                    result = self.db.add_entry(entry)
                    if self.chroma and self.chroma.available:
                        try:
                            self.chroma.add_embedding(
                                result["id"],
                                entry["content"],
                                {"scope": scope, "title": entry["title"]},
                            )
                            self.db.update_embedding_status(result["id"], "ready")
                        except Exception:
                            self.db.update_embedding_status(result["id"], "pending")
                            logger.warning("operation=sync_add_chroma_failed, entry_id=%s", result["id"])
                    count += 1
            except Exception as e:
                logger.warning("operation=sync_add_failed, path=%s, error=%s", rel_path, e)
        return count

    def _sync_modified(self, modified_files: list) -> int:
        count = 0
        for item in modified_files:
            rel_path = item["source_path"]
            entry_id = item["id"]
            filepath = self.knowledge_root / rel_path
            scope = self._infer_scope(rel_path)
            try:
                self.db.delete_entry(entry_id)
                if self.chroma and self.chroma.available:
                    self.chroma.delete_embedding(entry_id)

                entry = self.importer._parse_md_file(filepath, scope, self.knowledge_root)
                if entry:
                    result = self.db.add_entry(entry)
                    if self.chroma and self.chroma.available:
                        try:
                            self.chroma.add_embedding(
                                result["id"],
                                entry["content"],
                                {"scope": scope, "title": entry["title"]},
                            )
                            self.db.update_embedding_status(result["id"], "ready")
                        except Exception:
                            self.db.update_embedding_status(result["id"], "pending")
                            logger.warning("operation=sync_modify_chroma_failed, entry_id=%s", result["id"])
                    count += 1
            except Exception as e:
                logger.warning("operation=sync_modify_failed, path=%s, error=%s", rel_path, e)
        return count

    def _sync_deleted(self, deleted_ids: list) -> int:
        count = 0
        for item in deleted_ids:
            entry_id = item["id"]
            try:
                self.db.delete_entry(entry_id)
                if self.chroma and self.chroma.available:
                    self.chroma.delete_embedding(entry_id)
                count += 1
            except Exception as e:
                logger.warning("operation=sync_delete_failed, entry_id=%s, error=%s", entry_id, e)
        return count

    @staticmethod
    def _infer_scope(rel_path: str) -> str:
        parts = Path(rel_path).parts
        if parts and parts[0] in ("general", "workspace", "experience"):
            return parts[0]
        return "workspace"
