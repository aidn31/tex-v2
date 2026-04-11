"""Report generation orchestration.

generate_report is the orchestrator — it validates inputs, creates the
Gemini context cache, inserts the 6 report_sections rows, and fires a
Celery chord of 4 run_section tasks (sections 1-4) with
run_synthesis_sections as the callback.

run_synthesis_sections is a minimal stub until task 3.5 lands. It deletes
the context cache in a finally block and marks sections 5-6 as errored
with a 'Deferred to task 3.5' message.
"""

import json
import logging
import time
import traceback

from celery import chord, group
from celery.exceptions import SoftTimeLimitExceeded

from services.ai.router import get_ai_provider
from services.db import get_connection
from services.prompts import load_prompt
from services.rate_limit import acquire_gemini_slot
from services.roster_format import format_roster_for_prompt
from services.uri_expiry import get_valid_chunk_uris
from tasks.celery_app import celery_app
from tasks.section_generation import run_section

log = logging.getLogger(__name__)

SECTIONS_PARALLEL = (
    "offensive_sets",
    "defensive_schemes",
    "pnr_coverage",
    "player_pages",
)
SECTIONS_SEQUENTIAL = ("game_plan", "adjustments_practice")
ALL_SECTIONS = SECTIONS_PARALLEL + SECTIONS_SEQUENTIAL

CONTEXT_CACHE_TTL_SECONDS = 3600  # 1 hour — enough for a full chord to complete


def _write_dead_letter(
    task_name: str,
    task_args: dict,
    queue: str,
    error_message: str,
    error_tb: str,
    retry_count: int,
    report_id: str,
    user_id: str | None = None,
):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO dead_letter_tasks "
                "(task_name, task_args, queue, error_message, error_traceback, "
                "retry_count, film_id, report_id, user_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, NULL, %s, %s)",
                (
                    task_name,
                    json.dumps(task_args),
                    queue,
                    error_message[:2000],
                    (error_tb or "")[:4000],
                    retry_count,
                    report_id,
                    user_id,
                ),
            )
        conn.commit()
    except Exception:
        log.exception("Failed to write dead letter for %s report_id=%s", task_name, report_id)
        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        conn.close()


