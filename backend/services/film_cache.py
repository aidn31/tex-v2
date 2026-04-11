from typing import Optional


def check_film_cache(file_hash: str, prompt_version: str, conn) -> Optional[dict]:
    """Check film_analysis_cache for a cached result matching this hash + prompt version.

    Returns cached sections dict or None.
    Called by process_film at step 5 to skip reprocessing identical film content.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT sections, synthesis_document FROM film_analysis_cache "
            "WHERE file_hash = %s AND prompt_version = %s",
            (file_hash, prompt_version),
        )
        row = cur.fetchone()

    if not row:
        return None

    return {
        "sections": row[0],
        "synthesis_document": row[1],
    }
