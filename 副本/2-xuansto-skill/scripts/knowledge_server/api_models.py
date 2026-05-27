import logging
from typing import Optional

from .config import fastapi_available, KB_VERSION, make_response, make_error_response, AGENT_RETRIEVAL_PROFILES
from .security import InputValidator, SensitiveContentFilter

logger = logging.getLogger("knowledge-server")

if fastapi_available:
    from pydantic import BaseModel, Field, field_validator

    class SearchRequest(BaseModel):
        query: str
        scope: Optional[str] = None
        top_k: int = Field(default=5, ge=1, le=20)
        strategy: str = Field(default="hybrid")
        filters: Optional[dict] = None
        agent_role: Optional[str] = None

        @field_validator("strategy")
        @classmethod
        def validate_strategy(cls, v):
            if v not in ("hybrid", "semantic_only", "keyword_only"):
                raise ValueError("strategy必须是hybrid/semantic_only/keyword_only")
            return v

        @field_validator("scope")
        @classmethod
        def validate_scope(cls, v):
            if v is not None and v not in ("general", "workspace", "experience"):
                raise ValueError("scope必须是general/workspace/experience")
            return v

        @field_validator("agent_role")
        @classmethod
        def validate_agent_role(cls, v):
            if v is not None and v not in AGENT_RETRIEVAL_PROFILES:
                raise ValueError(f"agent_role必须是: {', '.join(AGENT_RETRIEVAL_PROFILES.keys())}")
            return v

    class AddRequest(BaseModel):
        title: str
        content: str
        scope: str = Field(default="workspace")
        tags: list[str] = Field(default_factory=list)
        source_path: Optional[str] = None
        source_rating: int = Field(default=3, ge=1, le=5)
        type: str = Field(default="unknown")
        category: str = Field(default="uncategorized")
        summary: Optional[str] = None
        content_path: Optional[str] = None

        @field_validator("scope")
        @classmethod
        def validate_scope(cls, v):
            if v not in ("general", "workspace", "experience"):
                raise ValueError("scope必须是general/workspace/experience")
            return v

    class UpdateRequest(BaseModel):
        title: Optional[str] = None
        content: Optional[str] = None
        tags: Optional[list[str]] = None
        confidence: Optional[float] = Field(default=None, ge=0, le=1)
        source_rating: Optional[int] = Field(default=None, ge=1, le=5)
        type: Optional[str] = None
        category: Optional[str] = None
        summary: Optional[str] = None
        content_path: Optional[str] = None
        success_count: Optional[int] = None
        failure_count: Optional[int] = None
        version: Optional[int] = None

    class BackupRequest(BaseModel):
        type: str = Field(default="full")
        destination: Optional[str] = None

        @field_validator("type")
        @classmethod
        def validate_type(cls, v):
            if v not in ("full", "incremental", "snapshot"):
                raise ValueError("type必须是full/incremental/snapshot")
            return v

    class RollbackVersionRequest(BaseModel):
        entry_id: str
        target_version: int = Field(ge=1)
else:
    SearchRequest = None
    AddRequest = None
    UpdateRequest = None
    BackupRequest = None
    RollbackVersionRequest = None
