from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import re
import logging

router = APIRouter(prefix="/api/secrets", tags=["密钥管理"])
logger = logging.getLogger(__name__)

class SecretLoadResponse(BaseModel):
    key: str
    exists: bool
    masked_value: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SecretValidateRequest(BaseModel):
    key: str = Field(..., description="密钥名称")
    value: Optional[str] = Field(default=None, description="待验证的值（可选）")
    check_expiry: bool = Field(default=True, description="是否检查过期")

class SecretValidateResponse(BaseModel):
    key: str
    is_valid: bool
    issues: List[str]
    severity: str
    checked_at: str

class SecretMaskResponse(BaseModel):
    key: str
    original_length: int
    masked_value: str
    mask_type: str

class HardcodedScanRequest(BaseModel):
    content: str = Field(..., description="待扫描的内容")
    file_path: Optional[str] = Field(default=None, description="文件路径（可选）")
    patterns: Optional[List[str]] = Field(default=None, description="自定义检测模式（可选）")

class HardcodedFinding(BaseModel):
    type: str
    severity: str
    line: int
    content: str
    recommendation: str

class HardcodedScanResponse(BaseModel):
    scan_id: str
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    findings: List[HardcodedFinding]
    scanned_at: str
    file_path: Optional[str]

class SecretHealthItem(BaseModel):
    key: str
    status: str
    days_until_expiry: Optional[int] = None
    last_used: Optional[str] = None
    rotation_required: bool

class SecretHealthResponse(BaseModel):
    overall_health: str
    total_secrets: int
    healthy_count: int
    warning_count: int
    critical_count: int
    items: List[SecretHealthItem]
    recommendations: List[str]
    checked_at: str

_secrets_store: Dict[str, Dict[str, Any]] = {
    "DB_PASSWORD": {
        "value": "prod_db_pass_2024",
        "created_at": "2024-01-01T00:00:00",
        "expires_at": "2025-12-31T23:59:59",
        "last_used": "2026-04-05T10:30:00"
    },
    "API_KEY": {
        "value": "sk-prod-api-key-abc123xyz",
        "created_at": "2024-06-15T08:00:00",
        "expires_at": "2026-06-15T08:00:00",
        "last_used": "2026-04-06T09:15:00"
    },
    "JWT_SECRET": {
        "value": "jwt_super_secret_key_2024_production",
        "created_at": "2024-03-01T12:00:00",
        "expires_at": None,
        "last_used": "2026-04-06T08:45:00"
    }
}

SECURITY_PATTERNS: List[tuple] = [
    (r'password\s*=\s*["\'][^"\']+["\']', 'hardcoded_password', 'HIGH', '使用环境变量或密钥管理服务存储密码'),
    (r'api_key\s*=\s*["\'][^"\']+["\']', 'hardcoded_api_key', 'HIGH', '使用环境变量或密钥管理服务存储API密钥'),
    (r'secret\s*=\s*["\'][^"\']+["\']', 'hardcoded_secret', 'HIGH', '使用安全的秘密管理方案'),
    (r'token\s*=\s*["\'][^"\']+["\']', 'hardcoded_token', 'MEDIUM', '使用OAuth或JWT等标准认证机制'),
    (r'eval\(\s*[^)]+\)', 'dangerous_eval', 'HIGH', '避免使用eval()，考虑更安全的替代方案'),
    (r'exec\(\s*[^)]+\)', 'dangerous_exec', 'HIGH', '避免使用exec()，重构代码以避免动态执行'),
    (r'subprocess\.call\(.*shell\s*=\s*True', 'shell_injection', 'HIGH', '避免shell=True，使用列表形式传递参数'),
    (r'os\.system\(', 'os_system_call', 'MEDIUM', '使用subprocess模块替代os.system()'),
    (r'pickle\.loads?\(', 'unsafe_deserialization', 'HIGH', '使用安全的数据格式如JSON替代pickle'),
    (r'yaml\.load\((?!.*Loader)', 'yaml_unsafe_load', 'MEDIUM', '指定安全的Loader，如yaml.safe_load()')
]

@router.get("/{key}", response_model=SecretLoadResponse, summary="加载密钥（脱敏输出）")
async def load_secret(key: str):
    if key not in _secrets_store:
        raise HTTPException(status_code=404, detail=f"密钥 {key} 不存在")
    
    secret = _secrets_store[key]
    value = secret.get("value", "")
    
    if len(value) <= 8:
        masked = "*" * len(value)
    else:
        masked = value[:3] + "*" * (len(value) - 6) + value[-3:]
    
    return SecretLoadResponse(
        key=key,
        exists=True,
        masked_value=masked,
        metadata={
            "created_at": secret.get("created_at"),
            "expires_at": secret.get("expires_at"),
            "last_used": secret.get("last_used")
        }
    )

