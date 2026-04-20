import hashlib
import json
import logging
import os
import traceback

from celery import group
from celery.exceptions import SoftTimeLimitExceeded

from tasks.celery_app import celery_app
from services.ai.router import get_ai_provider
from services.db import get_connection
from services.ffmpeg import FFmpegError, compress_film, split_film
from services.ffprobe import FilmValidationError, get_duration, validate_film_file
from services.gemini_files import GeminiUploadError, upload_to_gemini
from services.prompts import load_prompt
from services.r2 import download_from_r2, upload_to_r2
from services.rate_limit import acquire_gemini_slot
from services.roster_format import format_roster_for_prompt

log = logging.getLogger(__name__)

PROMPT_VERSION = "v1.0"


def _load_preprocess_prompt(section_type: str) -> tuple[str, str]:
    """Load a pre-processing prompt (chunk_extraction or chunk_synthesis).

    Raises NotImplementedError — not FileNotFoundError — when the prompt
    file has not yet been written, so the failure mode is unmistakable in
    logs and dead letters. Tommy drafts these separately; see ROADMAP.md
    ACTIVE BLOCKERS — "Pre-Processing Pipeline (Prompts 0A + 0B)".
    """
    try:
        return load_prompt(section_type)
    except FileNotFoundError as e:
        raise NotImplementedError(
            f"Prompt file for '{section_type}' is not written yet. "
            f"See ROADMAP.md ACTIVE BLOCKERS. Underlying: {e}"
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file using streaming reads."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def _write_dead_letter(task_name: str, task_args: dict, queue: str,
                       error_message: str, error_tb: str, retry_count: int,
                       film_id: str = None, report_id: str = None,
                       user_id: str = None):
    """Write a dead letter row for a task that has exhausted retries."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO dead_letter_tasks "
                "(task_name, task_args, queue, error_message, error_traceback, "
                "retry_count, film_id, report_id, user_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (task_name, json.dumps(task_args), queue,
                 error_message[:2000], (error_tb or "")[:4000],
                 retry_count, film_id, report_id, user_id),
            )
        conn.commit()
    except Exception:
        log.exception("Failed to write dead letter for %s film_id=%s", task_name, film_id)
        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        conn.close()


def _update_film_status(film_id: str, status: str, error_message: str = None,
                        gemini_processing_status: str = None):
    """Update films.status and optionally error_message and gemini_processing_status."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            sets = "status = %s, updated_at = now()"
            params: list = [status]
            if error_message is not None:
                sets += ", error_message = %s"
                params.append(error_message[:2000])
            if gemini_processing_status is not None:
                sets += ", gemini_processing_status = %s"
                params.append(gemini_processing_status)
            params.append(film_id)
            cur.execute(f"UPDATE films SET {sets} WHERE id = %s", params)
        conn.commit()
    finally:
        conn.close()


def _cleanup_tmp(tmp_files: list[str]):
    """Delete all tracked /tmp files. Called in finally blocks."""
    for path in tmp_files:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            log.warning("Failed to clean up tmp file: %s", path)


def _backoff(retry_number: int) -> int:
    """Exponential backoff: 30s, 120s, 480s."""
    delays = [30, 120, 480]
    if retry_number < len(delays):
        return delays[retry_number]
    return delays[-1]


