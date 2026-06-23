import re
from pathlib import PurePath

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile

from app.config import Settings
from app.constants import ALLOWED_FILE_TYPES


def sanitize_filename(filename: str) -> str:
    name = PurePath(filename).name.strip() or "upload"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)


def file_type_from_filename(filename: str) -> str:
    if "." not in filename:
        raise HTTPException(status_code=400, detail="Unsupported file type: missing extension")
    file_type = filename.rsplit(".", 1)[1].lower()
    if file_type not in ALLOWED_FILE_TYPES:
        allowed = ", ".join(sorted(ALLOWED_FILE_TYPES))
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed types: {allowed}")
    return file_type


def validate_upload_file(file: UploadFile) -> str:
    return file_type_from_filename(file.filename or "")


class S3Storage:
    def __init__(self, settings: Settings) -> None:
        self.provider = settings.storage_provider.lower().strip()
        if self.provider == "r2":
            if not settings.r2_account_id and not settings.r2_endpoint:
                raise RuntimeError("R2 storage requires R2_ACCOUNT_ID or R2_ENDPOINT.")
            self.bucket = settings.r2_bucket_name or settings.s3_bucket
            endpoint = settings.r2_endpoint or f"https://{settings.r2_account_id}.r2.cloudflarestorage.com"
            access_key = settings.r2_access_key_id or settings.s3_access_key
            secret_key = settings.r2_secret_access_key or settings.s3_secret_key
            self.public_base_url = settings.r2_public_base_url
        elif self.provider == "minio":
            self.bucket = settings.minio_bucket or settings.s3_bucket
            endpoint = settings.minio_endpoint or settings.s3_endpoint
            access_key = settings.minio_access_key or settings.s3_access_key
            secret_key = settings.minio_secret_key or settings.s3_secret_key
            self.public_base_url = None
        else:
            raise RuntimeError(f"Unsupported STORAGE_PROVIDER: {settings.storage_provider}")

        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="us-east-1",
        )

    def ensure_bucket(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            self.client.create_bucket(Bucket=self.bucket)

    def upload_fileobj(self, key: str, fileobj, content_type: str | None) -> None:
        self.ensure_bucket()
        fileobj.seek(0)
        extra_args = {"ContentType": content_type} if content_type else None
        if extra_args:
            self.client.upload_fileobj(fileobj, self.bucket, key, ExtraArgs=extra_args)
        else:
            self.client.upload_fileobj(fileobj, self.bucket, key)

    def upload_file(self, key: str, fileobj, content_type: str | None = None) -> None:
        self.upload_fileobj(key, fileobj, content_type)

    def download_file(self, key: str, destination_path: str) -> None:
        self.client.download_file(self.bucket, key, destination_path)

    def delete_file(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def get_file_metadata(self, key: str) -> dict:
        response = self.client.head_object(Bucket=self.bucket, Key=key)
        return {
            "key": key,
            "bucket": self.bucket,
            "content_length": response.get("ContentLength"),
            "content_type": response.get("ContentType"),
            "etag": response.get("ETag"),
            "last_modified": response.get("LastModified").isoformat() if response.get("LastModified") else None,
        }

    def create_presigned_download_url(self, key: str, expires_in_seconds: int = 3600) -> str:
        if self.public_base_url:
            return f"{self.public_base_url.rstrip('/')}/{key.lstrip('/')}"
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in_seconds,
        )
