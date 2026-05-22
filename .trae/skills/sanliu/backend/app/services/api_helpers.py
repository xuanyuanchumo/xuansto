from typing import Any, Dict, List, Optional, TypeVar, Generic
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

T = TypeVar("T")

class APIResponseBuilder:
    @staticmethod
    def success(data: Any = None, message: str = "Success") -> Dict[str, Any]:
        return {
            "success": True,
            "message": message,
            "data": data
        }

    @staticmethod
    def error(message: str, code: int = 400) -> Dict[str, Any]:
        return {
            "success": False,
            "message": message,
            "error_code": code
        }

    @staticmethod
    def deleted(entity_name: str, entity_id: int) -> Dict[str, Any]:
        return {
            "message": f"{entity_name} deleted successfully",
            "id": entity_id
        }

class StatsCalculator:
    @staticmethod
    def get_status_distribution(
        db: Session,
        model: Any,
        status_field: str = "status",
        filters: Optional[Dict] = None
    ) -> Dict[str, int]:
        query = db.query(
            getattr(model, status_field),
            func.count(model.id)
        )
        if filters:
            for key, value in filters.items():
                if value is not None:
                    query = query.filter(getattr(model, key) == value)
        results = query.group_by(getattr(model, status_field)).all()
        return {status: count for status, count in results}

    @staticmethod
    def calculate_percentage(part: int, total: int) -> float:
        return round((part / total * 100), 2) if total > 0 else 0.0

    @staticmethod
    def get_average(
        db: Session,
        model: Any,
        field: str,
        filters: Optional[Dict] = None
    ) -> Optional[float]:
        query = db.query(func.avg(getattr(model, field)))
        if filters:
            for key, value in filters.items():
                if value is not None:
                    query = query.filter(getattr(model, key) == value)
        result = query.scalar()
        return round(result, 2) if result else None

class EntityValidator:
    @staticmethod
    def check_exists(db: Session, model: Any, id: int, entity_name: str) -> Any:
        obj = db.query(model).filter(model.id == id).first()
        if not obj:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"{entity_name} not found")
        return obj

    @staticmethod
    def check_not_exists(db: Session, model: Any, field: str, value: Any, entity_name: str) -> None:
        obj = db.query(model).filter(getattr(model, field) == value).first()
        if obj:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=409,
                detail=f"{entity_name} with {field} '{value}' already exists"
            )

class SearchHelper:
    @staticmethod
    def build_search_query(
        db: Session,
        model: Any,
        search_fields: List[str],
        keyword: str
    ):
        from sqlalchemy import or_
        query = db.query(model)
        search_pattern = f"%{keyword}%"
        filters = []
        for field in search_fields:
            if hasattr(model, field):
                filters.append(getattr(model, field).ilike(search_pattern))
        if filters:
            query = query.filter(or_(*filters))
        return query

class CacheHelper:
    @staticmethod
    def get_or_set(
        cache_service: Any,
        key: str,
        fetch_func: callable,
        ttl: int = 60
    ) -> Any:
        cached = cache_service.get_json(key)
        if cached:
            return cached
        result = fetch_func()
        cache_service.set_json(key, result, ttl=ttl)
        return result

class ListResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    class Config:
        from_attributes = True
