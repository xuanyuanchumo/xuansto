from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.base import get_db
from ..models.skill_call import SkillCall
from ..models.decision_log import DecisionLog
from ..models.input_output_trace import InputOutputTrace
from ..models.code_change import CodeChange
from ..models.intermediate_artifact import IntermediateArtifact

router = APIRouter()

@router.get("/report/project/{project_id}")
def get_transparency_report(project_id: int, db: Session = Depends(get_db)):
    skill_calls = db.query(SkillCall).filter(SkillCall.details["project_id"].as_integer() == project_id).all()
    
    total_decisions = 0
    total_io_traces = 0
    total_code_changes = 0
    decision_types = {}
    
    for call in skill_calls:
        decisions = db.query(DecisionLog).filter(DecisionLog.skill_call_id == call.id).all()
        total_decisions += len(decisions)
        for d in decisions:
            decision_types[d.decision_type] = decision_types.get(d.decision_type, 0) + 1
        
        io_traces = db.query(InputOutputTrace).filter(InputOutputTrace.skill_call_id == call.id).all()
        total_io_traces += len(io_traces)
        
        code_changes = db.query(CodeChange).filter(CodeChange.skill_call_id == call.id).all()
        total_code_changes += len(code_changes)
    
    artifacts = db.query(IntermediateArtifact).filter(IntermediateArtifact.project_id == project_id).all()
    
    transparency_score = calculate_transparency_score(
        total_decisions, total_io_traces, total_code_changes, len(artifacts), len(skill_calls)
    )
    
    return {
        "project_id": project_id,
        "generated_at": datetime.now().isoformat(),
        "statistics": {
            "total_skill_calls": len(skill_calls),
            "total_decisions": total_decisions,
            "total_io_traces": total_io_traces,
            "total_code_changes": total_code_changes,
            "total_artifacts": len(artifacts),
            "decision_types": decision_types
        },
        "transparency_score": transparency_score
    }

def calculate_transparency_score(decisions, io_traces, code_changes, artifacts, skill_calls):
    if skill_calls == 0:
        return 0
    
    decision_score = min(decisions / skill_calls * 25, 25)
    io_score = min(io_traces / (skill_calls * 2) * 25, 25)
    code_score = min(code_changes / skill_calls * 20, 20)
    artifact_score = min(artifacts / skill_calls * 15, 15)
    reasoning_score = 15
    
    return round(decision_score + io_score + code_score + artifact_score + reasoning_score, 2)
