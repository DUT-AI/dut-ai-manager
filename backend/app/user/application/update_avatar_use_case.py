from datetime import datetime

from fastapi import HTTPException, UploadFile

from app.shared.application.query_support_utils import build_query_support
from app.shared.domain.query_support import FilterCriterion, FilterOperator
from app.shared.infrastructure.minio_service import MinioService
from app.user.domain.entity import UserEntity
from app.user.infrastructure.repository import UserRepository


class UpdateAvatarUseCase:
    """Use case for uploading and setting user avatar."""

    def __init__(self, repo: UserRepository, minio: MinioService):
        self.repo = repo
        self.minio = minio

    async def execute(self, user_id: int, file: UploadFile) -> UserEntity:
        qs = build_query_support(
            filters=[
                FilterCriterion(field="id", operator=FilterOperator.EQ, value=user_id)
            ],
            include=[
                "roles",
                "roles.role_permissions",
                "roles.role_permissions.permission",
            ],
        )
        user = self.repo.get_one(qs)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        file_content = await file.read()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = (
            file.filename.split(".")[-1]
            if file.filename and "." in file.filename
            else "jpg"
        )
        filename = f"avatars/{user_id}_{timestamp}.{ext}"

        avatar_url = await self.minio.upload_file(
            file_data=file_content,
            filename=filename,
            content_type=file.content_type or "image/jpeg",
        )

        # Update entity field
        updated = user.model_copy(update={"avatar_url": avatar_url})
        return self.repo.update(updated)
