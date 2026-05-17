from dishka import AsyncContainer

from app.auth.account_notification_handler import AccountNotificationHandler
from app.auth.application.user_event_handler import UserAccountHandler
from app.auth.domain.events import AccountCreated, ForgotPasswordRequested
from app.homework.application.event_handlers import (
    HomeworkGradedNotificationHandler,
    HomeworkNotificationHandler,
)
from app.homework.domain.value_objects import (
    HomeworkAssigned,
    HomeworkGraded,
    HomeworkOverdueDetected,
)
from app.meeting.application.event_handlers import MeetingNotificationHandler
from app.meeting.application.sse_handler import MeetingSseHandler
from app.meeting.domain.events import (
    MeetingAbsenceDetected,
    MeetingCreated,
    MeetingUpdated,
    ParticipantCheckedIn,
    ParticipantCheckedOut,
)
from app.permission_request.application.event_handlers import (
    PermissionRequestNotificationHandler,
)
from app.permission_request.domain.events import PermissionRequestCreated
from app.shared.domain.event_bus import EventBus
from app.user.domain.events import UserCreated
from app.violation.application.event_handlers import AutomatedViolationHandler
from app.violation.domain.events import ViolationCreated
from app.violation.notification_handler import ViolationNotificationHandler
from app.violation.permission_handler import PermissionViolationHandler


async def bootstrap_events(container: AsyncContainer):
    """
    Register all domain event handlers using Dishka dependencies.
    We subscribe the handler TYPES. The EventBus will resolve instances
    from the current Request scope during execution.
    """

    # Auth Module
    EventBus.subscribe(UserCreated, UserAccountHandler)
    EventBus.subscribe(AccountCreated, AccountNotificationHandler)
    EventBus.subscribe(ForgotPasswordRequested, AccountNotificationHandler)

    # Violation Module
    EventBus.subscribe(PermissionRequestCreated, PermissionViolationHandler)
    EventBus.subscribe(PermissionRequestCreated, PermissionRequestNotificationHandler)
    EventBus.subscribe(HomeworkOverdueDetected, AutomatedViolationHandler)
    EventBus.subscribe(MeetingAbsenceDetected, AutomatedViolationHandler)
    EventBus.subscribe(ParticipantCheckedIn, AutomatedViolationHandler)
    EventBus.subscribe(ViolationCreated, ViolationNotificationHandler)

    # Homework Module

    EventBus.subscribe(HomeworkAssigned, HomeworkNotificationHandler)
    EventBus.subscribe(HomeworkGraded, HomeworkGradedNotificationHandler)

    # Meeting Module
    EventBus.subscribe(ParticipantCheckedIn, MeetingNotificationHandler)
    EventBus.subscribe(ParticipantCheckedIn, MeetingSseHandler)
    EventBus.subscribe(ParticipantCheckedOut, MeetingSseHandler)
    EventBus.subscribe(MeetingCreated, MeetingNotificationHandler)
    EventBus.subscribe(MeetingUpdated, MeetingNotificationHandler)

    # print all handlers for verification
    EventBus.print_handlers()
