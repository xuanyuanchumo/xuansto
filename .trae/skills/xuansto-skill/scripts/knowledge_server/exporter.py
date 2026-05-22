import json
import logging
from pathlib import Path

from .config import yaml_available
from .db_engine import SQLiteEngine

logger = logging.getLogger("knowledge-server")


class KnowledgeExporter:
    def __init__(self, knowledge_root: Path, db_engine: SQLiteEngine):
        self.knowledge_root = knowledge_root
        self.db = db_engine

    def export_entry(self, entry_id: str) -> bool:
        entry = self.db.get_entry(entry_id)
        if entry is None:
            logger.warning("operation=export_entry, entry_id=%s, status=not_found", entry_id)
            return False
        try:
            filepath = self._determine_file_path(entry)
            frontmatter = self._format_frontmatter(entry)
            content = entry.get("content", "")
            self._write_markdown(filepath, frontmatter, content)
            logger.info("operation=export_entry, entry_id=%s, path=%s, status=ok", entry_id, filepath)
            return True
        except Exception as e:
            logger.warning("operation=export_entry, entry_id=%s, status=error, error=%s", entry_id, e)
            return False

    def export_all(self) -> dict:
        entries = self.db.get_all_entries()
        exported = 0
        errors = 0
        for entry in entries:
            if self.export_entry(entry["id"]):
                exported += 1
            else:
                errors += 1
        logger.info("operation=export_all, exported=%d, errors=%d", exported, errors)
        return {"exported": exported, "errors": errors}

    def _format_frontmatter(self, entry: dict) -> str:
        meta = {
            "id": entry.get("id", ""),
            "type": entry.get("type", "unknown"),
            "category": entry.get("category", "uncategorized"),
            "tags": entry.get("tags", []),
            "version": entry.get("version", 1),
            "updated": entry.get("updated", ""),
            "scope": entry.get("scope", "workspace"),
            "confidence": entry.get("confidence", 0.6),
        }
        if entry.get("title"):
            meta["title"] = entry["title"]
        if entry.get("summary"):
            meta["summary"] = entry["summary"]
        if entry.get("source_path"):
            meta["source_path"] = entry["source_path"]

        if yaml_available:
            import yaml
            rendered = yaml.dump(meta, default_flow_style=False, allow_unicode=True, sort_keys=False)
        else:
            rendered = json.dumps(meta, ensure_ascii=False, indent=2)
        return f"---\n{rendered}---\n"

    def _determine_file_path(self, entry: dict) -> Path:
        scope = entry.get("scope", "workspace")
        category = entry.get("category", "uncategorized")
        entry_id = entry.get("id", "unknown")

        title = entry.get("title", entry_id)
        safe_title = "".join(c if c.isalnum() or c in ("-", "_", " ") else "_" for c in title).strip()
        if not safe_title:
            safe_title = entry_id

        filename = f"{safe_title}.md"
        directory = self.knowledge_root / scope / category
        directory.mkdir(parents=True, exist_ok=True)
        return directory / filename

    def _write_markdown(self, filepath: Path, frontmatter: str, content: str):
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(frontmatter + content, encoding="utf-8")
