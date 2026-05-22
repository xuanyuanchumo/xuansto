"""
增强的技能文档更新器 (Phase 9.1)

核心功能:
1. 文档同步检测 - 检测代码与文档的同步状态
2. 自动更新过时内容 - 识别并更新过时的文档内容
3. 文档完整性验证 - 确保文档的完整性和一致性
4. 多格式支持 - 支持Markdown、JSON、YAML等格式

增强特性:
- 智能变更检测算法
- 差异化分析引擎
- 版本化文档管理
- 自动生成变更日志
- 跨文件引用验证
"""

import os
import re
import json
import sys
import hashlib
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
from collections import defaultdict
import difflib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class DocumentType(Enum):
    SKILL_DEFINITION = "skill_definition"
    API_DOCUMENTATION = "api_documentation"
    USER_GUIDE = "user_guide"
    CHANGELOG = "changelog"
    ARCHITECTURE_DOC = "architecture_doc"
    TEST_DOCUMENTATION = "test_documentation"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


class SyncStatus(Enum):
    SYNCED = "synced"
    OUTDATED = "outdated"
    MISSING = "missing"
    CONFLICT = "conflict"
    ERROR = "error"


class UpdateSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class DocumentInfo:
    """文档信息"""
    file_path: Path
    doc_type: DocumentType
    last_modified: datetime
    content_hash: str
    size_bytes: int
    line_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'file_path': str(self.file_path),
            'doc_type': self.doc_type.value,
            'last_modified': self.last_modified.isoformat(),
            'content_hash': self.content_hash,
            'size_bytes': self.size_bytes,
            'line_count': self.line_count,
            'metadata': self.metadata
        }


@dataclass
class SyncDetectionResult:
    """同步检测结果"""
    detection_id: str
    timestamp: str
    documents_analyzed: int
    synced_docs: List[DocumentInfo]
    outdated_docs: List[Dict[str, Any]]
    missing_docs: List[str]
    conflicts: List[Dict[str, Any]]
    summary: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'detection_id': self.detection_id,
            'timestamp': self.timestamp,
            'documents_analyzed': self.documents_analyzed,
            'synced_docs': [d.to_dict() for d in self.synced_docs],
            'outdated_docs': self.outdated_docs,
            'missing_docs': self.missing_docs,
            'conflicts': self.conflicts,
            'summary': self.summary
        }


@dataclass
class UpdateAction:
    """更新操作"""
    action_id: str
    target_file: Path
    action_type: str
    severity: UpdateSeverity
    description: str
    changes: List[Dict[str, Any]]
    auto_applicable: bool
    risk_level: str
    estimated_effort_minutes: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'action_id': self.action_id,
            'target_file': str(self.target_file),
            'action_type': self.action_type,
            'severity': self.severity.value,
            'description': self.description,
            'changes': self.changes,
            'auto_applicable': self.auto_applicable,
            'risk_level': self.risk_level,
            'estimated_effort_minutes': self.estimated_effort_minutes
        }


@dataclass
class UpdateResult:
    """更新结果"""
    result_id: str
    update_actions: List[UpdateAction]
    successful_updates: List[Dict[str, Any]]
    failed_updates: List[Dict[str, Any]]
    skipped_updates: List[Dict[str, Any]]
    summary: Dict[str, Any]
    changelog_entries: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'result_id': self.result_id,
            'update_actions': [a.to_dict() for a in self.update_actions],
            'successful_updates': self.successful_updates,
            'failed_updates': self.failed_updates,
            'skipped_updates': self.skipped_updates,
            'summary': self.summary,
            'changelog_entries': self.changelog_entries
        }


@dataclass
class ValidationReport:
    """验证报告"""
    report_id: str
    validated_at: str
    total_documents: int
    valid_documents: int
    invalid_documents: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    completeness_score: float
    consistency_score: float
    overall_health: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'report_id': self.report_id,
            'validated_at': self.validated_at,
            'total_documents': self.total_documents,
            'valid_documents': self.valid_documents,
            'invalid_documents': self.invalid_documents,
            'warnings': self.warnings,
            'completeness_score': self.completeness_score,
            'consistency_score': self.consistency_score,
            'overall_health': self.overall_health
        }


