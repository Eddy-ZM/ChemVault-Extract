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
        self.bucket = settings.s3_bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
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
