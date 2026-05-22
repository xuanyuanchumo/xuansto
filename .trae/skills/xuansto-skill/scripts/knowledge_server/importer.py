import json
import logging
import re
from pathlib import Path
from typing import Optional

from .config import KnowledgeConfig, yaml_available
from .db_engine import SQLiteEngine
from .vector_engine import ChromaEngine

logger = logging.getLogger("knowledge-server")


class FirstRunImporter:
    def __init__(self, config: KnowledgeConfig, sqlite_engine: SQLiteEngine, chroma_engine: ChromaEngine):
        self.config = config
        self.sqlite = sqlite_engine
        self.chroma = chroma_engine

    def should_import(self) -> bool:
        return self.sqlite.is_empty()

    def run(self) -> dict:
        stats = {"general": 0, "workspace": 0, "experience": 0, "errors": 0}
        root = self.config.knowledge_root

        for scope in ("general", "workspace", "experience"):
            scope_dir = root / scope
            if not scope_dir.is_dir():
                continue
            for md_file in scope_dir.rglob("*.md"):
                try:
                    entry = self._parse_md_file(md_file, scope, root)
                    if entry:
                        result = self.sqlite.add_entry(entry)
                        if self.chroma.available:
                            try:
                                self.chroma.add_embedding(
                                    result["id"],
                                    entry["content"],
                                    {"scope": scope, "title": entry["title"]},
                                )
                                self.sqlite.update_embedding_status(result["id"], "ready")
                            except Exception:
                                self.sqlite.update_embedding_status(result["id"], "pending")
                                logger.warning("operation=import_chroma_failed, entry_id=%s", result["id"])
                        stats[scope] += 1
                except Exception as e:
                    logger.warning("operation=import_failed, path=%s, error=%s", md_file, e)
                    stats["errors"] += 1

        self._ensure_backup_dirs()
        return stats

    def _parse_md_file(self, md_path: Path, scope: str, root: Path) -> Optional[dict]:
        text = md_path.read_text(encoding="utf-8")
        meta, body = self._parse_frontmatter(text)

        title = meta.get("title", md_path.stem) if meta else md_path.stem
        content = body.strip() if body else text.strip()
        if not content:
            return None

        tags = meta.get("tags", []) if meta else []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]

        confidence = 0.6
        if meta and "confidence" in meta:
            try:
                confidence = float(meta["confidence"])
            except (ValueError, TypeError):
                pass

        return {
            "title": title,
            "content": content,
            "scope": scope,
            "tags": tags,
            "source_path": str(md_path.relative_to(root)),
            "confidence": confidence,
            "type": meta.get("type", "unknown") if meta else "unknown",
            "category": meta.get("category", "uncategorized") if meta else "uncategorized",
            "summary": meta.get("summary") if meta else None,
            "content_path": str(md_path.relative_to(root)),
        }

    @staticmethod
    def _parse_frontmatter(text: str):
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", text, re.DOTALL)
        if not match:
            return None, text
        raw, body = match.group(1), match.group(2)
        try:
            if yaml_available:
                import yaml
                meta = yaml.safe_load(raw)
            else:
                meta = json.loads(raw)
            if not isinstance(meta, dict):
                return None, text
            return meta, body
        except (yaml.YAMLError if yaml_available else Exception):
            return None, text

    def _ensure_backup_dirs(self):
        root = self.config.knowledge_root
        for subdir in ("full", "incremental", "snapshot"):
            (root / "backup" / subdir).mkdir(parents=True, exist_ok=True)
