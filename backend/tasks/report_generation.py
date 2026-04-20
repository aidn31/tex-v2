"""Report generation orchestration.

generate_report is the orchestrator — it validates inputs, creates the
Gemini context cache, inserts the 6 report_sections rows, and fires a
Celery chord of 4 run_section tasks (sections 1-4) with
run_synthesis_sections as the callback.

run_synthesis_sections is the chord callback — it runs sections 5-6
sequentially via Gemini 2.5 Flash using the completed section 1-4 output
as text context. Section 5 (game_plan) feeds into section 6
(adjustments_practice). On completion it caches section outputs and
enqueues assemble_and_deliver. The Gemini context cache is always deleted
in a finally block regardless of outcome.

assemble_and_deliver fetches all 6 sections, calls assemble_pdf(), uploads
the resulting PDF to R2, updates the report status, and notifies the coach.
"""

import json
import logging
import os
import time
import traceback
from datetime import date, timezone

from celery import chord, group
from celery.exceptions import SoftTimeLimitExceeded

from services.ai.router import get_ai_provider, get_fallback_provider
from services.db import get_connection
from services.pdf import assemble_pdf
from services.prompts import load_prompt
from services.gemini_files import delete_gemini_file
from services.r2 import delete_from_r2, upload_bytes_to_r2
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


def _try_section_cache_hit(
    report_id: str,
    film_rows: list,
    prompt_version: str,
) -> dict | None:
    """Check film_analysis_cache for a complete set of sections 1-4.

    Returns the sections dict on hit, None on miss. Only fires for
    single-film reports where the film has a file_hash and the cache
    contains all 4 parallel section types with non-empty string content.
    Multi-film reports always fall through to normal flow.
    """
    if len(film_rows) != 1:
        return None

    _, _, file_hash = film_rows[0]
    if not file_hash:
        return None

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT sections FROM film_analysis_cache "
                "WHERE file_hash = %s AND prompt_version = %s",
                (file_hash, prompt_version),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row or not row[0]:
        return None

    sections = row[0]
    if not isinstance(sections, dict):
        return None

    for section_type in SECTIONS_PARALLEL:
        content = sections.get(section_type)
        if not isinstance(content, str) or not content.strip():
            return None

    return sections


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

        # 6.5. Section cache short-circuit — single-film regeneration at
        # same prompt_version. Skips Gemini entirely for sections 1-4 by
        # reading cached outputs from film_analysis_cache. Sections 5-6
        # still run normally via run_synthesis_sections.
        cached_sections = _try_section_cache_hit(report_id, film_rows, prompt_version)
        if cached_sections is not None:
            file_hash = film_rows[0][2]
            log.info(
                "generate_report: section cache HIT — skipping Gemini chord",
                extra={
                    "report_id": report_id,
                    "file_hash": file_hash,
                    "prompt_version": prompt_version,
                },
            )

            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    for section_type in SECTIONS_PARALLEL:
                        cur.execute(
                            "INSERT INTO report_sections "
                            "(report_id, section_type, status, content, "
                            "model_used, prompt_version) "
                            "VALUES (%s, %s, 'complete', %s, 'cached', %s) "
                            "ON CONFLICT (report_id, section_type) DO UPDATE "
                            "SET status = 'complete', "
                            "content = EXCLUDED.content, "
                            "model_used = 'cached', "
                            "prompt_version = EXCLUDED.prompt_version, "
                            "updated_at = now()",
                            (
                                report_id,
                                section_type,
                                cached_sections[section_type],
                                prompt_version,
                            ),
                        )
                    for section_type in SECTIONS_SEQUENTIAL:
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

            # Enqueue synthesis directly — no chord, no Gemini cache.
            # Empty cache_uri is safe: the finally block in
            # run_synthesis_sections guards deletion with `if cache_uri:`.
            run_synthesis_sections.delay(
                None, report_id=report_id, cache_uri=""
            )
            return

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
# run_synthesis_sections helpers
# ---------------------------------------------------------------------------

SECTION_LABELS = {
    "offensive_sets": "OFFENSIVE SETS",
    "defensive_schemes": "DEFENSIVE SCHEMES",
    "pnr_coverage": "PICK AND ROLL COVERAGE",
    "player_pages": "INDIVIDUAL PLAYER PAGES",
}