def _mark_report_error(report_id: str, message: str) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE reports SET status = 'error', error_message = %s, "
                "updated_at = now() WHERE id = %s",
                (message[:2000], report_id),
            )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# generate_report
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    name="tasks.report_generation.generate_report",
    queue="report_generation",
    max_retries=3,
    default_retry_delay=30,
    soft_time_limit=1500,
    time_limit=1800,
    acks_late=True,
)
def generate_report(self, report_id: str):
    """Build context cache, insert pending section rows, fire section chord.

    Per AGENTS.md generate_report full execution sequence.
    """
    try:
        # 1. Fetch report + idempotency check.
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT user_id, team_id, status, prompt_version "
                    "FROM reports WHERE id = %s",
                    (report_id,),
                )
                report_row = cur.fetchone()
        finally:
            conn.close()

        if not report_row:
            raise RuntimeError(f"Report not found: {report_id}")
        user_id, team_id, current_status, prompt_version = report_row
        if current_status in ("complete", "partial", "error"):
            log.info("generate_report: already terminal — skipping",
                     extra={"report_id": report_id, "status": current_status})
            return

        # 2. Mark processing.
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE reports SET status = 'processing', updated_at = now() "
                    "WHERE id = %s",
                    (report_id,),
                )
            conn.commit()
        finally:
            conn.close()

        # 3. Fetch film_ids from report_films.
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT film_id FROM report_films WHERE report_id = %s",
                    (report_id,),
                )
                film_ids = [str(r[0]) for r in cur.fetchall()]
        finally:
            conn.close()

        if not film_ids:
            raise RuntimeError(f"No films linked to report {report_id}")

        # 4. Verify all films are processed.
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, status, file_hash FROM films "
                    "WHERE id = ANY(%s::uuid[]) AND deleted_at IS NULL",
                    (film_ids,),
                )
                film_rows = cur.fetchall()
        finally:
            conn.close()

        if len(film_rows) != len(film_ids):
            raise RuntimeError(
                f"Expected {len(film_ids)} films but found {len(film_rows)} active"
            )

        not_ready = [str(r[0]) for r in film_rows if r[1] != "processed"]
        if not_ready:
            log.info(
                "generate_report: films still processing — retrying in 60s",
                extra={"report_id": report_id, "not_ready": not_ready},
            )
            raise self.retry(
                exc=RuntimeError(f"Films not yet processed: {not_ready}"),
                countdown=60,
            )

        # 5. Collect chunk URIs + synthesis documents for every film.
        all_chunk_uris: list[str] = []
        synthesis_parts: list[str] = []
        conn = get_connection()
        try:
            for film_id, _, file_hash in film_rows:
                chunks = get_valid_chunk_uris(str(film_id), conn)
                all_chunk_uris.extend(c["uri"] for c in chunks)

                if file_hash:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT synthesis_document FROM film_analysis_cache "
                            "WHERE file_hash = %s AND prompt_version = %s",
                            (file_hash, prompt_version),
                        )
                        row = cur.fetchone()
                    if row and row[0]:
                        synthesis_parts.append(row[0])
        finally:
            conn.close()

        if not all_chunk_uris:
            raise RuntimeError(
                f"No chunk URIs available for report {report_id} — films have no active chunks"
            )

        synthesis_document = "\n\n".join(synthesis_parts) if synthesis_parts else None

        # 6. Fetch roster.
        roster_text = format_roster_for_prompt(team_id)

        # 7. Create Gemini context cache.
        acquire_gemini_slot("gemini-2.5-pro")
        provider = get_ai_provider()
        cache_uri = provider.create_context_cache(
            chunk_uris=all_chunk_uris,
            synthesis_document=synthesis_document,
            roster_text=roster_text,
            ttl_seconds=CONTEXT_CACHE_TTL_SECONDS,
            display_name=f"tex-report-{report_id}",
        )

        # 8. Save cache URI on the report row so we can clean it up later.
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE reports SET context_cache_uri = %s, updated_at = now() "
                    "WHERE id = %s",
                    (cache_uri, report_id),
                )
            conn.commit()
        finally:
            conn.close()

        # 9. Insert / upsert all 6 report_sections rows as pending.
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                for section_type in ALL_SECTIONS:
                    cur.execute(
                        "INSERT INTO report_sections "
                        "(report_id, section_type, status, prompt_version) "
                        "VALUES (%s, %s, 'pending', %s) "
                        "ON CONFLICT (report_id, section_type) DO UPDATE "
                        "SET status = 'pending', updated_at = now()",
                        (report_id, section_type, prompt_version),
                    )
            conn.commit()
        finally:
            conn.close()

        # 10. Fire the chord for sections 1-4 → run_synthesis_sections callback.
        chord_header = group(
            run_section.s(report_id, section_type, cache_uri, prompt_version)
            for section_type in SECTIONS_PARALLEL
        )
        chord(chord_header)(
            run_synthesis_sections.s(report_id=report_id, cache_uri=cache_uri)
        )

        log.info(
            "generate_report: chord fired",
            extra={
                "report_id": report_id,
                "chunk_count": len(all_chunk_uris),
                "has_synthesis": bool(synthesis_document),
                "cache_uri": cache_uri,
            },
        )

    except SoftTimeLimitExceeded:
        message = "Report generation timed out after 25 minutes"
        _mark_report_error(report_id, message)
        _write_dead_letter(
            task_name="generate_report",
            task_args={"report_id": report_id},
            queue="report_generation",
            error_message=message,
            error_tb=traceback.format_exc(),
            retry_count=self.request.retries,
            report_id=report_id,
        )
        raise

    except Exception as exc:
        # self.retry() raises a Retry exception — let it propagate unchanged.
        from celery.exceptions import Retry
        if isinstance(exc, Retry):
            raise
        if self.request.retries >= self.max_retries:
            _mark_report_error(report_id, str(exc))
            _write_dead_letter(
                task_name="generate_report",
                task_args={"report_id": report_id},
                queue="report_generation",
                error_message=str(exc),
                error_tb=traceback.format_exc(),
                retry_count=self.request.retries,
                report_id=report_id,
            )
            raise
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))


# ---------------------------------------------------------------------------
# run_synthesis_sections — minimal stub (full version lands in task 3.5)
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    name="tasks.report_generation.run_synthesis_sections",
    queue="report_generation",
    max_retries=2,
    default_retry_delay=60,
    soft_time_limit=600,
    time_limit=720,
    acks_late=True,
)
def run_synthesis_sections(self, chord_results, report_id: str, cache_uri: str):
    """Chord callback — fires after all 4 sections 1-4 reach terminal state.

    STUB FOR TASK 3.5. Current behavior:
      - Logs chord completion.
      - Marks sections 5-6 as 'error' with 'Deferred to task 3.5' message.
      - Deletes the Gemini context cache in a finally block so we don't
        bleed storage cost while waiting for 3.5 to land.
      - Clears reports.context_cache_uri.
      - Does NOT assemble a PDF (that's task 3.7) and does NOT mark the
        report complete — leaves it in 'processing' until the full pipeline
        is built out.
    """
    try:
        # Mark sections 5-6 explicitly errored with the deferral message.
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                for section_type in SECTIONS_SEQUENTIAL:
                    cur.execute(
                        "UPDATE report_sections SET status = 'error', "
                        "error_message = 'Deferred to task 3.5 — run_synthesis_sections stub', "
                        "updated_at = now() "
                        "WHERE report_id = %s AND section_type = %s",
                        (report_id, section_type),
                    )
            conn.commit()
        finally:
            conn.close()

        log.info(
            "run_synthesis_sections stub complete",
            extra={"report_id": report_id, "chord_result_count": len(chord_results or [])},
        )

    finally:
        # Always delete the cache — success or failure.
        if cache_uri:
            try:
                provider = get_ai_provider()
                provider.delete_context_cache(cache_uri)
            except Exception:
                log.warning(
                    "Cache deletion failed in run_synthesis_sections",
                    extra={"report_id": report_id, "cache_uri": cache_uri},
                    exc_info=True,
                )
            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE reports SET context_cache_uri = NULL, updated_at = now() "
                        "WHERE id = %s",
                        (report_id,),
                    )
                conn.commit()
            finally:
                conn.close()
