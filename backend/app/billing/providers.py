from dishka import Provider, Scope, provide
from sqlalchemy.orm import Session

from app.billing.application.notification_handler import BillingNotificationHandler
from app.billing.application.use_cases import (
    CreateInvoiceUseCase,
    CreateMonthlyInvoicesUseCase,
    DeleteInvoiceUseCase,
    GetInvoicesUseCase,
    HandleSePayWebhookUseCase,
    UpdateInvoiceStatusUseCase,
    UpdateInvoiceUseCase,
)
from app.billing.infrastructure.repository import InvoiceRepository
from app.shared.infrastructure.notification.dispatcher import (
    UnifiedNotificationDispatcher,
)
from app.team.infrastructure.repository import TeamRepository
from app.violation.infrastructure.repository import ViolationRepository


class BillingModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_invoice_repo(self, session: Session) -> InvoiceRepository:
        return InvoiceRepository(session)

    @provide
    def create_invoice_uc(self, repo: InvoiceRepository) -> CreateInvoiceUseCase:
        return CreateInvoiceUseCase(repo)

    @provide
    def update_invoice_uc(self, repo: InvoiceRepository) -> UpdateInvoiceUseCase:
        return UpdateInvoiceUseCase(repo)

    @provide
    def update_invoice_status_uc(
        self, repo: InvoiceRepository
    ) -> UpdateInvoiceStatusUseCase:
        return UpdateInvoiceStatusUseCase(repo)

    @provide
    def get_invoices_uc(self, repo: InvoiceRepository) -> GetInvoicesUseCase:
        return GetInvoicesUseCase(repo)

    @provide
    def handle_webhook_uc(self, repo: InvoiceRepository) -> HandleSePayWebhookUseCase:
        return HandleSePayWebhookUseCase(repo)

    @provide
    def create_monthly_invoices_uc(
        self,
        repo: InvoiceRepository,
        violation_repo: ViolationRepository,
        team_repo: TeamRepository,
    ) -> CreateMonthlyInvoicesUseCase:
        return CreateMonthlyInvoicesUseCase(repo, violation_repo, team_repo)

    @provide
    def delete_invoice_uc(self, repo: InvoiceRepository) -> DeleteInvoiceUseCase:
        return DeleteInvoiceUseCase(repo)

    @provide
    def get_billing_notification_handler(
        self, dispatcher: UnifiedNotificationDispatcher
    ) -> BillingNotificationHandler:
        return BillingNotificationHandler(dispatcher)
