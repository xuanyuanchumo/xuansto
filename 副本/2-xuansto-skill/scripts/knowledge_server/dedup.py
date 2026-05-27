import hashlib
import json
import logging
from typing import Optional

from .config import KnowledgeConfig
from .db_engine import SQLiteEngine
from .vector_engine import ChromaEngine

logger = logging.getLogger("knowledge-server")


class DedupEngine:
    def __init__(self, sqlite_engine: SQLiteEngine, chroma_engine: ChromaEngine, config: KnowledgeConfig):
        self.sqlite = sqlite_engine
        self.chroma = chroma_engine
        self.threshold = config.dedup_threshold
        self.action = config.dedup_action

    @staticmethod
    def _compute_metadata_hash(entry: dict) -> str:
        entry_type = entry.get("type", "unknown")
        category = entry.get("category", "uncategorized")
        tags = entry.get("tags", [])
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except json.JSONDecodeError:
                tags = []
        sorted_tags = sorted(tags)
        raw = f"{entry_type}|{category}|{'|'.join(sorted_tags)}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]

    def check_duplicate(self, entry: dict) -> dict:
        summary = entry.get("summary") or entry.get("content", "")
        if not summary or not self.chroma.available:
            return {"is_duplicate": False, "action": "new", "existing_id": None, "similarity_score": 0.0}

        semantic_results = self.chroma.search_semantic(summary, top_k=3)
        if not semantic_results:
            return {"is_duplicate": False, "action": "new", "existing_id": None, "similarity_score": 0.0}

        max_sim = 0.0
        best_match_id = None
        for result in semantic_results:
            sim = result.get("_cosine_similarity", 0.0)
            if sim > max_sim:
                max_sim = sim
                best_match_id = result["id"]

        if max_sim < self.threshold:
            return {"is_duplicate": False, "action": "new", "existing_id": None, "similarity_score": max_sim}

        existing = self.sqlite.get_entry(best_match_id)
        if existing is None:
            return {"is_duplicate": False, "action": "new", "existing_id": None, "similarity_score": max_sim}

        new_meta_hash = self._compute_metadata_hash(entry)
        existing_meta_hash = self._compute_metadata_hash(existing)
        new_id = entry.get("id", "")

        if new_meta_hash == existing_meta_hash:
            action = self.action
            self.sqlite.log_dedup(new_id, existing["id"], max_sim, action)
            return {"is_duplicate": True, "action": action, "existing_id": existing["id"], "similarity_score": max_sim}
        else:
            self.sqlite.log_dedup(new_id, existing["id"], max_sim, "keep_both")
            return {"is_duplicate": False, "action": "keep_both", "existing_id": existing["id"], "similarity_score": max_sim}

    def merge_entries(self, existing: dict, new_entry: dict) -> dict:
        if new_entry.get("confidence", 0) >= existing.get("confidence", 0):
            primary = new_entry
            secondary = existing
        else:
            primary = existing
            secondary = new_entry

        merged = primary.copy()

        existing_tags = set(existing.get("tags", []))
        new_tags = set(new_entry.get("tags", []))
        merged["tags"] = list(existing_tags | new_tags)

        merged["success_count"] = existing.get("success_count", 0) + new_entry.get("success_count", 0)
        merged["failure_count"] = existing.get("failure_count", 0) + new_entry.get("failure_count", 0)
        merged["occurrences"] = existing.get("occurrences", 1) + new_entry.get("occurrences", 1)

        occ_a = existing.get("occurrences", 1)
        occ_b = new_entry.get("occurrences", 1)
        conf_a = existing.get("confidence", 0.6)
        conf_b = new_entry.get("confidence", 0.6)
        total_occ = occ_a + occ_b
        if total_occ > 0:
            merged["confidence"] = round((conf_a * occ_a + conf_b * occ_b) / total_occ, 4)
        else:
            merged["confidence"] = max(conf_a, conf_b)

        created_a = existing.get("created", "")
        created_b = new_entry.get("created", "")
        merged["created"] = min(created_a, created_b) if created_a and created_b else (created_a or created_b)
        from datetime import datetime, timezone
        merged["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        primary_summary = primary.get("summary") or ""
        secondary_summary = secondary.get("summary") or ""
        if secondary_summary and secondary_summary not in primary_summary:
            merged["summary"] = f"{primary_summary}; {secondary_summary}" if primary_summary else secondary_summary
        else:
            merged["summary"] = primary_summary

        if new_entry.get("source_rating", 3) > existing.get("source_rating", 3):
            merged["source_rating"] = new_entry["source_rating"]

        return merged
