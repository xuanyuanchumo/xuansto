from typing import TypeVar, Generic, Type, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from pydantic import BaseModel

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseCRUDService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_or_404(self, db: Session, id: int, entity_name: str = "Entity") -> ModelType:
        obj = self.get(db, id)
        if not obj:
            raise HTTPException(status_code=404, detail=f"{entity_name} not found")
        return obj

    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        query = db.query(self.model)
        if filters:
            for key, value in filters.items():
                if value is not None and hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        return query.offset(skip).limit(limit).all()

    def get_all(self, db: Session) -> List[ModelType]:
        return db.query(self.model).all()

    def create(self, db: Session, obj_in: CreateSchemaType) -> ModelType:
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, 
        db: Session, 
        db_obj: ModelType, 
        obj_in: UpdateSchemaType
    ) -> ModelType:
        update_data = obj_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_obj, key, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> bool:
        obj = self.get(db, id)
        if obj:
            db.delete(obj)
            db.commit()
            return True
        return False

    def count(self, db: Session, filters: Optional[Dict[str, Any]] = None) -> int:
        query = db.query(func.count(self.model.id))
        if filters:
            for key, value in filters.items():
                if value is not None and hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        return query.scalar()

    def exists_by_name(self, db: Session, name: str, exclude_id: Optional[int] = None) -> bool:
        query = db.query(self.model).filter(self.model.name == name)
        if exclude_id:
            query = query.filter(self.model.id != exclude_id)
        return query.first() is not None

    def check_unique_name(
        self, 
        db: Session, 
        name: str, 
        entity_name: str,
        exclude_id: Optional[int] = None
    ) -> None:
        if self.exists_by_name(db, name, exclude_id):
            raise HTTPException(
                status_code=409, 
                detail=f"{entity_name} with name '{name}' already exists"
            )

class StatusValidator:
    def __init__(self, valid_statuses: List[str]):
        self.valid_statuses = valid_statuses

    def validate(self, status: str, field_name: str = "status") -> None:
        if status not in self.valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid {field_name}. Must be one of: {self.valid_statuses}"
            )

class PaginationHelper:
    @staticmethod
    def calculate_offset(page: int, page_size: int) -> int:
        return (page - 1) * page_size

    @staticmethod
    def calculate_total_pages(total: int, page_size: int) -> int:
        return (total + page_size - 1) // page_size

    @staticmethod
    def get_paginated_result(
        items: List[Any],
        total: int,
        page: int,
        page_size: int
    ) -> Dict[str, Any]:
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": PaginationHelper.calculate_total_pages(total, page_size)
        }
