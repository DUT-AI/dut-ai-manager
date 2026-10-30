"""
Permission Request ORM Model — SQLAlchemy 2.0, infrastructure layer.
"""

from typing import TYPE_CHECKING

from sqlalchemy import JSON, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.permission_request.domain.entity import (
    PermissionRequest as PermissionRequestEntity,
)
from app.permission_request.domain.payloads import (
    AbsencePayload,
    ChangeMeetingPayload,
    LatePayload,
    OtherPayload,
    PermissionPayloadUnion,
    PostponePayload,
)
from app.permission_request.domain.value_objects import RequestCategory
from app.shared.domain.value_objects import UserRef
from app.shared.infrastructure.base_model import Base, SQLAlchemyTimestampMixin
from app.utils.parsers import parse_datetime, parse_int

if TYPE_CHECKING:
    from app.user.infrastructure.model import UserModel


class PermissionRequest(SQLAlchemyTimestampMixin, Base):
    """Permission Request model"""

    __tablename__ = "permission_requests"
    __table_args__ = (Index("ix_permission_requests_created_by", "created_by"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category: Mapped[RequestCategory] = mapped_column(String(100), index=True)
    note: Mapped[str] = mapped_column(String(500))

    # JSON Payload for Generic Strategy Pattern (Single Source of Truth)
    payload: Mapped[dict[str, object]] = mapped_column(
        JSON, default=dict, server_default="{}", nullable=False
    )

    # Relationships
    creator: Mapped["UserModel | None"] = relationship(
        foreign_keys="PermissionRequest.created_by",
    )
    updater: Mapped["UserModel | None"] = relationship(
        foreign_keys="PermissionRequest.updated_by",
    )

    def _build_typed_payload(self) -> PermissionPayloadUnion:
        raw_payload = dict(self.payload) if self.payload else {}
        match self.category:
            case RequestCategory.ABSENCE:
                return AbsencePayload(
                    meeting_id=parse_int(raw_payload.get("meeting_id"))
                )

            case RequestCategory.LATE:
                return LatePayload(
                    meeting_id=parse_int(raw_payload.get("meeting_id")),
                    start_time=parse_datetime(raw_payload.get("start_time")),
                )

            case RequestCategory.POSTPONE:
                return PostponePayload(
                    homework_id=parse_int(raw_payload.get("homework_id")),
                    start_time=parse_datetime(raw_payload.get("start_time")),
                )

            case RequestCategory.CHANGE_MEETING:
                return ChangeMeetingPayload(
                    meeting_id=parse_int(raw_payload.get("meeting_id")),
                    old_meeting_id=parse_int(raw_payload.get("old_meeting_id")),
                    start_time=parse_datetime(raw_payload.get("start_time")),
                )

            case _:
                return OtherPayload()

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

        typed_payload = self._build_typed_payload()

        return PermissionRequestEntity(
            id=self.id,
            user_id=self.created_by,
            created_by=self.created_by,
            updated_by=self.updated_by,
            note=self.note,
            payload=typed_payload,
            created_at=self.created_at,
            updated_at=self.updated_at,
            creator=creator_ref,
            updater=updater_ref,
        )

    @classmethod
    def from_entity(cls, entity: PermissionRequestEntity) -> "PermissionRequest":
        """Convert PermissionRequest domain entity to ORM model"""
        creator_id = (
            entity.created_by if entity.created_by is not None else entity.user_id
        )
        return cls(
            id=entity.id,
            category=entity.category,
            note=entity.note,
            payload=entity.payload.model_dump(mode="json"),
            created_by=creator_id,
            updated_by=entity.updated_by,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            is_deleted=entity.is_deleted,
        )
