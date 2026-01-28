from typing import Generic, List, Optional, Type, TypeVar

from sqlmodel import Session, SQLModel, select

T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    """Base repository class for database operations"""

    def __init__(self, session: Session, model: Type[T]):
        self.session = session
        self.model = model

    def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by ID"""
        entity = self.session.get(self.model, id)
        if entity and getattr(entity, "is_deleted", False):
            return None
        return entity

    def get_all(
        self, skip: int = 0, limit: int = 100, deleted: bool = False
    ) -> List[T]:
        """Get all entities with pagination"""
        statement = (
            select(self.model)
            .where(getattr(self.model, "is_deleted", False) == deleted)
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def restore(self, id: int) -> Optional[T]:
        """Restore a soft-deleted entity"""
        if not hasattr(self.model, "is_deleted"):
            return None

        statement = select(self.model).where(
            self.model.id == id, self.model.is_deleted == True
        )
        entity = self.session.exec(statement).first()

        if entity:
            entity.is_deleted = False
            self.session.add(entity)
            self.session.commit()
            self.session.refresh(entity)
            return entity
        return None

    def create(self, entity: T) -> T:
        """Create a new entity"""
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def update(self, entity: T) -> T:
        """Update an entity"""
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def delete(self, entity: T) -> None:
        """Soft delete an entity"""
        if hasattr(entity, "is_deleted"):
            entity.is_deleted = True
            self.session.add(entity)
        else:
            self.session.delete(entity)
        self.session.commit()

    def delete_by_id(self, id: int) -> bool:
        """Delete entity by ID"""
        entity = self.get_by_id(id)
        if entity:
            self.delete(entity)
            return True
        return False
