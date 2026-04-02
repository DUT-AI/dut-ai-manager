from dishka import AsyncContainer
from app.shared.domain.event_bus import EventBus
from app.user.domain.events import UserCreated
from app.auth.domain.events import AccountCreated
from app.permission_request.domain.events import PermissionRequestCreated
from app.auth.account_notification_handler import AccountNotificationHandler
from app.auth.application.user_event_handler import UserAccountHandler
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
    
    # Violation Module
    EventBus.subscribe(PermissionRequestCreated, PermissionViolationHandler)
    
    # print all handlers for verification
    EventBus.print_handlers()
