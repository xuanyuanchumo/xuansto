from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'scripts'))

from ..models.base import get_db
from ..models.requirement_trace import RequirementTrace

router = APIRouter()

class RequirementTraceCreate(BaseModel):
    project_id: int
    requirement_id: str
    requirement_title: Optional[str] = None
    feature_id: Optional[str] = None
    feature_title: Optional[str] = None
    trace_type: Optional[str] = None
    test_case_id: Optional[str] = None

class RequirementParseRequest(BaseModel):
    content: str
    requirement_type: Optional[str] = None

class BusinessRuleExtractRequest(BaseModel):
    content: str
    requirement_id: Optional[str] = None

class TraceMatrixRequest(BaseModel):
    project_id: int
    include_details: bool = True

class RequirementTraceResponse(BaseModel):
    id: int
    project_id: int
    requirement_id: str
    requirement_title: Optional[str]
    feature_id: Optional[str]
    feature_title: Optional[str]
    trace_type: Optional[str]
    status: str
    test_case_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=RequirementTraceResponse)
def create_trace(trace: RequirementTraceCreate, db: Session = Depends(get_db)):
    db_trace = RequirementTrace(**trace.model_dump())
    db.add(db_trace)
    db.commit()
    db.refresh(db_trace)
    return db_trace

@router.get("/project/{project_id}", response_model=List[RequirementTraceResponse])
def get_traces_by_project(project_id: int, status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(RequirementTrace).filter(RequirementTrace.project_id == project_id)
    if status:
        query = query.filter(RequirementTrace.status == status)
    return query.all()

@router.get("/coverage/{project_id}")
def get_coverage_report(project_id: int, db: Session = Depends(get_db)):
    traces = db.query(RequirementTrace).filter(RequirementTrace.project_id == project_id).all()
    total = len(traces)
    covered = len([t for t in traces if t.status == "covered"])
    verified = len([t for t in traces if t.status == "verified"])
    return {
        "project_id": project_id,
        "total_requirements": total,
        "covered": covered,
        "verified": verified,
        "coverage_rate": round(covered / total * 100, 2) if total > 0 else 0,
        "verification_rate": round(verified / total * 100, 2) if total > 0 else 0
    }

@router.put("/{trace_id}/status", response_model=RequirementTraceResponse)
def update_trace_status(trace_id: int, status: str, db: Session = Depends(get_db)):
    trace = db.query(RequirementTrace).filter(RequirementTrace.id == trace_id).first()
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    trace.status = status
    db.commit()
    db.refresh(trace)
    return trace

@router.post("/parse")
def parse_requirement(request: RequirementParseRequest):
    try:
        from requirement_parser import RequirementParser, RequirementType
        
        parser = RequirementParser()
        req_type = None
        if request.requirement_type:
            try:
                req_type = RequirementType(request.requirement_type)
            except ValueError:
                pass
        
        result = parser.parse(request.content, req_type)
        return {
            "success": True,
            "data": result.to_dict()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/extract-rules")
def extract_business_rules(request: BusinessRuleExtractRequest):
    try:
        from business_rule_extractor import BusinessRuleExtractor
        
        extractor = BusinessRuleExtractor()
        rules = extractor.extract_from_requirement(request.content, request.requirement_id or "")
        
        return {
            "success": True,
            "data": {
                "rules": [r.to_dict() for r in rules],
                "total": len(rules)
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/recognize-rules")
def recognize_business_rules(content: str):
    try:
        from business_rule_recognizer import BusinessRuleRecognizer, RecognitionMethod
        
        recognizer = BusinessRuleRecognizer()
        result = recognizer.recognize(content, RecognitionMethod.HYBRID)
        
        return {
            "success": True,
            "data": result.to_dict()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/generate-spec")
def generate_specification(
    project_name: str,
    author: str = "系统生成",
    requirements: List[Dict[str, Any]] = [],
    business_rules: List[Dict[str, Any]] = []
):
    try:
        from requirement_spec_generator import SpecificationGenerator
        from requirement_parser import ParsedRequirement, UserStory, FunctionalPoint, DataModel, AcceptanceCriteria, RequirementType, RequirementFormat
        from business_rule_extractor import BusinessRule
        
        generator = SpecificationGenerator(project_name, author)
        
        for req_data in requirements:
            req = ParsedRequirement(
                id=req_data.get("id", ""),
                title=req_data.get("title", ""),
                description=req_data.get("description", ""),
                requirement_type=RequirementType(req_data.get("requirement_type", "functional")),
                source_format=RequirementFormat(req_data.get("source_format", "natural_language"))
            )
            generator.add_requirement(req)
        
        spec_markdown = generator.generate_markdown()
        
        return {
            "success": True,
            "data": {
                "markdown": spec_markdown,
                "json": generator.generate_json()
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/matrix")
def get_trace_matrix(request: TraceMatrixRequest, db: Session = Depends(get_db)):
    try:
        from requirement_trace_manager import RequirementTraceManager
        
        traces = db.query(RequirementTrace).filter(
            RequirementTrace.project_id == request.project_id
        ).all()
        
        matrix_data = {
            "requirements": [
                {
                    "id": t.requirement_id,
                    "name": t.requirement_title or t.requirement_id,
                    "status": t.status,
                    "requirement_type": t.trace_type or "functional"
                }
                for t in traces
            ],
            "test_cases": [
                {
                    "id": t.test_case_id,
                    "name": f"测试-{t.test_case_id}",
                    "status": t.status
                }
                for t in traces if t.test_case_id
            ],
            "trace_links": [
                {
                    "source_id": t.requirement_id,
                    "target_id": t.test_case_id,
                    "trace_type": t.trace_type or "requirement_to_test",
                    "status": t.status
                }
                for t in traces if t.test_case_id
            ],
            "coverage_stats": {
                "total_requirements": len(traces),
                "covered_requirements": len([t for t in traces if t.status == "covered"]),
                "verified_requirements": len([t for t in traces if t.status == "verified"])
            }
        }
        
        return {
            "success": True,
            "data": matrix_data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/visualize")
def visualize_trace_matrix(matrix_data: Dict[str, Any]):
    try:
        from trace_matrix_visualizer import TraceMatrixVisualizer
        
        visualizer = TraceMatrixVisualizer()
        visualization = visualizer.generate_visualization(matrix_data)
        
        return {
            "success": True,
            "data": visualization.to_dict()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/report")
def generate_trace_report(
    project_name: str,
    matrix_data: Dict[str, Any],
    report_type: str = "summary"
):
    try:
        from trace_report_generator import TraceReportGenerator, ReportType
        
        generator = TraceReportGenerator()
        
        if report_type == "detailed":
            report = generator.generate_detailed_report(matrix_data, project_name)
        elif report_type == "gap_analysis":
            report = generator.generate_gap_analysis_report(matrix_data, project_name)
        else:
            report = generator.generate_summary_report(matrix_data, project_name)
        
        return {
            "success": True,
            "data": {
                "markdown": generator.to_markdown(report),
                "json": generator.to_json(report)
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
