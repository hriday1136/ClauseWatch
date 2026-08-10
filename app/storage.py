import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.config import settings
from app.crypto import decrypt_bytes, encrypt_bytes

s3_client = boto3.client(
    "s3",
    endpoint_url = settings.minio_endpoint,
    aws_access_key_id = settings.minio_access_key,
    aws_secret_access_key = settings.minio_secret_key,
    config=Config(
        signature_version="s3v4", 
        s3={"addressing_style": "path"}, 
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
    ),
    region_name=settings.minio_region
)

def ensure_bucket_exists() -> None:
    try:
        s3_client.head_bucket(Bucket=settings.minio_bucket_name)
    except ClientError:
        s3_client.create_bucket(Bucket=settings.minio_bucket_name)

def upload_file(key: str, file_bytes: bytes, content_type: str) -> None:
    encrypted_bytes = encrypt_bytes(file_bytes)
    s3_client.put_object(
        Bucket = settings.minio_bucket_name,
        Key=key,
        Body=encrypted_bytes,
        ContentType=content_type
    )

def download_file(key: str) -> bytes:
    response = s3_client.get_object(Bucket=settings.minio_bucket_name, Key=key)
    encrypted_bytes = response["Body"].read()
    return decrypt_bytes(encrypted_bytes)