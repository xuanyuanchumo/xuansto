from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
import re
import logging

router = APIRouter(prefix="/api/defense", tags=["四维防线"])
logger = logging.getLogger(__name__)

class LayerStatusInfo(BaseModel):
    layer_name: str
    layer_number: int
    status: str = Field(..., description="passed/warning/failed/skipped")
    score: float
    message: str
    last_check_time: str
    duration_ms: float

class DefenseStatusResponse(BaseModel):
    overall_status: str
    overall_score: float
    layers: List[LayerStatusInfo]
    last_full_check: str
    active_alerts_count: int

class QualityScoreResponse(BaseModel):
    current_score: float
    max_score: float
    trend: str = Field(..., description="improving/stable/declining")
    history: List[Dict[str, Any]]
    dimension_scores: Dict[str, float]
    last_updated: str

class AlertItem(BaseModel):
    alert_id: str
    layer: str
    severity: str = Field(..., description="info/warning/error/critical")
    title: string
    message: str
    timestamp: str
    resolved: bool

class AlertsResponse(BaseModel):
    total_alerts: int
    unresolved_count: int
    alerts: List[AlertItem]
    filtered_by: Optional[str] = None

class DefenseCheckRequest(BaseModel):
    input_text: str = Field(..., description="待检查的输入文本")
    context: Optional[Dict[str, Any]] = Field(default=None, description="上下文信息")
    full_check: bool = Field(default=True, description="是否执行完整检查")

class DefenseCheckResponse(BaseModel):
    check_id: str
    success: bool
    overall_score: float
    intent_type: str
    layers_result: List[Dict[str, Any]]
    fallback_strategy: Optional[str] = None
    total_duration_ms: float
    checked_at: str

_layer_states = {
    "PromptLayer": {
        "layer_name": "PromptLayer",
        "layer_number": 1,
        "status": "passed",
        "score": 0.85,
        "message": "意图识别完成，置信度良好",
        "last_check_time": datetime.now().isoformat(),
        "duration_ms": 45.2
    },
    "CapabilityLayer": {
        "layer_name": "CapabilityLayer",
        "layer_number": 2,
        "status": "passed",
        "score": 0.78,
        "message": "能力约束检查通过，技能匹配度良好",
        "last_check_time": datetime.now().isoformat(),
        "duration_ms": 32.5
    },
    "RuleValidationLayer": {
        "layer_name": "RuleValidationLayer",
        "layer_number": 3,
        "status": "warning",
        "score": 0.72,
        "message": "发现少量编码规范问题",
        "last_check_time": datetime.now().isoformat(),
        "duration_ms": 58.7
    },
    "FallbackRecoveryLayer": {
        "layer_name": "FallbackRecoveryLayer",
        "layer_number": 4,
        "status": "passed",
        "score": 4.2,
        "message": "质量评分达标，无需降级",
        "last_check_time": datetime.now().isoformat(),
        "duration_ms": 23.1
    }
}

_alerts_store: List[Dict[str, Any]] = [
    {
        "alert_id": "alert_001",
        "layer": "RuleValidationLayer",
        "severity": "warning",
        "title": "编码规范警告",
        "message": "检测到部分代码行长度超过120字符限制",
        "timestamp": (datetime.now().__sub__(__import__('datetime').timedelta(minutes=5))).isoformat(),
        "resolved": False
    },
    {
        "alert_id": "alert_002",
        "layer": "CapabilityLayer",
        "severity": "info",
        "title": "知识库覆盖提示",
        "message": "当前请求涉及的技术栈在知识库中覆盖度较低",
        "timestamp": (datetime.now().__sub(__import__('datetime').timedelta(minutes=15))).isoformat(),
        "resolved": True
    }
]

_score_history: List[Dict[str, Any]] = []
_dimension_scores = {
    "completeness": 4.2,
    "accuracy": 4.0,
    "clarity": 4.3,
    "actionability": 3.8,
    "safety": 4.5
}

@router.get("/status", response_model=DefenseStatusResponse, summary="获取四维防线各层状态")
async def get_defense_status():
    layers = []
    total_score = 0
    failed_count = 0
    
    for layer_name, state in _layer_states.items():
        layers.append(LayerStatusInfo(**state))
        total_score += state["score"]
        if state["status"] == "failed":
            failed_count += 1
    
    avg_score = total_score / len(_layer_states) if _layer_states else 0
    
    if failed_count > 0:
        overall_status = "failed"
    elif any(l.status == "warning" for l in layers):
        overall_status = "warning"
    else:
        overall_status = "passed"
    
    unresolved_alerts = sum(1 for a in _alerts_store if not a.get("resolved", False))
    
    return DefenseStatusResponse(
        overall_status=overall_status,
        overall_score=round(avg_score, 2),
        layers=layers,
        last_full_check=datetime.now().isoformat(),
        active_alerts_count=unresolved_alerts
    )

