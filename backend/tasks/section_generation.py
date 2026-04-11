"""Section generation tasks.

run_section executes a single section prompt against a pre-created Gemini
context cache. Sections 1-4 are dispatched in parallel as a Celery chord
group by generate_report. The chord callback (run_synthesis_sections) fires
after all four complete.
"""

import json
import logging
import time
import traceback

from celery.exceptions import SoftTimeLimitExceeded

from services.ai.router import get_ai_provider
from services.db import get_connection
from services.prompts import load_prompt
from services.rate_limit import acquire_gemini_slot
from tasks.celery_app import celery_app

log = logging.getLogger(__name__)


def _write_dead_letter(
    task_name: str,
    task_args: dict,
    queue: str,
    error_message: str,
    error_tb: str,
    retry_count: int,
    report_id: str,
):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO dead_letter_tasks "
                "(task_name, task_args, queue, error_message, error_traceback, "
                "retry_count, film_id, report_id, user_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, NULL, %s, NULL)",
                (
                    task_name,
                    json.dumps(task_args),
                    queue,
                    error_message[:2000],
                    (error_tb or "")[:4000],
                    retry_count,
                    report_id,
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


def _mark_section_error(report_id: str, section_type: str, message: str) -> None:
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


@celery_app.task(
    bind=True,
    name="tasks.section_generation.run_section",
    queue="section_generation",
    max_retries=3,
    default_retry_delay=30,
    soft_time_limit=480,
    time_limit=600,
    acks_late=True,
)
def run_section(self, report_id: str, section_type: str, cache_uri: str, prompt_version: str):
    """Run one of sections 1-4 against a pre-created Gemini context cache.

    Per AGENTS.md run_section full execution sequence. Sections 5-6 do NOT
    use this task — they run in run_synthesis_sections (task 3.5).
    """
    try:
        # 1. Idempotency check — if already complete, do nothing.
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT status FROM report_sections "
                    "WHERE report_id = %s AND section_type = %s",
                    (report_id, section_type),
                )
                row = cur.fetchone()
        finally:
            conn.close()

        if not row:
            raise RuntimeError(
                f"report_sections row missing for report={report_id} section={section_type}"
            )
        if row[0] == "complete":
            log.info("run_section: already complete — skipping",
                     extra={"report_id": report_id, "section_type": section_type})
            return

        # 2. Mark processing.
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE report_sections SET status = 'processing', updated_at = now() "
                    "WHERE report_id = %s AND section_type = %s",
                    (report_id, section_type),
                )
            conn.commit()
        finally:
            conn.close()

        # 3. Load prompt.
        prompt_text, file_version = load_prompt(section_type)
        # prompt_version is the version the orchestrator locked in at report
        # creation — if the file on disk has drifted, prefer what the orchestrator
        # captured (cache invalidation is keyed on it).
        version_to_save = prompt_version or file_version

        # 4. Rate limit slot (shared across all workers via Redis).
        acquire_gemini_slot("gemini-2.5-pro")

        # 5. Run the section prompt against the context cache.
        start = time.monotonic()
        provider = get_ai_provider()
        content = provider.analyze_video_cached(
            cache_uri=cache_uri,
            prompt=prompt_text,
            section_type=section_type,
        )
        elapsed = int(time.monotonic() - start)

        # 6. Persist result.
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE report_sections SET status = 'complete', content = %s, "
                    "model_used = %s, prompt_version = %s, tokens_input = %s, "
                    "tokens_output = %s, generation_time_seconds = %s, updated_at = now() "
                    "WHERE report_id = %s AND section_type = %s",
                    (
                        content,
                        "gemini-2.5-pro",
                        version_to_save,
                        provider.last_tokens_input,
                        provider.last_tokens_output,
                        elapsed,
                        report_id,
                        section_type,
                    ),
                )
            conn.commit()
        finally:
            conn.close()

        log.info(
            "run_section complete",
            extra={
                "report_id": report_id,
                "section_type": section_type,
                "tokens_input": provider.last_tokens_input,
                "tokens_output": provider.last_tokens_output,
                "elapsed_sec": elapsed,
            },
        )

    except SoftTimeLimitExceeded:
        message = f"Section {section_type} timed out after 8 minutes"
        _mark_section_error(report_id, section_type, message)
        _write_dead_letter(
            task_name="run_section",
            task_args={
                "report_id": report_id,
                "section_type": section_type,
                "cache_uri": cache_uri,
                "prompt_version": prompt_version,
            },
            queue="section_generation",
            error_message=message,
            error_tb=traceback.format_exc(),
            retry_count=self.request.retries,
            report_id=report_id,
        )
        raise

    except Exception as exc:
        if self.request.retries >= self.max_retries:
            _mark_section_error(report_id, section_type, str(exc))
            _write_dead_letter(
                task_name="run_section",
                task_args={
                    "report_id": report_id,
                    "section_type": section_type,
                    "cache_uri": cache_uri,
                    "prompt_version": prompt_version,
                },
                queue="section_generation",
                error_message=str(exc),
                error_tb=traceback.format_exc(),
                retry_count=self.request.retries,
                report_id=report_id,
            )
            raise
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))
