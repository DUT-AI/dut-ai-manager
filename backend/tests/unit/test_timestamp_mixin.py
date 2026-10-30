"""Unit tests for SQLAlchemyTimestampMixin and timestamp automation."""

from datetime import datetime, timezone
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.domain.base_entity import BaseEntity
from app.shared.infrastructure.base_model import Base, SQLAlchemyTimestampMixin


class DummyModel(SQLAlchemyTimestampMixin, Base):
    __tablename__ = "dummy_test_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50))


def test_base_entity_default_utc():
    entity = BaseEntity()
    assert entity.created_at is not None
    assert entity.created_at.tzinfo == timezone.utc
    assert entity.updated_at is not None
    assert entity.updated_at.tzinfo == timezone.utc


def test_sqlalchemy_timestamp_mixin_configuration():
    # Verify column type specifies timezone=True for PostgreSQL TIMESTAMPTZ
    created_col = DummyModel.__table__.columns["created_at"]
    updated_col = DummyModel.__table__.columns["updated_at"]

    assert created_col.type.timezone is True
    assert updated_col.type.timezone is True

    # Verify python client-side default callable produces UTC-aware datetime
    assert created_col.default is not None
    default_val = created_col.default.arg(None)
    assert isinstance(default_val, datetime)
    assert default_val.tzinfo == timezone.utc

    assert updated_col.default is not None
    default_upd = updated_col.default.arg(None)
    assert isinstance(default_upd, datetime)
    assert default_upd.tzinfo == timezone.utc
