#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问题追踪器模块

实现问题生命周期管理、状态追踪、历史记录和数据库集成。
支持问题状态流转：open → in_progress → resolved → closed，以及 reopened 流程。

使用示例:
    from issue_tracker import IssueTracker
    
    tracker = IssueTracker()
    issue = tracker.create_issue(
        title="登录功能异常",
        description="用户无法正常登录系统",
        priority=IssuePriority.HIGH,
        category=IssueCategory.BUG
    )
    tracker.start_issue(issue.issue_id)
    tracker.resolve_issue(issue.issue_id, "修复了登录验证逻辑")
"""

import json
import logging
import sys
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict

try:
    from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, Index, Float
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func
    from backend.app.models.base import Base
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    Base = object

from skillscripts.utils.path_config_manager import PathConfigManager


class IssueStatus(str, Enum):
    """问题状态"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"


class IssuePriority(str, Enum):
    """问题优先级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    TRIVIAL = "trivial"


class IssueCategory(str, Enum):
    """问题类别"""
    BUG = "bug"
    FEATURE = "feature"
    IMPROVEMENT = "improvement"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    PERFORMANCE = "performance"
    TEST = "test"
    REFACTORING = "refactoring"


class IssueResolution(str, Enum):
    """问题解决方式"""
    FIXED = "fixed"
    WONT_FIX = "wont_fix"
    DUPLICATE = "duplicate"
    INVALID = "invalid"
    CANNOT_REPRODUCE = "cannot_reproduce"
    WORKS_AS_INTENDED = "works_as_intended"


ISSUE_STATUS_TRANSITIONS = {
    IssueStatus.OPEN: [IssueStatus.IN_PROGRESS, IssueStatus.CLOSED],
    IssueStatus.IN_PROGRESS: [IssueStatus.RESOLVED, IssueStatus.OPEN],
    IssueStatus.RESOLVED: [IssueStatus.CLOSED, IssueStatus.REOPENED],
    IssueStatus.CLOSED: [IssueStatus.REOPENED],
    IssueStatus.REOPENED: [IssueStatus.IN_PROGRESS, IssueStatus.CLOSED],
}


@dataclass
class IssueComment:
    """问题评论"""
    comment_id: str
    issue_id: str
    author: str
    content: str
    created_at: str
    updated_at: Optional[str] = None
    is_internal: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "comment_id": self.comment_id,
            "issue_id": self.issue_id,
            "author": self.author,
            "content": self.content,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_internal": self.is_internal
        }


@dataclass
class IssueHistory:
    """问题历史记录"""
    history_id: str
    issue_id: str
    field_name: str
    old_value: str
    new_value: str
    changed_by: str
    changed_at: str
    reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "history_id": self.history_id,
            "issue_id": self.issue_id,
            "field_name": self.field_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "changed_by": self.changed_by,
            "changed_at": self.changed_at,
            "reason": self.reason
        }


@dataclass
class Issue:
    """问题实体"""
    issue_id: str
    title: str
    description: str
    category: IssueCategory
    priority: IssuePriority
    status: IssueStatus
    created_at: str
    updated_at: str
    assignee: str = ""
    reporter: str = ""
    project_id: str = ""
    department_id: str = ""
    labels: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    related_issues: List[str] = field(default_factory=list)
    blocked_by: List[str] = field(default_factory=list)
    blocks: List[str] = field(default_factory=list)
    resolution: Optional[IssueResolution] = None
    resolution_notes: str = ""
    resolved_at: Optional[str] = None
    resolved_by: str = ""
    closed_at: Optional[str] = None
    closed_by: str = ""
    due_date: Optional[str] = None
    estimated_hours: float = 0.0
    actual_hours: float = 0.0
    environment: str = ""
    steps_to_reproduce: str = ""
    expected_behavior: str = ""
    actual_behavior: str = ""
    attachments: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "assignee": self.assignee,
            "reporter": self.reporter,
            "project_id": self.project_id,
            "department_id": self.department_id,
            "labels": self.labels,
            "tags": self.tags,
            "related_issues": self.related_issues,
            "blocked_by": self.blocked_by,
            "blocks": self.blocks,
            "resolution": self.resolution.value if self.resolution else None,
            "resolution_notes": self.resolution_notes,
            "resolved_at": self.resolved_at,
            "resolved_by": self.resolved_by,
            "closed_at": self.closed_at,
            "closed_by": self.closed_by,
            "due_date": self.due_date,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "environment": self.environment,
            "steps_to_reproduce": self.steps_to_reproduce,
            "expected_behavior": self.expected_behavior,
            "actual_behavior": self.actual_behavior,
            "attachments": self.attachments,
            "references": self.references,
            "metrics": self.metrics
        }


if DATABASE_AVAILABLE:
    class IssueModel(Base):
        """问题数据库模型"""
        __tablename__ = "issues"
        
        id = Column(Integer, primary_key=True, index=True)
        issue_id = Column(String(50), unique=True, nullable=False, index=True)
        title = Column(String(500), nullable=False)
        description = Column(Text)
        category = Column(String(50), nullable=False, index=True)
        priority = Column(String(20), nullable=False, index=True)
        status = Column(String(50), nullable=False, index=True)
        assignee = Column(String(100), index=True)
        reporter = Column(String(100), index=True)
        project_id = Column(String(50), index=True)
        department_id = Column(String(50), index=True)
        labels = Column(JSON, default=list)
        tags = Column(JSON, default=list)
        related_issues = Column(JSON, default=list)
        blocked_by = Column(JSON, default=list)
        blocks = Column(JSON, default=list)
        resolution = Column(String(50), nullable=True)
        resolution_notes = Column(Text)
        resolved_at = Column(DateTime(timezone=True), nullable=True)
        resolved_by = Column(String(100))
        closed_at = Column(DateTime(timezone=True), nullable=True)
        closed_by = Column(String(100))
        due_date = Column(DateTime(timezone=True), nullable=True)
        estimated_hours = Column(Float, default=0.0)
        actual_hours = Column(Float, default=0.0)
        environment = Column(Text)
        steps_to_reproduce = Column(Text)
        expected_behavior = Column(Text)
        actual_behavior = Column(Text)
        attachments = Column(JSON, default=list)
        references = Column(JSON, default=list)
        metrics = Column(JSON, default=dict)
        created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
        updated_at = Column(DateTime(timezone=True), onupdate=func.now())
        
        __table_args__ = (
            Index('ix_issues_status_priority', 'status', 'priority'),
            Index('ix_issues_project_status', 'project_id', 'status'),
            Index('ix_issues_assignee_status', 'assignee', 'status'),
            Index('ix_issues_category_priority', 'category', 'priority'),
        )


class IssueStorage(ABC):
    """问题存储接口"""
    
    @abstractmethod
    def save(self, issue: Issue) -> bool:
        pass
    
    @abstractmethod
    def load(self, issue_id: str) -> Optional[Issue]:
        pass
    
    @abstractmethod
    def load_all(self) -> List[Issue]:
        pass
    
    @abstractmethod
    def delete(self, issue_id: str) -> bool:
        pass
    
    @abstractmethod
    def search(self, filters: Dict[str, Any]) -> List[Issue]:
        pass


class JSONIssueStorage(IssueStorage):
    """JSON文件存储实现"""
    
    def __init__(self, storage_path: Optional[Path] = None, logger: Optional[logging.Logger] = None):
        if storage_path is None:
            try:
                from skillscripts.utils.enhanced_path_config_manager import create_path_manager, PathKey
                manager = create_path_manager()
                self.storage_path = manager.resolve_path(PathKey.DATA_DIR) / "issues" / "issues.json"
            except Exception:
                self.storage_path = get_path_config().DATA_DIR / "issues" / "issues.json"
        else:
            self.storage_path = storage_path
        self.logger = logger or logging.getLogger(__name__)
        self._issues: Dict[str, Issue] = {}
        self._load_from_file()
    
    def _load_from_file(self) -> None:
        """从文件加载问题"""
        if not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for item in data.get("issues", []):
                issue = self._dict_to_issue(item)
                if issue:
                    self._issues[issue.issue_id] = issue
            
            self.logger.info(f"加载了 {len(self._issues)} 个问题")
        except Exception as e:
            self.logger.error(f"加载问题失败: {e}")
    
    def _dict_to_issue(self, item: Dict[str, Any]) -> Optional[Issue]:
        """字典转问题对象"""
        try:
            return Issue(
                issue_id=item["issue_id"],
                title=item["title"],
                description=item.get("description", ""),
                category=IssueCategory(item.get("category", "bug")),
                priority=IssuePriority(item.get("priority", "medium")),
                status=IssueStatus(item.get("status", "open")),
                created_at=item.get("created_at", datetime.now().isoformat()),
                updated_at=item.get("updated_at", datetime.now().isoformat()),
                assignee=item.get("assignee", ""),
                reporter=item.get("reporter", ""),
                project_id=item.get("project_id", ""),
                department_id=item.get("department_id", ""),
                labels=item.get("labels", []),
                tags=item.get("tags", []),
                related_issues=item.get("related_issues", []),
                blocked_by=item.get("blocked_by", []),
                blocks=item.get("blocks", []),
                resolution=IssueResolution(item["resolution"]) if item.get("resolution") else None,
                resolution_notes=item.get("resolution_notes", ""),
                resolved_at=item.get("resolved_at"),
                resolved_by=item.get("resolved_by", ""),
                closed_at=item.get("closed_at"),
                closed_by=item.get("closed_by", ""),
                due_date=item.get("due_date"),
                estimated_hours=item.get("estimated_hours", 0.0),
                actual_hours=item.get("actual_hours", 0.0),
                environment=item.get("environment", ""),
                steps_to_reproduce=item.get("steps_to_reproduce", ""),
                expected_behavior=item.get("expected_behavior", ""),
                actual_behavior=item.get("actual_behavior", ""),
                attachments=item.get("attachments", []),
                references=item.get("references", []),
                metrics=item.get("metrics", {})
            )
        except Exception as e:
            self.logger.error(f"转换问题失败: {e}")
            return None
    
    def _save_to_file(self) -> bool:
        """保存问题到文件"""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "issues": [issue.to_dict() for issue in self._issues.values()],
                "last_updated": datetime.now().isoformat(),
                "total_count": len(self._issues)
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            self.logger.error(f"保存问题失败: {e}")
            return False
    
    def save(self, issue: Issue) -> bool:
        """保存问题"""
        self._issues[issue.issue_id] = issue
        return self._save_to_file()
    
    def load(self, issue_id: str) -> Optional[Issue]:
        """加载单个问题"""
        return self._issues.get(issue_id)
    
    def load_all(self) -> List[Issue]:
        """加载所有问题"""
        return list(self._issues.values())
    
    def delete(self, issue_id: str) -> bool:
        """删除问题"""
        if issue_id in self._issues:
            del self._issues[issue_id]
            return self._save_to_file()
        return False
    
    def search(self, filters: Dict[str, Any]) -> List[Issue]:
        """搜索问题"""
        results = list(self._issues.values())
        
        if "status" in filters:
            status_filter = filters["status"]
            if isinstance(status_filter, list):
                results = [i for i in results if i.status in status_filter]
            else:
                results = [i for i in results if i.status == status_filter]
        
        if "priority" in filters:
            priority_filter = filters["priority"]
            if isinstance(priority_filter, list):
                results = [i for i in results if i.priority in priority_filter]
            else:
                results = [i for i in results if i.priority == priority_filter]
        
        if "category" in filters:
            category_filter = filters["category"]
            if isinstance(category_filter, list):
                results = [i for i in results if i.category in category_filter]
            else:
                results = [i for i in results if i.category == category_filter]
        
        if "assignee" in filters:
            results = [i for i in results if i.assignee == filters["assignee"]]
        
        if "reporter" in filters:
            results = [i for i in results if i.reporter == filters["reporter"]]
        
        if "project_id" in filters:
            results = [i for i in results if i.project_id == filters["project_id"]]
        
        if "labels" in filters:
            label_filter = filters["labels"]
            if isinstance(label_filter, list):
                results = [i for i in results if any(label in i.labels for label in label_filter)]
            else:
                results = [i for i in results if label_filter in i.labels]
        
        if "keyword" in filters:
            keyword = filters["keyword"].lower()
            results = [
                i for i in results
                if keyword in i.title.lower() or keyword in i.description.lower()
            ]
        
        return results


class IssueHistoryManager:
    """问题历史管理器"""
    
    def __init__(self, storage_path: Optional[Path] = None, logger: Optional[logging.Logger] = None):
        if storage_path is None:
            try:
                from skillscripts.utils.enhanced_path_config_manager import create_path_manager, PathKey
                manager = create_path_manager()
                self.storage_path = manager.resolve_path(PathKey.DATA_DIR) / "issues" / "history.json"
            except Exception:
                self.storage_path = get_path_config().DATA_DIR / "issues" / "history.json"
        else:
            self.storage_path = storage_path
        self.logger = logger or logging.getLogger(__name__)
        self._history: Dict[str, List[IssueHistory]] = {}
        self._load_history()
    
    def _load_history(self) -> None:
        """加载历史记录"""
        if not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for issue_id, histories in data.get("history", {}).items():
                self._history[issue_id] = [
                    IssueHistory(
                        history_id=h["history_id"],
                        issue_id=h["issue_id"],
                        field_name=h["field_name"],
                        old_value=h["old_value"],
                        new_value=h["new_value"],
                        changed_by=h["changed_by"],
                        changed_at=h["changed_at"],
                        reason=h.get("reason", "")
                    )
                    for h in histories
                ]
        except Exception as e:
            self.logger.error(f"加载历史记录失败: {e}")
    
    def _save_history(self) -> bool:
        """保存历史记录"""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "history": {
                    issue_id: [h.to_dict() for h in histories]
                    for issue_id, histories in self._history.items()
                },
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            self.logger.error(f"保存历史记录失败: {e}")
            return False
    
    def record_change(
        self,
        issue_id: str,
        field_name: str,
        old_value: str,
        new_value: str,
        changed_by: str,
        reason: str = ""
    ) -> IssueHistory:
        """记录变更"""
        history_id = hashlib.md5(
            f"{issue_id}:{field_name}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        history = IssueHistory(
            history_id=history_id,
            issue_id=issue_id,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by,
            changed_at=datetime.now().isoformat(),
            reason=reason
        )
        
        if issue_id not in self._history:
            self._history[issue_id] = []
        
        self._history[issue_id].append(history)
        self._save_history()
        
        return history
    
    def get_history(self, issue_id: str) -> List[IssueHistory]:
        """获取问题历史"""
        return self._history.get(issue_id, [])
    
    def get_recent_changes(self, limit: int = 100) -> List[IssueHistory]:
        """获取最近的变更"""
        all_changes = []
        for histories in self._history.values():
            all_changes.extend(histories)
        
        all_changes.sort(key=lambda h: h.changed_at, reverse=True)
        return all_changes[:limit]


class IssueCommentManager:
    """问题评论管理器"""
    
    def __init__(self, storage_path: Optional[Path] = None, logger: Optional[logging.Logger] = None):
        if storage_path is None:
            try:
                from skillscripts.utils.enhanced_path_config_manager import create_path_manager, PathKey
                manager = create_path_manager()
                self.storage_path = manager.resolve_path(PathKey.DATA_DIR) / "issues" / "comments.json"
            except Exception:
                self.storage_path = get_path_config().DATA_DIR / "issues" / "comments.json"
        else:
            self.storage_path = storage_path
        self.logger = logger or logging.getLogger(__name__)
        self._comments: Dict[str, List[IssueComment]] = {}
        self._load_comments()
    
    def _load_comments(self) -> None:
        """加载评论"""
        if not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for issue_id, comments in data.get("comments", {}).items():
                self._comments[issue_id] = [
                    IssueComment(
                        comment_id=c["comment_id"],
                        issue_id=c["issue_id"],
                        author=c["author"],
                        content=c["content"],
                        created_at=c["created_at"],
                        updated_at=c.get("updated_at"),
                        is_internal=c.get("is_internal", False)
                    )
                    for c in comments
                ]
        except Exception as e:
            self.logger.error(f"加载评论失败: {e}")
    
    def _save_comments(self) -> bool:
        """保存评论"""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "comments": {
                    issue_id: [c.to_dict() for c in comments]
                    for issue_id, comments in self._comments.items()
                },
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            self.logger.error(f"保存评论失败: {e}")
            return False
    
    def add_comment(
        self,
        issue_id: str,
        author: str,
        content: str,
        is_internal: bool = False
    ) -> IssueComment:
        """添加评论"""
        comment_id = hashlib.md5(
            f"{issue_id}:{author}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        comment = IssueComment(
            comment_id=comment_id,
            issue_id=issue_id,
            author=author,
            content=content,
            created_at=datetime.now().isoformat(),
            is_internal=is_internal
        )
        
        if issue_id not in self._comments:
            self._comments[issue_id] = []
        
        self._comments[issue_id].append(comment)
        self._save_comments()
        
        return comment
    
    def get_comments(self, issue_id: str, include_internal: bool = True) -> List[IssueComment]:
        """获取问题评论"""
        comments = self._comments.get(issue_id, [])
        if not include_internal:
            comments = [c for c in comments if not c.is_internal]
        return comments
    
    def update_comment(self, comment_id: str, new_content: str) -> Optional[IssueComment]:
        """更新评论"""
        for issue_id, comments in self._comments.items():
            for comment in comments:
                if comment.comment_id == comment_id:
                    comment.content = new_content
                    comment.updated_at = datetime.now().isoformat()
                    self._save_comments()
                    return comment
        return None
    
    def delete_comment(self, comment_id: str) -> bool:
        """删除评论"""
        for issue_id, comments in self._comments.items():
            for i, comment in enumerate(comments):
                if comment.comment_id == comment_id:
                    comments.pop(i)
                    self._save_comments()
                    return True
        return False


class IssueTracker:
    """问题追踪器主类"""
    
    def __init__(
        self,
        storage_path: Optional[Path] = None,
        use_database: bool = False,
        logger: Optional[logging.Logger] = None
    ):
        self.path_manager = PathConfigManager(auto_detect=True)
        self.logger = logger or logging.getLogger(__name__)
        
        if storage_path:
            self.storage_path = storage_path
        else:
            self.storage_path = self.path_manager.get_data_path() / "issues" / "issues.json"
        
        self.storage = JSONIssueStorage(self.storage_path, logger)
        self.history_manager = IssueHistoryManager(
            self.storage_path.parent / "history.json",
            logger
        )
        self.comment_manager = IssueCommentManager(
            self.storage_path.parent / "comments.json",
            logger
        )
        
        self._issues: List[Issue] = []
    
    def create_issue(
        self,
        title: str,
        description: str = "",
        category: IssueCategory = IssueCategory.BUG,
        priority: IssuePriority = IssuePriority.MEDIUM,
        assignee: str = "",
        reporter: str = "",
        project_id: str = "",
        department_id: str = "",
        labels: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        due_date: Optional[str] = None,
        estimated_hours: float = 0.0,
        environment: str = "",
        steps_to_reproduce: str = "",
        expected_behavior: str = "",
        actual_behavior: str = ""
    ) -> Issue:
        """创建问题"""
        timestamp = datetime.now().isoformat()
        issue_id = self._generate_issue_id(title, timestamp)
        
        issue = Issue(
            issue_id=issue_id,
            title=title,
            description=description,
            category=category,
            priority=priority,
            status=IssueStatus.OPEN,
            created_at=timestamp,
            updated_at=timestamp,
            assignee=assignee,
            reporter=reporter,
            project_id=project_id,
            department_id=department_id,
            labels=labels or [],
            tags=tags or [],
            due_date=due_date,
            estimated_hours=estimated_hours,
            environment=environment,
            steps_to_reproduce=steps_to_reproduce,
            expected_behavior=expected_behavior,
            actual_behavior=actual_behavior
        )
        
        self.storage.save(issue)
        self._issues.append(issue)
        
        self.history_manager.record_change(
            issue_id=issue.issue_id,
            field_name="status",
            old_value="",
            new_value=IssueStatus.OPEN.value,
            changed_by=reporter or "system",
            reason="问题创建"
        )
        
        self.logger.info(f"创建问题: {issue_id} - {title}")
        return issue
    
    def _generate_issue_id(self, title: str, timestamp: str) -> str:
        """生成问题ID"""
        content = f"{title}:{timestamp}"
        hash_part = hashlib.md5(content.encode()).hexdigest()[:8].upper()
        return f"ISS-{hash_part}"
    
    def get_issue(self, issue_id: str) -> Optional[Issue]:
        """获取问题"""
        return self.storage.load(issue_id)
    
    def update_issue(
        self,
        issue_id: str,
        changed_by: str = "system",
        **kwargs
    ) -> Optional[Issue]:
        """更新问题"""
        issue = self.storage.load(issue_id)
        if not issue:
            return None
        
        for field_name, new_value in kwargs.items():
            if hasattr(issue, field_name):
                old_value = getattr(issue, field_name)
                
                if old_value != new_value:
                    if isinstance(old_value, Enum):
                        old_value_str = old_value.value
                    else:
                        old_value_str = str(old_value)
                    
                    if isinstance(new_value, Enum):
                        new_value_str = new_value.value
                    else:
                        new_value_str = str(new_value)
                    
                    self.history_manager.record_change(
                        issue_id=issue_id,
                        field_name=field_name,
                        old_value=old_value_str,
                        new_value=new_value_str,
                        changed_by=changed_by
                    )
                    
                    setattr(issue, field_name, new_value)
        
        issue.updated_at = datetime.now().isoformat()
        self.storage.save(issue)
        
        return issue
    
    def _validate_transition(self, current_status: IssueStatus, new_status: IssueStatus) -> bool:
        """验证状态转换"""
        allowed_transitions = ISSUE_STATUS_TRANSITIONS.get(current_status, [])
        return new_status in allowed_transitions
    
    def start_issue(self, issue_id: str, assignee: str = "", changed_by: str = "system") -> Optional[Issue]:
        """开始处理问题"""
        issue = self.storage.load(issue_id)
        if not issue:
            return None
        
        if not self._validate_transition(issue.status, IssueStatus.IN_PROGRESS):
            self.logger.warning(
                f"无效的状态转换: {issue.status.value} -> in_progress"
            )
            return None
        
        old_status = issue.status
        issue.status = IssueStatus.IN_PROGRESS
        issue.updated_at = datetime.now().isoformat()
        
        if assignee:
            issue.assignee = assignee
        
        self.storage.save(issue)
        
        self.history_manager.record_change(
            issue_id=issue_id,
            field_name="status",
            old_value=old_status.value,
            new_value=IssueStatus.IN_PROGRESS.value,
            changed_by=changed_by,
            reason="开始处理问题"
        )
        
        self.logger.info(f"问题 {issue_id} 状态更新为 in_progress")
        return issue
    
    def resolve_issue(
        self,
        issue_id: str,
        resolution: IssueResolution = IssueResolution.FIXED,
        notes: str = "",
        resolved_by: str = "system"
    ) -> Optional[Issue]:
        """解决问题"""
        issue = self.storage.load(issue_id)
        if not issue:
            return None
        
        if not self._validate_transition(issue.status, IssueStatus.RESOLVED):
            self.logger.warning(
                f"无效的状态转换: {issue.status.value} -> resolved"
            )
            return None
        
        old_status = issue.status
        timestamp = datetime.now().isoformat()
        
        issue.status = IssueStatus.RESOLVED
        issue.resolution = resolution
        issue.resolution_notes = notes
        issue.resolved_at = timestamp
        issue.resolved_by = resolved_by
        issue.updated_at = timestamp
        
        self.storage.save(issue)
        
        self.history_manager.record_change(
            issue_id=issue_id,
            field_name="status",
            old_value=old_status.value,
            new_value=IssueStatus.RESOLVED.value,
            changed_by=resolved_by,
            reason=f"问题已解决: {resolution.value}"
        )
        
        self.logger.info(f"问题 {issue_id} 已解决: {resolution.value}")
        return issue
    
    def close_issue(self, issue_id: str, closed_by: str = "system") -> Optional[Issue]:
        """关闭问题"""
        issue = self.storage.load(issue_id)
        if not issue:
            return None
        
        if not self._validate_transition(issue.status, IssueStatus.CLOSED):
            self.logger.warning(
                f"无效的状态转换: {issue.status.value} -> closed"
            )
            return None
        
        old_status = issue.status
        timestamp = datetime.now().isoformat()
        
        issue.status = IssueStatus.CLOSED
        issue.closed_at = timestamp
        issue.closed_by = closed_by
        issue.updated_at = timestamp
        
        self.storage.save(issue)
        
        self.history_manager.record_change(
            issue_id=issue_id,
            field_name="status",
            old_value=old_status.value,
            new_value=IssueStatus.CLOSED.value,
            changed_by=closed_by,
            reason="问题已关闭"
        )
        
        self.logger.info(f"问题 {issue_id} 已关闭")
        return issue
    
    def reopen_issue(
        self,
        issue_id: str,
        reason: str = "",
        reopened_by: str = "system"
    ) -> Optional[Issue]:
        """重新打开问题"""
        issue = self.storage.load(issue_id)
        if not issue:
            return None
        
        if not self._validate_transition(issue.status, IssueStatus.REOPENED):
            self.logger.warning(
                f"无效的状态转换: {issue.status.value} -> reopened"
            )
            return None
        
        old_status = issue.status
        timestamp = datetime.now().isoformat()
        
        issue.status = IssueStatus.REOPENED
        issue.resolution = None
        issue.resolution_notes = ""
        issue.resolved_at = None
        issue.closed_at = None
        issue.updated_at = timestamp
        
        self.storage.save(issue)
        
        self.history_manager.record_change(
            issue_id=issue_id,
            field_name="status",
            old_value=old_status.value,
            new_value=IssueStatus.REOPENED.value,
            changed_by=reopened_by,
            reason=reason or "问题重新打开"
        )
        
        self.logger.info(f"问题 {issue_id} 已重新打开")
        return issue
    
    def add_comment(
        self,
        issue_id: str,
        author: str,
        content: str,
        is_internal: bool = False
    ) -> Optional[IssueComment]:
        """添加评论"""
        issue = self.storage.load(issue_id)
        if not issue:
            return None
        
        comment = self.comment_manager.add_comment(
            issue_id=issue_id,
            author=author,
            content=content,
            is_internal=is_internal
        )
        
        issue.updated_at = datetime.now().isoformat()
        self.storage.save(issue)
        
        return comment
    
    def get_comments(self, issue_id: str, include_internal: bool = True) -> List[IssueComment]:
        """获取问题评论"""
        return self.comment_manager.get_comments(issue_id, include_internal)
    
    def get_history(self, issue_id: str) -> List[IssueHistory]:
        """获取问题历史"""
        return self.history_manager.get_history(issue_id)
    
    def search_issues(self, filters: Optional[Dict[str, Any]] = None) -> List[Issue]:
        """搜索问题"""
        if not filters:
            return self.storage.load_all()
        return self.storage.search(filters)
    
    def get_issues_by_status(self, status: IssueStatus) -> List[Issue]:
        """按状态获取问题"""
        return self.search_issues({"status": status})
    
    def get_issues_by_assignee(self, assignee: str) -> List[Issue]:
        """按负责人获取问题"""
        return self.search_issues({"assignee": assignee})
    
    def get_issues_by_priority(self, priority: IssuePriority) -> List[Issue]:
        """按优先级获取问题"""
        return self.search_issues({"priority": priority})
    
    def get_issues_by_category(self, category: IssueCategory) -> List[Issue]:
        """按类别获取问题"""
        return self.search_issues({"category": category})
    
    def get_blocked_issues(self) -> List[Issue]:
        """获取被阻塞的问题"""
        all_issues = self.storage.load_all()
        return [i for i in all_issues if i.blocked_by]
    
    def get_overdue_issues(self) -> List[Issue]:
        """获取过期问题"""
        all_issues = self.storage.load_all()
        now = datetime.now()
        overdue = []
        
        for issue in all_issues:
            if issue.due_date and issue.status not in [IssueStatus.CLOSED, IssueStatus.RESOLVED]:
                due_date = datetime.fromisoformat(issue.due_date)
                if due_date < now:
                    overdue.append(issue)
        
        return overdue
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        all_issues = self.storage.load_all()
        
        by_status: Dict[str, int] = defaultdict(int)
        by_priority: Dict[str, int] = defaultdict(int)
        by_category: Dict[str, int] = defaultdict(int)
        by_assignee: Dict[str, int] = defaultdict(int)
        
        for issue in all_issues:
            by_status[issue.status.value] += 1
            by_priority[issue.priority.value] += 1
            by_category[issue.category.value] += 1
            if issue.assignee:
                by_assignee[issue.assignee] += 1
        
        open_count = by_status.get("open", 0) + by_status.get("reopened", 0)
        in_progress_count = by_status.get("in_progress", 0)
        resolved_count = by_status.get("resolved", 0)
        closed_count = by_status.get("closed", 0)
        
        resolution_rate = 0.0
        if len(all_issues) > 0:
            resolution_rate = (resolved_count + closed_count) / len(all_issues) * 100
        
        return {
            "total_issues": len(all_issues),
            "open_issues": open_count,
            "in_progress_issues": in_progress_count,
            "resolved_issues": resolved_count,
            "closed_issues": closed_count,
            "resolution_rate": round(resolution_rate, 2),
            "by_status": dict(by_status),
            "by_priority": dict(by_priority),
            "by_category": dict(by_category),
            "by_assignee": dict(by_assignee),
            "overdue_count": len(self.get_overdue_issues()),
            "blocked_count": len(self.get_blocked_issues())
        }
    
    def generate_report(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """生成报告"""
        filters = {}
        if project_id:
            filters["project_id"] = project_id
        
        issues = self.search_issues(filters) if filters else self.storage.load_all()
        stats = self.get_statistics()
        
        recent_changes = self.history_manager.get_recent_changes(50)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "project_id": project_id,
            "statistics": stats,
            "issues": [i.to_dict() for i in issues],
            "recent_changes": [h.to_dict() for h in recent_changes]
        }
    
    def export_to_json(self, output_path: Path, filters: Optional[Dict[str, Any]] = None) -> bool:
        """导出到JSON"""
        try:
            issues = self.search_issues(filters) if filters else self.storage.load_all()
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "exported_at": datetime.now().isoformat(),
                "total_count": len(issues),
                "issues": [i.to_dict() for i in issues]
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"导出 {len(issues)} 个问题到 {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"导出失败: {e}")
            return False
    
    def delete_issue(self, issue_id: str) -> bool:
        """删除问题"""
        issue = self.storage.load(issue_id)
        if not issue:
            return False
        
        self.storage.delete(issue_id)
        self.logger.info(f"删除问题: {issue_id}")
        return True


def setup_logger(verbose: bool = False) -> logging.Logger:
    """配置日志记录器"""
    logger = logging.getLogger("IssueTracker")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG if verbose else logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def main():
    """主函数"""
    logger = setup_logger(verbose=True)
    
    print("=" * 80)
    print("问题追踪器")
    print("=" * 80)
    
    tracker = IssueTracker(logger=logger)
    
    issue = tracker.create_issue(
        title="示例问题：登录功能异常",
        description="用户反馈无法正常登录系统",
        category=IssueCategory.BUG,
        priority=IssuePriority.HIGH,
        reporter="测试团队",
        labels=["登录", "认证"]
    )
    
    print(f"\n创建问题: {issue.issue_id}")
    print(f"标题: {issue.title}")
    print(f"状态: {issue.status.value}")
    print(f"优先级: {issue.priority.value}")
    
    tracker.start_issue(issue.issue_id, assignee="开发团队", changed_by="项目经理")
    tracker.add_comment(issue.issue_id, "开发团队", "已定位问题，正在修复中")
    
    tracker.resolve_issue(
        issue.issue_id,
        resolution=IssueResolution.FIXED,
        notes="修复了登录验证逻辑",
        resolved_by="开发团队"
    )
    
    tracker.close_issue(issue.issue_id, closed_by="测试团队")
    
    stats = tracker.get_statistics()
    print(f"\n统计信息:")
    print(f"总问题数: {stats['total_issues']}")
    print(f"开放问题: {stats['open_issues']}")
    print(f"进行中: {stats['in_progress_issues']}")
    print(f"已解决: {stats['resolved_issues']}")
    print(f"已关闭: {stats['closed_issues']}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