def _build_synthesis_context(section_rows: dict) -> str:
    """Concatenate completed sections 1-4 into text context for sections 5-6."""
    parts = []
    for section_type in SECTIONS_PARALLEL:
        info = section_rows.get(section_type, {})
        if info.get("status") == "complete" and info.get("content"):
            label = SECTION_LABELS[section_type]
            parts.append(f"{label}:\n{info['content']}")
    return "\n\n".join(parts)


def _mark_section_error(report_id: str, section_type: str, message: str) -> None:
    """Mark a synthesis section as errored."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE report_sections SET status = 'error', error_message = %s, "
                "updated_at = now() WHERE report_id = %s AND section_type = %s",
                (message[:2000], report_id, section_type),
            )
        conn.commit()
    finally:
        conn.close()


def _apply_failure_credit(user_id: str, report_id: str) -> None:
    """Grant one free report credit to compensate for a failed report.

    Per CLAUDE.md PAYMENT RULES: technical failure → automatic credit applied
    to account, no Stripe refund.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET report_credits = report_credits + 1, "
                "updated_at = now() WHERE id = %s",
                (user_id,),
            )
        conn.commit()
    finally:
        conn.close()
    log.info(
        "Failure credit applied",
        extra={"user_id": user_id, "report_id": report_id},
    )


