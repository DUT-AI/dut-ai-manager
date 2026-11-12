"""Parameterized Unified Entity Explorer Tool.

Enables the LLM to inspect multi-domain entities (meetings, evaluations,
homeworks, permission requests, violations) with strict IDOR protection.
"""

from datetime import UTC, datetime
from typing import Any
from sqlalchemy import DateTime as SaDateTime, select
from sqlalchemy.orm import Session

from app.chatbot.infrastructure.tools.base import BaseChatbotTool
from app.core.principal import AuthPrincipal
from app.homework.infrastructure.model import (
    HomeworkAssigneeModel,
    HomeworkModel,
    HomeworkSubmissionModel,
)
from app.meeting.infrastructure.model import (
    Meeting,
    MeetingEvaluation,
    MeetingOverallEvaluation,
    MeetingParticipant,
)
from app.permission_request.infrastructure.model import PermissionRequest
from app.violation.infrastructure.model import ViolationModel


class InspectEntityRecordsTool(BaseChatbotTool):
    """Unified exploratory tool for cross-referencing multi-domain entities."""

    name = "inspect_entity_records"
    description = (
        "CÔNG CỤ TRA CỨU ĐA CHIỀU CHUYÊN SÂU: Cho phép Agent tự do tra cứu hồ sơ gốc "
        "về các buổi học (meetings, trạng thái điểm danh, hạn chót đánh giá 24h, lịch sử đánh giá tổng thể và cá nhân), "
        "bài tập (homeworks, deadline cá nhân, lần nộp bài, điểm số), "
        "đơn xin phép (permission_requests, đơn vắng họp, đơn trễ, hoãn bài tập), "
        "hoặc vi phạm cá nhân (violations) để đối soát, so sánh mốc thời gian và giải thích chi tiết cho thành viên.\n"
        "ĐẶC BIỆT LƯU Ý KHI NGƯỜI DÙNG THẮC MẮC VỀ VI PHẠM ĐÁNH GIÁ/BUỔI HỌP/BÀI TẬP: "
        "Bạn PHẢI gọi tool này với entity_type='meeting' (nếu hỏi về buổi họp hoặc đánh giá buổi học) "
        "hoặc entity_type='homework' (nếu hỏi về nộp bài) để lấy chi tiết mốc thời gian thực tế, deadline và tình trạng nộp, "
        "tuyệt đối KHÔNG CHỈ tra cứu entity_type='violation'."
    )
    parameters = {
        "type": "object",
        "properties": {
            "entity_type": {
                "type": "string",
                "enum": ["meeting", "homework", "permission_request", "violation"],
                "description": "Loại thực thể cần tra cứu chi tiết.",
            },
            "keyword": {
                "type": "string",
                "description": "Từ khóa tìm kiếm theo tên, tiêu đề buổi họp, bài tập hoặc lý do (ví dụ: 'Sinh hoạt gen 1', 'FastAPI').",
            },
            "date": {
                "type": "string",
                "description": "Ngày diễn ra hoặc ngày liên quan dạng YYYY-MM-DD (ví dụ: '2026-10-29').",
            },
            "limit": {
                "type": "integer",
                "description": "Số lượng bản ghi tối đa (mặc định 5).",
                "default": 5,
            },
        },
        "required": ["entity_type"],
    }
    required_permissions = []  # Open to all authenticated members (Zero IDOR enforced)

    def execute(
        self, session: Session, args: dict[str, Any], user: AuthPrincipal
    ) -> dict[str, Any]:
        entity_type = args.get("entity_type", "").lower()
        keyword = args.get("keyword")
        date_str = args.get("date")
        limit = min(int(args.get("limit", 5)), 20)

        match entity_type:
            case "meeting":
                return self._inspect_meetings(session, user.user_id, keyword, date_str, limit)
            case "homework":
                return self._inspect_homeworks(session, user.user_id, keyword, limit)
            case "permission_request":
                return self._inspect_permissions(session, user.user_id, keyword, limit)
            case "violation":
                return self._inspect_violations(session, user.user_id, keyword, limit)
            case _:
                return {"error": f"Loại thực thể '{entity_type}' không được hỗ trợ."}

    def _inspect_meetings(
        self, session: Session, user_id: int, keyword: str | None, date_str: str | None, limit: int
    ) -> dict[str, Any]:
        """Fetch meeting details, check-in status, evaluation deadline, and user evaluations."""
        stmt = (
            select(Meeting, MeetingParticipant)
            .join(MeetingParticipant, MeetingParticipant.meeting_id == Meeting.id)
            .where(MeetingParticipant.user_id == user_id)
            .order_by(Meeting.start_time.desc())
        )
        if keyword:
            stmt = stmt.where(Meeting.title.ilike(f"%{keyword}%"))
        if date_str:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                start_dt = datetime.combine(target_date, datetime.min.time(), tzinfo=UTC)
                end_dt = datetime.combine(target_date, datetime.max.time(), tzinfo=UTC)
                stmt = stmt.where(Meeting.start_time.between(start_dt, end_dt))
            except ValueError:
                pass

        results = session.execute(stmt.limit(limit)).all()
        if not results:
            return {"message": "Không tìm thấy buổi học/cuộc họp phù hợp với thông tin cung cấp."}

        records = []
        for meeting, participant in results:
            # Tra cứu đánh giá 2 chiều của user trong meeting này
            eval_stmt = select(MeetingEvaluation).where(
                MeetingEvaluation.meeting_id == meeting.id,
                MeetingEvaluation.reviewer_id == user_id,
            )
            evals = list(session.scalars(eval_stmt).all())

            # Tra cứu đánh giá tổng thể (Overall Evaluation) do Trainer thực hiện
            overall_stmt = select(MeetingOverallEvaluation).where(
                MeetingOverallEvaluation.meeting_id == meeting.id
            )
            overall = session.scalars(overall_stmt).first()

            records.append({
                "meeting_id": meeting.id,
                "title": meeting.title,
                "start_time": meeting.start_time.strftime("%d/%m/%Y %H:%M") if meeting.start_time else None,
                "end_time": meeting.end_time.strftime("%d/%m/%Y %H:%M") if meeting.end_time else None,
                "my_role": participant.role,
                "attendance_status": participant.status.value if hasattr(participant.status, "value") else str(participant.status),
                "check_in_at": participant.check_in_at.strftime("%d/%m/%Y %H:%M") if participant.check_in_at else None,
                "enable_evaluation": meeting.enable_evaluation,
                "evaluation_deadline": meeting.evaluation_deadline.strftime("%d/%m/%Y %H:%M") if meeting.evaluation_deadline else "24 giờ sau khi kết thúc buổi học",
                "my_peer_evaluations_count": len(evals),
                "overall_evaluation": {
                    "is_completed": overall is not None,
                    "trainer_id": overall.trainer_id if overall else None,
                    "submitted_at": overall.created_at.strftime("%d/%m/%Y %H:%M") if overall and overall.created_at else None,
                },
            })

        return {"entity": "meeting", "total_found": len(records), "records": records}

    def _inspect_homeworks(
        self, session: Session, user_id: int, keyword: str | None, limit: int
    ) -> dict[str, Any]:
        """Fetch homework deadlines, user submissions, scores, and status."""
        stmt = (
            select(HomeworkModel, HomeworkAssigneeModel)
            .join(HomeworkAssigneeModel, HomeworkAssigneeModel.homework_id == HomeworkModel.id)
            .where(HomeworkAssigneeModel.user_id == user_id)
            .order_by(HomeworkAssigneeModel.deadline.desc())
        )
        if keyword:
            stmt = stmt.where(HomeworkModel.title.ilike(f"%{keyword}%"))

        results = session.execute(stmt.limit(limit)).all()
        if not results:
            return {"message": "Không tìm thấy bài tập nào được giao phù hợp với từ khóa."}

        records = []
        for hw, assignee in results:
            # Tra cứu các lần nộp bài của user
            sub_stmt = (
                select(HomeworkSubmissionModel)
                .where(
                    HomeworkSubmissionModel.homework_id == hw.id,
                    HomeworkSubmissionModel.user_id == user_id,
                )
                .order_by(HomeworkSubmissionModel.submitted_at.desc())
            )
            submissions = list(session.scalars(sub_stmt).all())

            is_submitted = len(submissions) > 0
            best_score = max([s.score for s in submissions if s.score is not None], default=None)
            passed = any(s.is_passed for s in submissions)

            records.append({
                "homework_id": hw.id,
                "title": hw.title,
                "individual_deadline": assignee.deadline.strftime("%d/%m/%Y %H:%M") if assignee.deadline else None,
                "is_submitted": is_submitted,
                "submission_count": len(submissions),
                "is_passed": passed,
                "score": best_score,
                "submissions": [
                    {
                        "submitted_at": s.submitted_at.strftime("%d/%m/%Y %H:%M") if s.submitted_at else None,
                        "type": s.submission_type,
                        "score": s.score,
                        "is_passed": s.is_passed,
                    }
                    for s in submissions[:3]
                ],
            })

        return {"entity": "homework", "total_found": len(records), "records": records}

    def _inspect_permissions(
        self, session: Session, user_id: int, keyword: str | None, limit: int
    ) -> dict[str, Any]:
        """Fetch permission requests created by the calling user."""
        stmt = (
            select(PermissionRequest)
            .where(
                PermissionRequest.created_by == user_id,
                PermissionRequest.is_deleted.is_(False),
            )
            .order_by(PermissionRequest.created_at.desc())
        )
        if keyword:
            stmt = stmt.where(PermissionRequest.note.ilike(f"%{keyword}%"))

        requests = session.scalars(stmt.limit(limit)).all()
        records = []
        for pr in requests:
            records.append({
                "id": pr.id,
                "category": pr.category.value if hasattr(pr.category, "value") else str(pr.category),
                "note": pr.note,
                "created_at": pr.created_at.strftime("%d/%m/%Y %H:%M") if pr.created_at else None,
                "payload": pr.payload.model_dump() if hasattr(pr.payload, "model_dump") else str(pr.payload),
            })

        return {"entity": "permission_request", "total_found": len(records), "records": records}

    def _inspect_violations(
        self, session: Session, user_id: int, keyword: str | None, limit: int
    ) -> dict[str, Any]:
        """Fetch personal violation records matching keywords."""
        stmt = (
            select(ViolationModel)
            .where(
                ViolationModel.user_id == user_id,
                ViolationModel.is_deleted.is_(False),
            )
            .order_by(ViolationModel.date.desc())
        )
        if keyword:
            stmt = stmt.where(ViolationModel.reason.ilike(f"%{keyword}%"))

        violations = session.scalars(stmt.limit(limit)).all()
        records = [
            {
                "id": v.id,
                "date": v.date.strftime("%d/%m/%Y %H:%M") if v.date else None,
                "reason": v.reason,
            }
            for v in violations
        ]
        return {"entity": "violation", "total_found": len(records), "records": records}
