from datetime import timedelta

from app.meeting.domain.value_objects import EvaluationType, ParticipantStatus
from app.meeting.infrastructure.repository import (
    MeetingEvaluationRepository,
    MeetingRepository,
)
from app.utils.datetime import get_current_utc7_time
from app.violation.domain.entity import Violation
from app.violation.infrastructure.repository import ViolationRepository


class CheckEvaluationDeadlineJobUseCase:
    """Tác vụ định kỳ kiểm tra các buổi học kết thúc quá 24h và tự động tạo vi phạm cho người chưa hoàn thành đánh giá."""

    def __init__(
        self,
        meeting_repo: MeetingRepository,
        evaluation_repo: MeetingEvaluationRepository,
        violation_repo: ViolationRepository,
    ):
        self.meeting_repo = meeting_repo
        self.evaluation_repo = evaluation_repo
        self.violation_repo = violation_repo

    async def execute(self) -> dict:
        now = get_current_utc7_time()
        # Tìm các meeting đã kết thúc, có bật evaluation
        # Lấy các buổi họp trong vòng 7 ngày qua để tránh quét toàn bộ lịch sử
        from sqlalchemy import select

        from app.meeting.infrastructure.model import Meeting as ORMMeeting

        seven_days_ago = now - timedelta(days=7)
        twenty_four_hours_ago = now - timedelta(hours=24)

        stmt = select(ORMMeeting).where(
            ORMMeeting.is_deleted.is_(False),
            ORMMeeting.enable_evaluation.is_(True),
            ORMMeeting.end_time <= twenty_four_hours_ago,
            ORMMeeting.end_time >= seven_days_ago,
        )
        orm_meetings = self.meeting_repo.session.scalars(stmt).all()
        meetings = [self.meeting_repo._to_domain(m) for m in orm_meetings]

        trainee_violations_created = 0
        trainer_violations_created = 0

        for meeting in meetings:
            if not meeting.id:
                continue

            meeting_evals = self.evaluation_repo.get_evaluations_by_meeting(meeting.id)

            # 1. Kiểm tra Trainee: Những ai có tham gia (JOINED / COMPLETED) nhưng chưa đánh giá Trainer
            joined_participants = [
                p
                for p in meeting.participants
                if p.status
                in (
                    ParticipantStatus.JOINED,
                    ParticipantStatus.LATE_EXCUSED,
                    ParticipantStatus.LATE_UNEXCUSED,
                    ParticipantStatus.COMPLETED,
                )
            ]

            trainee_eval_reviewers = {
                e.reviewer_id
                for e in meeting_evals
                if e.evaluation_type == EvaluationType.TRAINEE_TO_TRAINER
            }

            for participant in joined_participants:
                if participant.user_id not in trainee_eval_reviewers:
                    reason = f"Chưa hoàn thành đánh giá Trainer cho buổi học '{meeting.title}' trong vòng 24h"
                    # Kiểm tra xem đã tạo vi phạm này chưa
                    existing_violation = self._has_existing_violation(
                        participant.user_id, reason
                    )
                    if not existing_violation:
                        v = Violation.create_system_violation(
                            user_id=participant.user_id,
                            reason=reason,
                            date=now,
                        )
                        self.violation_repo.save(v)
                        trainee_violations_created += 1

            # 2. Kiểm tra Trainer (người tạo meeting): Phải chấm đủ cho toàn bộ Trainee đã tham gia
            trainer_id = meeting.created_by
            if trainer_id:
                trainer_eval_targets = {
                    e.target_user_id
                    for e in meeting_evals
                    if e.evaluation_type == EvaluationType.TRAINER_TO_TRAINEE
                }
                unevaluated_trainees = [
                    p
                    for p in joined_participants
                    if p.user_id not in trainer_eval_targets
                ]

                if unevaluated_trainees:
                    reason = f"Trainer chưa hoàn tất đánh giá học viên cho buổi học '{meeting.title}' trong vòng 24h"
                    existing_violation = self._has_existing_violation(
                        trainer_id, reason
                    )
                    if not existing_violation:
                        v = Violation.create_system_violation(
                            user_id=trainer_id,
                            reason=reason,
                            date=now,
                        )
                        self.violation_repo.save(v)
                        trainer_violations_created += 1

        return {
            "meetings_scanned": len(meetings),
            "trainee_violations_created": trainee_violations_created,
            "trainer_violations_created": trainer_violations_created,
        }

    def _has_existing_violation(self, user_id: int, reason: str) -> bool:
        from sqlalchemy import select

        from app.violation.infrastructure.model import ViolationModel

        stmt = select(ViolationModel).where(
            ViolationModel.user_id == user_id,
            ViolationModel.reason == reason,
            ViolationModel.is_deleted.is_(False),
        )
        return self.violation_repo.session.scalars(stmt).first() is not None