def _handle_all_sections_errored(report_id: str) -> None:
    """All 4 parallel sections failed — mark report error, credit, notify."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM reports WHERE id = %s", (report_id,))
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        log.error("Report not found for error handling: %s", report_id)
        return
    user_id = str(row[0])

    _mark_report_error(
        report_id,
        "All 4 parallel sections failed — no content for synthesis",
    )
    _apply_failure_credit(user_id, report_id)

    from tasks.notifications import notify_coach
    notify_coach.delay(report_id=report_id, notification_type="report_failed_credit_applied")

    log.info(
        "All parallel sections errored — report failed with credit",
        extra={"report_id": report_id, "user_id": user_id},
    )


def _run_text_section(
    report_id: str,
    section_type: str,
    context: str,
    prompt_version: str,
) -> str | None:
    """Run a single text-only section via Gemini Flash with Claude fallback.

    Returns content on success, None on failure. Failure marks the section
    as errored but does NOT fail the entire task — the report proceeds as
    partial.

    Per CLAUDE.md AI PROVIDER RULES: sections 5-6 use Gemini 2.5 Flash
    primary, Claude 3.5 Sonnet fallback. Fallback fires automatically.
    """
    try:
        # Mark processing.
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE report_sections SET status = 'processing', "
                    "updated_at = now() "
                    "WHERE report_id = %s AND section_type = %s",
                    (report_id, section_type),
                )
            conn.commit()
        finally:
            conn.close()

        # Load prompt (shared by Flash and Claude paths).
        prompt_text, file_version = load_prompt(section_type)
        version_to_save = prompt_version or file_version

        # Try Gemini Flash first.
        model_used = "gemini-2.5-flash"
        try:
            acquire_gemini_slot("gemini-2.5-flash")
            start = time.monotonic()
            provider = get_ai_provider()
            content = provider.analyze_text(
                context=context,
                prompt=prompt_text,
                section_type=section_type,
            )
            elapsed = int(time.monotonic() - start)
            tokens_in = provider.last_tokens_input
            tokens_out = provider.last_tokens_output
        except Exception as flash_exc:
            # Flash failed — fall back to Claude 3.5 Sonnet.
            log.warning(
                "Flash failed for %s — falling back to Claude",
                section_type,
                extra={
                    "report_id": report_id,
                    "section_type": section_type,
                    "flash_error": str(flash_exc),
                },
            )
            model_used = "claude-3-5-sonnet"
            start = time.monotonic()
            fallback = get_fallback_provider()
            content = fallback.analyze_text(
                context=context,
                prompt=prompt_text,
                section_type=section_type,
            )
            elapsed = int(time.monotonic() - start)
            tokens_in = fallback.last_tokens_input
            tokens_out = fallback.last_tokens_output

        # Persist result (same for both paths).
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE report_sections SET status = 'complete', content = %s, "
                    "model_used = %s, prompt_version = %s, tokens_input = %s, "
                    "tokens_output = %s, generation_time_seconds = %s, "
                    "updated_at = now() "
                    "WHERE report_id = %s AND section_type = %s",
                    (
                        content,
                        model_used,
                        version_to_save,
                        tokens_in,
                        tokens_out,
                        elapsed,
                        report_id,
                        section_type,
                    ),
                )
            conn.commit()
        finally:
            conn.close()

        log.info(
            "run_text_section complete",
            extra={
                "report_id": report_id,
                "section_type": section_type,
                "model": model_used,
                "tokens_input": tokens_in,
                "tokens_output": tokens_out,
                "elapsed_sec": elapsed,
            },
        )
        return content

    except Exception:
        # Both Flash and Claude failed.
        log.exception(
            "Both Flash and Claude failed for section %s",
            section_type,
            extra={"report_id": report_id, "section_type": section_type},
        )
        _mark_section_error(
            report_id,
            section_type,
            f"Flash and Claude both failed: {traceback.format_exc()[-500:]}",
        )
        return None


def _cache_section_outputs(
    report_id: str,
    section_rows: dict,
    prompt_version: str,
) -> None:
    """Write completed sections 1-4 to film_analysis_cache for future cache hits."""
    sections = {}
    for section_type in SECTIONS_PARALLEL:
        info = section_rows.get(section_type, {})
        if info.get("status") == "complete" and info.get("content"):
            sections[section_type] = info["content"]

    if not sections:
        return

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT f.file_hash FROM films f "
                "JOIN report_films rf ON rf.film_id = f.id "
                "WHERE rf.report_id = %s AND f.file_hash IS NOT NULL "
                "LIMIT 1",
                (report_id,),
            )
            row = cur.fetchone()
            if not row:
                log.warning(
                    "No film hash found for cache write — skipping",
                    extra={"report_id": report_id},
                )
                return
            file_hash = row[0]

            cur.execute(
                "UPDATE film_analysis_cache SET sections = %s "
                "WHERE file_hash = %s AND prompt_version = %s",
                (json.dumps(sections), file_hash, prompt_version),
            )
        conn.commit()
    finally:
        conn.close()

    log.info(
        "Sections 1-4 cached in film_analysis_cache",
        extra={
            "report_id": report_id,
            "file_hash": file_hash,
            "section_count": len(sections),
        },
    )


# ---------------------------------------------------------------------------
# run_synthesis_sections — chord callback (task 3.5)
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

    Runs sections 5-6 sequentially using Gemini 2.5 Flash with text context
    from completed sections 1-4. Section 5 (game_plan) feeds into section 6
    (adjustments_practice).

    On completion: writes sections 1-4 to film_analysis_cache and enqueues
    assemble_and_deliver (task 3.7).

    If all 4 parallel sections errored: marks report as error, applies
    failure credit, notifies coach. No synthesis attempted.
    """
    try:
        # 1. Fetch all 6 section rows for this report.
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT section_type, status, content "
                    "FROM report_sections WHERE report_id = %s",
                    (report_id,),
                )
                section_rows = {
                    row[0]: {"status": row[1], "content": row[2]}
                    for row in cur.fetchall()
                }
        finally:
            conn.close()

        # 2. Count errored / completed sections from sections 1-4.
        parallel_errored = sum(
            1 for st in SECTIONS_PARALLEL
            if section_rows.get(st, {}).get("status") == "error"
        )
        parallel_complete = sum(
            1 for st in SECTIONS_PARALLEL
            if section_rows.get(st, {}).get("status") == "complete"
        )

        log.info(
            "run_synthesis_sections: chord landed",
            extra={
                "report_id": report_id,
                "parallel_complete": parallel_complete,
                "parallel_errored": parallel_errored,
                "chord_result_count": len(chord_results or []),
            },
        )

        # 3. If all 4 errored — no context for synthesis.
        if parallel_errored == len(SECTIONS_PARALLEL):
            _handle_all_sections_errored(report_id)
            return

        # 4. Build synthesis context from completed sections 1-4.
        context = _build_synthesis_context(section_rows)

        # 5. Fetch prompt_version from report row.
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT prompt_version FROM reports WHERE id = %s",
                    (report_id,),
                )
                row = cur.fetchone()
        finally:
            conn.close()
        prompt_version = row[0] if row else "v1.0"

        # 6. Run section 5 — Game Plan (Gemini Flash).
        game_plan_content = _run_text_section(
            report_id, "game_plan", context, prompt_version,
        )

        # 7. Build section 6 context (sections 1-4 + section 5 if it succeeded).
        if game_plan_content:
            context_with_game_plan = context + f"\n\nGAME PLAN:\n{game_plan_content}"
        else:
            context_with_game_plan = context

        # 8. Run section 6 — Adjustments + Practice Plan (Gemini Flash).
        _run_text_section(
            report_id, "adjustments_practice", context_with_game_plan, prompt_version,
        )

        # 9. Cache sections 1-4 content in film_analysis_cache.
        _cache_section_outputs(report_id, section_rows, prompt_version)

        # 10. Enqueue assemble_and_deliver.
        assemble_and_deliver.delay(report_id)
        log.info(
            "run_synthesis_sections complete — assemble_and_deliver enqueued",
            extra={
                "report_id": report_id,
                "parallel_complete": parallel_complete,
            },
        )

    except SoftTimeLimitExceeded:
        message = "Synthesis sections timed out after 10 minutes"
        _mark_report_error(report_id, message)
        _write_dead_letter(
            task_name="run_synthesis_sections",
            task_args={"report_id": report_id, "cache_uri": cache_uri},
            queue="report_generation",
            error_message=message,
            error_tb=traceback.format_exc(),
            retry_count=self.request.retries,
            report_id=report_id,
        )
        raise

    except Exception as exc:
        from celery.exceptions import Retry
        if isinstance(exc, Retry):
            raise
        if self.request.retries >= self.max_retries:
            _mark_report_error(report_id, str(exc))
            _write_dead_letter(
                task_name="run_synthesis_sections",
                task_args={"report_id": report_id, "cache_uri": cache_uri},
                queue="report_generation",
                error_message=str(exc),
                error_tb=traceback.format_exc(),
                retry_count=self.request.retries,
                report_id=report_id,
            )
            raise
        raise self.retry(exc=exc, countdown=60 * (3 ** self.request.retries))

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
                        "UPDATE reports SET context_cache_uri = NULL, "
                        "updated_at = now() WHERE id = %s",
                        (report_id,),
                    )
                conn.commit()
            finally:
                conn.close()


