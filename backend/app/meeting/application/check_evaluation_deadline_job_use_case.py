from datetime import UTC, datetime, timedelta

from app.meeting.domain.constants import (
    MEETING_EVALUATION_DEADLINE_HOURS,
    MEETING_EVALUATION_SCAN_WINDOW_DAYS,
)
from app.meeting.domain.entity import Meeting, MeetingParticipant
from app.meeting.domain.value_objects import EvaluationType, ParticipantStatus
from app.meeting.infrastructure.repository import (
    MeetingEvaluationRepository,
    MeetingOverallEvaluationRepository,
    MeetingRepository,
)
from app.shared.domain.datetime_types import ensure_utc
from app.violation.domain.entity import Violation
from app.violation.infrastructure.repository import ViolationRepository


class CheckEvaluationDeadlineJobUseCase:
    """Tác vụ định kỳ kiểm tra các buổi học kết thúc quá 24h và tạo vi phạm."""

    def __init__(
        self,
        meeting_repo: MeetingRepository,
        evaluation_repo: MeetingEvaluationRepository,
        overall_eval_repo: MeetingOverallEvaluationRepository,
        violation_repo: ViolationRepository,
    ):
        self.meeting_repo = meeting_repo
        self.evaluation_repo = evaluation_repo
        self.overall_eval_repo = overall_eval_repo
        self.violation_repo = violation_repo

    async def execute(self) -> dict:
        now = datetime.now(UTC)
        start_bound = now - timedelta(days=MEETING_EVALUATION_SCAN_WINDOW_DAYS)
        end_bound = now - timedelta(hours=MEETING_EVALUATION_DEADLINE_HOURS)

        meetings = self.meeting_repo.get_meetings_for_evaluation_deadline_check(
            start_bound=start_bound,
            end_bound=end_bound,
        )

        trainee_violations = 0
        trainer_violations = 0

        for meeting in meetings:
            if not meeting.id:
                continue

            time_str = self._format_meeting_time(meeting)
            evals = self.evaluation_repo.get_evaluations_by_meeting(meeting.id)

            trainee_violations += self._check_trainees(meeting, evals, now, time_str)
            trainer_violations += self._check_trainers(meeting, now, time_str)

        return {
            "meetings_scanned": len(meetings),
            "trainee_violations_created": trainee_violations,
            "trainer_violations_created": trainer_violations,
        }

    def _format_meeting_time(self, meeting: Meeting) -> str:
        if meeting.start_time and meeting.end_time:
            st = meeting.start_time.strftime("%H:%M")
            et = meeting.end_time.strftime("%H:%M %d/%m/%Y")
            return f" ({st} - {et})"
        if meeting.start_time:
            return f" ({meeting.start_time.strftime('%H:%M %d/%m/%Y')})"
        return ""

    def _check_trainees(
        self, meeting: Meeting, evals: list, now: datetime, time_str: str
    ) -> int:
        # Nếu buổi học không có Trainer nào thì Trainee không cần đánh giá Trainer
        if not meeting.trainers:
            return 0

        joined_participants = [
            p
            for p in meeting.participants
            if self._is_joined(p) and not meeting.is_trainer(p.user_id)
        ]
        reviewers = {
            e.reviewer_id
            for e in evals
            if e.evaluation_type == EvaluationType.TRAINEE_TO_TRAINER
        }

        occurrence_date = (
            ensure_utc(meeting.end_time) + timedelta(hours=MEETING_EVALUATION_DEADLINE_HOURS)
            if meeting.end_time
            else now
        )

        created = 0
        for p in joined_participants:
            if p.user_id not in reviewers:
                reason = (
                    f"Chưa hoàn thành đánh giá Trainer cho buổi học "
                    f"'{meeting.title}'{time_str} trong vòng 24h"
                )
                if not self.violation_repo.exists_by_user_and_reason(p.user_id, reason):
                    v = Violation.create_system_violation(
                        user_id=p.user_id, reason=reason, date=occurrence_date
                    )
                    self.violation_repo.save(v)
                    created += 1
        return created

    def _check_trainers(self, meeting: Meeting, now: datetime, time_str: str) -> int:
        if not meeting.id or not meeting.trainers:
            return 0

        occurrence_date = (
            ensure_utc(meeting.end_time) + timedelta(hours=MEETING_EVALUATION_DEADLINE_HOURS)
            if meeting.end_time
            else now
        )

        created = 0
        if not self.overall_eval_repo.exists_for_meeting(meeting.id):
            for trainer in meeting.trainers:
                trainer_id = trainer.user_id
                reason = (
                    f"Trainer chưa hoàn tất đánh giá tổng thể buổi học "
                    f"'{meeting.title}'{time_str} trong vòng 24h"
                )
                if not self.violation_repo.exists_by_user_and_reason(
                    trainer_id, reason
                ):
                    v = Violation.create_system_violation(
                        user_id=trainer_id, reason=reason, date=occurrence_date
                    )
                    self.violation_repo.save(v)
                    created += 1
        return created

    @staticmethod
    def _is_joined(p: MeetingParticipant) -> bool:
        return p.status in (
            ParticipantStatus.JOINED,
            ParticipantStatus.LATE_EXCUSED,
            ParticipantStatus.LATE_UNEXCUSED,
            ParticipantStatus.COMPLETED,
        )
