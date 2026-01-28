"""MinIO Storage Service for file uploads."""

from app.schemas.response import BadRequestException
from io import BytesIO
from typing import Optional

from minio import Minio
from minio.error import S3Error
from loguru import logger

from app.core.config import settings
import json


class MinioService:
    """Service for handling file uploads to MinIO storage."""

    # Allowed file extensions for homework submissions
    ALLOWED_EXTENSIONS = {".zip", ".rar", ".7z", ".tar.gz", ".gz"}
    # Maximum file size in bytes (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    # Prefix for homework submissions
    SUBMISSIONS_PREFIX = "homework-submissions"
    HOMEWORK_PREFIX = "homeworks"

    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        logger.debug(
            f"MinIO client initialized with endpoint: {settings.MINIO_ENDPOINT}, bucket: {settings.MINIO_BUCKET_NAME}"
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist and set public read policy."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created MinIO bucket: {self.bucket_name}")

            # Set bucket policy for public read access
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{self.bucket_name}/*"],
                    }
                ],
            }

            self.client.set_bucket_policy(self.bucket_name, json.dumps(policy))
            logger.info(f"Set public read policy for bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Failed to ensure bucket exists: {e}")
            raise

    def validate_file(self, filename: str, file_size: int) -> Optional[str]:
        """
        Validate file extension and size.
        Returns error message if invalid, None if valid.
        """
        # Check file extension
        filename_lower = filename.lower()
        is_valid_extension = any(
            filename_lower.endswith(ext) for ext in self.ALLOWED_EXTENSIONS
        )
        if not is_valid_extension:
            return f"File type không được hỗ trợ. Chỉ chấp nhận: {', '.join(self.ALLOWED_EXTENSIONS)}"

        # Check file size
        if file_size > self.MAX_FILE_SIZE:
            max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            return f"File quá lớn. Giới hạn tối đa: {max_mb:.0f}MB"

        return None

    def upload_file(
        self,
        file_data: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload file to MinIO and return the public URL.

        Args:
            file_data: File content as bytes
            filename: Name to save the file as (should include the full path/prefix relative to bucket)
            content_type: MIME type of the file

        Returns:
            Public URL of the uploaded file
        """
        try:
            data = BytesIO(file_data)
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=filename,
                data=data,
                length=len(file_data),
                content_type=content_type,
            )
            logger.info(f"Uploaded file to MinIO: {filename}")
            return self.get_public_url(filename)
        except S3Error as e:
            logger.error(f"Failed to upload file to MinIO: {e}")
            raise BadRequestException("Failed to upload file to MinIO")

    def get_public_url(self, filename: str) -> str:
        """
        Get the public URL for a file in MinIO.

        Args:
            filename: Object name in the bucket

        Returns:
            Public URL to access the file
        """
        protocol = "https" if settings.MINIO_SECURE else "http"
        return f"{protocol}://{settings.MINIO_ENDPOINT}/{self.bucket_name}/{filename}"

    def delete_file(self, filename: str) -> bool:
        """
        Delete a file from MinIO.

        Args:
            filename: Object name to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            self.client.remove_object(self.bucket_name, filename)
            logger.info(f"Deleted file from MinIO: {filename}")
            return True
        except S3Error as e:
            logger.error(f"Failed to delete file from MinIO: {e}")
            return False
