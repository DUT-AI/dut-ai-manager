"""
Unit tests for UUIDv7 generation, composable mixins, and optional soft-delete BaseRepository.
"""

import time
from uuid import UUID

import pytest
from sqlalchemy import Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.shared.domain.base_entity import (
    BaseEntity,
    BaseUuidEntity,
    SoftDeleteEntityMixin,
)
from app.shared.domain.uuid_utils import uuid7
from app.shared.infrastructure.base_model import (
    SQLAlchemyIntPrimaryKeyMixin,
    SQLAlchemySoftDeleteMixin,
    SQLAlchemyTimestampMixin,
    SQLAlchemyTimestampOnlyMixin,
    SQLAlchemyUuidPrimaryKeyMixin,
)
from app.shared.infrastructure.base_repository import BaseRepository

# ==============================================================================
# In-Memory Test Models & Entities Setup
# ==============================================================================


class InMemoryBase(DeclarativeBase):
    pass


# Dummy User table to satisfy ForeignKey("users.id") in Audit mixin
class UserDummyModel(InMemoryBase):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, default="tester")


# 1. New Model: UUID PK, only timestamps (NO is_deleted, NO audit)
class TransientLogEntity(BaseUuidEntity):
    message: str


class TransientLogModel(SQLAlchemyUuidPrimaryKeyMixin, SQLAlchemyTimestampOnlyMixin, InMemoryBase):
    __tablename__ = "transient_logs"
    message: Mapped[str] = mapped_column(String)

    @classmethod
    def from_entity(cls, entity: TransientLogEntity) -> "TransientLogModel":
        return cls(id=entity.id, message=entity.message)

    def to_entity(self) -> TransientLogEntity:
        return TransientLogEntity(
            id=self.id,
            message=self.message,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


# 2. New Model: UUID PK, timestamps, AND soft-delete
class ProjectEntity(BaseUuidEntity, SoftDeleteEntityMixin):
    title: str


class ProjectModel(
    SQLAlchemyUuidPrimaryKeyMixin,
    SQLAlchemyTimestampOnlyMixin,
    SQLAlchemySoftDeleteMixin,
    InMemoryBase,
):
    __tablename__ = "test_projects"
    title: Mapped[str] = mapped_column(String)

    @classmethod
    def from_entity(cls, entity: ProjectEntity) -> "ProjectModel":
        return cls(id=entity.id, title=entity.title, is_deleted=entity.is_deleted)

    def to_entity(self) -> ProjectEntity:
        return ProjectEntity(
            id=self.id,
            title=self.title,
            is_deleted=self.is_deleted,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


# 3. Legacy Model: Int PK, legacy composite timestamp mixin (has is_deleted & audit)
class LegacyArticleEntity(BaseEntity):
    name: str


class LegacyArticleModel(SQLAlchemyIntPrimaryKeyMixin, SQLAlchemyTimestampMixin, InMemoryBase):
    __tablename__ = "legacy_articles"
    name: Mapped[str] = mapped_column(String)

    @classmethod
    def from_entity(cls, entity: LegacyArticleEntity) -> "LegacyArticleModel":
        return cls(id=entity.id, name=entity.name, is_deleted=entity.is_deleted)

    def to_entity(self) -> LegacyArticleEntity:
        return LegacyArticleEntity(
            id=self.id,
            name=self.name,
            is_deleted=self.is_deleted,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
        )


@pytest.fixture
def db_session():
    """In-memory SQLite session for testing repository operations."""
    engine = create_engine("sqlite:///:memory:")
    InMemoryBase.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


# ==============================================================================
# Phase 1: UUIDv7 Generation Tests
# ==============================================================================


def test_uuid7_basic_properties():
    """Verify UUIDv7 adheres to RFC 9562 version and variant."""
    u = uuid7()
    assert isinstance(u, UUID)
    assert u.version == 7
    assert u.variant == "specified in RFC 4122"


def test_uuid7_monotonic_time_ordering():
    """Verify UUIDv7 generates sequentially ordered values across time."""
    uuids = []
    for _ in range(10):
        uuids.append(uuid7())
        time.sleep(0.002)

    for i in range(len(uuids) - 1):
        assert uuids[i] < uuids[i + 1]


def test_uuid7_timestamp_precision():
    """Verify extracted timestamp from 48 bits matches current system time."""
    now_ms = int(time.time() * 1000)
    u = uuid7()
    extracted_ms = (u.int >> 80) & 0xFFFFFFFFFFFF
    assert abs(now_ms - extracted_ms) < 1000


# ==============================================================================
# Phase 2: User Story 1 - Flexible UUID Primary Key Support (MVP)
# ==============================================================================


def test_uuid_entity_and_model_crud(db_session: Session):
    """Verify adding and getting entities with UUIDv7 primary keys."""
    repo = BaseRepository(db_session, TransientLogModel)

    entity = TransientLogEntity(message="System started")
    assert isinstance(entity.id, UUID)
    assert entity.id.version == 7

    created = repo.add(entity)
    assert created.id == entity.id
    assert created.message == "System started"

    # Query by UUID object
    fetched = repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.message == "System started"

    # Query by string UUID
    fetched_by_str = repo.get_by_id(str(created.id))
    assert fetched_by_str is not None
    assert fetched_by_str.id == created.id


# ==============================================================================
# Phase 3: User Story 2 - Decoupled & Optional Soft-Deletion
# ==============================================================================


def test_model_without_soft_delete_queries_and_deletion(db_session: Session):
    """Verify models without is_deleted do not trigger is_deleted query filters and support hard_delete."""
    repo = BaseRepository(db_session, TransientLogModel)

    log1 = repo.add(TransientLogEntity(message="log 1"))
    log2 = repo.add(TransientLogEntity(message="log 2"))

    # get_all should succeed without searching for is_deleted column
    all_logs = repo.get_all()
    assert len(all_logs) == 2

    # get_paged should succeed without count(is_deleted)
    paged_logs, total = repo.get_paged()
    assert total == 2
    assert len(paged_logs) == 2

    # Calling soft_delete on model lacking is_deleted MUST raise NotImplementedError
    with pytest.raises(NotImplementedError, match="does not support soft delete"):
        repo.soft_delete(log1)

    with pytest.raises(NotImplementedError, match="does not support soft delete"):
        repo.delete_by_id(log1.id)

    # Calling hard_delete permanently deletes the row
    repo.hard_delete(log1)
    assert repo.get_by_id(log1.id) is None
    assert len(repo.get_all()) == 1

    repo.hard_delete_by_id(log2.id)
    assert repo.get_by_id(log2.id) is None
    assert len(repo.get_all()) == 0


def test_model_with_soft_delete_lifecycle(db_session: Session):
    """Verify models with is_deleted properly hide records upon soft_delete and restore."""
    repo = BaseRepository(db_session, ProjectModel)

    project = repo.add(ProjectEntity(title="AI Platform"))
    assert project.is_deleted is False

    # Soft delete
    repo.soft_delete(project)

    # get_by_id returns None for soft-deleted record
    assert repo.get_by_id(project.id) is None

    # get_all does not include soft-deleted record
    assert len(repo.get_all()) == 0

    # Can restore
    restored = repo.restore(project)
    assert restored.is_deleted is False
    assert repo.get_by_id(project.id) is not None

    # Hard delete removes it permanently
    repo.hard_delete_by_id(project.id)
    assert repo.get_by_id(project.id) is None
    assert len(repo.get_all(deleted=True)) == 0


# ==============================================================================
# Phase 4: User Story 3 - Backward Compatibility for Legacy Models
# ==============================================================================


def test_legacy_model_backward_compatibility(db_session: Session):
    """Verify legacy models with int IDs and composite TimestampMixin work seamlessly."""
    repo = BaseRepository(db_session, LegacyArticleModel)

    article = repo.add(LegacyArticleEntity(name="Old Post"))
    assert isinstance(article.id, int)
    assert article.is_deleted is False

    # Soft delete works via delete_by_id
    success = repo.delete_by_id(article.id)
    assert success is True
    assert repo.get_by_id(article.id) is None

    # Can include deleted
    deleted_articles = repo.get_all(deleted=True)
    assert len(deleted_articles) == 1
    assert deleted_articles[0].id == article.id
