from datetime import UTC, datetime, timedelta

from app.meeting.domain.entity import Meeting, MeetingParticipant
from app.meeting.domain.value_objects import EvaluationType, ParticipantStatus
from app.meeting.infrastructure.repository import (
    MeetingEvaluationRepository,
    MeetingOverallEvaluationRepository,
    MeetingRepository,
)
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
        seven_days_ago = now - timedelta(days=7)
        twenty_four_hours_ago = now - timedelta(hours=24)

        meetings = self.meeting_repo.get_meetings_for_evaluation_deadline_check(
            start_bound=seven_days_ago,
            end_bound=twenty_four_hours_ago,
        )

        trainee_violations = 0
        trainer_violations = 0

        for meeting in meetings:
            if not meeting.id:
                continue

            time_str = self._format_meeting_time(meeting)
            evals = self.evaluation_repo.get_evaluations_by_meeting(meeting.id)

            trainee_violations += self._check_trainees(meeting, evals, now, time_str)
            trainer_violations += self._check_trainer(meeting, now, time_str)

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
        joined_participants = [p for p in meeting.participants if self._is_joined(p)]
        reviewers = {
            e.reviewer_id
            for e in evals
            if e.evaluation_type == EvaluationType.TRAINEE_TO_TRAINER
        }

        created = 0
        for p in joined_participants:
            if p.user_id not in reviewers:
                reason = (
                    f"Chưa hoàn thành đánh giá Trainer cho buổi học "
                    f"'{meeting.title}'{time_str} trong vòng 24h"
                )
                if not self.violation_repo.exists_by_user_and_reason(p.user_id, reason):
                    v = Violation.create_system_violation(
                        user_id=p.user_id, reason=reason, date=now
                    )
                    self.violation_repo.save(v)
                    created += 1
        return created

    def _check_trainer(self, meeting: Meeting, now: datetime, time_str: str) -> int:
        trainer_id = meeting.created_by
        if not trainer_id or not meeting.id:
            return 0

        if not self.overall_eval_repo.exists_for_meeting(meeting.id):
            reason = (
                f"Trainer chưa hoàn tất đánh giá tổng thể buổi học "
                f"'{meeting.title}'{time_str} trong vòng 24h"
            )
            if not self.violation_repo.exists_by_user_and_reason(trainer_id, reason):
                v = Violation.create_system_violation(
                    user_id=trainer_id, reason=reason, date=now
                )
                self.violation_repo.save(v)
                return 1
        return 0

    @staticmethod
    def _is_joined(p: MeetingParticipant) -> bool:
        return p.status in (
            ParticipantStatus.JOINED,
            ParticipantStatus.LATE_EXCUSED,
            ParticipantStatus.LATE_UNEXCUSED,
            ParticipantStatus.COMPLETED,
        )
