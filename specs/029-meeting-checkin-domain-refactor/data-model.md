# Data Model: Meeting Check-In Domain Entity

## 1. Domain Entity Contract

```python
class MeetingParticipant(BaseEntity):
    id: int | None = None
    meeting_id: int | None = None
    user_id: int
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None
    status: ParticipantStatus = ParticipantStatus.NOT_JOINED
    link_image: str | None = None
    client_event_id: str | None = None
    user: UserRef | None = None

    def record_check_in(
        self,
        check_in_time: datetime,
        meeting_start_time: datetime,
        image_url: str | None = None,
        client_event_id: str | None = None,
    ) -> tuple[bool, str, bool]:
        """
        Ghi nhận điểm danh cho thành viên theo chuẩn DDD Invariants.
        
        Args:
            check_in_time: Mốc thời gian điểm danh (Timezone-Aware UTC)
            meeting_start_time: Mốc thời gian bắt đầu buổi họp (Timezone-Aware UTC)
            image_url: URL ảnh chụp minh chứng (tùy chọn)
            client_event_id: Idempotency Key từ client (tùy chọn)
            
        Returns:
            tuple[bool, str, bool]: (is_success, message, is_late)
        """
        ...
```

## 2. ORM Mapping Synchronization

Bảng `meeting_participants`:
```python
class MeetingParticipant(SQLAlchemyTimestampMixin, Base):
    __tablename__ = "meeting_participants"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    check_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    check_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    status: Mapped[ParticipantStatus] = mapped_column(String(50), default=ParticipantStatus.NOT_JOINED)
    link_image: Mapped[str | None] = mapped_column(String(500), default=None)
    client_event_id: Mapped[str | None] = mapped_column(String(255), default=None, index=True)
```

Mapper trong `ParticipantRepository`:
- `save(participant)`: Lưu đầy đủ `status`, `check_in_at`, `check_out_at`, `link_image`, `client_event_id`.
