import os
import time
from datetime import datetime, timedelta, timezone

from google import genai

from services.rate_limit import acquire_gemini_slot


class GeminiUploadError(Exception):
    """Raised when a Gemini File API upload fails."""
    pass


def _get_client():
    """Create a Gemini client. New client per call — safe for Celery workers."""
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def upload_to_gemini(local_path: str, mime_type: str = "video/mp4") -> dict:
    """Upload a local file to Gemini File API and poll until ACTIVE.

    Acquires a rate limit slot before uploading.
    Polls every 10 seconds for up to 5 minutes.

    Returns: {"uri": str, "expires_at": datetime} where expires_at is UTC.
    Raises: GeminiUploadError on failure or timeout.
    """
    client = _get_client()
    acquire_gemini_slot("gemini-file-api")

    try:
        uploaded_file = client.files.upload(
            file=local_path,
            config={"mime_type": mime_type},
        )
    except Exception as e:
        raise GeminiUploadError(f"Gemini file upload failed: {e}")

    # Poll until state is ACTIVE (max 5 minutes, every 10 seconds)
    max_polls = 30
    for _ in range(max_polls):
        try:
            file_info = client.files.get(name=uploaded_file.name)
        except Exception as e:
            raise GeminiUploadError(f"Failed to check Gemini file status: {e}")

        if file_info.state == "ACTIVE":
            expires_at = _parse_expiry(file_info)
            return {
                "uri": file_info.uri,
                "expires_at": expires_at,
            }

        if file_info.state == "FAILED":
            raise GeminiUploadError(
                f"Gemini file processing failed for {uploaded_file.name}"
            )

        time.sleep(10)

    raise GeminiUploadError(
        f"Gemini file {uploaded_file.name} did not become ACTIVE within 5 minutes."
    )


def delete_gemini_file(uri: str) -> None:
    """Delete a file from Gemini File API. Best-effort — logs but does not raise."""
    client = _get_client()
    try:
        # URI format is "https://generativelanguage.googleapis.com/..." or "files/abc123"
        # client.files.delete expects the file name like "files/abc123"
        name = uri.split("/")[-1] if "/" in uri else uri
        if not name.startswith("files/"):
            name = f"files/{name}"
        client.files.delete(name=name)
    except Exception:
        pass


def _parse_expiry(file_info) -> datetime:
    """Extract expiry timestamp from Gemini file info.

    Gemini files expire 48 hours after upload. The API returns expiration_time.
    Falls back to now + 47 hours if the field is not available.
    """
    if hasattr(file_info, "expiration_time") and file_info.expiration_time:
        exp = file_info.expiration_time
        if isinstance(exp, datetime):
            if exp.tzinfo is None:
                return exp.replace(tzinfo=timezone.utc)
            return exp
    # Fallback: 47 hours from now (conservative — actual is 48h)
    return datetime.now(timezone.utc) + timedelta(hours=47)