def _cleanup_chunks(report_id: str) -> None:
    """Delete Gemini file URIs and R2 chunk files for all films in this report.

    Best-effort — failures are logged but never block report delivery.
    Called AFTER reports.status is confirmed written to a terminal state.
    Per AGENTS.md steps 8-9.
    """
    films_bucket = os.environ.get("CLOUDFLARE_R2_BUCKET_FILMS", "")

    # Fetch film_ids for this report.
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
        return

    # Fetch all chunks for these films.
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, gemini_file_uri, gemini_file_state, r2_chunk_key "
                "FROM film_chunks WHERE film_id = ANY(%s::uuid[])",
                (film_ids,),
            )
            chunks = cur.fetchall()
    finally:
        conn.close()

    if not chunks:
        return

    deleted_gemini = 0
    deleted_r2 = 0

    for chunk_id, gemini_uri, gemini_state, r2_key in chunks:
        # Step 8: Delete Gemini file URI if still active.
        if gemini_uri and gemini_state == "active":
            delete_gemini_file(gemini_uri)
            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE film_chunks SET gemini_file_state = 'deleted' "
                        "WHERE id = %s",
                        (chunk_id,),
                    )
                conn.commit()
            finally:
                conn.close()
            deleted_gemini += 1

        # Step 9: Delete R2 chunk file.
        if r2_key and films_bucket:
            delete_from_r2(films_bucket, r2_key)
            deleted_r2 += 1

    log.info(
        "Chunk cleanup complete",
        extra={
            "report_id": report_id,
            "total_chunks": len(chunks),
            "deleted_gemini": deleted_gemini,
            "deleted_r2": deleted_r2,
        },
    )


