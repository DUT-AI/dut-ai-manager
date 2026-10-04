"""
Import Users Use Case — application orchestrator for bulk user import.
"""

from fastapi import BackgroundTasks, HTTPException, UploadFile
from loguru import logger

from app.rbac.domain.entity import RoleType
from app.rbac.infrastructure.repository import RoleRepository
from app.shared.application.query_support_utils import build_query_support
from app.shared.domain.query_support import FilterCriterion, FilterOperator
from app.user.application.create_user_use_case import CreateUserUseCase
from app.user.application.dtos import UserCreate, UserImportResult
from app.user.application.user_import_parser import UserImportParser
from app.user.domain.value_objects import UserImportRow
from app.user.infrastructure.repository import UserRepository


class ImportUsersUseCase:
    """Orchestrates bulk user importing from external files."""

    def __init__(
        self,
        create_user_uc: CreateUserUseCase,
        user_repo: UserRepository,
        role_repo: RoleRepository,
    ):
        self.create_user_uc = create_user_uc
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.parser = UserImportParser()

    async def execute(
        self, file: UploadFile, background_tasks: BackgroundTasks
    ) -> UserImportResult:
        # 1. Parse file into domain import row models
        rows = await self.parser.parse_file(file)

        # 2. Retrieve default role
        teammate_role = self.role_repo.get_by_name(RoleType.TEAMMATE.value)
        if not teammate_role or not teammate_role.id:
            raise HTTPException(
                status_code=400, detail="Default teammate role not found"
            )

        summary = UserImportResult(
            total=len(rows), success_count=0, error_count=0, errors=[]
        )

        seen_emails_in_batch: set[str] = set()

        # 3. Process each row
        for row in rows:
            await self._process_row(
                row=row,
                role_id=teammate_role.id,
                background_tasks=background_tasks,
                seen_emails=seen_emails_in_batch,
                summary=summary,
            )

        return summary

    async def _process_row(
        self,
        row: UserImportRow,
        role_id: int,
        background_tasks: BackgroundTasks,
        seen_emails: set[str],
        summary: UserImportResult,
    ) -> None:
        # Check validation errors from parsing/domain stage
        if row.validation_error:
            summary.error_count += 1
            summary.errors.append(f"Row {row.row_num}: {row.validation_error}")
            return

        # Check duplicate within the current file batch
        if row.email in seen_emails:
            summary.error_count += 1
            summary.errors.append(
                f"Row {row.row_num}: Duplicate email in import file ({row.email})"
            )
            return

        # Check existence in database
        qs_email = build_query_support(
            filters=[
                FilterCriterion(
                    field="email", operator=FilterOperator.EQ, value=row.email
                )
            ]
        )
        if self.user_repo.get_one(qs_email):
            summary.error_count += 1
            summary.errors.append(
                f"Row {row.row_num}: Email already exists ({row.email})"
            )
            return

        # Build DTO
        user_data = UserCreate(
            name=row.name,
            email=row.email,
            phone_number=row.phone_number,
            role_ids=[role_id],
        )

        # Execute creation with database savepoint
        try:
            with self.user_repo.session.begin_nested():
                await self.create_user_uc.execute(user_data, background_tasks)

            seen_emails.add(row.email)
            summary.success_count += 1
        except Exception as e:
            error_msg = str(e.detail) if hasattr(e, "detail") else str(e)
            if "validation error" in error_msg.lower():
                error_msg = "Invalid data format"

            logger.warning(f"Error importing row {row.row_num}: {error_msg}")
            summary.error_count += 1
            summary.errors.append(f"Row {row.row_num}: {error_msg}")
