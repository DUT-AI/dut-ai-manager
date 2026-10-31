"""
Meeting Evaluation Task Scanner.
Scans meetings that have evaluation enabled, within evaluation window (ended, not expired),
and identifies participants who have not yet submitted their evaluation.
"""

from datetime import datetime, timedelta

from app.meeting.domain.value_objects import ParticipantStatus
from app.meeting.infrastructure.repository import (
    MeetingEvaluationRepository,
    MeetingOverallEvaluationRepository,
    MeetingRepository,
)
from app.reminder.application.scanners.base_scanner import (
    BaseTaskScanner,
    ScannedCandidateTask,
    calculate_matching_stages,
)
from app.reminder.domain.entity import TaskType


class MeetingEvaluationTaskScanner(BaseTaskScanner):
    def __init__(
        self,
        meeting_repo: MeetingRepository,
        evaluation_repo: MeetingEvaluationRepository,
        overall_eval_repo: MeetingOverallEvaluationRepository,
    ):
        self.meeting_repo = meeting_repo
        self.evaluation_repo = evaluation_repo
        self.overall_eval_repo = overall_eval_repo

    def scan_pending_tasks(self, now: datetime) -> list[ScannedCandidateTask]:
        candidates: list[ScannedCandidateTask] = []

        # Lấy các buổi họp gần đây (bắt đầu trong vòng 3 ngày qua)
        three_days_ago = now - timedelta(days=3)
        meetings = self.meeting_repo.get_all_with_participants(
            start_date=three_days_ago,
            limit=100,
        )

        for meeting in meetings:
            if not meeting.id or not meeting.enable_evaluation:
                continue

            deadline = meeting.evaluation_deadline
            if not deadline:
                continue

            # Buổi học phải đã kết thúc và chưa quá hạn đánh giá
            if not meeting.is_finished(now) or meeting.is_evaluation_expired(now):
                continue

            stages = calculate_matching_stages(deadline, now)
            if not stages:
                continue

            # 1. Nhắc nhở Trainer nộp đánh giá tổng thể buổi học
            if meeting.trainers:
                has_overall = self.overall_eval_repo.exists_for_meeting(meeting.id)
                if not has_overall:
                    for trainer in meeting.trainers:
                        candidates.append(
                            ScannedCandidateTask(
                                task_type=TaskType.MEETING_EVALUATION,
                                task_id=meeting.id,
                                task_title=f"Đánh giá tổng thể buổi học: {meeting.title}",
                                user_id=trainer.user_id,
                                deadline=deadline,
                                action_url=f"/dashboard/meetings/{meeting.id}/evaluate",
                                stages=stages,
                            )
                        )

            # 2. Nhắc nhở Trainee đã tham gia mà chưa đánh giá Trainer
            if meeting.trainers:
                valid_trainees = [
                    p
                    for p in meeting.participants
                    if not p.is_deleted
                    and not meeting.is_trainer(p.user_id)
                    and p.status
                    in (
                        ParticipantStatus.JOINED,
                        ParticipantStatus.COMPLETED,
                        ParticipantStatus.LATE_EXCUSED,
                        ParticipantStatus.LATE_UNEXCUSED,
                    )
                ]

                for p in valid_trainees:
                    evaluated_count = self.evaluation_repo.count_evaluations_by_reviewer(
                        meeting_id=meeting.id,
                        reviewer_id=p.user_id,
                    )
                    if evaluated_count == 0:
                        candidates.append(
                            ScannedCandidateTask(
                                task_type=TaskType.MEETING_EVALUATION,
                                task_id=meeting.id,
                                task_title=f"Đánh giá buổi học: {meeting.title}",
                                user_id=p.user_id,
                                deadline=deadline,
                                action_url=f"/dashboard/meetings/{meeting.id}/evaluate",
                                stages=stages,
                            )
                        )

        return candidates
