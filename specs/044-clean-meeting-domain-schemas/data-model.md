# Data Model: Chuẩn Hóa Type Contracts & Domain Mapping

## 1. Domain Entities & Value Objects (Source of Truth)

### Aggregate Root: `Meeting` (`backend/app/meeting/domain/meeting.py`)
```python
class Meeting(BaseEntity):
    title: str
    start_time: datetime
    end_time: datetime
    content: str | None = None
    require_check_in: bool = True
    enable_evaluation: bool = False
    participants: list[MeetingParticipant] = Field(default_factory=list)
    creator: UserRef | None = None

    @property
    def trainers(self) -> list[MeetingParticipant]:
        """Type-safe trainers filtering, no getattr()"""
        return [
            p for p in self.participants
            if not p.is_deleted and p.role == ParticipantRole.TRAINER
        ]

    @property
    def trainees(self) -> list[MeetingParticipant]:
        """Type-safe trainees filtering, no getattr()"""
        return [
            p for p in self.participants
            if not p.is_deleted and p.role == ParticipantRole.TRAINEE
        ]
```

### Child Entity: `MeetingParticipant` (`backend/app/meeting/domain/participant.py`)
```python
class MeetingParticipant(BaseEntity):
    user_id: int
    meeting_id: int | None = None
    role: ParticipantRole = ParticipantRole.TRAINEE
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None
    status: ParticipantStatus = ParticipantStatus.NOT_JOINED
    link_image: str | None = None
    client_event_id: str | None = None
    user: UserRef | None = None  # Snapshot Value Object
```

### Domain Evaluation Entities (`backend/app/meeting/domain/evaluation.py`)
```python
class EvaluationScoreItem(BaseModel):
    criteria_code: str
    score: int = Field(ge=1, le=5)

class MeetingOverallEvaluation(BaseEntity):
    meeting_id: int
    trainer_id: int
    scores: list[EvaluationScoreItem] = Field(default_factory=list)
    average_score: float = 0.0
    general_feedback: str | None = None
    trainer: UserRef | None = None

class MeetingEvaluation(BaseEntity):
    meeting_id: int
    reviewer_id: int
    target_user_id: int
    evaluation_type: EvaluationType
    is_anonymous: bool = False
    scores: list[EvaluationScoreItem] = Field(default_factory=list)
    average_score: float = 0.0
    feedback_text: str | None = None
    reviewer: UserRef | None = None
    target_user: UserRef | None = None
```

---

## 2. Presentation DTOs & Mapping Rules

### `MeetingResponse` & `MeetingDetailResponse` (`meeting_schemas.py`)
```python
class MeetingResponse(BaseModel):
    id: int
    title: str
    content: str | None = None
    start_time: datetime
    end_time: datetime
    require_check_in: bool
    enable_evaluation: bool = False
    evaluation_deadline: datetime | None = None
    created_by: int | None = None
    trainers: list[UserRefDto] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, m: DomainMeeting) -> "MeetingResponse":
        trainers_dto: list[UserRefDto] = []
        for t in m.trainers:
            if t.user is not None:
                trainers_dto.append(
                    UserRefDto(
                        id=t.user.id,
                        name=t.user.name or f"Trainer #{t.user_id}",
                        avatar_url=t.user.avatar_url,
                    )
                )
            else:
                trainers_dto.append(
                    UserRefDto(
                        id=t.user_id,
                        name=f"Trainer #{t.user_id}",
                        avatar_url=None,
                    )
                )

        return cls(
            id=m.id or 0,
            title=m.title,
            content=m.content,
            start_time=m.start_time,
            end_time=m.end_time,
            require_check_in=m.require_check_in,
            enable_evaluation=bool(m.enable_evaluation),
            evaluation_deadline=m.evaluation_deadline,
            created_by=m.created_by,
            trainers=trainers_dto,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
```

```python
class MeetingDetailResponse(BaseModel):
    id: int
    title: str
    content: str | None = None
    start_time: datetime
    end_time: datetime
    require_check_in: bool
    enable_evaluation: bool = False
    evaluation_deadline: datetime | None = None
    created_by: int | None = None
    trainers: list[ParticipantResponse] = Field(default_factory=list)
    trainees: list[ParticipantResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, m: DomainMeeting) -> "MeetingDetailResponse":
        now = datetime.now(UTC)
        end_time_utc = (
            m.end_time
            if m.end_time.tzinfo is not None
            else m.end_time.replace(tzinfo=ZoneInfo("Asia/Ho_Chi_Minh")).astimezone(UTC)
        )
        is_ended = now > end_time_utc

        trainers: list[ParticipantResponse] = []
        trainees: list[ParticipantResponse] = []

        for p in m.participants:
            if p.id is None or p.is_deleted:
                continue

            check_out_at = p.check_out_at
            status = p.status

            if is_ended:
                if p.check_in_at and not check_out_at:
                    check_out_at = m.end_time
                    if status in (
                        ParticipantStatus.JOINED,
                        ParticipantStatus.LATE_EXCUSED,
                        ParticipantStatus.LATE_UNEXCUSED,
                    ):
                        status = ParticipantStatus.COMPLETED
                elif not p.check_in_at and status == ParticipantStatus.NOT_JOINED:
                    status = ParticipantStatus.ABSENT_UNEXCUSED

            p_user = p.user
            user_name = p_user.name if p_user and p_user.name else f"User #{p.user_id}"
            user_avatar = p_user.avatar_url if p_user else None

            p_dto = ParticipantResponse(
                id=p.id,
                user_id=p.user_id,
                role=p.role,
                user_name=user_name,
                user_avatar_url=user_avatar,
                check_in_at=p.check_in_at,
                check_out_at=check_out_at,
                status=status,
                link_image=p.link_image,
            )

            if p.role == ParticipantRole.TRAINER:
                trainers.append(p_dto)
            else:
                trainees.append(p_dto)

        return cls(
            id=m.id or 0,
            title=m.title,
            content=m.content,
            start_time=m.start_time,
            end_time=m.end_time,
            require_check_in=m.require_check_in,
            enable_evaluation=bool(m.enable_evaluation),
            evaluation_deadline=m.evaluation_deadline,
            created_by=m.created_by,
            trainers=trainers,
            trainees=trainees,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
```

### `ParticipantResponse` (`participant_schemas.py`)
```python
class ParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    role: ParticipantRole = ParticipantRole.TRAINEE
    user_name: str
    user_avatar_url: str | None = None
    check_in_at: UtcDateTime | None = None
    check_out_at: UtcDateTime | None = None
    status: ParticipantStatus
    link_image: str | None = None

    @classmethod
    def from_domain(cls, p: MeetingParticipant) -> "ParticipantResponse":
        if p.id is None:
            raise ValueError("Participant thiếu id")
        user_name = p.user.name if p.user and p.user.name else f"User #{p.user_id}"
        user_avatar = p.user.avatar_url if p.user else None
        return cls(
            id=p.id,
            user_id=p.user_id,
            role=p.role,
            user_name=user_name,
            user_avatar_url=user_avatar,
            check_in_at=p.check_in_at,
            check_out_at=p.check_out_at,
            status=p.status,
            link_image=p.link_image,
        )
```
