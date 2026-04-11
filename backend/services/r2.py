import os

import boto3


def get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{os.environ['CLOUDFLARE_R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["CLOUDFLARE_R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["CLOUDFLARE_R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )


def generate_presigned_upload_url(bucket: str, key: str, expiry_seconds: int = 3600) -> str:
    client = get_r2_client()
    return client.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expiry_seconds,
    )


def generate_presigned_read_url(bucket: str, key: str, expiry_seconds: int = 900) -> str:
    client = get_r2_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expiry_seconds,
    )


def download_from_r2(bucket: str, key: str, local_path: str) -> None:
    """Download a file from R2 to a local path."""
    client = get_r2_client()
    client.download_file(bucket, key, local_path)


def upload_to_r2(bucket: str, key: str, local_path: str) -> None:
    """Upload a local file to R2."""
    client = get_r2_client()
    client.upload_file(local_path, bucket, key)
