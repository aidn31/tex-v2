"""Video chunk upload/delete for the Gemini analysis layer.

Backend is selected by GEMINI_BACKEND:
  - "developer_api" — Gemini Developer API File API. URIs expire after 48h.
  - "vertex"        — Google Cloud Storage. URIs are gs:// paths and never expire.

The returned dict shape is identical across backends:
    {"uri": str, "expires_at": datetime}
For Vertex/GCS, expires_at is a far-future sentinel (year 9999) so existing
uri_expiry checks treat the URI as permanently valid.
"""

import os
import time
from datetime import datetime, timedelta, timezone

from services.rate_limit import acquire_gemini_slot


class GeminiUploadError(Exception):
    """Raised when a video chunk upload fails."""
    pass


# Far-future sentinel for GCS URIs — they do not expire.
GCS_NEVER_EXPIRES = datetime(9999, 12, 31, tzinfo=timezone.utc)


def _backend() -> str:
    return os.environ.get("GEMINI_BACKEND", "developer_api")


# -----------------------------------------------------------------
# Developer API path
# -----------------------------------------------------------------
def _get_dev_client():
    from google import genai

    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def _upload_developer_api(local_path: str, mime_type: str) -> dict:
    client = _get_dev_client()
    acquire_gemini_slot("gemini-file-api")

    try:
        uploaded_file = client.files.upload(
            file=local_path,
            config={"mime_type": mime_type},
        )
    except Exception as e:
        raise GeminiUploadError(f"Gemini file upload failed: {e}")

    max_polls = 30
    for _ in range(max_polls):
        try:
            file_info = client.files.get(name=uploaded_file.name)
        except Exception as e:
            raise GeminiUploadError(f"Failed to check Gemini file status: {e}")

        if file_info.state == "ACTIVE":
            return {
                "uri": file_info.uri,
                "expires_at": _parse_expiry(file_info),
            }

        if file_info.state == "FAILED":
            raise GeminiUploadError(
                f"Gemini file processing failed for {uploaded_file.name}"
            )

        time.sleep(10)

    raise GeminiUploadError(
        f"Gemini file {uploaded_file.name} did not become ACTIVE within 5 minutes."
    )


def _delete_developer_api(uri: str) -> None:
    client = _get_dev_client()
    try:
        name = uri.split("/")[-1] if "/" in uri else uri
        if not name.startswith("files/"):
            name = f"files/{name}"
        client.files.delete(name=name)
    except Exception:
        pass


# -----------------------------------------------------------------
# Vertex / GCS path
# -----------------------------------------------------------------
def _gcs_credentials():
    from google.oauth2 import service_account

    key_path = os.environ["GCP_SERVICE_ACCOUNT_KEY_PATH"]
    return service_account.Credentials.from_service_account_file(
        key_path,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )


def _get_gcs_client():
    from google.cloud import storage

    project = os.environ["GCP_PROJECT_ID"]
    return storage.Client(project=project, credentials=_gcs_credentials())


def _parse_gs_uri(uri: str) -> tuple[str, str]:
    """Split a gs://bucket/key URI into (bucket, key)."""
    if not uri.startswith("gs://"):
        raise ValueError(f"Not a GCS URI: {uri}")
    without_scheme = uri[len("gs://"):]
    bucket, _, key = without_scheme.partition("/")
    if not bucket or not key:
        raise ValueError(f"Malformed GCS URI: {uri}")
    return bucket, key


def _upload_vertex_gcs(local_path: str, mime_type: str) -> dict:
    bucket_name = os.environ["GCS_BUCKET_CHUNKS"]
    client = _get_gcs_client()

    # Derive film_id + filename from the /tmp path convention:
    # /tmp/{film_id}_chunk_{NNN}.mp4  or  /tmp/{film_id}_reupload_chunk_{NNN}.mp4
    filename = os.path.basename(local_path)
    stem = filename[:-4] if filename.endswith(".mp4") else filename
    parts = stem.split("_")
    film_id = parts[0] if parts else "unknown"

    key = f"chunks/{film_id}/{filename}"

    try:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(key)
        blob.upload_from_filename(local_path, content_type=mime_type)
    except Exception as e:
        raise GeminiUploadError(f"GCS upload failed: {e}")

    return {
        "uri": f"gs://{bucket_name}/{key}",
        "expires_at": GCS_NEVER_EXPIRES,
    }


def _delete_vertex_gcs(uri: str) -> None:
    try:
        bucket_name, key = _parse_gs_uri(uri)
        client = _get_gcs_client()
        bucket = client.bucket(bucket_name)
        bucket.blob(key).delete()
    except Exception:
        pass


# -----------------------------------------------------------------
# Public surface
# -----------------------------------------------------------------
def upload_to_gemini(local_path: str, mime_type: str = "video/mp4") -> dict:
    """Upload a chunk to whichever backend GEMINI_BACKEND selects.

    Returns: {"uri": str, "expires_at": datetime}
    Raises: GeminiUploadError on failure.
    """
    if _backend() == "vertex":
        return _upload_vertex_gcs(local_path, mime_type)
    return _upload_developer_api(local_path, mime_type)


def delete_gemini_file(uri: str) -> None:
    """Delete a previously uploaded chunk. Best-effort — never raises."""
    if not uri:
        return
    if uri.startswith("gs://"):
        _delete_vertex_gcs(uri)
    else:
        _delete_developer_api(uri)


def _parse_expiry(file_info) -> datetime:
    """Extract expiry from a Developer API file_info. 48h from upload."""
    if hasattr(file_info, "expiration_time") and file_info.expiration_time:
        exp = file_info.expiration_time
        if isinstance(exp, datetime):
            if exp.tzinfo is None:
                return exp.replace(tzinfo=timezone.utc)
            return exp
    return datetime.now(timezone.utc) + timedelta(hours=47)
