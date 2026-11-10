"""
Permission Request ORM Model — SQLAlchemy 2.0, infrastructure layer.
"""

from typing import TYPE_CHECKING, Any

from pydantic import TypeAdapter
from sqlalchemy import Index, String, literal_column
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.types import JSON, TypeDecorator

from app.permission_request.domain.entity import (
    PermissionRequest as PermissionRequestEntity,
)
from app.permission_request.domain.payloads import (
    BasePermissionPayload,
    PermissionPayloadUnion,
)
from app.permission_request.domain.value_objects import RequestCategory
from app.shared.domain.value_objects import UserRef
from app.shared.infrastructure.base_model import Base, SQLAlchemyTimestampMixin

if TYPE_CHECKING:
    from app.user.infrastructure.model import UserModel


def _normalize_payload_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Tự động suy diễn discriminator category nếu dict thiếu key này."""
    if "category" in d and d["category"]:
        return d
    result = dict(d)
    if "old_meeting_id" in result:
        result["category"] = RequestCategory.CHANGE_MEETING.value
        result.pop("start_time", None)
    elif "homework_id" in result:
        result["category"] = RequestCategory.POSTPONE.value
    elif "start_time" in result and "meeting_id" in result:
        result["category"] = RequestCategory.LATE.value
    elif "meeting_id" in result:
        result["category"] = RequestCategory.ABSENCE.value
    else:
        result["category"] = RequestCategory.OTHER.value
    return result


class PydanticPayloadType(TypeDecorator[PermissionPayloadUnion]):
    """SQLAlchemy TypeDecorator tự động serialize/deserialize Pydantic discriminated union payload."""

    impl = JSON
    cache_ok = True

    _adapter = TypeAdapter(PermissionPayloadUnion)

    def process_bind_param(
        self, value: object, dialect: object
    ) -> dict[str, Any] | None:
        if value is None:
            return None
        if isinstance(value, BasePermissionPayload):
            return value.model_dump(mode="json")
        if isinstance(value, dict):
            normalized = _normalize_payload_dict(value)
            parsed = self._adapter.validate_python(normalized)
            return self._adapter.dump_python(parsed, mode="json")
        return None

    def process_result_value(
        self, value: object, dialect: object
    ) -> PermissionPayloadUnion | None:
        if value is None or isinstance(value, BasePermissionPayload):
            return value
        if isinstance(value, dict):
            normalized = _normalize_payload_dict(value)
            return self._adapter.validate_python(normalized)
        return None


class PermissionRequest(SQLAlchemyTimestampMixin, Base):
    """Permission Request model"""

    __tablename__ = "permission_requests"
    __table_args__ = (
        Index("ix_permission_requests_created_by", "created_by"),
        Index(
            "ix_permission_requests_payload_meeting_id",
            literal_column("((payload ->> 'meeting_id'::text)::integer)"),
        ),
        Index(
            "ix_permission_requests_payload_old_meeting_id",
            literal_column("((payload ->> 'old_meeting_id'::text)::integer)"),
        ),
        Index(
            "ix_permission_requests_payload_homework_id",
            literal_column("((payload ->> 'homework_id'::text)::integer)"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category: Mapped[RequestCategory] = mapped_column(String(100), index=True)
    note: Mapped[str] = mapped_column(String(500))

    # Pydantic Typed Payload (Single Source of Truth, 100% Type-Safe)
    payload: Mapped[PermissionPayloadUnion] = mapped_column(
        PydanticPayloadType, nullable=False
    )

    # Relationships
    creator: Mapped["UserModel | None"] = relationship(
        foreign_keys="PermissionRequest.created_by",
    )
    updater: Mapped["UserModel | None"] = relationship(
        foreign_keys="PermissionRequest.updated_by",
    )

    @validates("payload")
    def validate_payload(self, key: str, value: object) -> PermissionPayloadUnion:
        if isinstance(value, BasePermissionPayload):
            return value
        if isinstance(value, dict):
            normalized = _normalize_payload_dict(value)
            return PydanticPayloadType._adapter.validate_python(normalized)
        raise ValueError(f"Invalid permission request payload: {value}")

    def to_entity(self) -> PermissionRequestEntity:
        if self.created_by is None:
            raise ValueError("permission request missing created_by")

        creator_ref = None
        if "creator" in self.__dict__ and self.creator:
            creator_ref = UserRef(
                id=self.creator.id,
                name=self.creator.name,
                avatar_url=self.creator.avatar_url,
            )

        updater_ref = None
        if "updater" in self.__dict__ and self.updater:
            updater_ref = UserRef(
                id=self.updater.id,
                name=self.updater.name,
                avatar_url=self.updater.avatar_url,
            )

        return PermissionRequestEntity(
            id=self.id,
            created_by=self.created_by,
            updated_by=self.updated_by,
            note=self.note,
            payload=self.payload,
            created_at=self.created_at,
            updated_at=self.updated_at,
            creator=creator_ref,
            updater=updater_ref,
            is_deleted=bool(self.is_deleted),
        )

    @classmethod
    def from_entity(cls, entity: PermissionRequestEntity) -> "PermissionRequest":
        """Convert PermissionRequest domain entity to ORM model"""
        return cls(
            id=entity.id,
            category=entity.category,
            note=entity.note,
            payload=entity.payload,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            is_deleted=entity.is_deleted,
        )
