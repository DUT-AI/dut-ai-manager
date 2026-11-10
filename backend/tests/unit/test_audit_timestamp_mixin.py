"""Unit tests for SQLAlchemyAuditTimestampMixin."""

from sqlalchemy import Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.shared.infrastructure.base_model import SQLAlchemyAuditTimestampMixin


class DummyBase(DeclarativeBase):
    pass


class DummyHardDeleteModel(SQLAlchemyAuditTimestampMixin, DummyBase):
    __tablename__ = "dummy_hard_delete"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)


def test_audit_timestamp_mixin_fields():
    """Kiểm tra model kế thừa SQLAlchemyAuditTimestampMixin có timestamps và audit nhưng không có is_deleted."""
    assert hasattr(DummyHardDeleteModel, "created_at")
    assert hasattr(DummyHardDeleteModel, "updated_at")
    assert hasattr(DummyHardDeleteModel, "created_by")
    assert hasattr(DummyHardDeleteModel, "updated_by")

    # BẮT BUỘC KHÔNG ĐƯỢC CÓ is_deleted
    assert not hasattr(DummyHardDeleteModel, "is_deleted")