def _fail_film_from_chunk(film_id: str, error_message: str):
    """Mark a film as error because a chunk permanently failed.

    Atomic and idempotent — uses a conditional UPDATE so only the first
    failing chunk transitions the film and notifies the coach. Subsequent
    chunk failures for the same film are no-ops.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE films SET status = 'error', error_message = %s, "
                "updated_at = now() "
                "WHERE id = %s AND status NOT IN ('error', 'processed')",
                (error_message[:2000], film_id),
            )
            updated = cur.rowcount > 0
        conn.commit()
    finally:
        conn.close()

    if updated:
        from tasks.notifications import notify_coach
        notify_coach.delay(film_id=film_id, notification_type="film_error")


# ---------------------------------------------------------------------------
# TASK: process_film
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    name="tasks.film_processing.process_film",
    queue="film_processing",
    max_retries=3,
    default_retry_delay=30,
    soft_time_limit=7000,
    time_limit=7200,
    acks_late=True,
)
def process_film(self, film_id: str):
    """Download film from R2, validate, compress, split, upload chunks to R2,
    then enqueue extract_chunk for each chunk."""

    tmp_files = []
    user_id = None
    bucket = os.environ["CLOUDFLARE_R2_BUCKET_FILMS"]

    try:
        # 1. Fetch film and check idempotency
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT user_id, r2_key, file_size_bytes, file_name, status "
                    "FROM films WHERE id = %s",
                    (film_id,),
                )
                row = cur.fetchone()
        finally:
            conn.close()

        if not row:
            log.error("process_film: film %s not found in DB", film_id)
            return

        user_id = str(row[0])
        r2_key = row[1]
        file_size_bytes = row[2]
        file_name = row[3]
        current_status = row[4]

        if current_status in ("processing", "processed", "error"):
            log.info("process_film: film %s already %s, skipping", film_id, current_status)
            return

        # 2. Set status to processing
        _update_film_status(film_id, "processing")

        # 3. Download raw film from R2 to /tmp
        ext = os.path.splitext(file_name)[1] or ".mp4"
        raw_path = f"/tmp/{film_id}_raw{ext}"
        tmp_files.append(raw_path)

        log.info("process_film: downloading %s from R2", film_id)
        download_from_r2(bucket, r2_key, raw_path)

        # 4. Compute SHA-256 hash
        file_hash = _compute_sha256(raw_path)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE films SET file_hash = %s WHERE id = %s",
                    (file_hash, film_id),
                )
            conn.commit()
        finally:
            conn.close()

        # 5. Check film_analysis_cache for this hash + prompt_version
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM film_analysis_cache "
                    "WHERE file_hash = %s AND prompt_version = %s",
                    (file_hash, PROMPT_VERSION),
                )
                cache_hit = cur.fetchone()
        finally:
            conn.close()

        if cache_hit:
            log.info("process_film: cache hit for film %s hash %s", film_id, file_hash[:12])
            _update_film_status(film_id, "processed")
            return

        # 6. FFprobe validation
        log.info("process_film: validating film %s", film_id)
        try:
            probe_result = validate_film_file(raw_path)
        except FilmValidationError as e:
            _write_dead_letter(
                task_name="process_film",
                task_args={"film_id": film_id},
                queue="film_processing",
                error_message=str(e),
                error_tb=None,
                retry_count=self.request.retries,
                film_id=film_id,
                user_id=user_id,
            )
            _update_film_status(film_id, "error", str(e))
            from tasks.notifications import notify_coach
            notify_coach.delay(film_id=film_id, notification_type="film_error")
            return

        duration = probe_result["duration"]

        # 7. Compress if file > 1.8GB
        input_path = raw_path
        if file_size_bytes > 1_800_000_000:
            compressed_path = f"/tmp/{film_id}_compressed.mp4"
            tmp_files.append(compressed_path)
            log.info("process_film: compressing film %s (%d bytes)", film_id, file_size_bytes)
            compress_film(raw_path, compressed_path)
            input_path = compressed_path

        # 8. Split into chunks
        chunk_pattern = f"/tmp/{film_id}_chunk_%03d.mp4"
        log.info("process_film: splitting film %s", film_id)
        chunk_paths = split_film(input_path, chunk_pattern)
        tmp_files.extend(chunk_paths)

        chunk_count = len(chunk_paths)

        # 9. Update films with duration and chunk count
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE films SET duration_seconds = %s, chunk_count = %s, updated_at = now() "
                    "WHERE id = %s",
                    (int(duration), chunk_count, film_id),
                )
            conn.commit()
        finally:
            conn.close()

        # 10. Upload each chunk to R2 and insert film_chunks row
        chunk_ids = []
        for idx, chunk_path in enumerate(chunk_paths):
            r2_chunk_key = f"chunks/{film_id}/chunk_{idx:03d}.mp4"

            log.info("process_film: uploading chunk %d/%d to R2 for film %s", idx + 1, chunk_count, film_id)
            upload_to_r2(bucket, r2_chunk_key, chunk_path)

            # Get chunk duration — use get_duration (no min/max validation)
            # because last chunk may be under 60 seconds
            chunk_duration = int(get_duration(chunk_path))

            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO film_chunks "
                        "(film_id, chunk_index, duration_seconds, r2_chunk_key, gemini_file_state) "
                        "VALUES (%s, %s, %s, %s, 'uploading') "
                        "ON CONFLICT (film_id, chunk_index) DO UPDATE SET "
                        "r2_chunk_key = EXCLUDED.r2_chunk_key, gemini_file_state = 'uploading' "
                        "RETURNING id",
                        (film_id, idx, chunk_duration, r2_chunk_key),
                    )
                    chunk_id = str(cur.fetchone()[0])
                    chunk_ids.append((chunk_id, idx))
                conn.commit()
            finally:
                conn.close()

        # 11. Enqueue extract_chunk tasks in parallel
        log.info("process_film: enqueueing %d extract_chunk tasks for film %s", len(chunk_ids), film_id)
        task_group = group(
            extract_chunk.s(film_id, chunk_id, chunk_index)
            for chunk_id, chunk_index in chunk_ids
        )
        task_group.apply_async()

        # 12. Update status
        _update_film_status(film_id, "chunks_uploaded",
                           gemini_processing_status="uploading")

        log.info("process_film: film %s chunks uploaded, extract_chunk tasks enqueued", film_id)

    except SoftTimeLimitExceeded:
        log.error("process_film: soft time limit exceeded for film %s", film_id)
        _write_dead_letter(
            task_name="process_film",
            task_args={"film_id": film_id},
            queue="film_processing",
            error_message="Processing timed out after 55 minutes",
            error_tb=traceback.format_exc(),
            retry_count=self.request.retries,
            film_id=film_id,
            user_id=user_id,
        )
        _update_film_status(film_id, "error", "Processing timed out after 55 minutes")
        raise

    except (FilmValidationError, FFmpegError) as exc:
        # Non-retryable errors — film is bad, not infrastructure
        _write_dead_letter(
            task_name="process_film",
            task_args={"film_id": film_id},
            queue="film_processing",
            error_message=str(exc),
            error_tb=traceback.format_exc(),
            retry_count=self.request.retries,
            film_id=film_id,
            user_id=user_id,
        )
        _update_film_status(film_id, "error", str(exc))
        from tasks.notifications import notify_coach
        notify_coach.delay(film_id=film_id, notification_type="film_error")

    except Exception as exc:
        if self.request.retries >= self.max_retries:
            _write_dead_letter(
                task_name="process_film",
                task_args={"film_id": film_id},
                queue="film_processing",
                error_message=str(exc),
                error_tb=traceback.format_exc(),
                retry_count=self.request.retries,
                film_id=film_id,
                user_id=user_id,
            )
            _update_film_status(film_id, "error", str(exc))
            from tasks.notifications import notify_coach
            notify_coach.delay(film_id=film_id, notification_type="film_error")
        raise self.retry(exc=exc, countdown=_backoff(self.request.retries))

    finally:
        _cleanup_tmp(tmp_files)


# ---------------------------------------------------------------------------
# TASK: extract_chunk
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    name="tasks.film_processing.extract_chunk",
    queue="film_processing",
    max_retries=3,
    default_retry_delay=30,
    soft_time_limit=480,
    time_limit=600,
    acks_late=True,
)
def extract_chunk(self, film_id: str, chunk_id: str, chunk_index: int):
    """Download chunk from R2, upload to Gemini File API, poll until ACTIVE,
    save URI + expiry to DB. If all chunks are active, enqueue run_chunk_synthesis."""

    tmp_files = []
    bucket = os.environ["CLOUDFLARE_R2_BUCKET_FILMS"]

    try:
        # 1. Fetch chunk row — idempotency check.
        # Only a fully complete chunk (Gemini file active AND Prompt 0A done)
        # short-circuits. A chunk whose file is already uploaded but whose
        # extraction is pending / extracting / errored must re-run Prompt 0A
        # on retry — otherwise a transient Prompt 0A failure would leave the
        # chunk stuck active-but-unextracted and silently skip every retry.
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT gemini_file_state, r2_chunk_key, extraction_status, "
                    "gemini_file_uri FROM film_chunks WHERE id = %s",
                    (chunk_id,),
                )
                row = cur.fetchone()
        finally:
            conn.close()

        if not row:
            log.error("extract_chunk: chunk %s not found", chunk_id)
            return

        gemini_file_state, r2_chunk_key, extraction_status, existing_uri = row

        if gemini_file_state == "active" and extraction_status == "complete":
            log.info("extract_chunk: chunk %s already extracted, skipping", chunk_id)
            return

        # 2. Resolve the Gemini URI. If the file is already uploaded (state
        # 'active' + URI present) we reuse it and skip the R2 download +
        # Gemini re-upload — Prompt 0A is the only work left.
        if gemini_file_state == "active" and existing_uri:
            log.info(
                "extract_chunk: chunk %s already uploaded (extraction_status=%s), resuming at Prompt 0A",
                chunk_id, extraction_status,
            )
            gemini_uri = existing_uri

            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE film_chunks SET extraction_status = 'extracting' "
                        "WHERE id = %s",
                        (chunk_id,),
                    )
                conn.commit()
            finally:
                conn.close()
        else:
            # Fresh path (or partial prior run without a saved URI).
            local_path = f"/tmp/{film_id}_chunk_{chunk_index:03d}.mp4"
            tmp_files.append(local_path)

            log.info("extract_chunk: downloading chunk %d for film %s from R2", chunk_index, film_id)
            download_from_r2(bucket, r2_chunk_key, local_path)

            log.info("extract_chunk: uploading chunk %d for film %s to Gemini", chunk_index, film_id)
            gemini_result = upload_to_gemini(local_path)
            gemini_uri = gemini_result["uri"]

            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE film_chunks SET "
                        "gemini_file_uri = %s, gemini_file_state = 'active', "
                        "gemini_file_expires_at = %s, extraction_status = 'extracting' "
                        "WHERE id = %s",
                        (gemini_result["uri"], gemini_result["expires_at"], chunk_id),
                    )
                conn.commit()
            finally:
                conn.close()

            log.info("extract_chunk: chunk %d for film %s is ACTIVE, uri=%s",
                     chunk_index, film_id, gemini_uri[:60])

        # 3. Run Prompt 0A against this chunk's video.
        # Loader raises NotImplementedError if the prompt file is not yet
        # written — existing retry + dead letter handlers surface it.
        prompt_0a, prompt_0a_version = _load_preprocess_prompt("chunk_extraction")

        log.info("extract_chunk: running Prompt 0A (%s) on chunk %d for film %s",
                 prompt_0a_version, chunk_index, film_id)
        acquire_gemini_slot("gemini-2.5-pro")
        provider = get_ai_provider()
        extraction_output = provider.analyze_video(
            uris=[gemini_uri],
            prompt=prompt_0a,
            section_type="chunk_extraction",
        )

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE film_chunks SET "
                    "extraction_output = %s, extraction_status = 'complete' "
                    "WHERE id = %s",
                    (extraction_output, chunk_id),
                )
            conn.commit()
        finally:
            conn.close()

        log.info(
            "extract_chunk: Prompt 0A complete for chunk %d film %s (%d chars, %d/%d tokens)",
            chunk_index, film_id, len(extraction_output),
            provider.last_tokens_input, provider.last_tokens_output,
        )

        # 6. Check if all chunks for this film are now active (atomic check)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                # Advisory lock prevents two chunks completing simultaneously
                # from both enqueueing synthesis
                cur.execute("SELECT pg_try_advisory_xact_lock(%s)",
                            (abs(hash(film_id)) % (2**31),))
                locked = cur.fetchone()[0]
                if locked:
                    cur.execute(
                        "SELECT COUNT(*) FROM film_chunks "
                        "WHERE film_id = %s AND extraction_status != 'complete'",
                        (film_id,),
                    )
                    incomplete = cur.fetchone()[0]
                    if incomplete == 0:
                        log.info("extract_chunk: all chunks extracted for film %s, enqueueing synthesis", film_id)
                        run_chunk_synthesis.delay(film_id)
            conn.commit()
        finally:
            conn.close()

    except SoftTimeLimitExceeded:
        log.error("extract_chunk: timeout for chunk %s film %s", chunk_id, film_id)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE film_chunks SET "
                    "gemini_file_state = 'failed', extraction_status = 'error' "
                    "WHERE id = %s",
                    (chunk_id,),
                )
            conn.commit()
        finally:
            conn.close()
        _fail_film_from_chunk(
            film_id,
            f"Chunk {chunk_index} processing timed out",
        )
        raise

    except GeminiUploadError as exc:
        if self.request.retries >= self.max_retries:
            log.error("extract_chunk: Gemini upload failed after retries for chunk %s: %s", chunk_id, exc)
            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE film_chunks SET "
                        "gemini_file_state = 'failed', extraction_status = 'error' "
                        "WHERE id = %s",
                        (chunk_id,),
                    )
                conn.commit()
            finally:
                conn.close()
            _write_dead_letter(
                task_name="extract_chunk",
                task_args={"film_id": film_id, "chunk_id": chunk_id, "chunk_index": chunk_index},
                queue="film_processing",
                error_message=str(exc),
                error_tb=traceback.format_exc(),
                retry_count=self.request.retries,
                film_id=film_id,
            )
            _fail_film_from_chunk(
                film_id,
                f"Chunk {chunk_index} failed to upload to Gemini: {exc}",
            )
        raise self.retry(exc=exc, countdown=_backoff(self.request.retries))

    except Exception as exc:
        if self.request.retries >= self.max_retries:
            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE film_chunks SET "
                        "gemini_file_state = 'failed', extraction_status = 'error' "
                        "WHERE id = %s",
                        (chunk_id,),
                    )
                conn.commit()
            finally:
                conn.close()
            _write_dead_letter(
                task_name="extract_chunk",
                task_args={"film_id": film_id, "chunk_id": chunk_id, "chunk_index": chunk_index},
                queue="film_processing",
                error_message=str(exc),
                error_tb=traceback.format_exc(),
                retry_count=self.request.retries,
                film_id=film_id,
            )
            _fail_film_from_chunk(
                film_id,
                f"Chunk {chunk_index} failed: {exc}",
            )
        raise self.retry(exc=exc, countdown=_backoff(self.request.retries))

    finally:
        _cleanup_tmp(tmp_files)


# ---------------------------------------------------------------------------
# TASK: run_chunk_synthesis (Prompt 0B — full-game synthesis)
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    name="tasks.film_processing.run_chunk_synthesis",
    queue="film_processing",
    max_retries=2,
    default_retry_delay=60,
    soft_time_limit=600,
    time_limit=720,
    acks_late=True,
)
def run_chunk_synthesis(self, film_id: str):
    """Run Prompt 0B: concatenate per-chunk extractions + roster, generate
    a full-game synthesis document, persist it to film_analysis_cache, and
    mark the film processed.

    Gated by the atomic last-chunk check in extract_chunk — this task only
    fires once every chunk reaches extraction_status='complete'.
    """
    try:
        # 1. Fetch film metadata (team_id, file_hash) and all chunk extractions.
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT team_id, file_hash FROM films WHERE id = %s",
                    (film_id,),
                )
                film_row = cur.fetchone()
                cur.execute(
                    "SELECT chunk_index, extraction_status, extraction_output "
                    "FROM film_chunks WHERE film_id = %s ORDER BY chunk_index",
                    (film_id,),
                )
                chunks = cur.fetchall()
        finally:
            conn.close()

        if not film_row:
            log.error("run_chunk_synthesis: film %s not found", film_id)
            return

        team_id, file_hash = film_row

        if not chunks:
            log.error("run_chunk_synthesis: no chunks found for film %s", film_id)
            _update_film_status(film_id, "error", "No chunks found after processing")
            return

        incomplete = [i for i, status, _ in chunks if status != "complete"]
        if incomplete:
            # Gate should have prevented this. If we got here anyway, bail
            # rather than synthesize a partial document.
            log.error(
                "run_chunk_synthesis: film %s has %d chunks with extraction_status != 'complete' (indexes=%s)",
                film_id, len(incomplete), incomplete,
            )
            _update_film_status(
                film_id, "error",
                f"Cannot synthesize — {len(incomplete)} chunk(s) failed extraction",
            )
            return

        total_count = len(chunks)

        # 2. Build the Prompt 0B input: concatenated chunk extractions + roster.
        extraction_blocks = []
        for chunk_index, _status, output in chunks:
            header = f"=== CHUNK {chunk_index + 1} OF {total_count} ==="
            extraction_blocks.append(f"{header}\n{output or ''}")
        extractions_text = "\n\n".join(extraction_blocks)

        roster_text = format_roster_for_prompt(team_id) if team_id else "(no team)"

        context = (
            "PER-CHUNK EXTRACTIONS:\n" + extractions_text
            + "\n\n---\n\nROSTER:\n" + roster_text
        )

        # 3. Load Prompt 0B. Stub raises NotImplementedError if not written.
        prompt_0b, prompt_0b_version = _load_preprocess_prompt("chunk_synthesis")

        log.info(
            "run_chunk_synthesis: running Prompt 0B (%s) on film %s (%d chunks, %d context chars)",
            prompt_0b_version, film_id, total_count, len(context),
        )

        # 4. Call Gemini Flash via analyze_text (text-only, no video re-read).
        acquire_gemini_slot("gemini-2.5-flash")
        provider = get_ai_provider()
        synthesis_document = provider.analyze_text(
            context=context,
            prompt=prompt_0b,
            section_type="chunk_synthesis",
        )

        # 5. UPSERT into film_analysis_cache keyed on file_hash.
        # Preserve any existing `sections` cache (set by prior reports at the
        # same file_hash) — only overwrite synthesis_document and metadata.
        if not file_hash:
            log.error("run_chunk_synthesis: film %s has no file_hash — cannot cache synthesis", film_id)
            _update_film_status(film_id, "error", "Missing file_hash on film row")
            return

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO film_analysis_cache "
                    "(file_hash, film_id, sections, synthesis_document, prompt_version) "
                    "VALUES (%s, %s, '{}'::jsonb, %s, %s) "
                    "ON CONFLICT (file_hash) DO UPDATE SET "
                    "synthesis_document = EXCLUDED.synthesis_document, "
                    "film_id = EXCLUDED.film_id, "
                    "prompt_version = EXCLUDED.prompt_version",
                    (file_hash, film_id, synthesis_document, PROMPT_VERSION),
                )
            conn.commit()
        finally:
            conn.close()

        # 6. Mark film processed.
        _update_film_status(film_id, "processed", gemini_processing_status="active")
        log.info(
            "run_chunk_synthesis: film %s synthesized (%d chars, %d/%d tokens)",
            film_id, len(synthesis_document),
            provider.last_tokens_input, provider.last_tokens_output,
        )

    except Exception as exc:
        if self.request.retries >= self.max_retries:
            _write_dead_letter(
                task_name="run_chunk_synthesis",
                task_args={"film_id": film_id},
                queue="film_processing",
                error_message=str(exc),
                error_tb=traceback.format_exc(),
                retry_count=self.request.retries,
                film_id=film_id,
            )
            _update_film_status(film_id, "error", f"Synthesis failed: {exc}")
        raise self.retry(exc=exc, countdown=60)
