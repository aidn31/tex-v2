import logging
import os

from services.db import get_connection
from services.gemini_files import upload_to_gemini
from services.r2 import download_from_r2

log = logging.getLogger(__name__)


def get_valid_chunk_uris(film_id: str, conn) -> list[dict]:
    """Get all chunk URIs for a film, re-uploading any that are expired or expiring.

    Returns list of dicts sorted by chunk_index:
        [{"chunk_index": 0, "uri": "files/abc123"}, ...]

    Any chunk whose gemini_file_expires_at is within 1 hour of now() gets
    re-downloaded from R2 and re-uploaded to Gemini. The DB row is updated
    with the new URI and expiry.

    Called by report generation in Phase 3.
    """
    bucket = os.environ["CLOUDFLARE_R2_BUCKET_FILMS"]

    with conn.cursor() as cur:
        # Find chunks that are expired or expiring within 1 hour
        cur.execute(
            "SELECT id, chunk_index, r2_chunk_key, gemini_file_uri "
            "FROM film_chunks "
            "WHERE film_id = %s AND gemini_file_state = 'active' "
            "AND gemini_file_expires_at < now() + interval '1 hour'",
            (film_id,),
        )
        expired_chunks = cur.fetchall()

    # Re-upload expired chunks
    for chunk_row in expired_chunks:
        chunk_id = str(chunk_row[0])
        chunk_index = chunk_row[1]
        r2_chunk_key = chunk_row[2]

        log.info("Re-uploading expired chunk %d for film %s", chunk_index, film_id)

        local_path = f"/tmp/{film_id}_reupload_chunk_{chunk_index:03d}.mp4"
        try:
            download_from_r2(bucket, r2_chunk_key, local_path)
            gemini_result = upload_to_gemini(local_path)

            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE film_chunks SET "
                    "gemini_file_uri = %s, gemini_file_expires_at = %s "
                    "WHERE id = %s",
                    (gemini_result["uri"], gemini_result["expires_at"], chunk_id),
                )
            conn.commit()
        finally:
            import os as _os
            if _os.path.exists(local_path):
                _os.remove(local_path)

    # Fetch all valid chunks
    with conn.cursor() as cur:
        cur.execute(
            "SELECT chunk_index, gemini_file_uri FROM film_chunks "
            "WHERE film_id = %s AND gemini_file_state = 'active' "
            "ORDER BY chunk_index",
            (film_id,),
        )
        rows = cur.fetchall()

    return [{"chunk_index": row[0], "uri": row[1]} for row in rows]
