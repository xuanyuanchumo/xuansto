import logging
from pathlib import Path
from typing import Any, Optional

from .config import chroma_available
from .embedding import EmbeddingManager

logger = logging.getLogger("knowledge-server")


class ChromaEngine:
    def __init__(self, chroma_path: Path, collection_name: str = "knowledge", embedding_manager: Optional[Any] = None):
        self.chroma_path = chroma_path
        self.collection_name = collection_name
        self.available = chroma_available
        self._client = None
        self._collection = None
        self._primary_collection = None
        self._embedding_manager = embedding_manager

        if self.available:
            try:
                import chromadb as _chromadb
                from chromadb.config import Settings as _ChromaSettings
                self._client = _chromadb.PersistentClient(
                    path=str(chroma_path),
                    settings=_ChromaSettings(anonymized_telemetry=False),
                )
                self._collection = self._client.get_or_create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
                if embedding_manager and embedding_manager.level == EmbeddingManager.LEVEL_API:
                    self._ensure_primary_collection()
                logger.info("operation=chroma_init, status=success, path=%s", chroma_path)
            except Exception as e:
                logger.warning("operation=chroma_init, status=failed, error=%s", e)
                self.available = False
                self._client = None
                self._collection = None
        else:
            logger.info("operation=chroma_init, status=unavailable")

    def _ensure_primary_collection(self):
        if self._client is None or self._primary_collection is not None:
            return
        try:
            self._primary_collection = self._client.get_or_create_collection(
                name=f"{self.collection_name}_primary",
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as e:
            logger.warning("operation=primary_collection_init, error=%s", e)

    def _get_active_collection(self):
        if self._embedding_manager and self._embedding_manager.level == EmbeddingManager.LEVEL_API:
            if self._primary_collection is None:
                self._ensure_primary_collection()
            if self._primary_collection is not None:
                return self._primary_collection
        return self._collection

    def add_embedding(self, entry_id: str, content: str, metadata: Optional[dict] = None):
        if not self.available:
            return

        meta = metadata or {}

        if self._embedding_manager and self._embedding_manager.level < EmbeddingManager.LEVEL_BM25_ONLY:
            embedding, dim = self._embedding_manager.generate_embedding(content)
            if embedding is None:
                raise RuntimeError("Embedding generation failed")

            collection = self._get_active_collection()
            if collection is None:
                raise RuntimeError("No active Chroma collection")

            try:
                collection.upsert(
                    ids=[entry_id],
                    embeddings=[embedding],
                    metadatas=[meta],
                    documents=[content],
                )
            except Exception as e:
                logger.warning("operation=chroma_add, entry_id=%s, error=%s", entry_id, e)
                raise
        else:
            if self._collection is None:
                return
            try:
                self._collection.upsert(
                    ids=[entry_id],
                    documents=[content],
                    metadatas=[meta],
                )
            except Exception as e:
                logger.warning("operation=chroma_add, entry_id=%s, error=%s", entry_id, e)
                raise

    def search_semantic(self, query: str, top_k: int = 20) -> list[dict]:
        if not self.available:
            return []

        try:
            if self._embedding_manager and self._embedding_manager.level < EmbeddingManager.LEVEL_BM25_ONLY:
                embedding, dim = self._embedding_manager.generate_embedding(query)
                if embedding is None:
                    return []

                collection = self._get_active_collection()
                if collection is None:
                    return []

                count = collection.count() or 0
                if count == 0:
                    return []

                results = collection.query(
                    query_embeddings=[embedding],
                    n_results=min(top_k, count),
                )
            else:
                if self._collection is None:
                    return []
                count = self._collection.count() or 0
                if count == 0:
                    return []
                results = self._collection.query(
                    query_texts=[query],
                    n_results=min(top_k, count),
                )

            items = []
            if results and results["ids"] and results["ids"][0]:
                ids = results["ids"][0]
                distances = results["distances"][0] if results.get("distances") else [0.0] * len(ids)
                documents = results["documents"][0] if results.get("documents") else [""] * len(ids)
                for i, entry_id in enumerate(ids):
                    dist = distances[i] if i < len(distances) else 0.0
                    similarity = 1.0 - dist
                    items.append({
                        "id": entry_id,
                        "content": documents[i] if i < len(documents) else "",
                        "_cosine_similarity": similarity,
                    })
            return items
        except Exception as e:
            logger.warning("operation=chroma_search, error=%s", e)
            return []

    def delete_embedding(self, entry_id: str):
        if not self.available:
            return
        for collection in (self._collection, self._primary_collection):
            if collection is not None:
                try:
                    collection.delete(ids=[entry_id])
                except Exception:
                    pass

    def get_vector_count(self) -> int:
        if not self.available:
            return 0
        total = 0
        for collection in (self._collection, self._primary_collection):
            if collection is not None:
                try:
                    total += collection.count()
                except Exception:
                    pass
        return total

    def get_all_ids(self) -> set:
        if not self.available:
            return set()
        all_ids = set()
        for collection in (self._collection, self._primary_collection):
            if collection is not None:
                try:
                    result = collection.get(include=[])
                    if result and result.get("ids"):
                        all_ids.update(result["ids"])
                except Exception:
                    pass
        return all_ids

    def mark_stale_entries(self, limit: int = 10) -> list[str]:
        collection = self._collection
        if collection is None:
            return []
        try:
            result = collection.get(include=[])
            if not result or not result.get("ids"):
                return []
            ids = result["ids"][:limit]
            if not ids:
                return []
            metas = [{"embedding_model_stale": True}] * len(ids)
            collection.update(ids=ids, metadatas=metas)
            return ids
        except Exception as e:
            logger.warning("operation=mark_stale, error=%s", e)
            return []

    def get_stale_entry_ids(self, limit: int = 10) -> list[str]:
        collection = self._collection
        if collection is None:
            return []
        try:
            result = collection.get(where={"embedding_model_stale": True}, include=[])
            if result and result.get("ids"):
                return result["ids"][:limit]
            return []
        except Exception:
            return []

    def close(self):
        self._client = None
        self._collection = None
        self._primary_collection = None
