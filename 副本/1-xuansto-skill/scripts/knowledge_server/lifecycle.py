import logging
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from .db_engine import SQLiteEngine

logger = logging.getLogger("knowledge-server")


class LifecycleManager:
    def __init__(self, knowledge_root: Path, db_engine: SQLiteEngine, exporter=None, lifecycle_config: Optional[dict] = None):
        self.knowledge_root = knowledge_root
        self.db = db_engine
        self.exporter = exporter
        cfg = lifecycle_config or {}
        self.archive_enabled = cfg.get("archive_enabled", True)
        self.archive_threshold_days = cfg.get("archive_threshold_days", cfg.get("archive_after_days", 90))
        self.archive_min_confidence = cfg.get("archive_min_confidence", cfg.get("confidence_threshold_archive", 0.5))
        self.archive_check_interval = cfg.get("archive_check_interval", 86400)
        self.archive_path = knowledge_root / cfg.get("archive_path", ".knowledge/archive") if cfg.get("archive_path") else knowledge_root / ".knowledge" / "archive"

    def check_and_archive(self) -> dict:
        if not self.archive_enabled:
            logger.info("operation=lifecycle_check, status=disabled")
            return {"checked": 0, "archived": 0, "errors": 0, "disabled": True}

        candidates = self._find_archive_candidates()
        logger.info("operation=lifecycle_check, candidates=%d", len(candidates))

        archived = 0
        errors = 0
        archived_ids = []

        for entry in candidates:
            if self._archive_entry(entry):
                archived += 1
                archived_ids.append(entry["id"])
            else:
                errors += 1

        report = {
            "checked": len(candidates),
            "archived": archived,
            "errors": errors,
            "archived_ids": archived_ids,
        }
        logger.info(
            "operation=lifecycle_check, checked=%d, archived=%d, errors=%d",
            len(candidates), archived, errors,
        )
        return report

    def _find_archive_candidates(self) -> list:
        conn = self.db._get_conn()
        threshold_date = (datetime.now(timezone.utc) - timedelta(days=self.archive_threshold_days)).strftime("%Y-%m-%d %H:%M:%S")

        cur = conn.execute(
            "SELECT * FROM knowledge_entries "
            "WHERE status != 'archived' AND status != 'deleted' "
            "AND confidence < ? "
            "AND (last_accessed IS NOT NULL AND last_accessed < ? OR last_accessed IS NULL AND updated < ?)",
            (self.archive_min_confidence, threshold_date, threshold_date),
        )
        return [self.db._row_to_dict(row) for row in cur.fetchall()]

    def _archive_entry(self, entry: dict) -> bool:
        entry_id = entry["id"]
        try:
            source_path = entry.get("source_path") or entry.get("content_path")
            if source_path:
                self._move_to_archive(source_path)

            self.db.update_entry(entry_id, {"status": "archived"})

            if self.exporter is not None:
                try:
                    self.exporter.export_entry(entry_id)
                except Exception as e:
                    logger.warning("operation=archive_export, entry_id=%s, error=%s", entry_id, e)

            logger.info("operation=archive_entry, entry_id=%s, status=archived", entry_id)
            return True
        except Exception as e:
            logger.warning("operation=archive_entry, entry_id=%s, status=error, error=%s", entry_id, e)
            return False

    def _move_to_archive(self, source_path: str) -> bool:
        src = Path(source_path)
        if not src.is_absolute():
            src = self.knowledge_root / src

        if not src.exists():
            logger.debug("operation=move_to_archive, source=%s, status=not_found", source_path)
            return False

        try:
            relative = src.relative_to(self.knowledge_root) if src.is_relative_to(self.knowledge_root) else Path(src.name)
            dest = self.archive_path / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
            logger.info("operation=move_to_archive, source=%s, dest=%s, status=moved", source_path, dest)
            return True
        except Exception as e:
            logger.warning("operation=move_to_archive, source=%s, status=error, error=%s", source_path, e)
            return False