@router.get("/quality-score", response_model=QualityScoreResponse, summary="获取质量评分及趋势")
async def get_quality_score():
    import random
    
    current_score = sum(_dimension_scores.values()) / len(_dimension_scores)
    
    now = datetime.now()
    new_entry = {
        "timestamp": now.isoformat(),
        "score": round(current_score, 2),
        "dimensions": dict(_dimension_scores)
    }
    
    _score_history.append(new_entry)
    if len(_score_history) > 100:
        _score_history.pop(0)
    
    trend = "stable"
    if len(_score_history) >= 5:
        recent = [h["score"] for h in _score_history[-5:]]
        if recent[-1] > recent[0] + 0.1:
            trend = "improving"
        elif recent[-1] < recent[0] - 0.1:
            trend = "declining"
    
    return QualityScoreResponse(
        current_score=round(current_score, 2),
        max_score=5.0,
        trend=trend,
        history=_score_history[-20:],
        dimension_scores=dict(_dimension_scores),
        last_updated=now.isoformat()
    )

@router.get("/alerts", response_model=AlertsResponse, summary="获取告警信息")
async def get_alerts(severity: Optional[str] = None, resolved: Optional[bool] = None):
    filtered_alerts = list(_alerts_store)
    
    if severity:
        filtered_alerts = [a for a in filtered_alerts if a.get("severity") == severity]
    
    if resolved is not None:
        filtered_alerts = [a for a in filtered_alerts if a.get("resolved") == resolved]
    
    alerts = [
        AlertItem(**alert) for alert in sorted(
            filtered_alerts,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
    ]
    
    unresolved_count = sum(1 for a in _alerts_store if not a.get("resolved", False))
    
    return AlertsResponse(
        total_alerts=len(_alerts_store),
        unresolved_count=unresolved_count,
        alerts=alerts[:50],
        filtered_by=severity
    )

@router.post("/check", response_model=DefenseCheckResponse, summary="手动触发防线检查")
async def trigger_defense_check(request: DefenseCheckRequest):
    import uuid
    import hashlib
    
    check_id = f"check_{uuid.uuid4().hex[:8]}"
    start_time = time.time()
    
    input_text = request.input_text
    context = request.context or {}
    
    layers_result = []
    
    prompt_score = _evaluate_prompt_layer(input_text, context)
    layers_result.append({
        "layer_name": "PromptLayer",
        "layer_number": 1,
        "status": "passed" if prompt_score >= 0.7 else "warning",
        "score": prompt_score,
        "message": f"Prompt层处理完成，得分: {prompt_score:.2f}",
        "duration_ms": (time.time() - start_time) * 1000 / 4
    })
    
    capability_score = _evaluate_capability_layer(input_text, context)
    layers_result.append({
        "layer_name": "CapabilityLayer",
        "layer_number": 2,
        "status": "passed" if capability_score >= 0.7 else ("failed" if capability_score < 0.5 else "warning"),
        "score": capability_score,
        "message": f"能力约束检查完成，匹配度: {capability_score:.2f}",
        "duration_ms": (time.time() - start_time) * 1000 / 4
    })
    
    rule_score, security_issues = _evaluate_rule_validation_layer(input_text)
    layers_result.append({
        "layer_name": "RuleValidationLayer",
        "layer_number": 3,
        "status": "failed" if security_issues > 0 else ("passed" if rule_score >= 0.7 else "warning"),
        "score": rule_score,
        "message": f"规则校验完成，发现{security_issues}个安全问题",
        "duration_ms": (time.time() - start_time) * 1000 / 4
    })
    
    quality_score = _evaluate_fallback_layer(input_text)
    layers_result.append({
        "layer_name": "FallbackRecoveryLayer",
        "layer_number": 4,
        "status": "passed" if quality_score >= 3.5 else "warning",
        "score": quality_score,
        "message": f"质量评分: {quality_score:.1f}/5.0",
        "duration_ms": (time.time() - start_time) * 1000 / 4
    })
    
    total_duration = (time.time() - start_time) * 1000
    all_scores = [l["score"] for l in layers_result]
    overall_score = sum(all_scores) / len(all_scores)
    
    success = all(l["status"] != "failed" for l in layers_result) and overall_score >= 0.6
    
    fallback_strategy = None
    if not success or quality_score < 3.5:
        if quality_score < 2.5:
            fallback_strategy = "request_human_help"
        elif quality_score < 3.5:
            fallback_strategy = "simplify_task"
    
    intent_type = _identify_intent(input_text)
    
    logger.info(f"防线检查完成: {check_id}, 成功: {success}, 得分: {overall_score:.2f}")
    
    return DefenseCheckResponse(
        check_id=check_id,
        success=success,
        overall_score=round(overall_score, 2),
        intent_type=intent_type,
        layers_result=layers_result,
        fallback_strategy=fallback_strategy,
        total_duration_ms=round(total_duration, 1),
        checked_at=datetime.now().isoformat()
    )

def _evaluate_prompt_layer(text: str, context: Dict[str, Any]) -> float:
    score = 1.0
    
    if not text or len(text.strip()) < 3:
        score -= 0.3
    
    dangerous_patterns = [r'rm\s+-rf', r'DROP\s+TABLE', r'eval\(', r'__import__']
    for pattern in dangerous_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            score -= 0.15
    
    ambiguity_indicators = ['可能', '也许', '大概', '或者']
    count = sum(1 for ind in ambiguity_indicators if ind in text)
    score -= min(0.3, count * 0.05)
    
    return max(0.0, min(1.0, score))

def _evaluate_capability_layer(text: str, context: Dict[str, Any]) -> float:
    tech_keywords = ['python', 'javascript', 'react', 'vue', 'django', 'fastapi', 
                     'docker', 'git', 'sql', 'redis', 'api', 'database']
    found = sum(1 for kw in tech_keywords if kw.lower() in text.lower())
    
    base_score = min(1.0, found * 0.08 + 0.4)
    
    code_indicators = len(re.findall(r'\b(def|class|function|import|const|let)\b', text.lower()))
    base_score += min(0.2, code_indicators * 0.02)
    
    return max(0.0, min(1.0, base_score))

def _evaluate_rule_validation_layer(text: str) -> tuple:
    security_patterns = [
        r'password\s*=\s*["\']',
        r'api_key\s*=\s*["\']',
        r'secret\s*=\s*["\']',
        r'eval\(',
        r'exec\(',
        r'subprocess\.call\(.*shell\s*=\s*True'
    ]
    
    issue_count = 0
    for pattern in security_patterns:
        if re.search(pattern, text):
            issue_count += 1
    
    score = max(0.0, 1.0 - issue_count * 0.2)
    
    line_length_issues = sum(1 for line in text.split('\n') if len(line.rstrip()) > 120)
    score -= min(0.2, line_length_issues * 0.02)
    
    return max(0.0, score), issue_count

def _evaluate_fallback_layer(text: str) -> float:
    scores = {
        'completeness': 4.0,
        'accuracy': 4.0,
        'clarity': 4.0,
        'actionability': 3.8,
        'safety': 4.2
    }
    
    if len(text) < 50:
        scores['completeness'] -= 1.0
    
    has_code = bool(re.search(r'```[\s\S]*?```', text))
    has_structure = bool(re.search(r'(?:^|\n)\s*(?:#{1,3}|\d+[.)])', text))
    
    if not has_code and not has_structure:
        scores['completeness'] -= 1.0
        scores['actionability'] -= 0.5
    
    dangerous = [r'rm\s+-rf\s+/', r'DROP\s+DATABASE', r'>\s*/etc/']
    for pattern in dangerous:
        if re.search(pattern, text, re.IGNORECASE):
            scores['safety'] -= 2.0
    
    global _dimension_scores
    _dimension_scores = {k: max(0, v) for k, v in scores.items()}
    
    return sum(scores.values()) / len(scores)

def _identify_intent(text: str) -> str:
    intents = {
        'code_generation': [r'创建|生成|新建|实现|开发|编写.*代码|函数|类'],
        'refactoring': [r'重构|优化|改进|整理|简化.*代码|结构'],
        'documentation': [r'文档|注释|说明|README|API文档'],
        'testing': [r'测试|单元测试|集成测试|测试用例|pytest'],
        'deployment': [r'部署|发布|上线|CI/CD|Docker'],
        'debugging': [r'调试|排查|修复|bug|错误|异常']
    }
    
    text_lower = text.lower()
    best_intent = 'unknown'
    max_matches = 0
    
    for intent, patterns in intents.items():
        matches = sum(1 for p in patterns if re.search(p, text_lower))
        if matches > max_matches:
            max_matches = matches
            best_intent = intent
    
    return best_intent
