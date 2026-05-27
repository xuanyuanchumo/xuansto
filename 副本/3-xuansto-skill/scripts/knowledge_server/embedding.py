import logging
import os
import threading
import time

from .config import openai_available, sentence_transformers_available

logger = logging.getLogger("knowledge-server")

if openai_available:
    from .config import _openai_module

if sentence_transformers_available:
    from .config import _STModel


class EmbeddingManager:
    LEVEL_API = 0
    LEVEL_LOCAL = 1
    LEVEL_BM25_ONLY = 2

    LEVEL_NAMES = {0: "api", 1: "local_semantic", 2: "bm25_only"}
    LEVEL_DIMENSIONS = {0: 1536, 1: 384, 2: 0}

    def __init__(self, config):
        self.config = config
        self._level = self.LEVEL_BM25_ONLY
        self._openai_client = None
        self._local_model = None
        self._lock = threading.Lock()
        self._last_api_check = 0.0
        self._api_check_interval = 300
        self._init_primary()
        self._init_fallback()

    def _init_primary(self):
        if not openai_available:
            logger.info("operation=embedding_init, level=api, status=openai_not_installed")
            return
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.info("operation=embedding_init, level=api, status=no_api_key")
            return
        try:
            self._openai_client = _openai_module.OpenAI(api_key=api_key)
            self._openai_client.embeddings.create(
                model="text-embedding-3-small",
                input="ping",
            )
            self._level = self.LEVEL_API
            logger.info("operation=embedding_init, level=api, model=text-embedding-3-small, dim=1536")
        except Exception as e:
            logger.warning("operation=embedding_init, level=api, status=probe_failed, error=%s", e)
            self._openai_client = None

    def _init_fallback(self):
        if self._level == self.LEVEL_API:
            return
        if not sentence_transformers_available:
            logger.info("operation=embedding_init, level=local, status=sentence_transformers_not_installed")
            return
        try:
            self._local_model = _STModel("all-MiniLM-L6-v2")
            self._level = self.LEVEL_LOCAL
            logger.info("operation=embedding_init, level=local, model=all-MiniLM-L6-v2, dim=384")
        except Exception as e:
            logger.warning("operation=embedding_init, level=local, status=failed, error=%s", e)
            self._local_model = None

    @property
    def level(self) -> int:
        with self._lock:
            return self._level

    @property
    def level_name(self) -> str:
        return self.LEVEL_NAMES.get(self.level, "unknown")

    @property
    def dimension(self) -> int:
        return self.LEVEL_DIMENSIONS.get(self.level, 0)

    @property
    def degraded(self) -> bool:
        return self.level > self.LEVEL_API

    def generate_embedding(self, text: str):
        current_level = self.level
        if current_level == self.LEVEL_API:
            return self._generate_api(text)
        elif current_level == self.LEVEL_LOCAL:
            return self._generate_local(text)
        return None, 0

    def _generate_api(self, text: str):
        try:
            response = self._openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
            )
            return response.data[0].embedding, 1536
        except Exception as e:
            logger.warning("operation=embedding_api_failed, error=%s", e)
            self._degrade()
            return self.generate_embedding(text)

    def _generate_local(self, text: str):
        try:
            embedding = self._local_model.encode(text).tolist()
            return embedding, 384
        except Exception as e:
            logger.warning("operation=embedding_local_failed, error=%s", e)
            self._degrade()
            return None, 0

    def _degrade(self):
        with self._lock:
            if self._level == self.LEVEL_API:
                self._level = self.LEVEL_LOCAL
                if self._local_model is None and sentence_transformers_available:
                    try:
                        self._local_model = _STModel("all-MiniLM-L6-v2")
                    except Exception:
                        self._level = self.LEVEL_BM25_ONLY
                elif self._local_model is None:
                    self._level = self.LEVEL_BM25_ONLY
                logger.warning("operation=embedding_degrade, new_level=%d", self._level)
            elif self._level == self.LEVEL_LOCAL:
                self._level = self.LEVEL_BM25_ONLY
                logger.warning("operation=embedding_degrade, new_level=bm25_only")

    def check_api_availability(self) -> bool:
        if self.level == self.LEVEL_API:
            return True
        now = time.time()
        if now - self._last_api_check < self._api_check_interval:
            return False
        self._last_api_check = now
        if not openai_available:
            return False
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return False
        try:
            if self._openai_client is None:
                self._openai_client = _openai_module.OpenAI(api_key=api_key)
            self._openai_client.embeddings.create(
                model="text-embedding-3-small",
                input="ping",
            )
            with self._lock:
                old_level = self._level
                self._level = self.LEVEL_API
            if old_level != self.LEVEL_API:
                logger.info("operation=embedding_recover, old_level=%d, new_level=api", old_level)
                return True
        except Exception:
            pass
        return False
