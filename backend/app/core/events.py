from dishka import AsyncContainer

from app.auth.account_notification_handler import AccountNotificationHandler
from app.auth.application.user_event_handler import UserAccountHandler
from app.auth.domain.events import AccountCreated
from app.homework.application.event_handlers import (
    HomeworkNotificationHandler,
    HomeworkGradedNotificationHandler
)
from app.homework.domain.value_objects import HomeworkAssigned, HomeworkOverdueDetected, HomeworkGraded
from app.permission_request.domain.events import PermissionRequestCreated
from app.shared.domain.event_bus import EventBus
from app.user.domain.events import UserCreated
from app.violation.application.event_handlers import AutomatedViolationHandler
from app.violation.notification_handler import ViolationNotificationHandler
from app.violation.domain.events import ViolationCreated
from app.violation.permission_handler import PermissionViolationHandler
from app.meeting.domain.events import ParticipantCheckedIn, MeetingCreated, MeetingUpdated, MeetingAbsenceDetected
from app.meeting.application.event_handlers import MeetingNotificationHandler
from app.permission_request.application.event_handlers import PermissionRequestNotificationHandler

async def bootstrap_events(container: AsyncContainer):
    """
    Register all domain event handlers using Dishka dependencies.
    We subscribe the handler TYPES. The EventBus will resolve instances
    from the current Request scope during execution.
    """

    # Auth Module
    EventBus.subscribe(UserCreated, UserAccountHandler)
    EventBus.subscribe(AccountCreated, AccountNotificationHandler)

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
    EventBus.subscribe(MeetingCreated, MeetingNotificationHandler)
    EventBus.subscribe(MeetingUpdated, MeetingNotificationHandler)

    # print all handlers for verification
    EventBus.print_handlers()