class DocumentSyncDetector:
    """文档同步检测器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self._config = config or {}
        self._document_cache: Dict[str, DocumentInfo] = {}
        self._logger = self._setup_logger()
        
        self._file_patterns = {
            DocumentType.SKILL_DEFINITION: ['**/*.md', '**/README.md'],
            DocumentType.API_DOCUMENTATION: ['**/*api*.md', '**/docs/api/**'],
            DocumentType.USER_GUIDE: ['**/docs/user/**/*.md', '**/guide*.md'],
            DocumentType.CHANGELOG: ['**/CHANGELOG.md', '**/HISTORY.md'],
            DocumentType.ARCHITECTURE_DOC: ['**/docs/architecture/**/*.md', '**/ARCHITECTURE.md'],
            DocumentType.TEST_DOCUMENTATION: ['**/docs/test/**/*.md', '**/TESTING.md'],
            DocumentType.CONFIGURATION: ['**/*.json', '**/*.yaml', '**/*.yml']
        }
        
        self._stale_threshold_days = self._config.get('stale_threshold_days', 7)
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('DocumentSyncDetector')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def detect_sync_status(
        self, 
        project_path: Path,
        source_files: Optional[List[Path]] = None
    ) -> SyncDetectionResult:
        """检测文档同步状态"""
        detection_id = f"SYNC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        all_documents = []
        outdated_documents = []
        missing_references = []
        conflicts = []
        
        if source_files:
            documents_to_check = [f for f in source_files if f.exists()]
        else:
            documents_to_check = self._discover_documents(project_path)
        
        for doc_path in documents_to_check:
            try:
                doc_info = self._analyze_document(doc_path)
                all_documents.append(doc_info)
                
                sync_status = self._check_document_sync_status(doc_info, project_path)
                
                if sync_status == SyncStatus.OUTDATED:
                    outdated_info = self._create_outdated_info(doc_info, project_path)
                    outdated_documents.append(outdated_info)
                elif sync_status == SyncStatus.MISSING:
                    missing_references.append(str(doc_path))
                    
            except Exception as e:
                self._logger.warning(f"无法分析文档 {doc_path}: {e}")
        
        reference_conflicts = self._detect_reference_conflicts(all_documents)
        conflicts.extend(reference_conflicts)
        
        synced_docs = [d for d in all_documents if d not in [item.get('document') for item in outdated_documents]]
        
        summary = self._generate_detection_summary(
            len(all_documents),
            len(synced_docs),
            len(outdated_documents),
            len(missing_references),
            len(conflicts)
        )
        
        result = SyncDetectionResult(
            detection_id=detection_id,
            timestamp=datetime.now().isoformat(),
            documents_analyzed=len(all_documents),
            synced_docs=synced_docs,
            outdated_docs=outdated_documents,
            missing_docs=missing_references,
            conflicts=conflicts,
            summary=summary
        )
        
        self._logger.info(f"同步检测完成: {len(all_documents)} 个文档, {len(outdated_documents)} 个过时")
        
        return result
    
    def _discover_documents(self, project_path: Path) -> List[Path]:
        """发现项目中的所有文档"""
        documents = []
        
        common_doc_patterns = [
            '*.md',
            '**/*.md',
            '**/docs/**/*.md',
            '**/documentation/**/*.md'
        ]
        
        for pattern in common_doc_patterns:
            try:
                found_files = list(project_path.glob(pattern))
                for f in found_files:
                    if f.is_file() and '__pycache__' not in str(f):
                        documents.append(f)
            except Exception:
                pass
        
        seen = set()
        unique_docs = []
        for doc in documents:
            if str(doc) not in seen:
                seen.add(str(doc))
                unique_docs.append(doc)
        
        return unique_docs
    
    def _analyze_document(self, file_path: Path) -> DocumentInfo:
        """分析单个文档"""
        stat = file_path.stat()
        last_modified = datetime.fromtimestamp(stat.st_mtime)
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
        lines = content.split('\n')
        
        doc_type = self._detect_document_type(file_path, content)
        
        metadata = self._extract_metadata(file_path, content)
        
        return DocumentInfo(
            file_path=file_path,
            doc_type=doc_type,
            last_modified=last_modified,
            content_hash=content_hash,
            size_bytes=stat.st_size,
            line_count=len(lines),
            metadata=metadata
        )
    
    def _detect_document_type(self, file_path: Path, content: str) -> DocumentType:
        """检测文档类型"""
        filename = file_path.name.lower()
        
        type_indicators = {
            DocumentType.SKILL_DEFINITION: ['skill', 'readme', 'overview'],
            DocumentType.API_DOCUMENTATION: ['api', 'endpoint', 'interface'],
            DocumentType.USER_GUIDE: ['guide', 'tutorial', 'getting started', 'user'],
            DocumentType.CHANGELOG: ['changelog', 'history', 'changes', 'release'],
            DocumentType.ARCHITECTURE_DOC: ['architecture', 'design', 'structure', 'system'],
            DocumentType.TEST_DOCUMENTATION: ['test', 'testing', 'specification'],
            DocumentType.CONFIGURATION: ['config', 'setting', '.json', '.yaml', '.yml']
        }
        
        content_lower = content[:500].lower()
        
        for doc_type, indicators in type_indicators.items():
            for indicator in indicators:
                if indicator in filename or indicator in content_lower:
                    return doc_type
        
        if file_path.suffix.lower() in ['.md']:
            return DocumentType.SKILL_DEFINITION
        
        return DocumentType.UNKNOWN
    
    def _extract_metadata(self, file_path: Path, content: str) -> Dict[str, Any]:
        """提取文档元数据"""
        metadata = {
            'has_title': bool(re.search(r'^#\s+.+', content, re.MULTILINE)),
            'has_toc': bool(re.search(r'(toc|table of contents)', content.lower())),
            'section_count': len(re.findall(r'^#{1,6}\s', content, re.MULTILINE)),
            'link_count': len(re.findall(r'\[.+?\]\(.+?\)', content)),
            'code_block_count': len(re.findall(r'```[\s\S]*?```', content)),
            'has_version_info': bool(re.search(r'(version|v\d+\.?\d*)', content, re.IGNORECASE)),
            'estimated_read_time_minutes': max(len(content.split()) // 200, 1)
        }
        
        front_matter_match = re.match(r'^---\n([\s\S]*?)\n---', content)
        if front_matter_match:
            try:
                import yaml
                metadata['front_matter'] = yaml.safe_load(front_matter_match.group(1))
            except ImportError:
                pass
        
        return metadata
    
    def _check_document_sync_status(
        self, 
        doc_info: DocumentInfo, 
        project_path: Path
    ) -> SyncStatus:
        """检查文档同步状态"""
        age_days = (datetime.now() - doc_info.last_modified).days
        
        if age_days > self._stale_threshold_days * 2:
            return SyncStatus.OUTDATED
        
        related_code_files = self._find_related_code_files(doc_info.file_path, project_path)
        
        if related_code_files:
            latest_code_change = max(
                (datetime.fromtimestamp(f.stat().st_mtime) for f in related_code_files if f.exists()),
                default=datetime.min
            )
            
            if latest_code_change > doc_info.last_modified + timedelta(days=self._stale_threshold_days):
                return SyncStatus.OUTDATED
        
        cached_doc = self._document_cache.get(str(doc_info.file_path))
        if cached_doc and cached_doc.content_hash != doc_info.content_hash:
            return SyncStatus.CONFLICT
        
        return SyncStatus.SYNCED
    
    def _find_related_code_files(
        self, 
        doc_path: Path, 
        project_path: Path
    ) -> List[Path]:
        """查找相关代码文件"""
        related_files = []
        
        doc_name = doc_path.stem.lower()
        
        code_patterns = [
            project_path / f"{doc_name}.py",
            project_path / f"{doc_name}.ts",
            project_path / f"{doc_name}.js",
        ]
        
        parent_dir = doc_path.parent
        for pattern in ['*.py', '*.ts', '*.js']:
            try:
                related_files.extend(parent_dir.glob(pattern))
            except Exception:
                pass
        
        return [f for f in related_files if f.exists() and f != doc_path]
    
    def _create_outdated_info(
        self, 
        doc_info: DocumentInfo, 
        project_path: Path
    ) -> Dict[str, Any]:
        """创建过期信息"""
        related_changes = self._identify_related_changes(doc_info, project_path)
        
        return {
            'document': doc_info.to_dict(),
            'status': 'outdated',
            'reason': f"文档已 { (datetime.now() - doc_info.last_modified).days } 天未更新",
            'related_changes': related_changes,
            'suggested_updates': self._suggest_updates_for_outdated_doc(doc_info, related_changes)
        }
    
    def _identify_related_changes(
        self, 
        doc_info: DocumentInfo, 
        project_path: Path
    ) -> List[Dict[str, Any]]:
        """识别相关变更"""
        changes = []
        
        related_files = self._find_related_code_files(doc_info.file_path, project_path)
        
        for code_file in related_files:
            try:
                stat = code_file.stat()
                modified_time = datetime.fromtimestamp(stat.st_mtime)
                
                if modified_time > doc_info.last_modified:
                    changes.append({
                        'file': str(code_file.relative_to(project_path)),
                        'modified_at': modified_time.isoformat(),
                        'change_type': 'modified'
                    })
            except Exception:
                continue
        
        changes.sort(key=lambda x: x['modified_at'], reverse=True)
        
        return changes[:10]
    
    def _suggest_updates_for_outdated_doc(
        self, 
        doc_info: DocumentInfo, 
        changes: List[Dict[str, Any]]
    ) -> List[str]:
        """为过期文档建议更新"""
        suggestions = []
        
        if not changes:
            suggestions.append("定期审查和更新文档内容")
            return suggestions
        
        change_types = set(c.get('change_type', 'unknown') for c in changes)
        
        if 'modified' in change_types:
            suggestions.extend([
                "审查相关代码的变更并更新文档",
                "验证文档中的示例代码是否仍然有效",
                "更新API接口描述（如有变化）",
                "添加新功能的说明"
            ])
        
        if doc_info.metadata.get('api_reference'):
            suggestions.append("特别关注API文档的准确性")
        
        return list(set(suggestions))[:5]
    
    def _detect_reference_conflicts(
        self, 
        documents: List[DocumentInfo]
    ) -> List[Dict[str, Any]]:
        """检测引用冲突"""
        conflicts = []
        
        doc_map = {str(d.file_path): d for d in documents}
        
        for doc in documents:
            try:
                with open(doc.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
                
                for link_text, link_url in links:
                    if link_url.startswith('http://') or link_url.startswith('https://'):
                        continue
                    
                    target_path = (doc.file_path.parent / link_url).resolve()
                    
                    if str(target_path) not in doc_map and not target_path.exists():
                        conflicts.append({
                            'source_file': str(doc.file_path),
                            'broken_link': link_url,
                            'link_text': link_text,
                            'type': 'broken_reference'
                        })
                        
            except Exception:
                continue
        
        return conflicts
    
    def _generate_detection_summary(
        self,
        total: int,
        synced: int,
        outdated: int,
        missing: int,
        conflicts: int
    ) -> Dict[str, Any]:
        """生成检测摘要"""
        health_percentage = ((total - outdated - missing) / total * 100) if total > 0 else 100
        
        if health_percentage >= 90:
            health_status = "excellent"
        elif health_percentage >= 70:
            health_status = "good"
        elif health_percentage >= 50:
            health_status = "fair"
        else:
            health_status = "poor"
        
        return {
            'total_documents': total,
            'synced_documents': synced,
            'outdated_documents': outdated,
            'missing_references': missing,
            'reference_conflicts': conflicts,
            'sync_health_percentage': round(health_percentage, 1),
            'health_status': health_status,
            'recommendation': self._get_health_recommendation(health_status, outdated, conflicts)
        }
    
    def _get_health_recommendation(
        self, 
        status: str, 
        outdated_count: int, 
        conflict_count: int
    ) -> str:
        """获取健康状态建议"""
        recommendations = {
            "excellent": "✅ 文档同步状况优秀，继续保持定期维护",
            "good": "👍 文档整体良好，建议处理少量过期文档",
            "fair": "⚠️ 文档需要关注，建议安排时间进行批量更新",
            "poor": "❌ 文档严重不同步，需要立即进行全面审查和更新"
        }
        
        base_rec = recommendations.get(status, "")
        
        if outdated_count > 5:
            base_rec += f"\n⚠️ 有 {outdated_count} 个过期文档需要优先处理"
        
        if conflict_count > 3:
            base_rec += f"\n🔗 发现 {conflict_count} 个断链需要修复"
        
        return base_rec


class OutdatedContentUpdater:
    """过时内容更新器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self._config = config or {}
        self._update_history: List[Dict[str, Any]] = []
        self._backup_manager = DocumentBackupManager(config)
        self._logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('OutdatedContentUpdater')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def generate_update_plan(
        self,
        detection_result: SyncDetectionResult,
        context: Dict[str, Any] = None
    ) -> List[UpdateAction]:
        """生成更新计划"""
        actions = []
        
        for outdated_doc in detection_result.outdated_docs:
            doc_actions = self._create_update_actions(outdated_doc, context)
            actions.extend(doc_actions)
        
        prioritized_actions = self._prioritize_actions(actions)
        
        self._logger.info(f"生成了 {len(prioritized_actions)} 个更新操作")
        
        return prioritized_actions
    
    def _create_update_actions(
        self, 
        outdated_info: Dict[str, Any], 
        context: Dict[str, Any] = None
    ) -> List[UpdateAction]:
        """创建更新操作"""
        doc_info_data = outdated_info.get('document', {})
        doc_path = Path(doc_info_data.get('file_path', ''))
        
        actions = []
        
        if not doc_path.exists():
            return actions
        
        try:
            with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return actions
        
        if self._needs_timestamp_update(content):
            actions.append(UpdateAction(
                action_id=f"TS-{hashlib.md5(str(doc_path).encode()).hexdigest()[:8]}",
                target_file=doc_path,
                action_type="timestamp_update",
                severity=UpdateSeverity.LOW,
                description="更新文档最后修改时间戳",
                changes=[{
                    'type': 'metadata',
                    'field': 'last_updated',
                    'new_value': datetime.now().isoformat()
                }],
                auto_applicable=True,
                risk_level='low',
                estimated_effort_minutes=1
            ))
        
        version_pattern = r'(?:version|v)(?:\s*[:=]\s*|:\s*)(\d+(?:\.\d+)*)'
        version_matches = re.findall(version_pattern, content, re.IGNORECASE)
        
        if version_matches:
            latest_version = version_matches[-1]
            new_version = self._increment_version(latest_version)
            
            actions.append(UpdateAction(
                action_id=f"VER-{hashlib.md5(str(doc_path).encode()).hexdigest()[:8]}",
                target_file=doc_path,
                action_type="version_bump",
                severity=UpdateSeverity.MEDIUM,
                description=f"版本号从 {latest_version} 更新到 {new_version}",
                changes=[{
                    'type': 'content',
                    'pattern': latest_version,
                    'replacement': new_version,
                    'location': 'header'
                }],
                auto_applicable=False,
                risk_level='medium',
                estimated_effort_minutes=2
            ))
        
        broken_links = outdated_info.get('related_changes', [])
        if broken_links:
            actions.append(UpdateAction(
                action_id=f"LINK-{hashlib.md5(str(doc_path).encode()).hexdigest()[:8]}",
                target_file=doc_path,
                action_type="link_verification",
                severity=UpdateSeverity.HIGH if len(broken_links) > 3 else UpdateSeverity.MEDIUM,
                description=f"验证和修复 {len(broken_links)} 个可能过时的链接或引用",
                changes=[{
                    'type': 'reference',
                    'items': broken_links[:5]
                }],
                auto_applicable=False,
                risk_level='medium',
                estimated_effort_minutes=len(broken_links) * 2
            ))
        
        if self._needs_content_refresh(content, outdated_info):
            actions.append(UpdateAction(
                action_id=f"CONTENT-{hashlib.md5(str(doc_path).encode()).hexdigest()[:8]}",
                target_file=doc_path,
                action_type="content_review",
                severity=UpdateSeverity.HIGH,
                description="审查和更新文档主要内容以反映最新变更",
                changes=[{
                    'type': 'comprehensive',
                    'scope': 'full_content',
                    'focus_areas': self._identify_focus_areas(content, outdated_info)
                }],
                auto_applicable=False,
                risk_level='high',
                estimated_effort_minutes=15
            ))
        
        return actions
    
    def _needs_timestamp_update(self, content: str) -> bool:
        """判断是否需要更新时间戳"""
        has_date_indicator = bool(re.search(
            r'(?:last.?updated|modified|date|updated)[:\s]+(\d{4}[-/]\d{2}[-/]\d{2})',
            content,
            re.IGNORECASE
        ))
        
        return has_date_indicator
    
    def _increment_version(self, version: str) -> str:
        """递增版本号"""
        parts = version.split('.')
        
        try:
            parts[-1] = str(int(parts[-1]) + 1)
            return '.'.join(parts)
        except ValueError:
            return f"{version}.1"
    
    def _needs_content_refresh(
        self, 
        content: str, 
        outdated_info: Dict[str, Any]
    ) -> bool:
        """判断是否需要内容刷新"""
        days_since_update = outdated_info.get('document', {}).get('last_modified', '')
        
        if days_since_update:
            try:
                last_update = datetime.fromisoformat(days_since_update)
                days_old = (datetime.now() - last_update).days
                
                if days_old > 30:
                    return True
            except Exception:
                pass
        
        significant_changes = len(outdated_info.get('related_changes', []))
        
        return significant_changes > 5
    
    def _identify_focus_areas(
        self, 
        content: str, 
        outdated_info: Dict[str, Any]
    ) -> List[str]:
        """识别重点关注区域"""
        focus_areas = []
        
        if re.search(r'```(?:python|javascript|typescript)', content):
            focus_areas.append('代码示例')
        
        if re.search(r'(?:api|endpoint|method|function)\b', content, re.IGNORECASE):
            focus_areas.append('API/方法说明')
        
        if re.search(r'(?:installation|setup|quick\s*start)', content, re.IGNORECASE):
            focus_areas.append('安装和配置说明')
        
        if re.search(r'(?:changelog|what\'?s\s*new|changes)', content, re.IGNORECASE):
            focus_areas.append('变更日志')
        
        if not focus_areas:
            focus_areas.append('全文审查')
        
        return focus_areas
    
    def _prioritize_actions(self, actions: List[UpdateAction]) -> List[UpdateAction]:
        """对更新操作排序"""
        severity_order = {
            UpdateSeverity.CRITICAL: 0,
            UpdateSeverity.HIGH: 1,
            UpdateSeverity.MEDIUM: 2,
            UpdateSeverity.LOW: 3,
            UpdateSeverity.INFO: 4
        }
        
        auto_first = sorted(
            actions,
            key=lambda a: (
                severity_order.get(a.severity, 5),
                0 if a.auto_applicable else 1,
                a.estimated_effort_minutes
            )
        )
        
        return auto_first
    
    def execute_updates(
        self,
        actions: List[UpdateAction],
        auto_apply_safe: bool = False,
        dry_run: bool = False
    ) -> UpdateResult:
        """执行更新操作"""
        result_id = f"UPDATE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        successful = []
        failed = []
        skipped = []
        changelog_entries = []
        
        for action in actions:
            try:
                if dry_run:
                    successful.append({
                        'action': action.to_dict(),
                        'status': 'simulated',
                        'message': f"[DRY RUN] 将执行: {action.description}"
                    })
                    changelog_entries.append(self._create_changelog_entry(action, simulated=True))
                    continue
                
                if action.auto_applicable and auto_apply_safe:
                    exec_result = self._apply_safe_action(action)
                    if exec_result['success']:
                        successful.append({
                            'action': action.to_dict(),
                            **exec_result
                        })
                        changelog_entries.append(self._create_changelog_entry(action))
                    else:
                        failed.append({
                            'action': action.to_dict(),
                            **exec_result
                        })
                else:
                    skipped.append({
                        'action': action.to_dict(),
                        'reason': 'requires_manual_intervention' if not action.auto_applicable else 'auto_apply_disabled'
                    })
                    
            except Exception as e:
                failed.append({
                    'action': action.to_dict(),
                    'error': str(e)
                })
        
        summary = {
            'total_actions': len(actions),
            'successful': len(successful),
            'failed': len(failed),
            'skipped': len(skipped),
            'success_rate': (len(successful) / len(actions) * 100) if actions else 0
        }
        
        result = UpdateResult(
            result_id=result_id,
            update_actions=actions,
            successful_updates=successful,
            failed_updates=failed,
            skipped_updates=skipped,
            summary=summary,
            changelog_entries=changelog_entries
        )
        
        self._update_history.append(result.to_dict())
        self._logger.info(f"更新执行完成: {len(successful)} 成功, {len(failed)} 失败, {len(skipped)} 跳过")
        
        return result
    
    def _apply_safe_action(self, action: UpdateAction) -> Dict[str, Any]:
        """应用安全操作"""
        target_file = action.target_file
        
        if not target_file.exists():
            return {'success': False, 'error': '目标文件不存在'}
        
        backup_path = self._backup_manager.create_backup(target_file)
        
        try:
            with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()
            
            modified_content = original_content
            
            for change in action.changes:
                if change.get('type') == 'metadata':
                    field = change.get('field')
                    new_value = change.get('new_value')
                    
                    patterns = [
                        rf'(last[_ ]?updated|modified|date)[^:\n]*:[^\n]*',
                        rf'\*\*{field}\*\*[^\n]*',
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, modified_content, re.IGNORECASE)
                        if match:
                            replacement = f"{match.group(0).split(':')[0]}: {new_value}"
                            modified_content = modified_content[:match.start()] + replacement + modified_content[match.end():]
                            break
            
            if modified_content != original_content:
                with open(target_file, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                
                return {
                    'success': True,
                    'backup_created': bool(backup_path),
                    'backup_path': backup_path or '',
                    'changes_applied': len(action.changes)
                }
            else:
                return {
                    'success': True,
                    'backup_created': False,
                    'message': '无需更改（内容已是最新）'
                }
                
        except Exception as e:
            if backup_path:
                self._backup_manager.restore(backup_path, target_file)
            
            return {'success': False, 'error': str(e)}
    
    def _create_changelog_entry(
        self, 
        action: UpdateAction, 
        simulated: bool = False
    ) -> Dict[str, Any]:
        """创建变更日志条目"""
        return {
            'timestamp': datetime.now().isoformat(),
            'action_id': action.action_id,
            'action_type': action.action_type,
            'target_file': str(action.target_file),
            'description': action.description,
            'severity': action.severity.value,
            'auto_applied': action.auto_applicable and not simulated,
            'simulated': simulated
        }


class DocumentBackupManager:
    """文档备份管理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self._config = config or {}
        self._backup_dir = Path(self._config.get('backup_dir', './.doc_backups'))
        self._logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('DocumentBackupManager')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def create_backup(self, file_path: Path) -> str:
        """创建备份"""
        if not file_path.exists():
            return ""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = self._backup_dir / backup_filename
        
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            shutil.copy2(file_path, backup_path)
            self._logger.debug(f"备份已创建: {backup_path}")
            return str(backup_path)
        except Exception as e:
            self._logger.error(f"备份失败: {e}")
            return ""
    
    def restore(self, backup_path: str, target_path: Path) -> bool:
        """从备份恢复"""
        backup = Path(backup_path)
        
        if not backup.exists():
            self._logger.error(f"备份不存在: {backup_path}")
            return False
        
        try:
            shutil.copy2(backup, target_path)
            self._logger.info(f"已从备份恢复: {target_path}")
            return True
        except Exception as e:
            self._logger.error(f"恢复失败: {e}")
            return False


class DocumentValidator:
    """文档完整性验证器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self._config = config or {}
        self._validation_rules = self._load_validation_rules()
        self._logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('DocumentValidator')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """加载验证规则"""
        return {
            'required_sections': {
                DocumentType.SKILL_DEFINITION: ['title', 'description', 'usage'],
                DocumentType.API_DOCUMENTATION: ['title', 'endpoints', 'authentication'],
                DocumentType.USER_GUIDE: ['introduction', 'prerequisites', 'steps'],
                DocumentType.CHANGELOG: ['title', 'entries'],
                DocumentType.ARCHITECTURE_DOC: ['overview', 'components'],
            },
            'quality_checks': {
                'max_line_length': 120,
                'require_title': True,
                'require_table_of_contents': False,
                'min_sections': 2,
                'spell_check_enabled': False
            },
            'consistency_rules': {
                'heading_style_consistent': True,
                'list_formatting_consistent': True,
                'code_block_language_specified': True
            }
        }
    
    def validate_documents(
        self,
        documents: List[DocumentInfo],
        project_context: Dict[str, Any] = None
    ) -> ValidationReport:
        """验证文档完整性"""
        report_id = f"VAL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        valid_docs = []
        invalid_docs = []
        warnings_list = []
        
        for doc in documents:
            validation_result = self._validate_single_document(doc, project_context)
            
            if validation_result['valid']:
                valid_docs.append(doc)
            else:
                invalid_docs.append({
                    'document': doc.to_dict(),
                    'issues': validation_result['issues']
                })
            
            warnings_list.extend(validation_result['warnings'])
        
        completeness_score = self._calculate_completeness_score(valid_docs, invalid_docs, documents)
        consistency_score = self._calculate_consistency_score(warnings_list, documents)
        
        overall_health = self._determine_overall_health(completeness_score, consistency_score)
        
        report = ValidationReport(
            report_id=report_id,
            validated_at=datetime.now().isoformat(),
            total_documents=len(documents),
            valid_documents=len(valid_docs),
            invalid_documents=invalid_docs,
            warnings=warnings_list,
            completeness_score=completeness_score,
            consistency_score=consistency_score,
            overall_health=overall_health
        )
        
        self._logger.info(f"验证完成: {len(valid_docs)}/{len(documents)} 个文档有效")
        
        return report
    
    def _validate_single_document(
        self,
        doc: DocumentInfo,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """验证单个文档"""
        issues = []
        warnings = []
        
        try:
            with open(doc.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return {
                'valid': False,
                'issues': [{'severity': 'critical', 'message': '无法读取文件'}],
                'warnings': []
            }
        
        required_sections = self._validation_rules.get('required_sections', {}).get(doc.doc_type, [])
        
        if required_sections:
            present_sections = self._extract_section_headers(content)
            missing_sections = [s for s in required_sections if s.lower() not in [h.lower() for h in present_sections]]
            
            if missing_sections:
                issues.append({
                    'severity': 'medium',
                    'type': 'missing_section',
                    'message': f"缺少必需章节: {', '.join(missing_sections)}"
                })
        
        quality_issues = self._check_quality_rules(content, doc)
        issues.extend(quality_issues['issues'])
        warnings.extend(quality_issues['warnings'])
        
        consistency_warnings = self._check_consistency(content, doc)
        warnings.extend(consistency_warnings)
        
        valid = len([i for i in issues if i.get('severity') == 'critical']) == 0
        
        return {
            'valid': valid,
            'issues': issues,
            'warnings': warnings
        }
    
    def _extract_section_headers(self, content: str) -> List[str]:
        """提取章节标题"""
        headers = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
        return headers
    
    def _check_quality_rules(
        self, 
        content: str, 
        doc: DocumentInfo
    ) -> Dict[str, Any]:
        """检查质量规则"""
        issues = []
        warnings = []
        
        quality_config = self._validation_rules.get('quality_checks', {})
        
        lines = content.split('\n')
        long_lines = [(i + 1, line) for i, line in enumerate(lines) if len(line) > quality_config.get('max_line_length', 120)]
        
        if long_lines and len(long_lines) > len(lines) * 0.05:
            warnings.append({
                'severity': 'low',
                'type': 'long_lines',
                'message': f"发现 {len(long_lines)} 行超过最大长度限制",
                'count': len(long_lines)
            })
        
        if quality_config.get('require_title', True):
            has_title = bool(re.search(r'^#\s+.+$', content, re.MULTILINE))
            if not has_title:
                issues.append({
                    'severity': 'high',
                    'type': 'missing_title',
                    'message': '文档缺少标题'
                })
        
        sections = self._extract_section_headers(content)
        min_sections = quality_config.get('min_sections', 2)
        
        if len(sections) < min_sections:
            issues.append({
                'severity': 'medium',
                'type': 'insufficient_structure',
                'message': f"文档结构过于简单，只有 {len(sections)} 个章节（至少需要 {min_sections} 个）"
            })
        
        return {'issues': issues, 'warnings': warnings}
    
    def _check_consistency(self, content: str, doc: DocumentInfo) -> List[Dict[str, Any]]:
        """检查一致性"""
        warnings = []
        
        consistency_rules = self._validation_rules.get('consistency_rules', {})
        
        if consistency_rules.get('heading_style_consistent', True):
            heading_styles = set()
            for match in re.finditer(r'^(#{1,6})\s', content, re.MULTILINE):
                heading_styles.add(match.group(1))
            
            if len(heading_styles) > 1:
                sample_styles = ', '.join(sorted(heading_styles)[:3])
                warnings.append({
                    'severity': 'info',
                    'type': 'inconsistent_heading_style',
                    'message': f"标题样式不一致，使用了多种标记级别: {sample_styles}"
                })
        
        code_blocks = re.findall(r'```(\w*)', content)
        unspecified_blocks = [cb for cb in code_blocks if not cb]
        
        if consistency_rules.get('code_block_language_specified', True) and unspecified_blocks:
            warnings.append({
                'severity': 'low',
                'type': 'unspecified_code_language',
                'message': f"{len(unspecified_blocks)} 个代码块未指定语言类型"
            })
        
        return warnings
    
    def _calculate_completeness_score(
        self,
        valid: List[DocumentInfo],
        invalid: List[Dict[str, Any]],
        total: List[DocumentInfo]
    ) -> float:
        """计算完整度分数"""
        if not total:
            return 1.0
        
        critical_invalid = sum(1 for i in invalid if any(issue.get('severity') == 'critical' for issue in i.get('issues', [])))
        
        base_score = (len(total) - critical_invalid) / len(total)
        
        section_coverage = 0
        for doc in total:
            try:
                with open(doc.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                sections = len(self._extract_section_headers(content))
                section_coverage += min(sections / 5, 1.0)
            except Exception:
                pass
        
        avg_section_coverage = section_coverage / len(total) if total else 0
        
        final_score = (base_score * 0.7) + (avg_section_coverage * 0.3)
        
        return round(min(max(final_score, 0), 1), 2)
    
    def _calculate_consistency_score(
        self,
        warnings: List[Dict[str, Any]],
        documents: List[DocumentInfo]
    ) -> float:
        """计算一致性分数"""
        if not documents:
            return 1.0
        
        consistency_warnings = [w for w in warnings if w.get('type') in [
            'inconsistent_heading_style',
            'unspecified_code_language'
        ]]
        
        warning_ratio = len(consistency_warnings) / len(documents)
        
        score = 1.0 - min(warning_ratio * 2, 1.0)
        
        return round(score, 2)
    
    def _determine_overall_health(
        self, 
        completeness: float, 
        consistency: float
    ) -> str:
        """确定整体健康状态"""
        combined = (completeness * 0.6) + (consistency * 0.4)
        
        if combined >= 0.9:
            return "excellent"
        elif combined >= 0.75:
            return "good"
        elif combined >= 0.6:
            return "fair"
        else:
            return "needs_improvement"


class EnhancedSkillDocUpdater:
    """增强的技能文档更新器主类"""
    
    def __init__(self, project_path: str, config: Dict[str, Any] = None):
        self.project_path = Path(project_path)
        self._config = config or {}
        
        self.sync_detector = DocumentSyncDetector(config)
        self.updater = OutdatedContentUpdater(config)
        self.validator = DocumentValidator(config)
        
        self._update_history: List[UpdateResult] = []
        self._validation_history: List[ValidationReport] = []
        self._logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('EnhancedSkillDocUpdater')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def run_full_update_cycle(
        self,
        auto_apply_safe: bool = False,
        dry_run: bool = False,
        specific_files: Optional[List[Path]] = None
    ) -> Dict[str, Any]:
        """运行完整的文档更新周期"""
        cycle_start = datetime.now()
        
        self._logger.info("=" * 70)
        self._logger.info("开始文档更新周期")
        self._logger.info("=" * 70)
        
        self._logger.info("步骤 1/3: 检测文档同步状态...")
        sync_result = self.sync_detector.detect_sync_status(
            self.project_path,
            source_files=specific_files
        )
        
        self._logger.info(f"检测完成: {sync_result.summary['health_status']}")
        
        self._logger.info("步骤 2/3: 生成并执行更新计划...")
        update_actions = self.updater.generate_update_plan(sync_result)
        
        update_result = self.updater.execute_updates(
            update_actions,
            auto_apply_safe=auto_apply_safe,
            dry_run=dry_run
        )
        
        self._logger.info(f"更新完成: {update_result.summary['successful']}/{update_result.summary['total_actions']} 成功")
        
        self._logger.info("步骤 3/3: 验证文档完整性...")
        all_docs = self._collect_all_documents()
        
        validation_report = self.validator.validate_documents(all_docs)
        
        cycle_end = datetime.now()
        
        cycle_report = {
            'cycle_id': f"DOC-CYCLE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'started_at': cycle_start.isoformat(),
            'completed_at': cycle_end.isoformat(),
            'duration_seconds': (cycle_end - cycle_start).total_seconds(),
            'sync_detection': sync_result.to_dict(),
            'update_result': update_result.to_dict(),
            'validation_report': validation_report.to_dict(),
            'overall_assessment': self._assess_overall_result(sync_result, update_result, validation_report)
        }
        
        self._update_history.append(update_result)
        self._validation_history.append(validation_report)
        
        self._logger.info("=" * 70)
        self._logger.info("文档更新周期完成")
        self._logger.info(f"- 同步状态: {sync_result.summary['health_status']}")
        self._logger.info(f"- 更新成功: {update_result.summary['success_rate']:.1f}%")
        self._logger.info(f"- 验证结果: {validation_report.overall_health}")
        self._logger.info("=" * 70)
        
        return cycle_report
    
    def _collect_all_documents(self) -> List[DocumentInfo]:
        """收集所有文档"""
        documents = []
        
        discovered = self.sync_detector._discover_documents(self.project_path)
        
        for doc_path in discovered:
            try:
                doc_info = self.sync_detector._analyze_document(doc_path)
                documents.append(doc_info)
            except Exception:
                continue
        
        return documents
    
    def _assess_overall_result(
        self,
        sync_result: SyncDetectionResult,
        update_result: UpdateResult,
        validation: ValidationReport
    ) -> Dict[str, Any]:
        """评估整体结果"""
        sync_health = sync_result.summary.get('sync_health_percentage', 100)
        update_success = update_result.summary.get('success_rate', 100)
        validation_completeness = validation.completeness_score
        validation_consistency = validation.consistency_score
        
        overall_score = (
            sync_health * 0.3 +
            update_success * 0.3 +
            validation_completeness * 0.2 +
            validation_consistency * 0.2
        )
        
        if overall_score >= 85:
            assessment = "优秀 - 文档系统运行良好"
        elif overall_score >= 70:
            assessment = "良好 - 整体表现不错，有少量改进空间"
        elif overall_score >= 55:
            assessment = "一般 - 需要关注一些问题"
        else:
            assessment = "需改进 - 存在较多问题需要处理"
        
        return {
            'overall_score': round(overall_score, 1),
            'assessment': assessment,
            'component_scores': {
                'sync_health': sync_health,
                'update_success': update_success,
                'completeness': validation_completeness,
                'consistency': validation_consistency
            },
            'recommendations': self._generate_final_recommendations(sync_result, update_result, validation)
        }
    
    def _generate_final_recommendations(
        self,
        sync: SyncDetectionResult,
        update: UpdateResult,
        validation: ValidationReport
    ) -> List[str]:
        """生成最终建议"""
        recommendations = []
        
        if sync.summary.get('outdated_documents', 0) > 5:
            recommendations.append(f"📝 有 {sync.summary['outdated_documents']} 个过期文档，建议安排批量更新")
        
        if update.summary.get('skipped', 0) > 3:
            recommendations.append(f"⏭️ {update.summary['skipped']} 个更新被跳过，考虑手动处理")
        
        if validation.overall_health in ['needs_improvement', 'fair']:
            recommendations.append("🔍 文档质量需要提升，建议进行结构性审查")
        
        if len(validation.warnings) > 10:
            recommendations.append(f"⚠️ 发现 {len(validation.warnings)} 个警告，建议逐步解决")
        
        if not recommendations:
            recommendations.append("✅ 文档系统运行良好，保持当前维护频率即可")
        
        return recommendations[:5]
    
    def get_update_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取更新历史"""
        return [r.to_dict() for r in self._update_history[-limit:]]
    
    def get_latest_validation(self) -> Optional[ValidationReport]:
        """获取最新验证报告"""
        return self._validation_history[-1] if self._validation_history else None
    
    def export_report(self, output_path: Path, report_data: Dict[str, Any]):
        """导出报告"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
        
        self._logger.info(f"报告已导出: {output_path}")


if __name__ == '__main__':
    print("增强的技能文档更新器模块已加载 (Phase 9.1)")
    print("\n主要组件:")
    print("- DocumentSyncDetector: 文档同步检测器")
    print("- OutdatedContentUpdater: 过时内容更新器")
    print("- DocumentBackupManager: 文档备份管理器")
    print("- DocumentValidator: 文档完整性验证器")
    print("- EnhancedSkillDocUpdater: 增强文档更新器主类")
