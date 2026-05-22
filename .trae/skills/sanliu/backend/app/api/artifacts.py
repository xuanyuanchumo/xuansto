from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..models.base import get_db
from ..models.intermediate_artifact import IntermediateArtifact

router = APIRouter()

class ArtifactCreate(BaseModel):
    project_id: int
    skill_call_id: Optional[int] = None
    artifact_type: str
    name: str
    content: Optional[str] = None
    file_path: Optional[str] = None
    metadata: Optional[dict] = None

class ArtifactResponse(BaseModel):
    id: int
    project_id: int
    skill_call_id: Optional[int]
    artifact_type: str
    name: str
    content: Optional[str]
    file_path: Optional[str]
    metadata: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=ArtifactResponse)
def create_artifact(artifact: ArtifactCreate, db: Session = Depends(get_db)):
    db_artifact = IntermediateArtifact(**artifact.model_dump())
    db.add(db_artifact)
    db.commit()
    db.refresh(db_artifact)
    return db_artifact

@router.get("/project/{project_id}", response_model=List[ArtifactResponse])
def get_artifacts_by_project(project_id: int, artifact_type: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(IntermediateArtifact).filter(IntermediateArtifact.project_id == project_id)
    if artifact_type:
        query = query.filter(IntermediateArtifact.artifact_type == artifact_type)
    return query.all()

@router.get("/{artifact_id}", response_model=ArtifactResponse)
def get_artifact(artifact_id: int, db: Session = Depends(get_db)):
    artifact = db.query(IntermediateArtifact).filter(IntermediateArtifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact
