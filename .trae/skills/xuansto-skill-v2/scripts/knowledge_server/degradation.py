import logging
import threading
import time

from .embedding import EmbeddingManager

logger = logging.getLogger("knowledge-server")


class DegradationManager:
    LEVEL_NORMAL = 0
    LEVEL_LOCAL_SEMANTIC = 1
    LEVEL_BM25_ONLY = 2
    LEVEL_FILE_SEARCH = 3

    LEVEL_NAMES = {0: "normal", 1: "local_semantic", 2: "bm25_only", 3: "file_search"}

    def __init__(self, chroma_engine, config, embedding_manager=None, sqlite_engine=None):
        self.chroma = chroma_engine
        self.config = config
        self.embedding_manager = embedding_manager
        self.sqlite = sqlite_engine
        self._level = self.LEVEL_NORMAL
        self._lock = threading.Lock()
        self._check_interval = 30
        self._running = False
        self._determine_initial_level()

    def _determine_initial_level(self):
        if self.embedding_manager:
            em_level = self.embedding_manager.level
            if em_level == EmbeddingManager.LEVEL_BM25_ONLY:
                self._level = self.LEVEL_BM25_ONLY
                logger.info("operation=degradation_init, level=bm25_only, reason=embedding_unavailable")
                return
            elif em_level == EmbeddingManager.LEVEL_LOCAL:
                self._level = self.LEVEL_LOCAL_SEMANTIC
                logger.info("operation=degradation_init, level=local_semantic, reason=embedding_local_only")
                return
        if not self.chroma.available:
            self._level = self.LEVEL_BM25_ONLY
            logger.info("operation=degradation_init, level=bm25_only, reason=chroma_unavailable")

    @property
    def level(self) -> int:
        with self._lock:
            return self._level

    @property
    def level_name(self) -> str:
        return self.LEVEL_NAMES.get(self.level, "unknown")

    def get_search_strategy(self) -> str:
        current = self.level
        if current == self.LEVEL_NORMAL:
            return "hybrid"
        elif current == self.LEVEL_LOCAL_SEMANTIC:
            return "hybrid"
        elif current == self.LEVEL_BM25_ONLY:
            return "keyword_only"
        else:
            return "file_search"

    def check_and_degrade(self) -> int:
        with self._lock:
            if self.sqlite is not None:
                try:
                    self.sqlite.count_entries()
                except Exception as e:
                    if self._level < self.LEVEL_FILE_SEARCH:
                        self._level = self.LEVEL_FILE_SEARCH
                        logger.warning("operation=degrade, level=file_search, reason=sqlite_unavailable, error=%s", e)
                    return self._level

            if self.embedding_manager:
                em_level = self.embedding_manager.level
                if em_level == EmbeddingManager.LEVEL_BM25_ONLY:
                    if self._level < self.LEVEL_BM25_ONLY:
                        self._level = self.LEVEL_BM25_ONLY
                        logger.warning("operation=degrade, level=bm25_only, reason=embedding_bm25_only")
                elif em_level == EmbeddingManager.LEVEL_LOCAL:
                    if self._level < self.LEVEL_LOCAL_SEMANTIC:
                        self._level = self.LEVEL_LOCAL_SEMANTIC
                        logger.warning("operation=degrade, level=local_semantic, reason=embedding_local")

            if self._level == self.LEVEL_NORMAL:
                if not self.chroma.available:
                    self._level = self.LEVEL_BM25_ONLY
                    logger.warning("operation=degrade, level=bm25_only, reason=chroma_unavailable")
                else:
                    try:
                        self.chroma.search_semantic("test", top_k=1)
                    except Exception:
                        self._level = self.LEVEL_LOCAL_SEMANTIC
                        logger.warning("operation=degrade, level=local_semantic, reason=vector_search_failed")

            return self._level

    def try_recover(self) -> int:
        with self._lock:
            recovered = False
            if self._level == self.LEVEL_FILE_SEARCH and self.sqlite is not None:
                try:
                    self.sqlite.count_entries()
                    self._level = self.LEVEL_BM25_ONLY
                    recovered = True
                    logger.info("operation=recover, level=bm25_only, reason=sqlite_recovered")
                except Exception:
                    return self._level

            if self.embedding_manager:
                self.embedding_manager.check_api_availability()
                em_level = self.embedding_manager.level
                if em_level == EmbeddingManager.LEVEL_API and self._level > self.LEVEL_NORMAL:
                    if self.chroma.available:
                        try:
                            self.chroma.search_semantic("test", top_k=1)
                            self._level = self.LEVEL_NORMAL
                            recovered = True
                            logger.info("operation=recover, level=normal")
                        except Exception:
                            pass
                elif em_level == EmbeddingManager.LEVEL_LOCAL and self._level > self.LEVEL_LOCAL_SEMANTIC:
                    self._level = self.LEVEL_LOCAL_SEMANTIC
                    recovered = True
                    logger.info("operation=recover, level=local_semantic")
            else:
                if self._level >= self.LEVEL_LOCAL_SEMANTIC:
                    if self.chroma.available:
                        try:
                            self.chroma.search_semantic("test", top_k=1)
                            self._level = self.LEVEL_NORMAL
                            recovered = True
                            logger.info("operation=recover, level=normal")
                        except Exception:
                            pass
            return self._level

    def start_periodic_check(self):
        if self._running:
            return
        self._running = True
        t = threading.Thread(target=self._periodic_check_loop, daemon=True)
        t.start()

    def stop_periodic_check(self):
        self._running = False

    def _periodic_check_loop(self):
        while self._running:
            time.sleep(self._check_interval)
            if self._level > self.LEVEL_NORMAL:
                self.try_recover()
            else:
                self.check_and_degrade()
