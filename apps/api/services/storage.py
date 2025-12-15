"""S3-compatible storage service for Pultimate.

Supports any S3-compatible service:
- Cloudflare R2
- MinIO
- AWS S3
- DigitalOcean Spaces
"""

import logging
import uuid

import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile

from core.config import settings

logger = logging.getLogger(__name__)

# File validation constants
ALLOWED_EXTENSIONS = {".pptx", ".potx", ".ppt"}
ALLOWED_MIME_TYPES = {
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.presentationml.template",
    "application/vnd.ms-powerpoint",
}
MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024  # Convert to bytes


class StorageService:
    """S3-compatible storage service with streaming upload support."""

    def __init__(self):
        self.session = aioboto3.Session()
        self.config = Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},  # Required for R2 compatibility
        )
        self.bucket = settings.S3_BUCKET

        logger.info(
            f"Storage initialized: endpoint={settings.S3_ENDPOINT_URL}, "
            f"bucket={self.bucket}, region={settings.S3_REGION}"
        )

    def _get_client_kwargs(self) -> dict:
        """Get boto3 client configuration."""
        return {
            "endpoint_url": settings.S3_ENDPOINT_URL,
            "aws_access_key_id": settings.S3_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.S3_SECRET_ACCESS_KEY,
            "region_name": settings.S3_REGION,
            "config": self.config,
        }

    def validate_file(self, file: UploadFile) -> None:
        """Validate file type and size.

        Raises:
            HTTPException: If file is invalid
        """
        # Check filename extension
        filename = file.filename or ""
        ext = "." + filename.split(".")[-1].lower() if "." in filename else ""

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

        # Check content type if available
        if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
            logger.warning(
                f"Unexpected MIME type: {file.content_type} for file {filename}. Proceeding based on extension."
            )

        # Check file size (if available in headers)
        if hasattr(file, "size") and file.size:
            if file.size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400, detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB"
                )

    async def upload_file(self, file: UploadFile, prefix: str, object_id: str = None, validate: bool = True) -> str:
        """Upload a file to S3-compatible storage.

        Args:
            file: FastAPI UploadFile object
            prefix: Storage prefix (e.g., 'decks', 'templates')
            object_id: Optional custom object ID (generates UUID if not provided)
            validate: Whether to validate file type/size

        Returns:
            S3 key of the uploaded object

        Raises:
            HTTPException: On validation or upload failure
        """
        if validate:
            self.validate_file(file)

        # Generate object key
        if object_id is None:
            object_id = str(uuid.uuid4())

        ext = file.filename.split(".")[-1].lower() if file.filename else "pptx"
        object_key = f"{prefix}/{object_id}.{ext}"

        logger.info(f"Uploading file: {file.filename} -> s3://{self.bucket}/{object_key}")

        try:
            async with self.session.client("s3", **self._get_client_kwargs()) as s3:
                # Stream upload - seek to start first
                file.file.seek(0)

                await s3.upload_fileobj(
                    file.file,
                    self.bucket,
                    object_key,
                    ExtraArgs={"ContentType": file.content_type or "application/octet-stream"},
                )

            logger.info(f"Upload successful: {object_key}")
            return object_key

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            logger.exception(f"S3 upload failed: {error_code} - {error_msg}")
            raise HTTPException(status_code=500, detail=f"Storage upload failed: {error_code}") from e
        except Exception as e:
            logger.exception(f"Unexpected upload error: {e}")
            raise HTTPException(status_code=500, detail="Storage upload failed unexpectedly") from e

    async def upload_deck(self, file: UploadFile, deck_id: str = None) -> str:
        """Upload a deck file with 'decks/' prefix."""
        return await self.upload_file(file, prefix="decks", object_id=deck_id)

    async def upload_template(self, file: UploadFile, template_id: str = None) -> str:
        """Upload a template file with 'templates/' prefix."""
        return await self.upload_file(file, prefix="templates", object_id=template_id)

    async def generate_presigned_url(
        self,
        key: str,
        expiration: int = 900,  # 15 minutes (secure default)
        bucket: str = None,
        filename: str = None,
    ) -> str:
        """Generate a presigned URL for downloading a file.

        Args:
            key: S3 object key
            expiration: URL expiration time in seconds (default: 15 min)
            bucket: Bucket name (uses default if not provided)
            filename: Optional filename for Content-Disposition header

        Returns:
            Presigned URL string
        """
        bucket = bucket or self.bucket

        params = {"Bucket": bucket, "Key": key}

        # Add Content-Disposition for attachment download
        if filename:
            params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'

        try:
            async with self.session.client("s3", **self._get_client_kwargs()) as s3:
                url = await s3.generate_presigned_url("get_object", Params=params, ExpiresIn=expiration)
                logger.info(f"Generated presigned URL for {key} (expires in {expiration}s)")
                return url
        except ClientError as e:
            logger.exception(f"Failed to generate presigned URL for {key}")
            raise HTTPException(status_code=500, detail="Failed to generate download URL") from e

    async def delete_file(self, key: str, bucket: str = None) -> bool:
        """Delete a file from storage.

        Args:
            key: S3 object key
            bucket: Bucket name (uses default if not provided)

        Returns:
            True if deleted successfully
        """
        bucket = bucket or self.bucket

        try:
            async with self.session.client("s3", **self._get_client_kwargs()) as s3:
                await s3.delete_object(Bucket=bucket, Key=key)
                logger.info(f"Deleted: s3://{bucket}/{key}")
                return True
        except ClientError:
            logger.exception(f"Failed to delete {key}")
            return False

    async def file_exists(self, key: str, bucket: str = None) -> bool:
        """Check if a file exists in storage.

        Args:
            key: S3 object key
            bucket: Bucket name (uses default if not provided)

        Returns:
            True if file exists
        """
        bucket = bucket or self.bucket

        try:
            async with self.session.client("s3", **self._get_client_kwargs()) as s3:
                await s3.head_object(Bucket=bucket, Key=key)
                return True
        except ClientError:
            return False

    async def download_file(self, key: str, local_path: str, bucket: str = None) -> None:
        """Download a file from storage to local path.

        Args:
            key: S3 object key
            local_path: Local file path to save to
            bucket: Bucket name (uses default if not provided)

        Raises:
            HTTPException: On download failure
        """
        bucket = bucket or self.bucket

        try:
            async with self.session.client("s3", **self._get_client_kwargs()) as s3:
                response = await s3.get_object(Bucket=bucket, Key=key)
                async with response["Body"] as stream:
                    data = await stream.read()
                    with open(local_path, "wb") as f:
                        f.write(data)
                logger.info(f"Downloaded: s3://{bucket}/{key} -> {local_path}")
        except ClientError as e:
            logger.exception(f"Failed to download {key}")
            raise HTTPException(status_code=500, detail=f"Failed to download file: {e}") from e

    async def upload_bytes(self, data: bytes, key: str, bucket: str = None) -> str:
        """Upload raw bytes to storage.

        Args:
            data: Bytes to upload
            key: S3 object key
            bucket: Bucket name (uses default if not provided)

        Returns:
            S3 key of uploaded object

        Raises:
            HTTPException: On upload failure
        """
        bucket = bucket or self.bucket

        try:
            async with self.session.client("s3", **self._get_client_kwargs()) as s3:
                await s3.put_object(Bucket=bucket, Key=key, Body=data)
                logger.info(f"Uploaded {len(data)} bytes to: s3://{bucket}/{key}")
                return key
        except ClientError as e:
            logger.exception(f"Failed to upload to {key}")
            raise HTTPException(status_code=500, detail=f"Failed to upload: {e}") from e


# Singleton instance
storage = StorageService()
