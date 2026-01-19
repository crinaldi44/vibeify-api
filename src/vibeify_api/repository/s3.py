"""S3 repository for file storage operations."""
from typing import Optional, BinaryIO
import uuid
from datetime import datetime

from vibeify_api.core.config import get_settings
from vibeify_api.core.s3 import get_s3_session

settings = get_settings()


class S3Repository:
    """Repository for S3 file storage operations.
    
    Provides abstraction over S3 operations for file storage and retrieval.
    """

    def __init__(self, bucket_name: Optional[str] = None):
        """Initialize S3 repository.
        
        Args:
            bucket_name: S3 bucket name (defaults to settings.S3_BUCKET_NAME)
        """
        self.bucket_name = bucket_name or settings.S3_BUCKET_NAME
        self.session = get_s3_session()

    def generate_key(self, filename: str, user_id: Optional[int] = None) -> str:
        """Generate a predictable S3 key for a file.
        
        Format: {year}/{month}/{day}/{user_id}/{uuid}-{filename}
        
        Args:
            filename: Original filename
            user_id: Optional user ID
            
        Returns:
            S3 key string
        """
        now = datetime.utcnow()
        date_prefix = f"{now.year}/{now.month:02d}/{now.day:02d}"
        file_uuid = str(uuid.uuid4())
        
        # Sanitize filename
        safe_filename = filename.replace(" ", "_").replace("/", "_")
        
        if user_id:
            return f"{date_prefix}/{user_id}/{file_uuid}-{safe_filename}"
        return f"{date_prefix}/{file_uuid}-{safe_filename}"

    async def generate_presigned_url(
        self,
        s3_key: str,
        operation: str = "put_object",
        expiration: Optional[int] = None,
    ) -> str:
        """Generate a presigned URL for S3 operations.
        
        Args:
            s3_key: S3 object key
            operation: S3 operation ('put_object' for upload, 'get_object' for download)
            expiration: URL expiration time in seconds (defaults to S3_PRESIGNED_URL_EXPIRATION)
            
        Returns:
            Presigned URL string
        """
        expiration = expiration or settings.S3_PRESIGNED_URL_EXPIRATION
        
        async with self.session.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        ) as s3_client:
            if operation == "put_object":
                url = await s3_client.generate_presigned_url(
                    "put_object",
                    Params={"Bucket": self.bucket_name, "Key": s3_key},
                    ExpiresIn=expiration,
                )
            else:  # get_object
                url = await s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": s3_key},
                    ExpiresIn=expiration,
                )
            return url

    async def upload_file(
        self,
        s3_key: str,
        file_data: BinaryIO,
        content_type: Optional[str] = None,
    ) -> dict:
        """Upload a file directly to S3.
        
        Args:
            s3_key: S3 object key
            file_data: File-like object to upload
            content_type: Optional content type
            
        Returns:
            Dictionary with upload result
        """
        async with self.session.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        ) as s3_client:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type
            
            await s3_client.upload_fileobj(
                file_data,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args,
            )
            
            return {"key": s3_key, "bucket": self.bucket_name}

    async def delete_file(self, s3_key: str) -> bool:
        """Delete a file from S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if deleted successfully
        """
        async with self.session.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        ) as s3_client:
            await s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key,
            )
            return True

    async def file_exists(self, s3_key: str) -> bool:
        """Check if a file exists in S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if file exists
        """
        async with self.session.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        ) as s3_client:
            try:
                await s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                )
                return True
            except s3_client.exceptions.ClientError:
                return False
