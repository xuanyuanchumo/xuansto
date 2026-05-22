import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .config import KnowledgeConfig
from .db_engine import SQLiteEngine
from .vector_engine import ChromaEngine
from .embedding import EmbeddingManager

logger = logging.getLogger("knowledge-server")

QUALITY_GATES = {
    "DISTILL-COMPLETE": {
        "description": "文档蒸馏流程完整执行",
        "check": lambda result: result is not None and result.get("entry_id") is not None,
    },
    "DISTILL-ACCURACY": {
        "description": "蒸馏内容准确度达标",
        "threshold": 0.8,
        "check": lambda result: result is not None and result.get("accuracy_score", 0.0) >= 0.8,
    },
    "DISTILL-COMPRESSION": {
        "description": "蒸馏压缩率达标",
        "threshold": 0.3,
        "check": lambda result: result is not None and result.get("compression_ratio", 1.0) <= 0.3,
    },
}


class DocFlowDistiller:
    def __init__(self, config: KnowledgeConfig, db: SQLiteEngine, vector: ChromaEngine, embedding_mgr: EmbeddingManager):
        self.config = config
        self.db = db
        self.vector = vector
        self.embedding_mgr = embedding_mgr

    def distill_document(self, raw_doc_path: str) -> Optional[dict]:
        raw_content = self._read_raw(raw_doc_path)
        if not raw_content:
            logger.warning("operation=distill, status=empty, path=%s", raw_doc_path)
            return None

        structured_data = self._extract_structured(raw_content)
        if not structured_data:
            logger.warning("operation=distill, status=extract_failed, path=%s", raw_doc_path)
            return None

        skill_entry = self._convert_to_skill_entry(structured_data)
        if not skill_entry:
            logger.warning("operation=distill, status=convert_failed, path=%s", raw_doc_path)
            return None

        entry_result = self.db.add_entry(skill_entry)
        if not entry_result:
            logger.warning("operation=distill, status=db_save_failed, path=%s", raw_doc_path)
            return None

        skill_entry["entry_id"] = entry_result["id"]

        embed_result = self._embed_entry(skill_entry)
        if embed_result:
            self.db.update_embedding_status(entry_result["id"], "ready")

        raw_size = len(raw_content.encode("utf-8"))
        distilled_size = len(skill_entry.get("content", "").encode("utf-8"))
        compression_ratio = distilled_size / raw_size if raw_size > 0 else 1.0

        result = {
            "entry_id": entry_result["id"],
            "content_hash": entry_result.get("content_hash"),
            "source_path": raw_doc_path,
            "accuracy_score": self._compute_accuracy(structured_data, skill_entry),
            "compression_ratio": round(compression_ratio, 4),
            "embedded": embed_result,
        }

        self._check_quality_gates(result)
        return result

    def batch_distill(self, doc_paths: list[str]) -> list[dict]:
        results = []
        for path in doc_paths:
            try:
                result = self.distill_document(path)
                results.append(result or {"source_path": path, "status": "failed"})
            except Exception as e:
                logger.error("operation=batch_distill, path=%s, error=%s", path, e)
                results.append({"source_path": path, "status": "error", "error": str(e)})
        logger.info("operation=batch_distill, total=%d, success=%d", len(doc_paths), sum(1 for r in results if r.get("entry_id")))
        return results

    def _read_raw(self, raw_doc_path: str) -> Optional[str]:
        p = Path(raw_doc_path)
        if not p.exists():
            return None
        try:
            return p.read_text(encoding="utf-8")
        except OSError:
            return None

    def _extract_structured(self, raw_content: str) -> Optional[dict]:
        title = ""
        title_match = re.search(r"^#\s+(.+)$", raw_content, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()

        sections = []
        current_section = {"heading": title or "Untitled", "content": []}
        for line in raw_content.splitlines():
            heading_match = re.match(r"^#{1,4}\s+(.+)$", line)
            if heading_match:
                if current_section["content"]:
                    sections.append(current_section)
                current_section = {"heading": heading_match.group(1).strip(), "content": []}
            else:
                stripped = line.strip()
                if stripped:
                    current_section["content"].append(stripped)
        if current_section["content"]:
            sections.append(current_section)

        tags = set()
        tag_patterns = [
            re.compile(r"`(\w+)`"),
            re.compile(r"\*\*(\w[\w\-]*)\*\*"),
        ]
        for section in sections:
            for line in section["content"]:
                for pat in tag_patterns:
                    for m in pat.findall(line):
                        if len(m) > 2:
                            tags.add(m.lower())

        summary_parts = []
        for section in sections[:3]:
            summary_parts.append(section["heading"] + ": " + " ".join(section["content"][:2]))
        summary = " ".join(summary_parts)[:500]

        doc_type = "unknown"
        content_lower = raw_content.lower()
        type_hints = {
            "standard": ["规范", "standard", "guideline", "convention"],
            "pattern": ["模式", "pattern", "design pattern", "架构"],
            "error-solution": ["错误", "error", "bug", "fix", "troubleshoot"],
            "glossary": ["术语", "glossary", "definition", "定义"],
        }
        for t, hints in type_hints.items():
            if any(h in content_lower for h in hints):
                doc_type = t
                break

        return {
            "title": title,
            "sections": sections,
            "tags": list(tags)[:20],
            "summary": summary,
            "type": doc_type,
            "raw_length": len(raw_content),
        }

    def _convert_to_skill_entry(self, structured_data: dict) -> Optional[dict]:
        if not structured_data.get("title"):
            return None

        content_parts = []
        for section in structured_data.get("sections", []):
            content_parts.append(f"## {section['heading']}")
            content_parts.extend(section["content"])
        distilled_content = "\n".join(content_parts)

        return {
            "title": structured_data["title"],
            "content": distilled_content,
            "scope": "general",
            "tags": structured_data.get("tags", []),
            "confidence": 0.7,
            "source_path": "",
            "source_rating": 3,
            "type": structured_data.get("type", "unknown"),
            "category": "distilled",
            "summary": structured_data.get("summary", ""),
        }

    def _embed_entry(self, skill_entry: dict) -> bool:
        entry_id = skill_entry.get("entry_id")
        content = skill_entry.get("content", "")
        if not entry_id or not content:
            return False
        try:
            self.vector.add_embedding(
                entry_id=entry_id,
                content=content,
                metadata={
                    "type": skill_entry.get("type", "unknown"),
                    "category": skill_entry.get("category", "distilled"),
                    "scope": skill_entry.get("scope", "general"),
                },
            )
            return True
        except Exception as e:
            logger.warning("operation=embed_entry, entry_id=%s, error=%s", entry_id, e)
            return False

    def _compute_accuracy(self, structured_data: dict, skill_entry: dict) -> float:
        raw_sections = len(structured_data.get("sections", []))
        distilled_content = skill_entry.get("content", "")
        distilled_sections = len(re.findall(r"^## ", distilled_content, re.MULTILINE))
        if raw_sections == 0:
            return 0.0
        section_coverage = min(distilled_sections / raw_sections, 1.0)
        tag_coverage = 1.0 if structured_data.get("tags") else 0.5
        return round(section_coverage * 0.7 + tag_coverage * 0.3, 4)

    def _check_quality_gates(self, result: dict):
        for gate_name, gate_def in QUALITY_GATES.items():
            passed = gate_def["check"](result)
            if not passed:
                logger.warning(
                    "operation=quality_gate, gate=%s, status=FAILED, result=%s",
                    gate_name,
                    json.dumps({k: v for k, v in result.items() if k != "content"}, default=str),
                )
            else:
                logger.info("operation=quality_gate, gate=%s, status=PASSED", gate_name)
