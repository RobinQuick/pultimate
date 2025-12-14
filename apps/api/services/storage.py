import uuid

import aioboto3
from botocore.config import Config
from fastapi import UploadFile

from core.config import settings


class StorageService:
    def __init__(self):
        self.session = aioboto3.Session()
        self.config = Config(signature_version='s3v4')

    async def upload_file(self, file: UploadFile, bucket: str, object_name: str = None) -> str:
        """
        Uploads a file to S3 and returns the key.
        """
        if object_name is None:
            ext = file.filename.split('.')[-1]
            object_name = f"{uuid.uuid4()}.{ext}"

        async with self.session.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
            config=self.config
        ) as s3:
            # Re-read file if needed or stream
            file.file.seek(0)
            await s3.upload_fileobj(file.file, bucket, object_name)
            
        return object_name

    async def generate_presigned_url(self, bucket: str, key: str, expiration=3600):
        async with self.session.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
            config=self.config
        ) as s3:
            url = await s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expiration
            )
            return url

storage = StorageService()
