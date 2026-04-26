from app.billing.application.use_cases import (
    CreateInvoiceUseCase,
    UpdateInvoiceUseCase,
    CreateMonthlyInvoicesUseCase,
    DeleteInvoiceUseCase,
    GetInvoicesUseCase,
    HandleSePayWebhookUseCase,
)
from app.billing.infrastructure.repository import InvoiceRepository
from app.violation.infrastructure.repository import ViolationRepository
from app.team.infrastructure.repository import TeamRepository
from dishka import Provider, Scope, provide
from sqlmodel import Session


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
        team_repo: TeamRepository
    ) -> CreateMonthlyInvoicesUseCase:
        return CreateMonthlyInvoicesUseCase(repo, violation_repo, team_repo)

    @provide
    def delete_invoice_uc(self, repo: InvoiceRepository) -> DeleteInvoiceUseCase:
        return DeleteInvoiceUseCase(repo)