# ---------------------------------------------------------------------------
# assemble_and_deliver — PDF assembly + R2 upload (task 3.8)
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    name="tasks.report_generation.assemble_and_deliver",
    queue="report_generation",
    max_retries=2,
    default_retry_delay=60,
    soft_time_limit=600,
    time_limit=720,
    acks_late=True,
)
def assemble_and_deliver(self, report_id: str):
    """Fetch sections, assemble PDF, upload to R2, update report status, notify coach.

    Per AGENTS.md assemble_and_deliver full execution sequence.
    """
    try:
        # 1. Fetch report + idempotency check.
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT user_id, team_id, status, created_at "
                    "FROM reports WHERE id = %s",
                    (report_id,),
                )
                report_row = cur.fetchone()
        finally:
            conn.close()

        if not report_row:
            raise RuntimeError(f"Report not found: {report_id}")
        user_id, team_id, current_status, created_at = report_row

        # 2. Idempotency — already terminal.
        if current_status in ("complete", "partial"):
            log.info(
                "assemble_and_deliver: already terminal — skipping",
                extra={"report_id": report_id, "status": current_status},
            )
            return

        # 3. Fetch team name for the cover page.
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT name FROM teams WHERE id = %s",
                    (team_id,),
                )
                team_row = cur.fetchone()
        finally:
            conn.close()
        team_name = team_row[0] if team_row else "Unknown Team"

        # 4. Fetch all 6 section rows.
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT section_type, status, content, error_message "
                    "FROM report_sections WHERE report_id = %s",
                    (report_id,),
                )
                sections = [
                    {
                        "section_type": row[0],
                        "status": row[1],
                        "content": row[2],
                        "error_message": row[3],
                    }
                    for row in cur.fetchall()
                ]
        finally:
            conn.close()

        # 5. Count errored sections.
        error_count = sum(1 for s in sections if s["status"] == "error")

        # 6. Full failure path — all 6 errored.
        if error_count == 6:
            _mark_report_error(
                report_id,
                "All 6 sections failed — no report generated",
            )
            _apply_failure_credit(str(user_id), report_id)
            from tasks.notifications import notify_coach
            notify_coach.delay(
                report_id=report_id,
                notification_type="report_failed_credit_applied",
            )
            log.info(
                "assemble_and_deliver: all sections errored — credit applied",
                extra={"report_id": report_id},
            )
            return

        # 7. Assemble PDF.
        is_partial = error_count > 0
        pdf_bytes = assemble_pdf(
            sections=sections,
            team_name=team_name,
            report_date=date.today(),
            is_partial=is_partial,
        )

        # 8. Upload PDF to R2 reports bucket.
        bucket = os.environ["CLOUDFLARE_R2_BUCKET_REPORTS"]
        r2_key = f"reports/{user_id}/{report_id}/scouting_report.pdf"
        upload_bytes_to_r2(
            bucket=bucket,
            key=r2_key,
            data=pdf_bytes,
            content_type="application/pdf",
        )

        # 9. Update report to terminal status.
        final_status = "partial" if is_partial else "complete"
        generation_seconds = None
        if created_at:
            from datetime import datetime
            now = datetime.now(timezone.utc)
            if created_at.tzinfo is None:
                from datetime import timezone as tz
                created_at = created_at.replace(tzinfo=tz.utc)
            generation_seconds = int((now - created_at).total_seconds())

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE reports SET status = %s, pdf_r2_key = %s, "
                    "completed_at = now(), generation_time_seconds = %s, "
                    "updated_at = now() WHERE id = %s",
                    (final_status, r2_key, generation_seconds, report_id),
                )
            conn.commit()
        finally:
            conn.close()

        # 10. Chunk cleanup — Gemini file URIs + R2 chunk files.
        # Report status is already written. Safe to delete per CLAUDE.md:
        # "Never delete R2 chunks before reports.status = complete"
        _cleanup_chunks(report_id)

        # 11. Notify coach.
        from tasks.notifications import notify_coach
        notification_type = "report_complete" if not is_partial else "report_partial"
        notify_coach.delay(
            report_id=report_id,
            notification_type=notification_type,
        )

        log.info(
            "assemble_and_deliver complete",
            extra={
                "report_id": report_id,
                "status": final_status,
                "error_count": error_count,
                "pdf_size_bytes": len(pdf_bytes),
                "r2_key": r2_key,
                "generation_seconds": generation_seconds,
            },
        )

    except SoftTimeLimitExceeded:
        message = "PDF assembly timed out after 10 minutes"
        _mark_report_error(report_id, message)
        _write_dead_letter(
            task_name="assemble_and_deliver",
            task_args={"report_id": report_id},
            queue="report_generation",
            error_message=message,
            error_tb=traceback.format_exc(),
            retry_count=self.request.retries,
            report_id=report_id,
        )
        raise

    except Exception as exc:
        from celery.exceptions import Retry
        if isinstance(exc, Retry):
            raise
        if self.request.retries >= self.max_retries:
            _mark_report_error(report_id, str(exc))
            _write_dead_letter(
                task_name="assemble_and_deliver",
                task_args={"report_id": report_id},
                queue="report_generation",
                error_message=str(exc),
                error_tb=traceback.format_exc(),
                retry_count=self.request.retries,
                report_id=report_id,
            )
            raise
        raise self.retry(exc=exc, countdown=60 * (3 ** self.request.retries))