@router.post("/validate", response_model=SecretValidateResponse, summary="验证密钥有效性")
async def validate_secret(request: SecretValidateRequest):
    issues = []
    severity = "INFO"
    
    if request.key not in _secrets_store:
        return SecretValidateResponse(
            key=request.key,
            is_valid=False,
            issues=[f"密钥 {request.key} 不存在"],
            severity="ERROR",
            checked_at=datetime.now().isoformat()
        )
    
    secret = _secrets_store[request.key]
    
    if request.check_expiry and secret.get("expires_at"):
        expires_at = datetime.fromisoformat(secret["expires_at"])
        if datetime.now() > expires_at:
            issues.append("密钥已过期")
            severity = "CRITICAL"
        elif (expires_at - datetime.now()).days < 30:
            issues.append(f"密钥将在 {(expires_at - datetime.now()).days} 天后过期")
            if severity != "CRITICAL":
                severity = "WARNING"
    
    if request.value is not None:
        stored_value = secret.get("value", "")
        if request.value != stored_value:
            issues.append("提供的值与存储的值不匹配")
            if severity not in ["CRITICAL", "ERROR"]:
                severity = "WARNING"
    
    if not issues:
        issues.append("密钥验证通过")
    
    return SecretValidateResponse(
        key=request.key,
        is_valid=severity not in ["CRITICAL", "ERROR"],
        issues=issues,
        severity=severity,
        checked_at=datetime.now().isoformat()
    )

@router.get("/mask/{key}", response_model=SecretMaskResponse, summary="获取脱敏后的密钥值")
async def mask_secret(key: str):
    if key not in _secrets_store:
        raise HTTPException(status_code=404, detail=f"密钥 {key} 不存在")
    
    value = _secrets_store[key].get("value", "")
    original_length = len(value)
    
    if original_length <= 4:
        masked = "*" * original_length
        mask_type = "full_mask"
    elif original_length <= 16:
        masked = value[:2] + "*" * (original_length - 4) + value[-2:]
        mask_type = "partial_mask"
    else:
        masked = value[:4] + "*" * (original_length - 8) + value[-4:]
        mask_type = "partial_mask"
    
    return SecretMaskResponse(
        key=key,
        original_length=original_length,
        masked_value=masked,
        mask_type=mask_type
    )

@router.post("/scan", response_model=HardcodedScanResponse, summary="硬编码敏感信息扫描")
async def scan_hardcoded(request: HardcodedScanRequest):
    import uuid
    
    scan_id = f"scan_{uuid.uuid4().hex[:8]}"
    findings = []
    
    patterns_to_use = SECURITY_PATTERNS
    if request.patterns:
        custom_patterns = [(p, 'custom_pattern', 'MEDIUM', '请审查此模式') for p in request.patterns]
        patterns_to_use = patterns_to_use + custom_patterns
    
    content = request.content
    lines = content.split('\n')
    
    for pattern, issue_type, severity, recommendation in patterns_to_use:
        for line_idx, line in enumerate(lines, 1):
            matches = re.finditer(pattern, line)
            for match in matches:
                findings.append(HardcodedFinding(
                    type=issue_type,
                    severity=severity,
                    line=line_idx,
                    content=match.group()[:100],
                    recommendation=recommendation
                ))
    
    critical_count = sum(1 for f in findings if f.severity == "HIGH")
    high_count = critical_count
    medium_count = sum(1 for f in findings if f.severity == "MEDIUM")
    low_count = sum(1 for f in findings if f.severity == "LOW")
    
    logger.info(f"扫描完成: {scan_id}, 发现 {len(findings)} 个问题 ({critical_count} 严重)")
    
    return HardcodedScanResponse(
        scan_id=scan_id,
        total_findings=len(findings),
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        findings=findings[:50],
        scanned_at=datetime.now().isoformat(),
        file_path=request.file_path
    )

@router.get("/health", response_model=SecretHealthResponse, summary="密钥健康度检查")
async def secrets_health():
    items = []
    healthy_count = 0
    warning_count = 0
    critical_count = 0
    recommendations = []
    
    now = datetime.now()
    
    for key, secret in _secrets_store.items():
        status = "healthy"
        days_until_expiry = None
        rotation_required = False
        
        expires_at_str = secret.get("expires_at")
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str)
            days_until_expiry = (expires_at - now).days
            
            if days_until_expiry < 0:
                status = "critical"
                critical_count += 1
                rotation_required = True
            elif days_until_expiry < 30:
                status = "warning"
                warning_count += 1
                rotation_required = True
            else:
                healthy_count += 1
        else:
            healthy_count += 1
        
        last_used_str = secret.get("last_used")
        
        items.append(SecretHealthItem(
            key=key,
            status=status,
            days_until_expiry=days_until_expiry,
            last_used=last_used_str,
            rotation_required=rotation_required
        ))
    
    if critical_count > 0:
        recommendations.append(f"有 {critical_count} 个密钥已过期，需要立即轮换")
        overall_health = "critical"
    elif warning_count > 0:
        recommendations.append(f"有 {warning_count} 个密钥即将到期，建议提前轮换")
        overall_health = "warning"
    else:
        overall_health = "healthy"
        recommendations.append("所有密钥状态良好")
    
    if len(_secrets_store) > 10:
        recommendations.append("建议定期清理不再使用的密钥")
    
    return SecretHealthResponse(
        overall_health=overall_health,
        total_secrets=len(_secrets_store),
        healthy_count=healthy_count,
        warning_count=warning_count,
        critical_count=critical_count,
        items=items,
        recommendations=recommendations,
        checked_at=now.isoformat()
    )
