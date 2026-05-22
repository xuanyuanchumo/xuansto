"""
知识查询 API组 - /api/knowledge/*

知识库CRUD、搜索、推荐
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import time
import re
import random

from ..models.base import get_db
from ..services.cache import cache_service

router = APIRouter()

class KnowledgeCategory(str, Enum):
    PATTERN = "pattern"
    BEST_PRACTICE = "best_practice"
    LESSON_LEARNED = "lesson_learned"
    DECISION_RECORD = "decision_record"
    TECHNICAL_NOTE = "technical_note"
    API_REFERENCE = "api_reference"
    TROUBLESHOOTING = "troubleshooting"
    EVOLUTION_INSIGHT = "evolution_insight"

class KnowledgeStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"

class KnowledgeItemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="标题")
    content: str = Field(..., min_length=1, description="内容")
    category: KnowledgeCategory = Field(..., description="分类")
    tags: List[str] = Field(default_factory=list, description="标签")
    source: Optional[str] = Field(None, description="来源")
    author: Optional[str] = Field(None, description="作者")
    status: KnowledgeStatus = Field(KnowledgeStatus.DRAFT, description="状态")
    priority: int = Field(3, ge=1, le=5, description="优先级(1-5)")
    related_ids: List[str] = Field(default_factory=list, description="关联知识ID列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")

class KnowledgeItemCreate(KnowledgeItemBase):
    pass

class KnowledgeItemUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = None
    category: Optional[KnowledgeCategory] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    author: Optional[str] = None
    status: Optional[KnowledgeStatus] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    related_ids: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class KnowledgeItem(KnowledgeItemBase):
    id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    version: int = 1
    view_count: int = 0
    like_count: int = 0
    search_vector: Optional[str] = None

    class Config:
        from_attributes = True

class KnowledgeListResponse(BaseModel):
    total: int
    items: List[KnowledgeItem]
    page: int
    page_size: int
    total_pages: int

class SearchResultItem(BaseModel):
    id: str
    title: str
    content_preview: str
    category: KnowledgeCategory
    score: float = Field(0.0, ge=0, le=1, description="相关度分数")
    highlights: List[str] = Field(default_factory=list, description="高亮片段")
    matched_tags: List[str] = Field(default_factory=list)

class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResultItem]
    search_time_ms: float
    suggestions: List[str] = Field(default_factory=list)

class RecommendResponse(BaseModel):
    knowledge_id: str
    title: str
    reason: str
    relevance_score: float = Field(0.0, ge=0, le=1)
    category: KnowledgeCategory

_knowledge_store: Dict[str, KnowledgeItem] = {}

def _init_mock_data():
    if _knowledge_store:
        return
    mock_items = [
        KnowledgeItem(
            id="kb_001",
            title="三省六部架构设计模式",
            content="三省六部架构是一种基于中国古代官制思想的软件架构模式，将系统划分为中书省（决策）、门下省（审核）、尚书省（执行）三层，每层下设六部职能部门。这种架构实现了职责分离、相互制衡的设计目标。",
            category=KnowledgeCategory.PATTERN,
            tags=["architecture", "design_pattern", "sanliu", "separation_of_concerns"],
            source="system_design",
            author="architect_team",
            status=KnowledgeStatus.PUBLISHED,
            priority=1,
            related_ids=[],
            view_count=1256,
            like_count=89,
            version=3
        ),
        KnowledgeItem(
            id="kb_002",
            title="TDD实践指南：从单元测试到集成测试",
            content="测试驱动开发(TDD)是敏捷开发的核心实践之一。本指南涵盖了红-绿-重构循环的最佳实践、测试金字塔理论、以及如何在复杂系统中有效应用TDD。重点包括：1) 测试命名规范 2) Mock对象使用策略 3) 边界条件覆盖 4) 持续集成中的测试策略。",
            category=KnowledgeCategory.BEST_PRACTICE,
            tags=["tdd", "testing", "agile", "unit_test", "integration_test"],
            source="engineering_standards",
            author="qa_team",
            status=KnowledgeStatus.PUBLISHED,
            priority=2,
            related_ids=["kb_005"],
            view_count=892,
            like_count=67,
            version=2
        ),
        KnowledgeItem(
            id="kb_003",
            title="API版本管理策略与向后兼容性",
            content="在微服务架构中，API版本管理至关重要。本文档详细介绍了语义化版本号(SemVer)、URL版本控制vs Header版本控制、废弃策略、以及如何通过适配器模式实现平滑过渡。核心原则：不破坏现有客户端、提供充分的迁移期、清晰的变更日志。",
            category=KnowledgeCategory.API_REFERENCE,
            tags=["api", "versioning", "backward_compatibility", "microservice", "rest"],
            source="api_design",
            author="platform_team",
            status=KnowledgeStatus.PUBLISHED,
            priority=2,
            related_ids=["kb_001"],
            view_count=654,
            like_count=45,
            version=1
        ),
        KnowledgeItem(
            id="kb_004",
            title="内存泄漏排查实战经验",
            content="在生产环境中排查内存泄漏需要系统化的方法：1) 使用heap snapshot对比分析 2) 关注闭包和事件监听器的引用 3) 检查缓存策略是否合理 4) 利用Chrome DevTools Memory面板定位问题根因。典型案例：定时器未清除导致的内存持续增长、大对象缓存无上限等。",
            category=KnowledgeCategory.TROUBLESHOOTING,
            tags=["memory_leak", "performance", "debugging", "javascript", "optimization"],
            source="incident_review",
            author="sre_team",
            status=KnowledgeStatus.PUBLISHED,
            priority=1,
            related_ids=["kb_007"],
            view_count=1432,
            like_count=112,
            version=4
        ),
        KnowledgeItem(
            id="kb_005",
            title="演化循环中的质量保障机制",
            content="自演化系统的质量保障需要在每个阶段嵌入质量门禁：分析阶段的输入验证、规划阶段的可行性评审、执行阶段的增量测试、验证阶段的回归检测、部署阶段的灰度发布。关键指标包括：缺陷密度、测试覆盖率、MTTR、变更失败率。",
            category=KnowledgeCategory.EVOLUTION_INSIGHT,
            tags=["evolution", "quality_gate", "ci_cd", "automation", "monitoring"],
            source="evolution_engine",
            author="core_team",
            status=KnowledgeStatus.PUBLISHED,
            priority=1,
            related_ids=["kb_002", "kb_006"],
            view_count=567,
            like_count=78,
            version=2
        ),
        KnowledgeItem(
            id="kb_006",
            title="持续集成流水线最佳实践",
            content="高效的CI流水线应遵循以下原则：快速反馈（<5分钟）、并行构建、缓存依赖、环境一致性、安全扫描左移。推荐工具链：构建→单元测试→静态分析→安全扫描→集成测试→部署准备。每个阶段应有明确的质量门禁标准。",
            category=KnowledgeCategory.BEST_PRACTICE,
            tags=["ci_cd", "pipeline", "devops", "automation", "jenkins"],
            source="devops_guide",
            author="devops_team",
            status=KnowledgeStatus.PUBLISHED,
            priority=2,
            related_ids=["kb_002", "kb_005"],
            view_count=778,
            like_count=56,
            version=1
        ),
        KnowledgeItem(
            id="kb_007",
            title="性能优化决策记录：2026-Q1系统提速计划",
            content="背景：系统响应时间P99超过3秒，用户体验下降明显。决策：采用多级缓存+异步化+数据库索引优化方案。预期效果：P99降低至800ms以内。实际结果：P99降至650ms，CPU使用率下降22%。",
            category=KnowledgeCategory.DECISION_RECORD,
            tags=["performance", "optimization", "decision", "cache", "async"],
            source="tech_decision",
            author="架构委员会",
            status=KnowledgeStatus.PUBLISHED,
            priority=2,
            related_ids=["kb_004"],
            view_count=445,
            like_count=34,
            version=1
        ),
        KnowledgeItem(
            id="kb_008",
            title="WebSocket连接管理的经验教训",
            content="在高并发WebSocket场景中遇到的坑：1) 心跳机制必须实现且间隔合理(推荐30s) 2) 重连需指数退避避免雪崩 3) 消息队列保证有序性 4) 服务端推送频率控制 5) 断线重连时状态恢复策略。教训：初期未做流量控制导致服务崩溃。",
            category=KnowledgeCategory.LESSON_LEARNED,
            tags=["websocket", "realtime", "connection_management", "scalability", "lesson"],
            source="postmortem",
            author="backend_team",
            status=KnowledgeStatus.PUBLISHED,
            priority=3,
            related_ids=[],
            view_count=334,
            like_count=28,
            version=1
        ),
    ]
    for item in mock_items:
        _knowledge_store[item.id] = item

_init_mock_data()

@router.get(
    "",
    response_model=KnowledgeListResponse,
    summary="知识列表",
    description="获取知识条目列表，支持分页、按分类和状态筛选"
)
async def get_knowledge_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[KnowledgeCategory] = Query(None),
    status: Optional[KnowledgeStatus] = Query(None),
    tag: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="关键词搜索"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向: asc, desc"),
    db: Session = Depends(get_db)
):
    items = list(_knowledge_store.values())

    if category:
        items = [i for i in items if i.category == category]
    if status:
        items = [i for i in items if i.status == status]
    if tag:
        items = [i for i in items if tag in i.tags]
    if search:
        search_lower = search.lower()
        items = [i for i in items if search_lower in i.title.lower() or search_lower in i.content.lower() or search_lower in ' '.join(i.tags).lower()]

    reverse = sort_order.lower() == "desc"
    items.sort(key=lambda x: getattr(x, sort_by, x.created_at), reverse=reverse)

    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_items = items[start:end]

    return KnowledgeListResponse(
        total=total,
        items=paginated_items,
        page=page,
        page_size=page_size,
        total_pages=max(1, (total + page_size - 1) // page_size)
    )

@router.post(
    "",
    response_model=KnowledgeItem,
    summary="新增知识条目",
    description="创建新的知识条目"
)
async def create_knowledge_item(
    item: KnowledgeItemCreate,
    db: Session = Depends(get_db)
):
    new_id = f"kb_{int(time.time() * 1000)}_{random.randint(1000,9999)}"
    new_item = KnowledgeItem(
        **item.model_dump(),
        id=new_id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        version=1,
        view_count=0,
        like_count=0
    )
    _knowledge_store[new_id] = new_item
    return new_item

@router.get(
    "/{item_id}",
    response_model=KnowledgeItem,
    summary="获取知识详情",
    description="根据ID获取知识条目的完整信息"
)
async def get_knowledge_item(
    item_id: str,
    db: Session = Depends(get_db)
):
    item = _knowledge_store.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"知识条目不存在: {item_id}")
    item.view_count += 1
    return item

@router.put(
    "/{item_id}",
    response_model=KnowledgeItem,
    summary="更新知识",
    description="更新指定知识条目"
)
async def update_knowledge_item(
    item_id: str,
    update_data: KnowledgeItemUpdate,
    db: Session = Depends(get_db)
):
    item = _knowledge_store.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"知识条目不存在: {item_id}")

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(item, field, value)

    item.updated_at = datetime.now()
    item.version += 1
    return item

@router.delete(
    "/{item_id}",
    summary="删除知识",
    description="删除指定知识条目（软删除或硬删除）"
)
async def delete_knowledge_item(
    item_id: str,
    hard_delete: bool = Query(False, description="是否硬删除"),
    db: Session = Depends(get_db)
):
    item = _knowledge_store.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"知识条目不存在: {item_id}")

    if hard_delete:
        del _knowledge_store[item_id]
    else:
        item.status = KnowledgeStatus.ARCHIVED

    return {"success": True, "message": f"知识条目 {item_id} 已{'删除' if hard_delete else '归档'}"}

@router.get(
    "/search",
    response_model=SearchResponse,
    summary="全文搜索",
    description="对知识库进行全文搜索，返回相关度排序的结果"
)
async def search_knowledge(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    category: Optional[KnowledgeCategory] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    query_lower = q.lower()
    results = []

    for item in _knowledge_store.values():
        if category and item.category != category:
            continue

        score = 0.0
        highlights = []

        if query_lower in item.title.lower():
            score += 0.5
            highlights.append(f"标题匹配: {item.title}")
        if query_lower in item.content.lower():
            score += 0.3
            idx = item.content.lower().find(query_lower)
            preview_start = max(0, idx - 30)
            preview_end = min(len(item.content), idx + len(q) + 60)
            highlights.append(f"...{item.content[preview_start:preview_end]}...")

        tag_matches = [t for t in item.tags if query_lower in t.lower()]
        if tag_matches:
            score += 0.2 * len(tag_matches)
            highlights.append(f"标签匹配: {', '.join(tag_matches)}")

        if score > 0:
            content_preview = item.content[:150] + "..." if len(item.content) > 150 else item.content
            results.append(SearchResultItem(
                id=item.id,
                title=item.title,
                content_preview=content_preview,
                category=item.category,
                score=min(score, 1.0),
                highlights=highlights[:3],
                matched_tags=tag_matches
            ))

    results.sort(key=lambda x: x.score, reverse=True)
    results = results[:limit]

    search_time = (time.time() - start_time) * 1000
    suggestions = list(set(
        tag for item in _knowledge_store.values()
        for tag in item.tags
        if query_lower in tag.lower()
    ))[:5]

    return SearchResponse(
        query=q,
        total_results=len(results),
        results=results,
        search_time_ms=round(search_time, 2),
        suggestions=suggestions
    )

@router.get(
    "/recommend",
    response_model=List[RecommendResponse],
    summary="智能推荐",
    description="基于当前上下文或浏览历史的智能知识推荐"
)
async def recommend_knowledge(
    current_item_id: Optional[str] = Query(None, description="当前查看的知识ID"),
    category: Optional[KnowledgeCategory] = Query(None),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    recommendations = []
    current_item = _knowledge_store.get(current_item_id) if current_item_id else None

    candidates = list(_knowledge_store.values())
    if current_item_id:
        candidates = [c for c in candidates if c.id != current_item_id]
    if category:
        candidates = [c for c in candidates if c.category == category]

    for candidate in candidates[:limit * 3]:
        score = random.uniform(0.5, 0.98)
        if current_item:
            shared_tags = set(current_item.tags) & set(candidate.tags)
            if shared_tags:
                score += 0.1 * len(shared_tags)
            if candidate.category == current_item.category:
                score += 0.05

        reasons = []
        if current_item and set(current_item.tags) & set(candidate.tags):
            reasons.append(f"共同标签: {', '.join(set(current_item.tags) & set(candidate.tags))}")
        if current_item and candidate.category == current_item.category:
            reasons.append("相同分类")
        reasons.append(candidate.category.value)

        recommendations.append(RecommendResponse(
            knowledge_id=candidate.id,
            title=candidate.title,
            reason="; ".join(reasons),
            relevance_score=min(round(score, 2), 1.0),
            category=candidate.category
        ))

    recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
    return recommendations[:limit]

@router.get(
    "/categories",
    summary="获取所有分类",
    description="获取知识库的所有分类及其统计信息"
)
async def get_categories(db: Session = Depends(get_db)):
    categories = {}
    for cat in KnowledgeCategory:
        count = sum(1 for item in _knowledge_store.values() if item.category == cat)
        categories[cat.value] = {
            "name": cat.value.replace("_", " ").title(),
            "count": count,
            "description": _get_category_description(cat)
        }
    return categories

@router.get(
    "/tags",
    summary="获取热门标签",
    description="获取知识库中使用最多的标签"
)
async def get_popular_tags(limit: int = Query(30, ge=1, le=100), db: Session = Depends(get_db)):
    tag_counts: Dict[str, int] = {}
    for item in _knowledge_store.values():
        for tag in item.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [{"tag": t, "count": c} for t, c in sorted_tags]

@router.post(
    "/{item_id}/like",
    summary="点赞知识条目",
    description="为知识条目点赞"
)
async def like_knowledge_item(item_id: str, db: Session = Depends(get_db)):
    item = _knowledge_store.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"知识条目不存在: {item_id}")
    item.like_count += 1
    return {"success": True, "like_count": item.like_count}

def _get_category_description(cat: KnowledgeCategory) -> str:
    descriptions = {
        KnowledgeCategory.PATTERN: "设计模式和架构模式",
        KnowledgeCategory.BEST_PRACTICE: "经过验证的最佳实践方法",
        KnowledgeCategory.LESSON_LEARNED: "项目中积累的经验教训",
        KnowledgeCategory.DECISION_RECORD: "重要技术决策的记录",
        KnowledgeCategory.TECHNICAL_NOTE: "技术笔记和文档",
        KnowledgeCategory.API_REFERENCE: "API接口文档和参考",
        KnowledgeCategory.TROUBLESHOOTING: "问题排查和解决方案",
        KnowledgeCategory.EVOLUTION_INSIGHT: "系统演化的洞察和分析",
    }
    return descriptions.get(cat, "")
