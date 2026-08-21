"""MinIO / S3 Storage Service for file uploads using aioboto3."""

import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError
from loguru import logger

from app.core.config import settings
from app.shared.application.response import BadRequestException


class MinioService:
    """Service for handling asynchronous file uploads to MinIO / S3 storage."""

    # Allowed file extensions for homework submissions
    ALLOWED_EXTENSIONS = {".zip", ".rar", ".7z", ".tar.gz", ".gz"}
    # Maximum file size in bytes (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    # Prefix for homework submissions
    SUBMISSIONS_PREFIX = "homework-submissions"
    HOMEWORK_PREFIX = "homeworks"

    def __init__(self):
        self.session = aioboto3.Session()
        self.bucket_name = settings.MINIO_BUCKET_NAME
        protocol = "https" if settings.MINIO_SECURE else "http"
        self.endpoint_url = f"{protocol}://{settings.MINIO_ENDPOINT}"
        self.aws_access_key_id = settings.MINIO_ACCESS_KEY
        self.aws_secret_access_key = settings.MINIO_SECRET_KEY
        self.boto_config = Config(
            connect_timeout=5,
            read_timeout=30,
            retries={"max_attempts": 2},
        )
        logger.debug(
            f"S3 Storage service initialized with endpoint: {self.endpoint_url}, bucket: {self.bucket_name}"
        )

    def _get_client(self):
        """Create an async s3 client context manager."""
        return self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            config=self.boto_config,
        )

    async def ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            async with self._get_client() as s3:
                try:
                    await s3.head_bucket(Bucket=self.bucket_name)
                except ClientError:
                    await s3.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Created S3/MinIO bucket: {self.bucket_name}")
        except Exception as e:
            logger.warning(f"Could not verify/create bucket {self.bucket_name}: {e}")

    def validate_file(self, filename: str, file_size: int) -> str | None:
        """
        Validate file extension and size.
        Returns error message if invalid, None if valid.
        """
        filename_lower = filename.lower()
        is_valid_extension = any(
            filename_lower.endswith(ext) for ext in self.ALLOWED_EXTENSIONS
        )
        if not is_valid_extension:
            return f"File type không được hỗ trợ. Chỉ chấp nhận: {', '.join(self.ALLOWED_EXTENSIONS)}"

        if file_size > self.MAX_FILE_SIZE:
            max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            return f"File quá lớn. Giới hạn tối đa: {max_mb:.0f}MB"

        return None

    async def upload_file(
        self,
        file_data: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload file to S3/MinIO asynchronously and return the public URL.

        Args:
            file_data: File content as bytes
            filename: Name to save the file as
            content_type: MIME type of the file

        Returns:
            Public URL of the uploaded file
        """
        try:
            async with self._get_client() as s3:
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=filename,
                    Body=file_data,
                    ContentType=content_type,
                )
                logger.info(f"Uploaded file to S3/MinIO: {filename}")
                return self.get_public_url(filename)
        except Exception as e:
            logger.error(f"Failed to upload file to S3/MinIO: {e}")
            raise BadRequestException(f"Failed to upload file to storage: {e}")

    def get_public_url(self, filename: str) -> str:
        """
        Get the public URL for a file in MinIO/S3.

        Args:
            filename: Object key in the bucket

        Returns:
            Public URL to access the file
        """
        protocol = "https" if settings.MINIO_SECURE else "http"
        return f"{protocol}://{settings.MINIO_ENDPOINT}/{self.bucket_name}/{filename}"

    async def delete_file(self, filename: str) -> bool:
        """
        Delete a file from S3/MinIO.

        Args:
            filename: Object key to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            async with self._get_client() as s3:
                await s3.delete_object(Bucket=self.bucket_name, Key=filename)
                logger.info(f"Deleted file from S3/MinIO: {filename}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete file from S3/MinIO: {e}")
            return False
