"""Use Case to retrieve role-adaptive quick prompt suggestions."""

from app.chatbot.schemas import QuickPromptItem
from app.core.permissions import (
    HomeworkPermission,
    MeetingPermission,
    ViolationPermission,
)
from app.core.principal import AuthPrincipal


class GetQuickPromptsUseCase:
    """Provides personalized prompt suggestions based on user permissions."""

    def execute(self, user: AuthPrincipal) -> list[QuickPromptItem]:
        prompts = [
            QuickPromptItem(
                label="Vi phạm gần đây",
                prompt="Tại sao gần đây tôi bị ghi nhận vi phạm?",
                category="personal",
            ),
            QuickPromptItem(
                label="Quy định điểm danh",
                prompt="Quy định giờ giấc điểm danh và đi trễ được tính như thế nào?",
                category="personal",
            ),
            QuickPromptItem(
                label="Thời hạn nộp bài",
                prompt="Quy định về thời hạn nộp bài tập và mức phạt nộp trễ?",
                category="personal",
            ),
            QuickPromptItem(
                label="Thủ tục xin phép",
                prompt="Tôi cần xin phép vắng họp trước bao lâu để không bị phạt?",
                category="personal",
            ),
        ]

        # Add administrative prompts if user has management permissions
        perms = user.permissions or []
        if ViolationPermission.READ in perms:
            prompts.append(
                QuickPromptItem(
                    label="Tổng hợp vi phạm tuần",
                    prompt="Tổng hợp tình hình vi phạm của toàn CLB trong 7 ngày qua",
                    category="administrative",
                )
            )
            prompts.append(
                QuickPromptItem(
                    label="Thành viên vi phạm nhiều",
                    prompt="Liệt kê danh sách các thành viên có từ 3 vi phạm trở lên trong tháng này",
                    category="administrative",
                )
            )
        if HomeworkPermission.READ in perms:
            prompts.append(
                QuickPromptItem(
                    label="Bài tập chưa nộp",
                    prompt="Bài tập mới nhất hiện còn những thành viên nào chưa nộp?",
                    category="administrative",
                )
            )
        if MeetingPermission.READ in perms:
            prompts.append(
                QuickPromptItem(
                    label="Vắng họp không phép",
                    prompt="Buổi họp gần nhất có những thành viên nào vắng mặt không phép?",
                    category="administrative",
                )
            )

        return prompts
